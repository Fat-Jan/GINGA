#!/usr/bin/env python3
"""Validate the stage closeout template before creating a backup commit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = Path(".ops/harness/stage_closeout_template.md")

REQUIRED_SECTIONS = (
    "Objective",
    "Scope",
    "Truth Sync",
    "Verification Summary",
    "Residual Risks",
    "Commit Message",
    "Next Step",
)

REQUIRED_TEMPLATE_MARKERS = (
    "STATUS.md",
    "ROADMAP.md",
    "notepad.md",
    ".ops/validation/**",
    ".ops/reports/**",
    "verification command",
    "residual risk",
    "commit message",
)

CONTENT_TERMS = (
    "stage",
    "update",
)
VERIFICATION_TERMS = (
    "verification:",
    "verified:",
    "test:",
    "tests:",
    "validate",
)
RISK_TERMS = (
    "residual risk",
    "remaining risk",
)


def _new_report() -> dict[str, Any]:
    return {
        "status": "PASS",
        "checks": [],
        "errors": [],
        "warnings": [],
    }


def _add_check(report: dict[str, Any], name: str, ok: bool, detail: str) -> None:
    report["checks"].append(
        {
            "name": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        }
    )


def _add_error(report: dict[str, Any], message: str) -> None:
    report["errors"].append(message)


def _contains_section(text: str, section: str) -> bool:
    expected = f"## {section}".lower()
    return any(line.strip().lower().startswith(expected) for line in text.splitlines())


def _validate_template(template_path: Path, report: dict[str, Any]) -> None:
    if not template_path.exists():
        _add_error(report, f"{template_path}: missing stage closeout template")
        _add_check(report, "stage closeout template exists", False, str(template_path))
        return

    text = template_path.read_text(encoding="utf-8")
    _add_check(report, "stage closeout template exists", True, str(template_path))

    missing_sections = [section for section in REQUIRED_SECTIONS if not _contains_section(text, section)]
    if missing_sections:
        _add_error(report, f"{template_path}: missing section(s): {missing_sections}")
    _add_check(
        report,
        "stage closeout template sections",
        not missing_sections,
        "all required sections present" if not missing_sections else f"missing {missing_sections}",
    )

    lowered = text.lower()
    missing_markers = [
        marker for marker in REQUIRED_TEMPLATE_MARKERS if marker.lower() not in lowered
    ]
    if missing_markers:
        _add_error(report, f"{template_path}: missing marker(s): {missing_markers}")
    _add_check(
        report,
        "stage closeout template markers",
        not missing_markers,
        "all required markers present" if not missing_markers else f"missing {missing_markers}",
    )


def _validate_commit_message(commit_message: str | None, report: dict[str, Any]) -> None:
    if commit_message is None:
        report["warnings"].append("commit message check skipped; pass --commit-message to validate backup wording")
        _add_check(report, "commit message discipline", True, "skipped")
        return

    message = commit_message.strip()
    lowered = message.lower()
    missing: list[str] = []
    if not all(term in lowered for term in CONTENT_TERMS):
        missing.append("stage/update content")
    if not any(term in lowered for term in VERIFICATION_TERMS):
        missing.append("verification evidence")
    if not any(term in lowered for term in RISK_TERMS):
        missing.append("remaining risk/residual risk")

    if missing:
        _add_error(report, f"commit message: missing {missing}")
    _add_check(
        report,
        "commit message discipline",
        not missing,
        "stage/update, verification, and residual risk wording present"
        if not missing
        else f"missing {missing}",
    )


def validate_closeout(template_path: Path, commit_message: str | None = None) -> dict[str, Any]:
    report = _new_report()
    _validate_template(template_path, report)
    _validate_commit_message(commit_message, report)
    report["status"] = "FAIL" if report["errors"] else "PASS"
    return report


def render_markdown_report(report: dict[str, Any], template_path: Path) -> str:
    lines = [
        "# Stage Closeout Harness",
        "",
        f"- status: `{report['status']}`",
        f"- template: `{template_path}`",
        "",
        "## Checks",
        "",
        "| check | status | detail |",
        "|---|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['detail']} |")

    lines.extend(["", "## Errors", ""])
    errors = report["errors"]
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    warnings = report["warnings"]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH)
    parser.add_argument("--json", type=Path, help="write structured JSON report")
    parser.add_argument("--report", type=Path, help="write Markdown report")
    parser.add_argument("--commit-message", help="validate proposed stage backup commit message")
    args = parser.parse_args(argv)

    template_path = args.template
    if not template_path.is_absolute():
        template_path = REPO_ROOT / template_path

    report = validate_closeout(template_path=template_path, commit_message=args.commit_message)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown_report(report, template_path), encoding="utf-8")

    print(f"{report['status']}: stage closeout harness")
    for check in report["checks"]:
        print(f"{check['status']}: {check['name']} - {check['detail']}")
    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")

    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
