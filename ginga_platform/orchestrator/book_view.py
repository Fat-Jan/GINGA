"""Read-only BookView projection and query helpers.

BookView is a derived workspace view.  It is not runtime state truth and must
not write under ``foundation/runtime_state``.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.runner.state_io import StateIO


DEFAULT_OUTPUT_ROOT = Path(".ops/book_views")


class BookViewError(RuntimeError):
    """BookView projection/query contract error."""


def export_book_view(
    book_id: str,
    *,
    run_id: str | None = None,
    state_root: str | Path | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Export a read-only projection under ``.ops/book_views/<book>/<run>``."""

    run = _safe_segment(run_id or _default_run_id())
    root = _validate_output_root(Path(output_root))
    out_dir = root / _safe_segment(book_id) / run
    sio = StateIO(book_id, state_root=state_root, autoload=True)
    state = sio.state
    chapters = _load_chapters(sio.state_dir)
    payload = _build_payload(book_id=book_id, run_id=run, sio=sio, state=state, chapters=chapters)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "book_view.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(_render_markdown(payload), encoding="utf-8")
    chapter_dir = out_dir / "chapters"
    chapter_dir.mkdir(exist_ok=True)
    for chapter in chapters:
        src = Path(chapter["path"])
        if src.is_file():
            shutil.copyfile(src, chapter_dir / src.name)
    return {"status": "exported", "book_id": book_id, "run_id": run, "output_dir": str(out_dir)}


def query_book_view(
    book_id: str,
    query: str,
    *,
    state_root: str | Path | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Read clean state/chapter artifacts and return simple deterministic matches."""

    sio = StateIO(book_id, state_root=state_root, autoload=True)
    state = sio.state
    chapters = _load_chapters(sio.state_dir)
    needle = str(query).strip().lower()
    matches: list[dict[str, Any]] = []
    for item in _query_corpus(state=state, chapters=chapters):
        haystack = str(item.get("text", "")).lower()
        if not needle or needle in haystack:
            matches.append(item)
        if len(matches) >= max(1, limit):
            break
    return {
        "book_id": book_id,
        "mode": "read_only",
        "query": query,
        "data_sources": ["StateIO", "chapter_artifacts"],
        "forbidden_default_sources": [".ops/book_analysis/**"],
        "match_count": len(matches),
        "matches": matches,
    }


def _build_payload(
    *,
    book_id: str,
    run_id: str,
    sio: StateIO,
    state: dict[str, dict[str, Any]],
    chapters: list[dict[str, Any]],
) -> dict[str, Any]:
    locked = state.get("locked", {})
    entity = state.get("entity_runtime", {})
    return {
        "book_id": book_id,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "projection": {
            "kind": "BookView",
            "truth_source": "StateIO",
            "is_state_truth": False,
            "writes_runtime_state": False,
            "output_boundary": ".ops/book_views/<book_id>/<run_id>/",
        },
        "data_sources": {
            "state_dir": str(sio.state_dir),
            "state_domains": ["locked", "entity_runtime", "workspace", "retrieved", "audit_log"],
            "chapter_artifacts": [chapter["path"] for chapter in chapters],
            "forbidden_default_sources": [".ops/book_analysis/**", ".ops/market_research/**", ".ops/external_sources/**"],
        },
        "story": {
            "premise": (locked.get("STORY_DNA") or {}).get("premise", ""),
            "conflict_engine": (locked.get("STORY_DNA") or {}).get("conflict_engine", ""),
            "topic": (locked.get("GENRE_LOCKED") or {}).get("topic", []),
            "total_words": (entity.get("GLOBAL_SUMMARY") or {}).get("total_words", 0),
        },
        "characters": (entity.get("CHARACTER_STATE") or {}),
        "foreshadow": (entity.get("FORESHADOW_STATE") or {}).get("pool", []),
        "chapters": chapters,
    }


def _load_chapters(state_dir: Path) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for path in sorted(state_dir.glob("chapter_*.md")):
        text = path.read_text(encoding="utf-8")
        chapters.append(
            {
                "name": path.name,
                "path": str(path),
                "title": _extract_title(text) or path.stem,
                "chars": len(text),
                "preview": _preview(text),
            }
        )
    return chapters


def _query_corpus(*, state: dict[str, dict[str, Any]], chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entity = state.get("entity_runtime", {})
    corpus: list[dict[str, Any]] = []
    for key, value in (entity.get("CHARACTER_STATE") or {}).items():
        corpus.append({"kind": "character", "id": key, "text": json.dumps(value, ensure_ascii=False)})
    for item in (entity.get("FORESHADOW_STATE") or {}).get("pool", []):
        corpus.append({"kind": "foreshadow", "id": item.get("id", ""), "text": json.dumps(item, ensure_ascii=False)})
    for chapter in chapters:
        corpus.append({"kind": "chapter", "id": chapter["name"], "text": f"{chapter['title']}\n{chapter['preview']}"})
    return corpus


def _render_markdown(payload: dict[str, Any]) -> str:
    story = payload["story"]
    lines = [
        f"# BookView: {payload['book_id']}",
        "",
        "> Derived projection only. State truth remains StateIO / foundation/runtime_state.",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- premise: {story.get('premise', '')}",
        f"- topic: {story.get('topic', [])}",
        f"- total_words: {story.get('total_words', 0)}",
        f"- chapters: {len(payload['chapters'])}",
        f"- foreshadow: {len(payload['foreshadow'])}",
        "",
        "## Chapters",
        "",
    ]
    for chapter in payload["chapters"]:
        lines.append(f"- `{chapter['name']}`: {chapter['title']} ({chapter['chars']} chars)")
    lines.append("")
    return "\n".join(lines)


def _validate_output_root(root: Path) -> Path:
    normalized = root.as_posix().rstrip("/")
    if not (normalized == ".ops/book_views" or normalized.endswith("/.ops/book_views")):
        raise BookViewError("BookView output_root must be .ops/book_views")
    return root


def _safe_segment(value: str) -> str:
    if not value or "/" in value or ".." in value:
        raise BookViewError(f"invalid path segment: {value!r}")
    return value


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _preview(text: str, limit: int = 260) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed[:limit]


__all__ = ["BookViewError", "DEFAULT_OUTPUT_ROOT", "export_book_view", "query_book_view"]
