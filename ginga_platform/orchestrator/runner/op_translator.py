"""op_translator — adapter list-of-ops → state_io flat dict 转换器 (ST-S2-PHASE0 P0-2).

来源：ARCHITECTURE.md §4.3 (skill adapter output_transform 返回 list of ops) +
state_io.py (apply 接受 flat dict {path: value}) + .ops/p7-prompts/ST-S2-PHASE0.md.

背景：
    dark-fantasy adapter.output_transform 返回 ``list[dict]``，每条形如::

        {"op": "delta" | "append" | "append_or_update" | "write",
         "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
         "value": <...>,
         "key": "<match key for append_or_update>"   # 可选
        }

    state_io.apply 期望::

        {"entity_runtime.RESOURCE_LEDGER.particles": <new_value>, ...}

    本模块负责：
        1. path 规范化：剥 ``runtime_state.`` 前缀；裸 ``chapter_text`` 映射到
           ``workspace.chapter_text``（state_io 顶层域不收 ``chapter_text``）
        2. delta / append / append_or_update：需要读旧值后算新值，再 write 出去
        3. 同 path 多 op 合并：后一个 op 基于前一个 op 算出来的临时值继续算
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Dict, List, Mapping

if TYPE_CHECKING:  # 仅类型注解使用，避免运行时循环 import
    from .state_io import StateIO


# 顶层域映射：adapter 用的 path 前缀 → state_io 合法顶层域
_RUNTIME_STATE_PREFIX = "runtime_state."

# 裸 path（无 runtime_state 前缀、且顶层不是 state_io 域）映射到 workspace 子域
# 让 12 step workflow 里的 "chapter_text" 这样的字段也能落盘
_BARE_PATH_MAPPING: Dict[str, str] = {
    "chapter_text": "workspace.chapter_text",
}

# state_io 的合法顶层域（从 state_io.py 反查；不直接 import 避免循环依赖）
_VALID_STATE_DOMAINS: tuple[str, ...] = (
    "locked", "entity_runtime", "workspace", "retrieved",
)


class OpTranslationError(ValueError):
    """op 翻译失败：op 名未知 / path 非法 / value 类型不匹配等."""


def adapter_ops_to_state_updates(
    ops: List[Mapping[str, Any]],
    state_io: "StateIO",
) -> Dict[str, Any]:
    """把 adapter.output_transform 的 list-of-ops 转成 state_io.apply 用的 flat dict.

    Args:
        ops: adapter 返回的 op 列表，每条至少含 ``op`` / ``path`` / ``value``；
             ``append_or_update`` 额外要求 ``key`` 字段（list 元素的 match 键）.
        state_io: state_io 实例，用于读旧值（delta/append/append_or_update 需要）.

    Returns:
        flat dict ``{normalized_path: new_value}``，可直接喂给
        ``state_io.apply(flat_dict)``.

    Raises:
        OpTranslationError: op 未识别 / path 非法 / value 类型与 op 不匹配.

    同一 path 多 op 时，后续 op 基于"前面 op 算出的中间值"继续累加 / 追加，
    保证最终落到 state_io 的是合并后的终值（避免 apply 时被后写覆盖）.
    """
    if not isinstance(ops, list):
        raise OpTranslationError(f"ops must be list, got {type(ops).__name__}")

    pending: Dict[str, Any] = {}

    for idx, op_entry in enumerate(ops):
        if not isinstance(op_entry, Mapping):
            raise OpTranslationError(f"ops[{idx}] must be mapping, got {type(op_entry).__name__}")
        op_name = op_entry.get("op")
        raw_path = op_entry.get("path")
        value = op_entry.get("value")
        if not op_name or not isinstance(op_name, str):
            raise OpTranslationError(f"ops[{idx}].op must be non-empty str, got {op_name!r}")
        if not raw_path or not isinstance(raw_path, str):
            raise OpTranslationError(f"ops[{idx}].path must be non-empty str, got {raw_path!r}")

        norm_path = _normalize_path(raw_path)

        # 取「当前」值：优先 pending（同 path 链式），fallback 到 state_io.
        if norm_path in pending:
            current = copy.deepcopy(pending[norm_path])
        else:
            current = state_io.read(norm_path)

        if op_name == "write":
            new_value = copy.deepcopy(value)
        elif op_name == "delta":
            new_value = _apply_delta(current, value, path=norm_path, idx=idx)
        elif op_name == "append":
            new_value = _apply_append(current, value, path=norm_path, idx=idx)
        elif op_name == "append_or_update":
            match_key = op_entry.get("key")
            if not match_key or not isinstance(match_key, str):
                raise OpTranslationError(
                    f"ops[{idx}] op=append_or_update requires non-empty 'key' field, got {match_key!r}"
                )
            new_value = _apply_append_or_update(
                current, value, match_key=match_key, path=norm_path, idx=idx
            )
        else:
            raise OpTranslationError(
                f"ops[{idx}] unknown op {op_name!r}; expected one of write/delta/append/append_or_update"
            )

        pending[norm_path] = new_value

    return pending


# ---------------------------------------------------------------------------
# Internals: path normalization
# ---------------------------------------------------------------------------

def _normalize_path(raw_path: str) -> str:
    """把 adapter 的 path 规范化成 state_io 接受的 dotted path.

    规则（按顺序优先）：
        1. ``runtime_state.<domain>.X`` → ``<domain>.X``（剥前缀）
        2. 顶层段已经是合法 state 域 → 原样
        3. 命中 _BARE_PATH_MAPPING（裸 chapter_text 等）→ 重写
        4. 否则抛 OpTranslationError（避免 silently 写到非法域被 state_io 拒）
    """
    if raw_path.startswith(_RUNTIME_STATE_PREFIX):
        return raw_path[len(_RUNTIME_STATE_PREFIX):]
    top = raw_path.split(".", 1)[0]
    if top in _VALID_STATE_DOMAINS:
        return raw_path
    if raw_path in _BARE_PATH_MAPPING:
        return _BARE_PATH_MAPPING[raw_path]
    # 兜底：裸字段如 ``foo.bar`` 没法识别 → 显式报错（fail-loud）.
    raise OpTranslationError(
        f"unrecognized path {raw_path!r}; expected runtime_state.* / "
        f"{_VALID_STATE_DOMAINS}.* / known bare key {list(_BARE_PATH_MAPPING)}"
    )


# ---------------------------------------------------------------------------
# Internals: op handlers
# ---------------------------------------------------------------------------

def _apply_delta(current: Any, value: Any, *, path: str, idx: int) -> Any:
    """delta：current + value.

    支持三种语义：
        - 数字 (int/float)：加法
        - dict：浅合并（value 的键覆盖 current 的同名键）
        - current 为 None：当作起始值，直接返回 value 的 deepcopy
    """
    if current is None:
        return copy.deepcopy(value)
    if isinstance(current, (int, float)) and isinstance(value, (int, float)):
        return current + value
    if isinstance(current, dict) and isinstance(value, dict):
        merged = copy.deepcopy(current)
        merged.update(copy.deepcopy(value))
        return merged
    raise OpTranslationError(
        f"ops[{idx}] op=delta path={path!r}: incompatible types "
        f"current={type(current).__name__}, value={type(value).__name__}; "
        "expected both numeric or both dict"
    )


def _apply_append(current: Any, value: Any, *, path: str, idx: int) -> List[Any]:
    """append：把 value 追加到 current（list）末尾.

    current 为 None / 空 → 新建 list；非 list 抛错.
    """
    if current is None:
        return [copy.deepcopy(value)]
    if not isinstance(current, list):
        raise OpTranslationError(
            f"ops[{idx}] op=append path={path!r}: current must be list, "
            f"got {type(current).__name__}"
        )
    new_list = copy.deepcopy(current)
    new_list.append(copy.deepcopy(value))
    return new_list


def _apply_append_or_update(
    current: Any,
    value: Any,
    *,
    match_key: str,
    path: str,
    idx: int,
) -> List[Any]:
    """append_or_update：按 ``match_key`` 在 current 里找匹配元素.

    - 找到：替换该元素为 value
    - 没找到：append value 到末尾

    value 必须是 dict（含 ``match_key`` 字段）；current 为 None / 空时新建 list.
    """
    if not isinstance(value, dict):
        raise OpTranslationError(
            f"ops[{idx}] op=append_or_update path={path!r}: value must be dict, "
            f"got {type(value).__name__}"
        )
    if match_key not in value:
        raise OpTranslationError(
            f"ops[{idx}] op=append_or_update path={path!r}: value missing match key {match_key!r}"
        )
    if current is None:
        return [copy.deepcopy(value)]
    if not isinstance(current, list):
        raise OpTranslationError(
            f"ops[{idx}] op=append_or_update path={path!r}: current must be list, "
            f"got {type(current).__name__}"
        )
    new_list = copy.deepcopy(current)
    target_key = value[match_key]
    replaced = False
    for i, item in enumerate(new_list):
        if isinstance(item, dict) and item.get(match_key) == target_key:
            new_list[i] = copy.deepcopy(value)
            replaced = True
            break
    if not replaced:
        new_list.append(copy.deepcopy(value))
    return new_list


__all__ = [
    "adapter_ops_to_state_updates",
    "OpTranslationError",
]
