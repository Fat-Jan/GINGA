"""Longform failure reporting regression tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class LongformFailureReportingTest(unittest.TestCase):
    def test_failed_batch_reports_actual_failed_chapter_after_partial_writes(self) -> None:
        import scripts.run_longform_llm_smoke as smoke

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            def fake_generate_batch(*, book_id, state_root, endpoint, word_target, start_chapter, batch_size):
                from ginga_platform.orchestrator.runner.state_io import StateIO

                sio = StateIO(book_id, state_root=state_root, autoload=True)
                paragraph = (
                    "无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。"
                    "血脉契约把末日城门压得发出裂响，短刃沿着天堑石缝刮出黑火。"
                )
                for chapter_no in (1, 2):
                    text = (
                        f"# 第{chapter_no}章 · 血门索债\n\n"
                        + "\n\n".join(paragraph for _ in range(80))
                        + f"\n<!-- foreshadow: id=fh-report-{chapter_no:03d} planted_ch={chapter_no} "
                        f"expected_payoff={chapter_no + 8} summary=血门索债 -->\n"
                    )
                    sio.write_artifact(
                        f"chapter_{chapter_no:02d}.md",
                        text,
                        source=f"test.partial.ch{chapter_no}",
                        artifact_type="chapter_text",
                        payload={"chapter_no": chapter_no, "execution_mode": "real_llm_demo"},
                    )
                raise RuntimeError(
                    "chapter 3 failed quality gate after repair: "
                    "short_chapter body_chinese_chars=3197 < 3500; style_warn cliche_metaphor=1"
                )

            original = smoke._generate_batch
            smoke._generate_batch = fake_generate_batch
            try:
                payload = smoke.run_longform_smoke(
                    book_id="longform-failure-reporting",
                    state_root=root / "state",
                    json_output=root / "longform.json",
                    report_output=root / "longform.md",
                    chapters=4,
                    batch_schedule=[4],
                    word_target=4000,
                    dry_run=False,
                    resume=True,
                )
            finally:
                smoke._generate_batch = original

        self.assertFalse(payload["passed"])
        self.assertEqual(payload["completed_chapters"], 2)
        runs_by_chapter = {run["chapter_no"]: run for run in payload["chapter_runs"]}
        self.assertEqual(runs_by_chapter[1]["status"], "ok")
        self.assertEqual(runs_by_chapter[2]["status"], "ok")
        self.assertEqual(runs_by_chapter[3]["status"], "failed")
        self.assertIn("style_warn cliche_metaphor=1", runs_by_chapter[3]["error"])
        self.assertNotIn(4, runs_by_chapter)
        self.assertEqual(payload["drift_report"]["completed_chapters"], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
