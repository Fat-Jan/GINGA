"""Warn-only Review / deslop sidecar reports.

The review report is advisory output only. It reads StateIO snapshots and
chapter artifacts, then writes a sidecar report under ``.ops/reviews``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.cli.longform_policy import (
    DEFAULT_CHAPTER_BATCH_SIZE,
    MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
    PRESSURE_TEST_BATCH_SIZE,
    count_chinese,
    evaluate_longform_hard_gate,
    first_body_excerpt,
    load_chapter_artifacts,
    longform_chapter_gate_check,
    longform_forbidden_hits,
    low_frequency_anchors,
    opening_loop_score,
    strip_html_comments,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


DEFAULT_OUTPUT_ROOT = Path(".ops/reviews")
DEFAULT_RUBRIC_ID = "platform_cn_webnovel_v1"


class ReviewError(RuntimeError):
    """Review/deslop sidecar contract error."""


def export_review_report(
    book_id: str,
    *,
    run_id: str | None = None,
    state_root: str | Path | None = None,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    rubric_profile: str = DEFAULT_RUBRIC_ID,
) -> dict[str, Any]:
    """Write a warn-only review report under ``.ops/reviews/<book>/<run>``."""

    run = _safe_segment(run_id or _default_run_id())
    root = _validate_output_root(Path(output_root))
    out_dir = root / _safe_segment(book_id) / run
    sio = StateIO(book_id, state_root=state_root, autoload=True)
    payload = build_review_report(
        book_id,
        run_id=run,
        state=sio.state,
        state_dir=sio.state_dir,
        rubric_profile=rubric_profile,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(_render_markdown(payload), encoding="utf-8")
    return {
        "status": payload["status"],
        "book_id": book_id,
        "run_id": run,
        "output_dir": str(out_dir),
        "issue_count": payload["summary"]["issue_count"],
    }


def build_review_report(
    book_id: str,
    *,
    run_id: str,
    state: dict[str, dict[str, Any]],
    state_dir: Path,
    rubric_profile: str = DEFAULT_RUBRIC_ID,
) -> dict[str, Any]:
    """Build a deterministic review report without mutating source inputs."""

    chapters = _load_chapters(state_dir)
    issues = _scan_chapters(chapters)
    longform_gate = _build_longform_quality_gate(state=state, chapters=chapters)
    style_fingerprint = _build_style_fingerprint(state=state, chapters=chapters)
    issues.extend(longform_gate["issues"])
    status = "warn" if issues else "pass"
    return {
        "kind": "ReviewDeslopReport",
        "book_id": book_id,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "passed": not issues,
        "mode": "warn_only",
        "auto_edit": False,
        "projection": {
            "kind": "ReviewDeslop",
            "truth_source": "StateIO",
            "is_state_truth": False,
            "writes_runtime_state": False,
            "output_boundary": ".ops/reviews/<book_id>/<run_id>/",
        },
        "rubric": {
            "id": rubric_profile,
            "scope": "report_only",
            "enters_creation_prompt": False,
            "categories": [
                "anti_ai_style",
                "platform_genre_fit",
                "webnovel_readability",
                "style_fingerprint",
            ],
        },
        "data_sources": {
            "state_dir": str(state_dir),
            "state_domains": ["locked", "entity_runtime", "workspace", "retrieved", "audit_log"],
            "chapter_artifacts": [chapter["path"] for chapter in chapters],
            "forbidden_default_sources": [".ops/book_analysis/**", ".ops/market_research/**", ".ops/external_sources/**"],
        },
        "context": _context_summary(state),
        "summary": {
            "chapter_count": len(chapters),
            "issue_count": len(issues),
            "warn_count": sum(1 for issue in issues if issue["severity"] == "warn"),
            "error_count": 0,
            "longform_gate_issue_count": len(longform_gate["issues"]),
            "reviewer_queue_count": len(longform_gate["reviewer_queue"]),
            "style_fingerprint_status": style_fingerprint["status"],
        },
        "style_fingerprint": style_fingerprint,
        "longform_quality_gate": longform_gate,
        "issues": issues,
        "suggestions": _suggestions_from_issues(issues),
    }


def _load_chapters(state_dir: Path) -> list[dict[str, Any]]:
    chapters = load_chapter_artifacts(state_dir)
    for chapter in chapters:
        chapter["title"] = _extract_title(chapter["text"]) or Path(chapter["path"]).stem
    return chapters


def _scan_chapters(chapters: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for chapter in chapters:
        text = chapter.get("text", "")
        issues.extend(_scan_patterns(chapter, text))
        if len(_body_paragraphs(text)) < 3 and len(text.strip()) >= 80:
            issues.append(
                _issue(
                    chapter,
                    code="thin_scene_flow",
                    category="webnovel_readability",
                    message="章节段落密度偏低，可能缺少连续场景推进。",
                    evidence="paragraph_count<3",
                )
            )
    return issues


def _scan_patterns(chapter: dict[str, Any], text: str) -> list[dict[str, Any]]:
    patterns = (
        ("anti_ai_style", "generic_emotion", r"说不出的感觉|难以言喻|复杂的情绪", "抽象情绪替代具体动作。"),
        ("anti_ai_style", "cliche_metaphor", r"命运的齿轮|内心深处|仿佛.*?命运", "常见套话削弱场景质感。"),
        ("anti_ai_style", "abrupt_transition", r"突然|猛然|下一秒", "高频突转词需要确认是否由动作因果支撑。"),
        ("platform_genre_fit", "game_system_tone", r"系统提示|叮|恭喜获得|任务完成", "游戏系统播报腔与当前风格锁冲突。"),
        ("platform_genre_fit", "light_novel_meta", r"吐槽|不会吧|这也太", "轻小说吐槽腔与当前风格锁冲突。"),
    )
    issues: list[dict[str, Any]] = []
    for category, code, pattern, message in patterns:
        for match in re.finditer(pattern, text):
            issues.append(
                _issue(
                    chapter,
                    code=code,
                    category=category,
                    message=message,
                    evidence=_evidence(text, match.start(), match.end()),
                )
            )
    return issues


def _build_longform_quality_gate(*, state: dict[str, dict[str, Any]], chapters: list[dict[str, Any]]) -> dict[str, Any]:
    gate_issues: list[dict[str, Any]] = []
    queue: dict[str, dict[str, Any]] = {}
    anchor_terms = low_frequency_anchors(state)
    batch_size = DEFAULT_CHAPTER_BATCH_SIZE
    for batch_start in range(0, len(chapters), batch_size):
        batch = chapters[batch_start : batch_start + batch_size]
        for chapter in batch:
            text = chapter.get("text", "")
            chapter_issues = _longform_chapter_issues(chapter, text, anchor_terms)
            gate_issues.extend(chapter_issues)
            for issue in chapter_issues:
                if _requires_reviewer(issue):
                    _queue_reviewer(queue, chapter, issue)
    hard_gate = evaluate_longform_hard_gate(state=state, chapters=chapters, window_size=batch_size)
    return {
        "enabled": True,
        "mode": "warn_only",
        "auto_edit": False,
        "hard_gate": hard_gate,
        "policy": {
            "recommended_batch_size": DEFAULT_CHAPTER_BATCH_SIZE,
            "upper_bound": MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
            "pressure_test_only_at_or_above": PRESSURE_TEST_BATCH_SIZE,
        },
        "low_frequency_anchors": anchor_terms,
        "batch_state_snapshots": _batch_state_snapshots(state=state, chapters=chapters, batch_size=batch_size),
        "issues": gate_issues,
        "reviewer_queue": list(queue.values()),
    }


def _build_style_fingerprint(*, state: dict[str, dict[str, Any]], chapters: list[dict[str, Any]]) -> dict[str, Any]:
    text = "\n".join(chapter.get("text", "") for chapter in chapters)
    body_text = strip_html_comments(text)
    sentences = _sentences(body_text)
    sentence_lengths = [count_chinese(sentence) for sentence in sentences if count_chinese(sentence) > 0]
    paragraphs = [paragraph for chapter in chapters for paragraph in _body_paragraphs(chapter.get("text", ""))]
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    dialogue_lines = [line for line in lines if _is_dialogue_line(line)]
    anchor_phrases = _context_summary(state)["anchor_phrases"]
    style_pattern_hits = _style_pattern_hits(body_text)
    return {
        "scope": "report_only",
        "auto_edit": False,
        "writes_runtime_state": False,
        "enters_creation_prompt": False,
        "status": "measured" if chapters else "no_chapters",
        "chapter_count": len(chapters),
        "total_chinese_chars": count_chinese(body_text),
        "paragraph_count": len(paragraphs),
        "dialogue_line_count": len(dialogue_lines),
        "dialogue_line_ratio": _ratio(len(dialogue_lines), len(lines)),
        "avg_sentence_chars": _average(sentence_lengths),
        "sentence_length_buckets": {
            "short": sum(1 for value in sentence_lengths if value <= 12),
            "medium": sum(1 for value in sentence_lengths if 13 <= value <= 35),
            "long": sum(1 for value in sentence_lengths if value >= 36),
        },
        "anchor_phrase_hits": {phrase: body_text.count(phrase) for phrase in anchor_phrases},
        "style_pattern_hits": style_pattern_hits,
        "notes": [
            "Style fingerprint is measured for review evidence only.",
            "It must not auto-edit prose, write StateIO, or enter creation prompts.",
        ],
    }


def _style_pattern_hits(text: str) -> dict[str, int]:
    patterns = {
        "generic_emotion": r"说不出的感觉|难以言喻|复杂的情绪",
        "cliche_metaphor": r"命运的齿轮|内心深处|仿佛.*?命运",
        "abrupt_transition": r"突然|猛然|下一秒",
        "game_system_tone": r"系统提示|叮|恭喜获得|任务完成",
        "light_novel_meta": r"吐槽|不会吧|这也太",
    }
    return {name: len(re.findall(pattern, text)) for name, pattern in patterns.items()}


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。！？!?]+", text) if part.strip()]


def _is_dialogue_line(line: str) -> bool:
    return line.startswith(("“", "「", '"')) or "：“" in line or ": \"" in line


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)


def _longform_chapter_issues(
    chapter: dict[str, Any],
    text: str,
    low_frequency_anchors: list[str],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    body_text = strip_html_comments(text)
    check = longform_chapter_gate_check(chapter=chapter, low_frequency_anchors=low_frequency_anchors)
    if check["opening_loop_risk"]:
        issues.append(
            _issue(
                chapter,
                code="opening_loop_risk",
                category="longform_continuity",
                message="章节开头疑似回到醒来/失忆/体内微粒/天堑边缘模板，可能把续写误判为重新开篇。",
                evidence=first_body_excerpt(text),
            )
        )
    if check["missing_low_frequency_anchor"]:
        issues.append(
            _issue(
                chapter,
                code="missing_low_frequency_anchor",
                category="longform_topic_lock",
                message="低频题材锚点缺失，组合题材可能被玄幻黑暗主轴稀释。",
                evidence="missing any of: " + ", ".join(low_frequency_anchors),
            )
        )
    if check["missing_foreshadow_marker"]:
        issues.append(
            _issue(
                chapter,
                code="missing_foreshadow_marker",
                category="longform_continuity",
                message="章节缺少伏笔标记，后续状态快照难以追踪铺垫与回收。",
                evidence="missing <!-- foreshadow: marker",
            )
        )
    if check["short_chapter"]:
        issues.append(
            _issue(
                chapter,
                code="short_chapter",
                category="longform_quality",
                message="章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。",
                evidence=f"chinese_chars={count_chinese(body_text)} < 2400",
            )
        )
    forbidden_hits = check["forbidden_hits"]
    if forbidden_hits:
        issues.append(
            _issue(
                chapter,
                code="forbidden_style_hit",
                category="longform_topic_lock",
                message="章节命中长篇正式 gate 禁词，需进入异常章 reviewer。",
                evidence=", ".join(f"{term}={count}" for term, count in forbidden_hits.items()),
            )
        )
    return issues


def _batch_state_snapshots(
    *,
    state: dict[str, dict[str, Any]],
    chapters: list[dict[str, Any]],
    batch_size: int,
) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for batch_start in range(0, len(chapters), batch_size):
        batch = chapters[batch_start : batch_start + batch_size]
        if not batch:
            continue
        snapshots.append(
            {
                "batch_no": len(snapshots) + 1,
                "chapter_range": _chapter_range_label(batch),
                "chapter_count": len(batch),
                "state_snapshot": _state_snapshot(state, batch),
                "quality_snapshot": _batch_quality_snapshot(batch, low_frequency_anchors(state)),
            }
        )
    return snapshots


def _chapter_range_label(batch: list[dict[str, Any]]) -> str:
    numbers = [_chapter_number(chapter) for chapter in batch]
    numbers = [number for number in numbers if number is not None]
    if not numbers:
        return ""
    return f"{min(numbers)}-{max(numbers)}"


def _chapter_number(chapter: dict[str, Any]) -> int | None:
    match = re.search(r"chapter_(\d+)\.md$", chapter.get("name", ""))
    return int(match.group(1)) if match else None


def _state_snapshot(state: dict[str, dict[str, Any]], batch: list[dict[str, Any]]) -> dict[str, Any]:
    entity = state.get("entity_runtime", {}) or {}
    character = ((entity.get("CHARACTER_STATE") or {}).get("protagonist") or {})
    ledger = entity.get("RESOURCE_LEDGER") or {}
    foreshadow = entity.get("FORESHADOW_STATE") or {}
    global_summary = entity.get("GLOBAL_SUMMARY") or {}
    recent_events = character.get("events") or []
    batch_text = "\n".join(chapter.get("text", "") for chapter in batch)
    return {
        "protagonist": character.get("name", ""),
        "particles": ledger.get("particles", 0),
        "foreshadow_pool_size": len(foreshadow.get("pool") or []),
        "total_words": global_summary.get("total_words", 0),
        "recent_events": recent_events[-3:],
        "anchors_present": sorted({anchor for anchor in low_frequency_anchors(state) if anchor in batch_text}),
    }


def _batch_quality_snapshot(batch: list[dict[str, Any]], low_frequency_anchors: list[str]) -> dict[str, Any]:
    opening_loop_chapters: list[str] = []
    missing_low_frequency_anchor_chapters: list[str] = []
    short_chapters: list[str] = []
    forbidden_hit_chapters: list[str] = []
    missing_foreshadow_chapters: list[str] = []
    for chapter in batch:
        text = chapter.get("text", "")
        body = strip_html_comments(text)
        if opening_loop_score(body) >= 3:
            opening_loop_chapters.append(chapter.get("name", ""))
        if low_frequency_anchors and not any(anchor in body for anchor in low_frequency_anchors):
            missing_low_frequency_anchor_chapters.append(chapter.get("name", ""))
        if count_chinese(body) < 2400:
            short_chapters.append(chapter.get("name", ""))
        if longform_forbidden_hits(body):
            forbidden_hit_chapters.append(chapter.get("name", ""))
        if "<!-- foreshadow:" not in text:
            missing_foreshadow_chapters.append(chapter.get("name", ""))
    return {
        "opening_loop_chapters": opening_loop_chapters,
        "missing_low_frequency_anchor_chapters": missing_low_frequency_anchor_chapters,
        "short_chapters": short_chapters,
        "forbidden_hit_chapters": forbidden_hit_chapters,
        "missing_foreshadow_chapters": missing_foreshadow_chapters,
    }


def _requires_reviewer(issue: dict[str, Any]) -> bool:
    if issue["code"] in {"short_chapter", "missing_foreshadow_marker", "forbidden_style_hit"}:
        return True
    chapter_no = _chapter_number({"name": issue.get("chapter", "")}) or 0
    return issue["code"] == "opening_loop_risk" and chapter_no > MAX_REAL_LLM_CHAPTER_BATCH_SIZE


def _queue_reviewer(queue: dict[str, dict[str, Any]], chapter: dict[str, Any], issue: dict[str, Any]) -> None:
    name = chapter.get("name", "")
    item = queue.setdefault(
        name,
        {
            "chapter": name,
            "path": chapter.get("path", ""),
            "reason_codes": [],
            "recommended_reviewer": "longform_quality_reviewer",
            "action": "review_manually",
        },
    )
    if issue["code"] not in item["reason_codes"]:
        item["reason_codes"].append(issue["code"])


def _issue(
    chapter: dict[str, Any],
    *,
    code: str,
    category: str,
    message: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "severity": "warn",
        "category": category,
        "code": code,
        "chapter": chapter.get("name", ""),
        "message": message,
        "evidence": evidence,
        "action": "review_manually",
    }


def _suggestions_from_issues(issues: list[dict[str, Any]]) -> list[str]:
    suggestions: list[str] = []
    categories = {issue["category"] for issue in issues}
    if "anti_ai_style" in categories:
        suggestions.append("把抽象心理和套话改成可观察动作、身体代价、环境反馈或对手反应。")
    if "platform_genre_fit" in categories:
        suggestions.append("平台风格冲突只做人工复核提示；如需改文，另开编辑流程，不由 review 自动写回。")
    if "webnovel_readability" in categories:
        suggestions.append("检查段落是否形成连续场景链：目标、阻力、动作、代价、反转。")
    if any(issue["category"].startswith("longform_") for issue in issues):
        suggestions.append("按 v1.7 gate 复核异常章：先看批后状态快照，再处理回环、低频题材锚点和伏笔缺失。")
    return suggestions


def _context_summary(state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    locked = state.get("locked", {})
    genre = locked.get("GENRE_LOCKED", {}) or {}
    story = locked.get("STORY_DNA", {}) or {}
    return {
        "topic": genre.get("topic", []),
        "forbidden_styles": (genre.get("style_lock") or {}).get("forbidden_styles", []),
        "anchor_phrases": (genre.get("style_lock") or {}).get("anchor_phrases", []),
        "premise_present": bool(story.get("premise")),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Review: {payload['book_id']}",
        "",
        "> Warn-only sidecar. It never edits chapter text or runtime_state.",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- status: `{payload['status']}`",
        f"- rubric: `{payload['rubric']['id']}` ({payload['rubric']['scope']})",
        f"- issues: {payload['summary']['issue_count']}",
        f"- longform_gate_issues: {payload['summary'].get('longform_gate_issue_count', 0)}",
        f"- reviewer_queue: {payload['summary'].get('reviewer_queue_count', 0)}",
        f"- style_fingerprint: `{payload['summary'].get('style_fingerprint_status', 'unknown')}`",
        "",
        "## Issues",
        "",
    ]
    if not payload["issues"]:
        lines.append("- none")
    for issue in payload["issues"]:
        lines.append(
            f"- `{issue['chapter']}` `{issue['code']}` [{issue['category']}]: "
            f"{issue['message']} Evidence: {issue['evidence']}"
        )
    lines.extend(["", "## Suggestions", ""])
    if not payload["suggestions"]:
        lines.append("- none")
    for suggestion in payload["suggestions"]:
        lines.append(f"- {suggestion}")
    fingerprint = payload.get("style_fingerprint") or {}
    if fingerprint:
        lines.extend(["", "## Style Fingerprint", ""])
        lines.append(f"- scope: `{fingerprint.get('scope', '')}`")
        lines.append(f"- auto_edit: `{fingerprint.get('auto_edit', False)}`")
        lines.append(f"- writes_runtime_state: `{fingerprint.get('writes_runtime_state', False)}`")
        lines.append(f"- enters_creation_prompt: `{fingerprint.get('enters_creation_prompt', False)}`")
        lines.append(f"- chapters: {fingerprint.get('chapter_count', 0)}")
        lines.append(f"- chinese_chars: {fingerprint.get('total_chinese_chars', 0)}")
        lines.append(f"- avg_sentence_chars: {fingerprint.get('avg_sentence_chars', 0)}")
        lines.append(f"- dialogue_line_ratio: {fingerprint.get('dialogue_line_ratio', 0)}")
        lines.append(f"- anchor_phrase_hits: {fingerprint.get('anchor_phrase_hits', {})}")
        lines.append(f"- style_pattern_hits: {fingerprint.get('style_pattern_hits', {})}")
    gate = payload.get("longform_quality_gate") or {}
    if gate:
        lines.extend(["", "## Longform Quality Gate", ""])
        for item in gate.get("batch_state_snapshots", []):
            quality = item.get("quality_snapshot", {})
            lines.append(
                f"- batch {item['batch_no']} `{item['chapter_range']}`: "
                f"protagonist={item['state_snapshot'].get('protagonist', '')}, "
                f"particles={item['state_snapshot'].get('particles', 0)}, "
                f"anchors={item['state_snapshot'].get('anchors_present', [])}, "
                f"short={quality.get('short_chapters', [])}, "
                f"forbidden={quality.get('forbidden_hit_chapters', [])}, "
                f"missing_foreshadow={quality.get('missing_foreshadow_chapters', [])}"
            )
        lines.append("")
        lines.append("### Reviewer Queue")
        if not gate.get("reviewer_queue"):
            lines.append("- none")
        for item in gate.get("reviewer_queue", []):
            lines.append(f"- `{item['chapter']}`: {', '.join(item['reason_codes'])}")
    lines.append("")
    return "\n".join(lines)


def _validate_output_root(root: Path) -> Path:
    normalized = root.as_posix().rstrip("/")
    if not (normalized == ".ops/reviews" or normalized.endswith("/.ops/reviews")):
        raise ReviewError("Review output_root must be .ops/reviews")
    return root


def _safe_segment(value: str) -> str:
    if not value or "/" in value or ".." in value:
        raise ReviewError(f"invalid path segment: {value!r}")
    return value


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _body_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _evidence(text: str, start: int, end: int, radius: int = 18) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[left:right]).strip()


__all__ = [
    "DEFAULT_OUTPUT_ROOT",
    "DEFAULT_RUBRIC_ID",
    "ReviewError",
    "build_review_report",
    "export_review_report",
]
