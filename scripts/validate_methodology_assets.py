#!/usr/bin/env python3
"""Validate foundation methodology-style markdown assets against a schema yaml."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping")
    return data


def split_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    raw = text[4:end]
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter must be a mapping")
    return data


def enum_fields(schema: dict[str, Any]) -> dict[str, set[Any]]:
    fields = schema.get("fields", {})
    enums: dict[str, set[Any]] = {}
    if not isinstance(fields, dict):
        return enums
    for name, spec in fields.items():
        if isinstance(spec, dict) and spec.get("type") == "enum":
            values = spec.get("enum", [])
            if isinstance(values, list):
                enums[name] = set(values)
    return enums


def validate_date(path: Path, value: Any) -> str | None:
    if isinstance(value, dt.date):
        return None
    if isinstance(value, str):
        try:
            dt.date.fromisoformat(value)
            return None
        except ValueError:
            pass
    return f"{path}: last_updated must be ISO date"


def validate_asset(path: Path, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in schema.get("required_fields", []):
        if field not in data or data[field] in (None, ""):
            errors.append(f"{path}: missing required field {field}")

    for field, allowed in enum_fields(schema).items():
        if field in data and data[field] not in allowed:
            errors.append(
                f"{path}: {field}={data[field]!r} not in {sorted(allowed, key=str)}"
            )

    if "last_updated" in data:
        date_error = validate_date(path, data["last_updated"])
        if date_error:
            errors.append(date_error)

    topic = data.get("topic")
    if "topic" in data and not (
        isinstance(topic, list) and all(isinstance(item, str) for item in topic)
    ):
        errors.append(f"{path}: topic must be a string list")

    source_path = data.get("source_path")
    if isinstance(source_path, str) and not Path(source_path).exists():
        errors.append(f"{path}: source_path does not exist: {source_path}")

    sub_sections = data.get("sub_sections")
    if sub_sections is not None and not isinstance(sub_sections, dict):
        errors.append(f"{path}: sub_sections must be a mapping when present")

    return errors


def iter_markdown(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in paths:
        if root.is_file() and root.suffix == ".md":
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.md")))
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_paths", nargs="+", help="Markdown file or directory paths")
    parser.add_argument("schema", help="Schema YAML path")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    asset_roots = [Path(path) for path in args.asset_paths]
    schema = load_yaml(schema_path)
    files = iter_markdown(asset_roots)
    if not files:
        print("No markdown assets found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        try:
            data = split_frontmatter(path)
            errors.extend(validate_asset(path, data, schema))
        except Exception as exc:  # noqa: BLE001 - validator should report all file failures.
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} error(s) across {len(files)} asset(s)")
        return 1

    print(f"OK: validated {len(files)} asset(s) against {schema_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
