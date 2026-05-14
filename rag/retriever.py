"""rag.retriever — orchestrates RAG Layer 1, Layer 2, and optional Layer 3."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping, Optional

from .cold_start import detect_state, load_recall_config
from .layer1_filter import recall as layer1_recall
from .layer2_vector import DeterministicTextEmbedder, search_vector, vector_ready
from .reranker import rerank_candidates, should_rerank


_LOG = logging.getLogger("rag.retriever")
_DEFAULT_EMBEDDING_PROVIDER = "deterministic-local"
_DEFAULT_EMBEDDING_MODEL_ID = "default"


def recall_cards(
    *,
    stage: Optional[str] = None,
    topic: Any = None,
    asset_type: Optional[str] = None,
    card_intent: Optional[str] = None,
    query_text: str = "",
    top_k: Optional[int] = None,
    candidate_k: Optional[int] = None,
    quality_floor: str = "B",
    index_path: Path | str | None = None,
    config: Optional[dict[str, Any]] = None,
    embedder: Any = None,
    llm_caller: Any = None,
) -> dict[str, Any]:
    """Recall cards with fail-open degradation diagnostics."""
    if config is None:
        config = load_recall_config()
    fp = Path(index_path) if index_path else Path("rag/index.sqlite")
    embedding_config = _resolve_embedding_config(config)
    vector_model_id = embedding_config["default_model_id"] if embedder is None else None
    diagnostics: dict[str, Any] = {
        "state": detect_state(fp),
        "requested_layers": _enabled_layers(fp, config),
        "used_layers": [],
        "warnings": [],
        "degraded_to": None,
        "vector_ready": False,
        "vector_reason": "",
        "rerank": False,
    }

    resolved_top_k = _resolve_top_k(stage, top_k, config)
    resolved_candidate_k = _resolve_candidate_k(stage, candidate_k, resolved_top_k, config)
    diagnostics["top_k"] = resolved_top_k
    diagnostics["candidate_k"] = resolved_candidate_k
    layer1_cards = layer1_recall(
        stage=stage,
        topic=topic,
        asset_type=asset_type,
        card_intent=card_intent,
        top_k=resolved_candidate_k,
        quality_floor=quality_floor,
        index_path=fp,
        config=config,
    )
    diagnostics["used_layers"] = [1]
    diagnostics["layer1_candidate_count"] = len(layer1_cards)
    cards = list(layer1_cards)

    if 2 in diagnostics["requested_layers"]:
        if embedder is None and not embedding_config["allow_default_embedder"]:
            diagnostics["warnings"].append("default_embedder_disabled")
            diagnostics["degraded_to"] = "layer1"
            return {"cards": cards[:resolved_top_k], "diagnostics": diagnostics}
        ready = vector_ready(fp, model_id=vector_model_id)
        diagnostics["vector_ready"] = ready.ready
        diagnostics["vector_reason"] = ready.reason
        if not ready.ready:
            diagnostics["warnings"].append("vector_not_ready")
            diagnostics["degraded_to"] = "layer1"
        elif not cards:
            diagnostics["warnings"].append("layer1_empty")
        else:
            try:
                vector_cards = search_vector(
                    fp,
                    query_text=query_text,
                    embedder=embedder or DeterministicTextEmbedder(),
                    top_k=resolved_top_k,
                    candidate_ids=[c["id"] for c in cards],
                    model_id=vector_model_id,
                )
            except Exception as exc:  # noqa: BLE001 - fail-open
                _LOG.warning("rag.retriever: layer2 failed open: %s", exc)
                vector_cards = []
                diagnostics["warnings"].append("vector_search_failed")
                diagnostics["degraded_to"] = "layer1"
            if vector_cards:
                cards = vector_cards
                diagnostics["used_layers"] = [1, 2]
            else:
                diagnostics["degraded_to"] = "layer1"

    if cards and should_rerank(stage, config):
        diagnostics["rerank"] = True
        if llm_caller is None:
            diagnostics["warnings"].append("rerank_llm_missing")
        else:
            before = [c.get("id") for c in cards]
            ranked = rerank_candidates(query_text, cards, llm_caller, top_k=resolved_top_k)
            cards = ranked
            after = [c.get("id") for c in cards]
            if after != before or len(after) <= len(before):
                diagnostics["used_layers"] = sorted(set(diagnostics["used_layers"] + [3]))

    return {"cards": cards[:resolved_top_k], "diagnostics": diagnostics}


def _enabled_layers(index_path: Path, config: Mapping[str, Any]) -> list[int]:
    section_name = "cold_start" if detect_state(index_path) == "cold" else "warm_start"
    section = config.get(section_name, {}) if isinstance(config, Mapping) else {}
    layers = section.get("enabled_layers", [1]) if isinstance(section, Mapping) else [1]
    if not isinstance(layers, list):
        return [1]
    out: list[int] = []
    for layer in layers:
        try:
            out.append(int(layer))
        except (TypeError, ValueError):
            continue
    return out or [1]


def _resolve_embedding_config(config: Mapping[str, Any]) -> dict[str, Any]:
    section = config.get("embedding", {}) if isinstance(config, Mapping) else {}
    if not isinstance(section, Mapping):
        section = {}
    default_model_id = section.get("default_model_id", _DEFAULT_EMBEDDING_MODEL_ID)
    default_provider = section.get("default_provider", _DEFAULT_EMBEDDING_PROVIDER)
    allow_default_embedder = section.get("allow_default_embedder", True)
    return {
        "default_model_id": str(default_model_id or _DEFAULT_EMBEDDING_MODEL_ID),
        "default_provider": str(default_provider or _DEFAULT_EMBEDDING_PROVIDER),
        "allow_default_embedder": bool(allow_default_embedder),
    }


def _resolve_top_k(stage: Optional[str], top_k: Optional[int], config: Mapping[str, Any]) -> int:
    if top_k is not None:
        try:
            return max(0, int(top_k))
        except (TypeError, ValueError):
            pass
    cfg = config.get("stage_specific_top_k", {}) if isinstance(config, Mapping) else {}
    if isinstance(cfg, Mapping):
        value = cfg.get(stage) if stage in cfg else cfg.get("default", 5)
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 5
    return 5


def _resolve_candidate_k(
    stage: Optional[str],
    candidate_k: Optional[int],
    top_k: int,
    config: Mapping[str, Any],
) -> int:
    if candidate_k is not None:
        try:
            return max(top_k, int(candidate_k))
        except (TypeError, ValueError):
            pass
    cfg = config.get("candidate_pool", {}) if isinstance(config, Mapping) else {}
    if isinstance(cfg, Mapping):
        value = cfg.get(stage) if stage in cfg else cfg.get("default")
        if value is not None:
            try:
                return max(top_k, int(value))
            except (TypeError, ValueError):
                pass
    return top_k


__all__ = ["recall_cards"]
