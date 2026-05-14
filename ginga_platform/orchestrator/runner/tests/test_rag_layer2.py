"""Unit tests for Sprint 3 RAG Layer 2 vector recall."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any


def _write_card_md(dirp: Path, slug: str, meta: dict[str, Any], body: str) -> Path:
    import yaml as _yaml

    fp = dirp / f"{slug}.md"
    fp.write_text(
        "---\n" + _yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body + "\n",
        encoding="utf-8",
    )
    return fp


class KeywordEmbedder:
    """Small deterministic embedder for tests."""

    def embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            float(lowered.count("dragon") + lowered.count("玄幻")),
            float(lowered.count("romance") + lowered.count("爱情")),
            float(lowered.count("spaceship") + lowered.count("科幻")),
        ]


class RagLayer2Test(unittest.TestCase):
    def _build_index(self, root: Path) -> Path:
        from rag.index_builder import build_index

        src = root / "prompts"
        src.mkdir()
        _write_card_md(
            src,
            "dragon",
            {
                "id": "card-dragon",
                "asset_type": "prompt_card",
                "title": "Dragon battle",
                "topic": ["玄幻"],
                "stage": "drafting",
                "quality_grade": "B+",
                "card_intent": "prose_generation",
                "source_path": "dragon.md",
                "last_updated": "2026-05-10",
            },
            "dragon dragon sword cultivation",
        )
        _write_card_md(
            src,
            "romance",
            {
                "id": "card-romance",
                "asset_type": "prompt_card",
                "title": "Romance beat",
                "topic": ["爱情"],
                "stage": "drafting",
                "quality_grade": "A",
                "card_intent": "prose_generation",
                "source_path": "romance.md",
                "last_updated": "2026-05-11",
            },
            "romance romance tenderness",
        )
        idx = root / "index.sqlite"
        stats = build_index([src], idx)
        self.assertEqual(stats.cards_indexed, 2)
        return idx

    def test_fake_embedder_ranks_by_cosine_similarity(self) -> None:
        from rag.layer2_vector import build_vector_index, search_vector, vector_ready

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_stats = build_vector_index(idx, KeywordEmbedder())

            self.assertEqual(build_stats.vectors_indexed, 2)
            ready = vector_ready(idx)
            self.assertTrue(ready.ready, ready.reason)

            hits = search_vector(idx, "dragon cultivation", KeywordEmbedder(), top_k=2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])
            self.assertGreater(hits[0]["_vector_score"], hits[1]["_vector_score"])

    def test_sqlite_vec_backend_unavailable_fails_open(self) -> None:
        from rag.layer2_vector import SQLiteVecBackend, build_vector_index, search_vector

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            backend = SQLiteVecBackend(sqlite_vec_module=None)

            build_stats = build_vector_index(idx, KeywordEmbedder(), backend=backend)
            hits = search_vector(idx, "dragon cultivation", KeywordEmbedder(), backend=backend)

            self.assertFalse(build_stats.sqlite_vec_available)
            self.assertEqual(build_stats.storage, "sqlite-json")
            self.assertEqual(build_stats.vectors_indexed, 2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])

    def test_sqlite_vec_load_failure_falls_back_to_json_vectors(self) -> None:
        from rag.layer2_vector import SQLiteVecBackend, build_vector_index, search_vector

        class BrokenSQLiteVec:
            @staticmethod
            def load(_conn: Any) -> None:
                raise RuntimeError("extension unavailable")

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            backend = SQLiteVecBackend(sqlite_vec_module=BrokenSQLiteVec())

            build_stats = build_vector_index(idx, KeywordEmbedder(), backend=backend)
            hits = search_vector(idx, "dragon cultivation", KeywordEmbedder(), backend=backend)

            self.assertFalse(build_stats.sqlite_vec_available)
            self.assertEqual(build_stats.storage, "sqlite-json")
            self.assertEqual(build_stats.vectors_indexed, 2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])

    def test_sqlite_vec_backend_searches_native_vec0_when_available(self) -> None:
        try:
            import sqlite_vec
        except Exception as exc:  # noqa: BLE001 - optional integration dependency
            self.skipTest(f"sqlite_vec is not installed: {exc}")
        from rag.layer2_vector import SQLiteVecBackend, build_vector_index, search_vector

        backend = SQLiteVecBackend(sqlite_vec_module=sqlite_vec)
        try:
            conn = backend.connect(":memory:")
            backend.create_schema(conn, 3)
        except Exception as exc:  # noqa: BLE001 - stdlib sqlite may disable load_extension
            self.skipTest(f"sqlite_vec cannot be loaded by this Python SQLite stack: {exc}")
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001 - best-effort cleanup
                pass

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))

            build_stats = build_vector_index(idx, KeywordEmbedder(), backend=backend)
            hits = search_vector(idx, "dragon cultivation", KeywordEmbedder(), top_k=2, backend=backend)

            self.assertTrue(build_stats.sqlite_vec_available)
            self.assertEqual(build_stats.storage, "sqlite-vec")
            self.assertEqual(build_stats.vectors_indexed, 2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])
            self.assertIn("_vector_distance", hits[0])
            self.assertLessEqual(hits[0]["_vector_distance"], hits[1]["_vector_distance"])
            self.assertGreater(hits[0]["_vector_score"], hits[1]["_vector_score"])

    def test_sqlite_vec_backend_handles_single_candidate_filter(self) -> None:
        try:
            import sqlite_vec
        except Exception as exc:  # noqa: BLE001 - optional integration dependency
            self.skipTest(f"sqlite_vec is not installed: {exc}")
        from rag.layer2_vector import SQLiteVecBackend, build_vector_index, search_vector

        backend = SQLiteVecBackend(sqlite_vec_module=sqlite_vec)
        try:
            conn = backend.connect(":memory:")
            backend.create_schema(conn, 3)
        except Exception as exc:  # noqa: BLE001 - optional integration dependency
            self.skipTest(f"sqlite_vec cannot be loaded by this Python SQLite stack: {exc}")
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001 - best-effort cleanup
                pass

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx, KeywordEmbedder(), backend=backend)

            hits = search_vector(
                idx,
                "dragon cultivation",
                KeywordEmbedder(),
                top_k=5,
                candidate_ids=["card-dragon"],
                backend=backend,
            )

            self.assertEqual([h["id"] for h in hits], ["card-dragon"])
            self.assertIn("_vector_distance", hits[0])

    def test_deterministic_text_embedder_is_stable(self) -> None:
        from rag.layer2_vector import DeterministicTextEmbedder

        embedder = DeterministicTextEmbedder(dimension=16)

        first = embedder.embed("Dragon sword, dragon fire.")
        second = embedder.embed("Dragon sword, dragon fire.")
        different = embedder.embed("Romance tenderness.")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertGreater(sum(abs(x) for x in first), 0.0)
        self.assertNotEqual(first, different)

    def test_deterministic_text_embedder_matches_chinese_subphrases(self) -> None:
        from rag.layer2_vector import DeterministicTextEmbedder

        embedder = DeterministicTextEmbedder(dimension=64)

        query = embedder.embed("规则怪谈 副本设计")
        relevant = embedder.embed("生成规则怪谈副本")
        unrelated = embedder.embed("学院课程考核体系")

        def cosine(left: list[float], right: list[float]) -> float:
            return sum(a * b for a, b in zip(left, right))

        self.assertGreater(cosine(query, relevant), cosine(query, unrelated))

    def test_default_embedding_recalls_similar_temp_index_entry(self) -> None:
        from rag.layer2_vector import build_vector_index, search_vector

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_stats = build_vector_index(idx)

            self.assertEqual(build_stats.vectors_indexed, 2)

            hits = search_vector(idx, "dragon sword cultivation", top_k=2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])
            self.assertGreater(hits[0]["_vector_score"], hits[1]["_vector_score"])

    def test_search_vector_uses_chinese_lexical_overlap_bonus(self) -> None:
        from rag.index_builder import build_index
        from rag.layer2_vector import build_vector_index, search_vector

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            _write_card_md(
                src,
                "many-children",
                {
                    "id": "card-many-children",
                    "asset_type": "prompt_card",
                    "title": "设计多子多福系统",
                    "topic": ["玄幻", "系统"],
                    "stage": "setting",
                    "quality_grade": "B",
                    "card_intent": "structural_design",
                    "source_path": "many-children.md",
                    "last_updated": "2026-05-10",
                },
                "生孩子获得奖励机制，家族修仙，系统反馈。",
            )
            _write_card_md(
                src,
                "generic-system",
                {
                    "id": "card-generic-system",
                    "asset_type": "prompt_card",
                    "title": "设计分支技能树",
                    "topic": ["玄幻", "系统"],
                    "stage": "setting",
                    "quality_grade": "A",
                    "card_intent": "structural_design",
                    "source_path": "generic-system.md",
                    "last_updated": "2026-05-11",
                },
                "技能路线、职业分支、升级消耗。",
            )
            idx = root / "index.sqlite"
            build_index([src], idx)
            build_vector_index(idx)

            hits = search_vector(
                idx,
                "多子多福 奖励机制",
                top_k=2,
                candidate_ids=["card-generic-system", "card-many-children"],
            )

            self.assertEqual(hits[0]["id"], "card-many-children")
            self.assertGreater(hits[0]["_lexical_score"], hits[1]["_lexical_score"])

    def test_search_vector_preserves_ordered_candidate_prior(self) -> None:
        from rag.index_builder import build_index
        from rag.layer2_vector import build_vector_index, search_vector

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            _write_card_md(
                src,
                "metadata-best",
                {
                    "id": "card-metadata-best",
                    "asset_type": "prompt_card",
                    "title": "Metadata best",
                    "topic": ["玄幻"],
                    "stage": "setting",
                    "quality_grade": "A",
                    "card_intent": "structural_design",
                    "source_path": "metadata-best.md",
                    "last_updated": "2026-05-10",
                },
                "shared vector body",
            )
            _write_card_md(
                src,
                "metadata-later",
                {
                    "id": "card-metadata-later",
                    "asset_type": "prompt_card",
                    "title": "Metadata later",
                    "topic": ["玄幻"],
                    "stage": "setting",
                    "quality_grade": "A",
                    "card_intent": "structural_design",
                    "source_path": "metadata-later.md",
                    "last_updated": "2026-05-10",
                },
                "shared vector body",
            )
            idx = root / "index.sqlite"
            build_index([src], idx)
            build_vector_index(idx)

            hits = search_vector(
                idx,
                "shared vector body",
                top_k=2,
                candidate_ids=["card-metadata-later", "card-metadata-best"],
            )

            self.assertEqual([hit["id"] for hit in hits], ["card-metadata-later", "card-metadata-best"])
            self.assertGreater(hits[0]["_candidate_prior_score"], hits[1]["_candidate_prior_score"])

    def test_retriever_uses_default_embedding_when_vector_index_ready(self) -> None:
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx)

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon sword cultivation",
                top_k=2,
                index_path=idx,
                config={
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual(result["diagnostics"]["used_layers"], [1, 2])
            self.assertNotIn("vector_embedder_missing", result["diagnostics"]["warnings"])
            self.assertEqual([c["id"] for c in result["cards"]], ["card-dragon", "card-romance"])

    def test_config_default_model_id_matches_default_vector_index(self) -> None:
        from rag.cold_start import load_recall_config
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx)
            config = load_recall_config()

            self.assertEqual(config["embedding"]["default_model_id"], "default")

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon sword cultivation",
                top_k=2,
                index_path=idx,
                config=config,
            )

            self.assertEqual(result["diagnostics"]["used_layers"], [1, 2])
            self.assertEqual([c["id"] for c in result["cards"]], ["card-dragon", "card-romance"])

    def test_retriever_uses_configured_default_embedding_model_id(self) -> None:
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx, model_id="configured-default")

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon sword cultivation",
                top_k=2,
                index_path=idx,
                config={
                    "embedding": {
                        "default_model_id": "configured-default",
                        "default_provider": "deterministic-local",
                        "allow_default_embedder": True,
                    },
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual(result["diagnostics"]["used_layers"], [1, 2])
            self.assertEqual([c["id"] for c in result["cards"]], ["card-dragon", "card-romance"])

    def test_retriever_degrades_when_default_embedder_disabled(self) -> None:
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx)

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon sword cultivation",
                top_k=2,
                index_path=idx,
                config={
                    "embedding": {
                        "default_model_id": "default",
                        "default_provider": "deterministic-local",
                        "allow_default_embedder": False,
                    },
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual(result["diagnostics"]["used_layers"], [1])
            self.assertEqual(result["diagnostics"]["degraded_to"], "layer1")
            self.assertIn("default_embedder_disabled", result["diagnostics"]["warnings"])
            self.assertEqual([c["id"] for c in result["cards"]], ["card-romance", "card-dragon"])

    def test_retriever_without_embedder_degrades_when_index_uses_custom_model(self) -> None:
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx, KeywordEmbedder(), model_id="keyword-test")

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon sword cultivation",
                top_k=2,
                index_path=idx,
                config={
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual(result["diagnostics"]["used_layers"], [1])
            self.assertEqual(result["diagnostics"]["degraded_to"], "layer1")
            self.assertEqual(result["diagnostics"]["vector_reason"], "vectors_missing")

    def test_retriever_falls_back_to_layer1_when_vector_not_ready(self) -> None:
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon cultivation",
                top_k=2,
                index_path=idx,
                embedder=KeywordEmbedder(),
                config={
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual([c["id"] for c in result["cards"]], ["card-romance", "card-dragon"])
            self.assertEqual(result["diagnostics"]["used_layers"], [1])
            self.assertEqual(result["diagnostics"]["degraded_to"], "layer1")
            self.assertIn("vector_not_ready", result["diagnostics"]["warnings"])

    def test_stale_vector_metadata_degrades_to_layer1(self) -> None:
        import sqlite3

        from rag.layer2_vector import build_vector_index, vector_ready
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_vector_index(idx, KeywordEmbedder())
            with closing(sqlite3.connect(str(idx))) as conn:
                conn.execute(
                    "UPDATE card_documents SET body_hash = ? WHERE card_id = ?",
                    ("stale-hash", "card-dragon"),
                )
                conn.commit()

            ready = vector_ready(idx)
            self.assertFalse(ready.ready)
            self.assertIn("stale", ready.reason)

            result = recall_cards(
                stage="drafting",
                topic=None,
                query_text="dragon cultivation",
                top_k=2,
                index_path=idx,
                embedder=KeywordEmbedder(),
                config={
                    "warm_start": {"enabled_layers": [1, 2]},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "enable_rerank_by_stage": {"default": False},
                },
            )
            self.assertEqual(result["diagnostics"]["used_layers"], [1])
            self.assertEqual([c["id"] for c in result["cards"]], ["card-romance", "card-dragon"])

    def test_retriever_uses_wider_candidate_k_for_layer2(self) -> None:
        from rag.index_builder import build_index
        from rag.layer2_vector import build_vector_index
        from rag.retriever import recall_cards

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for i in range(5):
                _write_card_md(
                    src,
                    f"generic-{i}",
                    {
                        "id": f"card-generic-{i}",
                        "asset_type": "prompt_card",
                        "title": f"Generic high quality {i}",
                        "topic": ["玄幻"],
                        "stage": "drafting",
                        "quality_grade": "A",
                        "card_intent": "prose_generation",
                        "source_path": f"generic-{i}.md",
                        "last_updated": f"2026-05-1{i}",
                    },
                    "romance tenderness",
                )
            _write_card_md(
                src,
                "dragon-low-quality",
                {
                    "id": "card-dragon-low-quality",
                    "asset_type": "prompt_card",
                    "title": "Dragon lower quality but semantically exact",
                    "topic": ["玄幻"],
                    "stage": "drafting",
                    "quality_grade": "B",
                    "card_intent": "prose_generation",
                    "source_path": "dragon-low-quality.md",
                    "last_updated": "2026-05-01",
                },
                "dragon dragon sword cultivation",
            )
            idx = root / "index.sqlite"
            build_index([src], idx)
            build_vector_index(idx, KeywordEmbedder())

            result = recall_cards(
                stage="drafting",
                topic=["玄幻"],
                query_text="dragon cultivation",
                top_k=2,
                index_path=idx,
                embedder=KeywordEmbedder(),
                config={
                    "warm_start": {"enabled_layers": [1, 2], "layer3_optional": True},
                    "cold_start": {"enabled_layers": [1]},
                    "stage_specific_top_k": {"drafting": 2, "default": 5},
                    "candidate_pool": {"default": 6},
                    "enable_rerank_by_stage": {"default": False},
                },
            )

            self.assertEqual(result["diagnostics"]["candidate_k"], 6)
            self.assertEqual(result["diagnostics"]["top_k"], 2)
            self.assertEqual(result["diagnostics"]["layer1_candidate_count"], 6)
            self.assertEqual(result["cards"][0]["id"], "card-dragon-low-quality")
            self.assertEqual(len(result["cards"]), 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
