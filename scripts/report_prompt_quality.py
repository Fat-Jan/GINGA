#!/usr/bin/env python3
"""Summarize Sprint 3 prompt-card quality and weak example candidates."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPTS_DIR = REPO_ROOT / "foundation" / "assets" / "prompts"
DEFAULT_OUTPUT = REPO_ROOT / ".ops" / "validation" / "prompt_quality_report.json"
GRADE_ORDER = {"D": 0, "C": 1, "B": 2, "B+": 3, "A-": 4, "A": 5}
WEAK_EXAMPLE_PATTERNS = [
    ("missing_example_section", re.compile(r"^##\s*示例输入\s*$", re.MULTILINE), False),
    ("example_direct_copy", re.compile(r"示例输入\s*\n\s*直接复制", re.MULTILINE), True),
    ("example_none", re.compile(r"示例输入\s*\n\s*无[。.\s]*", re.MULTILINE), True),
    ("example_empty", re.compile(r"示例输入\s*\n\s*(?:\n|$)", re.MULTILINE), True),
]


def repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str | None]:
    if not text.startswith("---\n"):
        return {}, "missing_frontmatter_fence"
    end = text.find("\n---", 4)
    if end == -1:
        return {}, "unterminated_frontmatter_fence"
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        return {}, f"yaml_error: {exc.__class__.__name__}"
    if not isinstance(data, dict):
        return {}, "frontmatter_not_mapping"
    return data, None


def weak_example_reasons(text: str) -> list[str]:
    reasons: list[str] = []
    for name, pattern, positive_match_is_weak in WEAK_EXAMPLE_PATTERNS:
        matched = pattern.search(text) is not None
        if positive_match_is_weak and matched:
            reasons.append(name)
        elif not positive_match_is_weak and not matched:
            reasons.append(name)
    return reasons


def example_excerpt(text: str) -> str:
    match = re.search(r"^##\s*示例输入\s*$([\s\S]*)", text, re.MULTILINE)
    if not match:
        return ""
    body = match.group(1).strip().splitlines()
    return " ".join(line.strip() for line in body[:2])[:160]


def build_report(prompts_dir: Path) -> dict[str, Any]:
    files = sorted(prompts_dir.glob("*.md"))
    quality_distribution = Counter()
    weak_candidates: list[dict[str, Any]] = []
    parse_errors: dict[str, str] = {}

    for path in files:
        text = path.read_text(encoding="utf-8")
        frontmatter, parse_error = parse_frontmatter(text)
        if parse_error:
            parse_errors[repo_relative(path)] = parse_error
        grade = str(frontmatter.get("quality_grade") or "UNKNOWN")
        quality_distribution[grade] += 1
        reasons = weak_example_reasons(text)
        if reasons:
            weak_candidates.append(
                {
                    "file": repo_relative(path),
                    "quality_grade": grade,
                    "title": frontmatter.get("title", ""),
                    "reasons": reasons,
                    "example_excerpt": example_excerpt(text),
                }
            )

    weak_candidates.sort(
        key=lambda item: (
            -GRADE_ORDER.get(item["quality_grade"], -1),
            item["file"],
        )
    )
    top_files_to_fix = weak_candidates[:50]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompts_dir": repo_relative(prompts_dir),
        "total_files": len(files),
        "quality_distribution": dict(sorted(quality_distribution.items())),
        "b_and_b_plus_counts": {
            "B": quality_distribution.get("B", 0),
            "B+": quality_distribution.get("B+", 0),
            "total": quality_distribution.get("B", 0) + quality_distribution.get("B+", 0),
        },
        "weak_example_candidate_count": len(weak_candidates),
        "weak_example_reason_counts": dict(
            Counter(reason for item in weak_candidates for reason in item["reasons"]).most_common()
        ),
        "parse_errors": parse_errors,
        "top_files_to_fix": top_files_to_fix,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompts_dir", nargs="?", type=Path, default=DEFAULT_PROMPTS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_report(args.prompts_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {repo_relative(args.output)}: total={report['total_files']} "
        f"weak_examples={report['weak_example_candidate_count']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
