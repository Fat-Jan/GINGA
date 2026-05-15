"""Integration test：12 step workflow 完整跑通 (ST-S2-PHASE0 P0-3).

跑一遍 dsl_parser → step_dispatch（注入 CapabilityRegistry.from_defaults + StateIO
+ SkillRouter + op_translator + dark-fantasy adapter monkey-patched）→ 12 step
全部执行：
    - A-F 调 capability stub（base-methodology / base-template 系列）
    - G 调 skill-router 路由到 dark-fantasy adapter（output 用 monkey-patch 固定）
    - H-V1 继续走 capability stub
    - 所有 state 写入路径都被 state_io 接受（无 StateIOError）
    - audit_log >= 12 条 step entry
    - entity_runtime.GLOBAL_SUMMARY.total_words > 0
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

from ginga_platform.orchestrator.registry.capability_registry import CapabilityRegistry
from ginga_platform.orchestrator.router.skill_router import SkillRouter
from ginga_platform.orchestrator.runner.dsl_parser import parse_workflow_dict
from ginga_platform.orchestrator.runner.op_translator import (
    adapter_ops_to_state_updates,
)
from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.runner.step_dispatch import StepFailed, dispatch_step
from ginga_platform.skills.dark_fantasy_ultimate_engine.adapter import (
    DarkFantasyAdapter,
)


# 仿照 novel_pipeline_mvp.yaml 但 state path 全部规范到合法 state_io 域，
# 避免裸 `chapter_text` 被 step_dispatch._apply_state_writes 通过白名单又被
# state_io 拒（顶层域不合法）.
# 设计：写 chapter_text 一律落到 workspace.chapter_text；audit_log 不走 apply，
# 让 checker / state_io.audit 直接处理.
_WORKFLOW_DICT: dict[str, Any] = {
    "name": "novel_pipeline_mvp_integration",
    "version": "1.0",
    "steps": [
        {
            "id": "A_brainstorm",
            "uses_capability": "base-methodology-creative-brainstorm",
            "state_writes": ["retrieved.brainstorm"],
        },
        {
            "id": "B_premise_lock",
            "uses_capability": "base-template-story-dna",
            "state_reads": ["retrieved.brainstorm"],
            "state_writes": ["locked.STORY_DNA"],
        },
        {
            "id": "C_world_build",
            "uses_capability": "base-template-worldview",
            "state_reads": ["locked.STORY_DNA"],
            "state_writes": ["locked.GENRE_LOCKED", "locked.WORLD"],
        },
        {
            "id": "D_character_seed",
            "uses_capability": "base-template-protagonist",
            "state_reads": ["locked.STORY_DNA", "locked.WORLD"],
            "state_writes": ["entity_runtime.CHARACTER_STATE"],
        },
        {
            "id": "E_outline",
            "uses_capability": "base-template-outline",
            "state_reads": ["locked.STORY_DNA", "locked.WORLD", "entity_runtime.CHARACTER_STATE"],
            "state_writes": ["locked.PLOT_ARCHITECTURE"],
        },
        {
            "id": "F_state_init",
            "uses_capability": "base-template-state-init",
            "state_reads": ["locked.*", "entity_runtime.CHARACTER_STATE"],
            "state_writes": [
                "entity_runtime.RESOURCE_LEDGER",
                "entity_runtime.FORESHADOW_STATE",
                "entity_runtime.GLOBAL_SUMMARY",
                "workspace.task_plan",
                "workspace.findings",
                "workspace.progress",
            ],
        },
        {
            "id": "G_chapter_draft",
            "uses_skill": "skill-router",
            "state_reads": ["locked.*", "entity_runtime.*", "retrieved.*"],
            "state_writes": [
                "workspace.chapter_text",
                "entity_runtime.RESOURCE_LEDGER.particles",
                "entity_runtime.RESOURCE_LEDGER.items",
                "entity_runtime.FORESHADOW_STATE.pool",
                "entity_runtime.GLOBAL_SUMMARY.total_words",
            ],
        },
        {
            "id": "H_chapter_settle",
            "uses_capability": "base-template-chapter-settle",
            "state_reads": ["workspace.chapter_text", "entity_runtime.*"],
            "state_writes": [
                "entity_runtime.CHARACTER_STATE",
                "entity_runtime.RESOURCE_LEDGER",
                "entity_runtime.FORESHADOW_STATE",
                "workspace.progress",
            ],
        },
        {
            "id": "R1_style_polish",
            "uses_capability": "base-methodology-style-polish",
            "state_reads": ["workspace.chapter_text", "locked.GENRE_LOCKED"],
            "state_writes": ["workspace.chapter_text"],
        },
        {
            "id": "R2_consistency_check",
            "uses_capability": "base-methodology-consistency-check",
            "state_reads": ["workspace.chapter_text", "locked.*", "entity_runtime.*"],
            # R2 通过 state_io.audit() 写 audit_log，不走 state_updates
            "state_writes": [],
        },
        {
            "id": "R3_final_pack",
            "uses_capability": "base-methodology-final-pack",
            "state_reads": ["workspace.chapter_text", "entity_runtime.GLOBAL_SUMMARY"],
            "state_writes": ["entity_runtime.GLOBAL_SUMMARY"],
        },
        {
            "id": "V1_release_check",
            "uses_capability": "base-checker-dod-final",
            "state_reads": ["workspace.chapter_text", "locked.*", "entity_runtime.*"],
            "state_writes": [],
        },
    ],
}


def _mock_dark_fantasy_skill_output() -> dict[str, Any]:
    """模拟 dark-fantasy skill 内部产出（adapter input_transform 后真 skill 会算这个）.

    用固定 dict 替代真 LLM 调用，让 adapter.output_transform 能算出 list-of-ops.
    """
    return {
        "chapter_text": (
            "【写作自检】视角/时序/暴力配比 OK\n"
            "无明在血雾里睁开眼。残存意识只剩刀柄的体温——那温度像一句没说出口的告别。\n"
            "他抬手摸向脖颈处那道残缺的面具，指尖触到的不是金属，是某种像律法一样冷的东西。"
        ),
        "writing_self_check": {"pov": "first", "violence_ratio": "0.3"},
        "chapter_settlement": {
            "particle_balance": {"period_start": 0, "delta": 1200, "period_end": 1200},
            "resource_changes": [{"type": "particles", "delta": 1200, "from": "ch1"}],
            "foreshadow_changes": [
                {"hook_id": "FH-001", "status": "tickled", "note": "面具残缺被首次触碰"},
            ],
        },
        "state_updates": {
            "CHARACTER_STATE": {"mood": "解离"},
        },
    }


def _build_dark_fantasy_skill_executor(state_io: StateIO):
    """构造 skill_registry 里 dark-fantasy 那一项需要的 ExecuteFn.

    把 adapter（input_transform / output_transform）+ op_translator 串起来，
    返回 dict 兼容 step_dispatch._apply_state_writes 的 ``state_updates`` 协议.
    """
    adapter = DarkFantasyAdapter(state_io)

    def _execute(inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> dict[str, Any]:
        # 1. 把 inputs（step.state_reads 读出来的）展开成 adapter 期望的 runtime_state 视图.
        # step_dispatch._gather_inputs 把每条 path 单独读，于是 inputs 的 key 是 path 串.
        # adapter.input_transform 需要的是嵌套 runtime_state；这里直接从 state_io 整域读.
        runtime_state = {
            "locked": state_io.read("locked") or {},
            "entity_runtime": state_io.read("entity_runtime") or {},
            "retrieved": state_io.read("retrieved") or {},
        }
        _ = adapter.input_transform(runtime_state)  # 让 transform 跑一遍验证可用
        # 2. mock skill_output（绕开真 LLM）
        skill_output = _mock_dark_fantasy_skill_output()
        # 3. adapter.output_transform → list-of-ops
        ops = adapter.output_transform(skill_output)
        # 4. op_translator 转 flat dict
        flat_updates = adapter_ops_to_state_updates(ops, state_io)
        return {
            "result": "<dark-fantasy mock chapter>",
            "state_updates": flat_updates,
            "chapter_text": skill_output["chapter_text"],
        }

    return _execute


class TwelveStepIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._state_root = Path(self._tmp.name) / "state"
        # 1. 建一个 sk registry + dark-fantasy contract.yaml（含 priority 段）让 SkillRouter 能解析.
        self._skills_root = Path(self._tmp.name) / "skills"
        self._setup_fake_skills_dir()

    def _setup_fake_skills_dir(self) -> None:
        sdir = self._skills_root / "dark-fantasy-ultimate-engine"
        sdir.mkdir(parents=True)
        (sdir / "contract.yaml").write_text(
            "skill_id: dark-fantasy-ultimate-engine\n"
            "priority:\n"
            "  - when: topic in [玄幻黑暗, 暗黑奇幻]\n"
            "    score: 100\n"
            "  - default: 0\n",
            encoding="utf-8",
        )
        (self._skills_root / "registry.yaml").write_text(
            "skills:\n"
            "  - skill_id: dark-fantasy-ultimate-engine\n"
            "    enabled: true\n",
            encoding="utf-8",
        )

    def test_full_12_step_run_through(self) -> None:
        # 1) 解析 workflow
        wf = parse_workflow_dict(_WORKFLOW_DICT)
        self.assertEqual(len(wf.steps), 12)

        # 2) 构造 StateIO + registries + router
        state_io = StateIO("integ-book", state_root=self._state_root)
        cap_reg = CapabilityRegistry.from_defaults()
        skill_router = SkillRouter(
            registry_path=self._skills_root / "registry.yaml",
            skills_root=self._skills_root,
        )
        skill_registry = {
            "dark-fantasy-ultimate-engine": _build_dark_fantasy_skill_executor(state_io),
        }
        runtime_ctx = {"state_io": state_io, "book_id": "integ-book"}

        # 3) 逐 step dispatch
        dispatch_results = []
        for step in wf.steps:
            result = dispatch_step(
                step,
                runtime_ctx,
                capability_registry=cap_reg,
                skill_registry=skill_registry,
                skill_router=skill_router,
            )
            dispatch_results.append(result)

        # 4) 断言：12 个 step 全跑完
        self.assertEqual(len(dispatch_results), 12, "12 step should all execute")
        # G_chapter_draft 应路由到 dark-fantasy
        g_result = next(r for r in dispatch_results if r.step_id == "G_chapter_draft")
        self.assertEqual(g_result.used, "skill:dark-fantasy-ultimate-engine")

        # 5) audit_log 至少 12 条 step_dispatch entry
        step_audits = [
            e for e in state_io.audit_log
            if isinstance(e.get("source"), str) and e["source"].startswith("step_dispatch:")
        ]
        self.assertGreaterEqual(
            len(step_audits), 12,
            f"expected >=12 step_dispatch audits, got {len(step_audits)}",
        )

        # 6) total_words > 0（adapter 算 chapter_text 字数 + R3 final_pack 再写一次）
        total_words = state_io.read("entity_runtime.GLOBAL_SUMMARY.total_words")
        self.assertIsNotNone(total_words)
        self.assertGreater(total_words, 0, f"total_words should be > 0, got {total_words}")

        # 7) chapter_text 落到 workspace 域（adapter output → workspace.chapter_text；
        #    R1_style_polish 再 overwrite）
        chapter_text = state_io.read("workspace.chapter_text")
        self.assertIsInstance(chapter_text, str)
        self.assertGreater(len(chapter_text), 0)

        # 8) 关键 state 字段都有值
        self.assertIsNotNone(state_io.read("locked.STORY_DNA.premise"))
        self.assertIsNotNone(state_io.read("locked.WORLD"))
        self.assertIsNotNone(state_io.read("locked.PLOT_ARCHITECTURE"))
        self.assertIsNotNone(state_io.read("entity_runtime.CHARACTER_STATE"))
        # FORESHADOW pool 被 adapter append_or_update 过：FH-001 应是 tickled
        pool = state_io.read("entity_runtime.FORESHADOW_STATE.pool") or []
        self.assertTrue(
            any(p.get("hook_id") == "FH-001" and p.get("status") == "tickled" for p in pool),
            f"FH-001 should be marked tickled by adapter, pool={pool}",
        )
        # RESOURCE_LEDGER.particles 经 adapter delta（+1200）+ H_chapter_settle overwrite 整域（=1200）
        # final 至少 > 0
        particles = state_io.read("entity_runtime.RESOURCE_LEDGER.particles")
        self.assertIsNotNone(particles)
        self.assertGreater(particles, 0)

    def test_adapter_input_transform_invoked_in_g_step(self) -> None:
        """G_chapter_draft 时确实把 runtime_state 喂给 adapter.input_transform."""
        wf = parse_workflow_dict(_WORKFLOW_DICT)
        state_io = StateIO("integ-book-2", state_root=self._state_root)
        cap_reg = CapabilityRegistry.from_defaults()
        skill_router = SkillRouter(
            registry_path=self._skills_root / "registry.yaml",
            skills_root=self._skills_root,
        )
        with patch.object(
            DarkFantasyAdapter,
            "input_transform",
            wraps=DarkFantasyAdapter.input_transform,
            autospec=True,
        ) as mock_input:
            skill_registry = {
                "dark-fantasy-ultimate-engine": _build_dark_fantasy_skill_executor(state_io),
            }
            runtime_ctx = {"state_io": state_io, "book_id": "integ-book-2"}
            for step in wf.steps:
                dispatch_step(
                    step,
                    runtime_ctx,
                    capability_registry=cap_reg,
                    skill_registry=skill_registry,
                    skill_router=skill_router,
                )
            self.assertGreaterEqual(
                mock_input.call_count, 1,
                "DarkFantasyAdapter.input_transform should be called at least once (G step)",
            )


class StepDispatchNoopPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_io = StateIO("noop-policy", state_root=Path(self._tmp.name) / "state")

    def test_missing_capability_fails_loud_by_default(self) -> None:
        wf = parse_workflow_dict(
            {
                "name": "missing_capability",
                "steps": [
                    {
                        "id": "A_missing",
                        "uses_capability": "missing-capability",
                        "state_writes": ["workspace.progress"],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(StepFailed, "capability not registered"):
            dispatch_step(wf.steps[0], {"state_io": self.state_io}, capability_registry={})

    def test_missing_skill_router_fails_loud_by_default(self) -> None:
        wf = parse_workflow_dict(
            {
                "name": "missing_router",
                "steps": [
                    {
                        "id": "G_missing_router",
                        "uses_skill": "skill-router",
                        "state_writes": ["workspace.chapter_text"],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(StepFailed, "skill_router not provided"):
            dispatch_step(wf.steps[0], {"state_io": self.state_io}, skill_registry={})

    def test_explicit_dev_noop_allowed_preserves_legacy_noop(self) -> None:
        wf = parse_workflow_dict(
            {
                "name": "dev_noop",
                "steps": [
                    {
                        "id": "A_missing",
                        "uses_capability": "missing-capability",
                        "state_writes": ["workspace.progress"],
                    }
                ],
            }
        )

        result = dispatch_step(
            wf.steps[0],
            {"state_io": self.state_io, "execution_mode": "dev/noop_allowed"},
            capability_registry={},
        )

        self.assertEqual(result.used, "capability:missing-capability")
        self.assertIn("noop", result.output["note"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
