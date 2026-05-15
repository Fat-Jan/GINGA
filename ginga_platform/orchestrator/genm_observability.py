"""Report-only observability surfaces inspired by Genm optional mechanisms."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml


DEFAULT_EVIDENCE_PACK_ROOT = Path(".ops/jury/evidence_packs")
DEFAULT_WORKFLOW_OBSERVABILITY_ROOT = Path(".ops/workflow_observability")
DEFAULT_MIGRATION_AUDIT_ROOT = Path(".ops/migration_audit")
DEFAULT_WORKFLOW_PATH = Path("ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml")
FORBIDDEN_SOURCE_PATTERNS = (
    ".ops/book_analysis/**",
    ".ops/market_research/**",
    ".ops/external_sources/**",
    ".ops/jury/**",
    ".ops/reviews/**",
)


class GenmObservabilityError(RuntimeError):
    """Report-only observability contract error."""


def export_jury_evidence_pack(
    *,
    run_id: str | None = None,
    evidence_paths: Sequence[str | Path],
    output_root: str | Path = DEFAULT_EVIDENCE_PACK_ROOT,
) -> dict[str, Any]:
    """Export a citation-only evidence pack for external or human jury."""

    run = _safe_segment(run_id or _timestamp_run_id())
    out_dir = _prepare_output_dir(Path(output_root), run)
    refs = [_evidence_ref(Path(path)) for path in evidence_paths]
    payload = _base_payload("JuryEvidencePack", run)
    payload.update(
        {
            "output_boundary": ".ops/jury/evidence_packs/<run_id>/",
            "evidence_count": len(refs),
            "evidence_refs": refs,
            "instructions": [
                "Use evidence_refs as citations; do not copy report bodies into prompts by default.",
                "Jury conclusions remain report-only until operator_accept and promotion checks pass.",
            ],
        }
    )
    _write_packet(out_dir, "evidence_pack", payload, _render_evidence_pack_markdown(payload))
    payload["output_dir"] = str(out_dir)
    return payload


def export_workflow_stage_observation(
    *,
    run_id: str | None = None,
    workflow_path: str | Path = DEFAULT_WORKFLOW_PATH,
    output_root: str | Path = DEFAULT_WORKFLOW_OBSERVABILITY_ROOT,
) -> dict[str, Any]:
    """Export a read-only workflow stage observability report."""

    run = _safe_segment(run_id or _timestamp_run_id())
    out_dir = _prepare_output_dir(Path(output_root), run)
    workflow = _load_yaml(Path(workflow_path))
    steps = workflow.get("steps") or []
    if not isinstance(steps, list):
        raise GenmObservabilityError("workflow steps must be a list")
    stages = [_stage_summary(index, step) for index, step in enumerate(steps, start=1)]
    payload = _base_payload("WorkflowStageObservation", run)
    payload.update(
        {
            "output_boundary": ".ops/workflow_observability/<run_id>/",
            "workflow_path": str(workflow_path),
            "workflow_name": workflow.get("name", ""),
            "runs_workflow": False,
            "stage_count": len(stages),
            "stages": stages,
            "observability": {
                "state_read_count": sum(len(stage["state_reads"]) for stage in stages),
                "state_write_count": sum(len(stage["state_writes"]) for stage in stages),
                "postcondition_count": sum(len(stage["postconditions"]) for stage in stages),
                "skill_stage_count": sum(1 for stage in stages if stage["uses_skill"]),
            },
        }
    )
    _write_packet(out_dir, "workflow_stage_report", payload, _render_stage_markdown(payload))
    payload["output_dir"] = str(out_dir)
    return payload


def export_migration_audit(
    *,
    run_id: str | None = None,
    scan_roots: Sequence[str | Path],
    output_root: str | Path = DEFAULT_MIGRATION_AUDIT_ROOT,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Export a read-only migration/source-boundary audit."""

    run = _safe_segment(run_id or _timestamp_run_id())
    out_dir = _prepare_output_dir(Path(output_root), run)
    repo = Path(repo_root).resolve()
    files = _scan_files(scan_roots)
    rel_files = [_repo_relative(path, repo) for path in files]
    forbidden_hits = [rel for rel in rel_files if _matches_forbidden_source(rel)]
    payload = _base_payload("MigrationAuditReport", run)
    payload.update(
        {
            "output_boundary": ".ops/migration_audit/<run_id>/",
            "auto_migrate": False,
            "scan_roots": [str(path) for path in scan_roots],
            "scanned_file_count": len(rel_files),
            "forbidden_source_patterns": list(FORBIDDEN_SOURCE_PATTERNS),
            "forbidden_source_hits": forbidden_hits,
            "status": "needs_review" if forbidden_hits else "pass",
            "notes": [
                "This audit reports candidate migration risk only.",
                "It must not move, rewrite, promote, or delete source files.",
            ],
        }
    )
    _write_packet(out_dir, "migration_audit", payload, _render_migration_markdown(payload))
    payload["output_dir"] = str(out_dir)
    return payload


