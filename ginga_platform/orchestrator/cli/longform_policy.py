"""Longform generation policy derived from v1.7 smoke evidence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_CHAPTER_BATCH_SIZE = 4
MAX_REAL_LLM_CHAPTER_BATCH_SIZE = 5
PRESSURE_TEST_BATCH_SIZE = 6
MIN_SUBMISSION_CHINESE_CHARS = 3500
BODY_CHINESE_TARGET_MIN = 4200
BODY_CHINESE_TARGET_MAX = 4600
LONGFORM_HARD_GATE_MODE = "block_next_real_llm_batch"
STYLE_WARN_PATTERNS = {
    "generic_emotion": r"说不出的感觉|难以言喻|复杂的情绪",
    "cliche_metaphor": r"命运的齿轮|内心深处|仿佛.*?命运",
    "abrupt_transition": r"突然|猛然|下一秒",
}
HARD_STYLE_WARN_NAMES = frozenset({"generic_emotion", "cliche_metaphor"})
SOFT_STYLE_WARN_NAMES = frozenset({"abrupt_transition"})


def validate_real_llm_batch_size(chapters: int, *, mock_llm: bool = False) -> None:
    """Fail real LLM longform batches that exceed the v1.7-3 human-reviewed upper bound."""

    if mock_llm or chapters <= MAX_REAL_LLM_CHAPTER_BATCH_SIZE:
        return
    raise ValueError(
        f"real LLM chapter batch too large: {chapters}. "
        f"Use <= {MAX_REAL_LLM_CHAPTER_BATCH_SIZE} for production, "
        f"{DEFAULT_CHAPTER_BATCH_SIZE} recommended; "
        f"{PRESSURE_TEST_BATCH_SIZE}+ is pressure-test only."
    )


def evaluate_longform_hard_gate(
    *,
    state: dict[str, dict[str, Any]],
    chapters: list[dict[str, Any]],
    window_size: int = DEFAULT_CHAPTER_BATCH_SIZE,
) -> dict[str, Any]:
    """Evaluate whether the next real LLM batch should be blocked.

    The gate is intentionally conservative after the v1.7-2 reviewer queue
    review: recent repeated opening loops, missing low-frequency anchors, or
    missing foreshadow markers require human/policy repair before another real
    generation batch.
    """

    recent = chapters[-window_size:] if window_size > 0 else list(chapters)
    anchors = low_frequency_anchors(state)
    chapter_checks = [
        longform_chapter_gate_check(chapter=chapter, low_frequency_anchors=anchors)
        for chapter in recent
    ]
    block_reasons: list[str] = []
    consecutive_opening_loop = 0
    max_consecutive_opening_loop = 0
    for check in chapter_checks:
        if check["opening_loop_risk"]:
            consecutive_opening_loop += 1
            max_consecutive_opening_loop = max(max_consecutive_opening_loop, consecutive_opening_loop)
        else:
            consecutive_opening_loop = 0
    if max_consecutive_opening_loop >= 2:
        block_reasons.append("consecutive_opening_loop_risk")
    if any(check["missing_low_frequency_anchor"] for check in chapter_checks):
        block_reasons.append("missing_low_frequency_anchor")
    if any(check["missing_foreshadow_marker"] for check in chapter_checks):
        block_reasons.append("missing_foreshadow_marker")
    return {
        "enabled": True,
        "mode": LONGFORM_HARD_GATE_MODE,
        "window_size": window_size,
        "inspected_chapters": [check["chapter"] for check in chapter_checks],
        "low_frequency_anchors": anchors,
        "block_reasons": block_reasons,
        "should_block_next_real_llm_batch": bool(block_reasons),
        "chapter_checks": chapter_checks,
    }


def validate_longform_hard_gate(
    *,
    state: dict[str, dict[str, Any]],
    chapters: list[dict[str, Any]],
    mock_llm: bool = False,
) -> None:
    """Fail before a real LLM call if recent chapter evidence violates the hard gate."""

    if mock_llm or not chapters:
        return
    gate = evaluate_longform_hard_gate(state=state, chapters=chapters)
    if not gate["should_block_next_real_llm_batch"]:
        return
    inspected = ", ".join(gate["inspected_chapters"])
    reasons = ", ".join(gate["block_reasons"])
    raise ValueError(
        "longform hard gate blocks next real LLM batch: "
        f"{reasons}; inspected={inspected}. "
        "Review/fix recent chapters or rerun with mock/test mode only."
    )


def load_chapter_artifacts(state_dir: Path) -> list[dict[str, Any]]:
    """Load chapter artifacts in the lightweight shape used by review/policy gates."""

    chapters: list[dict[str, Any]] = []
    for path in sorted(state_dir.glob("chapter_*.md")):
        text = path.read_text(encoding="utf-8")
        chapters.append({"name": path.name, "path": str(path), "text": text, "chars": len(text)})
    return chapters


def low_frequency_anchors(state: dict[str, dict[str, Any]]) -> list[str]:
    state_anchors = (
        ((state.get("locked", {}).get("GENRE_LOCKED") or {}).get("style_lock") or {}).get("anchor_phrases")
        or []
    )
    locked = state.get("locked", {}) or {}
    genre = locked.get("GENRE_LOCKED") or {}
    story = locked.get("STORY_DNA") or {}
    source_text = " ".join(
        [
            " ".join(str(item) for item in genre.get("topic", [])),
            str(story.get("premise", "")),
            str(story.get("conflict_engine", "")),
        ]
    )
    candidates = ("血脉", "末日", "多子多福", "繁衍契约")
    anchors = [anchor for anchor in candidates if anchor in state_anchors or anchor in source_text]
    return anchors or [anchor for anchor in state_anchors if anchor in {"血脉", "末日"}]


def longform_chapter_gate_check(
    *,
    chapter: dict[str, Any],
    low_frequency_anchors: list[str],
) -> dict[str, Any]:
    text = chapter.get("text", "")
    body_text = extract_chapter_body_text(text)
    chapter_no = _chapter_number(chapter)
    return {
        "chapter": chapter.get("name", ""),
        "opening_loop_risk": chapter_no > 1 and opening_loop_score(body_text) >= 3,
        "missing_low_frequency_anchor": bool(low_frequency_anchors)
        and not any(anchor in body_text for anchor in low_frequency_anchors),
        "missing_foreshadow_marker": "<!-- foreshadow:" not in text,
        "short_chapter": count_chinese(body_text) < MIN_SUBMISSION_CHINESE_CHARS,
        "forbidden_hits": longform_forbidden_hits(body_text),
        "soft_style_warn": soft_style_warn_hits(body_text),
    }


def _chapter_number(chapter: dict[str, Any]) -> int:
    raw = chapter.get("chapter_no") or (chapter.get("payload") or {}).get("chapter_no")
    try:
        if raw:
            return int(raw)
    except (TypeError, ValueError):
        pass
    match = re.search(r"chapter_(\d+)\.md$", str(chapter.get("name", "") or chapter.get("path", "")))
    return int(match.group(1)) if match else 0


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def extract_chapter_body_text(text: str) -> str:
    """Return only prose body text, excluding markdown overhead and sidecar comments."""

    without_comments = strip_html_comments(text)
    body_lines: list[str] = []
    for raw_line in without_comments.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("|"):
            continue
        body_lines.append(raw_line)
    return "\n".join(body_lines)


def count_chinese(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def longform_forbidden_hits(text: str) -> dict[str, int]:
    terms = ("系统提示", "叮", "恭喜获得", "都市腔", "轻小说吐槽")
    return {term: text.count(term) for term in terms if text.count(term)}


def style_warn_hits(text: str) -> dict[str, int]:
    return {
        name: len(matches)
        for name, pattern in STYLE_WARN_PATTERNS.items()
        if (matches := re.findall(pattern, text))
    }


def hard_style_warn_hits(text: str) -> dict[str, int]:
    return {name: count for name, count in style_warn_hits(text).items() if name in HARD_STYLE_WARN_NAMES}


def soft_style_warn_hits(text: str) -> dict[str, int]:
    return {name: count for name, count in style_warn_hits(text).items() if name in SOFT_STYLE_WARN_NAMES}


def opening_loop_score(text: str) -> int:
    opening = first_body_excerpt(text, limit=900)
    signal_patterns = (
        r"醒来|睁开眼",
        r"天堑边缘|废墟|灰白",
        r"体内.{0,12}微粒|微粒.{0,12}体内",
        r"失忆|记忆.{0,8}空白|不记得",
        r"短刃",
    )
    return sum(1 for pattern in signal_patterns if re.search(pattern, opening))


def first_body_excerpt(text: str, *, limit: int = 160) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("|") and not line.strip().startswith("#")
    ]
    return (" ".join(lines) or text.strip())[:limit]


__all__ = [
    "DEFAULT_CHAPTER_BATCH_SIZE",
    "BODY_CHINESE_TARGET_MAX",
    "BODY_CHINESE_TARGET_MIN",
    "HARD_STYLE_WARN_NAMES",
    "LONGFORM_HARD_GATE_MODE",
    "MAX_REAL_LLM_CHAPTER_BATCH_SIZE",
    "PRESSURE_TEST_BATCH_SIZE",
    "SOFT_STYLE_WARN_NAMES",
    "STYLE_WARN_PATTERNS",
    "count_chinese",
    "evaluate_longform_hard_gate",
    "extract_chapter_body_text",
    "first_body_excerpt",
    "hard_style_warn_hits",
    "load_chapter_artifacts",
    "longform_chapter_gate_check",
    "longform_forbidden_hits",
    "low_frequency_anchors",
    "opening_loop_score",
    "soft_style_warn_hits",
    "strip_html_comments",
    "style_warn_hits",
    "validate_longform_hard_gate",
    "validate_real_llm_batch_size",
]
