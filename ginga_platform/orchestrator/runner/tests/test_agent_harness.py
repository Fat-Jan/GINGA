"""Offline agent harness tests for P2-5.

The harness must exercise the public CLI shape without calling ask-llm:
init, single run, multi-chapter run, immersive run, and one failing path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml


class AgentHarnessTest(unittest.TestCase):
    def test_offline_harness_covers_cli_paths_and_error_exit_codes(self) -> None:
        from scripts.run_agent_harness import run_harness

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            json_output = root / "agent_harness.json"
            report_output = root / "agent_harness.md"

            result = run_harness(
                state_root=state_root,
                json_output=json_output,
                report_output=report_output,
            )

            self.assertTrue(result["passed"], result)
            cases = {case["name"]: case for case in result["cases"]}
            self.assertEqual(
                set(cases),
                {"init", "single_run", "multi_chapter", "immersive", "missing_state_error"},
            )

            self.assertEqual(cases["init"]["exit_code"], 0)
            self.assertEqual(cases["single_run"]["exit_code"], 0)
            self.assertEqual(cases["multi_chapter"]["exit_code"], 0)
            self.assertEqual(cases["immersive"]["exit_code"], 0)
            self.assertEqual(cases["missing_state_error"]["exit_code"], 1)

            for name in ("single_run", "multi_chapter", "immersive"):
                self.assertEqual(cases[name]["execution_mode"], "mock_harness")

            init_state = state_root / "harness-init"
            for domain in ("locked", "entity_runtime", "workspace", "retrieved", "audit_log"):
                self.assertTrue((init_state / f"{domain}.yaml").exists(), domain)

            single_state = state_root / "harness-single"
            self.assertTrue((single_state / "chapter_01.md").exists())
            single_audit = yaml.safe_load((single_state / "audit_log.yaml").read_text(encoding="utf-8"))
            entries = single_audit.get("entries", [])
            self.assertTrue(
                any(entry.get("payload", {}).get("artifact_type") == "chapter_text" for entry in entries),
                entries,
            )

            multi_chapters = sorted((state_root / "harness-multi").glob("chapter_*.md"))
            self.assertEqual([path.name for path in multi_chapters], ["chapter_01.md", "chapter_02.md"])

            immersive_chapters = sorted((state_root / "harness-immersive").glob("chapter_*.md"))
            self.assertEqual([path.name for path in immersive_chapters], ["chapter_01.md", "chapter_02.md"])

            self.assertTrue(json_output.exists())
            report_text = report_output.read_text(encoding="utf-8")
            self.assertIn("mock_harness", report_text)
            self.assertIn("does not prove production readiness", report_text)

    def test_cli_rejects_real_llm_batches_above_v17_upper_bound(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            init_code = cli_main(
                [
                    "init",
                    "policy-book",
                    "--topic",
                    "玄幻黑暗",
                    "--premise",
                    "policy test premise",
                    "--state-root",
                    str(state_root),
                ]
            )
            self.assertEqual(init_code, 0)

            run_code = cli_main(
                [
                    "run",
                    "policy-book",
                    "--chapters",
                    "8",
                    "--state-root",
                    str(state_root),
                ]
            )
            self.assertEqual(run_code, 1)
            self.assertEqual(list((state_root / "policy-book").glob("chapter_*.md")), [])

    def test_cli_immersive_defaults_to_recommended_five_chapter_batch(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            self.assertEqual(
                cli_main(
                    [
                        "init",
                        "default-immersive-book",
                        "--topic",
                        "玄幻黑暗",
                        "--premise",
                        "default batch policy premise",
                        "--state-root",
                        str(state_root),
                    ]
                ),
                0,
            )

            self.assertEqual(
                cli_main(
                    [
                        "run",
                        "default-immersive-book",
                        "--mock-llm",
                        "--immersive",
                        "--word-target",
                        "200",
                        "--state-root",
                        str(state_root),
                    ]
                ),
                0,
            )
            chapters = sorted((state_root / "default-immersive-book").glob("chapter_*.md"))
            self.assertEqual([path.name for path in chapters], [f"chapter_{idx:02d}.md" for idx in range(1, 6)])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
