"""Pure validation helpers for Reference Corpus P0 payloads."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .manifest import SOURCE_MARKER


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BOOK_ANALYSIS_RUN_FILES = (
    ("chapter_atoms.json", "missing_chapter_atoms"),
    ("quality_gates.json", "missing_quality_gates"),
    ("chapter_atom_report.md", "missing_chapter_atom_report"),
)
TROPE_RECIPE_RUN_FILES = (
    ("trope_recipes.json", "missing_trope_recipes"),
    ("quality_gates.json", "missing_quality_gates"),
    ("trope_recipe_report.md", "missing_trope_recipe_report"),
)
FORBIDDEN_ATOM_TEXT_FIELDS = {
    "excerpt",
    "text",
    "content",
    "body",
    "raw_text",
    "source_text",
    "title",
}
FORBIDDEN_RECIPE_TEXT_FIELDS = FORBIDDEN_ATOM_TEXT_FIELDS | {
    "asset",
    "prompt",
    "raw_idea",
    "runtime_state",
}
PROMOTED_TROPE_REQUIRED_FIELDS = (
    "id",
    "asset_type",
    "title",
    "topic",
    "stage",
    "quality_grade",
    "source_path",
    "last_updated",
    "promoted_from",
    "human_review_status",
    "source_contamination_check",
    "default_rag_eligible",
)


def validate_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a manifest dict without touching the filesystem."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for field in (
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
    ):
        if field not in payload:
            errors.append(_issue("missing_field", f"manifest missing {field}", field))

    source = _mapping(payload.get("source"))
    if not SHA256_RE.match(str(source.get("sha256", ""))):
        errors.append(_issue("invalid_sha256", "source sha256 must be 64 lowercase hex chars", "source.sha256"))
    if source.get("encoding") in (None, ""):
        errors.append(_issue("missing_encoding", "source encoding is required", "source.encoding"))
    if source.get("input_size_bytes", -1) < 0:
        errors.append(_issue("invalid_input_size", "source input size must be non-negative", "source.input_size_bytes"))

    chapters = _mapping(payload.get("chapters"))
    if chapters.get("count", -1) < 0:
        errors.append(_issue("invalid_chapter_count", "chapter count must be non-negative", "chapters.count"))
    if chapters.get("count") == 0:
        has_no_heading = any(item.get("code") == "no_chapter_heading" for item in _list(chapters.get("anomalies")))
        if not has_no_heading:
            errors.append(_issue("missing_no_heading_error", "zero chapters must record no_chapter_heading", "chapters.anomalies"))

    pollution = _mapping(payload.get("pollution"))
    if pollution.get("pollution_source") is not True:
        errors.append(_issue("missing_pollution_source", "pollution_source must be true", "pollution.pollution_source"))
    if pollution.get("source_marker") != SOURCE_MARKER:
        errors.append(_issue("missing_source_marker", "source marker must be [SOURCE_TROPE]", "pollution.source_marker"))
    if pollution.get("default_rag_excluded") is not True:
        errors.append(_issue("rag_not_excluded", "default RAG exclusion must be true", "pollution.default_rag_excluded"))
    for field in (
        "prompt_injection_allowed",
        "runtime_state_write_allowed",
        "raw_ideas_write_allowed",
        "default_input_whitelist_allowed",
    ):
        if pollution.get(field) is not False:
            errors.append(_issue("boundary_flag_not_false", f"{field} must be false", f"pollution.{field}"))

    keyword_sources = _mapping(payload.get("keyword_sources"))
    if keyword_sources.get("active") is not False:
        warnings.append(_issue("keyword_sources_active", "P0 keyword_sources.active should be false", "keyword_sources.active"))

    resources = _mapping(payload.get("resources"))
    if resources.get("excerpt_chars_saved") != 0:
        errors.append(_issue("excerpt_saved", "P0 must not save excerpts", "resources.excerpt_chars_saved"))
    if resources.get("private_cache_bytes") != 0:
        errors.append(_issue("private_cache_saved", "P0 must not save private cache bytes", "resources.private_cache_bytes"))

    validation = _mapping(payload.get("validation"))
    if errors and validation.get("status") == "passed":
        errors.append(_issue("invalid_passed_status", "manifest with errors cannot be passed", "validation.status"))

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_manifest_dict(
    payload: Mapping[str, Any],
    *,
    chapter_index: Any | None = None,
    run_root: str | Path | None = None,
    recall_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate manifest structure plus optional chapter/RAG boundary inputs."""

    report = validate_manifest_payload(payload)
    errors = list(report["errors"])
    warnings = list(report["warnings"])

    output = _mapping(payload.get("output"))
    if run_root is not None:
        root = Path(run_root)
        for key in ("manifest_path", "chapter_index_path", "report_path"):
            raw_path = output.get(key)
            if raw_path and not _is_within(root, Path(str(raw_path))):
                errors.append(_issue("output_path_outside_run_root", f"{key} is outside run root", f"output.{key}"))

    if chapter_index is not None:
        chapter_report = validate_chapter_index_payload(chapter_index)
        errors.extend(chapter_report["errors"])
        warnings.extend(chapter_report["warnings"])
        chapters = _mapping(payload.get("chapters"))
        if isinstance(chapter_index, list) and chapters.get("count") != len(chapter_index):
            errors.append(_issue("chapter_count_mismatch", "manifest chapter count differs from chapter_index", "chapters.count"))

    if recall_config is not None:
        if _recall_sources_include_book_analysis(recall_config):
            errors.append(
                _issue(
                    "default_rag_not_excluded",
                    "default RAG recall_sources includes .ops/book_analysis",
                    "recall_config.recall_sources",
                )
            )
        if not _recall_forbidden_excludes_book_analysis(recall_config):
            errors.append(
                _issue(
                    "rag_forbidden_missing",
                    "default RAG recall_forbidden_paths must exclude .ops/book_analysis",
                    "recall_config.recall_forbidden_paths",
                )
            )

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_chapter_index_payload(payload: Any) -> dict[str, Any]:
    """Validate a chapter_index payload without touching the filesystem."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(payload, list):
        return {
            "status": "failed",
            "errors": [_issue("invalid_chapter_index", "chapter index must be a list", "chapter_index")],
            "warnings": [],
        }

    seen_titles: dict[str, str] = {}
    previous_no: int | None = None
    for idx, item in enumerate(payload):
        path = f"chapter_index[{idx}]"
        if not isinstance(item, Mapping):
            errors.append(_issue("invalid_chapter_entry", "chapter entry must be an object", path))
            continue
        for field in ("chapter_id", "title", "start_offset", "end_offset", "char_count", "sha256", "anomalies"):
            if field not in item:
                errors.append(_issue("missing_chapter_field", f"chapter entry missing {field}", f"{path}.{field}"))
        if not SHA256_RE.match(str(item.get("sha256", ""))):
            errors.append(_issue("invalid_chapter_sha256", "chapter sha256 must be 64 lowercase hex chars", f"{path}.sha256"))
        if item.get("end_offset", 0) < item.get("start_offset", 0):
            errors.append(_issue("invalid_offsets", "end_offset must be >= start_offset", path))
        title = str(item.get("title", ""))
        if title in seen_titles:
            warnings.append(_issue("duplicate_title", f"duplicate title also seen at {seen_titles[title]}", f"{path}.title"))
        else:
            seen_titles[title] = str(item.get("chapter_id", path))
        chapter_no = item.get("chapter_no")
        if isinstance(chapter_no, int):
            if previous_no is not None and chapter_no <= previous_no:
                warnings.append(_issue("out_of_order", "chapter number is not increasing", f"{path}.chapter_no"))
            previous_no = chapter_no

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_reference_corpus(run_root: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate files produced by the P0 corpus builder."""

    run_root = Path(run_root)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    manifest_path = run_root / "source_manifest.json"
    chapter_index_path = run_root / "chapter_index.json"
    report_path = run_root / "scan_report.md"

    for path, code in (
        (manifest_path, "missing_manifest"),
        (chapter_index_path, "missing_chapter_index"),
        (report_path, "missing_report"),
    ):
        if not path.exists():
            errors.append(_issue(code, f"missing {path.name}", str(path)))
    if errors:
        return {"status": "failed", "errors": errors, "warnings": warnings}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chapter_index = json.loads(chapter_index_path.read_text(encoding="utf-8"))
    report = validate_manifest_dict(
        manifest,
        chapter_index=chapter_index,
        run_root=run_root,
        recall_config=_load_recall_config(repo_root),
    )
    errors.extend(report["errors"])
    warnings.extend(report["warnings"])

    if not report_path.read_text(encoding="utf-8").startswith(SOURCE_MARKER):
        errors.append(_issue("missing_report_source_marker", "report must start with [SOURCE_TROPE]", str(report_path)))
    if (run_root / ".private_evidence").exists():
        errors.append(_issue("private_evidence_created", "P0 must not create .private_evidence", str(run_root / ".private_evidence")))

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_chapter_atoms_run(run_root: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate files produced by the v1.3-2 chapter atom sidecar builder."""

    run_root = Path(run_root)
    root_for_boundary = Path(repo_root) if repo_root is not None else Path.cwd()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not _is_within(root_for_boundary / ".ops" / "book_analysis", run_root):
        errors.append(
            _issue(
                "run_root_outside_book_analysis",
                "chapter atom run_root must be under .ops/book_analysis",
                str(run_root),
            )
        )

    atoms_path = run_root / "chapter_atoms.json"
    gates_path = run_root / "quality_gates.json"
    report_path = run_root / "chapter_atom_report.md"
    for filename, code in BOOK_ANALYSIS_RUN_FILES:
        path = run_root / filename
        if not path.exists():
            errors.append(_issue(code, f"missing {filename}", str(path)))
    if errors:
        return {"status": "failed", "errors": errors, "warnings": warnings}

    atoms_payload = _read_json_mapping(atoms_path, errors)
    gates_payload = _read_json_mapping(gates_path, errors)
    if errors:
        return {"status": "failed", "errors": errors, "warnings": warnings}

    _validate_chapter_atom_payload(atoms_payload, atoms_path, run_root, errors, warnings)
    _validate_quality_gates(gates_payload, gates_path, errors)
    embedded_gates = atoms_payload.get("quality_gates")
    if isinstance(embedded_gates, Mapping):
        _validate_quality_gates(embedded_gates, atoms_path, errors)
    else:
        errors.append(_issue("missing_quality_gates", "chapter_atoms.json must embed quality_gates", str(atoms_path)))

    report_text = report_path.read_text(encoding="utf-8")
    if not report_text.startswith(SOURCE_MARKER):
        errors.append(_issue("missing_report_source_marker", "report must start with [SOURCE_TROPE]", str(report_path)))

    if (run_root / ".private_evidence").exists():
        errors.append(
            _issue(
                "private_evidence_created",
                "chapter atom run must not create .private_evidence",
                str(run_root / ".private_evidence"),
            )
        )

    recall_config = _load_recall_config(repo_root)
    if recall_config is not None:
        if _recall_sources_include_book_analysis(recall_config):
            errors.append(
                _issue(
                    "default_rag_not_excluded",
                    "default RAG recall_sources includes .ops/book_analysis",
                    "recall_config.recall_sources",
                )
            )
        if not _recall_forbidden_excludes_book_analysis(recall_config):
            errors.append(
                _issue(
                    "rag_forbidden_missing",
                    "default RAG recall_forbidden_paths must exclude .ops/book_analysis",
                    "recall_config.recall_forbidden_paths",
                )
            )

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_trope_recipe_run(run_root: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate files produced by the v1.3-3 Trope Recipe Candidate builder."""

    run_root = Path(run_root)
    root_for_boundary = Path(repo_root) if repo_root is not None else Path.cwd()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not _is_within(root_for_boundary / ".ops" / "book_analysis", run_root):
        errors.append(
            _issue(
                "run_root_outside_book_analysis",
                "trope recipe run_root must be under .ops/book_analysis",
                str(run_root),
            )
        )

    recipe_path = run_root / "trope_recipes.json"
    gates_path = run_root / "quality_gates.json"
    report_path = run_root / "trope_recipe_report.md"
    for filename, code in TROPE_RECIPE_RUN_FILES:
        path = run_root / filename
        if not path.exists():
            errors.append(_issue(code, f"missing {filename}", str(path)))
    if errors:
        return {"status": "failed", "errors": errors, "warnings": warnings}

    recipe_payload = _read_json_mapping(recipe_path, errors)
    gates_payload = _read_json_mapping(gates_path, errors)
    if errors:
        return {"status": "failed", "errors": errors, "warnings": warnings}

    _validate_trope_recipe_payload(recipe_payload, recipe_path, run_root, errors, warnings)
    _validate_quality_gates(gates_payload, gates_path, errors)
    embedded_gates = recipe_payload.get("quality_gates")
    if isinstance(embedded_gates, Mapping):
        _validate_quality_gates(embedded_gates, recipe_path, errors)
    else:
        errors.append(_issue("missing_quality_gates", "trope_recipes.json must embed quality_gates", str(recipe_path)))

    report_text = report_path.read_text(encoding="utf-8")
    if not report_text.startswith(SOURCE_MARKER):
        errors.append(_issue("missing_report_source_marker", "report must start with [SOURCE_TROPE]", str(report_path)))
    if ".private_evidence" in report_text:
        errors.append(_issue("private_evidence_referenced", "report must not reference .private_evidence", str(report_path)))

    if (run_root / ".private_evidence").exists():
        errors.append(
            _issue(
                "private_evidence_created",
                "trope recipe run must not create .private_evidence",
                str(run_root / ".private_evidence"),
            )
        )

    recall_config = _load_recall_config(repo_root)
    if recall_config is not None:
        if _recall_sources_include_book_analysis(recall_config):
            errors.append(
                _issue(
                    "default_rag_not_excluded",
                    "default RAG recall_sources includes .ops/book_analysis",
                    "recall_config.recall_sources",
                )
            )
        if not _recall_forbidden_excludes_book_analysis(recall_config):
            errors.append(
                _issue(
                    "rag_forbidden_missing",
                    "default RAG recall_forbidden_paths must exclude .ops/book_analysis",
                    "recall_config.recall_forbidden_paths",
                )
            )

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def validate_promoted_trope_assets(
    assets_root: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate v1.3-4 promoted trope assets stay in the approved whitelist."""

    assets_root = Path(assets_root)
    root_for_boundary = Path(repo_root) if repo_root is not None else Path.cwd()
    allowed_root = root_for_boundary / "foundation" / "assets" / "methodology"
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not _is_within(allowed_root, assets_root):
        errors.append(
            _issue(
                "promote_target_not_whitelisted",
                "promoted trope assets must be under foundation/assets/methodology",
                str(assets_root),
            )
        )
    paths = sorted(assets_root.glob("promoted-*.md")) if assets_root.exists() else []
    if not paths:
        errors.append(_issue("missing_promoted_assets", "no promoted trope assets found", str(assets_root)))

    for path in paths:
        frontmatter = _read_markdown_frontmatter(path, errors)
        if not frontmatter:
            continue
        for field in PROMOTED_TROPE_REQUIRED_FIELDS:
            if field not in frontmatter:
                errors.append(_issue("missing_promoted_field", f"missing {field}", f"{path}:{field}"))
        if frontmatter.get("asset_type") != "methodology":
            errors.append(_issue("invalid_promoted_asset_type", "promoted asset_type must be methodology", f"{path}:asset_type"))
        if frontmatter.get("human_review_status") != "approved":
            errors.append(_issue("promote_review_missing", "human_review_status must be approved", f"{path}:human_review_status"))
        if frontmatter.get("source_contamination_check") != "pass":
            errors.append(
                _issue("promote_contamination_missing", "source_contamination_check must be pass", f"{path}:source_contamination_check")
            )
        if frontmatter.get("default_rag_eligible") is not False:
            errors.append(_issue("promote_rag_flag_invalid", "default_rag_eligible must be false", f"{path}:default_rag_eligible"))
        if not str(frontmatter.get("promoted_from", "")).startswith("trope-"):
            errors.append(_issue("invalid_promoted_from", "promoted_from must reference a trope candidate", f"{path}:promoted_from"))

    return {"status": "failed" if errors else ("warning" if warnings else "passed"), "errors": errors, "warnings": warnings}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _issue(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _read_json_mapping(path: Path, errors: list[dict[str, str]]) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(_issue("invalid_json", f"{path.name} is not valid JSON: {exc}", str(path)))
        return {}
    if not isinstance(payload, Mapping):
        errors.append(_issue("invalid_payload", f"{path.name} must contain a JSON object", str(path)))
        return {}
    return payload


def _read_markdown_frontmatter(path: Path, errors: list[dict[str, str]]) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(_issue("missing_frontmatter", "promoted asset must start with YAML frontmatter", str(path)))
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        errors.append(_issue("unterminated_frontmatter", "promoted asset frontmatter is unterminated", str(path)))
        return {}
    try:
        import yaml

        payload = yaml.safe_load(text[4:end]) or {}
    except Exception as exc:  # noqa: BLE001
        errors.append(_issue("invalid_frontmatter", f"cannot parse frontmatter: {exc}", str(path)))
        return {}
    if not isinstance(payload, Mapping):
        errors.append(_issue("invalid_frontmatter", "frontmatter must be a mapping", str(path)))
        return {}
    return payload


def _validate_chapter_atom_payload(
    payload: Mapping[str, Any],
    payload_path: Path,
    run_root: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    del warnings

    pollution = _mapping(payload.get("pollution"))
    if pollution.get("pollution_source") is not True:
        errors.append(_issue("missing_pollution_source", "pollution_source must be true", f"{payload_path}:pollution.pollution_source"))
    if pollution.get("source_marker") != SOURCE_MARKER:
        errors.append(_issue("missing_source_marker", "source marker must be [SOURCE_TROPE]", f"{payload_path}:pollution.source_marker"))
    if pollution.get("default_rag_excluded") is not True:
        errors.append(_issue("rag_not_excluded", "default RAG exclusion must be true", f"{payload_path}:pollution.default_rag_excluded"))

    output = _mapping(payload.get("output"))
    for key, value in output.items():
        if isinstance(value, str) and value and not _is_within(run_root, Path(value)):
            errors.append(_issue("output_path_outside_run_root", f"{key} is outside run root", f"{payload_path}:output.{key}"))

    atoms = payload.get("chapter_atoms")
    if not isinstance(atoms, list):
        errors.append(_issue("invalid_chapter_atoms", "chapter_atoms must be a list", f"{payload_path}:chapter_atoms"))
        return
    for idx, atom in enumerate(atoms):
        path = f"{payload_path}:chapter_atoms[{idx}]"
        if not isinstance(atom, Mapping):
            errors.append(_issue("invalid_chapter_atom", "chapter atom must be an object", path))
            continue
        _reject_forbidden_atom_fields(atom, path, errors)


def _validate_trope_recipe_payload(
    payload: Mapping[str, Any],
    payload_path: Path,
    run_root: Path,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    del warnings

    pollution = _mapping(payload.get("pollution"))
    if pollution.get("pollution_source") is not True:
        errors.append(_issue("missing_pollution_source", "pollution_source must be true", f"{payload_path}:pollution.pollution_source"))
    if pollution.get("source_marker") != SOURCE_MARKER:
        errors.append(_issue("missing_source_marker", "source marker must be [SOURCE_TROPE]", f"{payload_path}:pollution.source_marker"))
    if pollution.get("default_rag_excluded") is not True:
        errors.append(_issue("rag_not_excluded", "default RAG exclusion must be true", f"{payload_path}:pollution.default_rag_excluded"))
    for field in (
        "prompt_injection_allowed",
        "runtime_state_write_allowed",
        "raw_ideas_write_allowed",
        "default_input_whitelist_allowed",
    ):
        if pollution.get(field) is not False:
            errors.append(_issue("boundary_flag_not_false", f"{field} must be false", f"{payload_path}:pollution.{field}"))

    output = _mapping(payload.get("output"))
    for key, value in output.items():
        if isinstance(value, str) and value and not _is_within(run_root, Path(value)):
            errors.append(_issue("output_path_outside_run_root", f"{key} is outside run root", f"{payload_path}:output.{key}"))

    promotion = _mapping(payload.get("promotion"))
    if promotion.get("status") != "not_promoted":
        errors.append(_issue("promotion_not_allowed", "v1.3-3 run must stay not_promoted", f"{payload_path}:promotion.status"))
    if promotion.get("promote_to") != "none":
        errors.append(_issue("promotion_not_allowed", "v1.3-3 run must not target promotion", f"{payload_path}:promotion.promote_to"))

    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        errors.append(_issue("invalid_trope_recipes", "candidates must be a list", f"{payload_path}:candidates"))
        return
    if not candidates:
        errors.append(_issue("missing_candidates", "at least one candidate is required", f"{payload_path}:candidates"))
        return

    seen_ids: set[str] = set()
    for idx, candidate in enumerate(candidates):
        path = f"{payload_path}:candidates[{idx}]"
        if not isinstance(candidate, Mapping):
            errors.append(_issue("invalid_trope_recipe", "candidate must be an object", path))
            continue
        candidate_id = str(candidate.get("candidate_id", ""))
        if not candidate_id:
            errors.append(_issue("missing_candidate_id", "candidate_id is required", f"{path}.candidate_id"))
        elif candidate_id in seen_ids:
            errors.append(_issue("duplicate_candidate_id", "candidate_id must be unique", f"{path}.candidate_id"))
        seen_ids.add(candidate_id)

        if candidate.get("pollution_source") is not True:
            errors.append(_issue("missing_pollution_source", "pollution_source must be true", f"{path}.pollution_source"))
        if candidate.get("candidate_type") != "trope_recipe_candidate":
            errors.append(_issue("invalid_candidate_type", "candidate_type must be trope_recipe_candidate", f"{path}.candidate_type"))
        if not str(candidate.get("trope_core", "")).strip():
            errors.append(_issue("missing_trope_core", "trope_core is required", f"{path}.trope_core"))
        if not str(candidate.get("reader_payoff", "")).strip():
            errors.append(_issue("missing_reader_payoff", "reader_payoff is required", f"{path}.reader_payoff"))
        if len(_list(candidate.get("trigger_conditions"))) < 1:
            errors.append(_issue("missing_trigger_conditions", "trigger_conditions is required", f"{path}.trigger_conditions"))
        if len(_list(candidate.get("variation_axes"))) < 2:
            errors.append(_issue("insufficient_variation_axes", "variation_axes must contain at least two items", f"{path}.variation_axes"))
        if len(_list(candidate.get("forbidden_copy_elements"))) < 1:
            errors.append(_issue("missing_forbidden_copy_elements", "forbidden_copy_elements is required", f"{path}.forbidden_copy_elements"))

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
            if ".private_evidence" in json.dumps(source_ref, ensure_ascii=False):
                errors.append(_issue("private_evidence_referenced", "source_ref must not reference .private_evidence", ref_path))

        safety = _mapping(candidate.get("safety"))
        if safety.get("source_contamination_check") not in {"pending", "pass"}:
            errors.append(
                _issue(
                    "invalid_source_contamination_check",
                    "source_contamination_check must be pending or pass",
                    f"{path}.safety.source_contamination_check",
                )
            )
        similarity_score = safety.get("similarity_score")
        if isinstance(similarity_score, (int, float)) and similarity_score >= 0.8:
            errors.append(_issue("similarity_score_failed", "similarity_score >= 0.80 must fail", f"{path}.safety.similarity_score"))
        if safety.get("human_review_status") not in {"pending", "approved", "rejected"}:
            errors.append(
                _issue("invalid_human_review_status", "human_review_status must be pending/approved/rejected", f"{path}.safety.human_review_status")
            )
        target = _mapping(candidate.get("target"))
        if target.get("promote_to") != "none":
            errors.append(_issue("promotion_not_allowed", "candidate promote_to must remain none in v1.3-3", f"{path}.target.promote_to"))

        _reject_forbidden_recipe_fields(candidate, path, errors)


def _validate_quality_gates(payload: Mapping[str, Any], path: Path, errors: list[dict[str, str]]) -> None:
    gate_errors = payload.get("errors")
    if payload.get("status") != "passed" or bool(gate_errors):
        errors.append(_issue("quality_gate_failed", "quality gates must pass with no errors", str(path)))


def _reject_forbidden_atom_fields(value: Any, path: str, errors: list[dict[str, str]]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_ATOM_TEXT_FIELDS:
                errors.append(_issue("atom_excerpt_saved", f"chapter atom must not persist text field {key}", child_path))
            _reject_forbidden_atom_fields(child, child_path, errors)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            _reject_forbidden_atom_fields(child, f"{path}[{idx}]", errors)


def _reject_forbidden_recipe_fields(value: Any, path: str, errors: list[dict[str, str]]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_RECIPE_TEXT_FIELDS:
                errors.append(_issue("recipe_forbidden_field_saved", f"recipe must not persist or masquerade as {key}", child_path))
            _reject_forbidden_recipe_fields(child, child_path, errors)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            _reject_forbidden_recipe_fields(child, f"{path}[{idx}]", errors)


def _is_within(root: Path, path: Path) -> bool:
    try:
        candidate = path if path.is_absolute() else Path.cwd() / path
        root_abs = root if root.is_absolute() else Path.cwd() / root
        candidate.resolve().relative_to(root_abs.resolve())
        return True
    except ValueError:
        return False


def _recall_sources_include_book_analysis(value: Mapping[str, Any]) -> bool:
    sources = value.get("recall_sources", [])
    if not isinstance(sources, list):
        return False
    for item in sources:
        path_value = item.get("path") if isinstance(item, Mapping) else item
        if isinstance(path_value, str) and ".ops/book_analysis" in path_value:
            return True
    return False


def _recall_forbidden_excludes_book_analysis(value: Mapping[str, Any]) -> bool:
    forbidden = value.get("recall_forbidden_paths", [])
    if not isinstance(forbidden, list):
        return False
    return any(isinstance(item, str) and item.startswith(".ops/book_analysis") for item in forbidden)


def _load_recall_config(repo_root: str | Path | None) -> Mapping[str, Any] | None:
    if repo_root is None:
        return None
    path = Path(repo_root) / "foundation" / "rag" / "recall_config.yaml"
    if not path.exists():
        return None
    import yaml

    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, Mapping) else {}
