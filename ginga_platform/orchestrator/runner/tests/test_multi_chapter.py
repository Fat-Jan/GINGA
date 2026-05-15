"""ST-S2-S-MULTI-CHAPTER 测试：多章 wire-up 与 multi_chapter runner.

覆盖范围：
    S-1 apply_chapter_rollup：单章滚动 entity_runtime（events / foreshadow / particles / total_words / arc_summaries）
    S-1 _extract_foreshadow_hooks：从 chapter_text 抽取 LLM 标注的伏笔
    S-1 _check_foreshadow_payoff：既有 hook expected_payoff 到期时切 tickled
    S-3/S-4 R 流水线 + V1 DoD（multi_chapter.run_multi_chapter mock LLM 路径）
    S-5 5 章连跑：累加正确性

LLM 调用全部 mock（不接真 ask-llm，避免单元测试依赖外部服务）.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from ginga_platform.orchestrator.cli.demo_pipeline import (
    _check_foreshadow_payoff,
    _extract_foreshadow_hooks,
    _extract_particle_delta,
    apply_chapter_rollup,
    init_book,
    run_workflow,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


def _make_fake_chapter_text(chapter_no: int, *, foreshadow_id: str | None = None, particles: int = 0) -> str:
    """生成够 3000+ bytes 的 mock 章节文本（含表格头 + 正文 + 可选伏笔注释）."""
    table = (
        "| 写作自检 | 内容 |\n|---|---|\n"
        "| 当前锚定 | 微粒/天堑/内宇宙 |\n"
        f"| 当前微粒 | {particles} |\n"
        f"| 预计微粒变化 | {particles} |\n"
        "| 主要冲突 | 失忆刺客 vs 微粒掠夺集团 |\n\n"
    )
    body_unit = (
        f"第{chapter_no}章 · 微粒在血雾里翻涌。无明睁眼，残存意识只剩刀柄的体温——那温度像一句没说出口的告别。"
        "他抬手摸向脖颈处那道残缺的面具，指尖触到的不是金属，是某种像律法一样冷的东西。"
        "天堑外的风穿过废都，把他剩下的呼吸切成碎片。微粒在血雾里像一群无声的鱼，等着被吞。\n"
    )
    body = body_unit * 30  # 保证 >3000 bytes
    extras = ""
    if foreshadow_id:
        extras = (
            f"\n<!-- foreshadow: id={foreshadow_id} planted_ch={chapter_no} "
            f"expected_payoff={chapter_no + 10} summary=第{chapter_no}章新埋的钩子 -->\n"
        )
    return table + body + extras


class ExtractForeshadowHooksTest(unittest.TestCase):
    def test_extract_html_comment_format(self) -> None:
        text = (
            "正文……\n"
            "<!-- foreshadow: id=fh-002 planted_ch=2 expected_payoff=20 summary=面具的低语 -->\n"
        )
        hooks = _extract_foreshadow_hooks(text, chapter_no=2)
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0]["id"], "fh-002")
        self.assertEqual(hooks[0]["planted_ch"], 2)
        self.assertEqual(hooks[0]["expected_payoff"], 20)
        self.assertEqual(hooks[0]["status"], "open")
        self.assertIn("面具", hooks[0]["summary"])

    def test_extract_chinese_line_format(self) -> None:
        text = "正文……\n【伏笔】id=fh-x01 planted_ch=3 expected_payoff=18 summary=刀柄上的血锈"
        hooks = _extract_foreshadow_hooks(text, chapter_no=3)
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0]["id"], "fh-x01")

    def test_dedupe_same_id(self) -> None:
        text = (
            "<!-- foreshadow: id=fh-a planted_ch=1 expected_payoff=5 summary=A -->\n"
            "<!-- foreshadow: id=fh-a planted_ch=1 expected_payoff=5 summary=A -->\n"
        )
        hooks = _extract_foreshadow_hooks(text, chapter_no=1)
        self.assertEqual(len(hooks), 1)

    def test_no_hooks_returns_empty(self) -> None:
        text = "正文里没有任何 foreshadow 注释。"
        self.assertEqual(_extract_foreshadow_hooks(text, chapter_no=4), [])


class CheckForeshadowPayoffTest(unittest.TestCase):
    def test_open_hook_due_marks_tickled(self) -> None:
        pool = [
            {"id": "fh-001", "planted_ch": 1, "expected_payoff": 5, "status": "open"},
        ]
        out = _check_foreshadow_payoff(pool, chapter_no=5)
        self.assertEqual(out[0]["status"], "tickled")
        self.assertEqual(out[0]["tickled_at_ch"], 5)

    def test_open_hook_not_due_remains_open(self) -> None:
        pool = [
            {"id": "fh-001", "planted_ch": 1, "expected_payoff": 30, "status": "open"},
        ]
        out = _check_foreshadow_payoff(pool, chapter_no=5)
        self.assertEqual(out[0]["status"], "open")

    def test_already_tickled_not_re_processed(self) -> None:
        pool = [
            {"id": "fh-001", "planted_ch": 1, "expected_payoff": 5, "status": "tickled"},
        ]
        out = _check_foreshadow_payoff(pool, chapter_no=10)
        self.assertEqual(out[0]["status"], "tickled")
        self.assertNotIn("tickled_at_ch", out[0])  # 不二次盖章


class ExtractParticleDeltaTest(unittest.TestCase):
    def test_explicit_delta_marker(self) -> None:
        self.assertEqual(_extract_particle_delta("...微粒delta: 1200..."), 1200)
        self.assertEqual(_extract_particle_delta("...微粒结算: -800..."), -800)

    def test_table_marker(self) -> None:
        self.assertEqual(_extract_particle_delta("| 预计微粒变化 | +1500 |"), 1500)

    def test_no_marker_returns_zero(self) -> None:
        self.assertEqual(_extract_particle_delta("没有结算"), 0)


class ApplyChapterRollupTest(unittest.TestCase):
    """S-1 核心：apply_chapter_rollup 把单章产出滚动写回 state."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._state_root = Path(self._tmp.name)
        self.book_id = "rollup-book"
        # patch DEFAULT_STATE_ROOT via state_root argument
        sio = StateIO(self.book_id, state_root=self._state_root)
        # seed minimum state
        sio.apply(
            {
                "locked.STORY_DNA.premise": "test",
                "entity_runtime.CHARACTER_STATE": {
                    "protagonist": {
                        "name": "无明",
                        "events": [],
                    }
                },
                "entity_runtime.FORESHADOW_STATE.pool": [
                    {"id": "fh-001", "planted_ch": 1, "expected_payoff": 10, "status": "open"},
                ],
                "entity_runtime.RESOURCE_LEDGER.particles": 0,
                "entity_runtime.GLOBAL_SUMMARY.total_words": 0,
                "entity_runtime.GLOBAL_SUMMARY.arc_summaries": [],
            },
            source="test.seed",
        )
        self.sio = sio

    def test_rollup_appends_event(self) -> None:
        ch_text = _make_fake_chapter_text(2)
        apply_chapter_rollup(self.sio, chapter_no=2, chapter_text=ch_text, word_count=3500)
        events = self.sio.read("entity_runtime.CHARACTER_STATE.protagonist.events")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["ch"], 2)
        self.assertEqual(events[0]["type"], "draft")

    def test_rollup_accumulates_total_words(self) -> None:
        apply_chapter_rollup(self.sio, chapter_no=1, chapter_text="...", word_count=3000)
        apply_chapter_rollup(self.sio, chapter_no=2, chapter_text="...", word_count=3500)
        total = self.sio.read("entity_runtime.GLOBAL_SUMMARY.total_words")
        self.assertEqual(total, 6500)

    def test_rollup_appends_new_foreshadow(self) -> None:
        ch_text = _make_fake_chapter_text(2, foreshadow_id="fh-002")
        apply_chapter_rollup(self.sio, chapter_no=2, chapter_text=ch_text, word_count=3500)
        pool = self.sio.read("entity_runtime.FORESHADOW_STATE.pool")
        ids = {p["id"] for p in pool}
        self.assertIn("fh-001", ids)
        self.assertIn("fh-002", ids)

    def test_rollup_tickles_due_foreshadow(self) -> None:
        # fh-001 expected_payoff=10；在第 10 章 rollup 时应当切 tickled
        apply_chapter_rollup(self.sio, chapter_no=10, chapter_text="...", word_count=3000)
        pool = self.sio.read("entity_runtime.FORESHADOW_STATE.pool")
        fh001 = next(p for p in pool if p["id"] == "fh-001")
        self.assertEqual(fh001["status"], "tickled")

    def test_rollup_arc_summary_every_5_chapters(self) -> None:
        for n in range(1, 6):
            apply_chapter_rollup(self.sio, chapter_no=n, chapter_text="...", word_count=1000)
        arcs = self.sio.read("entity_runtime.GLOBAL_SUMMARY.arc_summaries")
        # 第 5 章触发一次 arc 总结
        self.assertEqual(len(arcs), 1)
        self.assertEqual(arcs[0]["arc"], "chapter_1-5")
        self.assertEqual(arcs[0]["anchor_ch"], 5)

    def test_rollup_particle_delta_applied(self) -> None:
        ch_text = "...| 预计微粒变化 | +1200 |..."
        apply_chapter_rollup(self.sio, chapter_no=1, chapter_text=ch_text, word_count=1000)
        particles = self.sio.read("entity_runtime.RESOURCE_LEDGER.particles")
        self.assertEqual(particles, 1200)


