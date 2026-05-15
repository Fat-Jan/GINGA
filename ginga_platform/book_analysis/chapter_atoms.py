"""Chapter Atom v1.3-2 sidecar builder.

The atom payload is intentionally structural. It records stable identifiers,
hashes, offsets, and quality-gate results, but never stores chapter titles or
source excerpts.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from .manifest import SOURCE_MARKER


SCHEMA_VERSION = "0.2.0"
FORBIDDEN_FIELDS = {"title", "excerpt", "text", "content", "body", "raw_text", "source_text"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def extract_chapter_atoms(
    chapter_index: list[Mapping[str, Any]],
    *,
    run_id: str | None = None,
    created_at: Any = None,
    source_run_id: str | None = None,
) -> dict[str, Any]:
    """Extract structure-only chapter-boundary atoms from a P0 chapter index."""

    atoms: list[dict[str, Any]] = []
    for idx, chapter in enumerate(chapter_index, start=1):
        chapter_id = str(chapter.get("chapter_id", f"ch-{idx:04d}"))
        start_offset = _int_or_zero(chapter.get("start_offset"))
        end_offset = _int_or_zero(chapter.get("end_offset"))
        char_count = _int_or_zero(chapter.get("char_count"))
        title = str(chapter.get("title", ""))
        atoms.append(
            {
                "atom_id": f"atom-{chapter_id}-001",
                "atom_type": "chapter_boundary",
                "source_chapter_id": chapter_id,
                "source_chapter_no": chapter.get("chapter_no"),
                "ordinal": 1,
                "offset_range": {"start": start_offset, "end": end_offset},
                "char_count": char_count,
                "chapter_sha256": str(chapter.get("sha256", "")),
                "title_fingerprint": sha256(title.encode("utf-8")).hexdigest(),
                "pollution": _pollution_payload(),
            }
        )

    gates = evaluate_quality_gates(atoms)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": _format_created_at(created_at),
        "source_run_id": source_run_id,
        "pollution": _pollution_payload(),
        "chapter_atoms": atoms,
        "quality_gates": gates,
    }


def write_chapter_atoms_run(source_run_root: str | Path, run_id: str, output_base: str | Path) -> Path:
    """Build a Chapter Atom sidecar run from a P0 Reference Corpus run."""

    source_run_root = Path(source_run_root)
    output_base = Path(output_base)
    run_root = output_base / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    chapter_index = json.loads((source_run_root / "chapter_index.json").read_text(encoding="utf-8"))
    source_manifest = json.loads((source_run_root / "source_manifest.json").read_text(encoding="utf-8"))
    source_run_id = str(source_manifest.get("run_id", source_run_root.name))
    created_at = _format_created_at(None)
    payload = extract_chapter_atoms(
        chapter_index,
        run_id=run_id,
        created_at=created_at,
        source_run_id=source_run_id,
    )
    gates = payload["quality_gates"]
    run_config = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "source_run_id": source_run_id,
        "source_run_root": str(source_run_root),
        "output_root": str(run_root),
        "inputs": {
            "chapter_index_path": str(source_run_root / "chapter_index.json"),
            "source_manifest_path": str(source_run_root / "source_manifest.json"),
        },
        "outputs": {
            "chapter_atoms_path": str(run_root / "chapter_atoms.json"),
            "quality_gates_path": str(run_root / "quality_gates.json"),
            "report_path": str(run_root / "chapter_atom_report.md"),
        },
        "pollution": _pollution_payload(),
    }

    (run_root / "chapter_atoms.json").write_text(_json(payload), encoding="utf-8")
    (run_root / "quality_gates.json").write_text(_json(gates), encoding="utf-8")
    (run_root / "chapter_atom_report.md").write_text(render_chapter_atom_report(payload), encoding="utf-8")
    (run_root / "run_config.json").write_text(_json(run_config), encoding="utf-8")
    return run_root


def evaluate_quality_gates(atoms: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Return rejectable quality gates for a Chapter Atom payload."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for idx, atom in enumerate(atoms):
        path = f"chapter_atoms[{idx}]"
        atom_id = str(atom.get("atom_id", ""))
        if not atom_id:
            errors.append(_issue("missing_atom_id", "atom_id is required", f"{path}.atom_id"))
        elif atom_id in seen_ids:
            errors.append(_issue("duplicate_atom_id", "atom_id must be unique", f"{path}.atom_id"))
        seen_ids.add(atom_id)

        if not atom.get("source_chapter_id"):
            errors.append(_issue("missing_source_chapter_id", "source_chapter_id is required", f"{path}.source_chapter_id"))
        if not SHA256_RE.match(str(atom.get("chapter_sha256", ""))):
            errors.append(_issue("invalid_chapter_sha256", "chapter_sha256 must be 64 lowercase hex chars", f"{path}.chapter_sha256"))
        if not SHA256_RE.match(str(atom.get("title_fingerprint", ""))):
            errors.append(
                _issue("invalid_title_fingerprint", "title_fingerprint must be 64 lowercase hex chars", f"{path}.title_fingerprint")
            )
        for field in FORBIDDEN_FIELDS:
            if field in atom:
                errors.append(_issue("forbidden_field_saved", f"{field} must not be saved", f"{path}.{field}"))

        offset_range = atom.get("offset_range")
        if not isinstance(offset_range, Mapping):
            errors.append(_issue("invalid_offset_range", "offset_range must be an object", f"{path}.offset_range"))
            continue
        start = offset_range.get("start")
        end = offset_range.get("end")
        char_count = atom.get("char_count")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
            errors.append(_issue("invalid_offset_range", "offset_range must satisfy 0 <= start <= end", f"{path}.offset_range"))
        if isinstance(char_count, int) and char_count < 0:
            errors.append(_issue("invalid_char_count", "char_count must be non-negative", f"{path}.char_count"))

    return {"status": "failed" if errors else "passed", "errors": errors, "warnings": warnings}


def render_chapter_atom_report(payload: Mapping[str, Any]) -> str:
    """Render a source-marked structural report without chapter titles/excerpts."""

    gates = payload.get("quality_gates", {})
    atoms = payload.get("chapter_atoms", [])
    lines = [
        SOURCE_MARKER,
        "",
        "# Chapter Atom Report",
        "",
        "## Summary",
        f"- schema_version: {payload.get('schema_version', '')}",
        f"- run_id: {payload.get('run_id', '')}",
        f"- source_run_id: {payload.get('source_run_id', '')}",
        f"- atom_count: {len(atoms) if isinstance(atoms, list) else 0}",
        "",
        "## Quality Gates",
        f"- status: {gates.get('status', '') if isinstance(gates, Mapping) else ''}",
        f"- error_count: {len(gates.get('errors', [])) if isinstance(gates, Mapping) else 0}",
        f"- warning_count: {len(gates.get('warnings', [])) if isinstance(gates, Mapping) else 0}",
        "",
        "## Atom Types",
        "- chapter_boundary",
        "",
    ]
    return "\n".join(lines)


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


def _int_or_zero(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
