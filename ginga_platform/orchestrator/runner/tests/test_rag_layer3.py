"""Unit tests for Sprint 3 RAG Layer 3 rerank."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping


def _write_card_md(dirp: Path, slug: str, meta: dict[str, Any], body: str) -> Path:
    import yaml as _yaml

    fp = dirp / f"{slug}.md"
    fp.write_text(
        "---\n" + _yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body + "\n",
        encoding="utf-8",
    )
    return fp


class SimpleEmbedder:
    def embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [float(lowered.count("dragon")), float(lowered.count("romance"))]


class RagLayer3Test(unittest.TestCase):
    def test_should_rerank_refinement_true_and_drafting_false(self) -> None:
        from rag.reranker import should_rerank

        config = {
            "enable_rerank_by_stage": {
                "refinement": True,
                "drafting": False,
                "default": False,
            }
        }

        self.assertTrue(should_rerank("refinement", config))
        self.assertFalse(should_rerank("drafting", config))
        self.assertFalse(should_rerank("setting", config))

    def test_rerank_candidates_uses_llm_ids(self) -> None:
        from rag.reranker import rerank_candidates

        candidates = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

        def llm(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"ids": ["c", "a"]}

        ranked = rerank_candidates("query", candidates, llm)
        self.assertEqual([c["id"] for c in ranked], ["c", "a"])

    def test_bad_llm_response_fails_open_original_order(self) -> None:
        from rag.reranker import rerank_candidates

        candidates = [{"id": "a"}, {"id": "b"}, {"id": "c"}]

        def llm(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
            return {"ids": ["missing", "a"]}

        ranked = rerank_candidates("query", candidates, llm)
        self.assertEqual(ranked, candidates)

        def broken(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
            raise TimeoutError("slow")

        self.assertEqual(rerank_candidates("query", candidates, broken), candidates)

    def test_retriever_applies_rerank_for_refinement_only(self) -> None:
        from rag.index_builder import build_index
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for slug, body in [("dragon", "dragon dragon"), ("romance", "romance romance")]:
                _write_card_md(
                    src,
                    slug,
                    {
                        "id": f"card-{slug}",
                        "asset_type": "prompt_card",
                        "title": slug,
                        "topic": ["玄幻"],
                        "stage": "refinement",
                        "quality_grade": "A",
                        "card_intent": "prose_generation",
                        "source_path": f"{slug}.md",
                        "last_updated": "2026-05-12",
                    },
                    body,
                )
            idx = root / "index.sqlite"
            build_index([src], idx)
            build_vector_index(idx, SimpleEmbedder())

            def reverse_llm(_payload: Mapping[str, Any]) -> Mapping[str, Any]:
                return {"ids": ["card-romance", "card-dragon"]}

            config = {
                "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                "cold_start": {"enabled_layers": [1]},
                "stage_specific_top_k": {"refinement": 2, "drafting": 2, "default": 2},
                "enable_rerank_by_stage": {
                    "refinement": True,
                    "drafting": False,
                    "default": False,
                },
            }
            refined = recall_cards(
                stage="refinement",
                topic=None,
                query_text="dragon",
                top_k=2,
                index_path=idx,
                embedder=SimpleEmbedder(),
                llm_caller=reverse_llm,
                config=config,
            )
            self.assertEqual([c["id"] for c in refined["cards"]], ["card-romance", "card-dragon"])
            self.assertEqual(refined["diagnostics"]["used_layers"], [1, 2, 3])

            drafted = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon",
                top_k=2,
                index_path=idx,
                embedder=SimpleEmbedder(),
                llm_caller=reverse_llm,
                config=config,
            )
            self.assertEqual(drafted["diagnostics"]["used_layers"], [1])
            self.assertNotIn(3, drafted["diagnostics"]["used_layers"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
