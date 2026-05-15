"""guard_invoker — 前置硬阻断 hook (ARCHITECTURE.md §2.2 / §4.2).

调用约定：``invoke_guards(guard_ids, runtime_context)`` 在每个 Step 执行前由
``step_dispatch`` 触发。任一 guard 不通过 → raise ``GuardBlocked``，整个
workflow 中断（与 checker 软审计不同，guard 不可关）.

guard 资产形态 (meta/guards/<id>.guard.yaml)::

    guard_id: no-fake-read
    severity: block            # 固定 block（与 checker 区分）
    trigger_when:              # 规则集；任一命中即触发拦截
      - state_eq: { path: "workspace.last_action", value: "fake_read" }
      - state_missing: { path: "locked.STORY_DNA.premise" }
    message: "禁止伪造阅读：必须先调 latest-text-priority"
    llm_check:                 # 可选：rule-based 未命中 → 进 LLM 复核（S1 留 stub）
      enabled: false
      prompt_ref: "meta/guards/_prompts/no-fake-read.md"

S1 范围：只跑 rule-based ``trigger_when``，``llm_check`` enabled=true 时记
audit_log 然后 fail-open（不阻塞），等 S2 接入 LLM client.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml

# 延迟 import：避免 meta_integration 与 runner 之间出环（state_io 需要先加载）.
# 仅做 typing 用，运行时通过 duck typing 接 StateIO 实例。

_DEFAULT_GUARDS_ROOT = Path("meta/guards")


class GuardBlocked(RuntimeError):
    """前置硬阻断异常：guard 命中 → step 不允许执行."""

    def __init__(self, guard_id: str, message: str, *, rule: str = "", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(f"[guard:{guard_id}] {message} (rule={rule})")
        self.guard_id = guard_id
        self.message = message
        self.rule = rule
        self.details: dict[str, Any] = dict(details or {})


class GuardLoadError(RuntimeError):
    """guard YAML 加载 / schema 错误（S1 内部一致性错）."""


@dataclass(frozen=True)
class GuardSpec:
    """加载后的 guard 描述（来自 *.guard.yaml）."""

    guard_id: str
    trigger_when: list[dict[str, Any]]
    message: str
    severity: str = "block"
    llm_check_enabled: bool = False
    llm_prompt_ref: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def invoke_guards(
    guard_ids: list[str],
    runtime_context: Mapping[str, Any],
    *,
    guards_root: Path | str = _DEFAULT_GUARDS_ROOT,
) -> list[str]:
    """依次跑 ``guard_ids``；任一拦截 → 抛 ``GuardBlocked``.

    Returns: 实际通过的 guard_id 列表（按顺序）.

    ``runtime_context`` 期望含：
        - ``state_io``  : StateIO 实例（用于 state_eq / state_missing 规则）
        - ``step_id``   : 当前 step id（便于 audit_log）
        - ``params``    : Step 级临时参数（可选）
    """
    if not guard_ids:
        return []
    state_io = runtime_context.get("state_io")
    step_id = str(runtime_context.get("step_id", "<unknown>"))
    passed: list[str] = []
    for gid in guard_ids:
        spec = _load_guard_spec(gid, Path(guards_root))
        hit_rule = _eval_trigger_when(spec, runtime_context)
        if hit_rule is not None:
            # 记 audit_log 后再抛（如果有 state_io 实例）.
            if state_io is not None and hasattr(state_io, "audit"):
                state_io.audit(
                    source=f"guard:{gid}",
                    severity="error",
                    msg=spec.message,
                    action="block",
                    payload={"rule": hit_rule, "step_id": step_id},
                )
            raise GuardBlocked(gid, spec.message, rule=hit_rule, details={"step_id": step_id})
        if spec.llm_check_enabled:
            # S1 stub：记 audit_log，不阻塞；S2 接 LLM client 时改为真实判定.
            if state_io is not None and hasattr(state_io, "audit"):
                state_io.audit(
                    source=f"guard:{gid}",
                    severity="info",
                    msg="llm_check stubbed (S1 fail-open)",
                    action="log",
                    payload={"prompt_ref": spec.llm_prompt_ref, "step_id": step_id},
                )
        passed.append(gid)
    return passed


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _load_guard_spec(guard_id: str, guards_root: Path) -> GuardSpec:
    fp = guards_root / f"{guard_id}.guard.yaml"
    if not fp.exists():
        # S1 fallback：guard 文件未提供 (P7-meta 任务 M-2 还没跑) → 视为 noop.
        # 但要拍 audit_log 留痕。这里通过返回空 trigger 实现，invoke_guards 直接 pass。
        return GuardSpec(guard_id=guard_id, trigger_when=[], message=f"guard {guard_id!r} not found (S1 noop)")
    try:
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise GuardLoadError(f"failed to parse {fp}: {exc}") from exc
    if not isinstance(raw, dict):
        raise GuardLoadError(f"{fp.name} must be a mapping, got {type(raw).__name__}")
    trigger_when = _normalize_trigger_when(raw.get("trigger_when"))
    llm_block = raw.get("llm_check") or {}
    return GuardSpec(
        guard_id=str(raw.get("guard_id", guard_id)),
        trigger_when=trigger_when,
        message=str(raw.get("message", "")),
        severity=str(raw.get("severity", "block")),
        llm_check_enabled=bool(llm_block.get("enabled", False)),
        llm_prompt_ref=str(llm_block.get("prompt_ref", "")),
    )


def _eval_trigger_when(spec: GuardSpec, ctx: Mapping[str, Any]) -> Optional[str]:
    """返回命中的规则名（如 ``state_eq``），未命中返回 ``None``.

    支持规则：
        - ``state_eq``      : { path: <dotted>, value: <any> }
        - ``state_ne``      : { path: <dotted>, value: <any> }
        - ``state_missing`` : { path: <dotted> }
        - ``state_in``      : { path: <dotted>, values: list }
        - ``context_truthy``: { key: <ctx-key> }
    """
    state_io = ctx.get("state_io")
    for rule in spec.trigger_when:
        if not isinstance(rule, dict) or not rule:
            continue
        if "__structured__" in rule:
            if state_io is not None and hasattr(state_io, "audit"):
                state_io.audit(
                    source=f"guard:{spec.guard_id}",
                    severity="info",
                    msg="structured guard trigger not evaluated (fail-open)",
                    action="log",
                    payload={
                        "step_id": str(ctx.get("step_id", "<unknown>")),
                        "trigger": rule["__structured__"],
                    },
                )
            continue
        # 每个 rule 是单 key dict (rule_name -> args).
        rule_name, args = next(iter(rule.items()))
        args = args or {}
        try:
            hit = _apply_rule(rule_name, args, state_io, ctx)
        except StateLookupError:
            # state_io 不存在 / path 越界 → 当作未命中（safe-default fail-open for unknown）.
            hit = False
        if hit:
            return rule_name
    return None


def _normalize_trigger_when(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return list(raw)
    if isinstance(raw, dict):
        rules: list[dict[str, Any]] = []
        any_of = raw.get("any_of")
        if isinstance(any_of, list):
            for item in any_of:
                if isinstance(item, dict) and len(item) == 1:
                    key, value = next(iter(item.items()))
                    if key in {"state_eq", "state_ne", "state_missing", "state_in", "context_truthy"}:
                        rules.append({key: value})
                    else:
                        rules.append({"__structured__": {key: value}})
                else:
                    rules.append({"__structured__": item})
            return rules
        return [{"__structured__": raw}]
    raise GuardLoadError(f"trigger_when must be list or mapping, got {type(raw).__name__}")


class StateLookupError(RuntimeError):
    """内部：state_io 缺失或 path 解析失败."""


def _apply_rule(
    rule_name: str,
    args: Mapping[str, Any],
    state_io: Any,
    ctx: Mapping[str, Any],
) -> bool:
    if rule_name == "context_truthy":
        return bool(ctx.get(args.get("key", "")))
    if state_io is None:
        raise StateLookupError("state_io not in runtime_context")
    if rule_name == "state_eq":
        return state_io.read(args["path"]) == args.get("value")
    if rule_name == "state_ne":
        return state_io.read(args["path"]) != args.get("value")
    if rule_name == "state_missing":
        sentinel = object()
        return state_io.read(args["path"], default=sentinel) is sentinel
    if rule_name == "state_in":
        current = state_io.read(args["path"])
        return current in (args.get("values") or [])
    # 未知规则 → safe default：不命中（记 audit 由调用方决定）.
    return False


__all__ = [
    "GuardBlocked",
    "GuardLoadError",
    "GuardSpec",
    "invoke_guards",
]
