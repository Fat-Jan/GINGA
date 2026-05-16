#!/usr/bin/env python3
"""Validate Ginga multi-agent board governance invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BOARD = Path(".ops/subagents/board.json")

ALLOWED_STATUSES = {
    "queued",
    "assigned",
    "running",
    "validating",
    "done",
    "stale",
    "zombie",
    "retry_wait",
    "failed",
    "blocked",
}

REQUIRED_TASK_FIELDS = (
    "task_id",
    "title",
    "status",
    "owner",
    "owned_files",
    "expected_output",
    "verification",
    "created_at",
    "updated_at",
    "evidence",
    "blockers",
)

MODEL_CONTRACT_FIELDS = ("provider", "reason", "fallback")
BOUNDARY_TOKENS = (
    "harness",
    "subagent",
    "multi_agent",
    "multi-agent",
    "agent_harness",
    "real_llm",
    "real-llm",
    "run_real_llm",
    "model_topology",
)
MAIN_AGENT_TOKENS = ("main-agent", "main agent", "主 agent", "主控")
ROOT_WILDCARDS = {"*", "**", "./*", "./**", ".", "./"}


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text_blob(task: dict[str, Any]) -> str:
    parts: list[str] = []
    for value in task.values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
    return " ".join(parts).lower()


def _task_id(task: dict[str, Any], index: int) -> str:
    value = task.get("task_id")
    return str(value) if value else f"task[{index}]"


def _is_nontrivial(task: Any) -> bool:
    return isinstance(task, dict) and bool(task)


def _is_write_capable(task: dict[str, Any]) -> bool:
    mode = str(task.get("mode", "")).lower()
    if "write" in mode:
        return True

    owned_files = [str(item).lower() for item in _as_list(task.get("owned_files"))]
    if not owned_files:
        return False
    return any(not item.startswith("read-only:") and "(read-only)" not in item for item in owned_files)


def _is_active_task(task: dict[str, Any]) -> bool:
    return task.get("status") in {"queued", "assigned", "running", "validating", "blocked", "failed", "retry_wait"}


def _touches_governance_boundary(task: dict[str, Any]) -> bool:
    blob = _text_blob(task)
    return any(token in blob for token in BOUNDARY_TOKENS)


def _has_main_agent_validation(task: dict[str, Any]) -> bool:
    owner = str(task.get("owner", "")).lower()
    handoff = str(task.get("handoff_note", "")).lower()
    evidence = " ".join(str(item) for item in _as_list(task.get("evidence"))).lower()
    return any(token in owner or token in handoff or token in evidence for token in MAIN_AGENT_TOKENS)


def _add_check(checks: list[dict[str, Any]], name: str, errors: list[str], warnings: list[str]) -> None:
    checks.append(
        {
            "name": name,
            "status": "FAIL" if errors else "PASS",
            "errors": errors,
            "warnings": warnings,
        }
    )


def _is_legacy_warning(message: str) -> bool:
    return not message.startswith(("v2.", "v1.7-5-", "v1.9-", "P2-", "p2-"))


def _validate_task(task: dict[str, Any], index: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    task_name = _task_id(task, index)
    legacy_done = task.get("status") == "done" and not isinstance(task.get("model_contract"), dict)

    missing = [field for field in REQUIRED_TASK_FIELDS if field not in task]
    for field in missing:
        message = f"{task_name}: missing required field {field}"
        if legacy_done:
            warnings.append(message)
        else:
            errors.append(message)

    status = task.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"{task_name}: status {status!r} is not allowed")

    owned_files = task.get("owned_files")
    if "owned_files" in task and not isinstance(owned_files, list):
        errors.append(f"{task_name}: owned_files must be a list")
    if "evidence" in task and not isinstance(task.get("evidence"), list):
        errors.append(f"{task_name}: evidence must be a list")
    if "blockers" in task and not isinstance(task.get("blockers"), list):
        errors.append(f"{task_name}: blockers must be a list")

    write_capable = _is_write_capable(task)
    has_model_contract = isinstance(task.get("model_contract"), dict)
    if write_capable and not has_model_contract:
        message = f"{task_name}: write-capable-looking task is missing model_contract"
        if task.get("status") == "done":
            warnings.append(message)
        else:
            errors.append(message)

    if has_model_contract:
        contract = task["model_contract"]
        for field in MODEL_CONTRACT_FIELDS:
            if not contract.get(field):
                errors.append(f"{task_name}: model_contract missing {field}")
        if not contract.get("model") and not contract.get("model_tier"):
            errors.append(f"{task_name}: model_contract missing model or model_tier")

    if write_capable:
        for item in _as_list(task.get("owned_files")):
            if str(item).strip() in ROOT_WILDCARDS:
                errors.append(f"{task_name}: write-capable task owned_files may not use repo root wildcard")

    if _touches_governance_boundary(task) and not isinstance(task.get("forbidden_files"), list):
        message = f"{task_name}: forbidden_files required for harness/agent/real LLM boundary tasks"
        if legacy_done:
            warnings.append(message)
        else:
            errors.append(message)

    if task.get("status") == "done":
        if not _as_list(task.get("evidence")):
            message = f"{task_name}: done requires non-empty evidence"
            if legacy_done:
                warnings.append(message)
            else:
                errors.append(message)
        if not _has_main_agent_validation(task):
            message = f"{task_name}: done requires main-agent validation in owner, handoff_note, or evidence"
            if legacy_done:
                warnings.append(message)
            else:
                errors.append(message)

    return errors, warnings


def validate_board(board_path: Path | str = REPO_ROOT / DEFAULT_BOARD) -> dict[str, Any]:
    path = Path(board_path)
    if not path.is_absolute():
        path = REPO_ROOT / path

    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    try:
        board = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error = f"{_rel(path)}: board file missing"
        return {"status": "FAIL", "board": _rel(path), "checks": [], "errors": [error], "warnings": []}
    except json.JSONDecodeError as exc:
        error = f"{_rel(path)}: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
        return {"status": "FAIL", "board": _rel(path), "checks": [], "errors": [error], "warnings": []}

    shape_errors: list[str] = []
    if not isinstance(board, dict):
        shape_errors.append(f"{_rel(path)}: top-level board must be an object")
        tasks: list[Any] = []
    else:
        if not board.get("updated_at"):
            shape_errors.append(f"{_rel(path)}: missing top-level updated_at")
        if not isinstance(board.get("tasks"), list):
            shape_errors.append(f"{_rel(path)}: missing top-level tasks list")
            tasks = []
        else:
            tasks = board["tasks"]
    errors.extend(shape_errors)
    _add_check(checks, "board shape", shape_errors, [])

    task_errors: list[str] = []
    task_warnings: list[str] = []
    for index, task in enumerate(tasks):
        if not _is_nontrivial(task):
            task_errors.append(f"task[{index}]: task entry must be a non-empty object")
            continue
        current_errors, current_warnings = _validate_task(task, index)
        task_errors.extend(current_errors)
        task_warnings.extend(current_warnings)

    errors.extend(task_errors)
    current_warnings = [warning for warning in task_warnings if not _is_legacy_warning(warning)]
    legacy_warnings = [warning for warning in task_warnings if _is_legacy_warning(warning)]
    warnings.extend(current_warnings)
    _add_check(checks, "task governance invariants", task_errors, current_warnings)

    return {
        "status": "FAIL" if errors else "PASS",
        "board": _rel(path),
        "task_count": len(tasks),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "legacy_warnings": legacy_warnings,
    }


def write_markdown_report(result: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Multi-Agent Harness Report",
        "",
        f"- Status: {result['status']}",
        f"- Board: {result['board']}",
        f"- Task count: {result.get('task_count', 0)}",
        "",
        "## Checks",
        "",
    ]
    for check in result["checks"]:
        lines.append(f"- {check['status']}: {check['name']}")
        for error in check.get("errors", []):
            lines.append(f"  - ERROR: {error}")
        for warning in check.get("warnings", []):
            lines.append(f"  - WARNING: {warning}")

    if result["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in result["errors"])
    if result["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result["warnings"])
    if result.get("legacy_warnings"):
        lines.extend(["", "## Legacy Warnings", ""])
        lines.append("Older closed tasks predate v2.4 board governance; they are reported without failing or polluting terminal output.")
        lines.extend(f"- {warning}" for warning in result["legacy_warnings"])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_report(result: dict[str, Any]) -> None:
    print(f"{result['status']}: multi-agent harness board")
    print(f"board: {result['board']}")
    print(f"tasks: {result.get('task_count', 0)}")
    for check in result["checks"]:
        print(f"{check['status']}: {check['name']}")
    for error in result["errors"]:
        print(f"ERROR: {error}")
    for warning in result["warnings"]:
        print(f"WARNING: {warning}")
    legacy_count = len(result.get("legacy_warnings") or [])
    if legacy_count:
        print(f"legacy_warnings: {legacy_count} (see markdown/JSON report)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD, help="board JSON path")
    parser.add_argument("--json", type=Path, help="write structured validation JSON")
    parser.add_argument("--report", type=Path, help="write markdown validation report")
    args = parser.parse_args(argv)

    result = validate_board(args.board)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report:
        write_markdown_report(result, args.report)
    print_report(result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
