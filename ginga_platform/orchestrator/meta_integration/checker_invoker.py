"""checker_invoker — 后置软审计 hook (ARCHITECTURE.md §2.2 / §4.2).

调用约定：``invoke_checkers(checker_ids, step_output, runtime_context)`` 在每个
Step 输出后由 ``step_dispatch`` 触发。默认 ``mode=warn`` 仅记 ``audit_log``，作家
可通过 ``meta/user_overrides/checker_mode.yaml`` 切 ``block``（命中 → 抛
``CheckerBlocked``）或 ``off``（完全跳过）.

checker 资产形态 (meta/checkers/<id>.checker.yaml)::

    checker_id: aigc-style-detector
    default_mode: warn         # warn / block / off
    severity: warn
    check_logic:               # 规则集；任一命中即触发
      - output_contains: { keywords: ["显然", "诚然"], any: true }
      - state_eq: { path: "locked.GENRE_LOCKED.topic", value: "玄幻黑暗" }
    message: "AIGC 套话痕迹疑似过重，请人工复核"
    llm_check:
      enabled: false
      prompt_ref: "meta/checkers/_prompts/aigc-style-detector.md"

user override 形态 (meta/user_overrides/checker_mode.yaml)::

    aigc-style-detector: warn
    character-iq-checker: block
    cool-point-payoff-checker: off

未列出的 checker_id 走 ``default_mode``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import yaml

_DEFAULT_CHECKERS_ROOT = Path("meta/checkers")
_DEFAULT_OVERRIDES_PATH = Path("meta/user_overrides/checker_mode.yaml")
_VALID_MODES = ("off", "warn", "block")


class CheckerBlocked(RuntimeError):
    """后置软审计在 block 模式下命中 → 抛此异常."""

    def __init__(self, checker_id: str, message: str, *, rule: str = "", details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(f"[checker:{checker_id}] {message} (rule={rule})")
        self.checker_id = checker_id
        self.message = message
        self.rule = rule
        self.details: dict[str, Any] = dict(details or {})


class CheckerLoadError(RuntimeError):
    """checker YAML 加载 / schema 错误."""


@dataclass(frozen=True)
class CheckerSpec:
    """加载后的 checker 描述."""

    checker_id: str
    check_logic: list[dict[str, Any]]
    message: str
    default_mode: str = "warn"
    severity: str = "warn"
    llm_check_enabled: bool = False
    llm_prompt_ref: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def invoke_checkers(
    checker_ids: list[str],
    step_output: Mapping[str, Any],
    runtime_context: Mapping[str, Any],
    *,
    checkers_root: Path | str = _DEFAULT_CHECKERS_ROOT,
    overrides_path: Path | str = _DEFAULT_OVERRIDES_PATH,
) -> list[dict[str, Any]]:
    """依次跑 ``checker_ids``，返回每个 checker 的结果列表.

    每项形如 ``{"checker_id": ..., "mode": ..., "hit_rule": ..., "severity": ...}``.

    - ``mode=off``  → 完全跳过，结果项 ``hit_rule=None / mode=off``.
    - ``mode=warn`` → 命中只写 audit_log，``severity=warn``，不抛异常.
    - ``mode=block``→ 命中抛 ``CheckerBlocked``；否则只写 audit_log info.
    """
    if not checker_ids:
        return []
    state_io = runtime_context.get("state_io")
    step_id = str(runtime_context.get("step_id", "<unknown>"))

    # immersive_mode silenced hook (ARCHITECTURE.md §4.5 / dark-fantasy contract.immersive_mode).
    # 当 workspace.workflow_flags.checker_silenced=True 时全部 checker 直接 off，
    # 仅写一条 audit "checker silenced (immersive)"；避免每 checker 都 audit 一遍噪音.
    if state_io is not None and hasattr(state_io, "read"):
        try:
            silenced = bool(state_io.read("workspace.workflow_flags.checker_silenced", False))
        except Exception:
            silenced = False
        if silenced:
            if hasattr(state_io, "audit"):
                state_io.audit(
                    source="checker_invoker",
                    severity="info",
                    msg="checker silenced (immersive)",
                    action="log",
                    payload={"step_id": step_id, "checker_ids": list(checker_ids)},
                )
            return [
                {"checker_id": cid, "mode": "off", "hit_rule": None, "severity": "info",
                 "silenced": True}
                for cid in checker_ids
            ]

    overrides = _load_overrides(Path(overrides_path))
    results: list[dict[str, Any]] = []
    for cid in checker_ids:
        spec = _load_checker_spec(cid, Path(checkers_root))
        mode = overrides.get(cid, spec.default_mode)
        if mode not in _VALID_MODES:
            mode = "warn"
        if mode == "off":
            results.append({"checker_id": cid, "mode": "off", "hit_rule": None, "severity": "info"})
            continue
        hit_rule = _eval_check_logic(spec, step_output, runtime_context)
        result = {"checker_id": cid, "mode": mode, "hit_rule": hit_rule, "severity": spec.severity}
        results.append(result)
        if hit_rule is None:
            # 未命中：默认不写 audit_log（避免噪音），block 模式下也只是放行.
            continue
        # 命中：先写 audit_log.
        if state_io is not None and hasattr(state_io, "audit"):
            state_io.audit(
                source=f"checker:{cid}",
                severity=("error" if mode == "block" else "warn"),
                msg=spec.message,
                action=("block" if mode == "block" else "log"),
                payload={"rule": hit_rule, "step_id": step_id, "mode": mode},
            )
        if mode == "block":
            raise CheckerBlocked(cid, spec.message, rule=hit_rule, details={"step_id": step_id, "mode": mode})
    return results


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _load_overrides(fp: Path) -> dict[str, str]:
    if not fp.exists():
        return {}
    try:
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CheckerLoadError(f"failed to parse {fp}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CheckerLoadError(f"{fp.name} must be a mapping, got {type(raw).__name__}")
    return {str(k): str(v) for k, v in raw.items()}


def _load_checker_spec(checker_id: str, checkers_root: Path) -> CheckerSpec:
    fp = checkers_root / f"{checker_id}.checker.yaml"
    if not fp.exists():
        # S1 fallback：checker 未提供 → 当作 default warn + 空规则（永不命中）.
        return CheckerSpec(
            checker_id=checker_id,
            check_logic=[],
            message=f"checker {checker_id!r} not found (S1 noop)",
            default_mode="warn",
            severity="warn",
        )
    try:
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise CheckerLoadError(f"failed to parse {fp}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CheckerLoadError(f"{fp.name} must be a mapping, got {type(raw).__name__}")
    check_logic = raw.get("check_logic") or []
    if not isinstance(check_logic, list):
        raise CheckerLoadError(f"{fp.name} check_logic must be list, got {type(check_logic).__name__}")
    llm_block = raw.get("llm_check") or {}
    return CheckerSpec(
        checker_id=str(raw.get("checker_id", checker_id)),
        check_logic=list(check_logic),
        message=str(raw.get("message", "")),
        default_mode=str(raw.get("default_mode", "warn")),
        severity=str(raw.get("severity", "warn")),
        llm_check_enabled=bool(llm_block.get("enabled", False)),
        llm_prompt_ref=str(llm_block.get("prompt_ref", "")),
    )


def _eval_check_logic(
    spec: CheckerSpec,
    step_output: Mapping[str, Any],
    ctx: Mapping[str, Any],
) -> Optional[str]:
    """命中规则返回规则名，否则 ``None``.

    支持规则：
        - ``output_contains`` : { keywords: [str], any: bool=true }
        - ``output_missing``  : { keys: [str] }
        - ``state_eq``        : { path: <dotted>, value: <any> }
        - ``output_word_count_lt`` : { key: <output key>, min: int }
    """
    state_io = ctx.get("state_io")
    for rule in spec.check_logic:
        if not isinstance(rule, dict) or not rule:
            continue
        rule_name, args = next(iter(rule.items()))
        args = args or {}
        try:
            hit = _apply_check_rule(rule_name, args, step_output, state_io)
        except Exception:
            hit = False
        if hit:
            return rule_name
    return None


def _apply_check_rule(
    rule_name: str,
    args: Mapping[str, Any],
    step_output: Mapping[str, Any],
    state_io: Any,
) -> bool:
    if rule_name == "output_contains":
        keywords = args.get("keywords") or []
        any_mode = bool(args.get("any", True))
        haystack = _stringify_output(step_output)
        hits = [kw for kw in keywords if kw in haystack]
        return bool(hits) if any_mode else len(hits) == len(keywords)
    if rule_name == "output_missing":
        keys = args.get("keys") or []
        return any(k not in step_output for k in keys)
    if rule_name == "output_word_count_lt":
        key = args.get("key", "chapter_text")
        minimum = int(args.get("min", 0))
        text = step_output.get(key, "") or ""
        return len(str(text)) < minimum
    if rule_name == "state_eq":
        if state_io is None:
            return False
        return state_io.read(args["path"]) == args.get("value")
    return False


def _stringify_output(step_output: Mapping[str, Any]) -> str:
    """把 step_output 拍平成一个大字符串供 contains 匹配。"""
    parts: list[str] = []
    for v in step_output.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, (list, tuple)):
            parts.extend(str(x) for x in v)
        else:
            parts.append(str(v))
    return "\n".join(parts)


__all__ = [
    "CheckerBlocked",
    "CheckerLoadError",
    "CheckerSpec",
    "invoke_checkers",
]
