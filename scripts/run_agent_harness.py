#!/usr/bin/env python3
"""Run the P2-5 offline agent harness.

This harness exercises the public ``ginga`` argparse entrypoint with a
temporary ``state_root`` and mock LLM output. It proves CLI wiring, StateIO
state-domain persistence, audit logging, chapter artifact boundaries, and error
exit codes. It does not prove real LLM quality or production readiness.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
MOCK_MODE = "mock_harness"
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


def _normalize_output(text: str, state_root: Path) -> str:
    return text.replace(str(state_root), "<temporary mock harness state_root>")


def _normalize_argv(argv: Sequence[str], state_root: Path) -> list[str]:
    return [str(item).replace(str(state_root), "<temporary mock harness state_root>") for item in argv]


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
) -> HarnessCase:
    exit_code, stdout, stderr = _invoke_cli(argv)
    checks = check_fn(exit_code, stdout, stderr)
    return HarnessCase(
        name=name,
        argv=_normalize_argv(argv, state_root),
        expected_exit_code=expected_exit_code,
        exit_code=exit_code,
        execution_mode=MOCK_MODE if "--mock-llm" in argv else "cli_state_only",
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

    payload = {
        "generated_from": "scripts/run_agent_harness.py",
        "execution_mode": MOCK_MODE,
        "disclaimer": DISCLAIMER,
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
