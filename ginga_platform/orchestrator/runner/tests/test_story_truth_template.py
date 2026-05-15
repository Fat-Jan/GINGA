"""Tests for the Story Truth Template schema and validator CLI."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import validate_story_truth_template as storytruth


def _valid_template() -> dict[str, object]:
    return {
        "$schema": "ginga/foundation/v1",
        "asset_type": "story_truth_template",
        "description": "Layered truth template for one story project.",
        "project_contract": {
            "truth_source": "foundation/assets/story/sample/project_contract.yaml",
            "fields": ["positioning", "target_reader", "payoff_promise"],
        },
        "genre_contract": {
            "truth_source": "foundation/assets/genre_profile/dark_fantasy.yaml",
            "core_expectations": ["pressure", "costly_power"],
            "extension_slots": {"xianxia": ["realm_ladder", "breakthrough_cost"]},
        },
        "plot_architecture": {
            "truth_source": "foundation/assets/story/sample/plot_architecture.yaml",
            "fields": ["acts", "pivot_points", "conflict_escalation"],
        },
        "cast_contract": {
            "truth_source": "foundation/assets/story/sample/cast_contract.yaml",
            "fields": ["protagonist", "antagonists", "factions", "relationship_network"],
        },
        "world_contract": {
            "truth_source": "foundation/assets/story/sample/world_contract.yaml",
            "fields": ["geography", "history", "culture", "laws", "economy"],
        },
        "system_contracts": {
            "truth_source": "foundation/assets/story/sample/system_contracts.yaml",
            "fields": ["power_system", "resource_rules", "forbidden_changes"],
        },
        "payoff_ledger": {
            "truth_source": "foundation/runtime_state/sample/entity_runtime.yaml",
            "fields": ["payoff_id", "setup", "reader_reward", "release_chapter"],
        },
        "hook_ledger": {
            "truth_source": "foundation/runtime_state/sample/entity_runtime.yaml",
            "fields": ["hook_id", "chapter", "promise", "status"],
        },
        "foreshadow_ledger": {
            "truth_source": "foundation/runtime_state/sample/entity_runtime.yaml",
            "fields": ["foreshadow_id", "plant_chapter", "reveal_chapter", "status"],
        },
        "chapter_input_bundle": {
            "truth_source": "foundation/runtime_state/sample/workspace.yaml",
            "fields": ["chapter_goal", "scene_outline", "active_cast", "risk_notes"],
        },
        "runtime_state_projection": {
            "truth_source": "foundation/runtime_state/sample/",
            "fields": ["locked", "entity_runtime", "workspace", "audit_log"],
        },
        "style_contract": {
            "truth_source": "foundation/assets/story/sample/style_contract.yaml",
            "fields": ["narrative_pov", "dialogue_style", "forbidden_tone"],
        },
        "candidate_promotion_gate": {
            "truth_source": ".ops/governance/candidate_truth_gate.md",
            "required_evidence": [
                "operator_acceptance",
                "schema_validation",
                "source_contamination_check",
                "StateIO_or_validator_entrypoint",
                "audit_evidence",
            ],
        },
    }


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class StoryTruthTemplateValidatorTest(unittest.TestCase):
    def test_valid_template_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, _valid_template())

            report = storytruth.validate_file(path)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["errors"], [])

    def test_missing_required_layer_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = _valid_template()
            payload.pop("plot_architecture")
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, payload)

            report = storytruth.validate_file(path)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("plot_architecture" in error for error in report["errors"]))

    def test_genre_extension_slot_may_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = _valid_template()
            genre_contract = payload["genre_contract"]
            assert isinstance(genre_contract, dict)
            genre_contract["extension_slots"] = {
                "rule_horror": {
                    "rulebook_fields": ["rule", "violation_cost", "loophole"],
                    "risk_controls": ["no_free_rule_rewrite"],
                }
            }
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, payload)

            report = storytruth.validate_file(path)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["errors"], [])

    def test_candidate_or_report_truth_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = _valid_template()
            project_contract = payload["project_contract"]
            assert isinstance(project_contract, dict)
            project_contract["truth_source"] = ".ops/reports/story_truth_template_source_audit.md"
            genre_contract = payload["genre_contract"]
            assert isinstance(genre_contract, dict)
            genre_contract["truth_source"] = ".ops/book_analysis/run-001/trope_recipe_candidate.yaml"
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, payload)

            report = storytruth.validate_file(path)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("report-only" in error for error in report["errors"]))
        self.assertTrue(any(".ops/book_analysis" in error for error in report["errors"]))

    def test_candidate_promotion_gate_requires_all_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = _valid_template()
            gate = payload["candidate_promotion_gate"]
            assert isinstance(gate, dict)
            gate["required_evidence"] = ["operator_acceptance", "schema_validation"]
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, payload)

            report = storytruth.validate_file(path)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("source_contamination_check" in error for error in report["errors"]))
        self.assertTrue(any("audit_evidence" in error for error in report["errors"]))

    def test_cli_returns_nonzero_for_invalid_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "story_truth_template.yaml"
            _write_yaml(path, {"asset_type": "story_truth_template"})

            code = storytruth.main([str(path)])

        self.assertEqual(code, 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
