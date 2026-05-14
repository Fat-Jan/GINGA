"""rag.layer1_filter — Layer 1 frontmatter 召回 (R-2 + R-4).

API::

    recall(
        stage: str | None,
        topic: str | list[str] | None,
        asset_type: str | None,
        card_intent: str | None,
        top_k: int | None,        # None → 读 stage_specific_top_k[stage]
        quality_floor: str,       # "A" / "A-" / "B+" / "B" (C/D 默认 floor=B)
        index_path: Path | str,
        config: dict | None,
    ) -> list[dict]

冷启动 (index 不存在 / 无记录) → 返回 [] + audit log warn (jury-2 P0).
quality_grade 排序：A > A- > B+ > B > C > D；C/D 默认过滤 (由 quality_floor="B" 控制).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional


_LOG = logging.getLogger("rag.layer1_filter")

# 默认 sqlite 索引文件位置 (与 index_builder 约定一致).
_DEFAULT_INDEX_PATH = Path("rag/index.sqlite")

# 默认 recall_config 文件 (与 cold_start 约定一致).
_DEFAULT_CONFIG_PATH = Path("foundation/rag/recall_config.yaml")

# quality_grade 排序权重 (高 → 低)；未知 grade 排到末尾.
_QUALITY_ORDER: dict[str, int] = {
    "A": 0,
    "A-": 1,
    "B+": 2,
    "B": 3,
    "C": 4,
    "D": 5,
}

# 默认 floor：剔除 C / D；caller 可通过 quality_floor="C" 放宽.
_DEFAULT_QUALITY_FLOOR = "B"


class Layer1RecallError(RuntimeError):
    """recall API 内部一致性错误 (index 文件损坏等)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def recall(
    stage: Optional[str] = None,
    topic: Any = None,
    asset_type: Optional[str] = None,
    card_intent: Optional[str] = None,
    top_k: Optional[int] = None,
    quality_floor: str = _DEFAULT_QUALITY_FLOOR,
    *,
    index_path: Path | str | None = None,
    config: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """按 frontmatter 字段过滤召回卡片，按 quality_grade 排序.

    Parameters
    ----------
    stage:
        当前 workflow stage (drafting / refinement / ...)；命中 ``cards.stage`` 精确比较.
    topic:
        题材标签；可传 str 或 list[str]，list 内任一命中即算召回 (jury-3 partial match).
    asset_type:
        资产类型 (prompt_card / template / methodology / genre_profile / ...).
    card_intent:
        prompt_card 专属 12 大聚类之一 (prose_generation / structural_design / ...).
    top_k:
        召回上限；为 ``None`` 时按 ``stage_specific_top_k[stage]`` 取，缺省回 ``default_top_k`` (R-4).
    quality_floor:
        最低质量等级；A/A-/B+/B/C/D，比 floor 低的卡片被滤掉 (默认 B 即剔 C/D).
    index_path:
        sqlite 索引路径；默认 ``rag/index.sqlite``.
    config:
        预加载的 recall_config dict (避免重复 IO)；为 None 时按需 lazy load.

    Returns
    -------
    list[dict]
        召回结果，每条 dict 至少含::

            id / asset_type / stage / topic / quality_grade / card_intent / title /
            source_path / last_updated / _score (排序原始权重)

    Behavior
    --------
    - index 缺失 / 无表 / 0 条记录 → 返回 ``[]``，audit log warn "rag cold-start, empty result".
    - quality_floor 不在 ``_QUALITY_ORDER`` → 抛 ``Layer1RecallError``.
    """
    fp = Path(index_path) if index_path else _DEFAULT_INDEX_PATH
    if quality_floor not in _QUALITY_ORDER:
        raise Layer1RecallError(f"invalid quality_floor={quality_floor!r}; expected one of {list(_QUALITY_ORDER)}")

    if not fp.exists():
        _LOG.warning("rag.layer1_filter: index %s missing (cold-start, empty result)", fp)
        return []

    rows = _query(fp, stage=stage, asset_type=asset_type, card_intent=card_intent)
    if not rows:
        _LOG.warning("rag.layer1_filter: rag cold-start, empty result (index has 0 rows or no match)")
        return []

    # quality_floor 过滤.
    floor_score = _QUALITY_ORDER[quality_floor]
    rows = [r for r in rows if _quality_score(r.get("quality_grade", "")) <= floor_score]

    # topic 部分匹配 (list-as-OR).
    if topic is not None:
        wanted_topics = _coerce_topic(topic)
        if wanted_topics:
            rows = [r for r in rows if _topic_hit(r.get("topic", []), wanted_topics)]

    # 排序：quality_grade ASC (按 _QUALITY_ORDER) → last_updated DESC (新优先).
    rows.sort(
        key=lambda r: (_quality_score(r.get("quality_grade", "")), _negate_str(r.get("last_updated", "")))
    )

    if top_k is None:
        top_k = _resolve_top_k(stage, config)
    if top_k is not None and top_k > 0:
        rows = rows[:top_k]

    return rows


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _query(
    index_path: Path,
    *,
    stage: Optional[str],
    asset_type: Optional[str],
    card_intent: Optional[str],
) -> list[dict[str, Any]]:
    """从 sqlite 拉满足 stage/asset_type/card_intent 条件的候选."""
    sql = "SELECT id, asset_type, stage, topic_json, quality_grade, card_intent, title, source_path, last_updated FROM cards"
    where: list[str] = []
    params: list[Any] = []
    if stage:
        where.append("stage = ?")
        params.append(stage)
    if asset_type:
        where.append("asset_type = ?")
        params.append(asset_type)
    if card_intent:
        where.append("card_intent = ?")
        params.append(card_intent)
    if where:
        sql += " WHERE " + " AND ".join(where)
    try:
        with sqlite3.connect(str(index_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
    except sqlite3.OperationalError as exc:
        _LOG.warning("rag.layer1_filter: index query failed (%s); treating as empty", exc)
        return []
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        d["topic"] = _decode_topic(d.pop("topic_json", "[]"))
        out.append(d)
    return out


def _quality_score(grade: str) -> int:
    return _QUALITY_ORDER.get(grade, 99)


def _coerce_topic(topic: Any) -> list[str]:
    if isinstance(topic, str):
        return [topic.strip()] if topic.strip() else []
    if isinstance(topic, (list, tuple, set)):
        return [str(x).strip() for x in topic if str(x).strip()]
    return []


def _topic_hit(card_topics: Iterable[Any], wanted: list[str]) -> bool:
    card_set = {str(t).strip() for t in card_topics if str(t).strip()}
    return any(w in card_set for w in wanted)


def _decode_topic(blob: str) -> list[str]:
    if not blob:
        return []
    try:
        v = json.loads(blob)
    except json.JSONDecodeError:
        return []
    return [str(x) for x in v] if isinstance(v, list) else []


def _negate_str(s: str) -> str:
    """让 sort 升序时把 last_updated 当作降序：取反字符。

    这是 stdlib sort 不支持混排升降序时的常用技巧。比较 ``-str(x)`` 不直观，
    这里把 last_updated 转 negative 字典序：用一个"反 ASCII"的小技巧，
    实际只在 key 函数内消费，外部不暴露.
    """
    # 简单做法：用 (-ord, ...) 比较太重；改用元组 (score, NEG, last_updated_desc).
    # 这里就是把 string 取反返回，让 sort key 升序得到 last_updated 降序.
    # 实际改用 "rever" trick：返回 "ZZZ..."- s 难做；最简洁是返回一个 wrapper.
    return _NegStr(s)


class _NegStr:
    """让 ``sorted(..., key=lambda x: (..., _NegStr(x)))`` 实现单字段降序.

    实现 ``__lt__``：``self < other`` 等价 ``self.s > other.s``.
    """

    __slots__ = ("s",)

    def __init__(self, s: str) -> None:
        self.s = s

    def __lt__(self, other: "_NegStr") -> bool:  # type: ignore[override]
        return self.s > other.s

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        return isinstance(other, _NegStr) and self.s == other.s


def _resolve_top_k(stage: Optional[str], config: Optional[dict[str, Any]]) -> int:
    """从 recall_config.yaml 读 stage_specific_top_k；缺省回 default_top_k (R-4)."""
    if config is None:
        # lazy import 避免 cold_start 循环 (cold_start 也会 import 本模块).
        from .cold_start import load_recall_config

        config = load_recall_config()
    cfg = config.get("stage_specific_top_k") or {}
    if not isinstance(cfg, dict):
        return 5
    if stage and stage in cfg:
        try:
            return int(cfg[stage])
        except (TypeError, ValueError):
            pass
    # config 里写 "default"；硬底默认 5.
    try:
        return int(cfg.get("default", 5))
    except (TypeError, ValueError):
        return 5


__all__ = [
    "recall",
    "Layer1RecallError",
]
