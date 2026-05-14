#!/usr/bin/env python3
"""Build a temporary RAG index and evaluate reproducible recall quality."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.index_builder import build_index
from rag.layer1_filter import recall as layer1_recall
from rag.layer1_filter import topic_hit as layer1_topic_hit
from rag.layer2_vector import (
    DeterministicTextEmbedder,
    SQLiteVecBackend,
    build_vector_index,
    search_vector,
    vector_ready,
)
from rag.cold_start import load_recall_config

DEFAULT_PROMPTS_DIR = REPO_ROOT / "foundation" / "assets" / "prompts"
DEFAULT_METHODOLOGY_DIR = REPO_ROOT / "foundation" / "assets" / "methodology"
DEFAULT_SOURCES = [DEFAULT_PROMPTS_DIR, DEFAULT_METHODOLOGY_DIR]
DEFAULT_INDEX_PATH = REPO_ROOT / ".ops" / "validation" / "rag_recall_eval.sqlite"
DEFAULT_JSON_PATH = REPO_ROOT / ".ops" / "validation" / "rag_recall_quality.json"
DEFAULT_REPORT_PATH = REPO_ROOT / ".ops" / "reports" / "rag_recall_quality_report.md"
DEFAULT_RECALL_CONFIG_PATH = REPO_ROOT / "foundation" / "rag" / "recall_config.yaml"
EVAL_MODEL_ID = "rag-recall-eval-deterministic-v1"
MODEL_ID = EVAL_MODEL_ID
TOP_K = 5
CANDIDATE_K = 20
EVAL_RECALL_CONFIG = load_recall_config(DEFAULT_RECALL_CONFIG_PATH)
LAYER1_FILTER_EXPANSION = EVAL_RECALL_CONFIG.get("layer1_filter_expansion", {})
BLOCKER_KEYS = [
    "stage",
    "topic",
    "asset_type",
    "card_intent",
    "candidate_k",
    "top_k",
    "quality_floor",
    "missing_from_index",
]
QUALITY_ORDER: dict[str, int] = {
    "A": 0,
    "A-": 1,
    "B+": 2,
    "B": 3,
    "C": 4,
    "D": 5,
}

QUERY_SET: list[dict[str, Any]] = [
    {
        "query": "失忆刺客 第一章 开场",
        "stage": "drafting",
        "topics": ["悬疑", "武侠", "玄幻"],
        "asset_type": "prompt_card",
        "intent": "prose_generation",
        "expected_ids": [
            "prompts-card-outline_amnesia_arc-109",
            "prompts-card-create-assassin_creed",
        ],
        "relevant_ids": [
            "prompts-card-outline_amnesia_arc-109",
            "prompts-card-create-assassin_creed",
            "prompts-card-write-combat_scene-13",
        ],
        "notes": "章节开场创作，优先看 drafting prose_generation 对刺客/失忆/悬疑的语义命中。",
    },
    {
        "query": "黑暗玄幻 微粒经济",
        "stage": "setting",
        "topics": ["玄幻", "黑暗"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "expected_ids": [
            "prompts-card-simulate_fantasy_economy-102",
            "prompts-card-design_power_system-6",
        ],
        "relevant_ids": [
            "prompts-card-simulate_fantasy_economy-102",
            "prompts-card-design_power_system-6",
            "prompts-card-design_system_shop-83",
            "prompts-card-write_currency_creation-274",
            "prompts-card-manage_guild_resources-119",
        ],
        "notes": "世界观经济规则查询，Layer 1 用 setting+玄幻/黑暗+结构设计收窄。",
    },
    {
        "query": "章节悬念 回收伏笔",
        "stage": "framework",
        "topics": ["通用", "悬疑"],
        "asset_type": "prompt_card",
        "intent": "outline_planning",
        "expected_ids": [
            "prompts-card-check_foreshadowing-146",
            "prompts-card-check_foreshadowing_payoff-365",
        ],
        "relevant_ids": [
            "prompts-card-check_foreshadowing-146",
            "prompts-card-check_foreshadowing_payoff-365",
            "prompts-card-generate_foreshadowing-292",
            "prompts-card-generate-cliffhanger-147",
            "prompts-card-inject-cliffhanger-362",
            "prompts-card-outline_golden_three_chapters-41",
        ],
        "notes": "结构层查询，检查伏笔、悬念、章节节奏相关资产是否被召回。",
    },
    {
        "query": "角色状态更新",
        "stage": "setting",
        "topics": ["通用"],
        "asset_type": "prompt_card",
        "intent": "generator",
        "expected_ids": [
            "prompts-card-create_character_profile-9",
            "prompts-card-design_character_arc-122",
        ],
        "relevant_ids": [
            "prompts-card-create_character_profile-9",
            "prompts-card-design_character_arc-122",
            "prompts-card-generate_relationship_chart-80",
            "prompts-card-generate_spinoff_plot-116",
        ],
        "notes": "偏状态表/角色档案维护，验证通用 setting 生成器类卡片。",
    },
    {
        "query": "世界观设定 天堑 内宇宙",
        "stage": "setting",
        "topics": ["玄幻", "科幻", "通用"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "expected_ids": [
            "prompts-card-design_power_system-6",
            "prompts-card-design_infinite_dungeon-21",
        ],
        "relevant_ids": [
            "prompts-card-design_power_system-6",
            "prompts-card-design_infinite_dungeon-21",
            "prompts-card-design_cyber_cultivation-105",
            "prompts-card-design_fermi_paradox_solution-141",
            "base-methodology-writing-worldview-motif-catalog",
        ],
        "notes": "专名较强的世界观设定查询，观察没有精确词时的近邻质量。",
    },
    {
        "query": "反转设计 狗血女文",
        "stage": "framework",
        "topics": ["言情", "女频", "豪门"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "expected_ids": [
            "prompts-card-design-short_drama_twists",
            "prompts-card-construct_plot_twist-367",
        ],
        "relevant_ids": [
            "prompts-card-design-short_drama_twists",
            "prompts-card-construct_plot_twist-367",
            "prompts-card-outline_identity_switch-23",
        ],
        "notes": "女频反转/狗血桥段设计，检查 genre/topic 与语义共同作用。",
    },
    {
        "query": "规则怪谈 副本设计",
        "stage": "setting",
        "topics": ["怪谈", "悬疑", "恐怖"],
        "asset_type": "prompt_card",
        "intent": "generator",
        "expected_ids": [
            "prompts-card-generate_rules_dungeon-8",
            "prompts-card-generate-weird_rules",
        ],
        "relevant_ids": [
            "prompts-card-generate_rules_dungeon-8",
            "prompts-card-generate-weird_rules",
            "prompts-card-design_safe_house_rules-250",
            "prompts-card-write_scp_log-144",
            "prompts-card-write_narrative_via_notes-261",
        ],
        "notes": "规则怪谈强标签查询，预期 Layer 1 与 Layer 2 overlap 较高。",
    },
    {
        "query": "多子多福 奖励机制",
        "stage": "setting",
        "topics": ["系统", "玄幻"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "expected_ids": [
            "prompts-card-design-many_children_system-401",
            "prompts-card-design_system_shop-83",
        ],
        "relevant_ids": [
            "prompts-card-design-many_children_system-401",
            "prompts-card-design_system_shop-83",
            "prompts-card-generate_achievements-210",
            "prompts-card-generate_exchange_list-22",
            "prompts-card-generate_dungeon_rewards-27",
        ],
        "notes": "系统奖励机制查询，检验具体流派名与系统设定资产的距离。",
    },
    {
        "query": "终稿润色 文风统一",
        "stage": "refinement",
        "topics": ["文风"],
        "asset_type": "prompt_card",
        "intent": "editing_transformation",
        "expected_ids": [
            "prompts-card-polish_text_style-363",
        ],
        "relevant_ids": [
            "prompts-card-polish_text_style-363",
            "prompts-card-lock-style_and_restrictions",
            "prompts-card-mimic_character_voice-451",
            "prompts-card-differentiate-379",
        ],
        "notes": "终稿润色查询，使用 schema 内 polish/rewrite 类 editing_transformation，重点看标题是否直接相关。",
    },
    {
        "query": "市场定位 读者画像",
        "stage": "business",
        "topics": ["business", "通用"],
        "asset_type": "methodology",
        "expected_ids": [
            "base-methodology-creative-platform-analysis",
            "base-methodology-market-2026-webnovel-trends",
        ],
        "relevant_ids": [
            "base-methodology-creative-platform-analysis",
            "base-methodology-market-2026-webnovel-trends",
            "base-methodology-market-reading-power-taxonomy",
            "base-methodology-creative-submission-guide",
        ],
        "notes": "商业分析查询，验证 business 阶段是否能召回读者画像/卖点定位 methodology 资产。",
    },
    {
        "query": "第一章 黄金三章 爽点钩子",
        "stage": "framework",
        "topics": ["通用"],
        "asset_type": "prompt_card",
        "intent": "outline_planning",
        "expected_ids": [
            "prompts-card-outline_golden_three_chapters-41",
            "prompts-card-outline_golden_three-12",
        ],
        "relevant_ids": [
            "prompts-card-outline_golden_three_chapters-41",
            "prompts-card-outline_golden_three-12",
            "base-methodology-creative-golden-three",
            "base-methodology-market-reading-power-taxonomy",
        ],
        "notes": "黄金三章/开篇节奏查询，补充常见章节设计场景。",
    },
    {
        "query": "战斗场景 节奏 动作描写",
        "stage": "drafting",
        "topics": ["玄幻", "动作"],
        "asset_type": "prompt_card",
        "intent": "structural_design",
        "expected_ids": [
            "prompts-card-action-beat_sheet-219",
            "prompts-card-choreograph_fight_scene-355",
        ],
        "relevant_ids": [
            "prompts-card-action-beat_sheet-219",
            "prompts-card-choreograph_fight_scene-355",
            "prompts-card-write-combat_scene-13",
            "prompts-card-write_combat_choreography-456",
            "prompts-card-write_combat_psychology-376",
        ],
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
    if not index_path.exists():
        return 0
    try:
        with closing(sqlite3.connect(str(index_path))) as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
    except sqlite3.Error:
        return 0


def grade_distribution(index_path: Path) -> dict[str, int]:
    if not index_path.exists():
        return {}
    with closing(sqlite3.connect(str(index_path))) as conn:
        rows = conn.execute(
            "SELECT quality_grade, COUNT(*) FROM cards GROUP BY quality_grade ORDER BY quality_grade"
        ).fetchall()
    return {str(grade or "UNKNOWN"): int(count) for grade, count in rows}


def compute_ranking_metrics(
    ranked_ids: list[str],
    *,
    expected_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> dict[str, Any]:
    """Score a ranked hit list against the fixed gold set."""
    cutoff = max(0, int(k))
    top_ids = [str(card_id) for card_id in ranked_ids[:cutoff]]
    relevant_set = {str(card_id) for card_id in relevant_ids}
    expected_set = {str(card_id) for card_id in expected_ids}
    hits = [card_id for card_id in top_ids if card_id in relevant_set]
    expected_hits = [card_id for card_id in top_ids if card_id in expected_set]

    recall = len(set(hits)) / len(relevant_set) if relevant_set else 0.0
    expected_recall = len(set(expected_hits)) / len(expected_set) if expected_set else 0.0
    precision = len(hits) / cutoff if cutoff else 0.0
    mrr = 0.0
    for rank, card_id in enumerate(top_ids, start=1):
        if card_id in relevant_set:
            mrr = 1.0 / rank
            break

    dcg = 0.0
    for rank, card_id in enumerate(top_ids, start=1):
        if card_id in relevant_set:
            dcg += 1.0 / math.log2(rank + 1)
    ideal_relevant = min(len(relevant_set), cutoff)
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_relevant + 1))
    ndcg = dcg / ideal_dcg if ideal_dcg else 0.0

    return {
        "k": cutoff,
        "relevant_total": len(relevant_set),
        "expected_total": len(expected_set),
        "hits": len(hits),
        "expected_hits": len(expected_hits),
        "recall_at_k": round(recall, 10),
        "expected_recall_at_k": round(expected_recall, 10),
        "precision_at_k": round(precision, 10),
        "mrr": round(mrr, 10),
        "ndcg_at_k": round(ndcg, 10),
        "hit_ids": hits,
        "expected_hit_ids": expected_hits,
        "missing_expected_ids": sorted(expected_set - set(top_ids)),
        "missing_relevant_ids": sorted(relevant_set - set(top_ids)),
    }


def read_index_cards(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    try:
        with closing(sqlite3.connect(str(index_path))) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, asset_type, stage, topic_json, quality_grade,
                       card_intent, title, source_path, last_updated
                FROM cards
                ORDER BY id
                """
            ).fetchall()
    except sqlite3.Error:
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["topic"] = decode_topic(item.pop("topic_json", "[]"))
        out.append(item)
    return out


