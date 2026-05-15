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
