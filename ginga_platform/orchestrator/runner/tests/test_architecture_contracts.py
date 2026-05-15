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
