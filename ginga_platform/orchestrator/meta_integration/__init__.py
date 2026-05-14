"""platform.orchestrator.meta_integration — guard (前置硬阻断) + checker (后置软审计).

guard 来自 meta/guards/*.guard.yaml，由 Orchestrator 在 step.preconditions 触发；
checker 来自 meta/checkers/*.checker.yaml，由 Orchestrator 在 step.postconditions
触发，默认 warn-only，作家可通过 meta/user_overrides/checker_mode.yaml 切 block.

详见 ARCHITECTURE.md §2.2 / §4.2.
"""

from .guard_invoker import invoke_guards, GuardBlocked
from .checker_invoker import invoke_checkers, CheckerBlocked

__all__ = [
    "invoke_guards",
    "GuardBlocked",
    "invoke_checkers",
    "CheckerBlocked",
]
