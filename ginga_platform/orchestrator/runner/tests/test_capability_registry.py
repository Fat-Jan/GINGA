"""Unit tests for ginga_platform.orchestrator.registry.capability_registry (ST-S2-PHASE0 P0-1).

覆盖：
    - register + list_capabilities + resolve + call 四要素
    - CapabilityNotFound 抛错
    - Mapping-like 协议（__contains__ / get / __len__）让 step_dispatch 兼容消费
    - from_defaults() 注册 >=7 个 stub，含 workflow_mvp 必需 id
    - stub 返回结构含 result + state_updates，path 必须以合法 state 域开头
"""

from __future__ import annotations

import unittest

from ginga_platform.orchestrator.registry.capability_registry import (
    CapabilityNotFound,
    CapabilityRegistry,
)


# 与 novel_pipeline_mvp.yaml 的 uses_capability 字段对齐（A-V1）.
_REQUIRED_IDS: tuple[str, ...] = (
    "base-methodology-creative-brainstorm",
    "base-template-story-dna",
    "base-template-worldview",
    "base-template-protagonist",
    "base-template-outline",
    "base-methodology-style-polish",
    "base-card-chapter-draft",
)

_VALID_STATE_DOMAINS: tuple[str, ...] = (
    "locked", "entity_runtime", "workspace", "retrieved",
)


class CapabilityRegistryTest(unittest.TestCase):
    def test_register_and_list(self) -> None:
        reg = CapabilityRegistry()
        reg.register("foo", lambda inp, ctx: {"result": "X", "state_updates": {}})
        reg.register("bar", lambda inp, ctx: {"result": "Y", "state_updates": {}})
        caps = reg.list_capabilities()
        self.assertEqual(caps, ["bar", "foo"])  # 排序输出便于断言

    def test_resolve_missing_raises(self) -> None:
        reg = CapabilityRegistry()
        with self.assertRaises(CapabilityNotFound):
            reg.resolve("not-registered")

    def test_call_returns_dict_with_result_and_state_updates(self) -> None:
        reg = CapabilityRegistry()
        reg.register(
            "demo",
            lambda inp, ctx: {"result": "ok", "state_updates": {"locked.X": 1}},
        )
        out = reg.call("demo", {"x": 1})
        self.assertEqual(out["result"], "ok")
        self.assertEqual(out["state_updates"], {"locked.X": 1})

    def test_register_rejects_non_callable(self) -> None:
        reg = CapabilityRegistry()
        with self.assertRaises(TypeError):
            reg.register("bad", "not-a-fn")  # type: ignore[arg-type]

    def test_register_rejects_empty_id(self) -> None:
        reg = CapabilityRegistry()
        with self.assertRaises(ValueError):
            reg.register("", lambda inp, ctx: {})

    def test_mapping_protocol_for_step_dispatch_consumption(self) -> None:
        """step_dispatch 把 capability_registry 当 Mapping 用：__contains__ + get."""
        reg = CapabilityRegistry()
        reg.register("foo", lambda inp, ctx: {"result": 0, "state_updates": {}})
        self.assertIn("foo", reg)
        self.assertNotIn("bar", reg)
        self.assertIsNotNone(reg.get("foo"))
        self.assertIsNone(reg.get("bar"))
        self.assertEqual(len(reg), 1)

    def test_from_defaults_registers_at_least_seven_required(self) -> None:
        reg = CapabilityRegistry.from_defaults()
        caps = reg.list_capabilities()
        self.assertGreaterEqual(
            len(caps), 7,
            f"expected >=7 default capabilities, got {len(caps)}: {caps}",
        )
        # workflow_mvp 12 step 必须的 7 个 id 全在
        for cid in _REQUIRED_IDS:
            self.assertIn(cid, caps, f"missing required default capability: {cid}")

    def test_from_defaults_stubs_return_valid_shape(self) -> None:
        reg = CapabilityRegistry.from_defaults()
        for cid in reg.list_capabilities():
            out = reg.call(cid, {})
            self.assertIn("result", out, f"{cid}: missing 'result'")
            self.assertIn("state_updates", out, f"{cid}: missing 'state_updates'")
            self.assertIsInstance(out["state_updates"], dict, f"{cid}: state_updates not dict")
            # 每个 path 顶层必须是合法 state 域，避免 state_io 拒绝
            for path in out["state_updates"]:
                top = path.split(".", 1)[0]
                self.assertIn(
                    top, _VALID_STATE_DOMAINS,
                    f"{cid}: state path {path!r} has invalid top domain {top!r}",
                )

    def test_from_defaults_stubs_are_isolated_between_calls(self) -> None:
        """同一个 stub 两次调用必须返回独立 dict（避免 state_io 共享引用副作用）."""
        reg = CapabilityRegistry.from_defaults()
        cid = "base-template-state-init"
        out1 = reg.call(cid, {})
        out2 = reg.call(cid, {})
        self.assertIsNot(out1["state_updates"], out2["state_updates"])
        # 修改其一不影响其二
        if "entity_runtime.RESOURCE_LEDGER" in out1["state_updates"]:
            out1["state_updates"]["entity_runtime.RESOURCE_LEDGER"]["particles"] = 999
            self.assertNotEqual(
                out1["state_updates"]["entity_runtime.RESOURCE_LEDGER"]["particles"],
                out2["state_updates"]["entity_runtime.RESOURCE_LEDGER"]["particles"],
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
