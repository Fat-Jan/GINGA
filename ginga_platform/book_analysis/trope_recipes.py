"""Trope Recipe Candidate v1.3-3 sidecar builder.

The recipe payload stays inside the polluted book-analysis sidecar.  It is a
candidate for human review, not a Foundation asset and not workflow input.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .manifest import SOURCE_MARKER


SCHEMA_VERSION = "0.3.0"
RECIPE_TYPES = (
    "underestimated_reversal",
    "resource_pressure_breakthrough",
    "misdirection_reveal",
)
DEFAULT_VARIATION_AXES = (
    "genre_swap",
    "identity_swap",
    "conflict_scale_swap",
)


def extract_trope_recipe_candidates(
    chapter_atoms_payload: Mapping[str, Any],
    *,
    run_id: str | None = None,
    created_at: Any = None,
    source_run_id: str | None = None,
) -> dict[str, Any]:
    """Build de-sourced recipe candidates from structural chapter atoms."""

    atoms = chapter_atoms_payload.get("chapter_atoms")
    atom_items = atoms if isinstance(atoms, list) else []
    candidates: list[dict[str, Any]] = []
    for idx, atom in enumerate(atom_items, start=1):
        if not isinstance(atom, Mapping):
            continue
        recipe_type = RECIPE_TYPES[(idx - 1) % len(RECIPE_TYPES)]
        candidates.append(_candidate_from_atom(atom, idx, recipe_type))

    gates = evaluate_trope_recipe_gates(candidates)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": _format_created_at(created_at),
        "source_run_id": source_run_id or str(chapter_atoms_payload.get("run_id", "")),
        "pollution": _pollution_payload(),
        "candidates": candidates,
        "quality_gates": gates,
        "promotion": {
            "status": "not_promoted",
            "promote_to": "none",
            "requires_human_review": True,
        },
    }


def write_trope_recipe_run(source_atom_run_root: str | Path, run_id: str, output_base: str | Path) -> Path:
    """Build a v1.3-3 Trope Recipe Candidate sidecar run from a chapter atom run."""

    source_atom_run_root = Path(source_atom_run_root)
    output_base = Path(output_base)
    run_root = output_base / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    atoms_payload = json.loads((source_atom_run_root / "chapter_atoms.json").read_text(encoding="utf-8"))
    created_at = _format_created_at(None)
    payload = extract_trope_recipe_candidates(
        atoms_payload,
        run_id=run_id,
        created_at=created_at,
        source_run_id=str(atoms_payload.get("run_id", source_atom_run_root.name)),
    )
    gates = payload["quality_gates"]
    run_config = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "source_run_id": payload["source_run_id"],
        "source_atom_run_root": str(source_atom_run_root),
        "output_root": str(run_root),
        "inputs": {
            "chapter_atoms_path": str(source_atom_run_root / "chapter_atoms.json"),
        },
        "outputs": {
            "trope_recipes_path": str(run_root / "trope_recipes.json"),
            "quality_gates_path": str(run_root / "quality_gates.json"),
            "report_path": str(run_root / "trope_recipe_report.md"),
        },
        "pollution": _pollution_payload(),
        "promotion": payload["promotion"],
    }

    (run_root / "trope_recipes.json").write_text(_json(payload), encoding="utf-8")
    (run_root / "quality_gates.json").write_text(_json(gates), encoding="utf-8")
    (run_root / "trope_recipe_report.md").write_text(render_trope_recipe_report(payload), encoding="utf-8")
    (run_root / "run_config.json").write_text(_json(run_config), encoding="utf-8")
    return run_root


def evaluate_trope_recipe_gates(candidates: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Return rejectable quality gates for trope recipe candidates."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    if not candidates:
        errors.append(_issue("missing_candidates", "at least one trope recipe candidate is required", "candidates"))

    for idx, candidate in enumerate(candidates):
        path = f"candidates[{idx}]"
        candidate_id = str(candidate.get("candidate_id", ""))
        if not candidate_id:
            errors.append(_issue("missing_candidate_id", "candidate_id is required", f"{path}.candidate_id"))
        elif candidate_id in seen_ids:
            errors.append(_issue("duplicate_candidate_id", "candidate_id must be unique", f"{path}.candidate_id"))
        seen_ids.add(candidate_id)

        if candidate.get("pollution_source") is not True:
            errors.append(_issue("missing_pollution_source", "pollution_source must be true", f"{path}.pollution_source"))
        if not str(candidate.get("trope_core", "")).strip():
            errors.append(_issue("missing_trope_core", "trope_core is required", f"{path}.trope_core"))
        if not str(candidate.get("reader_payoff", "")).strip():
            errors.append(_issue("missing_reader_payoff", "reader_payoff is required", f"{path}.reader_payoff"))
        if len(_list(candidate.get("trigger_conditions"))) < 1:
            errors.append(_issue("missing_trigger_conditions", "at least one trigger condition is required", f"{path}.trigger_conditions"))
        if len(_list(candidate.get("variation_axes"))) < 2:
            errors.append(_issue("insufficient_variation_axes", "at least two variation axes are required", f"{path}.variation_axes"))
        if len(_list(candidate.get("forbidden_copy_elements"))) < 1:
            errors.append(
                _issue("missing_forbidden_copy_elements", "forbidden_copy_elements is required", f"{path}.forbidden_copy_elements")
            )

        source_refs = _list(candidate.get("source_refs"))
        if not source_refs:
            errors.append(_issue("missing_source_refs", "source_refs is required", f"{path}.source_refs"))
        for ref_idx, source_ref in enumerate(source_refs):
            ref_path = f"{path}.source_refs[{ref_idx}]"
            if not isinstance(source_ref, Mapping):
                errors.append(_issue("invalid_source_ref", "source_ref must be an object", ref_path))
                continue
            for field in ("evidence_id", "source_hash", "chapter_hash", "excerpt_hash"):
                if not str(source_ref.get(field, "")).strip():
                    errors.append(_issue("missing_source_ref_field", f"{field} is required", f"{ref_path}.{field}"))

        safety = _mapping(candidate.get("safety"))
        if safety.get("source_contamination_check") not in {"pending", "pass"}:
            errors.append(
                _issue(
                    "invalid_source_contamination_check",
                    "source_contamination_check must be pending or pass",
                    f"{path}.safety.source_contamination_check",
                )
            )
        if safety.get("human_review_status") not in {"pending", "approved", "rejected"}:
            errors.append(
                _issue("invalid_human_review_status", "human_review_status must be pending/approved/rejected", f"{path}.safety.human_review_status")
            )

        target = _mapping(candidate.get("target"))
        if target.get("promote_to") != "none":
            errors.append(_issue("promotion_not_allowed", "v1.3-3 candidates must not promote automatically", f"{path}.target.promote_to"))

    return {"status": "failed" if errors else "passed", "errors": errors, "warnings": warnings}


def render_trope_recipe_report(payload: Mapping[str, Any]) -> str:
    """Render a source-marked candidate report without excerpts or source names."""

    gates = _mapping(payload.get("quality_gates"))
    candidates = payload.get("candidates", [])
    candidate_count = len(candidates) if isinstance(candidates, list) else 0
    lines = [
        SOURCE_MARKER,
        "",
        "# Trope Recipe Candidate Report",
        "",
        "## Summary",
        f"- schema_version: {payload.get('schema_version', '')}",
        f"- run_id: {payload.get('run_id', '')}",
        f"- source_run_id: {payload.get('source_run_id', '')}",
        f"- candidate_count: {candidate_count}",
        f"- promotion_status: {_mapping(payload.get('promotion')).get('status', '')}",
        "",
        "## Quality Gates",
        f"- status: {gates.get('status', '')}",
        f"- error_count: {len(_list(gates.get('errors')))}",
        f"- warning_count: {len(_list(gates.get('warnings')))}",
        "",
        "## Candidate Types",
    ]
    for recipe_type in sorted({str(item.get("recipe_type", "")) for item in candidates if isinstance(item, Mapping)}):
        if recipe_type:
            lines.append(f"- {recipe_type}")
    lines.extend(
        [
            "",
            "## Boundary",
            "- default_rag_excluded: true",
            "- runtime_state_write_allowed: false",
            "- raw_ideas_write_allowed: false",
            "- prompt_injection_allowed: false",
            "- promote_to: none",
            "",
        ]
    )
    return "\n".join(lines)


def _candidate_from_atom(atom: Mapping[str, Any], index: int, recipe_type: str) -> dict[str, Any]:
    chapter_hash = str(atom.get("chapter_sha256", ""))
    title_hash = str(atom.get("title_fingerprint", ""))
    source_chapter_id = str(atom.get("source_chapter_id", f"ch-{index:04d}"))
    return {
        "candidate_id": f"trope-{source_chapter_id}-{index:03d}",
        "candidate_type": "trope_recipe_candidate",
        "recipe_type": recipe_type,
        "pollution_source": True,
        "source_refs": [
            {
                "evidence_id": str(atom.get("atom_id", f"atom-{source_chapter_id}-001")),
                "source_hash": chapter_hash,
                "chapter_hash": chapter_hash,
                "excerpt_hash": title_hash,
                "chapter_locator": {"source_chapter_id": source_chapter_id},
            }
        ],
        "trope_core": _trope_core(recipe_type),
        "reader_payoff": _reader_payoff(recipe_type),
        "trigger_conditions": _trigger_conditions(recipe_type),
        "variation_axes": list(DEFAULT_VARIATION_AXES),
        "forbidden_copy_elements": [
            "source proper nouns",
            "source dialogue",
            "source event chain",
            "unique mystery answer",
        ],
        "safety": {
            "source_contamination_check": "pending",
            "similarity_score": None,
            "human_review_status": "pending",
        },
        "target": {"promote_to": "none"},
    }


def _trope_core(recipe_type: str) -> str:
    return {
        "underestimated_reversal": "弱势角色被低估后，通过公开验证场景证明隐藏能力，使地位判断发生反转。",
        "resource_pressure_breakthrough": "短期资源缺口制造明确压力，角色付出可见代价换取阶段性突破。",
        "misdirection_reveal": "前置线索先服务读者预期，再在关键节点转为身份或因果反差。",
    }[recipe_type]


def _reader_payoff(recipe_type: str) -> str:
    return {
        "underestimated_reversal": "读者获得压抑后的证明快感和地位重估快感。",
        "resource_pressure_breakthrough": "读者获得倒计时压力释放、代价兑现和成长确认。",
        "misdirection_reveal": "读者获得重读线索的恍然感和信息差被翻转的惊喜。",
    }[recipe_type]


def _trigger_conditions(recipe_type: str) -> list[str]:
    return {
        "underestimated_reversal": ["外界形成明确低估判断", "存在可公开验证的能力或成果"],
        "resource_pressure_breakthrough": ["资源缺口有时间压力", "突破收益和代价都能被读者理解"],
        "misdirection_reveal": ["前置线索可被合理误读", "揭示节点能改变读者对因果的判断"],
    }[recipe_type]


def _pollution_payload() -> dict[str, Any]:
    return {
        "pollution_source": True,
        "source_marker": SOURCE_MARKER,
        "default_rag_excluded": True,
        "prompt_injection_allowed": False,
        "runtime_state_write_allowed": False,
        "raw_ideas_write_allowed": False,
        "default_input_whitelist_allowed": False,
    }


def _issue(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _format_created_at(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
