"""Tests for scripts.validate_architecture_contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_architecture_contracts as archlint


class ArchitectureContractsTest(unittest.TestCase):
    def test_validate_repo_returns_report_shape(self) -> None:
        report = archlint.validate_repo(Path(__file__).parents[4])

        self.assertEqual(report["status"], "PASS")
        self.assertIsInstance(report["checks"], list)
        self.assertIsInstance(report["warnings"], list)
        self.assertIsInstance(report["errors"], list)
        self.assertEqual(report["warnings"], [])
        check_names = {check["name"] for check in report["checks"]}
        self.assertIn("current planning hygiene", check_names)
        self.assertIn("P2-7 runner convergence", check_names)
        self.assertIn("v1.8-0 Model Topology observation boundary", check_names)
        self.assertIn("v1.8-1 Candidate Truth Gate wording", check_names)
        self.assertIn("v1.8-3 Genm optional observability boundary", check_names)
        self.assertIn("v2.0 Harness Map and v2.1 Harness self-check", check_names)

    def test_harness_contracts_require_map_and_self_check_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".ops/harness").mkdir(parents=True)
            (repo_root / "scripts").mkdir(parents=True)
            (repo_root / "AGENTS.md").write_text(
                "\n".join(
                    [
                        "# Agent 入口说明",
                        "Harness Engineering",
                        ".ops/validation/**",
                        ".ops/reports/**",
                        "StateIO",
                        "真实 LLM",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / ".ops/harness/README.md").write_text(
                "# Harness Map\n\nSTATUS.md\nscripts/verify_all.py\n",
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_harness_contracts(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "v2.0 Harness Map and v2.1 Harness self-check")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any("scripts/validate_harness_contracts.py" in error for error in report["errors"]))
            self.assertTrue(any("task_type" in error for error in report["errors"]))
            self.assertTrue(any("real_llm_policy" in error for error in report["errors"]))

    def test_current_planning_hygiene_detects_stale_next_step_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".ops/p7-prompts").mkdir(parents=True)
            (repo_root / ".ops/p7-handoff").mkdir(parents=True)
            (repo_root / "STATUS.md").write_text(
                "## 下一步\n\nP2-7 Platform runner 收敛。\n\nRAG 残余观察。\n",
                encoding="utf-8",
            )
            (repo_root / "ROADMAP.md").write_text(
                "下一步主线转入 agent harness 补强。\n",
                encoding="utf-8",
            )
            (repo_root / "notepad.md").write_text("下一步：主线做 agent harness 补强。\n", encoding="utf-8")
            (repo_root / "AGENTS.md").write_text(
                "正在从「文档蒸馏」进入「agent harness 补强」。\n",
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_current_planning_hygiene(repo_root, report)

            self.assertEqual(
                [check["name"] for check in report["checks"]],
                ["current planning hygiene"],
            )
            self.assertGreaterEqual(len(report["errors"]), 3)
            self.assertTrue(any("stale next-step wording" in error for error in report["errors"]))
            self.assertTrue(any(".ops/p7-prompts/README.md" in error for error in report["errors"]))
            self.assertTrue(any(".ops/p7-handoff/README.md" in error for error in report["errors"]))

    def test_recall_config_requires_v13_pollution_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_path = repo_root / "foundation/rag/recall_config.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "recall_forbidden_paths:",
                        "  - foundation/raw_ideas/**",
                        "  - foundation/runtime_state/**",
                        "  - meta/guards/**",
                        "  - meta/checkers/**",
                        "  - meta/constitution.yaml",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_recall_config(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "recall forbidden paths")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any(".ops/book_analysis/**" in error for error in report["errors"]))
            self.assertTrue(any(".ops/market_research/**" in error for error in report["errors"]))
            self.assertTrue(any(".ops/external_sources/**" in error for error in report["errors"]))

    def test_book_analysis_boundaries_require_docs_and_manifest_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".ops/book_analysis").mkdir(parents=True)

            (repo_root / ".ops/book_analysis/contamination_check_rules.md").write_text(
                "\n".join(
                    [
                        ".ops/book_analysis/<run_id>/",
                        "pollution_source: true",
                        "[SOURCE_TROPE]",
                        "StateIO",
                        "raw_ideas",
                        "默认 RAG",
                        "scan / split / manifest / validator / report",
                        "Sidecar RAG",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (repo_root / ".ops/book_analysis/p0_mvp_boundary.md").write_text(
                ".ops/book_analysis/<run_id>/\npollution_source: true\n[SOURCE_TROPE]\nStateIO\n",
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_book_analysis_boundaries(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "v1.3-0 book_analysis boundaries")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any("p0_mvp_boundary.md" in error for error in report["errors"]))
            self.assertTrue(any("source_manifest.schema.yaml" in error for error in report["errors"]))

    def test_model_topology_boundary_rejects_runtime_takeover(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module = repo_root / "ginga_platform/orchestrator/model_topology.py"
            module.parent.mkdir(parents=True)
            module.write_text(
                "\n".join(
                    [
                        'DEFAULT_OUTPUT_ROOT = Path(".ops/model_topology")',
                        'OUTPUT_BOUNDARY = ".ops/model_topology/<run_id>/"',
                        '"mode": "report_only"',
                        '"runtime_takeover": True',
                        '"stateio_mutation": False',
                        '"live probe disabled; pass --probe-live"',
                    ]
                ),
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_model_topology_boundary(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "v1.8-0 Model Topology observation boundary")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any("runtime_takeover" in error for error in report["errors"]))

    def test_candidate_truth_gate_requires_core_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            doc = repo_root / ".ops/governance/candidate_truth_gate.md"
            doc.parent.mkdir(parents=True)
            doc.write_text(
                "\n".join(
                    [
                        "# Candidate Truth Gate",
                        "",
                        "candidate-only",
                        "report-only",
                        "truth",
                        "StateIO",
                    ]
                ),
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_candidate_truth_gate(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "v1.8-1 Candidate Truth Gate wording")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any("operator_accept" in error for error in report["errors"]))
            self.assertTrue(any("default RAG" in error for error in report["errors"]))

    def test_genm_observability_boundary_rejects_runtime_or_migration_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            module = repo_root / "ginga_platform/orchestrator/genm_observability.py"
            module.parent.mkdir(parents=True)
            module.write_text(
                "\n".join(
                    [
                        'DEFAULT_EVIDENCE_PACK_ROOT = Path(".ops/jury/evidence_packs")',
                        'DEFAULT_WORKFLOW_OBSERVABILITY_ROOT = Path(".ops/workflow_observability")',
                        'DEFAULT_MIGRATION_AUDIT_ROOT = Path(".ops/migration_audit")',
                        '"mode": "report_only"',
                        '"writes_runtime_state": False',
                        '"enters_creation_prompt": False',
                        '"default_rag_eligible": False',
                        '"runs_workflow": False',
                        '"auto_migrate": False',
                        "export_jury_evidence_pack",
                        "export_workflow_stage_observation",
                        "export_migration_audit",
                        "StateIO(",
                    ]
                ),
                encoding="utf-8",
            )

            report = {"checks": [], "warnings": [], "errors": []}
            archlint.validate_genm_observability_boundary(repo_root, report)

            self.assertEqual(report["checks"][0]["name"], "v1.8-3 Genm optional observability boundary")
            self.assertEqual(report["checks"][0]["status"], "FAIL")
            self.assertTrue(any("StateIO" in error for error in report["errors"]))

    def test_main_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "arch-report.json"
            exit_code = archlint.main(["--json", str(json_path)])

            self.assertEqual(exit_code, 0)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "PASS")
            self.assertIn("warnings", data)
            self.assertIn("errors", data)
            self.assertEqual(data["warnings"], [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
