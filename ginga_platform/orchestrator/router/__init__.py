"""platform.orchestrator.router — skill router (按 contract.yaml priority 选 skill).

skill_router 读取 platform/skills/registry.yaml + 每个 enabled skill 的
contract.yaml priority 段，再结合当前 runtime_state（如 locked.GENRE_LOCKED.topic）
决定 G_chapter_draft 走哪个 skill。详见 ARCHITECTURE.md §4.3.
"""

from .skill_router import SkillRouter, RoutingDecision, RouterError

__all__ = ["SkillRouter", "RoutingDecision", "RouterError"]
