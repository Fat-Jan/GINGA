"""Unit tests for dark-fantasy immersive_mode end-to-end (ST-S2-I IMMERSIVE).

覆盖：
    - I-1: enter_immersive_mode 写 workflow_flags + audit "immersive entered"
    - I-3: checker_invoker silenced hook (workspace.workflow_flags.checker_silenced)
    - I-4: exit_immersive_mode 批量 apply（op_translator）+ R2_consistency_check trigger
    - I-2/I-5: ImmersiveRunner.run_block N 章 block（注入 mock LLM）
    - 异常路径：persist fallback / idempotent enter / pending 累积语义
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.meta_integration.checker_invoker import invoke_checkers
from ginga_platform.skills.dark_fantasy_ultimate_engine.adapter import DarkFantasyAdapter
from ginga_platform.orchestrator.cli.immersive_runner import ImmersiveRunner
from ginga_platform.orchestrator.cli.immersive_runner import _repair_prompt


class _BaseImmersiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_root = Path(self._tmp.name)
        self.sio = StateIO("immer-book", state_root=self.state_root)
        # seed locked + entity_runtime（避免 read 空）
        self.sio.apply(
            {
                "locked.GENRE_LOCKED.topic": ["玄幻黑暗"],
                "locked.STORY_DNA.premise": "test premise",
                "entity_runtime.RESOURCE_LEDGER": {"particles": 0, "items": []},
                "entity_runtime.FORESHADOW_STATE": {"pool": []},
                "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0},
                "workspace.task_plan": "seed",
            },
            source="seed",
        )
        self.adapter = DarkFantasyAdapter(self.sio)


class EnterImmersiveTest(_BaseImmersiveTest):
    def test_enter_sets_workflow_flags(self) -> None:
        self.adapter.enter_immersive_mode()
        self.assertTrue(self.sio.read("workspace.workflow_flags.immersive_mode"))
        self.assertTrue(self.sio.read("workspace.workflow_flags.checker_silenced"))

    def test_enter_audit_immersive_entered(self) -> None:
        self.adapter.enter_immersive_mode()
        msgs = [e["msg"] for e in self.sio.audit_log]
        self.assertTrue(any("immersive entered" in m for m in msgs), msgs)

    def test_enter_snapshot_taken(self) -> None:
        self.adapter.enter_immersive_mode()
        self.assertIsNotNone(self.adapter._last_safe_state)
        self.assertEqual(self.adapter._last_safe_state.get("book_id"), "immer-book")

    def test_enter_idempotent(self) -> None:
        self.adapter.enter_immersive_mode()
        before = len(self.sio.audit_log)
        self.adapter.enter_immersive_mode()
        after = len(self.sio.audit_log)
        self.assertEqual(before, after, "second enter should be no-op (no extra audit)")


class CheckerSilencedHookTest(_BaseImmersiveTest):
    def test_silenced_true_returns_all_off(self) -> None:
        self.sio.apply({"workspace.workflow_flags.checker_silenced": True}, source="test")
        ctx = {"state_io": self.sio, "step_id": "G_chapter_draft"}
        results = invoke_checkers(
            ["aigc-style-detector", "character-iq-checker"],
            {"chapter_text": "随便文本"},
            ctx,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["mode"] == "off" for r in results))
        self.assertTrue(all(r.get("silenced") is True for r in results))
        # audit 写一条 silenced（一条不是两条，避免噪音）
        silenced_audits = [
            e for e in self.sio.audit_log
            if "checker silenced (immersive)" in e.get("msg", "")
        ]
        self.assertEqual(len(silenced_audits), 1, "silenced audit should be written exactly once")

    def test_silenced_unset_returns_normal(self) -> None:
        # 没设过 silenced，不走 silenced 分支
        ctx = {"state_io": self.sio, "step_id": "G_chapter_draft"}
        # 用一个不存在的 checker id 触发 S1 fallback noop 路径（不命中规则）
        results = invoke_checkers(["__nonexistent_checker__"], {"chapter_text": "x"}, ctx)
        self.assertEqual(len(results), 1)
        self.assertNotIn("silenced", results[0])
        # 不应该出现 silenced 类 audit
        silenced_audits = [
            e for e in self.sio.audit_log
            if "checker silenced" in e.get("msg", "")
        ]
        self.assertEqual(len(silenced_audits), 0)


class ExitBatchApplyTest(_BaseImmersiveTest):
    def test_exit_translates_and_applies_pending(self) -> None:
        self.adapter.enter_immersive_mode()
        # 模拟 2 章 output_transform：每章 chapter_text + particle delta
        for i, text in enumerate(["第一章内容", "第二章内容"], start=1):
            self.adapter.output_transform({
                "chapter_text": text,
                "chapter_settlement": {"particle_balance": {"delta": 100 * i}},
            })
        self.assertGreater(len(self.adapter._pending_updates), 0)

        summary = self.adapter.exit_immersive_mode()
        self.assertIsNone(summary["last_error"], f"exit failed: {summary}")
        self.assertEqual(summary["chapter_count"], 2)
        self.assertGreater(summary["applied_count"], 0)

        # particle delta 累计：100 + 200 = 300
        particles = self.sio.read("entity_runtime.RESOURCE_LEDGER.particles")
        self.assertEqual(particles, 300)
        # chapter_text 被翻译到 workspace.chapter_text（op_translator 兜底 _BARE_PATH_MAPPING）
        ws_chapter = self.sio.read("workspace.chapter_text")
        self.assertIn("第二章内容", ws_chapter)

    def test_exit_resets_flags(self) -> None:
        self.adapter.enter_immersive_mode()
        self.adapter.output_transform({"chapter_text": "x"})
        self.adapter.exit_immersive_mode()
        self.assertFalse(self.sio.read("workspace.workflow_flags.immersive_mode"))
        self.assertFalse(self.sio.read("workspace.workflow_flags.checker_silenced"))

    def test_exit_audit_batch_applied(self) -> None:
        self.adapter.enter_immersive_mode()
        for _ in range(3):
            self.adapter.output_transform({"chapter_text": "ch"})
        self.adapter.exit_immersive_mode()
        msgs = [e["msg"] for e in self.sio.audit_log]
        batch_audits = [m for m in msgs if "batch applied" in m]
        self.assertEqual(len(batch_audits), 1, msgs)
        self.assertIn("3 chapters batch applied", batch_audits[0])

    def test_exit_triggers_r2(self) -> None:
        self.adapter.enter_immersive_mode()
        self.adapter.output_transform({"chapter_text": "ch"})
        self.adapter.exit_immersive_mode()
        msgs = [e["msg"] for e in self.sio.audit_log]
        r2_audits = [m for m in msgs if "R2_consistency_check triggered" in m]
        self.assertEqual(len(r2_audits), 1, msgs)

    def test_exit_without_enter_returns_zero(self) -> None:
        summary = self.adapter.exit_immersive_mode()
        self.assertEqual(summary["applied_count"], 0)
        self.assertEqual(summary["chapter_count"], 0)


class PendingAggregationTest(_BaseImmersiveTest):
    def test_immersive_output_transform_returns_empty(self) -> None:
        self.adapter.enter_immersive_mode()
        result = self.adapter.output_transform({"chapter_text": "x"})
        self.assertEqual(result, [], "immersive period output_transform should return []")
        self.assertGreater(len(self.adapter._pending_updates), 0)

    def test_non_immersive_output_transform_returns_updates(self) -> None:
        # 不进 immersive → output_transform 返回正常 list
        result = self.adapter.output_transform({"chapter_text": "x"})
        self.assertGreater(len(result), 0, "non-immersive should return ops")


class ExitFallbackTest(_BaseImmersiveTest):
    def test_persist_pending_on_failure(self) -> None:
        # 用一个 monkey-patched adapter 强制翻译失败
        self.adapter.enter_immersive_mode()
        # 注入一个 path 无法被 op_translator 识别的 op 触发异常
        self.adapter._pending_updates.append({
            "op": "write",
            "path": "totally_unknown_top.x",  # op_translator 抛 OpTranslationError
            "value": 1,
        })
        # chdir 到 tmp 让 .ops/immersive_fallback 落到 tmp 内
        import os
        cwd = os.getcwd()
        os.chdir(self._tmp.name)
        try:
            summary = self.adapter.exit_immersive_mode()
        finally:
            os.chdir(cwd)
        self.assertIsNotNone(summary["last_error"])
        # fallback json 存在
        fallback_dir = Path(self._tmp.name) / ".ops" / "immersive_fallback"
        self.assertTrue(fallback_dir.exists())
        files = list(fallback_dir.glob("immer-book_*.json"))
        self.assertGreater(len(files), 0)
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertIn("pending_updates", payload)


class ImmersiveRunnerRunBlockTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_root = Path(self._tmp.name)
        sio = StateIO("runner-book", state_root=self.state_root)
        sio.apply(
            {
                "locked.GENRE_LOCKED.topic": ["玄幻黑暗"],
                "locked.GENRE_LOCKED.style_lock": {"tone": ["暗黑"], "forbidden_styles": [], "anchor_phrases": ["微粒"]},
                "locked.STORY_DNA.premise": "p",
                "locked.STORY_DNA.conflict_engine": "ce",
                "locked.STORY_DNA.payoff_promise": "pp",
                "locked.WORLD.cosmology": "c",
                "locked.WORLD.economy": "e",
                "locked.PLOT_ARCHITECTURE.acts": [],
                "locked.PLOT_ARCHITECTURE.pivot_points": [{"beat": "b"}],
                "entity_runtime.CHARACTER_STATE": {"protagonist": {"name": "x", "inventory": [], "abilities": [], "body": {}, "psyche": {}}},
                "entity_runtime.RESOURCE_LEDGER": {"particles": 0, "items": []},
                "entity_runtime.FORESHADOW_STATE": {"pool": []},
                "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0},
            },
            source="seed",
        )

    def test_run_block_5_chapters_mock_llm(self) -> None:
        captured_prompts: list[str] = []
        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            captured_prompts.append(prompt)
            ch_no = len(captured_prompts)
            return f"# 第{ch_no}章\n\n" + ("墨" * 200)  # 200 个中文字符

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=5, word_target=200)

        self.assertEqual(result["chapter_count"], 5)
        self.assertEqual(len(captured_prompts), 5)
        self.assertEqual(result["batch_chapter_count"], 5)
        self.assertIsNone(result["last_error"])

        # 5 个 chapter_NN.md 落盘
        state_dir = self.state_root / "runner-book"
        chapter_files = sorted(state_dir.glob("chapter_*.md"))
        self.assertEqual(len(chapter_files), 5)

        # audit_log 含 "5 chapters batch applied" 和 R2 trigger
        sio2 = StateIO("runner-book", state_root=self.state_root)
        msgs = [e["msg"] for e in sio2.audit_log]
        self.assertTrue(any("5 chapters batch applied" in m for m in msgs), msgs)
        self.assertTrue(any("R2_consistency_check triggered" in m for m in msgs), msgs)
        # 期内 chapter drafted audit 也有 5 条
        drafted = [m for m in msgs if "chapter" in m and "drafted (immersive" in m]
        self.assertEqual(len(drafted), 5)
        # 期内不应有 checker warn entry（checker_silenced 拦截）
        warn_entries = [
            e for e in sio2.audit_log
            if e.get("severity") == "warn" and "checker" in e.get("source", "")
        ]
        self.assertEqual(len(warn_entries), 0, f"unexpected checker warn entries: {warn_entries}")

    def test_run_block_invalid_chapters_raises(self) -> None:
        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=lambda *_a, **_k: "x",
        )
        with self.assertRaises(ValueError):
            runner.run_block(chapters=0)

    def test_run_block_default_prompt_keeps_chapter_headings_continuous(self) -> None:
        captured_prompt_labels: list[str] = []

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            match = re.search(r"章节标题用「(.+?)」", prompt)
            self.assertIsNotNone(match, prompt)
            label = match.group(1)
            captured_prompt_labels.append(label)
            return f"# {label.replace('<小标题>', '黑雾初醒')}\n\n" + ("墨" * 200)

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        runner.run_block(chapters=5, word_target=200)

        expected_labels = ["第一章 · <小标题>"] + [
            f"第{n}章 · <小标题>" for n in range(2, 6)
        ]
        self.assertEqual(captured_prompt_labels, expected_labels)

        state_dir = self.state_root / "runner-book"
        heading_numbers: list[int] = []
        for path in sorted(state_dir.glob("chapter_*.md")):
            text = path.read_text(encoding="utf-8")
            match = re.search(r"第([一二三四五六七八九十0-9]+)章", text)
            self.assertIsNotNone(match, text[:120])
            raw = match.group(1)
            heading_numbers.append({"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}.get(raw, int(raw) if raw.isdigit() else -1))
        self.assertEqual(heading_numbers, [1, 2, 3, 4, 5])

    def test_run_block_normalizes_repeated_llm_heading_numbers(self) -> None:
        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            return "# 第一章 · 黑雾初醒\n\n" + ("墨" * 200)

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        runner.run_block(chapters=5, word_target=200)

        state_dir = self.state_root / "runner-book"
        headings: list[str] = []
        for path in sorted(state_dir.glob("chapter_*.md")):
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            headings.append(first_line)
        self.assertEqual(
            headings,
            [
                "# 第一章 · 黑雾初醒",
                "# 第2章 · 黑雾初醒",
                "# 第3章 · 黑雾初醒",
                "# 第4章 · 黑雾初醒",
                "# 第5章 · 黑雾初醒",
            ],
        )

    def test_run_block_carries_previous_chapter_excerpt_into_next_prompt(self) -> None:
        captured_prompts: list[str] = []

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            captured_prompts.append(prompt)
            ch_no = len(captured_prompts)
            if ch_no == 1:
                return (
                    "# 第一章 · 血契索债\n\n"
                    "无明没有重新醒来，他沿着天堑血桥逼近末日城邦。"
                    "短刃把血脉契约刻进掌心，微粒收益被下一轮索债锁死。"
                    "<!-- foreshadow: id=fh-bridge-1 planted_ch=1 expected_payoff=6 summary=血脉索债 -->"
                )
            return "# 第2章 · 接债入城\n\n" + ("血脉契约压在城门上。" * 60)

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=2, word_target=200)

        self.assertIsNone(result["last_error"])
        self.assertEqual(len(captured_prompts), 2)
        second_prompt = captured_prompts[1]
        self.assertIn("上一章生成摘要", second_prompt)
        self.assertIn("短刃把血脉契约刻进掌心", second_prompt)
        self.assertNotIn("缺少前章事件摘要", second_prompt)

    def test_run_block_uses_previous_chapter_ending_not_repeated_opening_as_bridge(self) -> None:
        captured_prompts: list[str] = []
        repeated_opening = (
            "痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气。"
            "他重新确认体内微粒和短刃。"
        )
        ending = (
            "无明把清道夫的骨牌按进城门血槽，血脉契约在门缝里亮起。"
            "末日城邦的守夜人抬灯，要求他立刻交出下一轮微粒收益。"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            captured_prompts.append(prompt)
            if len(captured_prompts) == 1:
                return f"# 第一章 · 坏开头\n\n{repeated_opening}\n\n{ending}"
            if "质量修复" in prompt:
                return "# 第一章 · 血门索债\n\n" + (ending * 90)
            return "# 第2章 · 接债入城\n\n" + ("血脉契约压在城门上。" * 80)

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=2, word_target=4000)

        self.assertIsNone(result["last_error"])
        second_prompt = captured_prompts[-1]
        self.assertIn("第2章", second_prompt)
        self.assertIn("上一章生成摘要", second_prompt)
        self.assertIn("守夜人抬灯", second_prompt)
        self.assertNotIn(repeated_opening, second_prompt)

    def test_run_block_repairs_short_or_opening_loop_chapter_before_writing(self) -> None:
        calls: list[str] = []
        bad_chapter = (
            "# 第一章 · 重启模板\n\n"
            "痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气。"
            "他重新确认体内微粒和短刃。"
        )
        repaired_chapter = (
            "# 第一章 · 血门索债\n\n"
            + ("无明把清道夫骨牌按进城门血槽，血脉契约逼着守夜人交出末日账册。" * 180)
            + "\n\n<!-- foreshadow: id=fh-repair planted_ch=1 expected_payoff=5 summary=血门索债 -->"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            calls.append(prompt)
            return bad_chapter if len(calls) == 1 else repaired_chapter

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=1, word_target=4000)

        self.assertIsNone(result["last_error"])
        self.assertEqual(len(calls), 2)
        self.assertIn("质量修复", calls[1])
        self.assertIn("正文汉字数 4200-4600", calls[1])
        self.assertIn("表格、标题、注释、标点不计入", calls[1])
        self.assertIn("正文汉字数低于 3500", calls[1])
        self.assertIn("9-11 个正文段落", calls[1])
        self.assertIn("每个正文段落 380-520 个汉字", calls[1])
        chapter_text = (self.state_root / "runner-book" / "chapter_01.md").read_text(encoding="utf-8")
        self.assertIn("血门索债", chapter_text)
        self.assertNotIn("痛觉并未因意识的回归而消退", chapter_text)

    def test_repair_prompt_rewrites_from_failure_summary_without_full_draft_anchor(self) -> None:
        long_problem_draft = (
            "痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气。"
            "他重新确认体内微粒和短刃。"
        ) * 80

        prompt = _repair_prompt(
            "BASE PROMPT",
            long_problem_draft,
            4000,
            2,
            attempt=1,
            failure="short_chapter chinese_chars=3313 < 3500",
        )

        self.assertIn("正文汉字数 4200-4600", prompt)
        self.assertIn("表格、标题、注释、标点不计入", prompt)
        self.assertIn("9-11 个正文段落", prompt)
        self.assertIn("每个正文段落 380-520 个汉字", prompt)
        self.assertIn("上一版失败摘要", prompt)
        self.assertIn("上一版短摘录", prompt)
        self.assertLess(prompt.count("痛觉并未因意识的回归而消退"), 4)
        self.assertNotIn("## 上一版问题稿", prompt)

    def test_quality_gate_uses_submission_floor_not_word_target_ratio(self) -> None:
        from ginga_platform.orchestrator.cli.immersive_runner import _quality_gate_failure

        chapter = (
            "| 写作自检 | 内容 |\n|---|---|\n| 当前锚定 | 血脉 |\n\n"
            "# 第一章 · 血门索债\n\n"
            + ("无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。" * 120)
            + "\n<!-- foreshadow: id=fh-floor planted_ch=1 expected_payoff=5 summary=血门索债 -->\n"
        )

        self.assertIsNone(_quality_gate_failure(chapter, word_target=4000, chapter_no=1))

    def test_run_block_repairs_review_style_warn_patterns_before_writing(self) -> None:
        calls: list[str] = []
        style_warn_chapter = (
            "# 第一章 · 血门索债\n\n"
            + ("无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。" * 90)
            + "突然，仿佛命运的齿轮在血雾深处转动。"
            + ("血脉契约把末日城门压得发出裂响，无明用短刃逼近守夜人。" * 90)
            + "\n\n<!-- foreshadow: id=fh-style planted_ch=1 expected_payoff=5 summary=血门索债 -->"
        )
        repaired_chapter = (
            "# 第一章 · 血门索债\n\n"
            + ("无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。" * 190)
            + "\n\n<!-- foreshadow: id=fh-style-repair planted_ch=1 expected_payoff=5 summary=血门索债 -->"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            calls.append(prompt)
            return style_warn_chapter if len(calls) == 1 else repaired_chapter

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=1, word_target=4000)

        self.assertIsNone(result["last_error"])
        self.assertEqual(len(calls), 2)
        self.assertIn("style_warn", calls[1])
        chapter_text = (self.state_root / "runner-book" / "chapter_01.md").read_text(encoding="utf-8")
        self.assertNotIn("突然", chapter_text)
        self.assertNotIn("命运的齿轮", chapter_text)

    def test_run_block_allows_second_repair_before_failing_fast(self) -> None:
        calls: list[str] = []
        bad_chapter = (
            "# 第一章 · 重启模板\n\n"
            "痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气。"
            "他重新确认体内微粒和短刃。"
        )
        still_short = "# 第一章 · 仍短\n\n" + ("无明把血脉契约按进末日城门。" * 120)
        second_repair_ok = (
            "# 第一章 · 血门索债\n\n"
            + ("无明把清道夫骨牌按进城门血槽，守夜人抬灯逼他交出下一轮微粒收益。" * 190)
            + "\n\n<!-- foreshadow: id=fh-repair-2 planted_ch=1 expected_payoff=5 summary=血门索债 -->"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            calls.append(prompt)
            if len(calls) == 1:
                return bad_chapter
            if len(calls) == 2:
                return still_short
            return second_repair_ok

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=1, word_target=4000)

        self.assertIsNone(result["last_error"])
        self.assertEqual(len(calls), 3)
        self.assertIn("质量修复第 2 次", calls[2])
        chapter_text = (self.state_root / "runner-book" / "chapter_01.md").read_text(encoding="utf-8")
        self.assertIn("血门索债", chapter_text)

    def test_run_block_fails_fast_when_repair_still_misses_submission_gate(self) -> None:
        calls: list[str] = []
        bad_chapter = (
            "# 第一章 · 仍然短\n\n"
            "痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气。"
            "他重新确认体内微粒和短刃。"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            calls.append(prompt)
            return bad_chapter

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=4, word_target=4000)

        self.assertIsNotNone(result["last_error"])
        self.assertIn("chapter 1 failed quality gate after repair", result["last_error"])
        self.assertEqual(len(calls), 3)
        self.assertEqual(result["chapter_count"], 0)
        self.assertFalse((self.state_root / "runner-book" / "chapter_01.md").exists())
        self.assertFalse((self.state_root / "runner-book" / "chapter_02.md").exists())

    def test_first_chapter_quality_gate_allows_origin_opening_if_length_passes(self) -> None:
        calls: list[str] = []
        origin_opening = (
            "# 第一章 · 天堑初醒\n\n"
            + ("痛觉并未因意识的回归而消退，无明睁开眼，看见灰白雾气和天堑边缘。"
               "体内微粒撞击短刃，血脉契约在末日城门上索债。" * 190)
            + "\n\n<!-- foreshadow: id=fh-origin planted_ch=1 expected_payoff=5 summary=首章起源 -->"
        )

        def mock_llm(prompt: str, endpoint: str, **kw) -> str:
            calls.append(prompt)
            return origin_opening

        runner = ImmersiveRunner(
            "runner-book",
            state_root=self.state_root,
            llm_caller=mock_llm,
        )
        result = runner.run_block(chapters=1, word_target=4000)

        self.assertIsNone(result["last_error"])
        self.assertEqual(len(calls), 1)
        self.assertTrue((self.state_root / "runner-book" / "chapter_01.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
