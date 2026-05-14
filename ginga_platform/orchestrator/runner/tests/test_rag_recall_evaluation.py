"""Regression tests for the fixed RAG recall evaluation query set."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[4]


class RagRecallEvaluationTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
