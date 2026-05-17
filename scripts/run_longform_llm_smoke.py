#!/usr/bin/env python3
"""Run a scoped multi-chapter real LLM smoke and report topic drift.

Default mode is dry-run. Use ``--run`` to call ask-llm through the existing
Ginga chapter pipeline. Outputs stay under ``.ops/longform_smoke``.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ginga_platform.orchestrator.cli.longform_policy import (
    DEFAULT_CHAPTER_BATCH_SIZE,
    MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
    MIN_SUBMISSION_CHINESE_CHARS,
    PRESSURE_TEST_BATCH_SIZE,
    extract_chapter_body_text,
)

DEFAULT_ENDPOINT = "久久"
DEFAULT_BOOK_ID = "longform-jiujiu-combo-smoke"
DEFAULT_STATE_ROOT = REPO_ROOT / ".ops" / "longform_smoke" / "state"
DEFAULT_JSON_OUTPUT = REPO_ROOT / ".ops" / "validation" / "longform_jiujiu_smoke.json"
DEFAULT_REPORT_OUTPUT = REPO_ROOT / ".ops" / "reports" / "longform_jiujiu_smoke_report.md"
DEFAULT_TOPIC = "玄幻黑暗 + 规则怪谈 + 末日多子多福"
DEFAULT_PREMISE = (
    "失忆刺客无明在末日天堑边缘醒来，发现短刃能吞吐微粒，"
    "而每座城都被规则怪谈式禁令和血脉繁衍契约共同支配。"
)
DEFAULT_ANCHORS = ["无明", "短刃", "微粒", "天堑", "规则", "血脉", "末日"]
DEFAULT_FORBIDDEN = ["系统提示", "叮", "恭喜获得", "都市腔", "轻小说吐槽"]
DEFAULT_TEST_CHAPTERS = 30


@dataclass
class ChapterRun:
    chapter_no: int
    batch_no: int
    batch_size: int
    status: str
    path: str
    chars: int
    chinese_chars: int
    anchor_hits: dict[str, int]
    forbidden_hits: dict[str, int]
    foreshadow_markers: int
    stdout_tail: str
    stderr_tail: str
    error: str = ""


@dataclass
class BatchRun:
    batch_no: int
    start_chapter: int
    end_chapter: int
    requested_size: int
    status: str
    stdout_tail: str
    error: str = ""


def _tail(text: str, limit: int = 1000) -> str:
    return text if len(text) <= limit else text[-limit:]


def _chapter_path(state_root: Path, book_id: str, chapter_no: int) -> Path:
    return state_root / book_id / f"chapter_{chapter_no:02d}.md"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _count_chinese(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def _count_terms(text: str, terms: Sequence[str]) -> dict[str, int]:
    return {term: text.count(term) for term in terms}


def _existing_completed(state_root: Path, book_id: str) -> int:
    state_dir = state_root / book_id
    completed = 0
    for path in sorted(state_dir.glob("chapter_*.md")):
        match = re.search(r"chapter_(\d+)\.md$", path.name)
        if match:
            completed = max(completed, int(match.group(1)))
    return completed


def _audit_entries(state_root: Path, book_id: str) -> list[dict[str, Any]]:
    path = state_root / book_id / "audit_log.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("entries", raw if isinstance(raw, list) else [])
    return entries if isinstance(entries, list) else []


def _state_summary(state_root: Path, book_id: str) -> dict[str, Any]:
    entity_path = state_root / book_id / "entity_runtime.yaml"
    entity = yaml.safe_load(entity_path.read_text(encoding="utf-8")) if entity_path.exists() else {}
    entity = entity if isinstance(entity, dict) else {}
    return {
        "audit_entries": len(_audit_entries(state_root, book_id)),
        "total_words": (entity.get("GLOBAL_SUMMARY") or {}).get("total_words"),
        "foreshadow_pool_size": len((entity.get("FORESHADOW_STATE") or {}).get("pool") or []),
        "character_events": len(((entity.get("CHARACTER_STATE") or {}).get("protagonist") or {}).get("events") or []),
    }


def _planned_chapter(
    chapter_no: int,
    state_root: Path,
    book_id: str,
    anchors: Sequence[str],
    forbidden: Sequence[str],
    *,
    batch_no: int,
    batch_size: int,
) -> ChapterRun:
    return ChapterRun(
        chapter_no=chapter_no,
        batch_no=batch_no,
        batch_size=batch_size,
        status="planned",
        path=str(_chapter_path(state_root, book_id, chapter_no)),
        chars=0,
        chinese_chars=0,
        anchor_hits={term: 0 for term in anchors},
        forbidden_hits={term: 0 for term in forbidden},
        foreshadow_markers=0,
        stdout_tail="",
        stderr_tail="",
    )


def _init_book(*, book_id: str, state_root: Path, topic: str, premise: str) -> str:
    from ginga_platform.orchestrator.cli.demo_pipeline import init_book

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        init_book(
            book_id,
            topic=topic,
            premise=premise,
            word_target=500000,
            state_root=state_root,
        )
    return stdout.getvalue()


def _generate_chapter(
    *,
    book_id: str,
    state_root: Path,
    endpoint: str,
    word_target: int,
    chapter_no: int,
) -> tuple[str | None, str]:
    from ginga_platform.orchestrator.cli.demo_pipeline import run_workflow

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        path = run_workflow(
            book_id,
            llm_endpoint=endpoint,
            word_target=word_target,
            chapter_no=chapter_no,
            state_root=state_root,
            mock_llm=False,
        )
    return path, stdout.getvalue()


def _generate_batch(
    *,
    book_id: str,
    state_root: Path,
    endpoint: str,
    word_target: int,
    start_chapter: int,
    batch_size: int,
) -> tuple[list[str], str]:
    from ginga_platform.orchestrator.cli.immersive_runner import ImmersiveRunner
    from ginga_platform.orchestrator.cli.demo_pipeline import _call_llm, _max_tokens_for_word_target

    def llm_caller(prompt: str, endpoint: str) -> str:
        return _call_llm(prompt, endpoint, max_tokens=_max_tokens_for_word_target(word_target))

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        runner = ImmersiveRunner(book_id, state_root=state_root, llm_caller=llm_caller)
        result = runner.run_block(
            chapters=batch_size,
            llm_endpoint=endpoint,
            word_target=word_target,
            start_chapter_no=start_chapter,
            execution_mode="real_llm_demo",
        )
    if result.get("last_error"):
        raise RuntimeError(str(result["last_error"]))
    return list(result.get("chapter_paths") or []), stdout.getvalue()


def _chapter_result(
    *,
    chapter_no: int,
    path: Path,
    stdout: str,
    stderr: str,
    anchors: Sequence[str],
    forbidden: Sequence[str],
    batch_no: int,
    batch_size: int,
) -> ChapterRun:
    text = _read_text(path)
    body_text = extract_chapter_body_text(text)
    return ChapterRun(
        chapter_no=chapter_no,
        batch_no=batch_no,
        batch_size=batch_size,
        status="ok" if path.exists() and text.strip() else "missing",
        path=str(path),
        chars=len(text),
        chinese_chars=_count_chinese(body_text),
        anchor_hits=_count_terms(text, anchors),
        forbidden_hits={term: count for term, count in _count_terms(text, forbidden).items() if count},
        foreshadow_markers=text.count("<!-- foreshadow:"),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
    )


def _drift_report(chapter_runs: list[ChapterRun], anchors: Sequence[str]) -> dict[str, Any]:
    completed = [run for run in chapter_runs if run.status == "ok"]
    low_anchor = [
        run.chapter_no
        for run in completed
        if sum(1 for value in run.anchor_hits.values() if value > 0) < max(2, min(4, len(anchors) // 2))
    ]
    forbidden = [run.chapter_no for run in completed if run.forbidden_hits]
    short = [run.chapter_no for run in completed if run.chinese_chars < MIN_SUBMISSION_CHINESE_CHARS]
    missing_foreshadow = [run.chapter_no for run in completed if run.foreshadow_markers == 0]
    return {
        "status": "needs_review" if (low_anchor or forbidden or short) else "stable",
        "completed_chapters": len(completed),
        "first_drift_chapter": min(low_anchor + forbidden + short) if (low_anchor or forbidden or short) else None,
        "first_drift_batch": _first_drift_batch(completed, set(low_anchor + forbidden + short)),
        "low_anchor_chapters": low_anchor,
        "forbidden_hit_chapters": forbidden,
        "short_chapters": short,
        "missing_foreshadow_chapters": missing_foreshadow,
        "anchor_totals": {
            anchor: sum(run.anchor_hits.get(anchor, 0) for run in completed)
            for anchor in anchors
        },
    }


def _first_drift_batch(completed: list[ChapterRun], drift_chapters: set[int]) -> dict[str, Any] | None:
    for run in completed:
        if run.chapter_no in drift_chapters:
            return {"batch_no": run.batch_no, "batch_size": run.batch_size, "chapter_no": run.chapter_no}
    return None


def _batch_drift_summary(chapter_runs: list[ChapterRun]) -> list[dict[str, Any]]:
    batches: dict[int, list[ChapterRun]] = {}
    for run in chapter_runs:
        batches.setdefault(run.batch_no, []).append(run)
    summary: list[dict[str, Any]] = []
    for batch_no, runs in sorted(batches.items()):
        completed = [run for run in runs if run.status == "ok"]
        summary.append(
            {
                "batch_no": batch_no,
                "batch_size": runs[0].batch_size if runs else 0,
                "chapters": [run.chapter_no for run in runs],
                "completed": len(completed),
                "low_anchor_chapters": [
                    run.chapter_no
                    for run in completed
                    if sum(1 for value in run.anchor_hits.values() if value > 0) < max(2, min(4, len(run.anchor_hits) // 2))
                ],
                "forbidden_hit_chapters": [run.chapter_no for run in completed if run.forbidden_hits],
                "short_chapters": [run.chapter_no for run in completed if run.chinese_chars < MIN_SUBMISSION_CHINESE_CHARS],
            }
        )
    return summary


def _failed_chapter_from_error(error: str) -> int | None:
    match = re.search(r"chapter\s+(\d+)\s+failed quality gate", error)
    return int(match.group(1)) if match else None


def _build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Longform Jiujiu Smoke Report",
        "",
        f"- dry_run: `{payload['dry_run']}`",
        f"- passed: `{payload['passed']}`",
        f"- endpoint: `{payload['endpoint']}`",
        f"- book_id: `{payload['book_id']}`",
        f"- requested_chapters: `{payload['requested_chapters']}`",
        f"- completed_chapters: `{payload['completed_chapters']}`",
        f"- word_target: `{payload['word_target']}`",
        f"- topic: {payload['topic']}",
        f"- drift_status: `{payload['drift_report']['status']}`",
        "",
        "## Drift",
        "",
    ]
    drift = payload["drift_report"]
    for key in ("low_anchor_chapters", "forbidden_hit_chapters", "short_chapters", "missing_foreshadow_chapters"):
        lines.append(f"- {key}: `{drift[key]}`")
    policy = payload.get("production_policy", {})
    if policy:
        lines.extend(
            [
                "",
                "## Production Policy",
                "",
                f"- recommended_batch_size: `{policy.get('recommended_batch_size')}`",
                f"- upper_bound: `{policy.get('upper_bound')}`",
                f"- pressure_test_only_at_or_above: `{policy.get('pressure_test_only_at_or_above')}`",
            ]
        )
    lines.extend(["", "## Batches", ""])
    for item in payload.get("batch_drift_summary", []):
        lines.append(
            f"- batch{item['batch_no']:02d}: size={item['batch_size']}, "
            f"chapters={item['chapters']}, completed={item['completed']}, "
            f"short={item['short_chapters']}, forbidden={item['forbidden_hit_chapters']}"
        )
    lines.extend(["", "## Chapters", ""])
    for item in payload["chapter_runs"]:
        forbidden = item["forbidden_hits"] or {}
        lines.append(
            f"- ch{item['chapter_no']:03d}: {item['status']}, "
            f"batch={item['batch_no']}/{item['batch_size']}, "
            f"chars={item['chars']}, zh={item['chinese_chars']}, "
            f"foreshadow={item['foreshadow_markers']}, forbidden={forbidden}"
        )
    lines.append("")
    return "\n".join(lines)


def _parse_batch_schedule(value: str | Sequence[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        schedule = [int(part) for part in parts]
    else:
        schedule = [int(item) for item in value]
    if not schedule or any(item < 1 for item in schedule):
        raise ValueError("batch schedule must contain positive integers")
    return schedule


def _expand_batches(*, start_chapter: int, target_chapters: int, schedule: Sequence[int]) -> list[tuple[int, int, int, int]]:
    batches: list[tuple[int, int, int, int]] = []
    chapter = start_chapter
    index = 0
    while chapter <= target_chapters:
        requested = schedule[index] if index < len(schedule) else schedule[-1]
        size = min(requested, target_chapters - chapter + 1)
        batches.append((len(batches) + 1, chapter, chapter + size - 1, size))
        chapter += size
        index += 1
    return batches


def _remaining_batches(*, completed: int, target_chapters: int, schedule: Sequence[int]) -> list[tuple[int, int, int, int]]:
    remaining: list[tuple[int, int, int, int]] = []
    for batch_no, start, end, _size in _expand_batches(start_chapter=1, target_chapters=target_chapters, schedule=schedule):
        if end <= completed:
            continue
        adjusted_start = max(start, completed + 1)
        remaining.append((batch_no, adjusted_start, end, end - adjusted_start + 1))
    return remaining


def run_longform_smoke(
    *,
    book_id: str = DEFAULT_BOOK_ID,
    endpoint: str = DEFAULT_ENDPOINT,
    state_root: Path = DEFAULT_STATE_ROOT,
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
    chapters: int = DEFAULT_TEST_CHAPTERS,
    word_target: int = 4000,
    batch_schedule: str | Sequence[int] = "3,4,5,6",
    topic: str = DEFAULT_TOPIC,
    premise: str = DEFAULT_PREMISE,
    anchors: Sequence[str] = DEFAULT_ANCHORS,
    forbidden_terms: Sequence[str] = DEFAULT_FORBIDDEN,
    dry_run: bool = True,
    resume: bool = True,
) -> dict[str, Any]:
    state_root = Path(state_root)
    json_output = Path(json_output)
    report_output = Path(report_output)
    chapter_runs: list[ChapterRun] = []
    batch_runs: list[BatchRun] = []
    existing_completed = _existing_completed(state_root, book_id)
    completed_for_schedule = existing_completed if resume else 0
    schedule = _parse_batch_schedule(batch_schedule)
    batches = _remaining_batches(completed=completed_for_schedule, target_chapters=chapters, schedule=schedule)

    if dry_run:
        for batch_no, start, end, size in batches:
            batch_runs.append(BatchRun(batch_no, start, end, size, "planned", ""))
            chapter_runs.extend(
                _planned_chapter(
                    chapter_no,
                    state_root,
                    book_id,
                    anchors,
                    forbidden_terms,
                    batch_no=batch_no,
                    batch_size=size,
                )
                for chapter_no in range(start, end + 1)
            )
    else:
        state_root.mkdir(parents=True, exist_ok=True)
        if existing_completed == 0 or not resume:
            _init_book(book_id=book_id, state_root=state_root, topic=topic, premise=premise)
        for batch_no, start, end, size in batches:
            try:
                generated_paths, stdout = _generate_batch(
                    book_id=book_id,
                    state_root=state_root,
                    endpoint=endpoint,
                    word_target=word_target,
                    start_chapter=start,
                    batch_size=size,
                )
                if len(generated_paths) < size:
                    batch_runs.append(BatchRun(batch_no, start, end, size, "failed", _tail(stdout), "batch_returned_too_few_paths"))
                    chapter_runs.append(
                        ChapterRun(
                            chapter_no=start + len(generated_paths),
                            batch_no=batch_no,
                            batch_size=size,
                            status="failed",
                            path=str(_chapter_path(state_root, book_id, start + len(generated_paths))),
                            chars=0,
                            chinese_chars=0,
                            anchor_hits={term: 0 for term in anchors},
                            forbidden_hits={},
                            foreshadow_markers=0,
                            stdout_tail=_tail(stdout),
                            stderr_tail="",
                            error="batch_returned_too_few_paths",
                        )
                    )
                    break
                batch_runs.append(BatchRun(batch_no, start, end, size, "ok", _tail(stdout)))
                for chapter_no in range(start, end + 1):
                    chapter_runs.append(_chapter_result(
                        chapter_no=chapter_no,
                        path=_chapter_path(state_root, book_id, chapter_no),
                        stdout=stdout,
                        stderr="",
                        anchors=anchors,
                        forbidden=forbidden_terms,
                        batch_no=batch_no,
                        batch_size=size,
                    ))
            except Exception as exc:  # noqa: BLE001 - report and stop.
                error = f"{type(exc).__name__}: {exc}"
                failed_chapter_no = _failed_chapter_from_error(error) or start
                batch_runs.append(BatchRun(batch_no, start, end, size, "failed", "", error))
                chapter_runs.append(
                    ChapterRun(
                        chapter_no=failed_chapter_no,
                        batch_no=batch_no,
                        batch_size=size,
                        status="failed",
                        path=str(_chapter_path(state_root, book_id, failed_chapter_no)),
                        chars=0,
                        chinese_chars=0,
                        anchor_hits={term: 0 for term in anchors},
                        forbidden_hits={},
                        foreshadow_markers=0,
                        stdout_tail="",
                        stderr_tail="",
                        error=error,
                    )
                )
                break

    completed_chapters = _existing_completed(state_root, book_id)
    if dry_run:
        completed_chapters = existing_completed
    else:
        chapter_runs = _merge_existing_runs(
            state_root=state_root,
            book_id=book_id,
            chapters=chapters,
            current_runs=chapter_runs,
            anchors=anchors,
            forbidden=forbidden_terms,
            schedule=schedule,
        )
    payload = {
        "generated_from": "scripts/run_longform_llm_smoke.py",
        "dry_run": dry_run,
        "passed": (not dry_run and completed_chapters >= chapters and all(run.status == "ok" for run in chapter_runs)),
        "endpoint": endpoint,
        "book_id": book_id,
        "topic": topic,
        "premise": premise,
        "requested_chapters": chapters,
        "completed_chapters": completed_chapters,
        "existing_completed_before": existing_completed,
        "resume": resume,
        "batch_schedule": schedule,
        "batch_runs": [asdict(run) for run in batch_runs],
        "word_target": word_target,
        "state_root": str(state_root),
        "anchors": list(anchors),
        "forbidden_terms": list(forbidden_terms),
        "production_policy": {
            "recommended_batch_size": DEFAULT_CHAPTER_BATCH_SIZE,
            "upper_bound": MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
            "pressure_test_only_at_or_above": PRESSURE_TEST_BATCH_SIZE,
            "min_submission_chinese_chars": MIN_SUBMISSION_CHINESE_CHARS,
        },
        "state_summary": _state_summary(state_root, book_id),
        "chapter_runs": [asdict(run) for run in chapter_runs],
    }
    payload["drift_report"] = _drift_report(chapter_runs, anchors)
    payload["batch_drift_summary"] = _batch_drift_summary(chapter_runs)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_output.write_text(_build_report(payload), encoding="utf-8")
    return payload


def _merge_existing_runs(
    *,
    state_root: Path,
    book_id: str,
    chapters: int,
    current_runs: list[ChapterRun],
    anchors: Sequence[str],
    forbidden: Sequence[str],
    schedule: Sequence[int],
) -> list[ChapterRun]:
    by_chapter = {run.chapter_no: run for run in current_runs}
    merged: list[ChapterRun] = []
    for chapter_no in range(1, chapters + 1):
        if chapter_no in by_chapter:
            merged.append(by_chapter[chapter_no])
            continue
        path = _chapter_path(state_root, book_id, chapter_no)
        if path.exists():
            batch_no = 1
            batch_size = schedule[0] if schedule else 1
            for candidate_no, start, end, size in _expand_batches(start_chapter=1, target_chapters=chapters, schedule=schedule):
                if start <= chapter_no <= end:
                    batch_no = candidate_no
                    batch_size = size
                    break
            merged.append(
                _chapter_result(
                    chapter_no=chapter_no,
                    path=path,
                    stdout="",
                    stderr="",
                    anchors=anchors,
                    forbidden=forbidden,
                    batch_no=batch_no,
                    batch_size=batch_size,
                )
            )
    return merged


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-id", default=DEFAULT_BOOK_ID)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--chapters", type=int, default=DEFAULT_TEST_CHAPTERS)
    parser.add_argument("--word-target", type=int, default=4000)
    parser.add_argument("--batch-schedule", default="3,4,5,6")
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--premise", default=DEFAULT_PREMISE)
    parser.add_argument("--anchor", action="append", dest="anchors")
    parser.add_argument("--forbidden-term", action="append", dest="forbidden_terms")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    mode.add_argument("--run", dest="dry_run", action="store_false")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload = run_longform_smoke(
        book_id=args.book_id,
        endpoint=args.endpoint,
        state_root=args.state_root,
        json_output=args.json_output,
        report_output=args.report_output,
        chapters=args.chapters,
        word_target=args.word_target,
        batch_schedule=args.batch_schedule,
        topic=args.topic,
        premise=args.premise,
        anchors=args.anchors or DEFAULT_ANCHORS,
        forbidden_terms=args.forbidden_terms or DEFAULT_FORBIDDEN,
        dry_run=args.dry_run,
        resume=args.resume,
    )
    print(
        f"wrote {args.json_output} and {args.report_output}; "
        f"dry_run={payload['dry_run']} completed={payload['completed_chapters']}/{payload['requested_chapters']} "
        f"drift={payload['drift_report']['status']}"
    )
    return 0 if payload["dry_run"] or payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
