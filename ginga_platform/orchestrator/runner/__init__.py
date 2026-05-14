"""platform.orchestrator.runner — workflow DSL → 命令式 dispatch + state IO.

Modules:
    dsl_parser     YAML workflow → Workflow / Step dataclass.
    step_dispatch  顺序执行 Step：guard → capability/skill → checker.
    state_io       runtime_state 的唯一读写入口 (jury-1 P0 强约束).
"""

from .dsl_parser import Workflow, Step, parse_workflow
from .state_io import StateIO
from .step_dispatch import dispatch_step, StepFailed

__all__ = [
    "Workflow",
    "Step",
    "parse_workflow",
    "StateIO",
    "dispatch_step",
    "StepFailed",
]
