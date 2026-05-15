"""v1.3-4 Promote Flow for reviewed trope recipe candidates.

Promotion is the only bridge from polluted `.ops/book_analysis` sidecar output
to governed Foundation assets.  It requires human approval, a passed
contamination check, and an explicit whitelisted target.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


ALLOWED_TARGETS = {
    "methodology": Path("foundation/assets/methodology"),
}

SCHEMA_VERSION = "0.4.0"


def promote_trope_recipes(
    recipe_payload: Mapping[str, Any],
    *,
    repo_root: str | Path,
    approved_candidate_ids: Sequence[str],
    target_kind: str,
) -> dict[str, Any]:
    """Promote approved trope recipe candidates into whitelisted assets."""

    root = Path(repo_root)
    if target_kind not in ALLOWED_TARGETS:
        raise ValueError(f"target_kind not whitelisted: {target_kind!r}")
    approved = {str(item) for item in approved_candidate_ids}
    if not approved:
        raise ValueError("approved_candidate_ids must not be empty")

    candidates = recipe_payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("recipe_payload.candidates must be a list")

    promoted_assets: list[dict[str, str]] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        candidate_id = str(candidate.get("candidate_id", ""))
        if candidate_id not in approved:
            continue
        _validate_promotable_candidate(candidate)
        rel_path = ALLOWED_TARGETS[target_kind] / f"promoted-{_slug(candidate_id)}.md"
        out_path = root / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_render_methodology_asset(candidate), encoding="utf-8")
        promoted_assets.append(
            {
                "candidate_id": candidate_id,
                "target_kind": target_kind,
                "path": rel_path.as_posix(),
            }
        )

    if not promoted_assets:
        raise ValueError("no approved candidates matched recipe_payload")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "promoted",
        "source_run_id": str(recipe_payload.get("run_id", "")),
        "target_kind": target_kind,
        "promoted_assets": promoted_assets,
    }


def _validate_promotable_candidate(candidate: Mapping[str, Any]) -> None:
    candidate_id = str(candidate.get("candidate_id", ""))
    if not candidate_id:
        raise ValueError("candidate_id is required")
    if candidate.get("candidate_type") != "trope_recipe_candidate":
        raise ValueError(f"candidate_type must be trope_recipe_candidate: {candidate_id}")
    safety = _mapping(candidate.get("safety"))
    if safety.get("human_review_status") != "approved":
        raise ValueError(f"human_review_status must be approved: {candidate_id}")
    if safety.get("source_contamination_check") != "pass":
        raise ValueError(f"source_contamination_check must be pass: {candidate_id}")
    similarity = safety.get("similarity_score")
    if isinstance(similarity, (int, float)) and similarity >= 0.8:
        raise ValueError(f"similarity_score too high for promotion: {candidate_id}")
    if not str(candidate.get("trope_core", "")).strip():
        raise ValueError(f"trope_core is required: {candidate_id}")
    if len(_list(candidate.get("forbidden_copy_elements"))) < 1:
        raise ValueError(f"forbidden_copy_elements is required: {candidate_id}")


def _render_methodology_asset(candidate: Mapping[str, Any]) -> str:
    candidate_id = str(candidate["candidate_id"])
    frontmatter = {
        "id": f"promoted-{_slug(candidate_id)}",
        "asset_type": "methodology",
        "title": f"Promoted Trope Recipe: {candidate_id}",
        "topic": ["reference_trope"],
        "stage": "ideation",
        "quality_grade": "B",
        "source_path": ".ops/book_analysis/**",
        "last_updated": "2026-05-15",
        "method_family": "创意",
        "rule_type": "guide",
        "promoted_from": candidate_id,
        "promotion_schema_version": SCHEMA_VERSION,
        "human_review_status": "approved",
        "source_contamination_check": "pass",
        "default_rag_eligible": False,
    }
    body = [
        "# Promoted Trope Recipe",
        "",
        f"- promoted_from: {candidate_id}",
        f"- recipe_type: {candidate.get('recipe_type', '')}",
        f"- trope_core: {candidate.get('trope_core', '')}",
        f"- reader_payoff: {candidate.get('reader_payoff', '')}",
        "",
        "## Trigger Conditions",
        *_bullet_lines(candidate.get("trigger_conditions")),
        "",
        "## Variation Axes",
        *_bullet_lines(candidate.get("variation_axes")),
        "",
        "## Forbidden Copy Elements",
        *_bullet_lines(candidate.get("forbidden_copy_elements")),
        "",
        "## Safety",
        "- This asset is de-sourced and manually approved.",
        "- Do not copy source names, dialogue, event chains, or unique mystery answers.",
    ]
    return (
        "---\n"
        + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "\n".join(body).rstrip()
        + "\n"
    )


def _bullet_lines(value: Any) -> list[str]:
    items = _list(value)
    return [f"- {item}" for item in items] if items else ["- none"]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return slug or "candidate"


__all__ = ["promote_trope_recipes", "ALLOWED_TARGETS"]
