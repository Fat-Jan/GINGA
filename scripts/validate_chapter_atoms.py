#!/usr/bin/env python3
"""Validate a v1.3-2 Chapter Atom + Quality Gates run directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ginga_platform.book_analysis.validation import validate_chapter_atoms_run


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="chapter atom run directory under .ops/book_analysis")
    parser.add_argument("--json", type=Path, help="write validation report JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir if args.run_dir.is_absolute() else REPO_ROOT / args.run_dir
    report = validate_chapter_atoms_run(run_dir, repo_root=REPO_ROOT)
    report = {
        **report,
        "run_dir": repo_relative(run_dir),
        "validator": "ginga_platform.book_analysis.validation.validate_chapter_atoms_run",
    }
    if args.json:
        json_path = args.json if args.json.is_absolute() else REPO_ROOT / args.json
        write_json(json_path, report)

    status = "PASS" if report["status"] == "passed" else "FAIL"
    print(
        f"{status} chapter atom validation: "
        f"errors={len(report.get('errors', []))} warnings={len(report.get('warnings', []))} "
        f"run={repo_relative(run_dir)}"
    )
    for item in report.get("errors", []):
        print(f"ERROR {item.get('code')}: {item.get('message')} [{item.get('path')}]")
    for item in report.get("warnings", []):
        print(f"WARN {item.get('code')}: {item.get('message')} [{item.get('path')}]")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
