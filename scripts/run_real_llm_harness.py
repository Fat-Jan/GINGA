#!/usr/bin/env python3
"""Run the v2.3 real LLM harness with preflight, postflight, and review gate.

Default mode is dry-run. Use ``--run`` explicitly before spending real model
calls. Outputs are scoped under ``.ops/real_llm_harness`` by default.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ginga_platform.orchestrator.cli.longform_policy import (  # noqa: E402
    DEFAULT_CHAPTER_BATCH_SIZE,
    MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
    MIN_SUBMISSION_CHINESE_CHARS,
    PRESSURE_TEST_BATCH_SIZE,
)
from ginga_platform.orchestrator.review import export_review_report  # noqa: E402
from scripts.run_longform_llm_smoke import run_longform_smoke  # noqa: E402
from scripts.run_real_llm_smoke import run_smoke  # noqa: E402


HARNESS_VERSION = "v2.3"
DEFAULT_ENDPOINT = "久久"
DEFAULT_PROFILE = "longform-small-batch"
DEFAULT_BOOK_ID = "v2-3-real-llm-harness"
DEFAULT_STATE_ROOT = REPO_ROOT / ".ops" / "real_llm_harness" / "state"
DEFAULT_JSON_OUTPUT = REPO_ROOT / ".ops" / "validation" / "real_llm_harness.json"
DEFAULT_REPORT_OUTPUT = REPO_ROOT / ".ops" / "reports" / "real_llm_harness_report.md"
DEFAULT_REVIEW_OUTPUT_ROOT = REPO_ROOT / ".ops" / "reviews"
MIN_LONGFORM_WORD_TARGET = MIN_SUBMISSION_CHINESE_CHARS
MAX_GENERATION_ATTEMPTS_PER_CHAPTER = 3
SUPPORTED_PROFILES = ("single-chapter-smoke", "longform-small-batch")
WILL_NOT_OVERWRITE = (
    "foundation/runtime_state/**",
    ".ops/longform_smoke/**",
    ".ops/real_llm_demo/**",
    ".ops/reviews/** except selected review_output_root",
)


@dataclass
class GateIssue:
    code: str
    severity: str
    detail: str


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _parse_batch_schedule(value: str | Sequence[int]) -> list[int]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        schedule = [int(part) for part in parts]
    else:
        schedule = [int(item) for item in value]
    if not schedule or any(item < 1 for item in schedule):
        raise ValueError("batch schedule must contain positive integers")
    return schedule


def _state_root_is_isolated(path: Path) -> bool:
    normalized = path.resolve().as_posix()
    return "/.ops/real_llm_harness/" in normalized or normalized.endswith("/.ops/real_llm_harness")


def _output_is_under(path: Path, segment: str) -> bool:
    normalized = path.resolve().as_posix()
    return f"/{segment}/" in normalized or normalized.endswith(f"/{segment}")


def _build_isolation(state_root: Path, json_output: Path, report_output: Path, review_output_root: Path) -> dict[str, Any]:
    return {
        "state_root": _repo_rel(state_root),
        "json_output": _repo_rel(json_output),
        "report_output": _repo_rel(report_output),
        "review_output_root": _repo_rel(review_output_root),
        "state_root_under_ops": _state_root_is_isolated(state_root),
        "json_under_validation": _output_is_under(json_output.parent, ".ops/validation"),
        "report_under_reports": _output_is_under(report_output.parent, ".ops/reports"),
        "review_under_ops_reviews": _output_is_under(review_output_root, ".ops/reviews"),
        "will_not_overwrite": list(WILL_NOT_OVERWRITE),
    }


def _cost_boundary(*, profile: str, chapters: int, word_target: int, batch_schedule: Sequence[int], dry_run: bool) -> dict[str, Any]:
    if profile == "single-chapter-smoke":
        estimated_calls = 1
        max_chapters = 1
        max_calls = 1
        max_attempts = 1
    else:
        max_attempts = MAX_GENERATION_ATTEMPTS_PER_CHAPTER
        estimated_calls = chapters * max_attempts
        max_chapters = MAX_REAL_LLM_CHAPTER_BATCH_SIZE
        max_calls = chapters * max_attempts
    return {
        "profile": profile,
        "dry_run_default": True,
        "run_requires_explicit_flag": True,
        "estimated_real_llm_calls": estimated_calls,
        "max_real_llm_calls": max_calls,
        "max_generation_attempts_per_chapter": max_attempts,
        "requested_chapters": chapters,
        "max_chapters": max_chapters,
        "recommended_batch_size": DEFAULT_CHAPTER_BATCH_SIZE,
        "upper_bound": MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
        "pressure_test_only_at_or_above": PRESSURE_TEST_BATCH_SIZE,
        "word_target": word_target,
        "min_longform_word_target": MIN_LONGFORM_WORD_TARGET,
        "batch_schedule": list(batch_schedule),
        "actual_cost_incurred": not dry_run,
    }


def _preflight(
    *,
    profile: str,
    endpoint: str,
    state_root: Path,
    json_output: Path,
    report_output: Path,
    review_output_root: Path,
    chapters: int,
    word_target: int,
    batch_schedule: Sequence[int],
    dry_run: bool,
    review_gate: bool,
) -> dict[str, Any]:
    errors: list[GateIssue] = []
    warnings: list[GateIssue] = []
    if profile not in SUPPORTED_PROFILES:
        errors.append(GateIssue("unsupported_profile", "error", f"profile={profile!r}"))
    if not endpoint.strip():
        errors.append(GateIssue("missing_endpoint", "error", "endpoint is required for real LLM harness"))
    if chapters < 1:
        errors.append(GateIssue("invalid_chapter_count", "error", "chapters must be >= 1"))
    if profile == "single-chapter-smoke" and chapters != 1:
        errors.append(GateIssue("single_chapter_profile_requires_one_chapter", "error", "single-chapter-smoke must use chapters=1"))
    if profile == "longform-small-batch":
        if chapters > MAX_REAL_LLM_CHAPTER_BATCH_SIZE:
            errors.append(
                GateIssue(
                    "longform_batch_exceeds_upper_bound",
                    "error",
                    f"chapters={chapters} exceeds upper_bound={MAX_REAL_LLM_CHAPTER_BATCH_SIZE}",
                )
            )
        if max(batch_schedule) > MAX_REAL_LLM_CHAPTER_BATCH_SIZE:
            errors.append(
                GateIssue(
                    "batch_schedule_exceeds_upper_bound",
                    "error",
                    f"batch_schedule={list(batch_schedule)} exceeds upper_bound={MAX_REAL_LLM_CHAPTER_BATCH_SIZE}",
                )
            )
        if word_target < MIN_LONGFORM_WORD_TARGET:
            issue = GateIssue(
                "word_target_below_short_chapter_threshold",
                "error" if not dry_run else "warn",
                f"word_target={word_target} is below {MIN_LONGFORM_WORD_TARGET}; prior v1.9-5 low-cost runs produced short-chapter observations",
            )
            if dry_run:
                warnings.append(issue)
            else:
                errors.append(issue)
    if not _state_root_is_isolated(state_root):
        errors.append(
            GateIssue(
                "state_root_not_isolated_ops_path",
                "error",
                "state_root must stay under .ops/real_llm_harness to avoid production state overwrite",
            )
        )
    if not _output_is_under(json_output.parent, ".ops/validation"):
        warnings.append(GateIssue("json_output_not_under_validation", "warn", "JSON evidence should land under .ops/validation/**"))
    if not _output_is_under(report_output.parent, ".ops/reports"):
        warnings.append(GateIssue("report_output_not_under_reports", "warn", "Markdown evidence should land under .ops/reports/**"))
    if review_gate and not _output_is_under(review_output_root, ".ops/reviews"):
        warnings.append(GateIssue("review_output_not_under_ops_reviews", "warn", "review sidecar should land under .ops/reviews/**"))
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": [asdict(item) for item in errors],
        "warnings": [asdict(item) for item in warnings],
        "checks": [
            "explicit_dry_run_or_run_mode",
            "real_llm_call_budget",
            "isolated_state_root",
            "isolated_validation_outputs",
            "longform_batch_upper_bound",
            "review_gate_configured" if review_gate else "review_gate_disabled_by_operator",
        ],
    }


def _postflight_from_generation(profile: str, generation: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"status": "planned", "errors": [], "warnings": [], "generation_summary": {}}
    errors: list[GateIssue] = []
    warnings: list[GateIssue] = []
    if not generation.get("passed"):
        errors.append(GateIssue("generation_not_passed", "error", "underlying real LLM smoke did not pass"))
    if profile == "longform-small-batch":
        drift = generation.get("drift_report") or {}
        failed_chapters = [
            run
            for run in generation.get("chapter_runs", [])
            if isinstance(run, dict) and run.get("status") == "failed"
        ]
        failed_batches = [
            run
            for run in generation.get("batch_runs", [])
            if isinstance(run, dict) and run.get("status") == "failed"
        ]
        first_failed_chapter = failed_chapters[0] if failed_chapters else {}
        first_failed_batch = failed_batches[0] if failed_batches else {}
        if drift.get("status") != "stable":
            warnings.append(GateIssue("drift_needs_review", "warn", f"drift_status={drift.get('status')}"))
        summary = {
            "requested_chapters": generation.get("requested_chapters"),
            "completed_chapters": generation.get("completed_chapters"),
            "drift_status": drift.get("status"),
            "failed_chapter": first_failed_chapter.get("chapter_no"),
            "failure_reason": first_failed_chapter.get("error") or first_failed_batch.get("error") or "",
            "failed_batches": [run.get("batch_no") for run in failed_batches if run.get("batch_no") is not None],
            "short_chapters": drift.get("short_chapters", []),
            "missing_foreshadow_chapters": drift.get("missing_foreshadow_chapters", []),
        }
    else:
        gap = generation.get("gap_report") or {}
        if gap.get("status") != "clear":
            warnings.append(GateIssue("single_chapter_gap_report_open", "warn", f"gap_status={gap.get('status')}"))
        summary = {
            "output_path": generation.get("output_path"),
            "artifact_execution_mode": generation.get("artifact_execution_mode"),
            "gap_status": gap.get("status"),
        }
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": [asdict(item) for item in errors],
        "warnings": [asdict(item) for item in warnings],
        "generation_summary": summary,
    }


def _run_review_gate(
    *,
    book_id: str,
    state_root: Path,
    review_output_root: Path,
    dry_run: bool,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {"status": "disabled", "errors": [], "warnings": [], "report": None}
    if dry_run:
        return {"status": "planned", "errors": [], "warnings": [], "report": None}
    state_dir = state_root / book_id
    if not any(state_dir.glob("chapter_*.md")):
        return {
            "status": "no_chapters",
            "errors": [],
            "warnings": [
                asdict(
                    GateIssue(
                        "review_gate_no_chapters",
                        "warn",
                        "review gate skipped because generation produced no chapter artifacts",
                    )
                )
            ],
            "report": None,
        }
    result = export_review_report(
        book_id,
        run_id="v2-3-real-llm-review-gate",
        state_root=state_root,
        output_root=review_output_root,
    )
    report_path = Path(result["output_dir"]) / "review_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    hard_gate = (payload.get("longform_quality_gate") or {}).get("hard_gate") or {}
    errors: list[GateIssue] = []
    warnings: list[GateIssue] = []
    if payload.get("mode") != "warn_only" or payload.get("auto_edit") is not False:
        errors.append(GateIssue("review_not_warn_only", "error", "review gate must remain warn-only and must not auto-edit"))
    projection = payload.get("projection") or {}
    if projection.get("writes_runtime_state") is not False:
        errors.append(GateIssue("review_writes_runtime_state", "error", "review gate must not write runtime state"))
    if hard_gate.get("should_block_next_real_llm_batch"):
        warnings.append(
            GateIssue(
                "review_hard_gate_blocks_next_batch",
                "warn",
                f"block_reasons={hard_gate.get('block_reasons', [])}",
            )
        )
    status = "FAIL" if errors else ("blocked" if warnings else "PASS")
    return {
        "status": status,
        "errors": [asdict(item) for item in errors],
        "warnings": [asdict(item) for item in warnings],
        "report": {
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "issue_count": (payload.get("summary") or {}).get("issue_count"),
            "review_report": _repo_rel(report_path),
            "hard_gate": hard_gate,
        },
    }


def _build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# v2.3 Real LLM Harness Report",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- profile: `{payload['profile']}`",
        f"- dry_run: `{payload['dry_run']}`",
        f"- passed: `{payload['passed']}`",
        f"- real_llm_executed: `{payload['real_llm_executed']}`",
        f"- endpoint: `{payload['endpoint']}`",
        f"- book_id: `{payload['book_id']}`",
        "",
        "## Preflight",
        "",
        f"- status: `{payload['preflight']['status']}`",
    ]
    for error in payload["preflight"]["errors"]:
        lines.append(f"- error `{error['code']}`: {error['detail']}")
    for warning in payload["preflight"]["warnings"]:
        lines.append(f"- warning `{warning['code']}`: {warning['detail']}")
    lines.extend(
        [
            "",
            "## Cost Boundary",
            "",
            f"- estimated_real_llm_calls: `{payload['cost_boundary']['estimated_real_llm_calls']}`",
            f"- max_real_llm_calls: `{payload['cost_boundary']['max_real_llm_calls']}`",
            f"- requested_chapters: `{payload['cost_boundary']['requested_chapters']}`",
            f"- max_chapters: `{payload['cost_boundary']['max_chapters']}`",
            f"- word_target: `{payload['cost_boundary']['word_target']}`",
            "",
            "## Isolation",
            "",
            f"- state_root: `{payload['isolation']['state_root']}`",
            f"- json_output: `{payload['isolation']['json_output']}`",
            f"- report_output: `{payload['isolation']['report_output']}`",
            f"- review_output_root: `{payload['isolation']['review_output_root']}`",
            "",
            "## Postflight",
            "",
            f"- status: `{payload['postflight']['status']}`",
            f"- generation_summary: `{payload['postflight']['generation_summary']}`",
            "",
            "## Review Gate",
            "",
            f"- status: `{payload['review_gate']['status']}`",
        ]
    )
    report = payload["review_gate"].get("report")
    if report:
        lines.append(f"- report: `{report.get('review_report')}`")
        lines.append(f"- issue_count: `{report.get('issue_count')}`")
        lines.append(f"- hard_gate_blocks_next_batch: `{(report.get('hard_gate') or {}).get('should_block_next_real_llm_batch')}`")
    for warning in payload["review_gate"].get("warnings", []):
        lines.append(f"- warning `{warning['code']}`: {warning['detail']}")
    lines.extend(["", "## Residual Risk", ""])
    for risk in payload["residual_risk"]:
        lines.append(f"- `{risk['code']}` ({risk['severity']}): {risk['mitigation']}")
    lines.extend(["", "## Gates", ""])
    for gate in payload["gates"]:
        lines.append(f"- `{gate}`")
    lines.append("")
    lines.append("This harness makes real calls repeatable; it does not make smoke evidence equal production readiness.")
    return "\n".join(lines) + "\n"


def _residual_risk(*, dry_run: bool, profile: str) -> list[dict[str, str]]:
    risks = [
        {
            "code": "real_llm_variability",
            "severity": "medium",
            "mitigation": "record endpoint, isolated state_root, generated artifacts, and review gate output for each run.",
        },
        {
            "code": "review_gate_is_report_only",
            "severity": "medium",
            "mitigation": "treat review hard-gate blocks as stop signals; do not auto-edit story text or write truth from reports.",
        },
        {
            "code": "longform_quality_not_proven_by_harness",
            "severity": "medium",
            "mitigation": "use small isolated batches and compare review output before widening any production run.",
        },
    ]
    if dry_run:
        risks.insert(
            0,
            {
                "code": "dry_run_has_no_quality_evidence",
                "severity": "high",
                "mitigation": "run with --run only after preflight is PASS and the operator accepts the cost boundary.",
            },
        )
    if profile == "longform-small-batch":
        risks.append(
            {
                "code": "v1_7_5_followup_still_required",
                "severity": "medium",
                "mitigation": "after prompt continuity repair, only run isolated small-batch validation and rerun review; do not expand batch size directly.",
            }
        )
    return risks


def _write_outputs(payload: dict[str, Any], json_output: Path, report_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_output.write_text(_build_report(payload), encoding="utf-8")


def run_harness(
    *,
    profile: str = DEFAULT_PROFILE,
    book_id: str = DEFAULT_BOOK_ID,
    endpoint: str = DEFAULT_ENDPOINT,
    state_root: Path = DEFAULT_STATE_ROOT,
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
    review_output_root: Path = DEFAULT_REVIEW_OUTPUT_ROOT,
    chapters: int = DEFAULT_CHAPTER_BATCH_SIZE,
    word_target: int = 4000,
    batch_schedule: str | Sequence[int] = "4",
    dry_run: bool = True,
    review_gate: bool = True,
) -> dict[str, Any]:
    state_root = Path(state_root)
    json_output = Path(json_output)
    report_output = Path(report_output)
    review_output_root = Path(review_output_root)
    schedule = _parse_batch_schedule(batch_schedule)
    isolation = _build_isolation(state_root, json_output, report_output, review_output_root)
    cost = _cost_boundary(
        profile=profile,
        chapters=chapters,
        word_target=word_target,
        batch_schedule=schedule,
        dry_run=dry_run,
    )
    preflight = _preflight(
        profile=profile,
        endpoint=endpoint,
        state_root=state_root,
        json_output=json_output,
        report_output=report_output,
        review_output_root=review_output_root,
        chapters=chapters,
        word_target=word_target,
        batch_schedule=schedule,
        dry_run=dry_run,
        review_gate=review_gate,
    )

    real_llm_executed = False
    generation: dict[str, Any] = {}
    if not dry_run and preflight["status"] == "PASS":
        real_llm_executed = True
        if profile == "single-chapter-smoke":
            generation = run_smoke(
                book_id=book_id,
                endpoint=endpoint,
                state_root=state_root,
                json_output=json_output.with_name(f"{json_output.stem}_single_chapter.json"),
                report_output=report_output.with_name(f"{report_output.stem}_single_chapter.md"),
                word_target=word_target,
                dry_run=False,
            )
        else:
            generation = run_longform_smoke(
                book_id=book_id,
                endpoint=endpoint,
                state_root=state_root,
                json_output=json_output.with_name(f"{json_output.stem}_longform.json"),
                report_output=report_output.with_name(f"{report_output.stem}_longform.md"),
                chapters=chapters,
                word_target=word_target,
                batch_schedule=schedule,
                dry_run=False,
                resume=False,
            )
    postflight = (
        {"status": "skipped", "errors": [], "warnings": [], "generation_summary": {"reason": "preflight_failed"}}
        if preflight["status"] != "PASS"
        else _postflight_from_generation(profile, generation, dry_run=dry_run)
    )
    review = (
        {"status": "skipped", "errors": [], "warnings": [], "report": None}
        if preflight["status"] != "PASS"
        else _run_review_gate(
            book_id=book_id,
            state_root=state_root,
            review_output_root=review_output_root,
            dry_run=dry_run,
            enabled=review_gate,
        )
    )
    passed = (
        preflight["status"] == "PASS"
        and (dry_run or postflight["status"] == "PASS")
        and review["status"] in {"planned", "disabled", "PASS", "no_chapters"}
    )
    payload = {
        "harness_version": HARNESS_VERSION,
        "generated_from": "scripts/run_real_llm_harness.py",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": profile,
        "dry_run": dry_run,
        "passed": passed,
        "real_llm_executed": real_llm_executed,
        "endpoint": endpoint,
        "book_id": book_id,
        "state_root": str(state_root),
        "json_output": str(json_output),
        "report_output": str(report_output),
        "review_output_root": str(review_output_root),
        "cost_boundary": cost,
        "isolation": isolation,
        "preflight": preflight,
        "postflight": postflight,
        "review_gate": review,
        "generation": generation,
        "residual_risk": _residual_risk(dry_run=dry_run, profile=profile),
        "gates": ["preflight", "cost_boundary", "isolated_output", "postflight", "review_gate"],
    }
    _write_outputs(payload, json_output, report_output)
    return payload


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=SUPPORTED_PROFILES, default=DEFAULT_PROFILE)
    parser.add_argument("--book-id", default=DEFAULT_BOOK_ID)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--review-output-root", type=Path, default=DEFAULT_REVIEW_OUTPUT_ROOT)
    parser.add_argument("--chapters", type=int, default=DEFAULT_CHAPTER_BATCH_SIZE)
    parser.add_argument("--word-target", type=int, default=4000)
    parser.add_argument("--batch-schedule", default="4")
    parser.add_argument("--no-review-gate", action="store_false", dest="review_gate")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    mode.add_argument("--run", dest="dry_run", action="store_false")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload = run_harness(
        profile=args.profile,
        book_id=args.book_id,
        endpoint=args.endpoint,
        state_root=args.state_root,
        json_output=args.json_output,
        report_output=args.report_output,
        review_output_root=args.review_output_root,
        chapters=args.chapters,
        word_target=args.word_target,
        batch_schedule=args.batch_schedule,
        dry_run=args.dry_run,
        review_gate=args.review_gate,
    )
    print(
        f"wrote {args.json_output} and {args.report_output}; "
        f"profile={payload['profile']} dry_run={payload['dry_run']} "
        f"preflight={payload['preflight']['status']} passed={payload['passed']}"
    )
    return 0 if payload["passed"] or payload["dry_run"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