def decode_topic(blob: str) -> list[str]:
    try:
        raw = json.loads(blob or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in raw] if isinstance(raw, list) else []


def topic_intersects(card_topics: list[str], wanted_topics: list[str]) -> bool:
    return layer1_topic_hit(card_topics, wanted_topics)


def quality_allowed(grade: str, floor: str) -> bool:
    return QUALITY_ORDER.get(str(grade), 99) <= QUALITY_ORDER.get(str(floor), 99)


def filter_value_matches(filter_name: str, wanted: Any, actual: Any) -> bool:
    if not wanted:
        return True
    allowed = LAYER1_FILTER_EXPANSION.get(filter_name, {}).get(str(wanted), [str(wanted)])
    return str(actual) in {str(item) for item in allowed}


def build_layer1_diagnostics(
    *,
    query_spec: dict[str, Any],
    index_path: Path,
    layer1_ids: list[str],
    quality_floor: str,
    top_k: int,
    candidate_k: int,
) -> dict[str, Any]:
    """Explain how Layer 1 metadata filters shrink the candidate set."""
    cards = read_index_cards(index_path)
    rows = list(cards)
    wanted_topics = [str(topic) for topic in query_spec.get("topics", [])]
    steps: list[dict[str, Any]] = [
        {"filter": "all_indexed_cards", "value": "*", "remaining": len(rows), "removed": 0},
    ]

    filters: list[tuple[str, Any]] = [
        ("stage", query_spec.get("stage")),
        ("asset_type", query_spec.get("asset_type")),
        ("card_intent", query_spec.get("intent")),
        ("quality_floor", quality_floor),
        ("topic", wanted_topics),
    ]

    for name, value in filters:
        before = len(rows)
        if name == "stage" and value:
            rows = [row for row in rows if filter_value_matches("stage", value, row.get("stage"))]
        elif name == "asset_type" and value:
            rows = [row for row in rows if row.get("asset_type") == value]
        elif name == "card_intent" and value:
            rows = [row for row in rows if filter_value_matches("card_intent", value, row.get("card_intent"))]
        elif name == "quality_floor" and value:
            rows = [row for row in rows if quality_allowed(str(row.get("quality_grade", "")), str(value))]
        elif name == "topic" and value:
            rows = [row for row in rows if topic_intersects(row.get("topic", []), wanted_topics)]
        steps.append(
            {
                "filter": name,
                "value": value if value is not None else "",
                "remaining": len(rows),
                "removed": before - len(rows),
            }
        )

    gold_ids = sorted(set(query_spec.get("expected_ids", [])) | set(query_spec.get("relevant_ids", [])))
    by_id = {str(row.get("id", "")): row for row in cards}
    gold_blockers: list[dict[str, Any]] = []
    for card_id in gold_ids:
        if card_id in layer1_ids:
            continue
        row = by_id.get(card_id)
        if row is None:
            gold_blockers.append({"id": card_id, "title": "", "blocked_by": ["missing_from_index"]})
            continue
        blocked_by: list[dict[str, Any]] = []
        if query_spec.get("stage") and not filter_value_matches("stage", query_spec.get("stage"), row.get("stage")):
            blocked_by.append({"filter": "stage", "wanted": query_spec.get("stage"), "actual": row.get("stage")})
        if query_spec.get("asset_type") and row.get("asset_type") != query_spec.get("asset_type"):
            blocked_by.append(
                {"filter": "asset_type", "wanted": query_spec.get("asset_type"), "actual": row.get("asset_type")}
            )
        if query_spec.get("intent") and not filter_value_matches(
            "card_intent", query_spec.get("intent"), row.get("card_intent")
        ):
            blocked_by.append(
                {"filter": "card_intent", "wanted": query_spec.get("intent"), "actual": row.get("card_intent")}
            )
        if not quality_allowed(str(row.get("quality_grade", "")), quality_floor):
            blocked_by.append(
                {"filter": "quality_floor", "wanted": quality_floor, "actual": row.get("quality_grade")}
            )
        if wanted_topics and not topic_intersects(row.get("topic", []), wanted_topics):
            blocked_by.append({"filter": "topic", "wanted": wanted_topics, "actual": row.get("topic", [])})
        gold_blockers.append(
            {
                "id": card_id,
                "title": row.get("title", ""),
                "blocked_by": blocked_by
                or [{"filter": "candidate_k", "wanted": candidate_k, "actual": "candidate_after_cutoff"}],
            }
        )

    if not layer1_ids:
        status = "empty"
    elif len(layer1_ids) < min(top_k, len(set(query_spec.get("relevant_ids", [])))):
        status = "narrow"
    elif gold_blockers:
        status = "gold_miss"
    else:
        status = "ok"

    return {
        "status": status,
        "candidate_k": candidate_k,
        "top_k": top_k,
        "candidate_count_before_top_k": len(rows),
        "returned_count": len(layer1_ids),
        "filter_steps": steps,
        "gold_blockers": gold_blockers,
    }


