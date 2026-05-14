#!/usr/bin/env python3
"""Report prompt_card frontmatter coverage and schema drift.

This is intentionally report-only by default. Use --strict when violations
should fail CI or a handoff checkpoint.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPTS_DIR = REPO_ROOT / "foundation" / "assets" / "prompts"
DEFAULT_SCHEMA = REPO_ROOT / "foundation" / "schema" / "prompt_card.yaml"
DEFAULT_OUTPUT = REPO_ROOT / ".ops" / "validation" / "prompt_frontmatter_report.json"
REQUIRED_FIELDS = [
    "id",
    "asset_type",
    "title",
    "topic",
    "stage",
    "quality_grade",
    "source_path",
    "last_updated",
]
CHECK_ENUM_FIELDS = ["stage", "card_intent", "card_kind", "output_kind"]


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
    raw = text[4:end]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return {}, f"yaml_error: {exc.__class__.__name__}"
    if not isinstance(data, dict):
        return {}, "frontmatter_not_mapping"
    return data, None


def load_schema_enums(schema_path: Path) -> dict[str, list[Any]]:
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
    fields = schema.get("fields") or {}
    enums: dict[str, list[Any]] = {}
    for field, spec in fields.items():
        if isinstance(spec, dict) and "enum" in spec:
            enums[field] = list(spec["enum"])
    return enums


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def build_report(prompts_dir: Path, schema_path: Path) -> dict[str, Any]:
    files = sorted(prompts_dir.glob("*.md"))
    enums = load_schema_enums(schema_path)
    missing_required: dict[str, list[str]] = {field: [] for field in REQUIRED_FIELDS}
    illegal_enum_values: dict[str, dict[str, list[str]]] = {}
    empty_topic_files: list[str] = []
    missing_task_full_files: list[str] = []
    parse_errors: dict[str, str] = {}
    coverage = Counter()

    for path in files:
        rel = repo_relative(path)
        frontmatter, error = parse_frontmatter(path.read_text(encoding="utf-8"))
        if error:
            parse_errors[rel] = error

        for field in REQUIRED_FIELDS:
            if is_empty(frontmatter.get(field)):
                missing_required[field].append(rel)
            else:
                coverage[field] += 1

        if is_empty(frontmatter.get("topic")):
            empty_topic_files.append(rel)
        if is_empty(frontmatter.get("task_full")):
            missing_task_full_files.append(rel)

        for field in CHECK_ENUM_FIELDS:
            allowed = enums.get(field)
            if not allowed or field not in frontmatter or is_empty(frontmatter.get(field)):
                continue
            value = frontmatter[field]
            if value not in allowed:
                illegal_enum_values.setdefault(field, {}).setdefault(str(value), []).append(rel)

    violation_count = (
        sum(len(paths) for paths in missing_required.values())
        + len(empty_topic_files)
        + len(missing_task_full_files)
        + sum(len(paths) for values in illegal_enum_values.values() for paths in values.values())
        + len(parse_errors)
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompts_dir": repo_relative(prompts_dir),
        "schema_path": repo_relative(schema_path),
        "total_files": len(files),
        "required_8_field_coverage": {
            field: {
                "present": coverage[field],
                "missing": len(missing_required[field]),
                "coverage_ratio": round(coverage[field] / len(files), 4) if files else 0,
            }
            for field in REQUIRED_FIELDS
        },
        "missing_required_files": missing_required,
        "empty_topic_files": empty_topic_files,
        "missing_task_full_files": missing_task_full_files,
        "illegal_enum_values": illegal_enum_values,
        "parse_errors": parse_errors,
        "violation_count": violation_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompts_dir", nargs="?", type=Path, default=DEFAULT_PROMPTS_DIR)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strict", action="store_true", help="exit nonzero when violations exist")
    args = parser.parse_args()

    report = build_report(args.prompts_dir, args.schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"wrote {repo_relative(args.output)}: total={report['total_files']} "
        f"violations={report['violation_count']}"
    )
    return 1 if args.strict and report["violation_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
