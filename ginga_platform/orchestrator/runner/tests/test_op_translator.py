"""Unit tests for ginga_platform.orchestrator.runner.op_translator (ST-S2-PHASE0 P0-2).

覆盖：
    - 4 op 全覆盖：write / delta / append / append_or_update
    - path 规范化：runtime_state.* 前缀剥离 + 裸 chapter_text 映射 + 合法域原样
    - 同 path 多 op 链式合并（pending 中间值参与后续算）
    - 异常路径：未知 op / path 非法 / value 类型不兼容 / append_or_update 缺 key
    - 端到端：翻译完后 state_io.apply 不报错，read 回来值符合预期
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ginga_platform.orchestrator.runner.op_translator import (
    OpTranslationError,
    adapter_ops_to_state_updates,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


class OpTranslatorPathTest(unittest.TestCase):
    def _new_state_io(self) -> StateIO:
        return StateIO("optest", state_root=Path(self._tmp.name))

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_runtime_state_prefix_stripped(self) -> None:
        sio = self._new_state_io()
        updates = adapter_ops_to_state_updates(
            [{
                "op": "write",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 42,
            }],
            sio,
        )
        self.assertIn("entity_runtime.RESOURCE_LEDGER.particles", updates)
        # 直接 apply 不应该报错
        sio.apply(updates, source="optest")
        self.assertEqual(sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 42)

    def test_bare_chapter_text_mapped_to_workspace(self) -> None:
        sio = self._new_state_io()
        updates = adapter_ops_to_state_updates(
            [{"op": "write", "path": "chapter_text", "value": "hello"}],
            sio,
        )
        self.assertEqual(updates, {"workspace.chapter_text": "hello"})
        sio.apply(updates, source="optest")
        self.assertEqual(sio.read("workspace.chapter_text"), "hello")

    def test_already_valid_domain_kept(self) -> None:
        sio = self._new_state_io()
        updates = adapter_ops_to_state_updates(
            [{"op": "write", "path": "locked.STORY_DNA.premise", "value": "x"}],
            sio,
        )
        self.assertEqual(updates, {"locked.STORY_DNA.premise": "x"})

    def test_unknown_path_raises(self) -> None:
        sio = self._new_state_io()
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{"op": "write", "path": "foo.bar", "value": 1}],
                sio,
            )


class OpTranslatorOpTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.sio = StateIO("optest", state_root=Path(self._tmp.name))

    def test_write_overwrites_existing(self) -> None:
        self.sio.apply({"entity_runtime.GLOBAL_SUMMARY.total_words": 100}, source="seed")
        updates = adapter_ops_to_state_updates(
            [{
                "op": "write",
                "path": "runtime_state.entity_runtime.GLOBAL_SUMMARY.total_words",
                "value": 999,
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        self.assertEqual(self.sio.read("entity_runtime.GLOBAL_SUMMARY.total_words"), 999)

    def test_delta_numeric_addition(self) -> None:
        self.sio.apply({"entity_runtime.RESOURCE_LEDGER.particles": 100}, source="seed")
        updates = adapter_ops_to_state_updates(
            [{
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 50,
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        self.assertEqual(self.sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 150)

    def test_delta_on_none_seeds_value(self) -> None:
        updates = adapter_ops_to_state_updates(
            [{
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 25,
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        self.assertEqual(self.sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 25)

    def test_delta_dict_merge(self) -> None:
        self.sio.apply(
            {"entity_runtime.CHARACTER_STATE": {"name": "无明", "iq": "low"}},
            source="seed",
        )
        updates = adapter_ops_to_state_updates(
            [{
                "op": "delta",
                "path": "runtime_state.entity_runtime.CHARACTER_STATE",
                "value": {"iq": "scheming", "mood": "dark"},
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        merged = self.sio.read("entity_runtime.CHARACTER_STATE")
        self.assertEqual(merged, {"name": "无明", "iq": "scheming", "mood": "dark"})

    def test_delta_incompatible_types_raises(self) -> None:
        self.sio.apply({"entity_runtime.RESOURCE_LEDGER.particles": 100}, source="seed")
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{
                    "op": "delta",
                    "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                    "value": "not_a_number",
                }],
                self.sio,
            )

    def test_append_creates_list_when_missing(self) -> None:
        updates = adapter_ops_to_state_updates(
            [{
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": {"type": "particles", "delta": 100},
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        items = self.sio.read("entity_runtime.RESOURCE_LEDGER.items")
        self.assertEqual(items, [{"type": "particles", "delta": 100}])

    def test_append_appends_to_existing_list(self) -> None:
        self.sio.apply(
            {"entity_runtime.RESOURCE_LEDGER.items": [{"a": 1}]},
            source="seed",
        )
        updates = adapter_ops_to_state_updates(
            [{
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": {"a": 2},
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        self.assertEqual(
            self.sio.read("entity_runtime.RESOURCE_LEDGER.items"),
            [{"a": 1}, {"a": 2}],
        )

    def test_append_non_list_raises(self) -> None:
        self.sio.apply({"entity_runtime.RESOURCE_LEDGER.items": 42}, source="seed")
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{
                    "op": "append",
                    "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                    "value": {"a": 1},
                }],
                self.sio,
            )

    def test_append_or_update_replaces_match(self) -> None:
        self.sio.apply(
            {"entity_runtime.FORESHADOW_STATE.pool": [
                {"hook_id": "FH-001", "status": "open"},
                {"hook_id": "FH-002", "status": "open"},
            ]},
            source="seed",
        )
        updates = adapter_ops_to_state_updates(
            [{
                "op": "append_or_update",
                "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                "value": {"hook_id": "FH-001", "status": "closed"},
                "key": "hook_id",
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        pool = self.sio.read("entity_runtime.FORESHADOW_STATE.pool")
        self.assertEqual(pool, [
            {"hook_id": "FH-001", "status": "closed"},
            {"hook_id": "FH-002", "status": "open"},
        ])

    def test_append_or_update_appends_when_no_match(self) -> None:
        self.sio.apply(
            {"entity_runtime.FORESHADOW_STATE.pool": [{"hook_id": "FH-001", "status": "open"}]},
            source="seed",
        )
        updates = adapter_ops_to_state_updates(
            [{
                "op": "append_or_update",
                "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                "value": {"hook_id": "FH-003", "status": "open"},
                "key": "hook_id",
            }],
            self.sio,
        )
        self.sio.apply(updates, source="optest")
        pool = self.sio.read("entity_runtime.FORESHADOW_STATE.pool")
        self.assertEqual(len(pool), 2)
        self.assertEqual(pool[1]["hook_id"], "FH-003")

    def test_append_or_update_requires_key(self) -> None:
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{
                    "op": "append_or_update",
                    "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                    "value": {"hook_id": "FH-001"},
                    # 缺 key
                }],
                self.sio,
            )

    def test_append_or_update_value_must_be_dict(self) -> None:
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{
                    "op": "append_or_update",
                    "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                    "value": "not-a-dict",
                    "key": "hook_id",
                }],
                self.sio,
            )

    def test_unknown_op_raises(self) -> None:
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates(
                [{"op": "stomp", "path": "runtime_state.entity_runtime.X", "value": 1}],
                self.sio,
            )

    def test_chained_ops_on_same_path(self) -> None:
        """同 path 多 op：后一个基于前一个算出的临时值继续算."""
        ops = [
            {
                "op": "write",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 100,
            },
            {
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 50,
            },
            {
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": -30,
            },
        ]
        updates = adapter_ops_to_state_updates(ops, self.sio)
        self.assertEqual(updates["entity_runtime.RESOURCE_LEDGER.particles"], 120)
        self.sio.apply(updates, source="optest")
        self.assertEqual(self.sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 120)

    def test_chained_append_on_same_path(self) -> None:
        ops = [
            {
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": {"a": 1},
            },
            {
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": {"a": 2},
            },
        ]
        updates = adapter_ops_to_state_updates(ops, self.sio)
        self.assertEqual(
            updates["entity_runtime.RESOURCE_LEDGER.items"],
            [{"a": 1}, {"a": 2}],
        )

    def test_empty_ops_returns_empty_dict(self) -> None:
        self.assertEqual(adapter_ops_to_state_updates([], self.sio), {})

    def test_non_list_ops_raises(self) -> None:
        with self.assertRaises(OpTranslationError):
            adapter_ops_to_state_updates({"not": "list"}, self.sio)  # type: ignore[arg-type]


class OpTranslatorE2EWithAdapterShapeTest(unittest.TestCase):
    """模拟 dark-fantasy adapter.output_transform 的完整返回结构 → 翻译 → apply."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.sio = StateIO("optest", state_root=Path(self._tmp.name))
        # 预置：模拟 F_state_init 已跑过
        self.sio.apply(
            {
                "entity_runtime.RESOURCE_LEDGER": {"particles": 0, "items": []},
                "entity_runtime.FORESHADOW_STATE": {"pool": [
                    {"hook_id": "FH-001", "status": "open"},
                ]},
                "entity_runtime.GLOBAL_SUMMARY": {"total_words": 0},
            },
            source="seed",
        )

    def test_full_adapter_output_shape(self) -> None:
        ops = [
            {"op": "write", "path": "chapter_text", "value": "无明睁眼，血雾里只剩刀柄的温度。"},
            {
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": 1200,
            },
            {
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": {"type": "particles", "delta": 1200, "from": "ch1"},
            },
            {
                "op": "append_or_update",
                "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                "value": {"hook_id": "FH-001", "status": "tickled"},
                "key": "hook_id",
            },
            {
                "op": "delta",
                "path": "runtime_state.entity_runtime.GLOBAL_SUMMARY.total_words",
                "value": 2400,
            },
        ]
        updates = adapter_ops_to_state_updates(ops, self.sio)
        # 关键路径都进 updates
        self.assertIn("workspace.chapter_text", updates)
        self.assertEqual(updates["entity_runtime.RESOURCE_LEDGER.particles"], 1200)
        self.assertEqual(updates["entity_runtime.GLOBAL_SUMMARY.total_words"], 2400)
        # apply 不报错
        self.sio.apply(updates, source="adapter")
        # 验证 read 回来一致
        self.assertEqual(self.sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 1200)
        self.assertGreater(self.sio.read("entity_runtime.GLOBAL_SUMMARY.total_words"), 0)
        pool = self.sio.read("entity_runtime.FORESHADOW_STATE.pool")
        self.assertEqual(pool[0]["status"], "tickled")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
