#!/usr/bin/env python3
"""Validate the Ginga Harness Engineering map and self-check contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_MAP_PATH = Path(".ops/harness/README.md")
AGENTS_PATH = Path("AGENTS.md")
VERIFY_ALL_PATH = Path("scripts/verify_all.py")
SELF_PATH = Path("scripts/validate_harness_contracts.py")

REQUIRED_AGENTS_MARKERS = (
    "Harness Engineering",
    "STATUS.md",
    ".ops/validation/**",
    ".ops/reports/**",
    ".ops/governance/candidate_truth_gate.md",
    "StateIO",
    "真实 LLM",
)

REQUIRED_HARNESS_MARKERS = (
    "task_type",
    "docs_or_status",
    "architecture_boundary",
    "cli_or_workflow",
    "rag_or_prompt",
    "sidecar_or_observability",
    "real_llm_policy",
    "subagent_coordination",
    "scripts/validate_harness_contracts.py",
    "scripts/verify_all.py",
    ".ops/validation/**",
    ".ops/reports/**",
    "candidate-only",
    "report-only",
    "truth",
    "StateIO",
    "真实 LLM",
)

REQUIRED_VERIFY_ALL_MARKERS = (
    "scripts/validate_harness_contracts.py",
)


def _read_text(repo_root: Path, rel_path: Path, errors: list[str]) -> str:
    path = repo_root / rel_path
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"{rel_path}: missing required file")
        return ""


def _missing_markers(text: str, markers: Sequence[str]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def validate_repo(repo_root: Path | None = None) -> dict[str, object]:
    root = (repo_root or REPO_ROOT).resolve()
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    agents_text = _read_text(root, AGENTS_PATH, errors)
    harness_text = _read_text(root, HARNESS_MAP_PATH, errors)
    verify_all_text = _read_text(root, VERIFY_ALL_PATH, errors)

    if not (root / SELF_PATH).exists():
        errors.append(f"{SELF_PATH}: missing v2.1 self-check script")

    agents_missing = _missing_markers(agents_text, REQUIRED_AGENTS_MARKERS)
    if agents_missing:
        errors.append(f"{AGENTS_PATH}: missing Harness marker(s): {agents_missing}")
    checks.append(
        {
            "name": "AGENTS.md Harness Engineering entry",
            "status": "PASS" if not agents_missing else "FAIL",
            "missing": agents_missing,
        }
    )

    harness_missing = _missing_markers(harness_text, REQUIRED_HARNESS_MARKERS)
    if harness_missing:
        errors.append(f"{HARNESS_MAP_PATH}: missing Harness Map marker(s): {harness_missing}")
    checks.append(
        {
            "name": "v2.0 Harness Map",
            "status": "PASS" if not harness_missing else "FAIL",
            "missing": harness_missing,
        }
    )

    verify_missing = _missing_markers(verify_all_text, REQUIRED_VERIFY_ALL_MARKERS)
    if verify_missing:
        errors.append(f"{VERIFY_ALL_PATH}: missing Harness validator marker(s): {verify_missing}")
    checks.append(
        {
            "name": "v2.1 Harness self-check wiring",
            "status": "PASS" if not verify_missing else "FAIL",
            "missing": verify_missing,
        }
    )

    return {
        "status": "FAIL" if errors else "PASS",
        "repo_root": str(root),
        "checks": checks,
        "errors": errors,
    }


def print_report(report: dict[str, object]) -> None:
    print(f"{report['status']}: harness contracts")
    for check in report["checks"]:  # type: ignore[index]
        name = check["name"]  # type: ignore[index]
        status = check["status"]  # type: ignore[index]
        missing = check["missing"]  # type: ignore[index]
        detail = "all required markers present" if not missing else f"missing {missing}"
        print(f"{status}: {name} - {detail}")
    errors = report["errors"]  # type: ignore[index]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"ERROR: {error}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write structured JSON report to this path")
    args = parser.parse_args(argv)

    report = validate_repo(REPO_ROOT)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_report(report)
    return 1 if report["errors"] else 0  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
