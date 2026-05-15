#!/usr/bin/env python3
"""Run or plan the P2-7C single-chapter real LLM smoke demo.

Default mode is ``--dry-run`` so normal verification never calls ask-llm.
Use ``--run`` explicitly to spend one real model call through ``ginga run``.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REAL_MODE = "real_llm_demo"
DEFAULT_ENDPOINT = "xiaomi-tp"
DEFAULT_STATE_ROOT = REPO_ROOT / ".ops" / "real_llm_demo" / "p2-7c-smoke-state"
DEFAULT_JSON_OUTPUT = REPO_ROOT / ".ops" / "validation" / "real_llm_demo_smoke.json"
DEFAULT_REPORT_OUTPUT = REPO_ROOT / ".ops" / "reports" / "real_llm_demo_report.md"
DEFAULT_TOPIC = "玄幻黑暗"
DEFAULT_PREMISE = "失忆刺客醒来后发现短刃会吞吐微粒，他必须在第一重天堑前判断追杀者来自谁。"
WILL_NOT_OVERWRITE = (
    "foundation/runtime_state/demo-book",
    "foundation/runtime_state/s2-demo",
    "foundation/runtime_state/immersive-demo",
    ".ops/reports/agent_harness_report.md",
)


@dataclass
class CliRun:
    name: str
    argv: list[str]
    exit_code: int | None
    stdout_tail: str
    stderr_tail: str


def _tail(text: str, limit: int = 1600) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _invoke_cli(argv: Sequence[str]) -> tuple[int, str, str]:
    from ginga_platform.orchestrator.cli.__main__ import main as cli_main

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = cli_main(list(argv))
    return int(exit_code), stdout.getvalue(), stderr.getvalue()


def _planned_run(name: str, argv: list[str]) -> CliRun:
    return CliRun(name=name, argv=argv, exit_code=None, stdout_tail="", stderr_tail="")


def _actual_run(name: str, argv: list[str]) -> CliRun:
    exit_code, stdout, stderr = _invoke_cli(argv)
    return CliRun(
        name=name,
        argv=argv,
        exit_code=exit_code,
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
    )


def _audit_entries(state_root: Path, book_id: str) -> list[dict]:
    audit_path = state_root / book_id / "audit_log.yaml"
    if not audit_path.exists():
        return []
    raw = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
    entries = raw.get("entries", raw if isinstance(raw, list) else [])
    return entries if isinstance(entries, list) else []


def _artifact_execution_mode(state_root: Path, book_id: str) -> str | None:
    for entry in _audit_entries(state_root, book_id):
        payload = entry.get("payload", {}) if isinstance(entry, dict) else {}
        if payload.get("artifact_type") == "chapter_text":
            mode = payload.get("execution_mode")
            return str(mode) if mode else None
    return None


def _load_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _count_foreshadow_markers(text: str) -> int:
    return text.count("<!-- foreshadow:")


def _state_snapshot(state_root: Path, book_id: str) -> dict:
    book_dir = state_root / book_id
    domain_files = {
        "locked": book_dir / "locked.yaml",
        "entity_runtime": book_dir / "entity_runtime.yaml",
        "workspace": book_dir / "workspace.yaml",
        "retrieved": book_dir / "retrieved.yaml",
        "audit_log": book_dir / "audit_log.yaml",
    }
    state_domains = {name: path.exists() for name, path in domain_files.items()}
    chapter_path = book_dir / "chapter_01.md"
    chapter_text = chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else ""
    entity = _load_yaml_mapping(domain_files["entity_runtime"])
    locked = _load_yaml_mapping(domain_files["locked"])
    audit_entries = _audit_entries(state_root, book_id)
    has_material = any(state_domains.values()) or bool(chapter_text)
    return {
        "status": "present" if has_material else "missing",
        "state_dir": str(book_dir),
        "state_domains": state_domains,
        "audit_entries": len(audit_entries),
        "locked_summary": {
            "has_story_dna": bool(locked.get("STORY_DNA")),
            "has_world": bool(locked.get("WORLD")),
            "has_plot_architecture": bool(locked.get("PLOT_ARCHITECTURE")),
        },
        "runtime_summary": {
            "total_words": (entity.get("GLOBAL_SUMMARY") or {}).get("total_words"),
            "foreshadow_pool_size": len((entity.get("FORESHADOW_STATE") or {}).get("pool") or []),
            "particles": (entity.get("RESOURCE_LEDGER") or {}).get("particles"),
            "character_events": len(((entity.get("CHARACTER_STATE") or {}).get("protagonist") or {}).get("events") or []),
        },
        "chapter_artifact": {
            "exists": chapter_path.exists(),
            "path": str(chapter_path),
            "execution_mode": _artifact_execution_mode(state_root, book_id) if chapter_path.exists() else None,
            "chars": len(chapter_text),
            "foreshadow_markers": _count_foreshadow_markers(chapter_text),
        },
    }


def _build_context_snapshot(*, dry_run: bool, before_run: dict, after_run: dict) -> dict:
    return {
        "status": "planned" if dry_run else "captured",
        "before_run": before_run,
        "after_run": after_run,
        "observed_delta": {
            "chapter_created": (
                not before_run["chapter_artifact"]["exists"]
                and after_run["chapter_artifact"]["exists"]
            ),
            "audit_entries_added": max(0, int(after_run.get("audit_entries", 0)) - int(before_run.get("audit_entries", 0))),
            "total_words_after": after_run["runtime_summary"].get("total_words"),
            "foreshadow_pool_after": after_run["runtime_summary"].get("foreshadow_pool_size"),
        },
    }


def _build_gap_report(payload: dict) -> dict:
    if payload["dry_run"]:
        return {
            "status": "planned",
            "open_gaps": [
                {
                    "code": "real_call_not_executed",
                    "severity": "info",
                    "detail": "dry-run only records scope and expected artifact paths.",
                },
                {
                    "code": "production_quality_not_proven",
                    "severity": "warn",
                    "detail": "a smoke run is still required before reading chapter quality evidence.",
                },
            ],
        }
    after = payload["context_snapshot"]["after_run"]
    open_gaps: list[dict] = []
    failed_commands = [item["name"] for item in payload["commands"] if item["exit_code"] != 0]
    if failed_commands:
        open_gaps.append(
            {
                "code": "command_failed",
                "severity": "error",
                "detail": f"non-zero command exits: {', '.join(failed_commands)}",
            }
        )
    if not after["chapter_artifact"]["exists"]:
        open_gaps.append(
            {
                "code": "chapter_artifact_missing",
                "severity": "error",
                "detail": "chapter_01.md was not produced under the scoped state_root.",
            }
        )
    if payload.get("artifact_execution_mode") != REAL_MODE:
        open_gaps.append(
            {
                "code": "artifact_mode_not_real_llm_demo",
                "severity": "error",
                "detail": f"artifact_execution_mode={payload.get('artifact_execution_mode')!r}",
            }
        )
    if after["chapter_artifact"].get("foreshadow_markers", 0) == 0:
        open_gaps.append(
            {
                "code": "foreshadow_marker_missing",
                "severity": "warn",
                "detail": "chapter artifact has no machine-readable foreshadow marker.",
            }
        )
    open_gaps.extend(
        [
            {
                "code": "production_quality_not_proven",
                "severity": "warn",
                "detail": "single smoke does not prove long-form production readiness.",
            },
            {
                "code": "single_chapter_scope",
                "severity": "info",
                "detail": "this gate covers one chapter only; multi-chapter continuity remains outside scope.",
            },
        ]
    )
    return {"status": "needs_review" if open_gaps else "clear", "open_gaps": open_gaps}


def _residual_risks(dry_run: bool) -> list[dict]:
    risks = [
        {
            "code": "real_llm_variability",
            "severity": "medium",
            "mitigation": "record endpoint, prompt scope, artifact path, and rerun only with explicit approval.",
        },
        {
            "code": "single_chapter_scope",
            "severity": "medium",
            "mitigation": "treat this as smoke evidence, not a multi-chapter quality claim.",
        },
        {
            "code": "provider_quality_not_longform_proven",
            "severity": "medium",
            "mitigation": "keep mock harness as boundary regression and use real demo reports for quality review.",
        },
        {
            "code": "endpoint_cost_dependency",
            "severity": "low",
            "mitigation": "default to dry-run; real calls require explicit --run.",
        },
    ]
    if dry_run:
        risks.insert(
            0,
            {
                "code": "dry_run_has_no_quality_evidence",
                "severity": "high",
                "mitigation": "run with --run before using this as real LLM evidence.",
            },
        )
    return risks


def _payload_from_snapshots(
    *,
    book_id: str,
    endpoint: str,
    state_root: Path,
    json_output: Path,
    report_output: Path,
    word_target: int,
    topic: str,
    premise: str,
    dry_run: bool,
    runs: list[CliRun],
    before_snapshot: dict,
    after_snapshot: dict,
    refreshed_existing: bool = False,
) -> dict:
    output_dir = state_root / book_id
    chapter_path = output_dir / "chapter_01.md"
    chapter_exists = chapter_path.exists()
    artifact_mode = _artifact_execution_mode(state_root, book_id) if chapter_exists else None
    passed = bool(
        (refreshed_existing or not dry_run)
        and all(run.exit_code == 0 for run in runs)
        and chapter_exists
        and artifact_mode == REAL_MODE
    )
    payload = {
        "generated_from": "scripts/run_real_llm_smoke.py",
        "execution_mode": REAL_MODE,
        "dry_run": dry_run,
        "refreshed_existing": refreshed_existing,
        "passed": passed,
        "endpoint": endpoint,
        "book_id": book_id,
        "topic": topic,
        "premise": premise,
        "word_target": word_target,
        "state_root": str(state_root),
        "output_path": str(chapter_path),
        "artifact_execution_mode": artifact_mode,
        "cost_risk": "1 ask-llm call, max_tokens=4096, timeout=300s; smoke quality only, not production readiness",
        "will_not_overwrite": list(WILL_NOT_OVERWRITE),
        "commands": [asdict(run) for run in runs],
    }
    payload["context_snapshot"] = _build_context_snapshot(
        dry_run=dry_run,
        before_run=before_snapshot,
        after_run=after_snapshot,
    )
    payload["gap_report"] = _build_gap_report(payload)
    payload["residual_risk"] = _residual_risks(dry_run)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_output.write_text(_build_report(payload), encoding="utf-8")
    return payload


def _book_id_default() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"p2-7c-real-llm-smoke-{stamp}"


def run_smoke(
    *,
    book_id: str,
    endpoint: str,
    state_root: Path,
    json_output: Path,
    report_output: Path,
    word_target: int = 800,
    topic: str = DEFAULT_TOPIC,
    premise: str = DEFAULT_PREMISE,
    dry_run: bool = True,
) -> dict:
    state_root = Path(state_root)
    json_output = Path(json_output)
    report_output = Path(report_output)
    output_dir = state_root / book_id
    init_argv = [
        "init",
        book_id,
        "--topic",
        topic,
        "--premise",
        premise,
        "--word-target",
        "50000",
        "--state-root",
        str(state_root),
    ]
    run_argv = [
        "run",
        book_id,
        "--llm-endpoint",
        endpoint,
        "--word-target",
        str(word_target),
        "--state-root",
        str(state_root),
    ]
    status_argv = ["status", book_id, "--state-root", str(state_root)]

    before_snapshot = _state_snapshot(state_root, book_id)
    runs = [
        _planned_run("init", init_argv),
        _planned_run("run", run_argv),
        _planned_run("status", status_argv),
    ]
    if not dry_run:
        state_root.mkdir(parents=True, exist_ok=True)
        runs = [
            _actual_run("init", init_argv),
            _actual_run("run", run_argv),
            _actual_run("status", status_argv),
        ]

    after_snapshot = _state_snapshot(state_root, book_id)
    return _payload_from_snapshots(
        book_id=book_id,
        endpoint=endpoint,
        state_root=state_root,
        json_output=json_output,
        report_output=report_output,
        word_target=word_target,
        topic=topic,
        premise=premise,
        dry_run=dry_run,
        runs=runs,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )


def refresh_existing_smoke(
    *,
    book_id: str,
    endpoint: str,
    state_root: Path,
    json_output: Path,
    report_output: Path,
    word_target: int = 800,
    topic: str = DEFAULT_TOPIC,
    premise: str = DEFAULT_PREMISE,
) -> dict:
    state_root = Path(state_root)
    json_output = Path(json_output)
    report_output = Path(report_output)
    snapshot = _state_snapshot(state_root, book_id)
    runs = [
        CliRun(name="refresh_existing", argv=["refresh-existing", book_id, "--state-root", str(state_root)], exit_code=0, stdout_tail="", stderr_tail="")
    ]
    return _payload_from_snapshots(
        book_id=book_id,
        endpoint=endpoint,
        state_root=state_root,
        json_output=json_output,
        report_output=report_output,
        word_target=word_target,
        topic=topic,
        premise=premise,
        dry_run=False,
        runs=runs,
        before_snapshot=snapshot,
        after_snapshot=snapshot,
        refreshed_existing=True,
    )


def _build_report(payload: dict) -> str:
    lines = [
        "# P2-7C Real LLM Smoke Report",
        "",
        f"- execution_mode: `{payload['execution_mode']}`",
        f"- dry_run: `{payload['dry_run']}`",
        f"- passed: `{payload['passed']}`",
        f"- endpoint: `{payload['endpoint']}`",
        f"- book_id: `{payload['book_id']}`",
        f"- state_root: `{payload['state_root']}`",
        f"- output_path: `{payload['output_path']}`",
        f"- cost_risk: {payload['cost_risk']}",
        "",
        "## Commands",
        "",
    ]
    for item in payload["commands"]:
        exit_text = "planned" if item["exit_code"] is None else str(item["exit_code"])
        lines.append(f"- `{item['name']}` exit={exit_text}: `./ginga {' '.join(item['argv'])}`")
    snapshot = payload["context_snapshot"]
    after = snapshot["after_run"]
    lines.extend(
        [
            "",
            "## Context Snapshot",
            "",
            f"- status: `{snapshot['status']}`",
            f"- before_status: `{snapshot['before_run']['status']}`",
            f"- after_status: `{after['status']}`",
            f"- chapter_chars: `{after['chapter_artifact']['chars']}`",
            f"- artifact_execution_mode: `{after['chapter_artifact']['execution_mode']}`",
            f"- audit_entries: `{after['audit_entries']}`",
            f"- total_words_after: `{after['runtime_summary']['total_words']}`",
            f"- foreshadow_pool_after: `{after['runtime_summary']['foreshadow_pool_size']}`",
        ]
    )
    lines.extend(["", "## Gap Report", ""])
    lines.append(f"- status: `{payload['gap_report']['status']}`")
    for gap in payload["gap_report"]["open_gaps"]:
        lines.append(f"- `{gap['code']}` ({gap['severity']}): {gap['detail']}")
    lines.extend(["", "## Residual Risk", ""])
    for risk in payload["residual_risk"]:
        lines.append(f"- `{risk['code']}` ({risk['severity']}): {risk['mitigation']}")
    lines.extend(["", "## will_not_overwrite", ""])
    for path in payload["will_not_overwrite"]:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("A dry run records scope only. A real smoke run is not production readiness or long-chapter quality evidence.")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book-id", default=_book_id_default())
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--word-target", type=int, default=800)
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--premise", default=DEFAULT_PREMISE)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    mode.add_argument("--run", dest="dry_run", action="store_false", help="perform the real ask-llm smoke call")
    mode.add_argument(
        "--refresh-existing",
        action="store_true",
        help="rebuild JSON/Markdown from an existing scoped real smoke state without calling ask-llm",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.refresh_existing:
        payload = refresh_existing_smoke(
            book_id=args.book_id,
            endpoint=args.endpoint,
            state_root=args.state_root,
            json_output=args.json_output,
            report_output=args.report_output,
            word_target=args.word_target,
            topic=args.topic,
            premise=args.premise,
        )
    else:
        payload = run_smoke(
            book_id=args.book_id,
            endpoint=args.endpoint,
            state_root=args.state_root,
            json_output=args.json_output,
            report_output=args.report_output,
            word_target=args.word_target,
            topic=args.topic,
            premise=args.premise,
            dry_run=args.dry_run,
        )
    print(
        f"wrote {args.json_output} and {args.report_output}; "
        f"execution_mode={payload['execution_mode']} dry_run={payload['dry_run']} passed={payload['passed']}"
    )
    return 0 if payload["dry_run"] or payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
