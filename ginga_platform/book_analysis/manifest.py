"""Manifest construction for Reference Corpus P0."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .limits import BookAnalysisLimits, DEFAULT_LIMITS
from .scan import SourceScanResult
from .split import SplitResult


SCHEMA_VERSION = "0.1.0"
SOURCE_MARKER = "[SOURCE_TROPE]"


def build_source_manifest(
    *,
    run_id: str,
    created_at: datetime | str | None,
    scan: SourceScanResult,
    split: SplitResult,
    output_root: str,
    manifest_path: str,
    chapter_index_path: str,
    report_path: str,
    elapsed_seconds: float,
    limits: BookAnalysisLimits = DEFAULT_LIMITS,
    configured_limits: BookAnalysisLimits | None = None,
    override_source: str = "default",
    validator: str = "not_run",
    keyword_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a source_manifest payload from scan and split results.

    The payload includes P0 pollution and resource fields by construction. It
    does not write files and does not include source text.
    """

    active_limits = configured_limits or limits
    validation_errors = list(scan.errors) + list(split.errors)
    validation_warnings = list(scan.warnings) + list(split.warnings)
    validation_status = _validation_status(scan.status, split.status, validation_errors, validation_warnings)

    payload: dict[str, Any] = {
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "created_at": _format_created_at(created_at),
        "source": scan.to_source_payload(),
        "output": {
            "root": output_root,
            "manifest_path": manifest_path,
            "chapter_index_path": chapter_index_path,
            "report_path": report_path,
            "private_evidence_path": None,
        },
        "chapters": split.to_chapters_payload(chapter_index_path),
        "resources": {
            "input_size_bytes": scan.input_size_bytes,
            "chapter_count": len(split.chapters),
            "elapsed_seconds": elapsed_seconds,
            "excerpt_chars_saved": 0,
            "private_cache_bytes": 0,
            "degraded": validation_status in {"failed", "completed_with_errors"},
            "stop_reason": _stop_reason(scan.status, split.status, validation_errors),
        },
        "keyword_sources": {
            "active": False,
            "allowed_source_types": ["explicit_config", "user_input", "approved_pattern_seed"],
            "entries": keyword_entries or [],
            "prohibited_sources": [
                "hardcoded",
                "unaudited_reference_text",
                "proper_noun_auto_extract",
            ],
        },
        "pollution": {
            "pollution_source": True,
            "source_marker": SOURCE_MARKER,
            "default_rag_excluded": True,
            "prompt_injection_allowed": False,
            "runtime_state_write_allowed": False,
            "raw_ideas_write_allowed": False,
            "default_input_whitelist_allowed": False,
        },
        "validation": {
            "validator": validator,
            "status": validation_status,
            "errors": _messages(validation_errors),
            "warnings": _messages(validation_warnings),
        },
        "limits": {
            "defaults": DEFAULT_LIMITS.to_dict(),
            "configured": active_limits.to_dict(),
            "override_source": override_source,
        },
    }
    return payload


def _validation_status(
    scan_status: str,
    split_status: str,
    errors: list[Mapping[str, Any]],
    warnings: list[Mapping[str, Any]],
) -> str:
    if errors or scan_status == "error" or split_status == "error":
        return "failed"
    if warnings or scan_status == "warning" or split_status == "warning":
        return "warning"
    return "not_run"


def _stop_reason(scan_status: str, split_status: str, errors: list[Mapping[str, Any]]) -> str:
    if scan_status != "error" and split_status != "error":
        return "completed"
    for item in errors:
        code = str(item.get("code", ""))
        if code in {
            "input_too_large",
            "too_many_chapters",
            "encoding_error",
            "no_chapter_heading",
            "output_boundary_violation",
            "validation_error",
        }:
            return code
    return "validation_error"


def _messages(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(item) for item in items]


def _format_created_at(value: datetime | str | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
