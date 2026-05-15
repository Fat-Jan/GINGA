"""Focused tests for A-F asset-backed capability providers.

The shared ``test_asset_capability_providers.py`` file is also being used by
H/R provider work, so these A-F assertions live separately to avoid crossing
worker ownership.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from ginga_platform.orchestrator.runner.dsl_parser import Step, parse_workflow
from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.runner.step_dispatch import dispatch_step


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKFLOW_PATH = _REPO_ROOT / "ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml"
_A_F_STEPS = (
    "A_brainstorm",
    "B_premise_lock",
    "C_world_build",
    "D_character_seed",
    "E_outline",
    "F_state_init",
)


class AssetCapabilityProviderAFTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_root = Path(self._tmp.name) / "state"
        self.workflow = parse_workflow(_WORKFLOW_PATH)

    def test_workflow_a_f_contract_matches_expected_capabilities_and_paths(self) -> None:
        expected: dict[str, dict[str, list[str] | str]] = {
            "A_brainstorm": {
                "uses_capability": "base-methodology-creative-brainstorm",
                "state_reads": [],
                "state_writes": ["retrieved.brainstorm"],
            },
            "B_premise_lock": {
                "uses_capability": "base-template-story-dna",
                "state_reads": ["retrieved.brainstorm"],
                "state_writes": ["locked.STORY_DNA"],
            },
            "C_world_build": {
                "uses_capability": "base-template-worldview",
                "state_reads": ["locked.STORY_DNA"],
                "state_writes": ["locked.GENRE_LOCKED", "locked.WORLD"],
            },
            "D_character_seed": {
                "uses_capability": "base-template-protagonist",
                "state_reads": ["locked.STORY_DNA", "locked.WORLD"],
                "state_writes": ["entity_runtime.CHARACTER_STATE"],
            },
            "E_outline": {
                "uses_capability": "base-template-outline",
                "state_reads": [
                    "locked.STORY_DNA",
                    "locked.WORLD",
                    "entity_runtime.CHARACTER_STATE",
                ],
                "state_writes": ["locked.PLOT_ARCHITECTURE"],
            },
            "F_state_init": {
                "uses_capability": "base-template-state-init",
                "state_reads": ["locked.*", "entity_runtime.CHARACTER_STATE"],
                "state_writes": [
                    "entity_runtime.RESOURCE_LEDGER",
                    "entity_runtime.FORESHADOW_STATE",
                    "entity_runtime.GLOBAL_SUMMARY",
                    "workspace.task_plan",
                    "workspace.findings",
                    "workspace.progress",
                ],
            },
        }

        for step_id, contract in expected.items():
            step = self.workflow.find(step_id)
            self.assertIsNotNone(step, step_id)
            assert step is not None
            self.assertEqual(step.uses_capability, contract["uses_capability"])
            self.assertEqual(step.uses_skill, None)
            self.assertEqual(step.state_reads, contract["state_reads"])
            self.assertEqual(step.state_writes, contract["state_writes"])

    def test_a_brainstorm_reads_asset_manifest_and_is_input_sensitive(self) -> None:
        from ginga_platform.orchestrator.registry.asset_providers import (
            build_asset_capability_providers,
        )

        providers = build_asset_capability_providers()
        brainstorm = providers["base-methodology-creative-brainstorm"]

        out_a = brainstorm({}, {"params": {"topic": "海底赛博修真", "premise": "潜水员在海沟发现会诵经的AI鲸骨"}})
        out_b = brainstorm({}, {"params": {"topic": "宫廷权谋", "premise": "替身公主用账本掀翻摄政王"}})

        for out in (out_a, out_b):
            self.assertIn("result", out)
            self.assertIn("state_updates", out)
            self.assertIn("retrieved.brainstorm", out["state_updates"])
            payload = out["state_updates"]["retrieved.brainstorm"]
            self.assertEqual(payload["asset_ref"]["id"], "base-methodology-creative-brainstorm")
            self.assertTrue(
                payload["asset_ref"]["path"].endswith(".md")
                or payload["asset_ref"]["path"].endswith(".yaml"),
                payload["asset_ref"],
            )
            self.assertIn("seed_input", payload)
            self.assertIn("core_idea", payload)

        self.assertIn("海底赛博修真", out_a["state_updates"]["retrieved.brainstorm"]["seed_input"])
        self.assertIn("宫廷权谋", out_b["state_updates"]["retrieved.brainstorm"]["seed_input"])
        self.assertNotEqual(
            out_a["state_updates"]["retrieved.brainstorm"]["core_idea"],
            out_b["state_updates"]["retrieved.brainstorm"]["core_idea"],
        )

    def test_a_f_dispatch_uses_asset_backed_outputs_and_only_allowed_paths(self) -> None:
        from ginga_platform.orchestrator.registry.asset_providers import (
            build_asset_capability_providers,
        )

        state_io = StateIO("asset-provider-book", state_root=self.state_root)
        providers = build_asset_capability_providers()
        ctx = {
            "state_io": state_io,
            "book_id": "asset-provider-book",
            "params": {
                "topic": "海底赛博修真",
                "premise": "潜水员在海沟发现会诵经的AI鲸骨",
                "word_target": 180000,
            },
        }

        results = [
            dispatch_step(step, ctx, capability_registry=providers)
            for step in self._workflow_steps(_A_F_STEPS)
        ]

        for result in results:
            step = self.workflow.find(result.step_id)
            self.assertIsNotNone(step)
            assert step is not None
            self.assertEqual(result.used, f"capability:{step.uses_capability}")
            self.assertTrue(result.state_writes_applied, result.step_id)
            self.assertEqual(
                set(result.state_writes_applied),
                set(result.output["state_updates"]),
                f"{result.step_id} returned paths outside its whitelist",
            )
            self.assertAllowedByStep(step, result.output["state_updates"])

        self.assertEqual(
            state_io.read("retrieved.brainstorm.asset_ref.id"),
            "base-methodology-creative-brainstorm",
        )
        self.assertEqual(
            state_io.read("locked.STORY_DNA.asset_ref.id"),
            "base-template-story-dna",
        )
        self.assertEqual(
            state_io.read("locked.WORLD.asset_ref.id"),
            "base-template-worldview",
        )
        self.assertEqual(
            state_io.read("entity_runtime.CHARACTER_STATE.asset_ref.id"),
            "base-template-protagonist",
        )
        self.assertEqual(
            state_io.read("locked.PLOT_ARCHITECTURE.asset_ref.id"),
            "base-template-outline",
        )
        self.assertEqual(
            state_io.read("workspace.task_plan.asset_ref.id"),
            "base-template-state-init",
        )

        self.assertIn("海底赛博修真", state_io.read("locked.STORY_DNA.premise"))
        self.assertIn("AI鲸骨", state_io.read("locked.WORLD.power_system"))
        self.assertIn("海底赛博修真", state_io.read("workspace.progress.current_phase"))
        self.assertEqual(state_io.read("entity_runtime.RESOURCE_LEDGER.particles"), 0)
        self.assertGreaterEqual(len(state_io.read("entity_runtime.FORESHADOW_STATE.pool")), 1)

    def _workflow_steps(self, step_ids: tuple[str, ...]) -> list[Step]:
        steps: list[Step] = []
        for step_id in step_ids:
            step = self.workflow.find(step_id)
            self.assertIsNotNone(step, step_id)
            assert step is not None
            steps.append(step)
        return steps

    def assertAllowedByStep(self, step: Step, updates: Mapping[str, Any]) -> None:
        concrete = {path for path in step.state_writes if not path.endswith(".*")}
        wildcards = {path[:-2] for path in step.state_writes if path.endswith(".*")}
        for path in updates:
            allowed = path in concrete or any(path == root or path.startswith(root + ".") for root in wildcards)
            self.assertTrue(allowed, f"{step.id}: update path {path!r} not allowed by {step.state_writes}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