class SingleChapterWorkflowConvergenceTest(unittest.TestCase):
    """P2-7: single chapter run should enter workflow DSL + skill adapter path."""

    def test_single_run_uses_workflow_steps_skill_router_and_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            state_root = Path(d) / "state"
            book_id = "p2-7-single"
            init_book(
                book_id,
                topic="玄幻黑暗",
                premise="测试 P2-7 runner 收敛",
                word_target=10000,
                state_root=state_root,
            )

            chapter_path = run_workflow(
                book_id,
                word_target=800,
                state_root=state_root,
                mock_llm=True,
            )

            self.assertIsNotNone(chapter_path)
            sio = StateIO(book_id, state_root=state_root)
            entries = sio.audit_log
            sources = [entry.get("source", "") for entry in entries]
            messages = [entry.get("msg", "") for entry in entries]

            self.assertTrue(
                any(source.startswith("step_dispatch:G_chapter_draft") for source in sources),
                sources,
            )
            self.assertTrue(
                any(source.startswith("step_dispatch:H_chapter_settle") for source in sources),
                sources,
            )
            self.assertTrue(
                any(source.startswith("step_dispatch:R1_style_polish") for source in sources),
                sources,
            )
            self.assertTrue(
                any(source.startswith("step_dispatch:V1_release_check") for source in sources),
                sources,
            )
            self.assertTrue(
                any("skill_router selected dark-fantasy-ultimate-engine" in msg for msg in messages),
                messages,
            )
            self.assertTrue(
                any("dark_fantasy_adapter.output_transform applied" in msg for msg in messages),
                messages,
            )
            self.assertIn("离线演练", sio.read("workspace.chapter_text", ""))
            artifact_entries = [
                entry for entry in entries
                if entry.get("payload", {}).get("artifact_type") == "chapter_text"
            ]
            self.assertTrue(artifact_entries, entries)


