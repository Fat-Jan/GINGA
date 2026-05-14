"""capability_registry — 资产 id → 可执行函数的注册中心.

来源：ARCHITECTURE.md §4.2（uses_capability 用资产 id，由 registry 解析）+
ROADMAP §二 Sprint 2 + .ops/p7-prompts/ST-S2-PHASE0.md.

定位：
    workflow YAML 的 step.uses_capability 字段是「资产 id」（如
    ``base-template-protagonist``），不是文件路径；本模块负责把 id 解析为
    实际可执行的 callable，再由 step_dispatch 调用。

当前边界：
    - ``from_defaults`` 仍是 mock harness / backward-compatible test registry：
      每个 capability 返回固定 dict，足够 step_dispatch 结构测试跑通
    - **不接真原料 / 不调 LLM**；真实 LLM 路径在 CLI demo / multi_chapter /
      immersive runner 中
    - 未来 production path 应替换为 asset-backed capability providers

返回格式约定（与 step_dispatch._apply_state_writes 对齐）::

    callable(inputs: Mapping[str, Any], context: Mapping[str, Any]) -> dict
    返回值必须含：
        result        : str | dict（capability 的主输出，便于 audit 摘要）
        state_updates : dict[str, Any]（flat path → value，喂给 state_io.apply）

state_updates 的 path 必须是合法 state_io 顶层域（locked / entity_runtime /
workspace / retrieved）的子路径，不允许裸 chapter_text 等无前缀键。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping

# capability 执行体类型签名（与 step_dispatch.ExecuteFn 对齐）.
CapabilityFn = Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]


class CapabilityNotFound(KeyError):
    """resolve / call 时找不到对应 capability id."""

    def __init__(self, capability_id: str) -> None:
        super().__init__(capability_id)
        self.capability_id = capability_id

    def __str__(self) -> str:  # pragma: no cover - 调试用
        return f"capability not registered: {self.capability_id!r}"


class CapabilityRegistry:
    """workflow step.uses_capability 字段的 id → 可执行函数 / 资产解析器.

    Usage::

        reg = CapabilityRegistry.from_defaults()
        fn = reg.resolve("base-template-protagonist")
        output = reg.call("base-template-protagonist", {"locked.STORY_DNA": ...})
        assert "result" in output and "state_updates" in output

    与 step_dispatch 集成：把 registry 当成 ``capability_registry`` 参数传入
    ``dispatch_step``（已支持 ``Mapping[str, ExecuteFn]`` 形态——本类实现
    ``__contains__`` / ``get`` 以兼容 Mapping 协议消费方）.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, CapabilityFn] = {}

    # -- public API ---------------------------------------------------------

    def register(self, capability_id: str, handler: CapabilityFn) -> None:
        """注册一个 capability handler.

        相同 id 重复注册会直接覆盖（开发期便利；S3 引入 frozen 状态再加锁）.
        """
        if not capability_id or not isinstance(capability_id, str):
            raise ValueError(f"capability_id must be non-empty str, got {capability_id!r}")
        if not callable(handler):
            raise TypeError(
                f"handler for {capability_id!r} must be callable, got {type(handler).__name__}"
            )
        self._handlers[capability_id] = handler

    def list_capabilities(self) -> List[str]:
        """返回已注册的 capability id 列表（稳定排序，便于断言 / 日志）."""
        return sorted(self._handlers.keys())

    def resolve(self, capability_id: str) -> CapabilityFn:
        """根据 id 取出 handler；缺失抛 ``CapabilityNotFound``."""
        try:
            return self._handlers[capability_id]
        except KeyError as exc:
            raise CapabilityNotFound(capability_id) from exc

    def call(self, capability_id: str, inputs: Mapping[str, Any], context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """便利方法：解析 + 调用，返回标准 dict 输出."""
        fn = self.resolve(capability_id)
        result = fn(inputs, context or {})
        if not isinstance(result, dict):
            raise TypeError(
                f"capability {capability_id!r} must return dict, got {type(result).__name__}"
            )
        return result

    # -- Mapping-like 兼容（让 step_dispatch.capability_registry 可以直接传本对象）---

    def __contains__(self, capability_id: object) -> bool:
        return isinstance(capability_id, str) and capability_id in self._handlers

    def __getitem__(self, capability_id: str) -> CapabilityFn:
        return self.resolve(capability_id)

    def get(self, capability_id: str, default: Any = None) -> Any:
        """Mapping.get 形态：未注册返回 ``default``（与 dict.get 一致）."""
        return self._handlers.get(capability_id, default)

    def __len__(self) -> int:
        return len(self._handlers)

    # -- factory ------------------------------------------------------------

    @classmethod
    def from_defaults(cls) -> "CapabilityRegistry":
        """Mock harness：注册足够 12 step 结构测试跑通的 capability stub.

        覆盖的 capability id（与 novel_pipeline_mvp.yaml 的 uses_capability 对齐）::

            A_brainstorm        base-methodology-creative-brainstorm
            B_premise_lock      base-template-story-dna
            C_world_build       base-template-worldview
            D_character_seed    base-template-protagonist
            E_outline           base-template-outline
            F_state_init        base-template-state-init
            G_chapter_draft     base-card-chapter-draft (default writer fallback)
            H_chapter_settle    base-template-chapter-settle
            R1_style_polish     base-methodology-style-polish
            R2_consistency_check base-methodology-consistency-check
            R3_final_pack       base-methodology-final-pack
            V1_release_check    base-checker-dod-final

        每个 stub 返回固定 ``state_updates`` 让 12 step 全部通过 state_io
        校验（路径必须在合法顶层域）.
        """
        reg = cls()

        # A_brainstorm：写 retrieved.brainstorm
        reg.register(
            "base-methodology-creative-brainstorm",
            _make_stub(
                result_text="<mock brainstorm: 失忆刺客闯入血雾废都，被吞噬律法困住>",
                state_updates={
                    "retrieved.brainstorm": {
                        "core_idea": "失忆刺客 vs 吞噬律法",
                        "tones": ["黑暗", "压抑", "暴力美学"],
                        "raw_seeds": ["血雾废都", "记忆碎片", "微粒律法"],
                    },
                },
            ),
        )

        # B_premise_lock：写 locked.STORY_DNA
        reg.register(
            "base-template-story-dna",
            _make_stub(
                result_text="<mock STORY_DNA locked>",
                state_updates={
                    "locked.STORY_DNA": {
                        "premise": "失忆刺客觉醒于吞噬律法之下，须夺回 840000000 微粒以重铸自我",
                        "core_conflict": "记忆 vs 律法 vs 微粒",
                        "audience": "黑暗玄幻读者",
                    },
                },
            ),
        )

        # C_world_build：写 locked.GENRE_LOCKED + locked.WORLD
        reg.register(
            "base-template-worldview",
            _make_stub(
                result_text="<mock world built>",
                state_updates={
                    "locked.GENRE_LOCKED": {
                        "topic": ["玄幻黑暗"],
                        "style_lock": "dark_philosophy_with_visceral_action",
                    },
                    "locked.WORLD": {
                        "physical": "血雾废都 + 吞噬律法",
                        "social": "微粒寡头 + 觉醒者地下网络",
                        "metaphor": "记忆是货币，遗忘是债务",
                    },
                },
            ),
        )

        # D_character_seed：写 entity_runtime.CHARACTER_STATE
        reg.register(
            "base-template-protagonist",
            _make_stub(
                result_text="<mock character seeds>",
                state_updates={
                    "entity_runtime.CHARACTER_STATE": {
                        "protagonist": {
                            "id": "wu_ming",
                            "name": "无明",
                            "drives": ["夺回记忆", "拆解吞噬律法", "复仇"],
                            "iq_level": "scheming",
                        },
                        "supporting": [],
                    },
                },
            ),
        )

        # E_outline：写 locked.PLOT_ARCHITECTURE
        reg.register(
            "base-template-outline",
            _make_stub(
                result_text="<mock outline>",
                state_updates={
                    "locked.PLOT_ARCHITECTURE": {
                        "act1": "觉醒 + 失忆 + 第一次掠夺",
                        "act2": "结盟地下网络 + 追查微粒源头",
                        "act3": "对决微粒寡头 + 重铸自我",
                        "foreshadows": ["FH-001:残缺面具", "FH-002:血雾低语"],
                    },
                },
            ),
        )

        # F_state_init：初始化 entity_runtime 全字段 + workspace 三件套
        reg.register(
            "base-template-state-init",
            _make_stub(
                result_text="<mock state init>",
                state_updates={
                    "entity_runtime.RESOURCE_LEDGER": {
                        "particles": 0,
                        "items": [],
                    },
                    "entity_runtime.FORESHADOW_STATE": {
                        "pool": [
                            {"hook_id": "FH-001", "status": "open"},
                            {"hook_id": "FH-002", "status": "open"},
                        ],
                    },
                    "entity_runtime.GLOBAL_SUMMARY": {
                        "total_words": 0,
                        "arc_summaries": [],
                    },
                    "workspace.task_plan": "- [ ] 写第 1 章\n",
                    "workspace.findings": "",
                    "workspace.progress": "init",
                },
            ),
        )

        # G_chapter_draft：base-card-chapter-draft 作为 default writer fallback
        # 路由器若选 dark-fantasy adapter，G 走 adapter 路径；这里只在 capability
        # 模式下作为兜底 default_writer 使用，返回 workspace.chapter_text。
        reg.register(
            "base-card-chapter-draft",
            _make_stub(
                result_text="<mock default writer chapter draft>",
                state_updates={
                    "workspace.chapter_text": (
                        "【写作自检】mock\n"
                        "无明在血雾里睁开眼，记忆只剩刀柄的温度。"
                    ),
                },
            ),
        )

        # H_chapter_settle：结算章节
        reg.register(
            "base-template-chapter-settle",
            _make_stub(
                result_text="<mock chapter settle>",
                state_updates={
                    "entity_runtime.CHARACTER_STATE": {
                        "protagonist": {
                            "id": "wu_ming",
                            "name": "无明",
                            "drives": ["夺回记忆", "拆解吞噬律法", "复仇"],
                            "iq_level": "scheming",
                            "mood": "压抑",
                        },
                        "supporting": [],
                    },
                    "entity_runtime.RESOURCE_LEDGER": {
                        "particles": 1200,
                        "items": [{"type": "particles", "delta": 1200, "from": "ch1"}],
                    },
                    "entity_runtime.FORESHADOW_STATE": {
                        "pool": [
                            {"hook_id": "FH-001", "status": "tickled"},
                            {"hook_id": "FH-002", "status": "open"},
                        ],
                    },
                    "workspace.progress": "ch1_drafted",
                },
            ),
        )

        # R1_style_polish：润色 chapter_text
        reg.register(
            "base-methodology-style-polish",
            _make_stub(
                result_text="<mock polish>",
                state_updates={
                    "workspace.chapter_text": (
                        "【写作自检】polished\n"
                        "无明在血雾里睁眼，残存意识只剩刀柄上的体温——那温度像告别。"
                    ),
                },
            ),
        )

        # R2_consistency_check：写 audit_log 用 state_io.audit，不能从 state_updates 走
        # 这里 stub 返回空 state_updates；让 checker_invoker / state_io.audit 处理审计
        reg.register(
            "base-methodology-consistency-check",
            _make_stub(
                result_text="<mock consistency: OK>",
                state_updates={},
            ),
        )

        # R3_final_pack：累 GLOBAL_SUMMARY.total_words + arc_summaries
        reg.register(
            "base-methodology-final-pack",
            _make_stub(
                result_text="<mock final pack>",
                state_updates={
                    "entity_runtime.GLOBAL_SUMMARY": {
                        "total_words": 5000,
                        "arc_summaries": [
                            {"chapter": 1, "summary": "无明觉醒，第一次掠夺"},
                        ],
                    },
                },
            ),
        )

        # V1_release_check：DoD-final，不动 state（audit 由 checker 负责）
        reg.register(
            "base-checker-dod-final",
            _make_stub(
                result_text="<mock DoD: passed>",
                state_updates={},
            ),
        )

        return reg


# ---------------------------------------------------------------------------
# Internal: stub factory
# ---------------------------------------------------------------------------

def _make_stub(*, result_text: str, state_updates: Dict[str, Any]) -> CapabilityFn:
    """生成一个固定输出的 mock capability handler.

    handler 签名遵循 step_dispatch.ExecuteFn：``(inputs, ctx) -> dict``.
    返回 dict 含 ``result`` + ``state_updates``；后者会被 step_dispatch
    在 ``step.state_writes`` 白名单过滤后落入 state_io.
    """

    def _handler(inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Dict[str, Any]:  # noqa: ARG001 - mock 不用 inputs
        # 深拷贝 state_updates 避免多次调用共享同一引用（state_io 内部也会 deepcopy，但这里早隔离更安全）.
        from copy import deepcopy
        return {
            "result": result_text,
            "state_updates": deepcopy(state_updates),
        }

    return _handler


__all__ = ["CapabilityRegistry", "CapabilityNotFound", "CapabilityFn"]
