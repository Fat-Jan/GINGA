#!/usr/bin/env python3
"""Build the explicit opt-in Reference Sidecar RAG index."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.reference_sidecar import DEFAULT_INDEX_PATH, build_reference_sidecar_index


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"sidecar sqlite index path; default {DEFAULT_INDEX_PATH}",
    )
    parser.add_argument("--json", type=Path, help="write build report to this path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    stats = build_reference_sidecar_index(repo_root=REPO_ROOT, index_path=args.index_path)
    report = {
        "status": "passed",
        "execution_mode": "reference_sidecar_rag",
        "explicit_opt_in_required": True,
        "index_path": str(args.index_path),
        "stats": stats.to_dict(),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS reference sidecar index: "
        f"cards_indexed={stats.cards_indexed} files_seen={stats.files_seen} index={args.index_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
