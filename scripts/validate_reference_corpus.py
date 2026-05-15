#!/usr/bin/env python3
"""Validate a v1.3-1 Reference Corpus P0 run directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK_ANALYSIS_ROOT = Path(".ops/book_analysis")
RECALL_CONFIG_PATH = Path("foundation/rag/recall_config.yaml")
SOURCE_MARKER = "[SOURCE_TROPE]"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FAKE_TITLE_RE = re.compile(r"^(第\s*\d+\s*章|chapter\s*\d+)$", re.IGNORECASE)
CHINESE_NUMERALS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
REQUIRED_TOP_FIELDS = {
    "run_id",
    "schema_version",
    "created_at",
    "source",
    "output",
    "chapters",
    "resources",
    "keyword_sources",
    "pollution",
    "validation",
    "limits",
}
REQUIRED_SOURCE_FIELDS = {"path", "sha256", "encoding", "title", "input_size_bytes"}
REQUIRED_OUTPUT_FIELDS = {"root", "manifest_path", "chapter_index_path", "report_path"}
REQUIRED_CHAPTER_FIELDS = {"count", "numbering_ok", "anomalies", "chapter_index_path"}
REQUIRED_RESOURCE_FIELDS = {
    "input_size_bytes",
    "chapter_count",
    "elapsed_seconds",
    "excerpt_chars_saved",
    "private_cache_bytes",
}
REQUIRED_KEYWORD_FIELDS = {"active", "allowed_source_types", "entries"}
REQUIRED_POLLUTION_VALUES = {
    "pollution_source": True,
    "source_marker": SOURCE_MARKER,
    "default_rag_excluded": True,
}
FORBIDDEN_REPO_PREFIXES = (
    Path("foundation/runtime_state"),
    Path("foundation/raw_ideas"),
    Path("foundation/assets/prompts"),
    Path("foundation/rag/indexes"),
    Path("meta/prompts"),
)
FORBIDDEN_RUN_NAMES = {
    ".private_evidence",
    "private_evidence",
    "runtime_state",
    "raw_ideas",
    "prompt",
    "prompts",
    "rag_index",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_repo_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def read_structured(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        raise ValueError(f"unsupported manifest suffix: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError("manifest must be a mapping")
    return data


def find_manifest(run_dir: Path) -> Path | None:
    for name in ("source_manifest.yaml", "source_manifest.yml", "source_manifest.json"):
        candidate = run_dir / name
        if candidate.is_file():
            return candidate
    return None


def load_chapter_index(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("chapters", "items", "chapter_index"):
            value = data.get(key)
            if isinstance(value, list):
                items = value
                break
        else:
            raise ValueError("chapter_index must be a list or contain chapters/items/chapter_index")
    else:
        raise ValueError("chapter_index must be a list or mapping")
    if not all(isinstance(item, dict) for item in items):
        raise ValueError("chapter_index entries must be mappings")
    return list(items)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add(findings: list[Finding], severity: str, code: str, message: str, path: Path | str = "") -> None:
    findings.append(Finding(severity=severity, code=code, message=message, path=str(path)))


def require_mapping(
    findings: list[Finding],
    parent: dict[str, Any],
    key: str,
    required_fields: set[str],
    path: str,
) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        add(findings, "error", "manifest_structure", f"{key} must be a mapping", path)
        return {}
    missing = sorted(required_fields - set(value))
    if missing:
        add(findings, "error", "manifest_required_fields", f"{key} missing fields: {missing}", path)
    return value


def anomaly_codes(manifest: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    chapters = manifest.get("chapters")
    if isinstance(chapters, dict):
        anomalies = chapters.get("anomalies")
        if isinstance(anomalies, list):
            for item in anomalies:
                if isinstance(item, dict) and isinstance(item.get("code"), str):
                    codes.add(item["code"])
    validation = manifest.get("validation")
    if isinstance(validation, dict):
        for key in ("errors", "warnings"):
            items = validation.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and isinstance(item.get("code"), str):
                        codes.add(item["code"])
    return codes


def add_declared_diagnostics(findings: list[Finding], manifest: dict[str, Any]) -> None:
    chapters = manifest.get("chapters")
    if isinstance(chapters, dict) and isinstance(chapters.get("anomalies"), list):
        for item in chapters["anomalies"]:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            severity = item.get("severity")
            message = item.get("message", "")
            if not isinstance(code, str) or severity not in {"error", "warning"}:
                continue
            add(findings, severity, code, str(message), str(item.get("chapter_ref", "")))


def parse_chapter_number(entry: dict[str, Any], title: str) -> int | None:
    for key in ("number", "chapter_number", "ordinal"):
        value = entry.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    match = re.search(r"(?:第\s*)?(\d+)\s*(?:章|回|节)", title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"第\s*([零〇一二两三四五六七八九十百]+)\s*(?:章|回|节)", title)
    if match:
        return parse_chinese_number(match.group(1))
    return None


def parse_chinese_number(text: str) -> int | None:
    if not text:
        return None
    if text == "十":
        return 10
    if "百" in text:
        return None
    if "十" in text:
        left, _, right = text.partition("十")
        tens = 1 if not left else CHINESE_NUMERALS.get(left)
        ones = 0 if not right else CHINESE_NUMERALS.get(right)
        if tens is None or ones is None:
            return None
        return tens * 10 + ones
    total = 0
    for char in text:
        digit = CHINESE_NUMERALS.get(char)
        if digit is None:
            return None
        total = total * 10 + digit
    return total


def ensure_reported(
    findings: list[Finding],
    recorded_codes: set[str],
    code: str,
    message: str,
    path: str,
) -> None:
    if code not in recorded_codes:
        add(findings, "error", "unreported_chapter_anomaly", f"{code}: {message}", path)


def validate_chapters(
    findings: list[Finding],
    manifest: dict[str, Any],
    chapter_entries: list[dict[str, Any]],
    chapter_index_path: Path,
) -> None:
    chapters = manifest.get("chapters", {})
    resources = manifest.get("resources", {})
    recorded = anomaly_codes(manifest)
    manifest_count = chapters.get("count")
    actual_count = len(chapter_entries)
    if manifest_count != actual_count:
        add(
            findings,
            "error",
            "chapter_count_mismatch",
            f"chapters.count={manifest_count!r} but chapter_index has {actual_count}",
            repo_relative(chapter_index_path),
        )
    if resources.get("chapter_count") != manifest_count:
        add(findings, "error", "resource_count_mismatch", "resources.chapter_count must equal chapters.count")

    title_counts: dict[str, int] = {}
    numbers: list[int] = []
    max_title_chars = (
        manifest.get("limits", {})
        .get("configured", {})
        .get("max_chapter_title_chars", 120)
    )
    if not isinstance(max_title_chars, int) or max_title_chars < 1:
        max_title_chars = 120

    for index, entry in enumerate(chapter_entries, start=1):
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            ensure_reported(findings, recorded, "empty_title", f"chapter {index} has empty title", repo_relative(chapter_index_path))
            continue
        stripped = title.strip()
        title_counts[stripped] = title_counts.get(stripped, 0) + 1
        if len(stripped) > max_title_chars:
            ensure_reported(findings, recorded, "long_title", f"chapter {index} title exceeds limit", repo_relative(chapter_index_path))
        number = parse_chapter_number(entry, stripped)
        if number is not None:
            numbers.append(number)
        chapter_hash = entry.get("sha256")
        if chapter_hash is not None and (not isinstance(chapter_hash, str) or not SHA256_RE.fullmatch(chapter_hash)):
            add(findings, "error", "chapter_hash_format", f"chapter {index} sha256 must be 64 lowercase hex", repo_relative(chapter_index_path))

    if any(count > 1 for count in title_counts.values()):
        ensure_reported(findings, recorded, "duplicate_title", "duplicate chapter titles detected", repo_relative(chapter_index_path))
    if numbers:
        if numbers != sorted(numbers):
            ensure_reported(findings, recorded, "out_of_order", "chapter numbers are out of order", repo_relative(chapter_index_path))
        expected = list(range(numbers[0], numbers[0] + len(numbers)))
        if numbers != expected:
            ensure_reported(findings, recorded, "missing_number", "chapter numbers are not contiguous", repo_relative(chapter_index_path))

    if "no_chapter_heading" in recorded and actual_count > 0:
        titles = [str(entry.get("title", "")).strip() for entry in chapter_entries]
        if all(FAKE_TITLE_RE.fullmatch(title) for title in titles if title):
            add(findings, "error", "fake_chapters", "no_chapter_heading run generated fake chapter titles", repo_relative(chapter_index_path))
        else:
            add(findings, "error", "no_heading_with_chapters", "no_chapter_heading must not produce chapter entries", repo_relative(chapter_index_path))


def validate_paths(
    findings: list[Finding],
    manifest: dict[str, Any],
    run_dir: Path,
    manifest_path: Path,
) -> tuple[Path | None, Path | None]:
    output = manifest.get("output", {})
    run_root = run_dir.resolve()
    declared_root = resolve_repo_path(output.get("root"))
    if declared_root and declared_root != run_root:
        add(findings, "error", "output_root_mismatch", "output.root must match the validated run directory", output.get("root", ""))

    allowed_root = (REPO_ROOT / BOOK_ANALYSIS_ROOT / run_dir.name).resolve()
    if run_root != allowed_root:
        add(findings, "error", "run_dir_boundary", f"run directory must be under {BOOK_ANALYSIS_ROOT}/<run_id>", repo_relative(run_dir))

    output_paths: list[Path] = [manifest_path.resolve()]
    for field in ("manifest_path", "chapter_index_path", "report_path", "validation_report_path"):
        path = resolve_repo_path(output.get(field))
        if path is None:
            if field in REQUIRED_OUTPUT_FIELDS:
                add(findings, "error", "output_path_missing", f"output.{field} is required")
            continue
        output_paths.append(path)
        if not is_relative_to(path, run_root):
            add(findings, "error", "output_boundary_violation", f"output.{field} must be inside the run directory", repo_relative(path))

    chapter_path = resolve_repo_path(output.get("chapter_index_path"))
    report_path = resolve_repo_path(output.get("report_path"))
    source_path = resolve_repo_path(manifest.get("source", {}).get("path"))
    if source_path:
        for output_path in output_paths:
            if source_path == output_path:
                add(findings, "error", "source_overwritten", "source.path must not equal an output path", repo_relative(output_path))
        if is_relative_to(source_path, run_root):
            add(findings, "error", "source_inside_run", "source.path must not be generated inside the run directory", repo_relative(source_path))

    for path in run_dir.rglob("*"):
        rel_names = set(path.relative_to(run_dir).parts)
        if path.is_dir() and path.name in FORBIDDEN_RUN_NAMES:
            add(findings, "error", "forbidden_run_artifact", "forbidden P0 artifact directory exists", repo_relative(path))
        if path.is_file() and rel_names.intersection(FORBIDDEN_RUN_NAMES):
            add(findings, "error", "forbidden_run_artifact", "forbidden P0 artifact file exists", repo_relative(path))

    return chapter_path, report_path


def validate_manifest(
    findings: list[Finding],
    manifest: dict[str, Any],
    run_dir: Path,
    manifest_path: Path,
) -> tuple[Path | None, Path | None]:
    missing = sorted(REQUIRED_TOP_FIELDS - set(manifest))
    if missing:
        add(findings, "error", "manifest_required_fields", f"manifest missing top-level fields: {missing}", repo_relative(manifest_path))

    source = require_mapping(findings, manifest, "source", REQUIRED_SOURCE_FIELDS, "source")
    output = require_mapping(findings, manifest, "output", REQUIRED_OUTPUT_FIELDS, "output")
    chapters = require_mapping(findings, manifest, "chapters", REQUIRED_CHAPTER_FIELDS, "chapters")
    resources = require_mapping(findings, manifest, "resources", REQUIRED_RESOURCE_FIELDS, "resources")
    keywords = require_mapping(findings, manifest, "keyword_sources", REQUIRED_KEYWORD_FIELDS, "keyword_sources")
    pollution = require_mapping(findings, manifest, "pollution", set(REQUIRED_POLLUTION_VALUES), "pollution")
    validation = require_mapping(findings, manifest, "validation", {"validator", "status", "errors", "warnings"}, "validation")
    limits = require_mapping(findings, manifest, "limits", {"defaults", "configured"}, "limits")
    add_declared_diagnostics(findings, manifest)

    if manifest.get("run_id") != run_dir.name:
        add(findings, "error", "run_id_mismatch", "manifest.run_id must match run directory name", str(manifest.get("run_id")))
    if not isinstance(manifest.get("created_at"), str):
        add(findings, "error", "created_at_type", "created_at must be an ISO 8601 string")

    sha = source.get("sha256")
    if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
        add(findings, "error", "source_sha256_format", "source.sha256 must be 64 lowercase hex")
    source_path = resolve_repo_path(source.get("path"))
    if source_path and source_path.is_file() and isinstance(sha, str) and SHA256_RE.fullmatch(sha):
        actual_sha = sha256_file(source_path)
        if actual_sha != sha:
            add(findings, "error", "source_sha256_mismatch", "source file sha256 differs from manifest", repo_relative(source_path))
    if resources.get("input_size_bytes") != source.get("input_size_bytes"):
        add(findings, "error", "resource_size_mismatch", "resources.input_size_bytes must equal source.input_size_bytes")

    for key, expected in REQUIRED_POLLUTION_VALUES.items():
        if pollution.get(key) != expected:
            add(findings, "error", "pollution_marker", f"pollution.{key} must be {expected!r}")
    for key in (
        "prompt_injection_allowed",
        "runtime_state_write_allowed",
        "raw_ideas_write_allowed",
        "default_input_whitelist_allowed",
    ):
        if pollution.get(key) is True:
            add(findings, "error", "pollution_boundary", f"pollution.{key} must not be true")

    if keywords.get("active") is not False:
        add(findings, "error", "keyword_sources_active", "P0 keyword_sources.active must be false")
    if not isinstance(keywords.get("entries"), list):
        add(findings, "error", "keyword_sources_entries", "keyword_sources.entries must be a list")
    if not isinstance(keywords.get("allowed_source_types"), list):
        add(findings, "error", "keyword_sources_allowed", "keyword_sources.allowed_source_types must be a list")

    if resources.get("excerpt_chars_saved") != 0:
        add(findings, "error", "excerpt_saved", "P0 resources.excerpt_chars_saved must be 0")
    if resources.get("private_cache_bytes") != 0:
        add(findings, "error", "private_cache_saved", "P0 resources.private_cache_bytes must be 0")
    configured = limits.get("configured") if isinstance(limits.get("configured"), dict) else {}
    if configured.get("max_excerpt_chars") not in (0, None):
        add(findings, "error", "excerpt_limit", "P0 limits.configured.max_excerpt_chars must be 0")
    if configured.get("private_cache_enabled") is True:
        add(findings, "error", "private_cache_enabled", "P0 private cache must be disabled")
    if configured.get("max_private_cache_bytes") not in (0, None):
        add(findings, "error", "private_cache_limit", "P0 max_private_cache_bytes must be 0")

    if chapters.get("chapter_index_path") != output.get("chapter_index_path"):
        add(findings, "error", "chapter_index_path_mismatch", "chapters.chapter_index_path must equal output.chapter_index_path")
    if validation.get("status") == "passed" and validation.get("errors"):
        add(findings, "error", "validation_status", "validation.status cannot be passed when validation.errors is non-empty")

    return validate_paths(findings, manifest, run_dir, manifest_path)


def validate_rag_boundaries(findings: list[Finding]) -> None:
    config_path = REPO_ROOT / RECALL_CONFIG_PATH
    if not config_path.is_file():
        add(findings, "error", "recall_config_missing", "default RAG recall config is missing", repo_relative(config_path))
        return
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        add(findings, "error", "recall_config_yaml", f"cannot parse recall config: {exc}", repo_relative(config_path))
        return
    if not isinstance(config, dict):
        add(findings, "error", "recall_config_structure", "recall config must be a mapping", repo_relative(config_path))
        return
    sources = config.get("recall_sources", [])
    if isinstance(sources, list):
        for source in sources:
            path_value = source.get("path") if isinstance(source, dict) else source
            if isinstance(path_value, str) and ".ops/book_analysis" in path_value:
                add(findings, "error", "rag_source_pollution", "recall_sources must not include .ops/book_analysis", repo_relative(config_path))
    else:
        add(findings, "error", "recall_sources_structure", "recall_sources must be a list", repo_relative(config_path))
    forbidden = config.get("recall_forbidden_paths", [])
    if not isinstance(forbidden, list):
        add(findings, "error", "recall_forbidden_structure", "recall_forbidden_paths must be a list", repo_relative(config_path))
        return
    if not any(isinstance(item, str) and item.startswith(".ops/book_analysis") for item in forbidden):
        add(findings, "error", "rag_forbidden_missing", "recall_forbidden_paths must exclude .ops/book_analysis", repo_relative(config_path))


def validate_forbidden_repo_outputs(findings: list[Finding], run_dir: Path) -> None:
    for prefix in FORBIDDEN_REPO_PREFIXES:
        path = REPO_ROOT / prefix
        if is_relative_to(run_dir, path):
            add(findings, "error", "forbidden_output_domain", "run directory is inside a forbidden output domain", repo_relative(run_dir))


def validate_text_marker(findings: list[Finding], report_path: Path | None) -> None:
    if report_path is None or not report_path.is_file():
        return
    if report_path.suffix.lower() not in {".md", ".txt"}:
        return
    try:
        first_chunk = report_path.read_text(encoding="utf-8")[:200]
    except UnicodeDecodeError:
        add(findings, "error", "report_encoding", "report must be readable as utf-8", repo_relative(report_path))
        return
    if not first_chunk.startswith(SOURCE_MARKER):
        add(findings, "error", "source_marker_missing", f"text report must start with {SOURCE_MARKER}", repo_relative(report_path))


def validate_run(run_dir: Path) -> dict[str, Any]:
    findings: list[Finding] = []
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        add(findings, "error", "run_dir_missing", "run directory does not exist", repo_relative(run_dir))
        return build_report(run_dir, None, findings)

    manifest_path = find_manifest(run_dir)
    if manifest_path is None:
        add(findings, "error", "manifest_missing", "source_manifest.yaml/json is missing", repo_relative(run_dir))
        return build_report(run_dir, None, findings)

    try:
        manifest = read_structured(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        add(findings, "error", "manifest_parse", f"cannot parse manifest: {exc}", repo_relative(manifest_path))
        return build_report(run_dir, manifest_path, findings)

    chapter_index_path, report_path = validate_manifest(findings, manifest, run_dir, manifest_path)
    validate_forbidden_repo_outputs(findings, run_dir)
    validate_rag_boundaries(findings)

    if chapter_index_path is None or not chapter_index_path.is_file():
        add(findings, "error", "chapter_index_missing", "chapter_index.json is missing", str(chapter_index_path or ""))
        chapter_entries: list[dict[str, Any]] = []
    else:
        try:
            chapter_entries = load_chapter_index(chapter_index_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            add(findings, "error", "chapter_index_parse", f"cannot parse chapter index: {exc}", repo_relative(chapter_index_path))
            chapter_entries = []
    if report_path is None or not report_path.is_file():
        add(findings, "error", "report_missing", "report file is missing", str(report_path or ""))

    validate_chapters(findings, manifest, chapter_entries, chapter_index_path or run_dir)
    validate_text_marker(findings, report_path)
    return build_report(run_dir, manifest_path, findings)


def build_report(run_dir: Path, manifest_path: Path | None, findings: list[Finding]) -> dict[str, Any]:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    return {
        "validator": "scripts/validate_reference_corpus.py",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": repo_relative(run_dir),
        "manifest_path": repo_relative(manifest_path) if manifest_path else None,
        "passed": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": [asdict(finding) for finding in errors],
        "warnings": [asdict(finding) for finding in warnings],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    target = path if path.is_absolute() else REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_summary(report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    print(
        f"{status} reference corpus validation: "
        f"errors={report['error_count']} warnings={report['warning_count']} run={report['run_dir']}"
    )
    for item in report["errors"][:10]:
        path = f" ({item['path']})" if item.get("path") else ""
        print(f"  ERROR {item['code']}: {item['message']}{path}")
    if report["error_count"] > 10:
        print(f"  ... {report['error_count'] - 10} more error(s)")
    for item in report["warnings"][:5]:
        path = f" ({item['path']})" if item.get("path") else ""
        print(f"  WARNING {item['code']}: {item['message']}{path}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Reference Corpus run directory under .ops/book_analysis/<run_id>")
    parser.add_argument("--json", type=Path, help="write validation_report.json to this path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir if args.run_dir.is_absolute() else REPO_ROOT / args.run_dir
    report = validate_run(run_dir)
    if args.json:
        write_json(args.json, report)
    print_summary(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
