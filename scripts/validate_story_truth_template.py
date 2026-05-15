#!/usr/bin/env python3
"""Validate the Story Truth Template schema draft."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_LAYERS = (
    "project_contract",
    "genre_contract",
    "plot_architecture",
    "cast_contract",
    "world_contract",
    "system_contracts",
    "payoff_ledger",
    "hook_ledger",
    "foreshadow_ledger",
    "chapter_input_bundle",
    "runtime_state_projection",
    "style_contract",
    "candidate_promotion_gate",
)
REQUIRED_PROMOTION_EVIDENCE = {
    "operator_acceptance",
    "schema_validation",
    "source_contamination_check",
    "StateIO_or_validator_entrypoint",
    "audit_evidence",
}
REPORT_ONLY_PREFIXES = (
    ".ops/reports/",
    ".ops/reviews/",
    ".ops/jury/",
    ".ops/market_research/",
    ".ops/model_topology/",
)
FORBIDDEN_TRUTH_SOURCE_PREFIXES = (
    ".ops/book_analysis/",
    ".ops/market_research/",
    ".ops/reviews/",
    ".ops/jury/",
)
FORBIDDEN_TRUTH_SOURCE_TERMS = (
    "candidate",
    "report",
    "raw_text",
    "source_text",
    "external_sources",
)


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _add_error(report: dict[str, Any], field: str, message: str) -> None:
    report["errors"].append(f"{field}: {message}")


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _truth_source_values(layer: Any) -> list[str]:
    if not isinstance(layer, dict):
        return []
    values: list[str] = []
    for key in ("truth_source", "truth_sources", "source_path", "source_paths"):
        for item in _as_list(layer.get(key)):
            if isinstance(item, str):
                values.append(item)
    return values


def _contains_forbidden_term(path_text: str) -> str | None:
    parts = [part.lower() for part in Path(path_text).parts]
    lowered = path_text.lower()
    for term in FORBIDDEN_TRUTH_SOURCE_TERMS:
        if term in parts or f"/{term}_" in lowered or f"_{term}" in lowered or lowered.endswith(term):
            return term
    return None


def _validate_truth_source(layer_name: str, source: str, report: dict[str, Any]) -> None:
    normalized = source.replace("\\", "/").lstrip("./")
    if normalized.startswith("ops/"):
        normalized = "." + normalized
    if any(normalized.startswith(prefix) for prefix in REPORT_ONLY_PREFIXES):
        _add_error(report, layer_name, f"report-only source cannot be truth_source: {source}")
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_TRUTH_SOURCE_PREFIXES):
        _add_error(report, layer_name, f"forbidden truth source path: {source}")
    forbidden_term = _contains_forbidden_term(normalized)
    if forbidden_term:
        _add_error(report, layer_name, f"candidate/report/raw source cannot be truth_source: {source}")


def _validate_layer_shape(name: str, value: Any, report: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        _add_error(report, name, "layer must be a mapping")
        return
    for source in _truth_source_values(value):
        _validate_truth_source(name, source, report)


def _validate_candidate_promotion_gate(gate: Any, report: dict[str, Any]) -> None:
    if not isinstance(gate, dict):
        _add_error(report, "candidate_promotion_gate", "layer must be a mapping")
        return
    evidence = set()
    raw_evidence = gate.get("required_evidence")
    if isinstance(raw_evidence, dict):
        evidence = {str(key) for key, enabled in raw_evidence.items() if enabled}
    elif isinstance(raw_evidence, list):
        evidence = {str(item) for item in raw_evidence}
    missing = sorted(REQUIRED_PROMOTION_EVIDENCE - evidence)
    for item in missing:
        _add_error(report, "candidate_promotion_gate", f"missing required evidence: {item}")
    for source in _truth_source_values(gate):
        normalized = source.replace("\\", "/").lstrip("./")
        if normalized != "ops/governance/candidate_truth_gate.md":
            _validate_truth_source("candidate_promotion_gate", source, report)


def validate_data(data: Any, *, path: Path | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "PASS",
        "path": _repo_relative(path) if path else None,
        "checks": [],
        "warnings": [],
        "errors": [],
    }
    if not isinstance(data, dict):
        _add_error(report, "template", "YAML root must be a mapping")
        report["status"] = "FAIL"
        return report

    if data.get("asset_type") != "story_truth_template":
        _add_error(report, "asset_type", "must be story_truth_template")

    for layer in REQUIRED_LAYERS:
        if layer not in data:
            _add_error(report, layer, "missing required layer")
            continue
        if layer == "candidate_promotion_gate":
            _validate_candidate_promotion_gate(data[layer], report)
        else:
            _validate_layer_shape(layer, data[layer], report)

    genre_contract = data.get("genre_contract")
    if isinstance(genre_contract, dict) and "extension_slots" in genre_contract:
        if not isinstance(genre_contract["extension_slots"], dict):
            _add_error(report, "genre_contract.extension_slots", "must be a mapping when present")

    report["checks"].append(
        {
            "name": "story truth template required layers",
            "status": "PASS" if not report["errors"] else "FAIL",
            "required_layers": list(REQUIRED_LAYERS),
        }
    )
    report["checks"].append(
        {
            "name": "candidate promotion gate evidence",
            "status": "PASS"
            if not any(error.startswith("candidate_promotion_gate:") for error in report["errors"])
            else "FAIL",
            "required_evidence": sorted(REQUIRED_PROMOTION_EVIDENCE),
        }
    )
    report["status"] = "PASS" if not report["errors"] else "FAIL"
    return report


def validate_file(path: Path) -> dict[str, Any]:
    return validate_data(_load_yaml(path), path=path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    target = path if path.is_absolute() else REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "template",
        type=Path,
        nargs="?",
        default=Path("foundation/schema/story_truth_template.yaml"),
        help="Story Truth Template YAML path; default foundation/schema/story_truth_template.yaml",
    )
    parser.add_argument("--json", type=Path, help="write validation report JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    template_path = args.template if args.template.is_absolute() else REPO_ROOT / args.template
    report = validate_file(template_path)
    if args.json:
        _write_json(args.json, report)

    print(
        f"{report['status']} story truth template: "
        f"errors={len(report['errors'])} warnings={len(report['warnings'])} "
        f"path={_repo_relative(template_path)}"
    )
    for error in report["errors"]:
        print(f"ERROR {error}")
    for warning in report["warnings"]:
        print(f"WARN {warning}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
