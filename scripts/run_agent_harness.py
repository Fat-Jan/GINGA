#!/usr/bin/env python3
"""Run the offline agent harness.

This harness exercises the public ``ginga`` argparse entrypoint with a
temporary ``state_root`` and mock LLM output. It proves CLI wiring, StateIO
state-domain persistence, audit logging, chapter artifact boundaries, sidecar
report-only boundaries, and error exit codes. It does not prove real LLM quality
or production readiness.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
MOCK_MODE = "mock_harness"
CLI_STATE_ONLY_MODE = "cli_state_only"
CLI_REPORT_ONLY_MODE = "cli_report_only"
DISCLAIMER = "mock_harness does not prove production readiness or real LLM demo completion"
STATE_DOMAINS = ("locked", "entity_runtime", "workspace", "retrieved", "audit_log")


@dataclass
class HarnessCase:
    name: str
    argv: list[str]
    expected_exit_code: int
    exit_code: int
    execution_mode: str
    stdout_tail: str
    stderr_tail: str
    checks: dict[str, bool]

    @property
    def passed(self) -> bool:
        return self.exit_code == self.expected_exit_code and all(self.checks.values())


def _normalization_roots(state_root: Path) -> tuple[tuple[str, str], ...]:
    return (
        (str(state_root), "<temporary mock harness state_root>"),
        (str(state_root.parent), "<temporary mock harness root>"),
    )


def _normalize_output(text: str, state_root: Path) -> str:
    normalized = text
    for raw, marker in _normalization_roots(state_root):
        normalized = normalized.replace(raw, marker)
    return normalized


def _normalize_argv(argv: Sequence[str], state_root: Path) -> list[str]:
    return [_normalize_output(str(item), state_root) for item in argv]


def _tail(text: str, limit: int = 1600) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


@contextlib.contextmanager
def _temporary_cwd(cwd: Path | None):
    if cwd is None:
        yield
        return
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        yield
    finally:
        os.chdir(previous)


def _invoke_cli(argv: Sequence[str], *, cwd: Path | None = None) -> tuple[int, str, str]:
    from ginga_platform.orchestrator.cli.__main__ import main as cli_main

    stdout = io.StringIO()
    stderr = io.StringIO()
    with _temporary_cwd(cwd), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = cli_main(list(argv))
    return int(exit_code), stdout.getvalue(), stderr.getvalue()


def _state_dir(state_root: Path, book_id: str) -> Path:
    return state_root / book_id


def _state_domains_exist(state_root: Path, book_id: str) -> bool:
    book_dir = _state_dir(state_root, book_id)
    return all((book_dir / f"{domain}.yaml").exists() for domain in STATE_DOMAINS)


def _chapter_files(state_root: Path, book_id: str) -> list[Path]:
    return sorted(_state_dir(state_root, book_id).glob("chapter_*.md"))


def _audit_entries(state_root: Path, book_id: str) -> list[dict]:
    audit_path = _state_dir(state_root, book_id) / "audit_log.yaml"
    if not audit_path.exists():
        return []
    raw = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
    entries = raw.get("entries", raw if isinstance(raw, list) else [])
    return entries if isinstance(entries, list) else []


def _has_artifact_audit(state_root: Path, book_id: str, *, mode: str = MOCK_MODE) -> bool:
    for entry in _audit_entries(state_root, book_id):
        payload = entry.get("payload", {}) if isinstance(entry, dict) else {}
        if payload.get("artifact_type") == "chapter_text" and payload.get("execution_mode") == mode:
            return True
    return False


def _has_audit_source_prefix(state_root: Path, book_id: str, prefix: str) -> bool:
    return any(
        isinstance(entry.get("source"), str) and entry["source"].startswith(prefix)
        for entry in _audit_entries(state_root, book_id)
    )


def _has_audit_message(state_root: Path, book_id: str, needle: str) -> bool:
    return any(needle in str(entry.get("msg", "")) for entry in _audit_entries(state_root, book_id))


def _seed_book(state_root: Path, book_id: str) -> None:
    exit_code, stdout, stderr = _invoke_cli(
        [
            "init",
            book_id,
            "--topic",
            "玄幻黑暗",
            "--premise",
            f"{book_id} offline harness premise",
            "--word-target",
            "50000",
            "--state-root",
            str(state_root),
        ]
    )
    if exit_code != 0:
        raise RuntimeError(f"failed to seed {book_id}: exit={exit_code} stdout={stdout} stderr={stderr}")


def _seed_book_with_chapter(state_root: Path, book_id: str) -> None:
    _seed_book(state_root, book_id)
    exit_code, stdout, stderr = _invoke_cli(
        [
            "run",
            book_id,
            "--mock-llm",
            "--word-target",
            "800",
            "--state-root",
            str(state_root),
        ]
    )
    if exit_code != 0:
        raise RuntimeError(f"failed to run seeded {book_id}: exit={exit_code} stdout={stdout} stderr={stderr}")


def _ops_root(state_root: Path) -> Path:
    return state_root.parent / ".ops"


def _json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _json_stdout(stdout: str) -> dict[str, Any]:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _write_market_fixture(state_root: Path) -> Path:
    fixture_path = state_root.parent / "fixtures" / "harness_market_fixture.json"
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = {
        "fixture_id": "harness-market",
        "collected_at": "2026-05-16T00:00:00Z",
        "sources": [
            {
                "source_id": "offline-ranking-1",
                "platform": "offline_fixture",
                "url": "https://example.invalid/harness-market",
                "collected_at": "2026-05-16T00:00:00Z",
                "data_quality": "synthetic_harness_fixture",
                "items": [
                    {
                        "rank": 1,
                        "title": "寒潮边城",
                        "genre": "玄幻黑暗",
                        "signals": ["快节奏开局", "黑暗升级", "低频锚点"],
                        "summary": "离线 fixture 只保留结构化市场信号。",
                        "raw_text": "EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK",
                    }
                ],
            }
        ],
    }
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return fixture_path


def _write_evidence_file(state_root: Path) -> Path:
    evidence_path = state_root.parent / "fixtures" / "harness_evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence = {
        "kind": "ReviewDeslopReport",
        "summary": "citation-only harness evidence",
        "body": "SENTINEL_FULL_TEXT_SHOULD_NOT_COPY",
    }
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence_path


def _seed_migration_audit_tree(state_root: Path) -> Path:
    root = state_root.parent
    clean = root / "foundation" / "assets" / "methodology" / "clean.md"
    source = root / ".ops" / "book_analysis" / "run-1" / "source.md"
    clean.parent.mkdir(parents=True, exist_ok=True)
    source.parent.mkdir(parents=True, exist_ok=True)
    clean.write_text("# Clean Methodology\n\nHarness clean source.\n", encoding="utf-8")
    source.write_text("# Imported Analysis Source\n\nBOOK_ANALYSIS_SENTINEL\n", encoding="utf-8")
    return root


def _case(
    *,
    name: str,
    argv: list[str],
    expected_exit_code: int,
    checks: dict[str, bool],
) -> HarnessCase:
    exit_code, stdout, stderr = _invoke_cli(argv)
    return HarnessCase(
        name=name,
        argv=argv,
        expected_exit_code=expected_exit_code,
        exit_code=exit_code,
        execution_mode=MOCK_MODE if "--mock-llm" in argv else "cli_state_only",
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        checks=checks,
    )


def _run_case_and_check(
    *,
    name: str,
    argv: list[str],
    expected_exit_code: int,
    state_root: Path,
    check_fn,
    execution_mode: str | None = None,
    cwd: Path | None = None,
) -> HarnessCase:
    exit_code, stdout, stderr = _invoke_cli(argv, cwd=cwd)
    checks = check_fn(exit_code, stdout, stderr)
    return HarnessCase(
        name=name,
        argv=_normalize_argv(argv, state_root),
        expected_exit_code=expected_exit_code,
        exit_code=exit_code,
        execution_mode=execution_mode or (MOCK_MODE if "--mock-llm" in argv else CLI_STATE_ONLY_MODE),
        stdout_tail=_tail(_normalize_output(stdout, state_root)),
        stderr_tail=_tail(_normalize_output(stderr, state_root)),
        checks=checks,
    )


def run_harness(
    *,
    state_root: Path,
    json_output: Path,
    report_output: Path,
) -> dict:
    state_root = Path(state_root)
    json_output = Path(json_output)
    report_output = Path(report_output)
    state_root.mkdir(parents=True, exist_ok=True)

    cases: list[HarnessCase] = []

    init_book = "harness-init"
    init_argv = [
        "init",
        init_book,
        "--topic",
        "玄幻黑暗",
        "--premise",
        "offline harness init premise",
        "--word-target",
        "50000",
        "--state-root",
        str(state_root),
    ]
    cases.append(
        _run_case_and_check(
            name="init",
            argv=init_argv,
            expected_exit_code=0,
            state_root=state_root,
            check_fn=lambda _code, _out, _err: {
                "state_domains": _state_domains_exist(state_root, init_book),
                "audit_log": len(_audit_entries(state_root, init_book)) > 0,
            },
        )
    )

    single_book = "harness-single"
    _seed_book(state_root, single_book)
    cases.append(
        _run_case_and_check(
            name="single_run",
            argv=[
                "run",
                single_book,
                "--mock-llm",
                "--word-target",
                "800",
                "--state-root",
                str(state_root),
            ],
            expected_exit_code=0,
            state_root=state_root,
            check_fn=lambda _code, _out, _err: {
                "state_domains": _state_domains_exist(state_root, single_book),
                "chapter_artifact": len(_chapter_files(state_root, single_book)) == 1,
                "artifact_audit": _has_artifact_audit(state_root, single_book),
                "workflow_g_dispatch": _has_audit_source_prefix(
                    state_root, single_book, "step_dispatch:G_chapter_draft"
                ),
                "workflow_v1_dispatch": _has_audit_source_prefix(
                    state_root, single_book, "step_dispatch:V1_release_check"
                ),
                "skill_router": _has_audit_message(
                    state_root, single_book, "skill_router selected dark-fantasy-ultimate-engine"
                ),
                "adapter_transform": _has_audit_message(
                    state_root, single_book, "dark_fantasy_adapter.output_transform applied"
                ),
                "rollup_audit": any(
                    "rolled up" in entry.get("msg", "") for entry in _audit_entries(state_root, single_book)
                ),
            },
        )
    )

    multi_book = "harness-multi"
    _seed_book(state_root, multi_book)
    cases.append(
        _run_case_and_check(
            name="multi_chapter",
            argv=[
                "run",
                multi_book,
                "--mock-llm",
                "--chapters",
                "2",
                "--word-target",
                "1200",
                "--state-root",
                str(state_root),
            ],
            expected_exit_code=0,
            state_root=state_root,
            check_fn=lambda _code, _out, _err: {
                "state_domains": _state_domains_exist(state_root, multi_book),
                "chapter_artifacts": [path.name for path in _chapter_files(state_root, multi_book)]
                == ["chapter_01.md", "chapter_02.md"],
                "artifact_audit": _has_artifact_audit(state_root, multi_book),
                "dod_audit": any(
                    "V1 DoD" in entry.get("msg", "") for entry in _audit_entries(state_root, multi_book)
                ),
            },
        )
    )

    immersive_book = "harness-immersive"
    _seed_book(state_root, immersive_book)
    cases.append(
        _run_case_and_check(
            name="immersive",
            argv=[
                "run",
                immersive_book,
                "--mock-llm",
                "--immersive",
                "--chapters",
                "2",
                "--word-target",
                "800",
                "--state-root",
                str(state_root),
            ],
            expected_exit_code=0,
            state_root=state_root,
            check_fn=lambda _code, _out, _err: {
                "state_domains": _state_domains_exist(state_root, immersive_book),
                "chapter_artifacts": [path.name for path in _chapter_files(state_root, immersive_book)]
                == ["chapter_01.md", "chapter_02.md"],
                "artifact_audit": _has_artifact_audit(state_root, immersive_book),
                "batch_audit": any(
                    "chapters batch applied" in entry.get("msg", "")
                    for entry in _audit_entries(state_root, immersive_book)
                ),
            },
        )
    )

    cases.append(
        _run_case_and_check(
            name="missing_state_error",
            argv=[
                "run",
                "harness-missing",
                "--mock-llm",
                "--state-root",
                str(state_root),
            ],
            expected_exit_code=1,
            state_root=state_root,
            check_fn=lambda code, _out, err: {
                "exit_code_nonzero": code == 1,
                "error_message": "state seed not found" in err,
                "no_chapter_artifact": len(_chapter_files(state_root, "harness-missing")) == 0,
            },
        )
    )

    ops_root = _ops_root(state_root)
    sidecar_book = "harness-sidecar"
    _seed_book_with_chapter(state_root, sidecar_book)

    book_view_path = ops_root / "book_views" / sidecar_book / "harness-inspect" / "book_view.json"
    cases.append(
        _run_case_and_check(
            name="inspect_book_view",
            argv=[
                "inspect",
                sidecar_book,
                "--run-id",
                "harness-inspect",
                "--state-root",
                str(state_root),
                "--output-root",
                str(ops_root / "book_views"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "book_view_report": book_view_path.is_file(),
                "state_root_not_nested_ops": not (state_root / sidecar_book / ".ops").exists(),
                "projection_read_only": (
                    _json_file(book_view_path).get("projection", {}).get("truth_source") == "StateIO"
                    and _json_file(book_view_path).get("projection", {}).get("is_state_truth") is False
                    and _json_file(book_view_path).get("projection", {}).get("writes_runtime_state") is False
                ),
            },
        )
    )

    cases.append(
        _run_case_and_check(
            name="query_book_view",
            argv=[
                "query",
                sidecar_book,
                "mock_harness",
                "--limit",
                "5",
                "--state-root",
                str(state_root),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, out, _err: {
                "stdout_json": _json_stdout(out).get("mode") == "read_only",
                "matches": "match_count" in _json_stdout(out),
                "no_book_analysis_sentinel": "BOOK_ANALYSIS_SENTINEL" not in out,
            },
        )
    )

    review_path = ops_root / "reviews" / sidecar_book / "harness-review" / "review_report.json"
    cases.append(
        _run_case_and_check(
            name="review_sidecar",
            argv=[
                "review",
                sidecar_book,
                "--run-id",
                "harness-review",
                "--state-root",
                str(state_root),
                "--output-root",
                str(ops_root / "reviews"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "review_report": review_path.is_file(),
                "warn_only": _json_file(review_path).get("mode") == "warn_only",
                "no_auto_edit": _json_file(review_path).get("auto_edit") is False,
                "projection_read_only": _json_file(review_path).get("projection", {}).get("writes_runtime_state")
                is False,
            },
        )
    )

    market_fixture = _write_market_fixture(state_root)
    market_path = ops_root / "market_research" / "harness-market" / "harness-market" / "market_report.json"
    cases.append(
        _run_case_and_check(
            name="market_sidecar",
            argv=[
                "market",
                "harness-market",
                "--run-id",
                "harness-market",
                "--fixture",
                str(market_fixture),
                "--authorize",
                "--output-root",
                str(ops_root / "market_research"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "market_report": market_path.is_file(),
                "offline_fixture": _json_file(market_path).get("collection_mode") == "offline_fixture",
                "authorized": _json_file(market_path).get("authorization", {}).get("explicit") is True,
                "projection_read_only": _json_file(market_path).get("projection", {}).get("writes_runtime_state")
                is False,
                "rag_ineligible": _json_file(market_path).get("rag_policy", {}).get("default_rag_eligible")
                is False,
                "raw_text_stripped": "EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK"
                not in market_path.read_text(encoding="utf-8") if market_path.is_file() else False,
            },
        )
    )

    workflow_path = ops_root / "workflow_observability" / "harness-workflow" / "workflow_stage_report.json"
    cases.append(
        _run_case_and_check(
            name="observability_workflow_stages",
            argv=[
                "observability",
                "workflow-stages",
                "--run-id",
                "harness-workflow",
                "--output-root",
                str(ops_root / "workflow_observability"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "workflow_report": workflow_path.is_file(),
                "report_only": _json_file(workflow_path).get("mode") == "report_only",
                "does_not_run": _json_file(workflow_path).get("runs_workflow") is False,
                "does_not_write_state": _json_file(workflow_path).get("writes_runtime_state") is False,
                "has_stages": int(_json_file(workflow_path).get("stage_count") or 0) > 0,
            },
        )
    )

    evidence_file = _write_evidence_file(state_root)
    evidence_path = ops_root / "jury" / "evidence_packs" / "harness-evidence" / "evidence_pack.json"
    cases.append(
        _run_case_and_check(
            name="observability_evidence_pack",
            argv=[
                "observability",
                "evidence-pack",
                "--run-id",
                "harness-evidence",
                "--evidence",
                str(evidence_file),
                "--output-root",
                str(ops_root / "jury" / "evidence_packs"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "evidence_pack": evidence_path.is_file(),
                "report_only": _json_file(evidence_path).get("mode") == "report_only",
                "one_evidence": _json_file(evidence_path).get("evidence_count") == 1,
                "does_not_write_state": _json_file(evidence_path).get("writes_runtime_state") is False,
                "body_not_copied": "SENTINEL_FULL_TEXT_SHOULD_NOT_COPY"
                not in evidence_path.read_text(encoding="utf-8") if evidence_path.is_file() else False,
            },
        )
    )

    migration_root = _seed_migration_audit_tree(state_root)
    migration_path = ops_root / "migration_audit" / "harness-migration" / "migration_audit.json"
    cases.append(
        _run_case_and_check(
            name="observability_migration_audit",
            argv=[
                "observability",
                "migration-audit",
                "--run-id",
                "harness-migration",
                "--scan-root",
                str(migration_root / "foundation"),
                "--scan-root",
                str(migration_root / ".ops" / "book_analysis"),
                "--output-root",
                str(ops_root / "migration_audit"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            cwd=migration_root,
            check_fn=lambda _code, _out, _err: {
                "migration_report": migration_path.is_file(),
                "report_only": _json_file(migration_path).get("mode") == "report_only",
                "no_auto_migrate": _json_file(migration_path).get("auto_migrate") is False,
                "does_not_write_state": _json_file(migration_path).get("writes_runtime_state") is False,
                "forbidden_hit": ".ops/book_analysis/run-1/source.md"
                in _json_file(migration_path).get("forbidden_source_hits", []),
            },
        )
    )

    topology_path = ops_root / "model_topology" / "harness-topology" / "model_topology_report.json"
    cases.append(
        _run_case_and_check(
            name="model_topology_observe",
            argv=[
                "model-topology",
                "observe",
                "--run-id",
                "harness-topology",
                "--output-root",
                str(ops_root / "model_topology"),
            ],
            expected_exit_code=0,
            state_root=state_root,
            execution_mode=CLI_REPORT_ONLY_MODE,
            check_fn=lambda _code, _out, _err: {
                "topology_report": topology_path.is_file(),
                "report_only": _json_file(topology_path).get("mode") == "report_only",
                "no_runtime_takeover": _json_file(topology_path).get("runtime_takeover") is False,
                "live_probe_disabled": _json_file(topology_path).get("probe_summary", {}).get("live_probe_enabled")
                is False,
                "role_matrix": bool(_json_file(topology_path).get("role_matrix")),
                "probes_not_run": all(
                    item.get("status") == "not_run" for item in _json_file(topology_path).get("probe_results", [])
                ),
            },
        )
    )

    payload = {
        "generated_from": "scripts/run_agent_harness.py",
        "execution_mode": MOCK_MODE,
        "disclaimer": DISCLAIMER,
        "matrix_version": "v2.2",
        "state_root": "<temporary mock harness state_root>",
        "passed": all(case.passed for case in cases),
        "cases": [asdict(case) | {"passed": case.passed} for case in cases],
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_output.write_text(_build_report(payload), encoding="utf-8")
    return payload


def _build_report(payload: dict) -> str:
    state_root = payload["state_root"]
    if "/ginga-agent-harness-" in state_root:
        state_root = "<temporary mock harness state_root>"
    lines = [
        "# Agent Harness Report",
        "",
        f"- matrix_version: `{payload.get('matrix_version', 'unknown')}`",
        f"- execution_mode: `{payload['execution_mode']}`",
        f"- disclaimer: {payload['disclaimer']}",
        f"- state_root: `{state_root}`",
        f"- passed: `{payload['passed']}`",
        "",
        "| case | exit | expected | passed | checks |",
        "|---|---:|---:|---|---|",
    ]
    for case in payload["cases"]:
        failed = [name for name, ok in case["checks"].items() if not ok]
        checks = "ok" if not failed else "failed: " + ", ".join(failed)
        lines.append(
            f"| {case['name']} | {case['exit_code']} | {case['expected_exit_code']} | {case['passed']} | {checks} |"
        )
    lines.append("")
    lines.append("This mock_harness run does not prove production readiness or real LLM demo completion.")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-root",
        type=Path,
        help="temporary runtime_state root; defaults to a TemporaryDirectory for CLI use",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=REPO_ROOT / ".ops" / "validation" / "agent_harness.json",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=REPO_ROOT / ".ops" / "reports" / "agent_harness_report.md",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.state_root is not None:
        payload = run_harness(
            state_root=args.state_root,
            json_output=args.json_output,
            report_output=args.report_output,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="ginga-agent-harness-") as d:
            payload = run_harness(
                state_root=Path(d) / "runtime_state",
                json_output=args.json_output,
                report_output=args.report_output,
            )
    print(
        f"wrote {args.json_output} and {args.report_output}; "
        f"execution_mode={payload['execution_mode']} passed={payload['passed']}"
    )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
