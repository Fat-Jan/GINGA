"""Longform real LLM smoke report tests.

These tests do not call ask-llm.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class LongformLLMSmokeTest(unittest.TestCase):
    def test_dry_run_records_thirty_chapter_batch_scope_without_state_writes(self) -> None:
        from scripts.run_longform_llm_smoke import run_longform_smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            payload = run_longform_smoke(
                book_id="longform-test",
                state_root=root / "state",
                json_output=root / "longform.json",
                report_output=root / "longform.md",
                chapters=30,
                batch_schedule=[3, 4, 5, 6],
                dry_run=True,
            )

            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["requested_chapters"], 30)
            self.assertEqual(payload["completed_chapters"], 0)
            self.assertEqual(payload["batch_schedule"], [3, 4, 5, 6])
            self.assertEqual(payload["production_policy"]["recommended_batch_size"], 4)
            self.assertEqual(payload["production_policy"]["upper_bound"], 5)
            self.assertEqual(payload["production_policy"]["pressure_test_only_at_or_above"], 6)
            self.assertEqual(len(payload["chapter_runs"]), 30)
            self.assertEqual([item["requested_size"] for item in payload["batch_runs"]], [3, 4, 5, 6, 6, 6])
            self.assertFalse((root / "state" / "longform-test").exists())
            self.assertTrue((root / "longform.json").exists())
            report = (root / "longform.md").read_text(encoding="utf-8")
            self.assertIn("Longform Jiujiu Smoke Report", report)
            self.assertIn("requested_chapters: `30`", report)
            self.assertIn("recommended_batch_size: `4`", report)

    def test_real_mode_uses_sequential_chapter_numbers_and_reports_drift(self) -> None:
        import scripts.run_longform_llm_smoke as smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            calls: list[int] = []

            def fake_generate_batch(*, book_id, state_root, endpoint, word_target, start_chapter, batch_size):
                from ginga_platform.orchestrator.runner.state_io import StateIO

                sio = StateIO(book_id, state_root=state_root, autoload=True)
                if not sio.read("locked.STORY_DNA"):
                    sio.apply(
                        {
                            "locked.STORY_DNA": {"premise": "无明持短刃过天堑"},
                            "locked.GENRE_LOCKED": {"topic": ["玄幻黑暗", "规则怪谈"]},
                            "entity_runtime.CHARACTER_STATE": {"protagonist": {"events": []}},
                            "entity_runtime.FORESHADOW_STATE": {"pool": []},
                            "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0},
                        },
                        source="test.seed_longform",
                    )
                paths = []
                for chapter_no in range(start_chapter, start_chapter + batch_size):
                    calls.append(chapter_no)
                    paragraph = (
                        f"无明握着短刃，在末日天堑下追索微粒与血脉规则。"
                        f"规则在墙上渗血，短刃替他记住第{chapter_no}次代价。"
                        "血脉契约逼迫城民交换姓名，微粒在黑雨里像灰烬一样回旋。"
                    )
                    text = (
                        f"# 第{chapter_no}章 · 天堑规则\n\n"
                        + "\n\n".join(paragraph for _ in range(75))
                        + f"\n<!-- foreshadow: id=fh-long-{chapter_no:03d} planted_ch={chapter_no} "
                        f"expected_payoff={chapter_no + 10} summary=天堑规则 -->\n"
                    )
                    path = state_root / book_id / f"chapter_{chapter_no:02d}.md"
                    sio.write_artifact(
                        f"chapter_{chapter_no:02d}.md",
                        text,
                        source=f"test.fake_longform.ch{chapter_no}",
                        artifact_type="chapter_text",
                        payload={"chapter_no": chapter_no, "execution_mode": "real_llm_demo"},
                    )
                    paths.append(str(path))
                sio.apply(
                    {
                        "entity_runtime.GLOBAL_SUMMARY.total_words": (start_chapter + batch_size - 1) * 80,
                        "entity_runtime.FORESHADOW_STATE.pool": [{"id": f"fh-long-{start_chapter + batch_size - 1:03d}"}],
                    },
                    source=f"test.fake_rollup.batch{start_chapter}",
                )
                return paths, "generated"

            original = smoke._generate_batch
            smoke._generate_batch = fake_generate_batch
            try:
                payload = smoke.run_longform_smoke(
                    book_id="longform-real-test",
                    state_root=root / "state",
                    json_output=root / "longform.json",
                    report_output=root / "longform.md",
                    chapters=15,
                    batch_schedule=[3, 4, 5, 6],
                    word_target=4000,
                    dry_run=False,
                    resume=True,
                )
            finally:
                smoke._generate_batch = original

            self.assertEqual(calls, list(range(1, 16)))
            self.assertTrue(payload["passed"], payload)
            self.assertEqual(payload["completed_chapters"], 15)
            self.assertEqual([item["requested_size"] for item in payload["batch_runs"]], [3, 4, 5, 3])
            self.assertEqual(payload["drift_report"]["status"], "stable")
            self.assertEqual(payload["drift_report"]["forbidden_hit_chapters"], [])
            self.assertTrue((root / "state" / "longform-real-test" / "chapter_15.md").exists())

    def test_drift_short_chapter_threshold_matches_submission_length_floor(self) -> None:
        from scripts.run_longform_llm_smoke import ChapterRun, _drift_report

        short_run = ChapterRun(
            chapter_no=1,
            batch_no=1,
            batch_size=2,
            status="ok",
            path="chapter_01.md",
            chars=3200,
            chinese_chars=3200,
            anchor_hits={"血脉": 1, "末日": 1, "规则": 1, "天堑": 1},
            forbidden_hits={},
            foreshadow_markers=1,
            stdout_tail="",
            stderr_tail="",
        )
        long_enough_run = ChapterRun(
            chapter_no=2,
            batch_no=1,
            batch_size=2,
            status="ok",
            path="chapter_02.md",
            chars=3600,
            chinese_chars=3600,
            anchor_hits={"血脉": 1, "末日": 1, "规则": 1, "天堑": 1},
            forbidden_hits={},
            foreshadow_markers=1,
            stdout_tail="",
            stderr_tail="",
        )

        report = _drift_report([short_run, long_enough_run], ["血脉", "末日", "规则", "天堑"])

        self.assertEqual(report["short_chapters"], [1])
        self.assertEqual(report["status"], "needs_review")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
