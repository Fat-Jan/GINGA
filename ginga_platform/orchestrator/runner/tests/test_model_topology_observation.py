"""v1.8-0 model topology observation tests.

The observation path is report-only. It must not route runtime providers,
write StateIO, or call real LLMs unless explicitly asked by the caller.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class ModelTopologyObservationTest(unittest.TestCase):
    def test_observation_exports_report_only_matrix_without_live_probe(self) -> None:
        from ginga_platform.orchestrator.model_topology import export_model_topology_observation

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = export_model_topology_observation(
                run_id="v1-8-0-test",
                output_root=root / "model_topology",
            )

            self.assertEqual(result["mode"], "report_only")
            self.assertFalse(result["runtime_takeover"])
            self.assertEqual(result["output_boundary"], ".ops/model_topology/<run_id>/")
            self.assertTrue(result["role_matrix"])
            self.assertIn("prose_writer", {row["role"] for row in result["role_matrix"]})
            self.assertGreaterEqual(result["runtime_surface"]["capability_count"], 12)
            self.assertEqual(result["probe_summary"]["live_probe_enabled"], False)
            self.assertTrue(all(item["status"] == "not_run" for item in result["probe_results"]))

            output_dir = root / "model_topology" / "v1-8-0-test"
            self.assertTrue((output_dir / "model_topology_report.json").exists())
            readme = (output_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("Model Topology Observation", readme)
            self.assertIn("runtime_takeover: `False`", readme)
            self.assertIn("prose_writer", readme)

    def test_live_probe_uses_injected_runner_and_keeps_report_only_boundary(self) -> None:
        from ginga_platform.orchestrator.model_topology import export_model_topology_observation

        calls: list[tuple[str, str]] = []

        def fake_probe(alias: str, prompt: str) -> dict[str, object]:
            calls.append((alias, prompt))
            return {
                "ok": alias == "fast-cn",
                "latency_ms": 12 if alias == "fast-cn" else 35,
                "model": "fake-model",
                "error": "" if alias == "fast-cn" else "timeout",
            }

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = export_model_topology_observation(
                run_id="v1-8-0-live",
                output_root=root / "model_topology",
                probe_live=True,
                probe_targets=[
                    {"role": "prose_writer", "alias": "fast-cn"},
                    {"role": "critic", "alias": "slow-critic"},
                ],
                probe_runner=fake_probe,
            )

            self.assertEqual(len(calls), 2)
            self.assertFalse(result["runtime_takeover"])
            self.assertEqual(result["probe_summary"]["live_probe_enabled"], True)
            self.assertEqual(result["probe_summary"]["ok_count"], 1)
            statuses = {item["alias"]: item["status"] for item in result["probe_results"]}
            self.assertEqual(statuses["fast-cn"], "ok")
            self.assertEqual(statuses["slow-critic"], "failed")

            payload = json.loads(
                (root / "model_topology" / "v1-8-0-live" / "model_topology_report.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(payload["probe_summary"]["ok_count"], 1)

    def test_cli_exports_observation_report(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rc = main(
                [
                    "model-topology",
                    "observe",
                    "--run-id",
                    "cli-smoke",
                    "--output-root",
                    str(root / "model_topology"),
                ]
            )

            self.assertEqual(rc, 0)
            report = root / "model_topology" / "cli-smoke" / "model_topology_report.json"
            self.assertTrue(report.exists())
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "report_only")
            self.assertFalse(payload["probe_summary"]["live_probe_enabled"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
