"""skill_router — 在 G_chapter_draft 这种 ``uses_skill: skill-router`` 的步骤上，
按 contract.yaml 的 ``priority`` 段决议出实际跑哪个 skill (ARCHITECTURE.md §4.3).

输入：
    current_step      : dsl_parser.Step
    runtime_context   : dict（必含 ``state_io``）
    available_skills  : 由 ``platform/skills/registry.yaml`` 列出，含 enabled / contract 路径

priority 段语法 (来自 contract.yaml)::

    priority:
      - when: topic in [玄幻黑暗, 暗黑奇幻]
        score: 100
      - when: topic in [其他玄幻]
        score: 30
      - default: 0

``when`` 表达式使用受限解析器（不上 ``eval``），只支持::

    <var> == <value>
    <var> != <value>
    <var> in [<list>]
    <var> not in [<list>]
    <bool_combo with and/or>     # MVP 不上，只跑单 clause

变量名映射到 runtime_state 路径或 runtime_context 字段（按下面 ``_VAR_MAPPING``）.
默认 fallback 走 ``default_writer`` (score=0).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml


_DEFAULT_SKILLS_ROOT = Path("platform/skills")
_DEFAULT_REGISTRY_PATH = _DEFAULT_SKILLS_ROOT / "registry.yaml"
_DEFAULT_FALLBACK_SKILL = "default_writer"

# priority `when` 表达式里用到的变量 → 解析方式 (state path or context key)。
# 解析顺序：1) state_io path 命中  2) runtime_context 顶层 key  3) 返回 None.
_STATE_VAR_PATHS: dict[str, str] = {
    "topic": "locked.GENRE_LOCKED.topic",
    "style_lock": "locked.GENRE_LOCKED.style_lock",
    "premise": "locked.STORY_DNA.premise",
}


class RouterError(RuntimeError):
    """skill_router 内部错误：registry 缺失 / contract 加载失败等."""


@dataclass(frozen=True)
class RoutingDecision:
    """skill 路由决策结果."""

    skill_id: str
    score: int
    matched_rule: str = ""
    candidates: list[tuple[str, int, str]] = field(default_factory=list)


@dataclass(frozen=True)
class SkillEntry:
    """registry.yaml 一行条目（中间表示）."""

    skill_id: str
    enabled: bool
    contract_path: Path


class SkillRouter:
    """状态化路由器：构造一次，多次复用。"""

    def __init__(
        self,
        registry_path: Path | str = _DEFAULT_REGISTRY_PATH,
        skills_root: Path | str = _DEFAULT_SKILLS_ROOT,
        *,
        fallback_skill: str = _DEFAULT_FALLBACK_SKILL,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.skills_root = Path(skills_root)
        self.fallback_skill = fallback_skill
        # cache: skill_id -> priority rules (list of dict)
        self._priority_cache: dict[str, list[dict[str, Any]]] = {}

    # -- public --------------------------------------------------------------

    def route(self, current_step: Any, runtime_context: Mapping[str, Any]) -> RoutingDecision:
        """对 ``current_step``（dsl_parser.Step 或任意带 ``id`` 属性的对象）跑决议."""
        skills = self._load_registry()
        candidates: list[tuple[str, int, str]] = []
        for entry in skills:
            if not entry.enabled:
                continue
            rules = self._load_priority(entry)
            score, matched = self._evaluate(rules, runtime_context)
            candidates.append((entry.skill_id, score, matched))
        candidates.sort(key=lambda x: x[1], reverse=True)
        if not candidates or candidates[0][1] <= 0:
            return RoutingDecision(
                skill_id=self.fallback_skill,
                score=0,
                matched_rule="fallback",
                candidates=candidates,
            )
        winner = candidates[0]
        return RoutingDecision(
            skill_id=winner[0],
            score=winner[1],
            matched_rule=winner[2],
            candidates=candidates,
        )

    # -- callable convenience：用作 step_dispatch.skill_router 回调时 ----
    def __call__(self, current_step: Any, runtime_context: Mapping[str, Any]) -> str:
        return self.route(current_step, runtime_context).skill_id

    # -- internals -----------------------------------------------------------

    def _load_registry(self) -> list[SkillEntry]:
        if not self.registry_path.exists():
            # P7-critical 还没写 registry.yaml → fallback 干净返回 []，让上层走 default.
            return []
        try:
            raw = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RouterError(f"failed to parse {self.registry_path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise RouterError(f"{self.registry_path.name} must be a mapping")
        items_raw = raw.get("skills") or []
        if not isinstance(items_raw, list):
            raise RouterError(f"{self.registry_path.name}.skills must be list")
        out: list[SkillEntry] = []
        for item in items_raw:
            if not isinstance(item, Mapping):
                continue
            skill_id = str(item.get("skill_id") or item.get("id") or "").strip()
            if not skill_id:
                continue
            enabled = bool(item.get("enabled", True))
            contract_rel = item.get("contract_path") or f"{skill_id}/contract.yaml"
            contract_path = self.skills_root / contract_rel if not Path(contract_rel).is_absolute() else Path(contract_rel)
            out.append(SkillEntry(skill_id=skill_id, enabled=enabled, contract_path=contract_path))
        return out

    def _load_priority(self, entry: SkillEntry) -> list[dict[str, Any]]:
        cached = self._priority_cache.get(entry.skill_id)
        if cached is not None:
            return cached
        if not entry.contract_path.exists():
            self._priority_cache[entry.skill_id] = []
            return []
        try:
            raw = yaml.safe_load(entry.contract_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RouterError(f"failed to parse {entry.contract_path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise RouterError(f"{entry.contract_path} must be a mapping")
        priority = raw.get("priority") or []
        if not isinstance(priority, list):
            raise RouterError(f"{entry.contract_path} priority must be list")
        self._priority_cache[entry.skill_id] = list(priority)
        return self._priority_cache[entry.skill_id]

    def _evaluate(
        self,
        rules: list[dict[str, Any]],
        runtime_context: Mapping[str, Any],
    ) -> tuple[int, str]:
        """返回 (score, matched_rule_repr)；未匹配返回 ``(0, "default")``."""
        default_score: int = 0
        for rule in rules:
            if not isinstance(rule, Mapping):
                continue
            if "default" in rule:
                try:
                    default_score = int(rule["default"])
                except (TypeError, ValueError):
                    default_score = 0
                continue
            when_expr = rule.get("when")
            score_raw = rule.get("score", 0)
            try:
                score_val = int(score_raw)
            except (TypeError, ValueError):
                score_val = 0
            if when_expr is None:
                continue
            if _evaluate_when(str(when_expr), runtime_context):
                return score_val, str(when_expr)
        return default_score, "default"


# ---------------------------------------------------------------------------
# Restricted ``when`` expression evaluator
# ---------------------------------------------------------------------------

# 支持的算子（按优先级）：``not in`` / ``in`` / ``==`` / ``!=``.
_OPERATORS: tuple[str, ...] = (" not in ", " in ", " == ", " != ")


def _evaluate_when(expr: str, ctx: Mapping[str, Any]) -> bool:
    """受限解析，仅支持单子句 (no and/or for S1)."""
    expr = expr.strip()
    if not expr:
        return False
    for op in _OPERATORS:
        if op in expr:
            left, right = expr.split(op, 1)
            return _apply_op(left.strip(), op.strip(), right.strip(), ctx)
    # 无算子 → 当作 context_truthy 测试.
    return bool(_resolve_var(expr, ctx))


def _apply_op(left: str, op: str, right: str, ctx: Mapping[str, Any]) -> bool:
    lval = _resolve_var(left, ctx)
    rval = _parse_literal(right)
    if op == "==":
        return lval == rval
    if op == "!=":
        return lval != rval
    if op == "in":
        return _membership(lval, rval)
    if op == "not in":
        return not _membership(lval, rval)
    return False


def _membership(lval: Any, rval: Any) -> bool:
    if isinstance(rval, (list, tuple, set)):
        # 左值是 list → 任一元素 in rval（topic 是 string[] 时常见）.
        if isinstance(lval, (list, tuple, set)):
            return any(item in rval for item in lval)
        return lval in rval
    if isinstance(rval, str) and isinstance(lval, str):
        return lval in rval
    return False


def _resolve_var(name: str, ctx: Mapping[str, Any]) -> Any:
    state_io = ctx.get("state_io")
    if name in _STATE_VAR_PATHS and state_io is not None and hasattr(state_io, "read"):
        return state_io.read(_STATE_VAR_PATHS[name])
    if name in ctx:
        return ctx[name]
    return None


_LITERAL_LIST_RE = re.compile(r"^\[(.*)\]$")


def _parse_literal(token: str) -> Any:
    """把 ``"[a, b]"`` / ``"foo"`` / ``42`` 解析成 Python 值."""
    token = token.strip()
    if not token:
        return ""
    m = _LITERAL_LIST_RE.match(token)
    if m:
        body = m.group(1).strip()
        if not body:
            return []
        parts = [_parse_literal(p) for p in _split_top_level(body, ",")]
        return parts
    # 字符串字面量去引号.
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token[1:-1]
    # 数字 / 布尔 / null.
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False
    if token.lower() in ("null", "none"):
        return None
    try:
        if "." in token:
            return float(token)
        return int(token)
    except ValueError:
        return token  # 裸字符串（如 ``玄幻黑暗``）


def _split_top_level(s: str, sep: str) -> list[str]:
    """简单 split：不处理嵌套括号（priority list 元素本身不嵌套 list 即可）."""
    return [p.strip() for p in s.split(sep) if p.strip()]


__all__ = ["SkillRouter", "RoutingDecision", "RouterError", "SkillEntry"]
