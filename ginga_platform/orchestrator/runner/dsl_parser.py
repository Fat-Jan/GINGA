"""dsl_parser — 把 workflow YAML 解析成 ``Workflow`` / ``Step`` 数据类.

输入：workflow YAML 文件路径（如
``platform/orchestrator/workflows/novel_pipeline_mvp.yaml``）.
输出：``Workflow``，其 ``steps`` 是 ``list[Step]``，每个 Step 至少含
ARCHITECTURE.md §4.4 描述的字段::

    id              : 必填
    uses_capability : 可选，资产 id (jury-2 P1 修订：用资产 id 而非路径)
    uses_skill      : 可选，"skill-router" 或具体 skill_id
    preconditions   : list[str]  形如 ["guard:no-fake-read"]
    postconditions  : list[str]  形如 ["checker:character-iq"]
    state_reads     : list[str]  state 字段路径
    state_writes    : list[str]
    description     : 可选说明

未来如果 P7-critical 在 novel_pipeline_mvp.yaml 加新字段，解析器仍向后兼容
（未识别字段保留在 ``Step.raw`` 里，不抛错）.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml


class DSLParseError(RuntimeError):
    """workflow YAML 解析失败 / schema 不合法."""


@dataclass
class Step:
    """单个 workflow step (ARCHITECTURE.md §4.4)."""

    id: str
    uses_capability: Optional[str] = None
    uses_skill: Optional[str] = None
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    state_reads: list[str] = field(default_factory=list)
    state_writes: list[str] = field(default_factory=list)
    description: str = ""
    # 透传未识别字段，避免 P7-critical 扩字段时 P7-runtime 阻塞 (向后兼容).
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_skill_step(self) -> bool:
        return bool(self.uses_skill)

    @property
    def is_capability_step(self) -> bool:
        return bool(self.uses_capability) and not self.uses_skill

    def guard_ids(self) -> list[str]:
        """从 ``preconditions`` 抽出形如 ``guard:<id>`` 的 id 列表."""
        return _strip_prefixes(self.preconditions, "guard:")

    def checker_ids(self) -> list[str]:
        """从 ``postconditions`` 抽出形如 ``checker:<id>`` 的 id 列表."""
        return _strip_prefixes(self.postconditions, "checker:")


@dataclass
class Workflow:
    """整条 workflow，按 ``steps`` 顺序执行 (transitions 留给 future Phase 2)."""

    name: str
    version: str
    steps: list[Step]
    raw: dict[str, Any] = field(default_factory=dict)

    def find(self, step_id: str) -> Optional[Step]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    @property
    def step_ids(self) -> list[str]:
        return [s.id for s in self.steps]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_workflow(path: Path | str) -> Workflow:
    """从 YAML 文件加载 ``Workflow``。"""
    fp = Path(path)
    if not fp.exists():
        raise DSLParseError(f"workflow file not found: {fp}")
    try:
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise DSLParseError(f"failed to parse {fp}: {exc}") from exc
    return parse_workflow_dict(raw)


def parse_workflow_dict(raw: Mapping[str, Any]) -> Workflow:
    """从已加载的 dict 构造 ``Workflow`` (单测便利入口)."""
    if not isinstance(raw, Mapping):
        raise DSLParseError(f"workflow root must be mapping, got {type(raw).__name__}")
    name = str(raw.get("name", "")).strip()
    if not name:
        raise DSLParseError("workflow missing required field: name")
    version = str(raw.get("version", "1.0"))
    steps_raw = raw.get("steps") or []
    if not isinstance(steps_raw, list):
        raise DSLParseError(f"workflow.steps must be list, got {type(steps_raw).__name__}")
    seen_ids: set[str] = set()
    steps: list[Step] = []
    for idx, item in enumerate(steps_raw):
        step = _parse_step(item, idx)
        if step.id in seen_ids:
            raise DSLParseError(f"duplicate step id: {step.id}")
        seen_ids.add(step.id)
        steps.append(step)
    return Workflow(name=name, version=version, steps=steps, raw=dict(raw))


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _parse_step(item: Any, idx: int) -> Step:
    if not isinstance(item, Mapping):
        raise DSLParseError(f"step[{idx}] must be mapping, got {type(item).__name__}")
    sid = str(item.get("id", "")).strip()
    if not sid:
        raise DSLParseError(f"step[{idx}] missing required field: id")
    uses_capability = item.get("uses_capability")
    uses_skill = item.get("uses_skill")
    return Step(
        id=sid,
        uses_capability=str(uses_capability) if uses_capability else None,
        uses_skill=str(uses_skill) if uses_skill else None,
        preconditions=_as_str_list(item.get("preconditions"), f"step[{sid}].preconditions"),
        postconditions=_as_str_list(item.get("postconditions"), f"step[{sid}].postconditions"),
        state_reads=_as_str_list(item.get("state_reads"), f"step[{sid}].state_reads"),
        state_writes=_as_str_list(item.get("state_writes"), f"step[{sid}].state_writes"),
        description=str(item.get("description", "")),
        raw=dict(item),
    )


def _as_str_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DSLParseError(f"{label} must be list, got {type(value).__name__}")
    return [str(x) for x in value]


def _strip_prefixes(items: list[str], prefix: str) -> list[str]:
    out: list[str] = []
    for it in items:
        if it.startswith(prefix):
            out.append(it[len(prefix):])
    return out


__all__ = [
    "Workflow",
    "Step",
    "DSLParseError",
    "parse_workflow",
    "parse_workflow_dict",
]
