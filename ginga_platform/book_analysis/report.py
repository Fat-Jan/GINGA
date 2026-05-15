"""Markdown report rendering for Reference Corpus P0."""

from __future__ import annotations

from typing import Any, Mapping

from .manifest import SOURCE_MARKER


def render_scan_report(
    manifest: Mapping[str, Any],
    chapter_index: list[Mapping[str, Any]] | None = None,
    split_result: Mapping[str, Any] | None = None,
) -> str:
    """Render a structure-only Markdown report.

    The report deliberately excludes source excerpts and chapter body text. It
    only names structural fields, counts, hashes, statuses, and anomalies.
    """

    source = manifest.get("source", {})
    chapters = manifest.get("chapters", {})
    resources = manifest.get("resources", {})
    validation = manifest.get("validation", {})
    anomalies = chapters.get("anomalies", [])
    if chapter_index is None and split_result is not None:
        raw_chapters = split_result.get("chapters", [])
        chapter_index = raw_chapters if isinstance(raw_chapters, list) else None
    chapter_count = len(chapter_index) if chapter_index is not None else chapters.get("count", 0)

    lines = [
        SOURCE_MARKER,
        "",
        "# Reference Corpus P0 Scan Report",
        "",
        "## Source",
        f"- title: {source.get('title', '')}",
        f"- path: {source.get('path', '')}",
        f"- sha256: {source.get('sha256', '')}",
        f"- encoding: {source.get('encoding', '')}",
        f"- input_size_bytes: {source.get('input_size_bytes', 0)}",
        f"- source_kind: {source.get('source_kind', '')}",
        "",
        "## Split",
        "- 结构: scan / split / manifest only; no source excerpt is included",
        f"- chapter_count: {chapter_count}",
        f"- numbering_ok: {chapters.get('numbering_ok', False)}",
        f"- heading_pattern_recorded: {bool(chapters.get('heading_pattern'))}",
        "",
        "## Resources",
        f"- elapsed_seconds: {resources.get('elapsed_seconds', 0)}",
        f"- excerpt_chars_saved: {resources.get('excerpt_chars_saved', 0)}",
        f"- private_cache_bytes: {resources.get('private_cache_bytes', 0)}",
        f"- stop_reason: {resources.get('stop_reason', '')}",
        "",
        "## Validation",
        f"- status: {validation.get('status', '')}",
        f"- error_count: {len(validation.get('errors', []))}",
        f"- warning_count: {len(validation.get('warnings', []))}",
        "",
        "## Chapter Anomalies",
    ]
    if anomalies:
        for item in anomalies:
            lines.append(
                f"- {item.get('severity', 'warning')}: {item.get('code', '')}"
                f" ({item.get('chapter_ref', '')}) {item.get('message', '')}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
