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
