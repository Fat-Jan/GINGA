"""rag.layer2_vector — Sprint 3 Layer 2 vector recall.

The primary storage is sqlite-compatible and deliberately light: vectors are
stored as JSON in ``card_vectors`` so tests and cold deployments do not require
sqlite-vec. If sqlite-vec is later available, this schema still keeps enough
metadata to rebuild a native vector table without changing callers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


_LOG = logging.getLogger("rag.layer2_vector")


_VECTOR_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS card_vectors (
    card_id     TEXT PRIMARY KEY,
    vector_json TEXT NOT NULL,
    body_hash   TEXT NOT NULL,
    model_id    TEXT NOT NULL,
    dimension   INTEGER NOT NULL,
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_card_vectors_model ON card_vectors(model_id);
"""

_SQLITE_VEC_TABLE = "card_vectors_vec0"
_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)
_AUTO_SQLITE_VEC = object()


@dataclass
class VectorBuildStats:
    cards_seen: int = 0
    vectors_indexed: int = 0
    skipped_empty_body: int = 0
    errors: int = 0
    sqlite_vec_available: bool = False
    storage: str = "sqlite-json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "cards_seen": self.cards_seen,
            "vectors_indexed": self.vectors_indexed,
            "skipped_empty_body": self.skipped_empty_body,
            "errors": self.errors,
            "sqlite_vec_available": self.sqlite_vec_available,
            "storage": self.storage,
        }


@dataclass
class VectorReady:
    ready: bool
    reason: str
    cards_count: int = 0
    vectors_count: int = 0


class DeterministicTextEmbedder:
    """Local token-hashing embedder for offline tests and spike runs."""

    def __init__(self, *, dimension: int = 64) -> None:
        self.dimension = max(1, int(dimension))

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall((text or "").lower())
        for token in _expand_tokens(tokens):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0.0:
            return vector
        return [x / norm for x in vector]


class SQLiteVecBackend:
    """Optional sqlite-vec backend; fails open when the extension is absent."""

    storage = "sqlite-vec"
    unavailable_storage = "sqlite-vec-unavailable"

    def __init__(self, sqlite_vec_module: Any = _AUTO_SQLITE_VEC) -> None:
        self._module = _import_sqlite_vec() if sqlite_vec_module is _AUTO_SQLITE_VEC else sqlite_vec_module
        self._sqlite = _select_sqlite_module()

    @property
    def available(self) -> bool:
        return self._module is not None

    def connect(self, index_path: Path | str) -> Any:
        return self._sqlite.connect(str(index_path))

    @property
    def row_factory(self) -> Any:
        return getattr(self._sqlite, "Row", sqlite3.Row)

    def create_schema(self, conn: sqlite3.Connection, dimension: int) -> bool:
        if not self._load(conn):
            return False
        conn.execute(f"DROP TABLE IF EXISTS {_SQLITE_VEC_TABLE}")
        conn.execute(
            f"""
            CREATE VIRTUAL TABLE {_SQLITE_VEC_TABLE}
            USING vec0(embedding float[{int(dimension)}])
            """
        )
        return True

    def insert(self, conn: sqlite3.Connection, rowid: int, vector: Sequence[float]) -> None:
        conn.execute(
            f"INSERT INTO {_SQLITE_VEC_TABLE}(rowid, embedding) VALUES (?, ?)",
            (rowid, json.dumps([float(x) for x in vector], ensure_ascii=False)),
        )

    def search(
        self,
        conn: sqlite3.Connection,
        query_vector: Sequence[float],
        *,
        top_k: int,
        candidate_rowids: Optional[Sequence[int]] = None,
    ) -> list[sqlite3.Row]:
        if not self._load(conn):
            return []
        sql = f"""
            SELECT rowid, distance
            FROM {_SQLITE_VEC_TABLE}
            WHERE embedding MATCH ? AND k = ?
        """
        params: list[Any] = [
            json.dumps([float(x) for x in query_vector], ensure_ascii=False),
            max(0, int(top_k)),
        ]
        if candidate_rowids is not None:
            if not candidate_rowids:
                return []
            placeholders = ",".join("?" for _ in candidate_rowids)
            sql += f" AND rowid IN ({placeholders})"
            params.extend(candidate_rowids)
        sql += " ORDER BY distance"
        try:
            return list(conn.execute(sql, params).fetchall())
        except Exception as exc:  # noqa: BLE001 - pysqlite3 has its own OperationalError class
            _LOG.warning("rag.layer2_vector: sqlite-vec search failed open: %s", exc)
            return []

    def _load(self, conn: sqlite3.Connection) -> bool:
        if self._module is None:
            return False
        load = getattr(self._module, "load", None)
        if not callable(load):
            return False
        try:
            enable_load_extension = getattr(conn, "enable_load_extension", None)
            if callable(enable_load_extension):
                enable_load_extension(True)
            load(conn)
        except Exception as exc:  # noqa: BLE001 - optional dependency fail-open
            _LOG.warning("rag.layer2_vector: sqlite-vec load failed open: %s", exc)
            return False
        finally:
            enable_load_extension = getattr(conn, "enable_load_extension", None)
            if callable(enable_load_extension):
                try:
                    enable_load_extension(False)
                except Exception:  # noqa: BLE001 - best-effort cleanup
                    pass
        return True


