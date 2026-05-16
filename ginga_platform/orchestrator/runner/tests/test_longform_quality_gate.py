"""v1.7 longform quality gate contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class LongformQualityGateTest(unittest.TestCase):
    def test_chapter_gate_counts_body_chinese_chars_without_markdown_overhead(self) -> None:
        from ginga_platform.orchestrator.cli.longform_policy import (
            count_chinese,
            extract_chapter_body_text,
            longform_chapter_gate_check,
        )

        markdown_overhead = (
            "| 写作自检 | 内容 |\n|---|---|\n"
            f"| 当前锚定 | {'血脉末日繁衍契约' * 25} |\n"
            f"| 当前微粒 | {'微粒天堑规则' * 25} |\n\n"
            "# 第一章 · 天堑之下的血肉契约\n\n"
        )
        body = "无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。" * 110
        text = markdown_overhead + body + "\n<!-- foreshadow: id=fh-body planted_ch=1 expected_payoff=5 summary=血门索债 -->\n"

        self.assertGreaterEqual(count_chinese(text), 3500)
        self.assertLess(count_chinese(extract_chapter_body_text(text)), 3500)

        check = longform_chapter_gate_check(
            chapter={"name": "chapter_01.md", "text": text},
            low_frequency_anchors=["血脉"],
        )

        self.assertTrue(check["short_chapter"])

    def _seed_longform_book(self, root: Path, book_id: str = "longform-gate-book") -> None:
        from ginga_platform.orchestrator.runner.state_io import StateIO

        sio = StateIO(book_id, state_root=root)
        sio.apply(
            {
                "locked.STORY_DNA": {
                    "premise": "无明在末日天堑追索短刃、血脉契约与微粒规则",
                    "conflict_engine": "个体存续 vs 末日城邦的血脉繁衍契约",
                },
                "locked.GENRE_LOCKED": {
                    "topic": ["玄幻黑暗", "规则怪谈", "末日多子多福"],
                    "style_lock": {
                        "forbidden_styles": ["游戏系统播报腔", "轻小说吐槽腔"],
                        "anchor_phrases": ["微粒", "天堑", "规则", "血脉", "末日"],
                    },
                },
                "entity_runtime.CHARACTER_STATE": {
                    "protagonist": {
                        "name": "无明",
                        "events": [
                            {"ch": 5, "type": "crossing", "impact": "无明进入血脉契约城"},
                            {"ch": 10, "type": "rule_cost", "impact": "短刃记录末日规则代价"},
                        ],
                    }
                },
                "entity_runtime.RESOURCE_LEDGER.particles": 120,
                "entity_runtime.FORESHADOW_STATE.pool": [{"id": "fh-001"}],
                "entity_runtime.GLOBAL_SUMMARY.total_words": 30000,
            },
            source="test.seed_longform_gate",
        )

        stable = (
            "无明握紧短刃，沿着末日天堑下的血脉规则前行。"
            "城墙上的禁令正在渗血，微粒从尸骨间回流，繁衍契约逼迫幸存者交出姓名。"
        )
        repeated_opening = (
            "无明睁开眼，发现自己仍在天堑边缘，体内微粒像虫卵一样蠕动，短刃贴着掌心发冷。"
            "失忆留下的空洞再次吞噬判断，他像重新醒来一样确认周围。"
        )
        for chapter_no in range(1, 11):
            if chapter_no in {6, 7}:
                body = (repeated_opening + "血脉契约和末日禁令只在远处闪回。") * 80
            elif chapter_no == 8:
                body = (repeated_opening + "黑暗废墟里只剩敌人的脚步声。") * 4
            elif chapter_no == 9:
                body = stable * 80 + "系统提示：叮，恭喜获得新规则。"
            else:
                body = stable * 80
            foreshadow = (
                ""
                if chapter_no == 10
                else f"\n<!-- foreshadow: id=fh-gate-{chapter_no:02d} planted_ch={chapter_no} "
                f"expected_payoff={chapter_no + 5} summary=血脉规则 -->\n"
            )
            sio.write_artifact(
                f"chapter_{chapter_no:02d}.md",
                f"# 第{chapter_no}章\n\n{body}{foreshadow}",
                source=f"test.seed_chapter.{chapter_no}",
                artifact_type="chapter_text",
                payload={"chapter_no": chapter_no, "execution_mode": "mock_harness"},
            )

    def test_review_report_contains_v17_longform_gate_and_reviewer_queue(self) -> None:
        from ginga_platform.orchestrator.review import export_review_report

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "reviews"
            self._seed_longform_book(state_root)

            export_review_report(
                "longform-gate-book",
                run_id="gate-run",
                state_root=state_root,
                output_root=output_root,
            )

            report_path = output_root / "longform-gate-book" / "gate-run" / "review_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            gate = report["longform_quality_gate"]

            self.assertTrue(gate["enabled"])
            self.assertEqual(gate["policy"]["recommended_batch_size"], 4)
            self.assertEqual(gate["policy"]["upper_bound"], 5)
            self.assertEqual(
                [item["chapter_range"] for item in gate["batch_state_snapshots"]],
                ["1-4", "5-8", "9-10"],
            )
            self.assertEqual(gate["hard_gate"]["enabled"], True)
            self.assertEqual(gate["hard_gate"]["mode"], "block_next_real_llm_batch")
            self.assertIn("consecutive_opening_loop_risk", gate["hard_gate"]["block_reasons"])
            self.assertIn("missing_low_frequency_anchor", gate["hard_gate"]["block_reasons"])
            self.assertIn("missing_foreshadow_marker", gate["hard_gate"]["block_reasons"])
            self.assertEqual(gate["batch_state_snapshots"][0]["state_snapshot"]["protagonist"], "无明")
            self.assertEqual(gate["batch_state_snapshots"][0]["state_snapshot"]["particles"], 120)
            self.assertIn(
                "chapter_08.md",
                gate["batch_state_snapshots"][1]["quality_snapshot"]["missing_low_frequency_anchor_chapters"],
            )

            gate_codes = {issue["code"] for issue in gate["issues"]}
            self.assertIn("opening_loop_risk", gate_codes)
            self.assertIn("missing_low_frequency_anchor", gate_codes)
            self.assertIn("missing_foreshadow_marker", gate_codes)

            queued = {item["chapter"] for item in gate["reviewer_queue"]}
            self.assertIn("chapter_06.md", queued)
            self.assertIn("chapter_07.md", queued)
            self.assertIn("chapter_08.md", queued)
            self.assertIn("chapter_09.md", queued)
            self.assertIn("chapter_10.md", queued)
            self.assertNotIn("chapter_01.md", queued)
            self.assertFalse(report["auto_edit"])
            self.assertEqual(report["mode"], "warn_only")
            self.assertGreaterEqual(report["summary"]["longform_gate_issue_count"], 3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
