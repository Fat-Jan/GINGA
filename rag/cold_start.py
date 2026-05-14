"""rag.cold_start — 冷暖启动检测 + 降级 (R-3, jury-2 P0).

冷启动：``rag/index.sqlite`` 不存在 / 表无记录 → disable Layer 2/3，只跑 Layer 1.
暖启动：``rag/index.sqlite`` 存在且有 ≥1 条记录 → 默认 Layer 1+2 (S3 实现).

读 ``foundation/rag/recall_config.yaml.cold_start`` 决定 ``enabled_layers`` /
``fallback_sort_by``；本模块只做状态判定 + 转发，不重复 layer1 实现.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal, Optional

import yaml


_LOG = logging.getLogger("rag.cold_start")

# 默认 recall_config 位置 (ARCHITECTURE 附录 A / ROADMAP F-10).
_DEFAULT_CONFIG_PATH = Path("foundation/rag/recall_config.yaml")


def detect_state(index_path: Path | str) -> Literal["cold", "warm"]:
    """判定 RAG 冷暖状态.

    rules (ARCHITECTURE §5.2)::

        index 文件缺失 / 表为空 → "cold"  → enabled_layers = [1]
        index 中有 >=1 条记录   → "warm"  → enabled_layers = [1, 2]

    Sprint 2 仅落地 Layer 1，warm 状态下也按 Layer 1 走 (Layer 2 在 S3 接入).
    """
    # lazy import 避免 rag.__init__ 循环.
    from .index_builder import count_cards

    fp = Path(index_path)
    if not fp.exists():
        return "cold"
    return "warm" if count_cards(fp) > 0 else "cold"


def load_recall_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """加载 ``recall_config.yaml``；不存在时返回默认骨架.

    默认骨架与 foundation/rag/recall_config.yaml 一致（cold_start.enabled_layers=[1]）.
    """
    fp = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    if not fp.exists():
        _LOG.warning("rag.cold_start: recall_config not found at %s, using built-in defaults", fp)
        return _builtin_defaults()
    try:
        raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        _LOG.error("rag.cold_start: parse recall_config failed: %s", exc)
        return _builtin_defaults()
    if not isinstance(raw, dict):
        return _builtin_defaults()
    return raw


def enabled_layers(
    index_path: Path | str,
    *,
    config: Optional[dict[str, Any]] = None,
) -> list[int]:
    """返回当前应启用的 RAG layer 列表，按 detect_state 切换 cold/warm 配置."""
    if config is None:
        config = load_recall_config()
    state = detect_state(index_path)
    section = config.get("cold_start" if state == "cold" else "warm_start", {})
    layers = section.get("enabled_layers", [1])
    if not isinstance(layers, list):
        return [1]
    return [int(x) for x in layers if isinstance(x, int) or (isinstance(x, str) and x.isdigit())]


def cold_recall_fallback(
    index_path: Path | str,
    *,
    stage: Optional[str] = None,
    topic: Any = None,
    asset_type: Optional[str] = None,
    card_intent: Optional[str] = None,
    top_k: Optional[int] = None,
    quality_floor: str = "B",
    config: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """冷启动降级召回 (Layer 1 only).

    内部直接转发到 ``layer1_filter.recall``，不引入 vector / rerank 路径；
    Layer 2/3 在 Sprint 2 不可用，调用方拿到 [] 时按 audit warn 处理.
    """
    # lazy import：避免 rag.__init__ 循环.
    from .layer1_filter import recall

    return recall(
        stage=stage,
        topic=topic,
        asset_type=asset_type,
        card_intent=card_intent,
        top_k=top_k,
        quality_floor=quality_floor,
        index_path=index_path,
        config=config,
    )


def _builtin_defaults() -> dict[str, Any]:
    """硬编码兜底 (recall_config.yaml 缺失时使用)."""
    return {
        "cold_start": {
            "enabled_layers": [1],
            "fallback_sort_by": ["quality_grade", "last_updated"],
            "log_degradation": True,
        },
        "warm_start": {
            "enabled_layers": [1, 2],
            "layer3_optional": True,
        },
        "stage_specific_top_k": {
            "ideation": 20,
            "setting": 15,
            "framework": 10,
            "outline": 10,
            "drafting": 5,
            "refinement": 3,
            "default": 5,
        },
    }


__all__ = [
    "detect_state",
    "load_recall_config",
    "enabled_layers",
    "cold_recall_fallback",
]
