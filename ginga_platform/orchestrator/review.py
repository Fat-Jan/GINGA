"""Warn-only Review / deslop sidecar reports.

The review report is advisory output only. It reads StateIO snapshots and
chapter artifacts, then writes a sidecar report under ``.ops/reviews``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.runner.state_io import StateIO


DEFAULT_OUTPUT_ROOT = Path(".ops/reviews")
DEFAULT_RUBRIC_ID = "platform_cn_webnovel_v1"


class ReviewError(RuntimeError):
    """Review/deslop sidecar contract error."""


def export_review_report(
    book_id: str,
    *,
    run_id: str | None = None,
    state_root: str | Path | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    rubric_profile: str = DEFAULT_RUBRIC_ID,
) -> dict[str, Any]:
    """Write a warn-only review report under ``.ops/reviews/<book>/<run>``."""

    run = _safe_segment(run_id or _default_run_id())
    root = _validate_output_root(Path(output_root))
    out_dir = root / _safe_segment(book_id) / run
    sio = StateIO(book_id, state_root=state_root, autoload=True)
    payload = build_review_report(
        book_id,
        run_id=run,
        state=sio.state,
        state_dir=sio.state_dir,
        rubric_profile=rubric_profile,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(_render_markdown(payload), encoding="utf-8")
    return {
        "status": payload["status"],
        "book_id": book_id,
        "run_id": run,
        "output_dir": str(out_dir),
        "issue_count": payload["summary"]["issue_count"],
    }


def build_review_report(
    book_id: str,
    *,
    run_id: str,
    state: dict[str, dict[str, Any]],
    state_dir: Path,
    rubric_profile: str = DEFAULT_RUBRIC_ID,
) -> dict[str, Any]:
    """Build a deterministic review report without mutating source inputs."""

    chapters = _load_chapters(state_dir)
    issues = _scan_chapters(chapters)
    status = "warn" if issues else "pass"
    return {
        "kind": "ReviewDeslopReport",
        "book_id": book_id,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "passed": not issues,
        "mode": "warn_only",
        "auto_edit": False,
        "projection": {
            "kind": "ReviewDeslop",
            "truth_source": "StateIO",
            "is_state_truth": False,
            "writes_runtime_state": False,
            "output_boundary": ".ops/reviews/<book_id>/<run_id>/",
        },
        "rubric": {
            "id": rubric_profile,
            "scope": "report_only",
            "enters_creation_prompt": False,
            "categories": [
                "anti_ai_style",
                "platform_genre_fit",
                "webnovel_readability",
            ],
        },
        "data_sources": {
            "state_dir": str(state_dir),
            "state_domains": ["locked", "entity_runtime", "workspace", "retrieved", "audit_log"],
            "chapter_artifacts": [chapter["path"] for chapter in chapters],
            "forbidden_default_sources": [".ops/book_analysis/**", ".ops/market_research/**", ".ops/external_sources/**"],
        },
        "context": _context_summary(state),
        "summary": {
            "chapter_count": len(chapters),
            "issue_count": len(issues),
            "warn_count": sum(1 for issue in issues if issue["severity"] == "warn"),
            "error_count": 0,
        },
        "issues": issues,
        "suggestions": _suggestions_from_issues(issues),
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
                "text": text,
            }
        )
    return chapters


def _scan_chapters(chapters: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for chapter in chapters:
        text = chapter.get("text", "")
        issues.extend(_scan_patterns(chapter, text))
        if len(_body_paragraphs(text)) < 3 and len(text.strip()) >= 80:
            issues.append(
                _issue(
                    chapter,
                    code="thin_scene_flow",
                    category="webnovel_readability",
                    message="章节段落密度偏低，可能缺少连续场景推进。",
                    evidence="paragraph_count<3",
                )
            )
    return issues


def _scan_patterns(chapter: dict[str, Any], text: str) -> list[dict[str, Any]]:
    patterns = (
        ("anti_ai_style", "generic_emotion", r"说不出的感觉|难以言喻|复杂的情绪", "抽象情绪替代具体动作。"),
        ("anti_ai_style", "cliche_metaphor", r"命运的齿轮|内心深处|仿佛.*?命运", "常见套话削弱场景质感。"),
        ("anti_ai_style", "abrupt_transition", r"突然|猛然|下一秒", "高频突转词需要确认是否由动作因果支撑。"),
        ("platform_genre_fit", "game_system_tone", r"系统提示|叮|恭喜获得|任务完成", "游戏系统播报腔与当前风格锁冲突。"),
        ("platform_genre_fit", "light_novel_meta", r"吐槽|不会吧|这也太", "轻小说吐槽腔与当前风格锁冲突。"),
    )
    issues: list[dict[str, Any]] = []
    for category, code, pattern, message in patterns:
        for match in re.finditer(pattern, text):
            issues.append(
                _issue(
                    chapter,
                    code=code,
                    category=category,
                    message=message,
                    evidence=_evidence(text, match.start(), match.end()),
                )
            )
    return issues


def _issue(
    chapter: dict[str, Any],
    *,
    code: str,
    category: str,
    message: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "severity": "warn",
        "category": category,
        "code": code,
        "chapter": chapter.get("name", ""),
        "message": message,
        "evidence": evidence,
        "action": "review_manually",
    }


def _suggestions_from_issues(issues: list[dict[str, Any]]) -> list[str]:
    suggestions: list[str] = []
    categories = {issue["category"] for issue in issues}
    if "anti_ai_style" in categories:
        suggestions.append("把抽象心理和套话改成可观察动作、身体代价、环境反馈或对手反应。")
    if "platform_genre_fit" in categories:
        suggestions.append("平台风格冲突只做人工复核提示；如需改文，另开编辑流程，不由 review 自动写回。")
    if "webnovel_readability" in categories:
        suggestions.append("检查段落是否形成连续场景链：目标、阻力、动作、代价、反转。")
    return suggestions


def _context_summary(state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    locked = state.get("locked", {})
    genre = locked.get("GENRE_LOCKED", {}) or {}
    story = locked.get("STORY_DNA", {}) or {}
    return {
        "topic": genre.get("topic", []),
        "forbidden_styles": (genre.get("style_lock") or {}).get("forbidden_styles", []),
        "anchor_phrases": (genre.get("style_lock") or {}).get("anchor_phrases", []),
        "premise_present": bool(story.get("premise")),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Review: {payload['book_id']}",
        "",
        "> Warn-only sidecar. It never edits chapter text or runtime_state.",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- status: `{payload['status']}`",
        f"- rubric: `{payload['rubric']['id']}` ({payload['rubric']['scope']})",
        f"- issues: {payload['summary']['issue_count']}",
        "",
        "## Issues",
        "",
    ]
    if not payload["issues"]:
        lines.append("- none")
    for issue in payload["issues"]:
        lines.append(
            f"- `{issue['chapter']}` `{issue['code']}` [{issue['category']}]: "
            f"{issue['message']} Evidence: {issue['evidence']}"
        )
    lines.extend(["", "## Suggestions", ""])
    if not payload["suggestions"]:
        lines.append("- none")
    for suggestion in payload["suggestions"]:
        lines.append(f"- {suggestion}")
    lines.append("")
    return "\n".join(lines)


def _validate_output_root(root: Path) -> Path:
    normalized = root.as_posix().rstrip("/")
    if not (normalized == ".ops/reviews" or normalized.endswith("/.ops/reviews")):
        raise ReviewError("Review output_root must be .ops/reviews")
    return root


def _safe_segment(value: str) -> str:
    if not value or "/" in value or ".." in value:
        raise ReviewError(f"invalid path segment: {value!r}")
    return value


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _body_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _evidence(text: str, start: int, end: int, radius: int = 18) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[left:right]).strip()


__all__ = [
    "DEFAULT_OUTPUT_ROOT",
    "DEFAULT_RUBRIC_ID",
    "ReviewError",
    "build_review_report",
    "export_review_report",
]
