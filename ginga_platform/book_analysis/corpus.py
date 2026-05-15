"""Reference Corpus P0 public API and thin IO wrappers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

from .limits import DEFAULT_LIMITS, BookAnalysisLimits
from .manifest import build_source_manifest as _build_manifest
from .report import render_scan_report
from .scan import SourceScanResult, scan_source_bytes
from .split import ChapterEntry, SplitResult, split_chapters as _split_text
from .chapter_atoms import write_chapter_atoms_run
from .promote import promote_trope_recipes
from .trope_recipes import write_trope_recipe_run


def scan_source(
    source_path: str | Path,
    *,
    encoding: str | None = None,
    title: str | None = None,
    source_kind: str = "user_file",
    limits: Mapping[str, Any] | BookAnalysisLimits | None = None,
) -> dict[str, Any]:
    """Read and scan a source file, returning metadata without source text."""

    path = Path(source_path)
    active_limits = _coerce_limits(limits)
    result = scan_source_bytes(
        path.read_bytes(),
        path=path,
        title=title,
        source_kind=source_kind,
        mtime=path.stat().st_mtime,
        encoding=encoding,
        limits=active_limits,
    )
    return result.to_dict(include_text=False)


def split_chapters(
    source: str | Path,
    *,
    encoding: str | None = None,
    limits: Mapping[str, Any] | BookAnalysisLimits | None = None,
) -> dict[str, Any]:
    """Split a source path or raw text into a compatibility chapter payload."""

    active_limits = _coerce_limits(limits)
    text = Path(source).read_text(encoding=encoding or "utf-8") if _looks_like_existing_path(source) else str(source)
    return _split_payload_for_contract(_split_text(text, limits=active_limits))


def build_source_manifest(
    *,
    run_id: str,
    source: Mapping[str, Any] | SourceScanResult,
    split_result: Mapping[str, Any] | SplitResult,
    output_root: str | Path,
    elapsed_seconds: float,
    created_at: Any = None,
    limits: Mapping[str, Any] | BookAnalysisLimits | None = None,
) -> dict[str, Any]:
    """Build a P0 manifest from dict or dataclass inputs."""

    active_limits = _coerce_limits(limits)
    scan = source if isinstance(source, SourceScanResult) else _scan_result_from_meta(source)
    split = split_result if isinstance(split_result, SplitResult) else _split_result_from_payload(split_result)
    root = str(output_root)
    return _build_manifest(
        run_id=run_id,
        created_at=created_at,
        scan=scan,
        split=split,
        output_root=root,
        manifest_path=str(Path(root) / "source_manifest.json"),
        chapter_index_path=str(Path(root) / "chapter_index.json"),
        report_path=str(Path(root) / "scan_report.md"),
        elapsed_seconds=elapsed_seconds,
        configured_limits=active_limits,
        override_source="explicit_config" if limits else "default",
        validator="ginga_platform.book_analysis.validation.validate_reference_corpus",
    )


def build_reference_corpus(
    *,
    source_path: str | Path,
    run_id: str,
    output_base: str | Path,
    encoding: str | None = None,
    title: str | None = None,
    source_kind: str = "user_file",
    limits: Mapping[str, Any] | BookAnalysisLimits | None = None,
) -> Path:
    """Build P0 run outputs under `.ops/book_analysis/<run_id>`."""

    started = time.monotonic()
    active_limits = _coerce_limits(limits)
    source_path = Path(source_path)
    run_root = Path(output_base) / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    scan = scan_source_bytes(
        source_path.read_bytes(),
        path=source_path,
        mtime=source_path.stat().st_mtime,
        encoding=encoding,
        title=title,
        source_kind=source_kind,
        limits=active_limits,
    )
    split = _split_text(scan.text or "", limits=active_limits)
    elapsed = time.monotonic() - started
    manifest = _build_manifest(
        run_id=run_id,
        created_at=None,
        scan=scan,
        split=split,
        output_root=str(run_root),
        manifest_path=str(run_root / "source_manifest.json"),
        chapter_index_path=str(run_root / "chapter_index.json"),
        report_path=str(run_root / "scan_report.md"),
        elapsed_seconds=elapsed,
        configured_limits=active_limits,
        override_source="explicit_config" if limits else "default",
        validator="ginga_platform.book_analysis.validation.validate_reference_corpus",
    )

    chapter_index = split.chapter_index_payload()
    (run_root / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_root / "chapter_index.json").write_text(json.dumps(chapter_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_root / "scan_report.md").write_text(render_scan_report(manifest, chapter_index=chapter_index), encoding="utf-8")
    return run_root


def build_chapter_atoms(*, source_run_root: str | Path, run_id: str, output_base: str | Path) -> Path:
    """Build v1.3-2 Chapter Atom sidecar outputs from a P0 run."""

    return write_chapter_atoms_run(source_run_root=source_run_root, run_id=run_id, output_base=output_base)


def build_trope_recipes(*, source_atom_run_root: str | Path, run_id: str, output_base: str | Path) -> Path:
    """Build v1.3-3 Trope Recipe Candidate sidecar outputs from a chapter atom run."""

    return write_trope_recipe_run(source_atom_run_root=source_atom_run_root, run_id=run_id, output_base=output_base)


def _coerce_limits(value: Mapping[str, Any] | BookAnalysisLimits | None) -> BookAnalysisLimits:
    if isinstance(value, BookAnalysisLimits):
        return value
    return DEFAULT_LIMITS.with_overrides(value)


def _looks_like_existing_path(value: str | Path) -> bool:
    try:
        return Path(value).exists()
    except OSError:
        return False


def _split_payload_for_contract(result: SplitResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "chapters": [_chapter_for_contract(chapter) for chapter in result.chapters],
        "anomalies": list(result.anomalies),
        "warnings": list(result.warnings),
        "errors": list(result.errors),
        "heading_pattern": result.heading_pattern,
        "numbering_ok": result.numbering_ok,
    }


def _chapter_for_contract(chapter: ChapterEntry) -> dict[str, Any]:
    return {
        "index": int(chapter.chapter_id.split("-")[-1]),
        "chapter_id": chapter.chapter_id,
        "chapter_no": chapter.chapter_no,
        "title": _display_title(chapter.title),
        "start_offset": chapter.start_offset,
        "end_offset": chapter.end_offset,
        "char_count": chapter.char_count,
        "sha256": chapter.sha256,
        "anomalies": list(chapter.anomalies),
    }


def _display_title(title: str) -> str:
    return title.split(maxsplit=1)[1].strip() if " " in title else title


def _scan_result_from_meta(source: Mapping[str, Any]) -> SourceScanResult:
    return SourceScanResult(
        status=str(source.get("status", "ok")),
        path=str(source.get("path", "")),
        sha256=str(source.get("sha256", "")),
        input_size_bytes=int(source.get("input_size_bytes", 0)),
        encoding=str(source.get("encoding", "")),
        title=str(source.get("title", "")),
        source_kind=str(source.get("source_kind", "user_file")),
        text=None,
        original_mtime=source.get("original_mtime"),
        errors=tuple(source.get("errors", ())),
        warnings=tuple(source.get("warnings", ())),
    )


def _split_result_from_payload(payload: Mapping[str, Any]) -> SplitResult:
    chapters = []
    for idx, item in enumerate(payload.get("chapters", []), start=1):
        chapters.append(
            ChapterEntry(
                chapter_id=str(item.get("chapter_id", f"ch-{idx:04d}")),
                chapter_no=item.get("chapter_no") or item.get("index"),
                title=str(item.get("title", "")),
                start_offset=int(item.get("start_offset", 0)),
                end_offset=int(item.get("end_offset", 0)),
                char_count=int(item.get("char_count", 0)),
                sha256=str(item.get("sha256", "")),
                anomalies=tuple(item.get("anomalies", ())),
            )
        )
    return SplitResult(
        status=str(payload.get("status", "ok")),
        chapters=tuple(chapters),
        anomalies=tuple(payload.get("anomalies", ())),
        heading_pattern=str(payload.get("heading_pattern", "")),
        errors=tuple(payload.get("errors", ())),
        warnings=tuple(payload.get("warnings", ())),
    )
