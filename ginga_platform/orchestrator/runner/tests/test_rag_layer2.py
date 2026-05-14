"""Unit tests for Sprint 3 RAG Layer 2 vector recall."""

from __future__ import annotations

import tempfile
import unittest
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

    def test_default_embedding_recalls_similar_temp_index_entry(self) -> None:
        from rag.layer2_vector import build_vector_index, search_vector

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_index(Path(d))
            build_stats = build_vector_index(idx)

            self.assertEqual(build_stats.vectors_indexed, 2)

            hits = search_vector(idx, "dragon sword cultivation", top_k=2)
            self.assertEqual([h["id"] for h in hits], ["card-dragon", "card-romance"])
            self.assertGreater(hits[0]["_vector_score"], hits[1]["_vector_score"])

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
            with sqlite3.connect(str(idx)) as conn:
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
