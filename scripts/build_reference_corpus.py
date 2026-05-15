#!/usr/bin/env python3
"""Build a minimal v1.3-1 Reference Corpus P0 run.

The implementation delegates scan / split / manifest / report generation to
``ginga_platform.book_analysis`` so the CLI and unit-tested core share one
behavior surface.
"""

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

from ginga_platform.book_analysis.corpus import build_reference_corpus


def default_run_id(source_path: Path) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_path.stem).strip("-") or "source"
    return f"book-analysis-{stamp}-{slug[:40]}"


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


def write_run_config(run_root: Path, *, run_id: str, source_path: Path) -> None:
    payload = {
        "run_id": run_id,
        "source_path": str(source_path),
        "keyword_sources": {
            "active": False,
            "allowed_source_types": ["explicit_config", "user_input", "approved_pattern_seed"],
            "entries": [],
        },
        "p0_scope": ["scan", "split", "manifest", "validator", "report"],
    }
    (run_root / "run_config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_run(args: argparse.Namespace) -> dict[str, str | int]:
    source_path = args.source if args.source.is_absolute() else REPO_ROOT / args.source
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"source file not found: {source_path}")

    output_root = ensure_ops_output_root(args.output_root)
    run_id = args.run_id or default_run_id(source_path)
    run_root = output_root / run_id
    if run_root.exists():
        raise FileExistsError(f"run directory already exists: {repo_relative(run_root)}")

    run_root = build_reference_corpus(
        source_path=source_path,
        run_id=run_id,
        output_base=output_root,
        encoding=args.encoding,
        title=args.title,
        source_kind=args.source_kind,
    )
    write_run_config(Path(run_root), run_id=run_id, source_path=source_path)

    validation_report_path = Path(run_root) / "validation_report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_reference_corpus.py"),
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
        "manifest_path": repo_relative(Path(run_root) / "source_manifest.json"),
        "validator_exit_code": completed.returncode,
        "validator_stdout": completed.stdout.strip(),
        "validator_stderr": completed.stderr.strip(),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source text file to scan")
    parser.add_argument("--run-id", help="optional run id; defaults to timestamp + source stem")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/book_analysis"),
        help="output root, default .ops/book_analysis",
    )
    parser.add_argument("--encoding", help="explicit source encoding")
    parser.add_argument("--title", help="source title to record in manifest")
    parser.add_argument(
        "--source-kind",
        default="user_file",
        choices=["user_file", "local_fixture", "external_capture", "unknown"],
        help="source kind recorded in manifest",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = build_run(args)
    except (OSError, ValueError) as exc:
        print(f"FAIL reference corpus build: {exc}", file=sys.stderr)
        return 1
    status = "PASS" if result["validator_exit_code"] == 0 else "FAIL"
    print(f"{status} reference corpus build: run={result['run_dir']} validator_exit={result['validator_exit_code']}")
    if result["validator_stdout"]:
        print(result["validator_stdout"])
    if result["validator_stderr"]:
        print(result["validator_stderr"], file=sys.stderr)
    return 0 if result["validator_exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
