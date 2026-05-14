"""rag.reranker — Sprint 3 optional Layer 3 LLM rerank."""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Optional, Sequence


_LOG = logging.getLogger("rag.reranker")


LLMCaller = Callable[[Mapping[str, Any]], Any]


def should_rerank(stage: str | None, config: Mapping[str, Any] | None) -> bool:
    """Return whether Layer 3 should run for ``stage``."""
    cfg = (config or {}).get("enable_rerank_by_stage") if isinstance(config, Mapping) else None
    if not isinstance(cfg, Mapping):
        return False
    value = cfg.get(stage) if stage in cfg else cfg.get("default", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def rerank_candidates(
    query_text: str,
    candidates: Sequence[Mapping[str, Any]],
    llm_caller: Optional[LLMCaller],
    *,
    top_k: Optional[int] = None,
    timeout_s: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Ask an LLM caller for an ordered id list, failing open to original order."""
    original = [dict(c) for c in candidates]
    if not original or llm_caller is None:
        return original
    payload = {
        "query_text": query_text,
        "candidate_ids": [str(c.get("id", "")) for c in original],
        "candidates": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "quality_grade": c.get("quality_grade"),
                "stage": c.get("stage"),
                "topic": c.get("topic"),
            }
            for c in original
        ],
        "top_k": top_k,
        "timeout_s": timeout_s,
    }
    try:
        response = llm_caller(payload)
        ids = _extract_ids(response)
    except Exception as exc:  # noqa: BLE001 - fail-open
        _LOG.warning("rag.reranker: llm rerank failed open: %s", exc)
        return original
    if not ids:
        return original
    by_id = {str(c.get("id", "")): c for c in original}
    if any(i not in by_id for i in ids):
        return original
    if len(set(ids)) != len(ids):
        return original
    ranked = [dict(by_id[i]) for i in ids]
    if top_k is not None:
        try:
            ranked = ranked[: max(0, int(top_k))]
        except (TypeError, ValueError):
            pass
    return ranked


def _extract_ids(response: Any) -> list[str]:
    raw: Any
    if isinstance(response, Mapping):
        raw = response.get("ids", response.get("ranked_ids", response.get("ordered_ids")))
    else:
        raw = response
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if str(x)]


__all__ = ["LLMCaller", "should_rerank", "rerank_candidates"]
