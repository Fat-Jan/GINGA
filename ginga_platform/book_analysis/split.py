"""Chapter splitting helpers for Chinese reference texts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from .limits import BookAnalysisLimits, DEFAULT_LIMITS


HEADING_PATTERN = re.compile(
    r"^[ \t　]*(?P<title>"
    r"第(?P<num>[0-9零〇一二两三四五六七八九十百千万]+)[章节卷回部集][^\n\r]*"
    r"|(?P<special>序章|楔子|番外[^\n\r]{0,80}|后记|尾声|终章)"
    r")[ \t　]*$",
    re.MULTILINE,
)

SPECIAL_WARNING_CODES = {
    "序章": "suspicious_preface",
    "楔子": "suspicious_preface",
    "番外": "suspicious_extra",
    "后记": "suspicious_extra",
    "尾声": "suspicious_extra",
    "终章": "suspicious_extra",
}


@dataclass(frozen=True)
class ChapterEntry:
    """A structural chapter index entry.

    Offsets are Python string character offsets, not byte offsets. The chapter
    hash is computed from the exact split text but the text itself is not kept.
    """

    chapter_id: str
    chapter_no: int | None
    title: str
    start_offset: int
    end_offset: int
    char_count: int
    sha256: str
    anomalies: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable chapter index entry."""

        payload = asdict(self)
        payload["anomalies"] = list(self.anomalies)
        return payload


