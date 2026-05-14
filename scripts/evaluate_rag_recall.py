#!/usr/bin/env python3
"""Build a temporary RAG index and evaluate reproducible recall quality."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.index_builder import build_index
from rag.layer1_filter import recall as layer1_recall
from rag.layer2_vector import (
    DeterministicTextEmbedder,
    SQLiteVecBackend,
    build_vector_index,
    search_vector,
    vector_ready,
)

DEFAULT_PROMPTS_DIR = REPO_ROOT / "foundation" / "assets" / "prompts"
DEFAULT_METHODOLOGY_DIR = REPO_ROOT / "foundation" / "assets" / "methodology"
DEFAULT_SOURCES = [DEFAULT_PROMPTS_DIR, DEFAULT_METHODOLOGY_DIR]
DEFAULT_INDEX_PATH = REPO_ROOT / ".ops" / "validation" / "rag_recall_eval.sqlite"
DEFAULT_JSON_PATH = REPO_ROOT / ".ops" / "validation" / "rag_recall_quality.json"
DEFAULT_REPORT_PATH = REPO_ROOT / ".ops" / "reports" / "rag_recall_quality_report.md"
MODEL_ID = "rag-recall-eval-deterministic-v1"
TOP_K = 5

QUERY_SET: list[dict[str, Any]] = [
    {
        "query": "失忆刺客 第一章 开场",
        "stage": "drafting",
        "topics": ["悬疑", "武侠", "玄幻"],
        "asset_type": "prompt_card",
        "intent": "prose_generation",
        "notes": "章节开场创作，优先看 drafting prose_generation 对刺客/失忆/悬疑的语义命中。",
    },
    {
        "query": "黑暗玄幻 微粒经济",
        "stage": "setting",
        "topics": ["玄幻", "黑暗"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "notes": "世界观经济规则查询，Layer 1 用 setting+玄幻/黑暗+结构设计收窄。",
    },
    {
        "query": "章节悬念 回收伏笔",
        "stage": "framework",
        "topics": ["通用", "悬疑"],
        "asset_type": "prompt_card",
        "intent": "outline_planning",
        "notes": "结构层查询，检查伏笔、悬念、章节节奏相关资产是否被召回。",
    },
    {
        "query": "角色状态更新",
        "stage": "setting",
        "topics": ["通用"],
        "asset_type": "prompt_card",
        "intent": "generator",
        "notes": "偏状态表/角色档案维护，验证通用 setting 生成器类卡片。",
    },
    {
        "query": "世界观设定 天堑 内宇宙",
        "stage": "setting",
        "topics": ["玄幻", "科幻", "通用"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "notes": "专名较强的世界观设定查询，观察没有精确词时的近邻质量。",
    },
    {
        "query": "反转设计 狗血女文",
        "stage": "framework",
        "topics": ["言情", "女频", "豪门"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "notes": "女频反转/狗血桥段设计，检查 genre/topic 与语义共同作用。",
    },
    {
        "query": "规则怪谈 副本设计",
        "stage": "setting",
        "topics": ["怪谈", "悬疑", "恐怖"],
        "asset_type": "prompt_card",
        "intent": "generator",
        "notes": "规则怪谈强标签查询，预期 Layer 1 与 Layer 2 overlap 较高。",
    },
    {
        "query": "多子多福 奖励机制",
        "stage": "setting",
        "topics": ["系统", "玄幻"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "notes": "系统奖励机制查询，检验具体流派名与系统设定资产的距离。",
    },
    {
        "query": "终稿润色 文风统一",
        "stage": "refinement",
        "topics": ["文风"],
        "asset_type": "prompt_card",
        "intent": "editing_transformation",
        "notes": "终稿润色查询，使用 schema 内 polish/rewrite 类 editing_transformation，重点看标题是否直接相关。",
    },
    {
        "query": "市场定位 读者画像",
        "stage": "business",
        "topics": ["business", "通用"],
        "asset_type": "methodology",
        "notes": "商业分析查询，验证 business 阶段是否能召回读者画像/卖点定位 methodology 资产。",
    },
    {
        "query": "第一章 黄金三章 爽点钩子",
        "stage": "framework",
        "topics": ["通用"],
        "asset_type": "prompt_card",
        "intent": "outline_planning",
        "notes": "黄金三章/开篇节奏查询，补充常见章节设计场景。",
    },
    {
        "query": "战斗场景 节奏 动作描写",
        "stage": "drafting",
        "topics": ["玄幻", "动作"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "notes": "动作戏场景查询，检验 drafting 与 structural_design 的交叉召回。",
    },
]


def repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def compact_hit(hit: dict[str, Any], *, include_score: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": hit.get("id", ""),
        "title": hit.get("title", ""),
    }
    if include_score:
        out["score"] = round(float(hit.get("_vector_score", hit.get("_score", 0.0)) or 0.0), 6)
    return out


def count_rows(index_path: Path, table: str) -> int:
    try:
        with sqlite3.connect(str(index_path)) as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
    except sqlite3.Error:
        return 0


def grade_distribution(index_path: Path) -> dict[str, int]:
    with sqlite3.connect(str(index_path)) as conn:
        rows = conn.execute(
            "SELECT quality_grade, COUNT(*) FROM cards GROUP BY quality_grade ORDER BY quality_grade"
        ).fetchall()
    return {str(grade or "UNKNOWN"): int(count) for grade, count in rows}


def evaluate_query(
    query_spec: dict[str, Any],
    *,
    index_path: Path,
    embedder: DeterministicTextEmbedder,
    backend: SQLiteVecBackend,
) -> dict[str, Any]:
    asset_type = str(query_spec["asset_type"])
    card_intent = query_spec.get("intent")
    layer1_hits = layer1_recall(
        stage=query_spec["stage"],
        topic=query_spec["topics"],
        asset_type=asset_type,
        card_intent=card_intent,
        top_k=TOP_K,
        quality_floor="B",
        index_path=index_path,
        config={"stage_specific_top_k": {"default": TOP_K}},
    )
    layer1_ids = [str(hit.get("id", "")) for hit in layer1_hits]

    native_search_error = ""
    try:
        layer2_hits = search_vector(
            index_path,
            str(query_spec["query"]),
            embedder=embedder,
            top_k=TOP_K,
            candidate_ids=layer1_ids or None,
            model_id=MODEL_ID,
            backend=backend,
        )
    except Exception as exc:  # noqa: BLE001 - native sqlite-vec is optional for evaluation.
        native_search_error = f"{exc.__class__.__name__}: {exc}"
        layer2_hits = search_vector(
            index_path,
            str(query_spec["query"]),
            embedder=embedder,
            top_k=TOP_K,
            candidate_ids=layer1_ids or None,
            model_id=MODEL_ID,
            backend=None,
        )
    layer2_ids = [str(hit.get("id", "")) for hit in layer2_hits]
    overlap_ids = [card_id for card_id in layer2_ids if card_id in set(layer1_ids)]
    overlap_ratio = len(overlap_ids) / max(1, min(len(layer1_ids), len(layer2_ids)))

    return {
        "query": query_spec["query"],
        "filters": {
            "stage": query_spec["stage"],
            "topics": query_spec["topics"],
            "asset_type": asset_type,
            "card_intent": card_intent,
            "quality_floor": "B",
            "top_k": TOP_K,
        },
        "layer1": {
            "ids": layer1_ids,
            "titles": [str(hit.get("title", "")) for hit in layer1_hits],
            "hits": [compact_hit(hit) for hit in layer1_hits],
        },
        "layer2": {
            "ids": layer2_ids,
            "titles": [str(hit.get("title", "")) for hit in layer2_hits],
            "scores": [round(float(hit.get("_vector_score", hit.get("_score", 0.0)) or 0.0), 6) for hit in layer2_hits],
            "hits": [compact_hit(hit, include_score=True) for hit in layer2_hits],
        },
        "overlap": {
            "ids": overlap_ids,
            "count": len(overlap_ids),
            "ratio": round(overlap_ratio, 4),
        },
        "native_sqlite_vec": bool(layer2_hits and any("_vector_distance" in hit for hit in layer2_hits)),
        "native_search_error": native_search_error,
        "notes": query_spec["notes"],
    }


def build_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    environment = payload["environment"]
    query_results = payload["queries"]
    lines: list[str] = [
        "# RAG 真实召回质量评估报告",
        "",
        f"- 生成时间: {payload['generated_at']}",
        f"- 数据源: `{environment['sources']}`",
        f"- 临时索引: `{environment['index_path']}`",
        f"- JSON 输出: `{environment['json_path']}`",
        "",
        "## 总体结论",
        "",
        (
            f"- 本次从真实资产构建 Layer 1 索引 {summary['cards_indexed']} 张卡，"
            f"Layer 2 向量 {summary['vectors_indexed']} 条。"
        ),
        (
            f"- sqlite-vec native 状态: {summary['native_sqlite_vec_status']}；"
            f"构建存储: `{summary['vector_storage']}`；fallback: `{summary['fallback_status']}`。"
        ),
        (
            f"- {summary['query_count']} 条固定查询平均 Layer 1 命中 {summary['avg_layer1_hits']:.2f}，"
            f"平均 Layer 2 命中 {summary['avg_layer2_hits']:.2f}，平均 overlap {summary['avg_overlap_ratio']:.2f}。"
        ),
        "",
        "## 环境",
        "",
        f"- Python: `{environment['python']}`",
        f"- sqlite: `{environment['sqlite_version']}`",
        f"- sqlite-vec module available: `{environment['sqlite_vec_module_available']}`",
        f"- vector_ready: `{summary['vector_ready_reason']}`",
        f"- quality_grade distribution: `{summary['quality_grade_distribution']}`",
        "",
        "## 方法",
        "",
        "- 使用 `rag.index_builder.build_index()` 从 `foundation/assets/prompts` 和 `foundation/assets/methodology` 重建临时 SQLite 索引。",
        "- 使用 `rag.layer2_vector.build_vector_index()` 构建 Layer 2，传入 `SQLiteVecBackend()` 优先尝试 native sqlite-vec。",
        "- 每条查询先按 stage/topic/asset_type/card_intent/quality_floor 做 Layer 1 过滤；Layer 1 非空时在候选内做 Layer 2 top-k 重排，Layer 1 为空时记录一次全局 Layer 2 诊断。",
        "- embedding 使用项目内离线 `DeterministicTextEmbedder`，不调用 LLM，不发网络请求。",
        "",
        "## 每条查询 Top Hits",
        "",
    ]

    for item in query_results:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                (
                    f"- Filters: stage=`{item['filters']['stage']}`, topics=`{item['filters']['topics']}`, "
                    f"asset_type=`{item['filters']['asset_type']}`, "
                    f"intent=`{item['filters']['card_intent'] or 'none'}`"
                ),
                f"- Layer 1: {format_hits(item['layer1']['hits'])}",
                f"- Layer 2: {format_hits(item['layer2']['hits'])}",
                f"- Overlap: {item['overlap']['count']} / ratio {item['overlap']['ratio']}",
                f"- Notes: {item['notes']}",
                "",
            ]
        )

    lines.extend(
        [
            "## 观察到的问题",
            "",
            *[f"- {text}" for text in payload["observations"]],
            "",
            "## 下一步建议",
            "",
            *[f"- {text}" for text in payload["recommendations"]],
            "",
        ]
    )
    return "\n".join(lines)


def format_hits(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "(empty)"
    parts: list[str] = []
    for hit in hits:
        score = hit.get("score")
        suffix = f" ({score:.4f})" if isinstance(score, float) else ""
        parts.append(f"{hit.get('id', '')} / {hit.get('title', '')}{suffix}")
    return "; ".join(parts)


def make_observations(results: list[dict[str, Any]], vector_stats: dict[str, Any]) -> list[str]:
    observations: list[str] = []
    empty_l1 = [item["query"] for item in results if not item["layer1"]["ids"]]
    empty_l2 = [item["query"] for item in results if not item["layer2"]["ids"]]
    low_overlap = [item["query"] for item in results if item["overlap"]["ratio"] < 0.6]
    if empty_l1:
        observations.append(f"Layer 1 空召回查询: {empty_l1}。这通常来自 metadata 过滤过窄或资产标签缺口。")
    if empty_l2:
        observations.append(f"Layer 2 空召回查询: {empty_l2}。本次 Layer 2 限定在 Layer 1 候选内，因此会继承 Layer 1 空集。")
    if low_overlap:
        observations.append(f"Overlap 低于 0.6 的查询: {low_overlap}。向量重排改变了候选排序或 native 查询 fallback 为空。")
    if empty_l1 and not empty_l2:
        observations.append("Layer 1 空召回时，脚本保留全局 Layer 2 结果作为诊断；这些结果不代表正式 retriever 会注入这些卡片。")
    if vector_stats["storage"] != "sqlite-vec":
        observations.append("native sqlite-vec 未成为最终查询路径，评估结果使用 JSON 向量余弦 fallback。")
    native_errors = sorted({item["native_search_error"] for item in results if item.get("native_search_error")})
    if native_errors:
        observations.append(f"native sqlite-vec 查询失败后已回退 JSON 向量，错误样例: {native_errors[:2]}。")
    observations.append("DeterministicTextEmbedder 是 token hashing，适合复现 smoke/趋势评估，但不等价于生产级语义 embedding。")
    return observations


def make_recommendations(results: list[dict[str, Any]]) -> list[str]:
    recommendations = [
        "把本脚本纳入后续资产变更后的固定评估入口，用 JSON diff 跟踪召回质量漂移。",
        "为高频业务查询维护 expected/relevant id 集合，后续可计算 recall@k、MRR、nDCG 等更硬的指标。",
        "针对 Layer 1 空召回或明显窄召回的 query，优先补 metadata topic/card_intent，而不是先改检索代码。",
    ]
    if any("微粒经济" in item["query"] or "内宇宙" in item["query"] for item in results):
        recommendations.append("对专名强、资产未覆盖的题材词建立同义词/领域词表，降低 Layer 1 过滤漏召回。")
    return recommendations


def resolve_source_paths(prompts_dir: Path, explicit_sources: list[Path] | None) -> list[Path]:
    """Resolve index sources while preserving the legacy --prompts-dir override."""
    resolved_prompts = prompts_dir.resolve()
    if explicit_sources is None:
        return [resolved_prompts, DEFAULT_METHODOLOGY_DIR.resolve()]
    source_paths = [path.resolve() for path in explicit_sources]
    if resolved_prompts not in source_paths:
        source_paths.insert(0, resolved_prompts)
    return source_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=DEFAULT_PROMPTS_DIR,
        help="Prompt-card source directory; kept for compatibility and included in --sources.",
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        type=Path,
        default=None,
        help="Asset source directories/files to index. Defaults to prompts + methodology assets.",
    )
    parser.add_argument("--index-path", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    prompts_dir = args.prompts_dir.resolve()
    source_paths = resolve_source_paths(prompts_dir, args.sources)
    index_path = args.index_path.resolve()
    json_path = args.json_output.resolve()
    report_path = args.report_output.resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    index_stats = build_index(source_paths, index_path)
    embedder = DeterministicTextEmbedder()
    backend = SQLiteVecBackend()
    vector_stats_obj = build_vector_index(index_path, embedder, model_id=MODEL_ID, backend=backend)
    ready = vector_ready(index_path, model_id=MODEL_ID)

    results = [
        evaluate_query(query_spec, index_path=index_path, embedder=embedder, backend=backend)
        for query_spec in QUERY_SET
    ]
    native_used = any(item["native_sqlite_vec"] for item in results)
    native_search_errors = sorted({item["native_search_error"] for item in results if item["native_search_error"]})
    overlap_values = [float(item["overlap"]["ratio"]) for item in results]
    layer1_counts = [len(item["layer1"]["ids"]) for item in results]
    layer2_counts = [len(item["layer2"]["ids"]) for item in results]
    vector_stats = vector_stats_obj.to_dict()
    if native_used and native_search_errors:
        fallback_status = "partial-sqlite-json"
        native_status = "部分查询使用 native sqlite-vec，部分查询失败后回退 JSON 向量"
    elif native_used:
        fallback_status = "none"
        native_status = "可用并用于全部有结果查询"
    else:
        fallback_status = "sqlite-json"
        native_status = "未用于查询"

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": {
            "python": sys.version.split()[0],
            "sqlite_version": sqlite3.sqlite_version,
            "sqlite_vec_module_available": bool(backend.available),
            "prompts_dir": repo_relative(prompts_dir),
            "sources": [repo_relative(path) for path in source_paths],
            "index_path": repo_relative(index_path),
            "json_path": repo_relative(json_path),
            "report_path": repo_relative(report_path),
            "model_id": MODEL_ID,
            "top_k": TOP_K,
        },
        "index_build": index_stats.to_dict(),
        "vector_build": vector_stats,
        "summary": {
            "query_count": len(results),
            "cards_indexed": index_stats.cards_indexed,
            "documents_indexed": count_rows(index_path, "card_documents"),
            "vectors_indexed": vector_stats_obj.vectors_indexed,
            "vector_storage": vector_stats_obj.storage,
            "fallback_status": fallback_status,
            "native_sqlite_vec_available": bool(backend.available),
            "native_sqlite_vec_used": native_used,
            "native_sqlite_vec_status": native_status,
            "native_search_errors": native_search_errors,
            "vector_ready": ready.ready,
            "vector_ready_reason": ready.reason,
            "avg_layer1_hits": sum(layer1_counts) / max(1, len(layer1_counts)),
            "avg_layer2_hits": sum(layer2_counts) / max(1, len(layer2_counts)),
            "avg_overlap_ratio": sum(overlap_values) / max(1, len(overlap_values)),
            "empty_layer1_queries": [item["query"] for item in results if not item["layer1"]["ids"]],
            "empty_layer2_queries": [item["query"] for item in results if not item["layer2"]["ids"]],
            "quality_grade_distribution": grade_distribution(index_path),
            "intent_distribution_top10": Counter(
                result["filters"]["card_intent"] for result in results
            ).most_common(10),
        },
        "queries": results,
    }
    payload["observations"] = make_observations(results, vector_stats)
    payload["recommendations"] = make_recommendations(results)

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown_report(payload), encoding="utf-8")
    print(
        f"wrote {repo_relative(json_path)} and {repo_relative(report_path)}; "
        f"cards={index_stats.cards_indexed} vectors={vector_stats_obj.vectors_indexed} "
        f"native_used={native_used} fallback={fallback_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
