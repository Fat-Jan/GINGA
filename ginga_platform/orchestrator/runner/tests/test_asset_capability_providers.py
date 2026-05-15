"""Focused tests for P2-7B asset-backed H/R capability providers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.registry.asset_providers import (
    H_CHAPTER_SETTLE_ID,
    R1_STYLE_POLISH_ID,
    R2_CONSISTENCY_CHECK_ID,
    R3_FINAL_PACK_ID,
    V1_RELEASE_CHECK_ID,
    h_chapter_settle_provider,
    r1_style_polish_provider,
    r2_consistency_check_provider,
    r3_final_pack_provider,
    v1_release_check_provider,
)
from ginga_platform.orchestrator.runner.dsl_parser import Step
from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.runner.step_dispatch import dispatch_step


def _base_entity_runtime() -> dict[str, Any]:
    return {
        "CHARACTER_STATE": {
            "protagonist": {
                "name": "无明",
                "events": [],
                "psyche": {"mood": "警觉"},
            }
        },
        "RESOURCE_LEDGER": {
            "particles": 100,
            "items": [{"type": "particles", "delta": 100, "from": "seed"}],
        },
        "FORESHADOW_STATE": {
            "pool": [
                {
                    "id": "fh-old",
                    "planted_ch": 1,
                    "expected_payoff": 2,
                    "status": "open",
                    "summary": "旧伏笔",
                }
            ],
        },
        "GLOBAL_SUMMARY": {
            "total_words": 7,
            "arc_summaries": [{"chapter": 0, "summary": "seed", "words": 7}],
        },
    }


def _chapter_text(*, particles: int, hook_id: str, marker: str = "血雾") -> str:
    return (
        "| 写作自检 | 内容 |\n|---|---|\n"
        f"| 当前锚定 | {marker}/微粒/天堑 |\n"
        f"| 预计微粒变化 | +{particles} |\n\n"
        f"# 第2章 · {marker}\n\n"
        f"无明在{marker}里收刀，微粒沿着骨缝倒灌。他没有解释恐惧，只把短刃按回袖中。\n"
        f"<!-- foreshadow: id={hook_id} planted_ch=2 expected_payoff=9 summary={marker}里的新钩子 -->\n"
    )


def _passing_v1_inputs() -> dict[str, Any]:
    chapter_body = (
        "| 写作自检 | 内容 |\n|---|---|\n| 当前锚定 | 血雾/微粒 |\n"
        "| 预计微粒变化 | +120 |\n\n"
        "# 第1章 · 血雾醒刃\n\n"
        "无明在血雾里醒来，短刃贴着掌心吐出一线微粒。他没有立刻相信记忆，"
        "只把追杀者的脚步数进呼吸里。第一重天堑像一张合拢的黑网，逼他在沉默里完成第一次选择。\n\n"
        "他用短刃划开旧誓的皮层，微粒顺着骨缝回流，照出追杀者袖口同样的符文。"
        "这不是偶遇，而是旧秩序留下的账本。\n"
        "<!-- foreshadow: id=FH-001 planted_ch=1 expected_payoff=12 summary=追杀者袖口符文与短刃同源 -->\n"
    )
    return {
        "workspace.chapter_text": chapter_body,
        "locked": {
            "STORY_DNA": {"premise": "记忆与微粒律法的冲突"},
            "WORLD": {"rules": ["微粒可被掠夺"]},
            "PLOT_ARCHITECTURE": {"act1": "觉醒"},
        },
        "entity_runtime": {
            "CHARACTER_STATE": {"protagonist": {"id": "wu_ming"}},
            "RESOURCE_LEDGER": {"particles": 1200},
            "FORESHADOW_STATE": {"pool": [{"id": "FH-001", "status": "open"}]},
            "GLOBAL_SUMMARY": {"total_words": 3200},
        },
        "audit_log": [
            {"source": "step_dispatch:G_chapter_draft", "severity": "info", "msg": "ok"},
        ],
    }


class AssetProviderContractTest(unittest.TestCase):
    def test_provider_asset_refs_point_to_capability_assets(self) -> None:
        for provider, capability_id in (
            (h_chapter_settle_provider, H_CHAPTER_SETTLE_ID),
            (r1_style_polish_provider, R1_STYLE_POLISH_ID),
            (r2_consistency_check_provider, R2_CONSISTENCY_CHECK_ID),
            (r3_final_pack_provider, R3_FINAL_PACK_ID),
        ):
            out = provider({}, {})
            self.assertEqual(out["provider"], "asset-backed")
            self.assertEqual(out["capability_id"], capability_id)
            self.assertTrue(Path(out["asset_ref"]).exists(), out["asset_ref"])


class HChapterSettleProviderTest(unittest.TestCase):
    def test_h_settle_is_input_sensitive_and_uses_legal_state_paths(self) -> None:
        text_a = _chapter_text(particles=250, hook_id="fh-a", marker="血雾")
        text_b = _chapter_text(particles=900, hook_id="fh-b", marker="黑雨")

        out_a = h_chapter_settle_provider(
            {"workspace.chapter_text": text_a, "entity_runtime": _base_entity_runtime()},
            {"chapter_no": 2},
        )
        out_b = h_chapter_settle_provider(
            {"workspace.chapter_text": text_b, "entity_runtime": _base_entity_runtime()},
            {"chapter_no": 2},
        )

        self.assertNotEqual(out_a["state_updates"], out_b["state_updates"])
        self.assertEqual(
            sorted(out_a["state_updates"]),
            [
                "entity_runtime.CHARACTER_STATE",
                "entity_runtime.FORESHADOW_STATE",
                "entity_runtime.RESOURCE_LEDGER",
                "workspace.progress",
            ],
        )
        self.assertEqual(out_a["state_updates"]["entity_runtime.RESOURCE_LEDGER"]["particles"], 350)
        pool = out_a["state_updates"]["entity_runtime.FORESHADOW_STATE"]["pool"]
        self.assertTrue(any(entry.get("id") == "fh-a" for entry in pool), pool)
        self.assertEqual(next(entry for entry in pool if entry.get("id") == "fh-old")["status"], "tickled")
        events = out_a["state_updates"]["entity_runtime.CHARACTER_STATE"]["protagonist"]["events"]
        self.assertEqual(events[-1]["ch"], 2)
        self.assertIn("fh-a", out_a["state_updates"]["workspace.progress"])

    def test_h_settle_progress_is_reader_facing_summary_not_internal_stub(self) -> None:
        out = h_chapter_settle_provider(
            {"workspace.chapter_text": _chapter_text(particles=180, hook_id="fh-readable", marker="黑雨"), "entity_runtime": _base_entity_runtime()},
            {"chapter_no": 2},
        )
        progress = out["state_updates"]["workspace.progress"]
        self.assertIn("第 2 章结算", progress)
        self.assertIn("微粒变化 +180", progress)
        self.assertIn("fh-readable", progress)
        self.assertNotIn("asset-backed provider", progress)


class RProvidersTest(unittest.TestCase):
    def test_r1_polish_adds_missing_style_anchor_without_damaging_comments_or_title(self) -> None:
        text = (
            "| 写作自检 | 内容 |\n|---|---|\n"
            "| 当前锚定 | 血雾 |\n\n"
            "# 第2章 · 血雾\n\n"
            "无明拔刀。下一息，追兵压近。\n"
            "<!-- foreshadow: id=fh-r1-anchor planted_ch=2 expected_payoff=8 summary=血雾会回头 -->\n"
        )
        out = r1_style_polish_provider(
            {
                "workspace.chapter_text": text,
                "locked.GENRE_LOCKED": {"style_lock": {"anchor_phrases": ["血雾", "微粒"], "tone": ["暗黑"]}},
            },
            {},
        )
        polished = out["state_updates"]["workspace.chapter_text"]
        self.assertIn("# 第2章 · 血雾", polished)
        self.assertIn("微粒", polished)
        self.assertIn(
            "<!-- foreshadow: id=fh-r1-anchor planted_ch=2 expected_payoff=8 summary=血雾会回头 -->",
            polished,
        )

    def test_r1_polish_is_deterministic_input_sensitive_and_preserves_foreshadow_comment(self) -> None:
        text = (
            "他感到无比震惊和愤怒。突然之间，血雾压了下来。\n"
            "<!-- foreshadow: id=fh-r1 planted_ch=2 expected_payoff=8 summary=血雾会回头 -->\n"
        )
        out = r1_style_polish_provider(
            {
                "workspace.chapter_text": text,
                "locked.GENRE_LOCKED": {"style_lock": {"anchor_phrases": ["血雾"]}},
            },
            {},
        )
        polished = out["state_updates"]["workspace.chapter_text"]
        self.assertNotEqual(polished, text)
        self.assertIn("血雾", polished)
        self.assertIn(
            "<!-- foreshadow: id=fh-r1 planted_ch=2 expected_payoff=8 summary=血雾会回头 -->",
            polished,
        )
        self.assertEqual(
            r1_style_polish_provider({"workspace.chapter_text": text}, {})["state_updates"][
                "workspace.chapter_text"
            ],
            polished,
        )

    def test_r2_returns_structured_report_and_audit_intent_without_state_updates(self) -> None:
        out = r2_consistency_check_provider(
            {
                "workspace.chapter_text": "无明听见叮的一声，系统提示他恭喜获得奖励。",
                "locked": {"GENRE_LOCKED": {"style_lock": {"forbidden_styles": ["游戏系统播报腔"]}}},
                "entity_runtime": _base_entity_runtime(),
            },
            {"chapter_no": 2},
        )
        self.assertEqual(out["state_updates"], {})
        self.assertIn("consistency_report", out["result"])
        self.assertFalse(out["result"]["pass"])
        self.assertTrue(out["audit_intents"])
        self.assertEqual(out["audit_intents"][0]["action"], "log")
        self.assertNotIn("audit_log", out["state_updates"])

    def test_r2_report_lists_quality_details_and_recommendations(self) -> None:
        out = r2_consistency_check_provider(
            {
                "workspace.chapter_text": "无明拔刀。追兵压近。",
                "locked": {
                    "WORLD": {"power_system": "血雾微粒以债和记忆为媒介"},
                    "GENRE_LOCKED": {"style_lock": {"forbidden_styles": ["游戏系统播报腔"]}},
                },
                "entity_runtime": _base_entity_runtime(),
            },
            {"chapter_no": 2},
        )
        report = out["result"]
        codes = [issue["code"] for issue in report["issues"]]
        self.assertIn("missing_world_anchor", codes)
        self.assertIn("missing_foreshadow_annotation", codes)
        self.assertIn("summary", report)
        self.assertIn("recommendations", report)
        self.assertTrue(report["recommendations"])
        self.assertIn("checked_details", report["consistency_report"])
        self.assertEqual(report["consistency_report"]["checked_details"]["foreshadow_count"], 0)

    def test_r2_report_is_readable_actionable_and_not_state_mutating(self) -> None:
        out = r2_consistency_check_provider(
            {
                "workspace.chapter_text": "无明拔刀。追兵压近。",
                "locked": {
                    "WORLD": {"power_system": "血雾微粒以债和记忆为媒介"},
                    "GENRE_LOCKED": {"style_lock": {"forbidden_styles": ["游戏系统播报腔"]}},
                },
                "entity_runtime": _base_entity_runtime(),
            },
            {"chapter_no": 2},
        )
        report = out["result"]

        self.assertEqual(out["state_updates"], {})
        self.assertIn("readability_report", report)
        readability = report["readability_report"]
        self.assertIn("headline", readability)
        self.assertIn("action_items", readability)
        self.assertIn("evidence", readability)
        self.assertTrue(readability["action_items"])
        self.assertIn("missing_world_anchor", [item["code"] for item in readability["action_items"]])
        self.assertNotIn("audit_log", out["state_updates"])

    def test_r3_final_pack_word_count_and_summary_come_from_chapter_text(self) -> None:
        short = "无明拔刀。\n血雾合拢。"
        long = short + "\n他在旧城门前停住，听见骨缝里的微粒细响。"
        base_summary = {"total_words": 10, "arc_summaries": []}

        out_short = r3_final_pack_provider(
            {"workspace.chapter_text": short, "entity_runtime.GLOBAL_SUMMARY": base_summary},
            {"chapter_no": 3},
        )
        out_long = r3_final_pack_provider(
            {"workspace.chapter_text": long, "entity_runtime.GLOBAL_SUMMARY": base_summary},
            {"chapter_no": 3},
        )

        summary_short = out_short["state_updates"]["entity_runtime.GLOBAL_SUMMARY"]
        summary_long = out_long["state_updates"]["entity_runtime.GLOBAL_SUMMARY"]
        self.assertNotEqual(summary_short["total_words"], summary_long["total_words"])
        self.assertNotEqual(summary_short["arc_summaries"][-1]["words"], 5000)
        self.assertIn("无明拔刀", summary_short["arc_summaries"][-1]["summary"])
        self.assertEqual(
            sorted(out_short["state_updates"]),
            ["entity_runtime.GLOBAL_SUMMARY"],
        )

    def test_r3_summary_ignores_markdown_tables_titles_and_foreshadow_comments(self) -> None:
        text = (
            "| 写作自检 | 内容 |\n|---|---|\n| 当前锚定 | 血雾 |\n\n"
            "# 第3章 · 血雾\n\n"
            "<!-- foreshadow: id=fh-r3 planted_ch=3 expected_payoff=9 summary=血雾回潮 -->\n"
            "无明拔刀。\n血雾合拢。"
        )
        out = r3_final_pack_provider(
            {"workspace.chapter_text": text, "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0, "arc_summaries": []}},
            {"chapter_no": 3},
        )
        summary = out["state_updates"]["entity_runtime.GLOBAL_SUMMARY"]["arc_summaries"][-1]["summary"]
        self.assertIn("无明拔刀", summary)
        self.assertNotIn("写作自检", summary)
        self.assertNotIn("第3章", summary)
        self.assertNotIn("foreshadow", summary)
        self.assertNotIn("|", summary)

    def test_r3_result_exposes_summary_source_and_uncovered_boundaries(self) -> None:
        text = (
            "# 第3章 · 血雾\n\n"
            "无明拔刀。\n\n"
            "血雾合拢，微粒在掌心结成旧债。"
            "<!-- foreshadow: id=fh-r3-readable planted_ch=3 expected_payoff=9 summary=旧债回潮 -->\n"
        )
        out = r3_final_pack_provider(
            {"workspace.chapter_text": text, "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0, "arc_summaries": []}},
            {"chapter_no": 3},
        )
        result = out["result"]
        self.assertEqual(result["summary_source"], "workspace.chapter_text")
        self.assertIn("input_summary", result)
        self.assertIn("无明拔刀", result["input_summary"])
        self.assertIn("uncovered_boundaries", result)
        self.assertIn("not_real_llm_quality_gate", result["uncovered_boundaries"])


class V1ReleaseCheckProviderTest(unittest.TestCase):
    def test_v1_pass_report_is_structured_asset_backed_and_does_not_write_state(self) -> None:
        out = v1_release_check_provider(_passing_v1_inputs(), {"book_id": "book-a"})
        report = out["result"]

        self.assertEqual(out["provider"], "asset-backed")
        self.assertEqual(out["capability_id"], V1_RELEASE_CHECK_ID)
        self.assertTrue(Path(out["asset_ref"]).exists(), out["asset_ref"])
        self.assertEqual(out["state_updates"], {})
        self.assertTrue(report["pass"], report)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["summary"]["issue_count"], 0)
        self.assertEqual(report["inputs_checked"]["chapter_text"], "present")
        self.assertEqual(report["inputs_checked"]["locked"], ["PLOT_ARCHITECTURE", "STORY_DNA", "WORLD"])
        self.assertGreaterEqual(report["summary"]["foreshadow_count"], 1)
        self.assertGreaterEqual(report["summary"]["body_paragraph_count"], 2)

    def test_v1_fail_report_is_input_sensitive_and_lists_issues(self) -> None:
        bad_inputs = _passing_v1_inputs()
        bad_inputs["workspace.chapter_text"] = "  "
        bad_inputs["locked"] = {"STORY_DNA": {"premise": "only one locked domain"}}
        bad_inputs["entity_runtime"] = {"CHARACTER_STATE": {"protagonist": {"id": "wu_ming"}}}
        bad_inputs["audit_log"] = [
            {"source": "checker:consistency", "severity": "error", "msg": "设定冲突"},
            {"source": "guard:x", "severity": "block", "action": "block", "msg": "阻断"},
        ]

        out = v1_release_check_provider(bad_inputs, {"book_id": "book-b"})
        report = out["result"]

        self.assertFalse(report["pass"], report)
        self.assertEqual(out["state_updates"], {})
        issue_codes = [issue["code"] for issue in report["issues"]]
        self.assertIn("chapter_text_empty", issue_codes)
        self.assertIn("locked_domain_missing", issue_codes)
        self.assertIn("entity_runtime_domain_missing", issue_codes)
        self.assertIn("audit_log_error_entry", issue_codes)
        self.assertIn("audit_log_blocking_entry", issue_codes)
        self.assertEqual(report["summary"]["blocking_audit_count"], 2)

    def test_v1_quality_gate_flags_short_template_like_chapter(self) -> None:
        inputs = _passing_v1_inputs()
        inputs["workspace.chapter_text"] = (
            "| 写作自检 | 内容 |\n|---|---|\n| 当前锚定 | mock |\n\n"
            "# 第1章 · 短章\n\n"
            "无明拔刀。\n"
        )
        out = v1_release_check_provider(inputs, {"book_id": "book-short"})
        report = out["result"]
        self.assertFalse(report["pass"], report)
        issue_codes = [issue["code"] for issue in report["issues"]]
        self.assertIn("chapter_text_too_short", issue_codes)
        self.assertIn("body_paragraphs_too_few", issue_codes)
        self.assertIn("foreshadow_annotation_missing", issue_codes)

    def test_v1_release_report_contains_context_gap_and_residual_risk_sidecar(self) -> None:
        out = v1_release_check_provider(_passing_v1_inputs(), {"book_id": "book-a", "execution_mode": "real_llm_demo"})
        report = out["result"]

        self.assertEqual(out["state_updates"], {})
        self.assertIn("context_snapshot", report)
        self.assertEqual(report["context_snapshot"]["book_id"], "book-a")
        self.assertEqual(report["context_snapshot"]["execution_mode"], "real_llm_demo")
        self.assertGreater(report["context_snapshot"]["chapter_text_chars"], 0)
        self.assertIn("gap_report", report)
        self.assertIn("open_gaps", report["gap_report"])
        self.assertIn("residual_risk", report)
        self.assertTrue(report["residual_risk"])
        self.assertIn("quality_summary", report)

    def test_v1_step_dispatch_applies_no_audit_log_state_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_io = StateIO("v1-dispatch", state_root=Path(tmp))
            passing_inputs = _passing_v1_inputs()
            state_io.apply(
                {
                    "workspace.chapter_text": passing_inputs["workspace.chapter_text"],
                    "locked.STORY_DNA": passing_inputs["locked"]["STORY_DNA"],
                    "locked.WORLD": passing_inputs["locked"]["WORLD"],
                    "locked.PLOT_ARCHITECTURE": passing_inputs["locked"]["PLOT_ARCHITECTURE"],
                    "entity_runtime.CHARACTER_STATE": passing_inputs["entity_runtime"]["CHARACTER_STATE"],
                    "entity_runtime.RESOURCE_LEDGER": passing_inputs["entity_runtime"]["RESOURCE_LEDGER"],
                    "entity_runtime.FORESHADOW_STATE": passing_inputs["entity_runtime"]["FORESHADOW_STATE"],
                    "entity_runtime.GLOBAL_SUMMARY": passing_inputs["entity_runtime"]["GLOBAL_SUMMARY"],
                },
                source="test.seed",
            )
            before = len(state_io.audit_log)
            step = Step(
                id="V1_release_check",
                uses_capability=V1_RELEASE_CHECK_ID,
                state_reads=["workspace.chapter_text", "locked.*", "entity_runtime.*", "audit_log"],
                state_writes=["audit_log"],
            )

            result = dispatch_step(
                step,
                {"state_io": state_io, "book_id": "v1-dispatch"},
                capability_registry={V1_RELEASE_CHECK_ID: v1_release_check_provider},
            )

            self.assertTrue(result.output["result"]["pass"], result.output)
            self.assertEqual(result.state_writes_applied, [])
            self.assertGreater(len(state_io.audit_log), before)
            step_entries = [
                entry for entry in state_io.audit_log
                if entry.get("source") == "step_dispatch:V1_release_check"
            ]
            self.assertEqual(len(step_entries), 1)
            self.assertEqual(step_entries[0]["payload"]["writes_applied"], [])

    def test_r2_step_dispatch_applies_provider_audit_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_io = StateIO("r2-dispatch", state_root=Path(tmp))
            state_io.apply(
                {
                    "workspace.chapter_text": "无明听见叮的一声，系统提示他恭喜获得奖励。",
                    "locked.GENRE_LOCKED": {"style_lock": {"forbidden_styles": ["游戏系统播报腔"]}},
                    "entity_runtime.CHARACTER_STATE": {"protagonist": {"name": "无明"}},
                },
                source="test.seed",
            )
            step = Step(
                id="R2_consistency_check",
                uses_capability=R2_CONSISTENCY_CHECK_ID,
                state_reads=["workspace.chapter_text", "locked.*", "entity_runtime.*"],
                state_writes=["audit_log"],
            )

            result = dispatch_step(
                step,
                {"state_io": state_io, "book_id": "r2-dispatch"},
                capability_registry={R2_CONSISTENCY_CHECK_ID: r2_consistency_check_provider},
            )

            self.assertEqual(result.state_writes_applied, [])
            self.assertTrue(
                any(entry.get("source") == "asset_provider:R2_consistency_check" for entry in state_io.audit_log),
                state_io.audit_log,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
