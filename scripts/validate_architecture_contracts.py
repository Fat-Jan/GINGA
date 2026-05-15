#!/usr/bin/env python3
"""Validate workflow, skill contract, registry, and state path architecture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


WORKFLOW_PATH = Path("ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml")
SKILLS_DIR = Path("ginga_platform/skills")
SKILL_ROUTER_PATH = Path("ginga_platform/orchestrator/router/skill_router.py")
FOUNDATION_ASSETS_DIR = Path("foundation/assets")
RECALL_CONFIG_PATH = Path("foundation/rag/recall_config.yaml")
CURRENT_STATUS_PATH = Path("STATUS.md")
PLANNING_DOC_PATHS = (
    Path("AGENTS.md"),
    Path("STATUS.md"),
    Path("ROADMAP.md"),
    Path("notepad.md"),
    Path("ARCHITECTURE.md"),
)
P7_HISTORY_NOTICE_PATHS = (
    Path(".ops/p7-prompts/README.md"),
    Path(".ops/p7-handoff/README.md"),
)
CODE_STATE_WRITE_ALLOWLIST = {
    Path("ginga_platform/orchestrator/runner/state_io.py"),
    Path("ginga_platform/orchestrator/cli/locked_patch.py"),
}
STATE_DOMAIN_FILENAMES = {
    "locked.yaml",
    "entity_runtime.yaml",
    "workspace.yaml",
    "retrieved.yaml",
    "audit_log.yaml",
}

ALLOWED_STATE_TOPS = {
    "locked",
    "entity_runtime",
    "workspace",
    "retrieved",
    "audit_log",
    "chapter_text",
}
REQUIRED_CONTRACT_FIELDS = {
    "skill_id",
    "version",
    "inputs",
    "outputs",
    "state_updates",
    "priority",
    "forbidden_mutation",
    "adapter",
}
REQUIRED_RECALL_FORBIDDEN_PATHS = {
    "foundation/raw_ideas/**",
    "meta/checkers/**",
}
REQUIRED_STATUS_SNIPPETS = (
    "P2-7",
    "Platform runner 收敛",
    "RAG 残余观察",
)
STALE_NEXT_STEP_PHRASES = (
    "下一步主线转入 agent harness 补强",
    "下一步 agent harness",
    "下一步主线是 agent harness 补强",
    "下一步：主线做 agent harness 补强",
    "正在从「文档蒸馏」进入「agent harness 补强」",
)
P27_RUNNER_SNIPPETS = {
    Path("ginga_platform/orchestrator/cli/demo_pipeline.py"): (
        "_workflow_step_dispatch",
        "DarkFantasyAdapter",
        "SkillRouter",
        "dispatch_step",
    ),
    Path("ginga_platform/orchestrator/router/skill_router.py"): (
        "skills must be list or mapping",
        'item.get("contract_path") or item.get("contract")',
    ),
    Path("ginga_platform/orchestrator/runner/dsl_parser.py"): (
        "return bool(self.uses_capability) and not self.uses_skill",
    ),
    Path("ginga_platform/orchestrator/runner/step_dispatch.py"): (
        'if path == "audit_log"',
    ),
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def split_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        return None
    return data


def add_error(report: dict[str, Any], path: Path, field: str, message: str) -> None:
    report["errors"].append(f"{path}: {field}: {message}")


def add_warning(report: dict[str, Any], path: Path, field: str, message: str) -> None:
    report["warnings"].append(f"{path}: {field}: {message}")


def add_check(report: dict[str, Any], name: str, ok: bool, detail: str) -> None:
    report["checks"].append(
        {
            "name": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        }
    )


def allowed_state_path(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    top = path_value.split(".", 1)[0]
    return top in ALLOWED_STATE_TOPS


def collect_asset_ids(repo_root: Path, report: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    assets_root = repo_root / FOUNDATION_ASSETS_DIR
    if not assets_root.exists():
        add_error(report, FOUNDATION_ASSETS_DIR, "path", "foundation assets directory missing")
        return ids

    for path in sorted(assets_root.rglob("*.md")):
        try:
            frontmatter = split_frontmatter(path)
        except Exception as exc:  # noqa: BLE001 - lint should keep scanning.
            add_warning(report, path.relative_to(repo_root), "frontmatter", f"cannot parse: {exc}")
            continue
        if frontmatter and isinstance(frontmatter.get("id"), str):
            ids.add(frontmatter["id"])

    add_check(report, "foundation asset ids", True, f"found {len(ids)} frontmatter id(s)")
    return ids


def collect_registry_capability_ids(report: dict[str, Any]) -> set[str]:
    try:
        from ginga_platform.orchestrator.registry.capability_registry import (
            CapabilityRegistry,
        )
    except Exception as exc:  # noqa: BLE001 - fallback to asset ids is intentional.
        add_warning(
            report,
            Path("ginga_platform/orchestrator/registry/capability_registry.py"),
            "import",
            f"cannot import CapabilityRegistry; using foundation asset ids only: {exc}",
        )
        return set()

    try:
        ids = set(CapabilityRegistry.from_defaults().list_capabilities())
    except Exception as exc:  # noqa: BLE001 - fallback to asset ids is intentional.
        add_warning(
            report,
            Path("ginga_platform/orchestrator/registry/capability_registry.py"),
            "from_defaults",
            f"cannot list default capabilities; using foundation asset ids only: {exc}",
        )
        return set()

    add_check(report, "capability registry", True, f"found {len(ids)} default capability id(s)")
    return ids


def validate_workflow(repo_root: Path, report: dict[str, Any]) -> None:
    path = repo_root / WORKFLOW_PATH
    try:
        workflow = load_yaml(path)
    except Exception as exc:  # noqa: BLE001 - user needs location, not traceback.
        add_error(report, WORKFLOW_PATH, "yaml", f"cannot load workflow: {exc}")
        add_check(report, "workflow loads", False, "workflow YAML did not load")
        return

    if not isinstance(workflow, dict):
        add_error(report, WORKFLOW_PATH, "root", "workflow YAML must be a mapping")
        add_check(report, "workflow loads", False, "workflow root is not a mapping")
        return

    steps = workflow.get("steps")
    if not isinstance(steps, list):
        add_error(report, WORKFLOW_PATH, "steps", "must be a list")
        add_check(report, "workflow steps", False, "steps is not a list")
        return
    add_check(report, "workflow steps", True, f"loaded {len(steps)} step(s)")

    known_capabilities = collect_registry_capability_ids(report) | collect_asset_ids(repo_root, report)

    for index, step in enumerate(steps):
        field_prefix = f"steps[{index}]"
        if not isinstance(step, dict):
            add_error(report, WORKFLOW_PATH, field_prefix, "step must be a mapping")
            continue

        step_id = step.get("id")
        step_label = str(step_id) if isinstance(step_id, str) and step_id else f"index {index}"
        step_field = f"steps[{index}]({step_label})"
        if not isinstance(step_id, str) or not step_id:
            add_error(report, WORKFLOW_PATH, f"{field_prefix}.id", "missing required step id")

        uses_capability = step.get("uses_capability")
        uses_skill = step.get("uses_skill")
        if not uses_capability and not uses_skill:
            add_warning(
                report,
                WORKFLOW_PATH,
                step_field,
                "missing uses_capability/uses_skill; allowed only for pure state steps",
            )

        if uses_capability:
            if not isinstance(uses_capability, str):
                add_error(report, WORKFLOW_PATH, f"{step_field}.uses_capability", "must be a string id")
            elif uses_capability not in known_capabilities:
                add_error(
                    report,
                    WORKFLOW_PATH,
                    f"{step_field}.uses_capability",
                    f"{uses_capability!r} not found in CapabilityRegistry.from_defaults() or foundation/assets frontmatter id",
                )

        if uses_skill == "skill-router" and not (repo_root / SKILL_ROUTER_PATH).exists():
            add_error(
                report,
                WORKFLOW_PATH,
                f"{step_field}.uses_skill",
                f"skill-router requires {SKILL_ROUTER_PATH}",
            )

        for state_field in ("state_reads", "state_writes"):
            values = step.get(state_field, [])
            if values is None:
                values = []
            if not isinstance(values, list):
                add_error(report, WORKFLOW_PATH, f"{step_field}.{state_field}", "must be a list")
                continue
            for item in values:
                item_field = f"{step_field}.{state_field}"
                if not allowed_state_path(item):
                    add_error(
                        report,
                        WORKFLOW_PATH,
                        item_field,
                        f"{item!r} has invalid top-level state path; allowed: {sorted(ALLOWED_STATE_TOPS)}",
                    )
                elif item == "chapter_text":
                    add_warning(
                        report,
                        WORKFLOW_PATH,
                        item_field,
                        "bare chapter_text is allowed for now; prefer workspace.chapter_text in future workflow revisions",
                    )

    add_check(report, "skill-router file", (repo_root / SKILL_ROUTER_PATH).exists(), str(SKILL_ROUTER_PATH))


def validate_skill_contracts(repo_root: Path, report: dict[str, Any]) -> None:
    skills_root = repo_root / SKILLS_DIR
    contract_paths = sorted(path for path in skills_root.glob("*/contract.yaml") if path.is_file())
    if not contract_paths:
        add_error(report, SKILLS_DIR, "contract.yaml", "no skill contracts found")
        add_check(report, "skill contracts", False, "found 0 contract(s)")
        return

    for path in contract_paths:
        rel_path = path.relative_to(repo_root)
        try:
            contract = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            add_error(report, rel_path, "yaml", f"cannot load contract: {exc}")
            continue
        if not isinstance(contract, dict):
            add_error(report, rel_path, "root", "contract must be a mapping")
            continue

        for field in sorted(REQUIRED_CONTRACT_FIELDS):
            if field not in contract:
                add_error(report, rel_path, field, "missing required field")

        forbidden_mutation = contract.get("forbidden_mutation")
        if not forbidden_mutation:
            add_error(report, rel_path, "forbidden_mutation", "must not be empty")

    add_check(report, "skill contracts", True, f"found {len(contract_paths)} contract(s)")


def validate_recall_config(repo_root: Path, report: dict[str, Any]) -> None:
    path = repo_root / RECALL_CONFIG_PATH
    try:
        config = load_yaml(path)
    except Exception as exc:  # noqa: BLE001
        add_error(report, RECALL_CONFIG_PATH, "yaml", f"cannot load recall config: {exc}")
        add_check(report, "recall config", False, "recall YAML did not load")
        return

    if not isinstance(config, dict):
        add_error(report, RECALL_CONFIG_PATH, "root", "recall config must be a mapping")
        add_check(report, "recall config", False, "root is not a mapping")
        return

    forbidden_paths = config.get("recall_forbidden_paths")
    if not isinstance(forbidden_paths, list):
        add_error(report, RECALL_CONFIG_PATH, "recall_forbidden_paths", "must be a list")
        add_check(report, "recall forbidden paths", False, "field is not a list")
        return

    missing = sorted(REQUIRED_RECALL_FORBIDDEN_PATHS - set(forbidden_paths))
    if missing:
        add_error(
            report,
            RECALL_CONFIG_PATH,
            "recall_forbidden_paths",
            f"missing required forbidden path(s): {missing}",
        )
    add_check(report, "recall forbidden paths", not missing, f"contains {len(forbidden_paths)} path(s)")


def validate_state_write_boundaries(repo_root: Path, report: dict[str, Any]) -> None:
    """Ensure runtime_state YAML writes stay behind StateIO or locked patch flow."""
    suspicious: list[str] = []
    for base in ("ginga_platform", "scripts"):
        root = repo_root / base
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(repo_root)
            if rel in CODE_STATE_WRITE_ALLOWLIST:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for lineno, line in enumerate(lines, start=1):
                writes_text = ".write_text(" in line or ".open(" in line or "open(" in line
                writes_yaml = "yaml.safe_dump" in line or "yaml.dump" in line
                names_state_domain = any(name in line for name in STATE_DOMAIN_FILENAMES)
                names_runtime_state = "foundation/runtime_state" in line or "runtime_state/" in line
                if (writes_text or writes_yaml) and (names_state_domain or names_runtime_state):
                    suspicious.append(f"{rel}:{lineno}")

    unique = sorted(set(suspicious))
    if unique:
        add_error(
            report,
            Path("ginga_platform"),
            "StateIO boundary",
            f"possible direct runtime_state YAML write outside StateIO: {unique}",
        )
    add_check(
        report,
        "StateIO write boundary",
        not unique,
        "runtime_state YAML writes are limited to StateIO / locked patch flow",
    )


def validate_current_planning_hygiene(repo_root: Path, report: dict[str, Any]) -> None:
    """Keep current planning docs aligned with STATUS.md."""
    error_count_before = len(report["errors"])

    status_path = repo_root / CURRENT_STATUS_PATH
    try:
        status_text = status_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        status_text = ""
        add_error(report, CURRENT_STATUS_PATH, "current status", "STATUS.md missing")

    for snippet in REQUIRED_STATUS_SNIPPETS:
        if snippet not in status_text:
            add_error(
                report,
                CURRENT_STATUS_PATH,
                "current status",
                f"missing current planning marker: {snippet}",
            )

    for rel_path in PLANNING_DOC_PATHS:
        path = repo_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            add_error(report, rel_path, "planning hygiene", "required planning doc missing")
            continue
        for phrase in STALE_NEXT_STEP_PHRASES:
            if phrase in text:
                add_error(
                    report,
                    rel_path,
                    "stale next-step wording",
                    f"replace stale phrase with P2-7 Platform runner 收敛: {phrase}",
                )

    for rel_path in P7_HISTORY_NOTICE_PATHS:
        path = repo_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            add_error(
                report,
                rel_path,
                "historical notice",
                "missing README.md that marks this directory as historical, not current todo",
            )
            continue
        missing = [marker for marker in ("历史", "STATUS.md") if marker not in text]
        if missing:
            add_error(
                report,
                rel_path,
                "historical notice",
                f"README.md must mention {missing} so old [ ] items are not read as current todo",
            )

    add_check(
        report,
        "current planning hygiene",
        len(report["errors"]) == error_count_before,
        "STATUS.md next step, stale doc wording, and .ops/p7 history notices are aligned",
    )


def validate_platform_runner_convergence(repo_root: Path, report: dict[str, Any]) -> None:
    """Check that the P2-7A runner convergence wiring remains present."""
    missing: list[str] = []
    for rel_path, snippets in P27_RUNNER_SNIPPETS.items():
        path = repo_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            add_error(report, rel_path, "P2-7 runner convergence", "required source file missing")
            continue
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{rel_path}: {snippet}")

    if missing:
        add_error(
            report,
            Path("ginga_platform/orchestrator"),
            "P2-7 runner convergence",
            f"missing required wiring snippet(s): {missing}",
        )
    add_check(
        report,
        "P2-7 runner convergence",
        not missing,
        "single-run path keeps workflow DSL, skill-router, adapter, and StateIO dispatch wiring",
    )


def validate_repo(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or Path.cwd()).resolve()
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    report: dict[str, Any] = {
        "status": "PASS",
        "repo_root": str(root),
        "checks": [],
        "warnings": [],
        "errors": [],
    }

    validate_workflow(root, report)
    validate_skill_contracts(root, report)
    validate_recall_config(root, report)
    validate_state_write_boundaries(root, report)
    validate_current_planning_hygiene(root, report)
    validate_platform_runner_convergence(root, report)
    report["status"] = "FAIL" if report["errors"] else "PASS"
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"{report['status']}: architecture contracts")
    for check in report["checks"]:
        print(f"{check['status']}: {check['name']} - {check['detail']}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_path", help="Write structured JSON report to path")
    args = parser.parse_args(argv)

    report = validate_repo(Path.cwd())

    if args.json_path:
        json_path = Path(args.json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print_report(report)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