# -- S-3 / S-4 / S-5 tests are in test cases below ---------------------------


class MultiChapterRunnerTest(unittest.TestCase):
    """S-5: multi_chapter.run_multi_chapter mock LLM 路径，验证 5 章连跑."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._state_root = Path(self._tmp.name)
        # 重定向默认 state_root 到 tmp：mock 模块级函数（非已绑定的默认参数）
        self._patch_root = patch(
            "ginga_platform.orchestrator.runner.state_io._default_state_root",
            return_value=self._state_root,
        )
        self._patch_root.start()
        self.addCleanup(self._patch_root.stop)
        self.book_id = "multi-book"

    def _seed_book(self) -> None:
        init_book(
            self.book_id,
            topic="玄幻黑暗",
            premise="测试用 premise",
            word_target=10000,
        )

    def test_5_chapters_end_to_end_with_mock_llm(self) -> None:
        from ginga_platform.orchestrator.cli import multi_chapter

        self._seed_book()

        # mock LLM 调用：每次返回一个 mock chapter_text
        call_count = {"n": 0}

        def _fake_call_llm(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
            call_count["n"] += 1
            ch_no = call_count["n"]
            return _make_fake_chapter_text(ch_no, foreshadow_id=f"fh-mc-{ch_no:02d}", particles=100 * ch_no)

        with patch("ginga_platform.orchestrator.cli.demo_pipeline._call_llm", side_effect=_fake_call_llm):
            with patch(
                "ginga_platform.orchestrator.cli.multi_chapter._call_llm_for_polish",
                side_effect=lambda txt, endpoint: txt + "\n<!-- polished by R1 -->",
            ):
                result = multi_chapter.run_multi_chapter(
                    self.book_id,
                    chapters=5,
                    llm_endpoint="windhub",
                    word_target=3500,
                )

        self.assertTrue(result["ok"], f"runner should report ok=True, got {result}")
        self.assertEqual(result["chapters_done"], 5)
        # 5 个 chapter_NN.md
        state_dir = self._state_root / self.book_id
        chapters = sorted(state_dir.glob("chapter_*.md"))
        self.assertEqual(len(chapters), 5, f"expected 5 chapter files, got {[c.name for c in chapters]}")
        # 每章 >= 3000 bytes（DoD 字段之一）
        for c in chapters:
            self.assertGreaterEqual(c.stat().st_size, 3000, f"{c.name} too small ({c.stat().st_size} bytes)")

        # total_words 累加正确（5 章 × _make_fake_chapter_text 字数）
        sio = StateIO(self.book_id, state_root=self._state_root)
        total = sio.read("entity_runtime.GLOBAL_SUMMARY.total_words")
        self.assertGreater(total, 0)
        # arc_summaries 第 5 章触发
        arcs = sio.read("entity_runtime.GLOBAL_SUMMARY.arc_summaries")
        self.assertGreaterEqual(len(arcs), 1)
        # foreshadow pool 至少 N 条（原 fh-001 + 5 章 mock 新 hook）
        pool = sio.read("entity_runtime.FORESHADOW_STATE.pool")
        self.assertGreaterEqual(len(pool), 1 + 5)

        # DoD checker 结果（V1）
        self.assertIn("dod_report", result)
        self.assertTrue(result["dod_report"]["pass"], f"DoD should pass, got {result['dod_report']}")

    def test_dod_fails_when_chapter_too_short(self) -> None:
        from ginga_platform.orchestrator.cli import multi_chapter

        self._seed_book()

        def _short_chapter_text(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
            return "短得离谱"  # < 3000 bytes

        with patch("ginga_platform.orchestrator.cli.demo_pipeline._call_llm", side_effect=_short_chapter_text):
            with patch(
                "ginga_platform.orchestrator.cli.multi_chapter._call_llm_for_polish",
                side_effect=lambda txt, endpoint: txt,
            ):
                result = multi_chapter.run_multi_chapter(
                    self.book_id,
                    chapters=2,
                    llm_endpoint="windhub",
                    word_target=3500,
                )
        # short chapter 应触发 DoD warn（min_bytes 不达标）
        self.assertFalse(result["dod_report"]["pass"], f"DoD should fail on short chapters, got {result['dod_report']}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
