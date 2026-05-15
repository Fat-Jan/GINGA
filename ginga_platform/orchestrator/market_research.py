"""Explicitly authorized Market Research sidecar reports.

The v1.6 sidecar starts with offline fixtures only. It summarizes market
signals and source metadata, strips raw external text, and never writes
runtime_state or default RAG inputs.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = Path(".ops/market_research")


class MarketResearchError(RuntimeError):
    """Market Research sidecar contract error."""


def export_market_research_report(
    book_id: str,
    *,
    run_id: str | None = None,
    fixture_path: str | Path,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    authorized: bool = False,
) -> dict[str, Any]:
    """Write an authorized offline-fixture market report sidecar."""

    if not authorized:
        raise MarketResearchError("explicit authorization is required for market research sidecar")
    run = _safe_segment(run_id or _default_run_id())
    root = _validate_output_root(Path(output_root))
    fixture = _load_fixture(Path(fixture_path))
    payload = build_market_research_report(book_id, run_id=run, fixture=fixture, fixture_path=Path(fixture_path))

    out_dir = root / _safe_segment(book_id) / run
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "market_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(_render_markdown(payload), encoding="utf-8")
    return {
        "status": "exported",
        "book_id": book_id,
        "run_id": run,
        "output_dir": str(out_dir),
        "signal_count": len(payload["market_signals"]),
    }


def build_market_research_report(
    book_id: str,
    *,
    run_id: str,
    fixture: dict[str, Any],
    fixture_path: Path,
) -> dict[str, Any]:
    """Build a sanitized market report from an offline fixture."""

    sources = [_source_summary(source) for source in _fixture_sources(fixture)]
    items = [item for source in _fixture_sources(fixture) for item in _source_items(source)]
    market_signals = _market_signals(items)
    return {
        "kind": "MarketResearchSidecarReport",
        "book_id": book_id,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "collection_mode": "offline_fixture",
        "authorization": {
            "explicit": True,
            "required": True,
            "scope": "offline_fixture_only",
        },
        "projection": {
            "kind": "MarketResearchSidecar",
            "is_state_truth": False,
            "writes_runtime_state": False,
            "output_boundary": ".ops/market_research/<book_id>/<run_id>/",
        },
        "rag_policy": {
            "default_rag_eligible": False,
            "external_raw_text_included": False,
            "forbidden_default_sources": [".ops/market_research/**", ".ops/external_sources/**"],
        },
        "fixture": {
            "path": str(fixture_path),
            "fixture_id": fixture.get("fixture_id", ""),
            "collected_at": fixture.get("collected_at", ""),
        },
        "sources": sources,
        "market_signals": market_signals,
        "ranked_items": [_sanitize_item(item) for item in items],
    }


def _load_fixture(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise MarketResearchError(f"fixture not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarketResearchError(f"fixture must be JSON: {path}") from exc
    if not isinstance(data, dict):
        raise MarketResearchError("fixture root must be an object")
    if not isinstance(data.get("sources"), list):
        raise MarketResearchError("fixture.sources must be a list")
    return data


def _fixture_sources(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return [source for source in fixture.get("sources", []) if isinstance(source, dict)]


def _source_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in source.get("items", []) if isinstance(item, dict)]


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    required = ("source_id", "platform", "collected_at", "data_quality")
    missing = [field for field in required if not source.get(field)]
    if missing:
        raise MarketResearchError(f"source missing required field(s): {missing}")
    return {
        "source_id": str(source.get("source_id", "")),
        "platform": str(source.get("platform", "")),
        "url": str(source.get("url", "")),
        "collected_at": str(source.get("collected_at", "")),
        "data_quality": str(source.get("data_quality", "")),
        "item_count": len(_source_items(source)),
    }


def _market_signals(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    genres: Counter[str] = Counter()
    for item in items:
        genre = str(item.get("genre", "")).strip()
        if genre:
            genres[genre] += 1
        for signal in item.get("signals", []) if isinstance(item.get("signals"), list) else []:
            value = str(signal).strip()
            if value:
                counter[value] += 1

    signals: list[dict[str, Any]] = []
    for value, count in counter.most_common():
        signals.append({"type": "signal", "value": value, "count": count})
    for value, count in genres.most_common():
        signals.append({"type": "genre", "value": value, "count": count})
    return signals


def _sanitize_item(item: dict[str, Any]) -> dict[str, Any]:
    allowed = ("rank", "title", "genre", "signals", "summary")
    sanitized = {key: item.get(key) for key in allowed if key in item}
    sanitized["raw_text_included"] = False
    return sanitized


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Market Research: {payload['book_id']}",
        "",
        "> Explicitly authorized sidecar. External raw text is stripped and default RAG remains ineligible.",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- collection_mode: `{payload['collection_mode']}`",
        f"- fixture_collected_at: {payload['fixture'].get('collected_at', '')}",
        f"- sources: {len(payload['sources'])}",
        f"- signals: {len(payload['market_signals'])}",
        "",
        "## Sources",
        "",
    ]
    for source in payload["sources"]:
        lines.append(
            f"- `{source['source_id']}` {source['platform']} "
            f"collected_at={source['collected_at']} quality={source['data_quality']} items={source['item_count']}"
        )
    lines.extend(["", "## Signals", ""])
    if not payload["market_signals"]:
        lines.append("- none")
    for signal in payload["market_signals"]:
        lines.append(f"- {signal['type']}: {signal['value']} ({signal['count']})")
    lines.append("")
    return "\n".join(lines)


def _validate_output_root(root: Path) -> Path:
    normalized = root.as_posix().rstrip("/")
    if not (normalized == ".ops/market_research" or normalized.endswith("/.ops/market_research")):
        raise MarketResearchError("Market Research output_root must be .ops/market_research")
    return root


def _safe_segment(value: str) -> str:
    if not value or "/" in value or ".." in value:
        raise MarketResearchError(f"invalid path segment: {value!r}")
    return value


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


__all__ = [
    "DEFAULT_OUTPUT_ROOT",
    "MarketResearchError",
    "build_market_research_report",
    "export_market_research_report",
]