def _base_payload(kind: str, run_id: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "schema_version": "v1.8-3",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "report_only",
        "writes_runtime_state": False,
        "enters_creation_prompt": False,
        "default_rag_eligible": False,
    }


def _prepare_output_dir(output_root: Path, run_id: str) -> Path:
    out_dir = output_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_packet(out_dir: Path, stem: str, payload: dict[str, Any], markdown: str) -> None:
    (out_dir / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "README.md").write_text(markdown, encoding="utf-8")


def _evidence_ref(path: Path) -> dict[str, Any]:
    exists = path.exists()
    stat = path.stat() if exists else None
    return {
        "path": str(path),
        "exists": exists,
        "sha256": _sha256(path) if exists and path.is_file() else "",
        "bytes": stat.st_size if stat else 0,
        "kind_hint": _kind_hint(path),
    }


def _kind_hint(path: Path) -> str:
    name = path.name
    if name.endswith(".json"):
        return "json_report"
    if name.endswith(".md"):
        return "markdown_report"
    if name.endswith((".yaml", ".yml")):
        return "yaml_manifest"
    return "file_ref"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise GenmObservabilityError(f"workflow must be mapping: {path}")
    return data


def _stage_summary(index: int, step: Any) -> dict[str, Any]:
    if not isinstance(step, dict):
        raise GenmObservabilityError(f"workflow step #{index} must be mapping")
    return {
        "index": index,
        "id": str(step.get("id") or ""),
        "uses_capability": step.get("uses_capability"),
        "uses_skill": step.get("uses_skill"),
        "state_reads": _string_list(step.get("state_reads")),
        "state_writes": _string_list(step.get("state_writes")),
        "preconditions": _string_list(step.get("preconditions")),
        "postconditions": _string_list(step.get("postconditions")),
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _scan_files(scan_roots: Sequence[str | Path]) -> list[Path]:
    files: list[Path] = []
    for root in scan_roots:
        path = Path(root)
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(files)


def _repo_relative(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _matches_forbidden_source(rel_path: str) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in FORBIDDEN_SOURCE_PATTERNS)


def _safe_segment(value: str) -> str:
    if not value or "/" in value or ".." in value:
        raise GenmObservabilityError(f"invalid path segment: {value!r}")
    return value


def _timestamp_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _render_evidence_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Jury Evidence Pack: {payload['run_id']}",
        "",
        "> Report-only citation packet. It does not copy evidence bodies into prompts.",
        "",
        f"- evidence_count: {payload['evidence_count']}",
        f"- default_rag_eligible: `{payload['default_rag_eligible']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in payload["evidence_refs"]:
        lines.append(f"- `{item['path']}` exists={item['exists']} bytes={item['bytes']} sha256={item['sha256']}")
    lines.append("")
    return "\n".join(lines)


def _render_stage_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Workflow Stage Observation: {payload['run_id']}",
        "",
        "> Report-only workflow observability. It never runs the workflow.",
        "",
        f"- workflow: `{payload['workflow_path']}`",
        f"- stage_count: {payload['stage_count']}",
        f"- runs_workflow: `{payload['runs_workflow']}`",
        "",
        "## Stages",
        "",
    ]
    for stage in payload["stages"]:
        lines.append(
            f"- {stage['index']}. `{stage['id']}` capability={stage['uses_capability']} "
            f"skill={stage['uses_skill']} writes={stage['state_writes']}"
        )
    lines.append("")
    return "\n".join(lines)


def _render_migration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Migration Audit: {payload['run_id']}",
        "",
        "> Report-only audit. It does not move, rewrite, or promote files.",
        "",
        f"- status: `{payload['status']}`",
        f"- scanned_file_count: {payload['scanned_file_count']}",
        f"- forbidden_hit_count: {len(payload['forbidden_source_hits'])}",
        "",
        "## Forbidden Source Hits",
        "",
    ]
    if not payload["forbidden_source_hits"]:
        lines.append("- none")
    for path in payload["forbidden_source_hits"]:
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_EVIDENCE_PACK_ROOT",
    "DEFAULT_MIGRATION_AUDIT_ROOT",
    "DEFAULT_WORKFLOW_OBSERVABILITY_ROOT",
    "DEFAULT_WORKFLOW_PATH",
    "FORBIDDEN_SOURCE_PATTERNS",
    "GenmObservabilityError",
    "export_jury_evidence_pack",
    "export_migration_audit",
    "export_workflow_stage_observation",
]
