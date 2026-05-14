"""Regression tests for the fixed RAG recall evaluation query set."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[4]


class RagRecallEvaluationTest(unittest.TestCase):
    def test_fixed_query_set_has_gold_ids_for_every_query(self) -> None:
        """Every fixed recall query must carry a gold set for regression scoring."""
        from scripts.evaluate_rag_recall import QUERY_SET

        self.assertEqual(len(QUERY_SET), 12)

        missing: dict[str, list[str]] = {}
        for item in QUERY_SET:
            expected_ids = item.get("expected_ids")
            relevant_ids = item.get("relevant_ids")
            problems: list[str] = []
            if not isinstance(expected_ids, list) or not expected_ids:
                problems.append("expected_ids")
            if not isinstance(relevant_ids, list) or not relevant_ids:
                problems.append("relevant_ids")
            if isinstance(expected_ids, list) and isinstance(relevant_ids, list):
                expected_set = set(expected_ids)
                relevant_set = set(relevant_ids)
                if not expected_set.issubset(relevant_set):
                    problems.append("expected_not_subset_of_relevant")
            if problems:
                missing[str(item.get("query", "<missing-query>"))] = problems

        self.assertEqual(missing, {})

    def test_metric_helpers_score_ranked_hits_against_gold_set(self) -> None:
        from scripts.evaluate_rag_recall import compute_ranking_metrics, format_metrics

        metrics = compute_ranking_metrics(
            ["doc-c", "doc-a", "doc-x"],
            expected_ids=["doc-a"],
            relevant_ids=["doc-a", "doc-b"],
            k=3,
        )

        self.assertEqual(metrics["hits"], 1)
        self.assertAlmostEqual(metrics["recall_at_k"], 0.5)
        self.assertAlmostEqual(metrics["precision_at_k"], 1 / 3)
        self.assertAlmostEqual(metrics["mrr"], 0.5)
        self.assertGreater(metrics["ndcg_at_k"], 0.0)
        self.assertLessEqual(metrics["ndcg_at_k"], 1.0)
        self.assertIn("expected_recall@3=1.000", format_metrics(metrics))

    def test_diagnostics_topic_intersection_uses_layer1_aliases(self) -> None:
        from scripts.evaluate_rag_recall import topic_intersects

        self.assertTrue(topic_intersects(["规则怪谈"], ["怪谈"]))
        self.assertTrue(topic_intersects(["general"], ["通用"]))
        self.assertTrue(topic_intersects(["战斗"], ["动作"]))
        self.assertTrue(topic_intersects(["系统流"], ["系统"]))

    def test_diagnostics_filter_matches_use_configured_expansion(self) -> None:
        from scripts.evaluate_rag_recall import filter_value_matches

        self.assertTrue(filter_value_matches("stage", "framework", "outline"))
        self.assertTrue(filter_value_matches("stage", "framework", "analysis"))
        self.assertTrue(filter_value_matches("stage", "drafting", "outline"))
        self.assertTrue(filter_value_matches("stage", "drafting", "setting"))
        self.assertFalse(filter_value_matches("stage", "drafting", "analysis"))
        self.assertTrue(filter_value_matches("card_intent", "structural_design", "simulation"))
        self.assertTrue(filter_value_matches("card_intent", "prose_generation", "outline_planning"))
        self.assertTrue(filter_value_matches("card_intent", "prose_generation", "prototype_creation"))
        self.assertTrue(filter_value_matches("card_intent", "generator", "prototype_creation"))
        self.assertFalse(filter_value_matches("card_intent", "prose_generation", "simulation"))

    def test_evaluation_query_intents_are_prompt_card_schema_values(self) -> None:
        """Only prompt-card evaluation queries must use prompt-card schema intents."""
        from scripts.evaluate_rag_recall import QUERY_SET

        schema = yaml.safe_load((_REPO_ROOT / "foundation/schema/prompt_card.yaml").read_text(encoding="utf-8"))
        allowed = set(schema["fields"]["card_intent"]["enum"])
        invalid = [
            (item["query"], item["intent"])
            for item in QUERY_SET
            if item.get("asset_type") == "prompt_card" and item.get("intent") not in allowed
        ]
        self.assertEqual(invalid, [])

        methodology_queries = [item for item in QUERY_SET if item.get("asset_type") == "methodology"]
        self.assertGreaterEqual(len(methodology_queries), 1)
        self.assertTrue(all(not item.get("intent") for item in methodology_queries))

    def test_historical_empty_layer1_queries_have_candidates(self) -> None:
        """Historical empty Layer 1 queries should have at least one true frontmatter candidate."""
        from rag.index_builder import build_index
        from rag.layer1_filter import recall
        from scripts.evaluate_rag_recall import DEFAULT_SOURCES, QUERY_SET, TOP_K

        target_queries = {
            "反转设计 狗血女文",
            "终稿润色 文风统一",
            "市场定位 读者画像",
        }
        specs = [item for item in QUERY_SET if item["query"] in target_queries]
        self.assertEqual({item["query"] for item in specs}, target_queries)

        with tempfile.TemporaryDirectory() as d:
            index_path = Path(d) / "rag_eval.sqlite"
            stats = build_index(DEFAULT_SOURCES, index_path)
            self.assertGreaterEqual(stats.cards_indexed, 461)

            empty: dict[str, list[str]] = {}
            for spec in specs:
                hits = recall(
                    stage=spec["stage"],
                    topic=spec["topics"],
                    asset_type=spec["asset_type"],
                    card_intent=spec.get("intent"),
                    top_k=TOP_K,
                    quality_floor="B",
                    index_path=index_path,
                    config={"stage_specific_top_k": {"default": TOP_K}},
                )
                if not hits:
                    empty[spec["query"]] = [
                        f"stage={spec['stage']}",
                        f"topics={spec['topics']}",
                        f"asset_type={spec['asset_type']}",
                        f"intent={spec.get('intent')}",
                    ]
                if spec["query"] == "市场定位 读者画像":
                    hit_ids = [str(hit.get("id", "")) for hit in hits]
                    self.assertNotIn("prompts-card-461", hit_ids)
                    self.assertTrue(any(card_id.startswith("base-methodology-") for card_id in hit_ids), hit_ids)

            self.assertEqual(empty, {})

    def test_default_sources_include_prompts_and_methodology(self) -> None:
        from scripts.evaluate_rag_recall import DEFAULT_PROMPTS_DIR, DEFAULT_SOURCES, resolve_source_paths

        relative_sources = {source.relative_to(_REPO_ROOT).as_posix() for source in DEFAULT_SOURCES}
        self.assertEqual(
            relative_sources,
            {
                "foundation/assets/prompts",
                "foundation/assets/methodology",
            },
        )

        custom_prompts = _REPO_ROOT / "custom-prompts"
        resolved = [path.relative_to(_REPO_ROOT).as_posix() for path in resolve_source_paths(custom_prompts, None)]
        self.assertEqual(resolved, ["custom-prompts", "foundation/assets/methodology"])

        explicit = resolve_source_paths(DEFAULT_PROMPTS_DIR, [_REPO_ROOT / "foundation/assets/methodology"])
        self.assertEqual(
            [path.relative_to(_REPO_ROOT).as_posix() for path in explicit],
            ["foundation/assets/prompts", "foundation/assets/methodology"],
        )

    def test_query_result_contains_gold_metrics_and_layer1_filter_diagnostics(self) -> None:
        from rag.index_builder import build_index
        from rag.layer2_vector import DeterministicTextEmbedder, SQLiteVecBackend, build_vector_index
        from scripts.evaluate_rag_recall import EVAL_MODEL_ID, evaluate_query

        query_spec = {
            "query": "diagnostic narrow query",
            "stage": "drafting",
            "topics": ["topic-that-does-not-exist"],
            "asset_type": "prompt_card",
            "intent": "prose_generation",
            "expected_ids": ["prompts-card-write-combat_scene-13"],
            "relevant_ids": ["prompts-card-write-combat_scene-13"],
            "notes": "Exercise empty/narrow Layer 1 diagnostics.",
        }

        with tempfile.TemporaryDirectory() as d:
            index_path = Path(d) / "rag_eval.sqlite"
            build_index([_REPO_ROOT / "foundation/assets/prompts"], index_path)
            embedder = DeterministicTextEmbedder()
            backend = SQLiteVecBackend()
            build_vector_index(index_path, embedder, model_id=EVAL_MODEL_ID, backend=backend)

            result = evaluate_query(query_spec, index_path=index_path, embedder=embedder, backend=backend)

        self.assertIn("gold", result)
        self.assertEqual(result["gold"]["expected_ids"], ["prompts-card-write-combat_scene-13"])
        self.assertIn("metrics", result["layer1"])
        self.assertIn("metrics", result["layer2"])
        self.assertIn("diagnostics", result["layer1"])
        self.assertEqual(result["layer1"]["diagnostics"]["status"], "empty")
        self.assertGreater(result["layer1"]["diagnostics"]["filter_steps"][0]["remaining"], 0)
        self.assertEqual(result["layer1"]["diagnostics"]["filter_steps"][-1]["remaining"], 0)
        self.assertEqual(result["filters"]["top_k"], 5)
        self.assertEqual(result["filters"]["candidate_k"], 20)
        self.assertEqual(result["layer1"]["diagnostics"]["candidate_k"], 20)

    def test_candidate_k_expands_layer2_pool_without_changing_metric_k(self) -> None:
        from scripts.evaluate_rag_recall import EVAL_MODEL_ID, evaluate_query

        query_spec = {
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
            "notes": "Exercise candidate_k decoupling from final top_k.",
        }

        with tempfile.TemporaryDirectory() as d:
            index_path = Path(d) / "rag_eval.sqlite"
            from rag.index_builder import build_index
            from rag.layer2_vector import DeterministicTextEmbedder, SQLiteVecBackend, build_vector_index

            build_index([_REPO_ROOT / "foundation/assets/prompts"], index_path)
            embedder = DeterministicTextEmbedder()
            backend = SQLiteVecBackend()
            build_vector_index(index_path, embedder, model_id=EVAL_MODEL_ID, backend=backend)

            result = evaluate_query(
                query_spec,
                index_path=index_path,
                embedder=embedder,
                backend=backend,
                candidate_k=9,
                top_k=5,
            )

        self.assertEqual(result["filters"]["candidate_k"], 9)
        self.assertEqual(result["filters"]["top_k"], 5)
        self.assertLessEqual(len(result["layer1"]["ids"]), 9)
        self.assertLessEqual(len(result["layer2"]["ids"]), 5)
        self.assertEqual(result["layer1"]["metrics"]["k"], 5)
        self.assertEqual(result["layer2"]["metrics"]["k"], 5)

    def test_stable_payload_omits_wall_clock_time_for_json_diffing(self) -> None:
        from scripts.evaluate_rag_recall import build_payload

        minimal_results = [
            {
                "query": "q",
                "filters": {"card_intent": None},
                "layer1": {"ids": ["a"], "metrics": {"recall_at_k": 1.0, "precision_at_k": 1.0, "mrr": 1.0, "ndcg_at_k": 1.0}},
                "layer2": {"ids": ["a"], "metrics": {"recall_at_k": 1.0, "precision_at_k": 1.0, "mrr": 1.0, "ndcg_at_k": 1.0}},
                "overlap": {"ratio": 1.0},
                "native_search_error": "",
            }
        ]
        common = {
            "source_paths": [_REPO_ROOT / "foundation/assets/prompts"],
            "prompts_dir": _REPO_ROOT / "foundation/assets/prompts",
            "index_path": _REPO_ROOT / ".ops/validation/test.sqlite",
            "json_path": _REPO_ROOT / ".ops/validation/test.json",
            "report_path": _REPO_ROOT / ".ops/reports/test.md",
            "index_stats": type("Stats", (), {"cards_indexed": 1, "to_dict": lambda self: {"cards_indexed": 1}})(),
            "vector_stats_obj": type(
                "VectorStats",
                (),
                {
                    "vectors_indexed": 1,
                    "storage": "sqlite-json",
                    "to_dict": lambda self: {"vectors_indexed": 1, "storage": "sqlite-json"},
                },
            )(),
            "ready": type("Ready", (), {"ready": True, "reason": "ready"})(),
            "backend_available": False,
            "quality_grade_distribution": {"A": 1},
        }

        first = build_payload(results=minimal_results, **common)
        second = build_payload(results=minimal_results, **common)

        self.assertEqual(first, second)
        self.assertNotIn("generated_at", first)
        self.assertIn("generated_from", first)

    def test_payload_summarizes_layer1_gold_blockers(self) -> None:
        from scripts.evaluate_rag_recall import build_payload

        minimal_results = [
            {
                "query": "q",
                "filters": {"card_intent": "prose_generation", "candidate_k": 20},
                "layer1": {
                    "ids": [],
                    "metrics": {"recall_at_k": 0.0, "expected_recall_at_k": 0.0, "precision_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0},
                    "diagnostics": {
                        "status": "gold_miss",
                        "gold_blockers": [
                            {"id": "gold-stage", "blocked_by": [{"filter": "stage"}]},
                            {"id": "gold-topic", "blocked_by": [{"filter": "topic"}]},
                            {"id": "gold-topic-candidate", "blocked_by": [{"filter": "topic"}, {"filter": "candidate_k"}]},
                            {"id": "gold-topk", "blocked_by": [{"filter": "top_k"}]},
                            {"id": "gold-missing", "blocked_by": ["missing_from_index"]},
                        ],
                    },
                },
                "layer2": {"ids": [], "metrics": {"recall_at_k": 0.0, "expected_recall_at_k": 0.0, "precision_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}},
                "overlap": {"ratio": 0.0},
                "native_search_error": "",
            }
        ]
        common = {
            "source_paths": [_REPO_ROOT / "foundation/assets/prompts"],
            "prompts_dir": _REPO_ROOT / "foundation/assets/prompts",
            "index_path": _REPO_ROOT / ".ops/validation/test.sqlite",
            "json_path": _REPO_ROOT / ".ops/validation/test.json",
            "report_path": _REPO_ROOT / ".ops/reports/test.md",
            "index_stats": type("Stats", (), {"cards_indexed": 1, "to_dict": lambda self: {"cards_indexed": 1}})(),
            "vector_stats_obj": type(
                "VectorStats",
                (),
                {
                    "vectors_indexed": 1,
                    "storage": "sqlite-json",
                    "to_dict": lambda self: {"vectors_indexed": 1, "storage": "sqlite-json"},
                },
            )(),
            "ready": type("Ready", (), {"ready": True, "reason": "ready"})(),
            "backend_available": False,
            "quality_grade_distribution": {"A": 1},
        }

        payload = build_payload(results=minimal_results, **common)
        summary = payload["summary"]["layer1_blocker_summary"]

        self.assertEqual(summary["stage"], 1)
        self.assertEqual(summary["topic"], 2)
        self.assertEqual(summary["candidate_k"], 1)
        self.assertEqual(summary["top_k"], 1)
        self.assertEqual(summary["missing_from_index"], 1)
        self.assertEqual(summary["asset_type"], 0)
        self.assertEqual(summary["card_intent"], 0)
        self.assertEqual(summary["quality_floor"], 0)
        report = __import__("scripts.evaluate_rag_recall", fromlist=["build_markdown_report"]).build_markdown_report(payload)
        self.assertIn("## Layer 1 Blocker Summary", report)
        self.assertIn("| topic | 2 |", report)

    def test_recommendations_do_not_repeat_met_expected_recall_target(self) -> None:
        from scripts.evaluate_rag_recall import make_recommendations

        results = [
            {
                "query": "q",
                "layer2": {
                    "metrics": {
                        "expected_recall_at_k": 1.0,
                        "recall_at_k": 0.5,
                        "precision_at_k": 0.5,
                        "mrr": 1.0,
                        "ndcg_at_k": 0.8,
                    }
                },
            }
        ]

        recommendations = make_recommendations(results)

        self.assertFalse(any("expected_recall@5 拉到 0.700+" in item for item in recommendations))
        self.assertTrue(any("expected_recall@5 已达到" in item for item in recommendations))


if __name__ == "__main__":
    unittest.main()
