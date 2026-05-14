"""rag — Sprint 2 RAG Layer 1 (frontmatter 召回 + 冷启动降级).

模块路径 (ARCHITECTURE.md §五 / ROADMAP §2.2.2)::

    rag/
        index_builder.py   扫 foundation/assets/ → sqlite (id/stage/topic/asset_type/quality_grade/card_intent/source_path)
        layer1_filter.py   recall() API：stage/topic/asset_type/card_intent 过滤 + quality_grade 排序
        cold_start.py      detect_state + cold_recall_fallback (jury-2 P0 冷启动降级)

Sprint 2 仅落地 Layer 1；Layer 2 (向量召回) / Layer 3 (LLM rerank) 留给 S3.
"""

from .index_builder import build_index, IndexBuildError
from .layer1_filter import recall, Layer1RecallError
from .cold_start import detect_state, cold_recall_fallback

__all__ = [
    "build_index",
    "IndexBuildError",
    "recall",
    "Layer1RecallError",
    "detect_state",
    "cold_recall_fallback",
]
