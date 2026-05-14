"""platform.orchestrator.registry — 资产 id → 可执行能力/资产解析层 (Sprint 2 P0-1).

来源：ARCHITECTURE.md §4.2 jury-2 P1 修订：
    workflow step.uses_capability 用资产 id（不许文件路径），由 registry 解析为
    可执行函数（mock stub / 真 prompt loader / 真 LLM caller，按 sprint 演进）.

Sprint 2 阶段：mock stub（不接真原料，不调 LLM），让 12 step 能跑通；
Sprint 3 切真原料 + LLM 后，由 L Track 替换 stub。
"""

from .capability_registry import CapabilityRegistry, CapabilityNotFound

__all__ = ["CapabilityRegistry", "CapabilityNotFound"]
