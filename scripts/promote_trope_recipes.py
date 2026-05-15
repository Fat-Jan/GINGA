#!/usr/bin/env python3
"""Promote approved v1.3-3 trope recipe candidates to Foundation assets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ginga_platform.book_analysis.promote import promote_trope_recipes


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
    parser.add_argument("recipes_json", type=Path, help="v1.3-3 trope_recipes.json")
    parser.add_argument(
        "--approved-candidate-id",
        action="append",
        default=[],
        help="candidate id explicitly approved by human review; repeat for multiple candidates",
    )
    parser.add_argument(
        "--target-kind",
        default="methodology",
        choices=["methodology"],
        help="whitelisted Foundation target kind",
    )
    parser.add_argument("--json", type=Path, help="write promotion report JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    recipes_path = args.recipes_json if args.recipes_json.is_absolute() else REPO_ROOT / args.recipes_json
    try:
        payload = json.loads(recipes_path.read_text(encoding="utf-8"))
        report = promote_trope_recipes(
            payload,
            repo_root=REPO_ROOT,
            approved_candidate_ids=args.approved_candidate_id,
            target_kind=args.target_kind,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL trope recipe promote: {exc}", file=sys.stderr)
        return 1

    report = {
        **report,
        "recipes_json": repo_relative(recipes_path),
        "promoter": "ginga_platform.book_analysis.promote.promote_trope_recipes",
    }
    if args.json:
        json_path = args.json if args.json.is_absolute() else REPO_ROOT / args.json
        write_json(json_path, report)

    print(
        f"PASS trope recipe promote: promoted={len(report['promoted_assets'])} "
        f"target_kind={report['target_kind']}"
    )
    for item in report["promoted_assets"]:
        print(f"- {item['candidate_id']} -> {item['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
