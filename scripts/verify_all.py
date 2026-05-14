#!/usr/bin/env python3
"""Run the repository verification gate and summarize results."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
TAIL_LINES = 20
TAIL_CHARS = 4000


@dataclass
class CommandResult:
    command: str
    exit_code: int
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str


BASELINE_COMMANDS: list[list[str]] = [
    ["python", "-m", "unittest", "discover", "-s", "ginga_platform", "-p", "test_*.py"],
    ["python3", "scripts/validate_architecture_contracts.py"],
    ["python3", "scripts/validate_prompt_frontmatter.py", "--strict"],
    ["python3", "scripts/report_prompt_quality.py", "foundation/assets/prompts"],
    [
        "python3",
        "scripts/validate_methodology_assets.py",
        "foundation/assets/methodology",
        "foundation/schema/methodology.yaml",
    ],
]

PRESSURE_COMMAND = ["python3", "scripts/run_s3_pressure_tests.py"]
RAG_EVAL_COMMAND = ["python3", "scripts/evaluate_rag_recall.py"]


def shell_quote(value: str) -> str:
    if value and all(ch.isalnum() or ch in "@%_+=:,./-" for ch in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def command_text(command: Sequence[str]) -> str:
    return " ".join(shell_quote(part) for part in command)


def tail_text(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    tail = "\n".join(lines[-TAIL_LINES:])
    if len(tail) > TAIL_CHARS:
        tail = tail[-TAIL_CHARS:]
    return tail


def run_command(command: Sequence[str]) -> CommandResult:
    start = time.monotonic()
    completed = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = time.monotonic() - start
    return CommandResult(
        command=command_text(command),
        exit_code=completed.returncode,
        duration_seconds=round(duration, 3),
        stdout_tail=tail_text(completed.stdout),
        stderr_tail=tail_text(completed.stderr),
    )


def print_result(result: CommandResult) -> None:
    status = "PASS" if result.exit_code == 0 else "FAIL"
    print(f"[{status}] {result.duration_seconds:.3f}s exit={result.exit_code} :: {result.command}")
    if result.stdout_tail:
        print("--- stdout tail ---")
        print(result.stdout_tail)
    if result.stderr_tail:
        print("--- stderr tail ---")
        print(result.stderr_tail)
    print()


def build_commands(args: argparse.Namespace) -> list[list[str]]:
    commands = list(BASELINE_COMMANDS)
    if args.quick:
        return commands
    if args.include_pressure:
        commands.append(PRESSURE_COMMAND)
    if args.include_rag_eval:
        commands.append(RAG_EVAL_COMMAND)
    return commands


def write_json(path: Path, results: Sequence[CommandResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_epoch": round(time.time(), 3),
        "repo_root": str(REPO_ROOT),
        "passed": all(result.exit_code == 0 for result in results),
        "results": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="run only the five baseline checks; this is also the default without include flags",
    )
    parser.add_argument(
        "--include-pressure",
        action="store_true",
        help="also run scripts/run_s3_pressure_tests.py",
    )
    parser.add_argument(
        "--include-rag-eval",
        action="store_true",
        help="also run scripts/evaluate_rag_recall.py",
    )
    parser.add_argument("--json", type=Path, help="write a JSON summary to this path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    commands = build_commands(args)
    results: list[CommandResult] = []

    print(f"Verification start: {len(commands)} command(s)")
    print(f"Repo root: {REPO_ROOT}")
    print()

    for command in commands:
        result = run_command(command)
        results.append(result)
        print_result(result)

    failed = [result for result in results if result.exit_code != 0]
    total_seconds = sum(result.duration_seconds for result in results)

    print("Summary")
    print(f"  total: {len(results)}")
    print(f"  passed: {len(results) - len(failed)}")
    print(f"  failed: {len(failed)}")
    print(f"  duration_seconds: {total_seconds:.3f}")
    if failed:
        print("  failed_commands:")
        for result in failed:
            print(f"    - {result.command} (exit {result.exit_code})")

    if args.json:
        write_json(args.json, results)
        print(f"  json: {args.json}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