@dataclass(frozen=True)
class SplitResult:
    """Result of structural chapter splitting."""

    status: str
    chapters: tuple[ChapterEntry, ...]
    anomalies: tuple[dict[str, Any], ...]
    heading_pattern: str
    errors: tuple[dict[str, Any], ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()

    @property
    def numbering_ok(self) -> bool:
        """Return whether numbered chapters form a continuous sequence."""

        numbered = [chapter.chapter_no for chapter in self.chapters if chapter.chapter_no is not None]
        return numbered == list(range(1, len(numbered) + 1))

    def chapter_index_payload(self) -> list[dict[str, Any]]:
        """Return the serializable chapter_index.json payload."""

        return [chapter.to_dict() for chapter in self.chapters]

    def to_chapters_payload(self, chapter_index_path: str) -> dict[str, Any]:
        """Return the manifest `chapters` summary payload."""

        return {
            "count": len(self.chapters),
            "numbering_ok": self.numbering_ok,
            "anomalies": list(self.anomalies),
            "chapter_index_path": chapter_index_path,
            "heading_pattern": self.heading_pattern,
            "index_fields": [
                "chapter_id",
                "chapter_no",
                "title",
                "start_offset",
                "end_offset",
                "char_count",
                "sha256",
                "anomalies",
            ],
        }


def split_chapters(text: str, *, limits: BookAnalysisLimits = DEFAULT_LIMITS) -> SplitResult:
    """Split text by common Chinese chapter headings.

    No synthetic chapter is created when no heading is found; callers receive an
    `error` result with zero chapters.
    """

    matches = list(HEADING_PATTERN.finditer(text))
    if not matches:
        anomaly = {
            "code": "no_chapter_heading",
            "severity": "error",
            "message": "no supported Chinese chapter heading was found",
            "chapter_ref": "",
        }
        return SplitResult(
            status="error",
            chapters=(),
            anomalies=(anomaly,),
            heading_pattern=HEADING_PATTERN.pattern,
            errors=(anomaly,),
        )

    if len(matches) > limits.max_chapters:
        anomaly = {
            "code": "too_many_chapters",
            "severity": "error",
            "message": f"chapter count {len(matches)} exceeds limit {limits.max_chapters}",
            "chapter_ref": "",
        }
        return SplitResult(
            status="error",
            chapters=(),
            anomalies=(anomaly,),
            heading_pattern=HEADING_PATTERN.pattern,
            errors=(anomaly,),
        )

    chapters: list[ChapterEntry] = []
    all_anomalies: list[dict[str, Any]] = []
    seen_titles: dict[str, str] = {}
    previous_no: int | None = None
    numbering_styles: set[str] = set()

    for idx, match in enumerate(matches):
        title = _normalize_title(match.group("title"))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chapter_no = _parse_chapter_no(match.groupdict().get("num"))
        chapter_id = f"ch-{idx + 1:04d}"
        chapter_anomalies: list[dict[str, Any]] = []

        if not title:
            chapter_anomalies.append(_anomaly("empty_title", "warning", "empty chapter title", chapter_id))
        if len(title) > limits.max_chapter_title_chars:
            chapter_anomalies.append(
                _anomaly("long_title", "warning", "chapter title exceeds configured limit", chapter_id)
            )
        if title in seen_titles:
            chapter_anomalies.append(
                _anomaly(
                    "duplicate_title",
                    "warning",
                    f"duplicate title also seen at {seen_titles[title]}",
                    chapter_id,
                )
            )
        else:
            seen_titles[title] = chapter_id

        special_code = _special_code(title)
        if special_code:
            chapter_anomalies.append(_anomaly(special_code, "warning", "special heading requires review", chapter_id))

        if chapter_no is None:
            chapter_anomalies.append(_anomaly("missing_number", "warning", "heading has no numeric chapter number", chapter_id))
        else:
            style = "arabic" if re.search(r"\d", match.group("num") or "") else "chinese"
            numbering_styles.add(style)
            if previous_no is not None and chapter_no <= previous_no:
                chapter_anomalies.append(_anomaly("out_of_order", "warning", "chapter number is not increasing", chapter_id))
            elif previous_no is not None and chapter_no != previous_no + 1:
                chapter_anomalies.append(_anomaly("missing_number", "warning", "chapter numbering is not continuous", chapter_id))
            previous_no = chapter_no

        chapter_text = text[start:end]
        chapters.append(
            ChapterEntry(
                chapter_id=chapter_id,
                chapter_no=chapter_no,
                title=title,
                start_offset=start,
                end_offset=end,
                char_count=len(chapter_text),
                sha256=sha256(chapter_text.encode("utf-8")).hexdigest(),
                anomalies=tuple(chapter_anomalies),
            )
        )
        all_anomalies.extend(chapter_anomalies)

    if len(numbering_styles) > 1:
        mixed = _anomaly("mixed_numbering", "warning", "chapter numbering mixes arabic and Chinese numerals", "")
        all_anomalies.append(mixed)

    status = "warning" if all_anomalies else "ok"
    warnings = tuple(item for item in all_anomalies if item.get("severity") == "warning")
    errors = tuple(item for item in all_anomalies if item.get("severity") == "error")
    if errors:
        status = "error"
    return SplitResult(
        status=status,
        chapters=tuple(chapters),
        anomalies=tuple(all_anomalies),
        heading_pattern=HEADING_PATTERN.pattern,
        errors=errors,
        warnings=warnings,
    )


def _normalize_title(title: str | None) -> str:
    return (title or "").strip(" \t　\r\n")


def _special_code(title: str) -> str | None:
    for prefix, code in SPECIAL_WARNING_CODES.items():
        if title.startswith(prefix):
            return code
    return None


def _anomaly(code: str, severity: str, message: str, chapter_ref: str) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "chapter_ref": chapter_ref}


def _parse_chapter_no(raw: str | None) -> int | None:
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    return _parse_chinese_number(raw)


def _parse_chinese_number(raw: str) -> int | None:
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100, "千": 1000, "万": 10000}
    total = 0
    section = 0
    number = 0
    for char in raw:
        if char in digits:
            number = digits[char]
        elif char in units:
            unit = units[char]
            if unit == 10000:
                section = (section + number) * unit
                total += section
                section = 0
            else:
                section += (number or 1) * unit
            number = 0
        else:
            return None
    return total + section + number
