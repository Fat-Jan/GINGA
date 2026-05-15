"""v1.8-3 Genm optional observability contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class GenmOptionalObservabilityTest(unittest.TestCase):
    def test_evidence_pack_exports_report_only_references_without_copying_full_text(self) -> None:
        from ginga_platform.orchestrator.genm_observability import export_jury_evidence_pack

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            evidence = root / "review_report.json"
            evidence.write_text(
                json.dumps(
                    {
                        "kind": "ReviewDeslopReport",
                        "status": "warn",
                        "summary": {"issue_count": 3},
                        "secret_full_text": "SENTINEL_FULL_TEXT_SHOULD_NOT_COPY",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            payload = export_jury_evidence_pack(
                run_id="pack-001",
                evidence_paths=[evidence],
                output_root=root / ".ops" / "jury" / "evidence_packs",
            )

            self.assertEqual(payload["mode"], "report_only")
            self.assertFalse(payload["writes_runtime_state"])
            self.assertFalse(payload["enters_creation_prompt"])
            self.assertEqual(payload["evidence_count"], 1)
            self.assertEqual(payload["evidence_refs"][0]["path"], str(evidence))
            self.assertNotIn("SENTINEL_FULL_TEXT_SHOULD_NOT_COPY", json.dumps(payload, ensure_ascii=False))
            self.assertTrue((root / ".ops" / "jury" / "evidence_packs" / "pack-001" / "evidence_pack.json").exists())

    def test_workflow_stage_observation_reads_workflow_without_running_it(self) -> None:
        from ginga_platform.orchestrator.genm_observability import export_workflow_stage_observation

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            workflow = root / "workflow.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: tiny",
                        "steps:",
                        "  - id: A",
                        "    uses_capability: cap-a",
                        "    state_reads: []",
                        "    state_writes: [locked.STORY_DNA]",
                        "  - id: B",
                        "    uses_skill: skill-router",
                        "    state_reads: [locked.STORY_DNA]",
                        "    state_writes: [workspace.chapter_text]",
                    ]
                ),
                encoding="utf-8",
            )

            payload = export_workflow_stage_observation(
                run_id="stage-001",
                workflow_path=workflow,
                output_root=root / ".ops" / "workflow_observability",
            )

            self.assertEqual(payload["mode"], "report_only")
            self.assertFalse(payload["runs_workflow"])
            self.assertFalse(payload["writes_runtime_state"])
            self.assertEqual(payload["stage_count"], 2)
            self.assertEqual(payload["stages"][0]["id"], "A")
            self.assertEqual(payload["stages"][1]["uses_skill"], "skill-router")

    def test_migration_audit_reports_forbidden_sources_without_mutating_targets(self) -> None:
        from ginga_platform.orchestrator.genm_observability import export_migration_audit

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            clean = root / "foundation" / "assets" / "methodology" / "clean.md"
            clean.parent.mkdir(parents=True)
            clean.write_text("clean asset\n", encoding="utf-8")
            polluted = root / ".ops" / "book_analysis" / "run-1" / "source.md"
            polluted.parent.mkdir(parents=True)
            polluted.write_text("polluted source\n", encoding="utf-8")

            payload = export_migration_audit(
                run_id="audit-001",
                scan_roots=[root / "foundation", root / ".ops"],
                output_root=root / ".ops" / "migration_audit",
                repo_root=root,
            )

            self.assertEqual(payload["mode"], "report_only")
            self.assertFalse(payload["auto_migrate"])
            self.assertFalse(payload["writes_runtime_state"])
            self.assertGreaterEqual(payload["scanned_file_count"], 2)
            self.assertIn(".ops/book_analysis/run-1/source.md", payload["forbidden_source_hits"])
            self.assertEqual(clean.read_text(encoding="utf-8"), "clean asset\n")

    def test_cli_exports_workflow_stage_observation(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            workflow = root / "workflow.yaml"
            workflow.write_text("name: tiny\nsteps:\n  - id: A\n    state_reads: []\n    state_writes: []\n", encoding="utf-8")

            code = main(
                [
                    "observability",
                    "workflow-stages",
                    "--run-id",
                    "cli-stage",
                    "--workflow-path",
                    str(workflow),
                    "--output-root",
                    str(root / ".ops" / "workflow_observability"),
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue((root / ".ops" / "workflow_observability" / "cli-stage" / "workflow_stage_report.json").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
