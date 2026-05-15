"""Report-only model topology observation for Ginga.

This module records a role/stage/provider matrix and optional live probe
results. It does not select runtime providers, write StateIO, or mutate
workflow behavior.
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ginga_platform.orchestrator.registry.capability_registry import CapabilityRegistry


DEFAULT_OUTPUT_ROOT = Path(".ops/model_topology")
OUTPUT_BOUNDARY = ".ops/model_topology/<run_id>/"

ProbeRunner = Callable[[str, str], Mapping[str, Any]]

DEFAULT_ROLE_MATRIX: tuple[dict[str, Any], ...] = (
    {
        "role": "showrunner",
        "stage_refs": ["A_brainstorm", "B_premise_lock", "E_outline"],
        "capability": "planning / story architecture / conflict arbitration",
        "primary_tier": "strong reasoning",
        "fallback_tier": "medium reasoning",
        "output_boundary": "proposal_only",
        "human_gate": True,
        "probe_alias": "久久",
    },
    {
        "role": "prose_writer",
        "stage_refs": ["G_chapter_draft"],
        "capability": "chapter prose drafting with same-chapter-single-writer discipline",
        "primary_tier": "cn prose anchor",
        "fallback_tier": "same-family whole-chapter draft fallback",
        "output_boundary": "chapter_text_artifact",
        "human_gate": True,
        "probe_alias": "久久",
    },
    {
        "role": "state_settler",
        "stage_refs": ["H_chapter_settle", "R2_consistency_check"],
        "capability": "state delta audit and consistency review",
        "primary_tier": "deterministic asset-backed provider",
        "fallback_tier": "none without explicit operator review",
        "output_boundary": "candidate_or_audit_intent",
        "human_gate": True,
        "probe_alias": None,
    },
    {
        "role": "style_reviewer",
        "stage_refs": ["R1_style_polish", "review"],
        "capability": "style, anti-AI, and readability review",
        "primary_tier": "report-only reviewer",
        "fallback_tier": "deterministic local checks",
        "output_boundary": "report_only",
        "human_gate": False,
        "probe_alias": "久久",
    },
    {
        "role": "longform_critic",
        "stage_refs": ["review", "longform_quality_gate"],
        "capability": "batch continuity and drift detection",
        "primary_tier": "long-context critic",
        "fallback_tier": "human reviewer brief",
        "output_boundary": "report_only",
        "human_gate": True,
        "probe_alias": "久久",
    },
)


def export_model_topology_observation(
    *,
    run_id: str | None = None,
    output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    probe_live: bool = False,
    probe_targets: Sequence[Mapping[str, str]] | None = None,
    probe_runner: ProbeRunner | None = None,
) -> dict[str, Any]:
    """Export a report-only model topology observation packet."""

    resolved_run_id = run_id or _timestamp_run_id()
    output_dir = Path(output_root) / resolved_run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    role_matrix = [dict(row) for row in DEFAULT_ROLE_MATRIX]
    targets = _resolve_probe_targets(role_matrix, probe_targets)
    runner = probe_runner or _ask_llm_probe
    probe_results = [
        _run_probe(target, runner) if probe_live else _not_run_probe(target)
        for target in targets
    ]
    payload = {
        "schema_version": "v1.8-0",
        "mode": "report_only",
        "run_id": resolved_run_id,
        "generated_at": _now_iso(),
        "runtime_takeover": False,
        "stateio_mutation": False,
        "output_boundary": OUTPUT_BOUNDARY,
        "role_matrix": role_matrix,
        "runtime_surface": _runtime_surface(),
        "probe_summary": _summarize_probes(probe_live, probe_results),
        "probe_results": probe_results,
        "redlines": [
            "observation report must not select runtime providers",
            "probe results must not write StateIO or runtime_state",
            "critic/reviewer roles remain report-only",
            "provider snapshots are dated evidence, not long-term truth",
        ],
    }

    (output_dir / "model_topology_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(_render_readme(payload), encoding="utf-8")
    payload["output_dir"] = str(output_dir)
    return payload


def _resolve_probe_targets(
    role_matrix: Sequence[Mapping[str, Any]],
    probe_targets: Sequence[Mapping[str, str]] | None,
) -> list[dict[str, str]]:
    if probe_targets is not None:
        return [
            {"role": str(item["role"]), "alias": str(item["alias"])}
            for item in probe_targets
        ]
    targets: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in role_matrix:
        alias = row.get("probe_alias")
        if not alias:
            continue
        item = (str(row["role"]), str(alias))
        if item in seen:
            continue
        seen.add(item)
        targets.append({"role": item[0], "alias": item[1]})
    return targets


def _not_run_probe(target: Mapping[str, str]) -> dict[str, Any]:
    return {
        "role": target["role"],
        "alias": target["alias"],
        "status": "not_run",
        "ok": None,
        "latency_ms": None,
        "model": None,
        "error": "live probe disabled; pass --probe-live to run ask-llm probe",
    }


def _run_probe(target: Mapping[str, str], runner: ProbeRunner) -> dict[str, Any]:
    started = time.monotonic()
    alias = target["alias"]
    try:
        raw = dict(runner(alias, _probe_prompt(target["role"])))
        ok = bool(raw.get("ok"))
        latency = raw.get("latency_ms")
        if latency is None:
            latency = int((time.monotonic() - started) * 1000)
        return {
            "role": target["role"],
            "alias": alias,
            "status": "ok" if ok else "failed",
            "ok": ok,
            "latency_ms": latency,
            "model": raw.get("model"),
            "error": str(raw.get("error") or ""),
        }
    except Exception as exc:  # pragma: no cover - defensive around external command
        return {
            "role": target["role"],
            "alias": alias,
            "status": "failed",
            "ok": False,
            "latency_ms": int((time.monotonic() - started) * 1000),
            "model": None,
            "error": str(exc),
        }


def _ask_llm_probe(alias: str, prompt: str) -> dict[str, Any]:
    started = time.monotonic()
    proc = subprocess.run(
        ["ask-llm", alias, prompt, "--max-tokens", "64"],
        text=True,
        capture_output=True,
        check=False,
        timeout=45,
    )
    return {
        "ok": proc.returncode == 0,
        "latency_ms": int((time.monotonic() - started) * 1000),
        "model": None,
        "error": proc.stderr.strip()[-500:] if proc.returncode else "",
    }


def _probe_prompt(role: str) -> str:
    return f"Ginga model topology probe for role={role}. Reply with one short Chinese sentence."


def _runtime_surface() -> dict[str, Any]:
    registry = CapabilityRegistry.from_defaults()
    capabilities = registry.list_capabilities()
    return {
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "has_workflow_dsl": Path("ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml").exists(),
        "stateio_writer": "ginga_platform/orchestrator/runner/state_io.py",
        "report_only_surfaces": [
            ".ops/reviews/<book_id>/<run_id>/",
            ".ops/market_research/<book_id>/<run_id>/",
            ".ops/book_views/<book_id>/<run_id>/",
            OUTPUT_BOUNDARY,
        ],
    }


def _summarize_probes(probe_live: bool, results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ok_count = sum(1 for item in results if item.get("status") == "ok")
    failed_count = sum(1 for item in results if item.get("status") == "failed")
    return {
        "live_probe_enabled": probe_live,
        "target_count": len(results),
        "ok_count": ok_count,
        "failed_count": failed_count,
        "not_run_count": sum(1 for item in results if item.get("status") == "not_run"),
    }


def _render_readme(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Model Topology Observation",
        "",
        f"- run_id: `{payload['run_id']}`",
        f"- mode: `{payload['mode']}`",
        f"- runtime_takeover: `{payload['runtime_takeover']}`",
        f"- output_boundary: `{payload['output_boundary']}`",
        "",
        "## Role Matrix",
        "",
        "| role | stage_refs | primary_tier | output_boundary |",
        "|---|---|---|---|",
    ]
    for row in payload["role_matrix"]:
        lines.append(
            f"| {row['role']} | {', '.join(row['stage_refs'])} | "
            f"{row['primary_tier']} | {row['output_boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Probe Summary",
            "",
            f"- live_probe_enabled: `{payload['probe_summary']['live_probe_enabled']}`",
            f"- ok_count: `{payload['probe_summary']['ok_count']}`",
            f"- failed_count: `{payload['probe_summary']['failed_count']}`",
            f"- not_run_count: `{payload['probe_summary']['not_run_count']}`",
            "",
            "## Redlines",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["redlines"])
    lines.append("")
    return "\n".join(lines)


def _timestamp_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = ["export_model_topology_observation"]