def build_vector_index(
    index_path: Path | str,
    embedder: Any = None,
    *,
    model_id: str = "default",
    backend: Optional[SQLiteVecBackend] = None,
) -> VectorBuildStats:
    """Embed indexed card bodies into ``card_vectors``.

    ``embedder`` may be a callable or an object exposing ``embed(text)``. Any
    per-card embed failure is counted and skipped so vector build is fail-open.
    """
    fp = Path(index_path)
    embedder = embedder or DeterministicTextEmbedder()
    stats = VectorBuildStats(sqlite_vec_available=_sqlite_vec_available())
    if backend is not None:
        stats.sqlite_vec_available = backend.available
        stats.storage = backend.storage if backend.available else "sqlite-json"
    if not fp.exists():
        return stats

    with closing(sqlite3.connect(str(fp))) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(_VECTOR_SCHEMA_SQL)
        try:
            rows = conn.execute(
                """
                SELECT c.rowid, c.id, d.body_text, d.body_hash
                FROM cards c
                JOIN card_documents d ON d.card_id = c.id
                ORDER BY c.id
                """
            ).fetchall()
        except sqlite3.OperationalError as exc:
            _LOG.warning("rag.layer2_vector: vector build skipped: %s", exc)
            return stats

        pending: list[tuple[sqlite3.Row, list[float]]] = []
        for row in rows:
            stats.cards_seen += 1
            body = str(row["body_text"] or "")
            if not body.strip():
                stats.skipped_empty_body += 1
                continue
            try:
                vector = _embed(embedder, body)
            except Exception as exc:  # noqa: BLE001 - fail-open per card
                stats.errors += 1
                _LOG.warning("rag.layer2_vector: embed failed for %s: %s", row["id"], exc)
                continue
            if not vector:
                stats.skipped_empty_body += 1
                continue
            pending.append((row, vector))

        use_native_backend = False
        if backend is not None and pending and backend.available:
            try:
                with closing(backend.connect(fp)) as native_conn:
                    native_conn.row_factory = backend.row_factory
                    use_native_backend = backend.create_schema(native_conn, len(pending[0][1]))
                    native_conn.commit()
                stats.sqlite_vec_available = use_native_backend
                stats.storage = backend.storage if use_native_backend else "sqlite-json"
            except Exception as exc:  # noqa: BLE001 - optional dependency fail-open
                _LOG.warning("rag.layer2_vector: sqlite-vec schema failed open: %s", exc)
                stats.sqlite_vec_available = False
                stats.storage = "sqlite-json"
                use_native_backend = False

        for row, vector in pending:
            conn.execute(
                """
                INSERT INTO card_vectors (card_id, vector_json, body_hash, model_id, dimension)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    vector_json=excluded.vector_json,
                    body_hash=excluded.body_hash,
                    model_id=excluded.model_id,
                    dimension=excluded.dimension,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    row["id"],
                    json.dumps(vector, ensure_ascii=False),
                    row["body_hash"],
                    model_id,
                    len(vector),
                ),
            )
            stats.vectors_indexed += 1
        conn.commit()
        if use_native_backend:
            with closing(backend.connect(fp)) as native_conn:
                if not backend._load(native_conn):
                    stats.sqlite_vec_available = False
                    stats.storage = "sqlite-json"
                    return stats
                for row, vector in pending:
                    try:
                        backend.insert(native_conn, int(row["rowid"]), vector)
                    except Exception as exc:  # noqa: BLE001 - optional dependency fail-open
                        _LOG.warning("rag.layer2_vector: sqlite-vec insert failed for %s: %s", row["id"], exc)
                        stats.errors += 1
                native_conn.commit()
    return stats


def vector_ready(index_path: Path | str, *, model_id: Optional[str] = None) -> VectorReady:
    """Return whether every indexed card has a fresh stored vector."""
    fp = Path(index_path)
    if not fp.exists():
        return VectorReady(False, "index_missing")

    try:
        with closing(sqlite3.connect(str(fp))) as conn:
            cards_count = _count(conn, "cards")
            if cards_count <= 0:
                return VectorReady(False, "no_cards", cards_count=cards_count)
            docs_count = _count(conn, "card_documents")
            if docs_count < cards_count:
                return VectorReady(False, "documents_missing", cards_count=cards_count)
            where = "WHERE model_id = ?" if model_id else ""
            params: tuple[Any, ...] = (model_id,) if model_id else ()
            vectors_count = int(
                conn.execute(f"SELECT COUNT(*) FROM card_vectors {where}", params).fetchone()[0] or 0
            )
            if vectors_count < cards_count:
                return VectorReady(False, "vectors_missing", cards_count=cards_count, vectors_count=vectors_count)
            stale = conn.execute(
                """
                SELECT COUNT(*)
                FROM cards c
                JOIN card_documents d ON d.card_id = c.id
                LEFT JOIN card_vectors v ON v.card_id = c.id
                WHERE v.card_id IS NULL
                   OR v.body_hash != d.body_hash
                   OR (? IS NOT NULL AND v.model_id != ?)
                """,
                (model_id, model_id),
            ).fetchone()[0]
            if int(stale or 0) > 0:
                return VectorReady(False, "stale_vectors", cards_count=cards_count, vectors_count=vectors_count)
            return VectorReady(True, "ready", cards_count=cards_count, vectors_count=vectors_count)
    except sqlite3.OperationalError as exc:
        return VectorReady(False, f"schema_missing:{exc}")


def search_vector(
    index_path: Path | str,
    query_text: str,
    embedder: Any = None,
    *,
    top_k: int = 10,
    candidate_ids: Optional[Iterable[str]] = None,
    model_id: Optional[str] = None,
    backend: Optional[SQLiteVecBackend] = None,
) -> list[dict[str, Any]]:
    """Search stored JSON vectors with deterministic in-Python cosine scoring."""
    embedder = embedder or DeterministicTextEmbedder()
    ready = vector_ready(index_path, model_id=model_id)
    if not ready.ready:
        return []
    try:
        query_vector = _embed(embedder, query_text or "")
    except Exception as exc:  # noqa: BLE001 - fail-open
        _LOG.warning("rag.layer2_vector: query embed failed: %s", exc)
        return []
    query_terms = _lexical_terms(query_text or "")
    wanted = {str(x) for x in candidate_ids} if candidate_ids is not None else None
    if wanted is not None and not wanted:
        return []

    fp = Path(index_path)
    if backend is not None and backend.available:
        backend_hits = _search_sqlite_vec_backend(
            fp,
            query_vector,
            backend,
            top_k=top_k,
            candidate_ids=wanted,
            model_id=model_id,
            query_terms=query_terms,
        )
        if backend_hits:
            return backend_hits

    sql = """
        SELECT c.id, c.asset_type, c.stage, c.topic_json, c.quality_grade,
               c.card_intent, c.title, c.source_path, c.last_updated,
               d.body_text, v.vector_json
        FROM card_vectors v
        JOIN cards c ON c.id = v.card_id
        LEFT JOIN card_documents d ON d.card_id = c.id
    """
    params: list[Any] = []
    where: list[str] = []
    if model_id:
        where.append("v.model_id = ?")
        params.append(model_id)
    if wanted is not None:
        placeholders = ",".join("?" for _ in wanted)
        where.append(f"c.id IN ({placeholders})")
        params.extend(sorted(wanted))
    if where:
        sql += " WHERE " + " AND ".join(where)

    out: list[dict[str, Any]] = []
    with closing(sqlite3.connect(str(fp))) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(sql, params).fetchall():
            vector = _decode_vector(row["vector_json"])
            score = _cosine(query_vector, vector)
            item = dict(row)
            item["topic"] = _decode_topic(item.pop("topic_json", "[]"))
            item.pop("vector_json", None)
            item["_vector_score"] = score
            lexical_score = _lexical_score(query_terms, item)
            item["_lexical_score"] = lexical_score
            item["_score"] = score + lexical_score
            out.append(item)
    out.sort(key=lambda item: (-float(item.get("_score", 0.0)), str(item.get("id", ""))))
    return out[: max(0, int(top_k))]


def _sqlite_vec_available() -> bool:
    return _import_sqlite_vec() is not None


def _import_sqlite_vec() -> Any:
    try:
        return __import__("sqlite_vec")
    except Exception:
        return None


def _select_sqlite_module() -> Any:
    try:
        import pysqlite3  # type: ignore[import-not-found]

        conn = pysqlite3.connect(":memory:")
        try:
            if hasattr(conn, "load_extension"):
                return pysqlite3
        finally:
            conn.close()
    except Exception:
        pass
    return sqlite3


def _embed(embedder: Any, text: str) -> list[float]:
    fn = getattr(embedder, "embed", None)
    raw = fn(text) if callable(fn) else embedder(text)
    return [float(x) for x in raw]


def _expand_tokens(tokens: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        if not token:
            continue
        expanded.append(token)
        if _contains_cjk(token):
            chars = list(token)
            for size in (2, 3):
                if len(chars) >= size:
                    expanded.extend("".join(chars[i : i + size]) for i in range(len(chars) - size + 1))
    return expanded


def _contains_cjk(token: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in token)


def _lexical_terms(text: str) -> set[str]:
    return set(_expand_tokens(_TOKEN_RE.findall((text or "").lower())))


def _lexical_score(query_terms: set[str], item: Mapping[str, Any]) -> float:
    if not query_terms:
        return 0.0
    haystack_parts = [
        str(item.get("title", "")),
        " ".join(str(topic) for topic in item.get("topic", []) if str(topic)),
        str(item.get("body_text", "")),
    ]
    doc_terms = _lexical_terms(" ".join(haystack_parts))
    if not doc_terms:
        return 0.0
    overlap = query_terms & doc_terms
    return 0.08 * (len(overlap) / max(1, len(query_terms)))


def _count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] or 0)
    except sqlite3.OperationalError:
        return 0


def _decode_vector(blob: str) -> list[float]:
    try:
        raw = json.loads(blob)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    return [float(x) for x in raw]


def _decode_topic(blob: str) -> list[str]:
    try:
        raw = json.loads(blob or "[]")
    except json.JSONDecodeError:
        return []
    return [str(x) for x in raw] if isinstance(raw, list) else []


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    n = min(len(left), len(right))
    if n == 0:
        return 0.0
    dot = sum(left[i] * right[i] for i in range(n))
    l_norm = math.sqrt(sum(left[i] * left[i] for i in range(n)))
    r_norm = math.sqrt(sum(right[i] * right[i] for i in range(n)))
    if l_norm == 0.0 or r_norm == 0.0:
        return 0.0
    return dot / (l_norm * r_norm)


def _search_sqlite_vec_backend(
    index_path: Path,
    query_vector: Sequence[float],
    backend: SQLiteVecBackend,
    *,
    top_k: int,
    candidate_ids: Optional[set[str]],
    model_id: Optional[str],
    query_terms: set[str],
) -> list[dict[str, Any]]:
    with closing(backend.connect(index_path)) as conn:
        conn.row_factory = backend.row_factory
        candidate_rowids = _candidate_rowids(conn, candidate_ids, model_id=model_id)
        vector_top_k = max(int(top_k), min(len(candidate_rowids or []), int(top_k) * 4)) if candidate_rowids is not None else int(top_k)
        vector_rows = backend.search(
            conn,
            query_vector,
            top_k=vector_top_k,
            candidate_rowids=candidate_rowids,
        )
        if not vector_rows:
            return []
        distances = {int(row["rowid"]): float(row["distance"]) for row in vector_rows}
        placeholders = ",".join("?" for _ in distances)
        rows = conn.execute(
            f"""
            SELECT c.rowid, c.id, c.asset_type, c.stage, c.topic_json, c.quality_grade,
                   c.card_intent, c.title, c.source_path, c.last_updated, d.body_text
            FROM cards c
            LEFT JOIN card_documents d ON d.card_id = c.id
            WHERE c.rowid IN ({placeholders})
            """,
            list(distances),
        ).fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        rowid = int(item.pop("rowid"))
        distance = distances.get(rowid, 0.0)
        item["topic"] = _decode_topic(item.pop("topic_json", "[]"))
        item["_vector_distance"] = distance
        item["_vector_score"] = 1.0 / (1.0 + max(0.0, distance))
        lexical_score = _lexical_score(query_terms, item)
        item["_lexical_score"] = lexical_score
        item["_score"] = item["_vector_score"] + lexical_score
        out.append(item)
    out.sort(key=lambda item: (-float(item.get("_score", 0.0)), str(item.get("id", ""))))
    return out[: max(0, int(top_k))]


def _candidate_rowids(
    conn: sqlite3.Connection,
    candidate_ids: Optional[set[str]],
    *,
    model_id: Optional[str],
) -> Optional[list[int]]:
    where: list[str] = []
    params: list[Any] = []
    if candidate_ids is not None:
        if not candidate_ids:
            return []
        placeholders = ",".join("?" for _ in candidate_ids)
        where.append(f"c.id IN ({placeholders})")
        params.extend(sorted(candidate_ids))
    if model_id:
        where.append("v.model_id = ?")
        params.append(model_id)
    sql = """
        SELECT c.rowid
        FROM cards c
        JOIN card_vectors v ON v.card_id = c.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    return [int(row[0]) for row in conn.execute(sql, params).fetchall()]


__all__ = [
    "DeterministicTextEmbedder",
    "SQLiteVecBackend",
    "VectorBuildStats",
    "VectorReady",
    "build_vector_index",
    "vector_ready",
    "search_vector",
]
