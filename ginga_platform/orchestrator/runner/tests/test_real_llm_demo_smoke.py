"""P2-7C real LLM smoke boundary tests.

The smoke helper defaults to dry-run mode. Tests must not call ask-llm.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class RealLLMDemoSmokeTest(unittest.TestCase):
    def test_dry_run_records_scope_without_calling_real_llm(self) -> None:
        from scripts.run_real_llm_smoke import run_smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "state"
            json_output = root / "real_llm_demo.json"
            report_output = root / "real_llm_demo.md"

            payload = run_smoke(
                book_id="p2-7c-smoke-test",
                endpoint="久久",
                state_root=state_root,
                json_output=json_output,
                report_output=report_output,
                word_target=800,
                dry_run=True,
            )

            self.assertEqual(payload["execution_mode"], "real_llm_demo")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["endpoint"], "久久")
            self.assertIn("1 ask-llm call", payload["cost_risk"])
            self.assertIn("context_snapshot", payload)
            self.assertEqual(payload["context_snapshot"]["status"], "planned")
            self.assertIn("before_run", payload["context_snapshot"])
            self.assertIn("after_run", payload["context_snapshot"])
            self.assertIn("gap_report", payload)
            self.assertEqual(payload["gap_report"]["status"], "planned")
            self.assertTrue(payload["gap_report"]["open_gaps"])
            self.assertIn("residual_risk", payload)
            self.assertGreaterEqual(len(payload["residual_risk"]), 3)
            self.assertFalse((state_root / "p2-7c-smoke-test").exists())
            self.assertTrue(json_output.exists())
            report = report_output.read_text(encoding="utf-8")
            self.assertIn("P2-7C Real LLM Smoke Report", report)
            self.assertIn("dry_run: `True`", report)
            self.assertIn("## Context Snapshot", report)
            self.assertIn("## Gap Report", report)
            self.assertIn("## Residual Risk", report)
            self.assertIn("will_not_overwrite", report)

    def test_real_run_payload_summarizes_context_and_quality_gaps_without_calling_llm(self) -> None:
        from scripts import run_real_llm_smoke
        from scripts.run_real_llm_smoke import run_smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "state"
            book_id = "p2-7c-real-test"

            def fake_run(name: str, argv: list[str]) -> run_real_llm_smoke.CliRun:
                from ginga_platform.orchestrator.runner.state_io import StateIO

                state_io = StateIO(book_id, state_root=state_root)
                if name == "init":
                    state_io.apply(
                        {
                            "locked.STORY_DNA": {"premise": "血雾里的记忆债"},
                            "locked.GENRE_LOCKED": {"topic": ["玄幻黑暗"]},
                            "locked.WORLD": {"economy": "微粒为通货"},
                            "locked.PLOT_ARCHITECTURE": {"acts": [{"name": "觉醒"}]},
                            "entity_runtime.CHARACTER_STATE": {"protagonist": {"events": []}},
                            "entity_runtime.RESOURCE_LEDGER": {"particles": 0},
                            "entity_runtime.FORESHADOW_STATE": {"pool": []},
                            "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0},
                            "workspace.progress": "init",
                        },
                        source="test.fake_init",
                    )
                elif name == "run":
                    chapter = (
                        "| 写作自检 | 内容 |\n|---|---|\n"
                        "| 当前锚定 | 血雾/微粒 |\n| 预计微粒变化 | +80 |\n\n"
                        "# 第1章 · 血雾醒刃\n\n"
                        "无明在血雾里醒来，短刃贴着掌心吐出一线微粒。\n\n"
                        "追杀者袖口的符文与短刃同源，第一重天堑逼近。\n"
                        "<!-- foreshadow: id=fh-real planted_ch=1 expected_payoff=12 summary=追杀者符文同源 -->\n"
                    )
                    state_io.write_artifact(
                        "chapter_01.md",
                        chapter,
                        source="cli.run.G_chapter_draft.ch1",
                        artifact_type="chapter_text",
                        payload={"chapter_no": 1, "execution_mode": "real_llm_demo"},
                    )
                    state_io.apply(
                        {
                            "entity_runtime.CHARACTER_STATE": {"protagonist": {"events": [{"ch": 1, "type": "draft"}]}},
                            "entity_runtime.RESOURCE_LEDGER": {"particles": 80},
                            "entity_runtime.FORESHADOW_STATE": {"pool": [{"id": "fh-real", "status": "open"}]},
                            "entity_runtime.GLOBAL_SUMMARY": {"total_words": 58},
                        },
                        source="test.fake_run_rollup",
                    )
                return run_real_llm_smoke.CliRun(name=name, argv=argv, exit_code=0, stdout_tail=f"{name} ok", stderr_tail="")

            original = run_real_llm_smoke._actual_run
            run_real_llm_smoke._actual_run = fake_run
            try:
                payload = run_smoke(
                    book_id=book_id,
                    endpoint="久久",
                    state_root=state_root,
                    json_output=root / "real.json",
                    report_output=root / "real.md",
                    word_target=800,
                    dry_run=False,
                )
            finally:
                run_real_llm_smoke._actual_run = original

            self.assertTrue(payload["passed"], payload)
            before = payload["context_snapshot"]["before_run"]
            after = payload["context_snapshot"]["after_run"]
            self.assertEqual(before["status"], "missing")
            self.assertTrue(after["state_domains"]["locked"])
            self.assertEqual(after["chapter_artifact"]["execution_mode"], "real_llm_demo")
            self.assertGreater(after["chapter_artifact"]["chars"], 0)
            self.assertEqual(payload["gap_report"]["status"], "needs_review")
            gap_codes = [gap["code"] for gap in payload["gap_report"]["open_gaps"]]
            self.assertIn("production_quality_not_proven", gap_codes)
            self.assertIn("single_chapter_scope", gap_codes)
            report = (root / "real.md").read_text(encoding="utf-8")
            self.assertIn("chapter_chars", report)
            self.assertIn("production_quality_not_proven", report)

    def test_refresh_existing_rebuilds_report_from_prior_artifact_without_commands(self) -> None:
        from scripts.run_real_llm_smoke import refresh_existing_smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "state"
            book_id = "p2-7c-existing"
            from ginga_platform.orchestrator.runner.state_io import StateIO

            state_io = StateIO(book_id, state_root=state_root)
            state_io.apply(
                {
                    "locked.STORY_DNA": {"premise": "血雾"},
                    "locked.WORLD": {},
                    "locked.PLOT_ARCHITECTURE": {},
                    "entity_runtime.CHARACTER_STATE": {"protagonist": {"events": [{"ch": 1}]}},
                    "entity_runtime.RESOURCE_LEDGER": {"particles": 0},
                    "entity_runtime.FORESHADOW_STATE": {"pool": [{"id": "fh-existing"}]},
                    "entity_runtime.GLOBAL_SUMMARY": {"total_words": 12},
                },
                source="test.seed_existing",
            )
            state_io.write_artifact(
                "chapter_01.md",
                "# 第1章\n\n无明在血雾中醒来。\n<!-- foreshadow: id=fh-existing planted_ch=1 expected_payoff=8 summary=血雾回声 -->\n",
                source="cli.run.G_chapter_draft.ch1",
                artifact_type="chapter_text",
                payload={"chapter_no": 1, "execution_mode": "real_llm_demo"},
            )

            payload = refresh_existing_smoke(
                book_id=book_id,
                endpoint="久久",
                state_root=state_root,
                json_output=root / "existing.json",
                report_output=root / "existing.md",
            )

            self.assertTrue(payload["passed"], payload)
            self.assertFalse(payload["dry_run"])
            self.assertTrue(payload["refreshed_existing"])
            self.assertEqual(payload["commands"][0]["name"], "refresh_existing")
            self.assertEqual(payload["artifact_execution_mode"], "real_llm_demo")
            self.assertEqual(payload["context_snapshot"]["status"], "captured")
            self.assertIn("Context Snapshot", (root / "existing.md").read_text(encoding="utf-8"))

    def test_v23_real_llm_harness_dry_run_records_preflight_postflight_and_review_gate(self) -> None:
        from scripts.run_real_llm_harness import run_harness

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            payload = run_harness(
                profile="longform-small-batch",
                book_id="v23-dry-run",
                endpoint="久久",
                state_root=root / ".ops" / "real_llm_harness" / "state",
                json_output=root / ".ops" / "validation" / "real_llm_harness.json",
                report_output=root / ".ops" / "reports" / "real_llm_harness_report.md",
                review_output_root=root / ".ops" / "reviews",
                chapters=4,
                word_target=4000,
                batch_schedule="4",
                dry_run=True,
                review_gate=True,
            )

            self.assertEqual(payload["harness_version"], "v2.3")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["profile"], "longform-small-batch")
            self.assertEqual(payload["preflight"]["status"], "PASS")
            self.assertEqual(payload["postflight"]["status"], "planned")
            self.assertEqual(payload["review_gate"]["status"], "planned")
            self.assertEqual(payload["cost_boundary"]["estimated_real_llm_calls"], 12)
            self.assertEqual(payload["cost_boundary"]["max_real_llm_calls"], 12)
            self.assertEqual(payload["cost_boundary"]["max_generation_attempts_per_chapter"], 3)
            self.assertEqual(payload["cost_boundary"]["max_chapters"], 5)
            self.assertEqual(payload["cost_boundary"]["min_longform_word_target"], 3500)
            self.assertTrue(payload["isolation"]["state_root_under_ops"])
            self.assertIn(".ops/real_llm_harness", payload["isolation"]["state_root"])
            self.assertIn("review_gate", payload["gates"])
            self.assertTrue((root / ".ops" / "validation" / "real_llm_harness.json").exists())
            report = (root / ".ops" / "reports" / "real_llm_harness_report.md").read_text(encoding="utf-8")
            self.assertIn("v2.3 Real LLM Harness Report", report)
            self.assertIn("Preflight", report)
            self.assertIn("Review Gate", report)

    def test_longform_4000_chapter_uses_full_generation_budget(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import _max_tokens_for_word_target

        self.assertEqual(_max_tokens_for_word_target(4000), 12000)
        self.assertEqual(_max_tokens_for_word_target(3500), 11200)
        self.assertEqual(_max_tokens_for_word_target(800), 4096)

    def test_v23_real_llm_harness_preflight_rejects_unsafe_real_run(self) -> None:
        from scripts.run_real_llm_harness import run_harness

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            payload = run_harness(
                profile="longform-small-batch",
                book_id="v23-unsafe-run",
                endpoint="久久",
                state_root=root / "foundation" / "runtime_state",
                json_output=root / ".ops" / "validation" / "real_llm_harness.json",
                report_output=root / ".ops" / "reports" / "real_llm_harness_report.md",
                review_output_root=root / ".ops" / "reviews",
                chapters=6,
                word_target=1200,
                batch_schedule="6",
                dry_run=False,
                review_gate=True,
            )

            self.assertEqual(payload["preflight"]["status"], "FAIL")
            error_codes = {item["code"] for item in payload["preflight"]["errors"]}
            self.assertIn("longform_batch_exceeds_upper_bound", error_codes)
            self.assertIn("state_root_not_isolated_ops_path", error_codes)
            self.assertIn("word_target_below_short_chapter_threshold", error_codes)
            self.assertFalse(payload["real_llm_executed"])

    def test_v23_real_llm_harness_postflight_summarizes_fail_fast_chapter(self) -> None:
        from scripts import run_real_llm_harness
        from scripts.run_real_llm_harness import run_harness

        def fake_longform_smoke(**_kwargs):
            return {
                "passed": False,
                "requested_chapters": 4,
                "completed_chapters": 0,
                "batch_runs": [
                    {
                        "batch_no": 1,
                        "status": "failed",
                        "error": "RuntimeError: chapter 1 failed quality gate after repair: short_chapter chinese_chars=3313 < 3500",
                    }
                ],
                "chapter_runs": [
                    {
                        "chapter_no": 1,
                        "status": "failed",
                        "error": "RuntimeError: chapter 1 failed quality gate after repair: short_chapter chinese_chars=3313 < 3500",
                    }
                ],
                "drift_report": {
                    "status": "stable",
                    "short_chapters": [],
                    "missing_foreshadow_chapters": [],
                },
            }

        original = run_real_llm_harness.run_longform_smoke
        run_real_llm_harness.run_longform_smoke = fake_longform_smoke
        try:
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                payload = run_harness(
                    profile="longform-small-batch",
                    book_id="v23-failfast",
                    endpoint="久久",
                    state_root=root / ".ops" / "real_llm_harness" / "state",
                    json_output=root / ".ops" / "validation" / "real_llm_harness.json",
                    report_output=root / ".ops" / "reports" / "real_llm_harness_report.md",
                    review_output_root=root / ".ops" / "reviews",
                    chapters=4,
                    word_target=4000,
                    batch_schedule="4",
                    dry_run=False,
                    review_gate=True,
                )
                report = (root / ".ops" / "reports" / "real_llm_harness_report.md").read_text(encoding="utf-8")
        finally:
            run_real_llm_harness.run_longform_smoke = original

        self.assertFalse(payload["passed"])
        summary = payload["postflight"]["generation_summary"]
        self.assertEqual(summary["failed_chapter"], 1)
        self.assertIn("short_chapter", summary["failure_reason"])
        self.assertEqual(summary["failed_batches"], [1])
        self.assertEqual(payload["review_gate"]["status"], "no_chapters")
        self.assertEqual(payload["review_gate"]["warnings"][0]["code"], "review_gate_no_chapters")
        self.assertIn("failed_chapter", report)
        self.assertIn("short_chapter", report)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
