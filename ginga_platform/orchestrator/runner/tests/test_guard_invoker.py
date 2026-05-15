"""Tests for meta guard invoker contract compatibility."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ginga_platform.orchestrator.meta_integration.guard_invoker import invoke_guards
from ginga_platform.orchestrator.runner.state_io import StateIO


class GuardInvokerTest(unittest.TestCase):
    def test_repo_structured_guard_yaml_is_fail_open_until_rule_engine_supports_it(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = StateIO("guard-book", state_root=Path(d))
            passed = invoke_guards(
                ["latest-text-priority"],
                {"state_io": sio, "step_id": "G_chapter_draft"},
            )

            self.assertEqual(passed, ["latest-text-priority"])
            self.assertTrue(
                any("structured guard trigger not evaluated" in entry.get("msg", "") for entry in sio.audit_log),
                sio.audit_log,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
