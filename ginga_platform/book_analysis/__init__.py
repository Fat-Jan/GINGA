"""Pure helpers for Reference Corpus and reviewed trope promotion runs."""

from .limits import BookAnalysisLimits, DEFAULT_LIMITS
from .chapter_atoms import extract_chapter_atoms, write_chapter_atoms_run
from .corpus import (
    build_chapter_atoms,
    build_reference_corpus,
    build_source_manifest,
    build_trope_recipes,
    promote_trope_recipes,
    scan_source,
)
from .promote import promote_trope_recipes as promote_trope_recipes_from_payload
from .report import render_scan_report
from .scan import SourceScanResult, scan_source_bytes
from .split import ChapterEntry, SplitResult, split_chapters
from .trope_recipes import extract_trope_recipe_candidates, write_trope_recipe_run
from .validation import (
    validate_chapter_index_payload,
    validate_chapter_atoms_run,
    validate_manifest_dict,
    validate_manifest_payload,
    validate_promoted_trope_assets,
    validate_reference_corpus,
    validate_trope_recipe_run,
)

__all__ = [
    "BookAnalysisLimits",
    "ChapterEntry",
    "DEFAULT_LIMITS",
    "SourceScanResult",
    "SplitResult",
    "build_reference_corpus",
    "build_chapter_atoms",
    "build_trope_recipes",
    "build_source_manifest",
    "extract_chapter_atoms",
    "extract_trope_recipe_candidates",
    "promote_trope_recipes",
    "promote_trope_recipes_from_payload",
    "render_scan_report",
    "scan_source",
    "scan_source_bytes",
    "split_chapters",
    "validate_chapter_index_payload",
    "validate_chapter_atoms_run",
    "validate_manifest_dict",
    "validate_manifest_payload",
    "validate_promoted_trope_assets",
    "validate_reference_corpus",
    "validate_trope_recipe_run",
    "write_chapter_atoms_run",
    "write_trope_recipe_run",
]
