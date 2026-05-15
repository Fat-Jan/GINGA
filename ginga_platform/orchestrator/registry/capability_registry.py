"""capability_registry — 资产 id → 可执行函数的注册中心.

来源：ARCHITECTURE.md §4.2（uses_capability 用资产 id，由 registry 解析）+
ROADMAP §二 Sprint 2 + .ops/p7-prompts/ST-S2-PHASE0.md.

定位：
    workflow YAML 的 step.uses_capability 字段是「资产 id」（如
    ``base-template-protagonist``），不是文件路径；本模块负责把 id 解析为
    实际可执行的 callable，再由 step_dispatch 调用。

当前边界：
    - ``from_defaults`` 注册 asset-backed deterministic providers：每个
      capability 解析 ``foundation/assets/capabilities`` 中的资产卡，并基于
      workflow inputs / runtime_context 返回 state_updates
    - provider 不直接写 ``StateIO``，不调真实 LLM；真实正文生成仍在 CLI
      demo / multi_chapter / immersive runner 的 LLM 或 skill adapter 路径中

返回格式约定（与 step_dispatch._apply_state_writes 对齐）::

    callable(inputs: Mapping[str, Any], context: Mapping[str, Any]) -> dict
    返回值必须含：
        provider      : "asset-backed"
        asset_ref     : dict（可审计资产来源）
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
        """Register the MVP 12-step asset-backed default capability providers.

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

        每个 provider 返回 ``provider=asset-backed`` 与 ``asset_ref``，并只通过
        ``state_updates`` 暴露待写状态；实际写入仍由 ``step_dispatch`` 和
        ``StateIO`` 负责。
        """
        reg = cls()
        from .asset_providers import build_asset_capability_providers

        for capability_id, handler in build_asset_capability_providers().items():
            reg.register(capability_id, handler)

        return reg


__all__ = ["CapabilityRegistry", "CapabilityNotFound", "CapabilityFn"]
