"""Longform generation policy derived from v1.7 smoke evidence."""

from __future__ import annotations

DEFAULT_CHAPTER_BATCH_SIZE = 5
MAX_REAL_LLM_CHAPTER_BATCH_SIZE = 7
PRESSURE_TEST_BATCH_SIZE = 10


def validate_real_llm_batch_size(chapters: int, *, mock_llm: bool = False) -> None:
    """Fail real LLM longform batches that exceed the v1.7 measured upper bound."""

    if mock_llm or chapters <= MAX_REAL_LLM_CHAPTER_BATCH_SIZE:
        return
    raise ValueError(
        f"real LLM chapter batch too large: {chapters}. "
        f"Use <= {MAX_REAL_LLM_CHAPTER_BATCH_SIZE} for production, "
        f"{DEFAULT_CHAPTER_BATCH_SIZE} recommended; "
        f"{PRESSURE_TEST_BATCH_SIZE}+ is pressure-test only."
    )


__all__ = [
    "DEFAULT_CHAPTER_BATCH_SIZE",
    "MAX_REAL_LLM_CHAPTER_BATCH_SIZE",
    "PRESSURE_TEST_BATCH_SIZE",
    "validate_real_llm_batch_size",
]
