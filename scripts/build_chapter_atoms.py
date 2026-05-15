#!/usr/bin/env python3
"""Build a v1.3-2 Chapter Atom + Quality Gates sidecar run."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ginga_platform.book_analysis.corpus import build_chapter_atoms


def default_run_id(source_run_root: Path) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_run_root.name).strip("-") or "source"
    return f"chapter-atoms-{stamp}-{slug[:40]}"


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_ops_output_root(output_root: Path) -> Path:
    resolved = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    resolved = resolved.resolve()
    allowed = (REPO_ROOT / ".ops" / "book_analysis").resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise ValueError("output root must place runs under .ops/book_analysis") from exc
    return resolved


def build_run(args: argparse.Namespace) -> dict[str, str | int]:
    source_run_root = args.source_run_root if args.source_run_root.is_absolute() else REPO_ROOT / args.source_run_root
    source_run_root = source_run_root.resolve()
    if not source_run_root.is_dir():
        raise FileNotFoundError(f"source run directory not found: {source_run_root}")

    output_root = ensure_ops_output_root(args.output_root)
    run_id = args.run_id or default_run_id(source_run_root)
    run_root = output_root / run_id
    if run_root.exists() and not args.force:
        raise FileExistsError(f"run directory already exists: {repo_relative(run_root)}")
    if run_root.exists():
        for child in run_root.iterdir():
            if child.is_dir():
                raise FileExistsError(f"refusing to overwrite nested directory: {repo_relative(child)}")
            child.unlink()

    run_root = build_chapter_atoms(source_run_root=source_run_root, run_id=run_id, output_base=output_root)
    validation_report_path = Path(run_root) / "validation_report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_chapter_atoms.py"),
            str(run_root),
            "--json",
            str(validation_report_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "run_dir": repo_relative(Path(run_root)),
        "atoms_path": repo_relative(Path(run_root) / "chapter_atoms.json"),
        "validator_exit_code": completed.returncode,
        "validator_stdout": completed.stdout.strip(),
        "validator_stderr": completed.stderr.strip(),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_run_root", type=Path, help="v1.3-1 source run directory")
    parser.add_argument("--run-id", help="optional run id; defaults to timestamp + source run name")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/book_analysis"),
        help="output root, default .ops/book_analysis",
    )
    parser.add_argument("--force", action="store_true", help="overwrite files in an existing run directory")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = build_run(args)
    except (OSError, ValueError) as exc:
        print(f"FAIL chapter atom build: {exc}", file=sys.stderr)
        return 1
    status = "PASS" if result["validator_exit_code"] == 0 else "FAIL"
    print(f"{status} chapter atom build: run={result['run_dir']} validator_exit={result['validator_exit_code']}")
    if result["validator_stdout"]:
        print(result["validator_stdout"])
    if result["validator_stderr"]:
        print(result["validator_stderr"], file=sys.stderr)
    return 0 if result["validator_exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
