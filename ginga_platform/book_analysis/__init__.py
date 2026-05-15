"""Pure helpers for Reference Corpus P0 book-analysis runs."""

from .limits import BookAnalysisLimits, DEFAULT_LIMITS
from .chapter_atoms import extract_chapter_atoms, write_chapter_atoms_run
from .corpus import build_chapter_atoms, build_reference_corpus, build_source_manifest, scan_source
from .report import render_scan_report
from .scan import SourceScanResult, scan_source_bytes
from .split import ChapterEntry, SplitResult, split_chapters
from .validation import (
    validate_chapter_index_payload,
    validate_manifest_dict,
    validate_manifest_payload,
    validate_reference_corpus,
)

__all__ = [
    "BookAnalysisLimits",
    "ChapterEntry",
    "DEFAULT_LIMITS",
    "SourceScanResult",
    "SplitResult",
    "build_reference_corpus",
    "build_chapter_atoms",
    "build_source_manifest",
    "extract_chapter_atoms",
    "render_scan_report",
    "scan_source",
    "scan_source_bytes",
    "split_chapters",
    "validate_chapter_index_payload",
    "validate_manifest_dict",
    "validate_manifest_payload",
    "validate_reference_corpus",
    "write_chapter_atoms_run",
]