def evaluate_query(
    query_spec: dict[str, Any],
    *,
    index_path: Path,
    embedder: DeterministicTextEmbedder,
    backend: SQLiteVecBackend,
    candidate_k: int = CANDIDATE_K,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    asset_type = str(query_spec["asset_type"])
    card_intent = query_spec.get("intent")
    expected_ids = [str(card_id) for card_id in query_spec.get("expected_ids", [])]
    relevant_ids = [str(card_id) for card_id in query_spec.get("relevant_ids", [])]
    quality_floor = "B"
    layer1_hits = layer1_recall(
        stage=query_spec["stage"],
        topic=query_spec["topics"],
        asset_type=asset_type,
        card_intent=card_intent,
        top_k=candidate_k,
        quality_floor=quality_floor,
        index_path=index_path,
        config=EVAL_RECALL_CONFIG,
    )
    layer1_ids = [str(hit.get("id", "")) for hit in layer1_hits]
    layer1_diagnostics = build_layer1_diagnostics(
        query_spec=query_spec,
        index_path=index_path,
        layer1_ids=layer1_ids,
        quality_floor=quality_floor,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    native_search_error = ""
    try:
        layer2_hits = search_vector(
            index_path,
            str(query_spec["query"]),
            embedder=embedder,
            top_k=top_k,
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
            top_k=top_k,
            candidate_ids=layer1_ids or None,
            model_id=MODEL_ID,
            backend=None,
        )
    layer2_ids = [str(hit.get("id", "")) for hit in layer2_hits]
    overlap_ids = [card_id for card_id in layer2_ids if card_id in set(layer1_ids)]
    overlap_ratio = len(overlap_ids) / max(1, min(len(layer1_ids), len(layer2_ids)))

    return {
        "query": query_spec["query"],
        "gold": {
            "expected_ids": expected_ids,
            "relevant_ids": relevant_ids,
        },
        "filters": {
            "stage": query_spec["stage"],
            "topics": query_spec["topics"],
            "asset_type": asset_type,
            "card_intent": card_intent,
            "quality_floor": quality_floor,
            "candidate_k": candidate_k,
            "top_k": top_k,
        },
        "layer1": {
            "ids": layer1_ids,
            "titles": [str(hit.get("title", "")) for hit in layer1_hits],
            "hits": [compact_hit(hit) for hit in layer1_hits],
            "metrics": compute_ranking_metrics(
                layer1_ids,
                expected_ids=expected_ids,
                relevant_ids=relevant_ids,
                k=top_k,
            ),
            "diagnostics": layer1_diagnostics,
        },
        "layer2": {
            "ids": layer2_ids,
            "titles": [str(hit.get("title", "")) for hit in layer2_hits],
            "scores": [round(float(hit.get("_vector_score", hit.get("_score", 0.0)) or 0.0), 6) for hit in layer2_hits],
            "hits": [compact_hit(hit, include_score=True) for hit in layer2_hits],
            "metrics": compute_ranking_metrics(
                layer2_ids,
                expected_ids=expected_ids,
                relevant_ids=relevant_ids,
                k=top_k,
            ),
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
    layer1_metrics = summary["metrics"]["layer1"]
    layer2_metrics = summary["metrics"]["layer2"]
    top_k = int(environment.get("top_k", TOP_K))
    candidate_k = int(environment.get("candidate_k", CANDIDATE_K))
    lines: list[str] = [
        "# RAG 真实召回质量评估报告",
        "",
        f"- 生成来源: `{payload['generated_from']}`",
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
        (
            f"- Layer 1 gold 指标: recall@{top_k}={layer1_metrics['recall_at_k']:.3f}，"
            f"precision@{top_k}={layer1_metrics['precision_at_k']:.3f}，"
            f"MRR={layer1_metrics['mrr']:.3f}，nDCG@{top_k}={layer1_metrics['ndcg_at_k']:.3f}。"
        ),
        (
            f"- Layer 2 gold 指标: expected_recall@{top_k}={layer2_metrics['expected_recall_at_k']:.3f}，"
            f"recall@{top_k}={layer2_metrics['recall_at_k']:.3f}，"
            f"precision@{top_k}={layer2_metrics['precision_at_k']:.3f}，"
            f"MRR={layer2_metrics['mrr']:.3f}，nDCG@{top_k}={layer2_metrics['ndcg_at_k']:.3f}。"
        ),
        (
            f"- Layer 1 给 Layer 2 的候选池 candidate_k={candidate_k}；"
            f"最终评估 metrics 固定按 top_k={top_k}。"
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
        f"- 每条查询先按 stage/topic/asset_type/card_intent/quality_floor 做 Layer 1 过滤；Layer 1 产出 candidate_k={candidate_k} 候选池，Layer 2 在候选内做 top_k={top_k} 重排；Layer 1 为空时记录一次全局 Layer 2 诊断。",
        "- embedding 使用项目内离线 `DeterministicTextEmbedder`，不调用 LLM，不发网络请求。",
        "",
        "## Layer 1 Blocker Summary",
        "",
        "| blocked_by | gold id count |",
        "|---|---:|",
        *[
            f"| {key} | {int(summary['layer1_blocker_summary'].get(key, 0))} |"
            for key in BLOCKER_KEYS
        ],
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
                    f"- Filters: stage=`{item['filters'].get('stage', 'unknown')}`, "
                    f"topics=`{item['filters'].get('topics', [])}`, "
                    f"asset_type=`{item['filters'].get('asset_type', 'unknown')}`, "
                    f"intent=`{item['filters'].get('card_intent') or 'none'}`, "
                    f"candidate_k=`{item['filters'].get('candidate_k', candidate_k)}`, "
                    f"top_k=`{item['filters'].get('top_k', top_k)}`"
                ),
                f"- Layer 1: {format_hits(item['layer1'].get('hits', []))}",
                f"- Layer 1 metrics: {format_metrics(item['layer1']['metrics'], default_k=top_k)}",
                f"- Layer 2: {format_hits(item['layer2'].get('hits', []))}",
                f"- Layer 2 metrics: {format_metrics(item['layer2']['metrics'], default_k=top_k)}",
                f"- Layer 1 diagnostic: {format_diagnostics(item['layer1']['diagnostics'])}",
                f"- Overlap: {item['overlap'].get('count', 0)} / ratio {item['overlap'].get('ratio', 0.0)}",
                f"- Notes: {item.get('notes', '')}",
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


def format_metrics(metrics: dict[str, Any], *, default_k: int = TOP_K) -> str:
    k = int(metrics.get("k", default_k))
    return (
        f"expected_recall@{k}={metrics.get('expected_recall_at_k', 0.0):.3f}, "
        f"recall@{k}={metrics['recall_at_k']:.3f}, "
        f"precision@{k}={metrics['precision_at_k']:.3f}, "
        f"MRR={metrics['mrr']:.3f}, "
        f"nDCG@{k}={metrics['ndcg_at_k']:.3f}, "
        f"hits={metrics.get('hits', 0)}/{metrics.get('relevant_total', 0)}"
    )


def format_diagnostics(diagnostics: dict[str, Any]) -> str:
    status = diagnostics.get("status", "unknown")
    blockers = diagnostics.get("gold_blockers") or []
    if not blockers:
        return str(status)
    fragments: list[str] = []
    for blocker in blockers[:3]:
        blocked_by = blocker.get("blocked_by") or []
        filters = [str(item.get("filter", "")) for item in blocked_by if isinstance(item, dict)]
        fragments.append(f"{blocker.get('id', '')} blocked_by={filters}")
    suffix = "; ".join(fragments)
    if len(blockers) > 3:
        suffix += f"; +{len(blockers) - 3} more"
    return f"{status}; {suffix}"


def average_metrics(results: list[dict[str, Any]], layer_name: str) -> dict[str, float]:
    keys = ["recall_at_k", "expected_recall_at_k", "precision_at_k", "mrr", "ndcg_at_k"]
    if not results:
        return {key: 0.0 for key in keys}
    return {
        key: round(
            sum(float(result[layer_name]["metrics"].get(key, 0.0)) for result in results) / max(1, len(results)),
            6,
        )
        for key in keys
    }


def summarize_layer1_blockers(results: list[dict[str, Any]]) -> dict[str, int]:
    """Count how many missed gold ids each Layer 1 blocker explains."""
    counts: Counter[str] = Counter({key: 0 for key in BLOCKER_KEYS})
    for result in results:
        diagnostics = result.get("layer1", {}).get("diagnostics", {})
        for blocker in diagnostics.get("gold_blockers") or []:
            seen_for_gold: set[str] = set()
            for item in blocker.get("blocked_by") or []:
                if isinstance(item, str):
                    key = item
                elif isinstance(item, dict):
                    key = str(item.get("filter", ""))
                else:
                    key = ""
                if key in BLOCKER_KEYS:
                    seen_for_gold.add(key)
            for key in seen_for_gold:
                counts[key] += 1
    return {key: int(counts[key]) for key in BLOCKER_KEYS}


def build_payload(
    *,
    results: list[dict[str, Any]],
    source_paths: list[Path],
    prompts_dir: Path,
    index_path: Path,
    json_path: Path,
    report_path: Path,
    index_stats: Any,
    vector_stats_obj: Any,
    ready: Any,
    backend_available: bool,
    quality_grade_distribution: dict[str, int],
) -> dict[str, Any]:
    native_used = any(bool(item.get("native_sqlite_vec")) for item in results)
    native_search_errors = sorted({item.get("native_search_error", "") for item in results if item.get("native_search_error")})
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

    diagnostics_by_status: dict[str, list[str]] = {}
    for item in results:
        status = str(item.get("layer1", {}).get("diagnostics", {}).get("status", "unknown"))
        if status != "ok":
            diagnostics_by_status.setdefault(status, []).append(str(item["query"]))

    payload: dict[str, Any] = {
        "generated_from": "scripts/evaluate_rag_recall.py",
        "environment": {
            "python": sys.version.split()[0],
            "sqlite_version": sqlite3.sqlite_version,
            "sqlite_vec_module_available": bool(backend_available),
            "prompts_dir": repo_relative(prompts_dir),
            "sources": [repo_relative(path) for path in source_paths],
            "index_path": repo_relative(index_path),
            "json_path": repo_relative(json_path),
            "report_path": repo_relative(report_path),
            "model_id": EVAL_MODEL_ID,
            "candidate_k": int(results[0].get("filters", {}).get("candidate_k", CANDIDATE_K)) if results else CANDIDATE_K,
            "top_k": int(results[0].get("filters", {}).get("top_k", TOP_K)) if results else TOP_K,
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
            "native_sqlite_vec_available": bool(backend_available),
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
            "layer1_diagnostics_by_status": diagnostics_by_status,
            "quality_grade_distribution": quality_grade_distribution,
            "intent_distribution_top10": Counter(
                result["filters"]["card_intent"] for result in results
            ).most_common(10),
            "layer1_blocker_summary": summarize_layer1_blockers(results),
            "metrics": {
                "layer1": average_metrics(results, "layer1"),
                "layer2": average_metrics(results, "layer2"),
            },
        },
        "queries": results,
    }
    payload["observations"] = make_observations(results, vector_stats)
    payload["recommendations"] = make_recommendations(results)
    return payload


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
    diagnostic_statuses = {
        status: [
            item["query"]
            for item in results
            if item.get("layer1", {}).get("diagnostics", {}).get("status") == status
        ]
        for status in ["narrow", "gold_miss"]
    }
    if diagnostic_statuses["narrow"]:
        observations.append(f"Layer 1 窄召回查询: {diagnostic_statuses['narrow']}。请查看每条 query 的 gold_blockers。")
    if diagnostic_statuses["gold_miss"]:
        observations.append(
            f"Layer 1 非空但漏掉 gold id 的查询: {diagnostic_statuses['gold_miss']}。这通常是 stage/topic/card_intent 过窄或 top_k 截断。"
        )
    if vector_stats["storage"] != "sqlite-vec":
        observations.append("native sqlite-vec 未成为最终查询路径，评估结果使用 JSON 向量余弦 fallback。")
    native_errors = sorted({item["native_search_error"] for item in results if item.get("native_search_error")})
    if native_errors:
        observations.append(f"native sqlite-vec 查询失败后已回退 JSON 向量，错误样例: {native_errors[:2]}。")
    observations.append("DeterministicTextEmbedder 是 token hashing，适合复现 smoke/趋势评估，但不等价于生产级语义 embedding。")
    return observations


def make_recommendations(results: list[dict[str, Any]]) -> list[str]:
    layer2_metrics = average_metrics(results, "layer2") if results else {}
    expected_recall = float(layer2_metrics.get("expected_recall_at_k", 0.0))
    recall = float(layer2_metrics.get("recall_at_k", 0.0))
    recommendations = [
        "把本脚本纳入后续资产变更后的固定评估入口，用 JSON diff 跟踪召回质量漂移。",
        "持续维护 expected/relevant id 集合；新增资产或重标 metadata 时同步更新 gold set。",
        "针对 Layer 1 空召回或明显窄召回的 query，优先补 metadata topic/card_intent，而不是先改检索代码。",
    ]
    if expected_recall < 0.7:
        recommendations.append(
            f"下一轮目标先把 Layer 2 expected_recall@{TOP_K} 拉到 0.700+，recall@{TOP_K} 再逐步追。"
        )
    elif recall >= 0.5:
        recommendations.append(
            f"Layer 2 expected_recall@{TOP_K} 已达到 {expected_recall:.3f}，"
            f"recall@{TOP_K} 已达到 {recall:.3f}；下一轮优先压低 candidate_k 残余 blocker 并守住 0.500+。"
        )
    else:
        recommendations.append(
            f"Layer 2 expected_recall@{TOP_K} 已达到 {expected_recall:.3f}；下一轮优先把 recall@{TOP_K} 从 {recall:.3f} 往 0.500+ 推。"
        )
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
    payload = build_payload(
        results=results,
        source_paths=source_paths,
        prompts_dir=prompts_dir,
        index_path=index_path,
        json_path=json_path,
        report_path=report_path,
        index_stats=index_stats,
        vector_stats_obj=vector_stats_obj,
        ready=ready,
        backend_available=backend.available,
        quality_grade_distribution=grade_distribution(index_path),
    )

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown_report(payload), encoding="utf-8")
    print(
        f"wrote {repo_relative(json_path)} and {repo_relative(report_path)}; "
        f"cards={index_stats.cards_indexed} vectors={vector_stats_obj.vectors_indexed} "
        f"native_used={payload['summary']['native_sqlite_vec_used']} fallback={payload['summary']['fallback_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
