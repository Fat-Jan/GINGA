#!/usr/bin/env python3
"""Local Sprint 3 pressure-test quantification.

This script reads existing local artifacts only. It does not call LLM endpoints,
does not mutate runtime_state, and writes only the Sprint 3 pressure-test JSON
and Markdown reports.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - repository scripts already depend on PyYAML.
    yaml = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_PATH = ROOT / ".ops/validation/s3_pressure_test.json"
REPORT_PATH = ROOT / ".ops/reports/s3_pressure_test_report.md"
TARGET_RATE = 0.80

CN_NUMBERS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{rel(path)} must contain a JSON object")
    return data


def read_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read local runtime YAML artifacts")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def first_chapter_heading(path: Path) -> tuple[int | None, str | None]:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        raw = line.strip()
        if raw.startswith("|"):
            continue
        if raw.startswith("#"):
            stripped = raw.lstrip("#").strip()
        elif raw.startswith("**第") and raw.endswith("**"):
            stripped = raw.strip("*").strip()
        else:
            continue
        match = re.search(r"第\s*([0-9]+|[一二三四五六七八九十]+)\s*章", stripped)
        if not match:
            continue
        raw = match.group(1)
        if raw.isdigit():
            return int(raw), stripped
        if raw in CN_NUMBERS:
            return CN_NUMBERS[raw], stripped
    return None, None


def cjkish_length(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.sub(r"\s+", "", text))


def dimension(
    name: str,
    passed: bool,
    score: float,
    evidence: dict[str, Any],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if passed else "fail",
        "score": round(score, 4),
        "passed": passed,
        "evidence": evidence,
        "notes": notes or [],
    }


def evaluate_runtime_continuity(label: str, demo_dir: Path, immersive: bool = False) -> dict[str, Any]:
    chapter_files = sorted(demo_dir.glob("chapter_*.md"))
    chapter_numbers: list[int | None] = []
    headings: list[str | None] = []
    lengths: list[int] = []
    for path in chapter_files:
        number, heading = first_chapter_heading(path)
        chapter_numbers.append(number)
        headings.append(heading)
        lengths.append(cjkish_length(path))

    entity = read_yaml(demo_dir / "entity_runtime.yaml")
    audit = read_yaml(demo_dir / "audit_log.yaml")
    foreshadow_pool = (
        entity.get("FORESHADOW_STATE", {}).get("pool", [])
        if isinstance(entity.get("FORESHADOW_STATE"), dict)
        else []
    )
    events = (
        entity.get("CHARACTER_STATE", {})
        .get("protagonist", {})
        .get("events", [])
        if isinstance(entity.get("CHARACTER_STATE"), dict)
        else []
    )
    total_words = (
        entity.get("GLOBAL_SUMMARY", {}).get("total_words")
        if isinstance(entity.get("GLOBAL_SUMMARY"), dict)
        else None
    )
    audit_entries = audit.get("entries", []) if isinstance(audit.get("entries"), list) else []
    audit_text = "\n".join(str(item.get("msg", "")) for item in audit_entries if isinstance(item, dict))

    expected_sequence = list(range(1, 6))
    sequence_ok = chapter_numbers == expected_sequence
    files_ok = len(chapter_files) >= 5 and all(length >= 2500 for length in lengths[:5])
    anchor_terms = ["微粒", "天堑", "内宇宙", "短刃"]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in chapter_files[:5])
    anchor_hits = {term: combined.count(term) for term in anchor_terms}
    anchors_ok = all(count > 0 for count in anchor_hits.values())

    if immersive:
        applied_ok = "5 chapters batch applied" in audit_text
        r2_ok = "R2_consistency_check triggered" in audit_text
        passed = files_ok and sequence_ok and anchors_ok and applied_ok and r2_ok
        score = sum([files_ok, sequence_ok, anchors_ok, applied_ok, r2_ok]) / 5
        notes = []
        if not sequence_ok:
            notes.append("Chapter headings do not progress 1..5; this may indicate batch apply/title continuity drift.")
    else:
        events_ok = len(events) >= 5
        foreshadow_ok = isinstance(foreshadow_pool, list) and len(foreshadow_pool) >= 5
        r2_ok = audit_text.count("R2 ran") >= 5
        passed = files_ok and sequence_ok and anchors_ok and events_ok and foreshadow_ok and r2_ok
        score = sum([files_ok, sequence_ok, anchors_ok, events_ok, foreshadow_ok, r2_ok]) / 6
        notes = []

    return dimension(
        label,
        passed,
        score,
        {
            "dir": rel(demo_dir),
            "chapter_files": [rel(path) for path in chapter_files],
            "chapter_heading_numbers": chapter_numbers,
            "chapter_headings": headings,
            "min_compact_length": min(lengths) if lengths else 0,
            "entity_events": len(events) if isinstance(events, list) else 0,
            "foreshadow_count": len(foreshadow_pool) if isinstance(foreshadow_pool, list) else 0,
            "total_words": total_words,
            "anchor_hits": anchor_hits,
        },
        notes,
    )


def evaluate_prompt_schema() -> dict[str, Any]:
    path = ROOT / ".ops/validation/prompt_frontmatter_report.json"
    data = read_json(path)
    coverage = data.get("required_8_field_coverage", {})
    min_coverage = min(
        (field.get("coverage_ratio", 0) for field in coverage.values() if isinstance(field, dict)),
        default=0,
    )
    violation_count = int(data.get("violation_count", 0))
    passed = violation_count == 0 and min_coverage >= 1.0
    return dimension(
        "prompt schema readiness",
        passed,
        1.0 if passed else min_coverage,
        {
            "source": rel(path),
            "total_files": data.get("total_files", 0),
            "min_required_field_coverage": min_coverage,
            "violation_count": violation_count,
            "parse_error_count": len(data.get("parse_errors", {})),
        },
    )


def evaluate_weak_example_debt() -> dict[str, Any]:
    path = ROOT / ".ops/validation/prompt_quality_report.json"
    data = read_json(path)
    total = int(data.get("total_files", 0))
    weak = int(data.get("weak_example_candidate_count", 0))
    debt_ratio = weak / total if total else 1.0
    passed = weak == 0
    score = max(0.0, 1.0 - debt_ratio)
    return dimension(
        "weak-example debt",
        passed,
        score,
        {
            "source": rel(path),
            "total_files": total,
            "weak_example_candidate_count": weak,
            "debt_ratio": round(debt_ratio, 4),
            "reason_counts": data.get("weak_example_reason_counts", {}),
        },
        ["Failing until weak_example_candidate_count reaches 0."],
    )


def evaluate_methodology_assets() -> dict[str, Any]:
    report = ROOT / ".ops/reports/methodology_assets_report.md"
    validator = ROOT / "scripts/validate_methodology_assets.py"
    methodology_schema = ROOT / "foundation/schema/methodology.yaml"
    checker_schema = ROOT / "foundation/schema/checker_or_schema_ref.yaml"
    methodology_files = sorted((ROOT / "foundation/assets/methodology").glob("*.md"))
    checker_files = sorted((ROOT / "foundation/assets/checkers_or_schema_refs").glob("*.md"))
    text = report.read_text(encoding="utf-8") if report.exists() else ""
    report_claims = {
        "methodology_assets_created": re.search(r"Methodology assets created:\s+12", text) is not None,
        "checker_assets_created": re.search(r"Checker/schema-ref assets created:\s+1", text) is not None,
    }
    checks = [
        report.exists(),
        validator.exists(),
        methodology_schema.exists(),
        checker_schema.exists(),
        len(methodology_files) >= 12,
        len(checker_files) >= 1,
        all(report_claims.values()),
    ]
    passed = all(checks)
    return dimension(
        "methodology asset readiness",
        passed,
        sum(checks) / len(checks),
        {
            "report": rel(report),
            "validator": rel(validator),
            "methodology_asset_count": len(methodology_files),
            "checker_asset_count": len(checker_files),
            "report_claims": report_claims,
        },
    )


def evaluate_dedup_evidence() -> dict[str, Any]:
    path = ROOT / ".ops/validation/dedup_evidence.json"
    data = read_json(path)
    sample_count = int(data.get("sample_count", 0))
    decision_counts = data.get("decision_counts", {})
    unknown = 0
    if isinstance(decision_counts, dict):
        unknown = int(decision_counts.get("unknown", 0))
    passed = data.get("status") == "ok" and sample_count >= 25 and unknown == 0
    score = sum([data.get("status") == "ok", sample_count >= 25, unknown == 0]) / 3
    return dimension(
        "dedup evidence readiness",
        passed,
        score,
        {
            "source": rel(path),
            "status": data.get("status"),
            "prompt_card_count": data.get("prompt_card_count"),
            "base_doc_count": data.get("base_doc_count"),
            "sample_count": sample_count,
            "decision_counts": decision_counts,
        },
    )


def evaluate_rag_test_status() -> dict[str, Any]:
    handoff = ROOT / ".ops/p7-handoff/ST-S3-R-LAYER23.md"
    tests = [
        ROOT / "ginga_platform/orchestrator/runner/tests/test_rag_layer1.py",
        ROOT / "ginga_platform/orchestrator/runner/tests/test_rag_layer2.py",
        ROOT / "ginga_platform/orchestrator/runner/tests/test_rag_layer3.py",
    ]
    modules = [
        ROOT / "rag/layer1_filter.py",
        ROOT / "rag/layer2_vector.py",
        ROOT / "rag/reranker.py",
        ROOT / "rag/retriever.py",
    ]
    text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""
    focused_ok = "Ran 13 tests OK" in text
    regression_ok = "Ran 112 tests OK" in text
    checks = [handoff.exists(), all(path.exists() for path in tests), all(path.exists() for path in modules), focused_ok]
    passed = all(checks)
    notes = []
    if regression_ok:
        notes.append("Handoff also records full ginga_platform discovery: Ran 112 tests OK.")
    return dimension(
        "RAG test status",
        passed,
        sum(checks) / len(checks),
        {
            "handoff": rel(handoff),
            "test_files": [rel(path) for path in tests],
            "module_files": [rel(path) for path in modules],
            "focused_test_evidence": "Ran 13 tests OK" if focused_ok else None,
            "full_regression_evidence": "Ran 112 tests OK" if regression_ok else None,
            "runtime_policy": "not rerun by pressure script; local handoff/test-file evidence only",
        },
        notes,
    )


def build_results() -> dict[str, Any]:
    dims = [
        evaluate_runtime_continuity(
            "multi-chapter continuity",
            ROOT / "foundation/runtime_state/s2-demo",
            immersive=False,
        ),
        evaluate_runtime_continuity(
            "immersive continuity",
            ROOT / "foundation/runtime_state/immersive-demo",
            immersive=True,
        ),
        evaluate_prompt_schema(),
        evaluate_weak_example_debt(),
        evaluate_methodology_assets(),
        evaluate_dedup_evidence(),
        evaluate_rag_test_status(),
    ]
    pass_count = sum(1 for item in dims if item["passed"])
    pass_rate = pass_count / len(dims) if dims else 0.0
    mean_score = sum(float(item["score"]) for item in dims) / len(dims) if dims else 0.0
    return {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "task_id": "ST-S3-P-PRESSURE-TEST",
        "policy": {
            "local_only": True,
            "llm_calls": False,
            "mutates_runtime_state": False,
            "target_pass_rate": TARGET_RATE,
        },
        "overall": {
            "passed": pass_rate >= TARGET_RATE,
            "pass_count": pass_count,
            "dimension_count": len(dims),
            "pass_rate": round(pass_rate, 4),
            "mean_score": round(mean_score, 4),
        },
        "dimensions": dims,
        "failing_dimensions": [item["name"] for item in dims if not item["passed"]],
    }


def render_report(results: dict[str, Any]) -> str:
    overall = results["overall"]
    lines = [
        "# Sprint 3 Pressure Test Report",
        "",
        f"Generated: `{results['generated_at']}`",
        "",
        "## Overall",
        "",
        f"- Pass rate: **{overall['pass_rate']:.1%}** ({overall['pass_count']}/{overall['dimension_count']})",
        f"- Mean dimension score: **{overall['mean_score']:.1%}**",
        f"- Target: **{TARGET_RATE:.0%}**",
        f"- Result: **{'PASS' if overall['passed'] else 'FAIL'}**",
        "- Runtime policy: local artifact reads only; no LLM calls; no runtime_state mutation.",
        "",
        "## Dimensions",
        "",
        "| Dimension | Status | Score | Key evidence |",
        "|---|---:|---:|---|",
    ]
    for item in results["dimensions"]:
        evidence = item["evidence"]
        if item["name"] == "weak-example debt":
            key = f"{evidence['weak_example_candidate_count']}/{evidence['total_files']} weak candidates"
        elif item["name"] in {"multi-chapter continuity", "immersive continuity"}:
            key = (
                f"headings={evidence['chapter_heading_numbers']}; "
                f"anchors={evidence['anchor_hits']}"
            )
        elif item["name"] == "prompt schema readiness":
            key = f"violations={evidence['violation_count']}; min coverage={evidence['min_required_field_coverage']:.0%}"
        elif item["name"] == "RAG test status":
            key = evidence.get("focused_test_evidence") or "missing focused test evidence"
        else:
            key = ", ".join(f"{k}={v}" for k, v in evidence.items() if k in {"status", "sample_count", "methodology_asset_count", "checker_asset_count"})
        lines.append(f"| {item['name']} | {item['status'].upper()} | {item['score']:.1%} | {key} |")

    lines.extend(["", "## Failing Dimensions", ""])
    failing = [item for item in results["dimensions"] if not item["passed"]]
    if not failing:
        lines.append("- None.")
    else:
        for item in failing:
            lines.append(f"- **{item['name']}**: {item['notes'][0] if item['notes'] else 'See JSON evidence.'}")

    lines.extend(["", "## Notes", ""])
    for item in results["dimensions"]:
        for note in item.get("notes", []):
            lines.append(f"- {item['name']}: {note}")
    if not any(item.get("notes") for item in results["dimensions"]):
        lines.append("- No additional notes.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 after writing reports, even when pass rate is below target.",
    )
    args = parser.parse_args()

    results = build_results()
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(results), encoding="utf-8")

    overall = results["overall"]
    print(
        f"S3 pressure test: pass_rate={overall['pass_rate']:.1%} "
        f"({overall['pass_count']}/{overall['dimension_count']}), "
        f"mean_score={overall['mean_score']:.1%}, "
        f"target={TARGET_RATE:.0%}, result={'PASS' if overall['passed'] else 'FAIL'}"
    )
    if results["failing_dimensions"]:
        print("Failing dimensions: " + ", ".join(results["failing_dimensions"]))
    print(f"Wrote {rel(VALIDATION_PATH)}")
    print(f"Wrote {rel(REPORT_PATH)}")

    if args.report_only or overall["passed"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
