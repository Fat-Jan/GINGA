"""step_dispatch — 单个 ``Step`` 的执行编排：guard → capability/skill → checker.

调用顺序 (ARCHITECTURE.md §4.2)::

    1. invoke_guards(step.guard_ids(), context)         # preconditions
    2. 解析 uses_capability / uses_skill：
       - uses_capability → 通过 ``capability_registry`` 解析为 callable
       - uses_skill="skill-router" → 通过 ``skill_router`` 决议出 skill_id，再调 adapter
       - uses_skill=<concrete> → 直接调对应 adapter
    3. invoke_checkers(step.checker_ids(), output, context)  # postconditions

任一 guard 命中 → ``GuardBlocked`` 中断；capability/skill 执行抛任何异常都被包成
``StepFailed``；checker 在 warn 模式只记 audit_log，block 模式抛 ``CheckerBlocked``
（向上层 workflow 暴露）.

state 读写约定：
  - 在 step 开始时把 ``step.state_reads`` 读出来放进 ``inputs`` 字典
  - 在 step 结束时检查 capability/skill 返回的 ``state_updates``，只允许写
    ``step.state_writes`` 列出的路径（防止 skill 越权改 state）
  - 所有 state 操作必须经 ``StateIO``，不允许绕过 (jury-1 P0 强约束)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from .dsl_parser import Step
from .state_io import StateIO
from ..meta_integration.guard_invoker import invoke_guards, GuardBlocked
from ..meta_integration.checker_invoker import invoke_checkers, CheckerBlocked


class StepFailed(RuntimeError):
    """capability / skill 执行失败的统一异常."""

    def __init__(self, step_id: str, reason: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(f"[step:{step_id}] {reason}")
        self.step_id = step_id
        self.reason = reason
        self.__cause__ = cause


# 类型约定：capability / skill 执行体均接 (inputs, context) → output_dict.
# output_dict 至少含 "result" 字段，可选 "state_updates": {<path>: <value>}.
ExecuteFn = Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class DispatchResult:
    """单 step 的执行结果摘要."""

    step_id: str
    used: str                       # "capability:<id>" / "skill:<id>" / "noop"
    output: dict[str, Any] = field(default_factory=dict)
    guards_passed: list[str] = field(default_factory=list)
    checker_results: list[dict[str, Any]] = field(default_factory=list)
    state_writes_applied: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def dispatch_step(
    step: Step,
    runtime_context: dict[str, Any],
    *,
    capability_registry: Optional[Mapping[str, ExecuteFn]] = None,
    skill_registry: Optional[Mapping[str, ExecuteFn]] = None,
    skill_router: Optional[Callable[[Step, Mapping[str, Any]], str]] = None,
) -> DispatchResult:
    """按 §4.2 顺序执行单 step.

    ``runtime_context`` 必含 ``state_io: StateIO``（jury-1 P0 强约束）.
    可选键：``book_id`` / ``params`` / 其他上下文.
    ``capability_registry`` / ``skill_registry`` 是 P7-critical 注册的 adapter 表。
    P2-7 收敛后缺失注册项默认 fail-loud；只有显式
    ``execution_mode="dev/noop_allowed"`` 才保留旧 S1 noop 行为。
    """
    state_io = runtime_context.get("state_io")
    if not isinstance(state_io, StateIO):
        raise StepFailed(step.id, "runtime_context.state_io must be StateIO instance")
    # 注入 step_id 给 guard/checker 用.
    ctx = dict(runtime_context)
    ctx["step_id"] = step.id

    # 1. preconditions: guards (前置硬阻断).
    try:
        guards_passed = invoke_guards(step.guard_ids(), ctx)
    except GuardBlocked:
        # 上层 workflow 自己接 GuardBlocked，不在这里降级。
        raise

    # 2. 执行 capability / skill.
    inputs = _gather_inputs(step, state_io)
    # 2.5 RAG hook (ST-S2-R / ARCHITECTURE §5.3): respect runtime_state.workflow_flags.rag_mode.
    _inject_rag_cards(step, ctx, inputs, state_io)
    output, used = _execute_body(
        step,
        inputs,
        ctx,
        capability_registry=capability_registry or {},
        skill_registry=skill_registry or {},
        skill_router=skill_router,
    )

    # 3. 把 state_updates 落到 StateIO（仅限 step.state_writes 内）.
    writes_applied = _apply_state_writes(step, output, state_io)
    audit_intents_applied = _apply_audit_intents(step, output, state_io)

    # 4. postconditions: checkers (后置软审计).
    try:
        checker_results = invoke_checkers(step.checker_ids(), output, ctx)
    except CheckerBlocked:
        # block 模式被触发，已经写过 audit_log，向上层抛.
        raise

    state_io.audit(
        source=f"step_dispatch:{step.id}",
        severity="info",
        msg=f"step {step.id} completed",
        action="log",
        payload={
            "used": used,
            "guards_passed": guards_passed,
            "writes_applied": writes_applied,
            "audit_intents_applied": audit_intents_applied,
            "checker_results": checker_results,
        },
    )

    return DispatchResult(
        step_id=step.id,
        used=used,
        output=dict(output),
        guards_passed=guards_passed,
        checker_results=checker_results,
        state_writes_applied=writes_applied,
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _gather_inputs(step: Step, state_io: StateIO) -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    for path in step.state_reads:
        if path == "audit_log":
            inputs[path] = list(state_io.audit_log)
            continue
        # 支持 wildcard "<domain>.*"：直接读整域（dispatch 不做更复杂模式匹配）.
        if path.endswith(".*"):
            domain = path[:-2]
            inputs[domain] = state_io.read(domain)
        else:
            inputs[path] = state_io.read(path)
    return inputs


def _execute_body(
    step: Step,
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    *,
    capability_registry: Mapping[str, ExecuteFn],
    skill_registry: Mapping[str, ExecuteFn],
    skill_router: Optional[Callable[[Step, Mapping[str, Any]], str]],
) -> tuple[Mapping[str, Any], str]:
    if step.is_capability_step:
        cap = step.uses_capability or ""
        fn = capability_registry.get(cap)
        if fn is None:
            if _noop_allowed(ctx):
                return ({"result": None, "note": f"capability {cap!r} not registered (dev noop)"}, f"capability:{cap}")
            raise StepFailed(step.id, f"capability not registered: {cap!r}")
        return (_safe_call(fn, step.id, inputs, ctx), f"capability:{cap}")

    if step.is_skill_step:
        wanted = step.uses_skill or ""
        if wanted == "skill-router":
            if skill_router is None:
                if _noop_allowed(ctx):
                    return ({"result": None, "note": "skill_router not provided (dev noop)"}, "skill:default_writer")
                raise StepFailed(step.id, "skill_router not provided")
            chosen = skill_router(step, ctx) or "default_writer"
        else:
            chosen = wanted
        fn = skill_registry.get(chosen)
        if fn is None:
            if _noop_allowed(ctx):
                return ({"result": None, "note": f"skill {chosen!r} not registered (dev noop)"}, f"skill:{chosen}")
            raise StepFailed(step.id, f"skill not registered: {chosen!r}")
        return (_safe_call(fn, step.id, inputs, ctx), f"skill:{chosen}")

    # 既不 uses_capability 也不 uses_skill：当作纯 state-only step (如 F_state_init).
    return ({"result": None, "note": "no-op step (state-only)"}, "noop")


def _noop_allowed(ctx: Mapping[str, Any]) -> bool:
    return str(ctx.get("execution_mode") or ctx.get("mode") or "") == "dev/noop_allowed"


def _safe_call(
    fn: ExecuteFn,
    step_id: str,
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
) -> Mapping[str, Any]:
    try:
        result = fn(inputs, ctx)
    except Exception as exc:
        raise StepFailed(step_id, f"capability/skill raised {type(exc).__name__}: {exc}", cause=exc) from exc
    if not isinstance(result, Mapping):
        raise StepFailed(step_id, f"capability/skill must return mapping, got {type(result).__name__}")
    return result


def _apply_state_writes(step: Step, output: Mapping[str, Any], state_io: StateIO) -> list[str]:
    updates = output.get("state_updates") or {}
    if not updates:
        return []
    if not isinstance(updates, Mapping):
        raise StepFailed(step.id, f"state_updates must be mapping, got {type(updates).__name__}")
    allowed = set(step.state_writes)
    # state_writes 支持 wildcard ``entity_runtime.*``；命中规则：path 以 prefix 开头.
    wildcards = {w[:-2] for w in allowed if w.endswith(".*")}
    concrete = {w for w in allowed if not w.endswith(".*")}
    filtered: dict[str, Any] = {}
    rejected: list[str] = []
    for path, value in updates.items():
        if path in concrete or any(path.startswith(w + ".") or path == w for w in wildcards):
            filtered[path] = value
        else:
            rejected.append(path)
    if rejected:
        state_io.audit(
            source=f"step_dispatch:{step.id}",
            severity="warn",
            msg=f"state writes rejected (outside step.state_writes)",
            action="log",
            payload={"rejected": rejected, "allowed": list(allowed)},
        )
    if filtered:
        state_io.apply(filtered, source=f"step_dispatch:{step.id}")
    return list(filtered.keys())


def _apply_audit_intents(step: Step, output: Mapping[str, Any], state_io: StateIO) -> int:
    intents = output.get("audit_intents") or []
    if not intents:
        return 0
    if not isinstance(intents, list):
        raise StepFailed(step.id, f"audit_intents must be list, got {type(intents).__name__}")
    applied = 0
    for idx, intent in enumerate(intents):
        if not isinstance(intent, Mapping):
            raise StepFailed(step.id, f"audit_intents[{idx}] must be mapping, got {type(intent).__name__}")
        payload = intent.get("payload") if isinstance(intent.get("payload"), Mapping) else {}
        state_io.audit(
            source=str(intent.get("source") or f"step_dispatch:{step.id}:audit_intent"),
            severity=str(intent.get("severity") or "info"),
            msg=str(intent.get("msg") or ""),
            action=str(intent.get("action") or "log"),
            payload=dict(payload),
        )
        applied += 1
    return applied



# ---------------------------------------------------------------------------
# RAG hook (R-5, ARCHITECTURE §5.3 / jury-3 P1)
# ---------------------------------------------------------------------------

def _inject_rag_cards(
    step: Step,
    ctx: Mapping[str, Any],
    inputs: dict[str, Any],
    state_io: StateIO,
) -> None:
    """根据 ``ctx['workflow_flags']['rag_mode']`` 决定是否注入 RAG 召回卡片.

    模式:
      - ``rag_mode="off"`` → 不调召回，audit info "rag disabled by user".
      - ``rag_mode="on"`` / 缺省 → 调 ``rag.retriever.recall_cards`` 注入
        ``inputs["retrieved.cards"]``.

    fail-safe: 召回模块异常 → 写 audit warn，``retrieved.cards`` 保持空 list；
    **不会** 让 step 主流程失败 (rag 故障不算 step 失败).
    """
    flags = ctx.get("workflow_flags") if isinstance(ctx, Mapping) else None
    if not isinstance(flags, Mapping):
        flags = {}
    mode = str(flags.get("rag_mode", "on")).lower()
    if mode == "off":
        state_io.audit(
            source=f"step_dispatch:{step.id}:rag",
            severity="info",
            msg="rag disabled by user (workflow_flags.rag_mode=off)",
            action="log",
        )
        inputs.setdefault("retrieved.cards", [])
        return

    hint = step.raw.get("retrieval_hint") if isinstance(step.raw, Mapping) else None
    if not isinstance(hint, Mapping):
        hint = {}
    try:
        from rag.retriever import recall_cards as _recall_cards  # lazy import; rag is optional at S1.
    except Exception as exc:  # noqa: BLE001 — fail-safe: rag missing
        state_io.audit(
            source=f"step_dispatch:{step.id}:rag",
            severity="warn",
            msg=f"rag module not importable: {type(exc).__name__}: {exc}",
            action="log",
        )
        inputs.setdefault("retrieved.cards", [])
        return

    try:
        result = _recall_cards(
            stage=hint.get("stage"),
            topic=hint.get("topic"),
            asset_type=hint.get("asset_type"),
            card_intent=hint.get("card_intent"),
            query_text=str(hint.get("query_text") or inputs.get("query_text") or ""),
            top_k=hint.get("top_k"),
            candidate_k=hint.get("candidate_k"),
            quality_floor=hint.get("quality_floor", "B"),
            index_path=hint.get("index_path"),
            config=ctx.get("rag_config") if isinstance(ctx.get("rag_config"), dict) else None,
            embedder=ctx.get("rag_embedder"),
            llm_caller=ctx.get("rag_llm_caller"),
        )
        cards = result.get("cards", []) if isinstance(result, Mapping) else []
        diagnostics = result.get("diagnostics", {}) if isinstance(result, Mapping) else {}
    except Exception as exc:  # noqa: BLE001 — fail-safe: bad index / config
        state_io.audit(
            source=f"step_dispatch:{step.id}:rag",
            severity="warn",
            msg=f"rag recall failed: {type(exc).__name__}: {exc}",
            action="log",
        )
        inputs.setdefault("retrieved.cards", [])
        return

    inputs["retrieved.cards"] = list(cards)
    state_io.audit(
        source=f"step_dispatch:{step.id}:rag",
        severity="info",
        msg=f"rag recall injected {len(cards)} card(s)",
        action="log",
        payload={"hint": dict(hint), "count": len(cards), "diagnostics": diagnostics},
    )


__all__ = [
    "StepFailed",
    "DispatchResult",
    "ExecuteFn",
    "dispatch_step",
]
