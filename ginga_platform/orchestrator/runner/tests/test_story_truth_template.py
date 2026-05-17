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


class StoryTruthTemplateStateSliceTest(unittest.TestCase):
    def test_longform_gate_reports_soft_style_warn_without_block_reason(self) -> None:
        from ginga_platform.orchestrator.cli.longform_policy import evaluate_longform_hard_gate

        state = {"locked": {"GENRE_LOCKED": {"style_lock": {"anchor_phrases": ["血脉"]}}}}
        chapter = {
            "name": "chapter_01.md",
            "text": (
                "# 第一章 · 血门索债\n\n"
                + ("突然，血脉契约把末日城门压得发出裂响，无明用短刃逼近守夜人。" * 120)
                + "\n\n<!-- foreshadow: id=fh-soft planted_ch=1 expected_payoff=5 summary=血门索债 -->"
            ),
        }

        gate = evaluate_longform_hard_gate(state=state, chapters=[chapter])

        self.assertFalse(gate["should_block_next_real_llm_batch"])
        self.assertEqual(gate["block_reasons"], [])
        self.assertEqual(gate["chapter_checks"][0]["soft_style_warn"], {"abrupt_transition": 120})

    def test_init_book_writes_project_and_genre_contracts_through_stateio(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import init_book
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "state"
            init_book(
                "story-truth-state",
                topic="玄幻黑暗",
                premise="失忆刺客追索微粒真相",
                word_target=500000,
                state_root=state_root,
                target_platform="番茄",
                target_reader="男频长篇爽文读者",
                update_frequency="daily",
            )

            sio = StateIO("story-truth-state", state_root=state_root)

        project_contract = sio.read("locked.PROJECT_CONTRACT")
        genre_contract = sio.read("locked.GENRE_CONTRACT")
        self.assertEqual(project_contract["target_platform"], "番茄")
        self.assertEqual(project_contract["target_reader"], "男频长篇爽文读者")
        self.assertEqual(project_contract["total_word_count_goal"], 500000)
        self.assertEqual(project_contract["update_frequency"], "daily")
        self.assertIn("失忆刺客追索微粒真相", project_contract["positioning"])
        self.assertEqual(project_contract["source"], "v1.9-story-truth-template")
        self.assertEqual(genre_contract["profile_ref"], "玄幻黑暗")
        self.assertIn("核心爽点", genre_contract["reader_expectations"][0])
        self.assertEqual(genre_contract["source"], "v1.9-story-truth-template")

    def test_cli_init_accepts_story_truth_contract_options(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "state"
            code = cli_main(
                [
                    "init",
                    "story-truth-cli",
                    "--topic",
                    "规则怪谈",
                    "--premise",
                    "主角在规则副本中寻找真相",
                    "--word-target",
                    "300000",
                    "--target-platform",
                    "七猫",
                    "--target-reader",
                    "悬疑规则怪谈读者",
                    "--update-frequency",
                    "weekday",
                    "--state-root",
                    str(state_root),
                ]
            )
            self.assertEqual(code, 0)
            sio = StateIO("story-truth-cli", state_root=state_root)

        self.assertEqual(sio.read("locked.PROJECT_CONTRACT.target_platform"), "七猫")
        self.assertEqual(sio.read("locked.PROJECT_CONTRACT.target_reader"), "悬疑规则怪谈读者")
        self.assertEqual(sio.read("locked.PROJECT_CONTRACT.update_frequency"), "weekday")
        self.assertEqual(sio.read("locked.GENRE_CONTRACT.profile_ref"), "规则怪谈")


class ChapterInputBundleTest(unittest.TestCase):
    def test_run_workflow_writes_chapter_input_bundle_before_generation(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import init_book, run_workflow
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "state"
            init_book(
                "chapter-bundle-book",
                topic="玄幻黑暗",
                premise="失忆刺客追索微粒真相",
                word_target=500000,
                state_root=state_root,
            )
            chapter_path = run_workflow(
                "chapter-bundle-book",
                word_target=800,
                state_root=state_root,
                mock_llm=True,
            )
            self.assertIsNotNone(chapter_path)
            sio = StateIO("chapter-bundle-book", state_root=state_root)

        bundle = sio.read("workspace.CHAPTER_INPUT_BUNDLE")
        self.assertEqual(bundle["chapter_no"], 1)
        self.assertIn("失忆刺客", bundle["chapter_goal"])
        self.assertTrue(bundle["active_character_state"])
        self.assertTrue(bundle["relevant_world_rules"])
        self.assertTrue(bundle["hook_or_foreshadow_ops"])
        self.assertIn("previous_chapter_bridge", bundle)
        self.assertIn("opening_continuity_guard", bundle)
        self.assertIn("low_frequency_anchors", bundle)
        self.assertEqual(bundle["min_submission_chinese_chars"], 3500)
        self.assertEqual(bundle["minimum_body_chars"], 3500)
        self.assertEqual(bundle["truth_source"], "StateIO")
        self.assertFalse(bundle["reads_report_only_sources"])
        self.assertIn(".ops/book_analysis/**", bundle["forbidden_sources"])

    def test_chapter_prompt_consumes_bundle_continuity_and_low_frequency_anchors(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import (
            _build_chapter_prompt,
            build_chapter_input_bundle,
        )

        state = {
            "locked": {
                "STORY_DNA": {
                    "premise": "无明在末日天堑追索血脉繁衍契约",
                    "conflict_engine": "血脉繁衍契约 vs 末日城邦",
                    "payoff_promise": "每次力量增长都要付出血脉代价",
                },
                "GENRE_LOCKED": {
                    "topic": ["玄幻黑暗", "末日多子多福"],
                    "style_lock": {
                        "tone": ["暗黑"],
                        "forbidden_styles": ["游戏系统播报腔"],
                        "anchor_phrases": ["微粒", "天堑", "血脉", "末日", "繁衍契约"],
                    },
                },
                "GENRE_CONTRACT": {
                    "core_payoffs": ["多子多福", "末日城邦"],
                },
            },
            "entity_runtime": {
                "CHARACTER_STATE": {
                    "protagonist": {
                        "name": "无明",
                        "events": [
                            {"ch": 5, "type": "rule_cost", "impact": "短刃记录了末日城邦的血脉代价"},
                            {"ch": 6, "type": "contract", "impact": "繁衍契约要求无明交出下一次微粒收益"},
                        ],
                    }
                },
                "FORESHADOW_STATE": {
                    "pool": [
                        {
                            "id": "fh-low-anchor",
                            "status": "open",
                            "expected_payoff": 11,
                            "summary": "血脉契约会在末日城邦索债",
                        }
                    ]
                },
                "GLOBAL_SUMMARY": {
                    "total_words": 24000,
                    "arc_summaries": [
                        {
                            "arc": "chapter_1-5",
                            "summary": "无明从天堑废墟进入末日城邦，短刃确认血脉债务",
                        }
                    ],
                },
            },
        }

        bundle = build_chapter_input_bundle(state, word_target=4000, chapter_no=7)
        state["workspace"] = {"CHAPTER_INPUT_BUNDLE": bundle}
        prompt = _build_chapter_prompt(state, word_target=4000, chapter_no=7)

        self.assertIn("## 章节输入包", prompt)
        self.assertIn("承接最近事件", prompt)
        self.assertIn("繁衍契约要求无明交出下一次微粒收益", prompt)
        self.assertIn("开篇必须承接上一章状态变化", prompt)
        self.assertIn("禁止重新醒来", prompt)
        self.assertIn("本章必须保持低频题材锚点", prompt)
        self.assertIn("血脉", prompt)
        self.assertIn("末日", prompt)
        self.assertIn("多子多福", prompt)
        self.assertIn("繁衍契约", prompt)
        self.assertIn("正式投稿质量下限", prompt)
        self.assertIn("正文汉字数 4200-4600", prompt)
        self.assertIn("表格、标题、注释、标点不计入", prompt)
        self.assertIn("正文汉字数低于 3500", prompt)
        self.assertIn("9-11 个正文段落", prompt)
        self.assertIn("每个正文段落 380-520 个汉字", prompt)
        self.assertIn("不得把醒来、睁眼、灰白环境、体内微粒或天堑边缘当作新开场", prompt)
        self.assertIn("禁止写“说不出的感觉”“难以言喻”“复杂的情绪”", prompt)
        self.assertIn("禁止出现“突然”“猛然”“下一秒”", prompt)
        self.assertIn("命运的齿轮", prompt)

    def test_chapter_prompt_counts_body_chinese_chars_not_markdown_overhead(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import _build_chapter_prompt

        state = {
            "locked": {
                "STORY_DNA": {"premise": "失忆刺客追索血脉契约", "conflict_engine": "末日城邦索债"},
                "GENRE_LOCKED": {"topic": ["玄幻黑暗"], "style_lock": {"anchor_phrases": ["血脉", "末日"]}},
                "WORLD": {"economy": "微粒"},
                "PLOT_ARCHITECTURE": {"pivot_points": [{"ch": 1, "beat": "血门索债"}]},
            },
            "entity_runtime": {
                "CHARACTER_STATE": {"protagonist": {"events": []}},
                "FORESHADOW_STATE": {"pool": []},
                "GLOBAL_SUMMARY": {"total_words": 0},
            },
        }

        prompt = _build_chapter_prompt(state, word_target=4000, chapter_no=1)

        self.assertIn("正文汉字数 4200-4600", prompt)
        self.assertIn("表格、标题、注释、标点不计入", prompt)
        self.assertIn("正文汉字数低于 3500", prompt)
        self.assertIn("9-11 个正文段落", prompt)
        self.assertIn("每个正文段落 380-520 个汉字", prompt)
        self.assertNotIn("目标字数 4000 字", prompt)

    def test_chapter_input_bundle_uses_hard_gate_low_frequency_anchor_source(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import build_chapter_input_bundle

        state = {
            "locked": {
                "STORY_DNA": {
                    "premise": "无明在末日天堑追索血脉繁衍契约",
                    "conflict_engine": "多子多福契约 vs 末日城邦",
                },
                "GENRE_LOCKED": {
                    "topic": ["玄幻黑暗", "末日多子多福"],
                    "style_lock": {"anchor_phrases": ["微粒", "天堑"]},
                },
            },
            "entity_runtime": {
                "CHARACTER_STATE": {"protagonist": {"events": []}},
                "FORESHADOW_STATE": {"pool": []},
                "GLOBAL_SUMMARY": {"total_words": 0},
            },
        }

        bundle = build_chapter_input_bundle(state, word_target=4000, chapter_no=7)

        self.assertIn("血脉", bundle["low_frequency_anchors"])
        self.assertIn("末日", bundle["low_frequency_anchors"])
        self.assertIn("多子多福", bundle["low_frequency_anchors"])
        self.assertIn("繁衍契约", bundle["low_frequency_anchors"])

    def test_immersive_runner_writes_chapter_input_bundle(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import init_book
        from ginga_platform.orchestrator.cli.immersive_runner import ImmersiveRunner
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "state"
            init_book(
                "chapter-bundle-immersive",
                topic="玄幻黑暗",
                premise="失忆刺客追索微粒真相",
                word_target=500000,
                state_root=state_root,
            )

            def fake_llm(_prompt: str, _endpoint: str) -> str:
                return "第1章 · 测试\n\n无明握紧短刃，微粒在天堑边缘震动。\n<!-- foreshadow: id=fh-i planted_ch=1 expected_payoff=8 summary=immersive -->"

            runner = ImmersiveRunner("chapter-bundle-immersive", state_root=state_root, llm_caller=fake_llm)
            result = runner.run_block(chapters=2, word_target=200, execution_mode="mock_harness")
            self.assertIsNone(result["last_error"])
            sio = StateIO("chapter-bundle-immersive", state_root=state_root)

        bundle = sio.read("workspace.CHAPTER_INPUT_BUNDLE")
        self.assertEqual(bundle["chapter_no"], 2)
        self.assertEqual(bundle["truth_source"], "StateIO")
        self.assertFalse(bundle["reads_report_only_sources"])
        self.assertIn(".ops/book_analysis/**", bundle["forbidden_sources"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
