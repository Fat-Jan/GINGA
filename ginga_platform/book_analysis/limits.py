"""Resource limits for Reference Corpus P0.

The defaults mirror `.ops/book_analysis/p0_mvp_boundary.md` and are kept in a
small dataclass so callers can pass explicit overrides into pure helpers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Mapping, Any


@dataclass(frozen=True)
class BookAnalysisLimits:
    """Conservative P0 resource limits.

    P0 forbids excerpts and private evidence caches, so those fields remain
    fixed to zero/false even when other limits are overridden.
    """

    max_input_size_bytes: int = 10_485_760
    max_chapters: int = 500
    max_elapsed_seconds: int = 120
    max_chapter_title_chars: int = 120
    max_excerpt_chars: int = 0
    private_cache_enabled: bool = False
    max_private_cache_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/YAML serializable representation."""

        return asdict(self)

    def with_overrides(self, overrides: Mapping[str, Any] | None) -> "BookAnalysisLimits":
        """Return a copy with safe P0 overrides applied.

        Excerpt and private-cache settings cannot be enabled through this
        helper because doing so would violate the P0 contamination boundary.
        """

        if not overrides:
            return self

        allowed = {
            "max_input_size_bytes",
            "max_chapters",
            "max_elapsed_seconds",
            "max_chapter_title_chars",
        }
        clean: dict[str, Any] = {key: overrides[key] for key in allowed if key in overrides}
        return replace(self, **clean)


DEFAULT_LIMITS = BookAnalysisLimits()
