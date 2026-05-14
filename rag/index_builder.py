"""rag.index_builder — 扫 foundation/assets/ 建 sqlite 索引 (R-1).

输入：``foundation/assets/prompts/**/*.md`` (含 frontmatter)，未来扩到 base/
输出：``rag/index.sqlite``，保留 ``cards`` 表，并补充 ``card_documents`` 正文表::

    CREATE TABLE cards (
        id              TEXT PRIMARY KEY,
        asset_type      TEXT,
        stage           TEXT,
        topic_json      TEXT,        -- JSON array; 用 LIKE 查 partial match
        quality_grade   TEXT,
        card_intent     TEXT,
        title           TEXT,
        source_path     TEXT,
        last_updated    TEXT
    );

冷启动行为 (jury-2 P0)：源目录不存在 / 空 / 无合法 frontmatter →
    不报错，建空索引文件 + 日志记录，调用方 (layer1_filter / cold_start) 处理.
"""

from __future__ import annotations

import json
import logging
import re
import hashlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

import yaml


_LOG = logging.getLogger("rag.index_builder")

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<body>.*?)\n---\s*(?:\n|$)",
    re.DOTALL,
)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id              TEXT PRIMARY KEY,
    asset_type      TEXT,
    stage           TEXT,
    topic_json      TEXT,
    quality_grade   TEXT,
    card_intent     TEXT,
    title           TEXT,
    source_path     TEXT,
    last_updated    TEXT
);
CREATE INDEX IF NOT EXISTS idx_stage ON cards(stage);
CREATE INDEX IF NOT EXISTS idx_asset_type ON cards(asset_type);
CREATE INDEX IF NOT EXISTS idx_quality_grade ON cards(quality_grade);
CREATE INDEX IF NOT EXISTS idx_card_intent ON cards(card_intent);

CREATE TABLE IF NOT EXISTS card_documents (
    card_id     TEXT PRIMARY KEY,
    body_text   TEXT,
    body_hash   TEXT,
    source_path TEXT,
    FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_card_documents_hash ON card_documents(body_hash);
"""


class IndexBuildError(RuntimeError):
    """索引构建失败."""


@dataclass
class IndexBuildStats:
    """构建摘要 (供 audit / log 使用)."""

    sources_scanned: int = 0
    files_seen: int = 0
    cards_indexed: int = 0
    skipped_no_frontmatter: int = 0
    skipped_invalid_yaml: int = 0
    skipped_missing_id: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "sources_scanned": self.sources_scanned,
            "files_seen": self.files_seen,
            "cards_indexed": self.cards_indexed,
            "skipped_no_frontmatter": self.skipped_no_frontmatter,
            "skipped_invalid_yaml": self.skipped_invalid_yaml,
            "skipped_missing_id": self.skipped_missing_id,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_index(
    sources: Iterable[Path | str],
    index_path: Path | str,
    *,
    fail_fast: bool = False,
) -> IndexBuildStats:
    """扫 ``sources`` 下的 ``*.md``，把 frontmatter 写到 sqlite.

    冷启动 (ARCHITECTURE §5.2)：``sources`` 全部不存在或为空 → 仍建空索引文件，
    返回 ``stats.cards_indexed == 0``，调用方据此走降级路径.

    ``fail_fast=True`` 时单条 frontmatter 解析失败即抛 ``IndexBuildError``，
    默认 ``False`` 跳过坏卡 (写 log，stats 累加 skipped_*).
    """
    fp = Path(index_path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    # 重建：先删旧文件，避免上次坏数据残留 (sqlite 不主动收回 DELETE 空间).
    if fp.exists():
        fp.unlink()
    stats = IndexBuildStats()

    with closing(sqlite3.connect(str(fp))) as conn:
        conn.executescript(_SCHEMA_SQL)
        for src in sources:
            stats.sources_scanned += 1
            root = Path(src)
            if not root.exists():
                _LOG.info("rag.index_builder: source %s missing (cold-start ok)", root)
                continue
            for md_path in _iter_md_files(root):
                stats.files_seen += 1
                row = _parse_md(md_path, stats, fail_fast=fail_fast)
                if row is None:
                    continue
                _upsert_card(conn, row)
                stats.cards_indexed += 1
        conn.commit()

    _LOG.info("rag.index_builder: %s", stats.to_dict())
    return stats


def open_index(index_path: Path | str) -> sqlite3.Connection:
    """打开 (或自动建) 一个 sqlite 索引连接。

    若文件不存在 → 建空表 (cold-start scaffolding); 调用方负责 close.
    """
    fp = Path(index_path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(fp))
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def count_cards(index_path: Path | str) -> int:
    """返回索引中 cards 的总行数 (用于 detect_state 冷暖判定)."""
    fp = Path(index_path)
    if not fp.exists():
        return 0
    with closing(sqlite3.connect(str(fp))) as conn:
        try:
            cur = conn.execute("SELECT COUNT(*) FROM cards")
            (n,) = cur.fetchone()
        except sqlite3.OperationalError:
            # 没有 cards 表 (旧库)；当作空索引.
            return 0
    return int(n or 0)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _iter_md_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.suffix == ".md":
        yield root
        return
    if root.is_dir():
        # 递归扫 *.md (foundation/assets/prompts/*.md 现阶段平铺，但允许子目录).
        yield from sorted(root.rglob("*.md"))


def _parse_md(
    fp: Path,
    stats: IndexBuildStats,
    *,
    fail_fast: bool,
) -> Optional[dict[str, str]]:
    try:
        text = fp.read_text(encoding="utf-8")
    except OSError as exc:
        if fail_fast:
            raise IndexBuildError(f"read fail {fp}: {exc}") from exc
        _LOG.warning("rag.index_builder: read fail %s: %s", fp, exc)
        return None
    m = _FRONTMATTER_RE.match(text)
    if not m:
        stats.skipped_no_frontmatter += 1
        return None
    body_text = text[m.end() :].strip()
    try:
        meta = yaml.safe_load(m.group("body")) or {}
    except yaml.YAMLError as exc:
        if fail_fast:
            raise IndexBuildError(f"yaml fail {fp}: {exc}") from exc
        stats.skipped_invalid_yaml += 1
        _LOG.warning("rag.index_builder: yaml fail %s: %s", fp, exc)
        return None
    if not isinstance(meta, Mapping):
        stats.skipped_invalid_yaml += 1
        return None

    card_id = str(meta.get("id") or "").strip()
    if not card_id:
        stats.skipped_missing_id += 1
        return None

    topic = meta.get("topic")
    if isinstance(topic, str):
        topic_list = [topic]
    elif isinstance(topic, list):
        topic_list = [str(x) for x in topic]
    else:
        topic_list = []

    return {
        "id": card_id,
        "asset_type": str(meta.get("asset_type") or ""),
        "stage": str(meta.get("stage") or ""),
        "topic_json": json.dumps(topic_list, ensure_ascii=False),
        "quality_grade": str(meta.get("quality_grade") or ""),
        "card_intent": str(meta.get("card_intent") or ""),
        "title": str(meta.get("title") or ""),
        "source_path": str(meta.get("source_path") or str(fp)),
        "last_updated": str(meta.get("last_updated") or ""),
        "body_text": body_text,
        "body_hash": hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
    }


def _upsert_card(conn: sqlite3.Connection, row: Mapping[str, str]) -> None:
    conn.execute(
        """
        INSERT INTO cards (id, asset_type, stage, topic_json,
                           quality_grade, card_intent, title,
                           source_path, last_updated)
        VALUES (:id, :asset_type, :stage, :topic_json,
                :quality_grade, :card_intent, :title,
                :source_path, :last_updated)
        ON CONFLICT(id) DO UPDATE SET
            asset_type=excluded.asset_type,
            stage=excluded.stage,
            topic_json=excluded.topic_json,
            quality_grade=excluded.quality_grade,
            card_intent=excluded.card_intent,
            title=excluded.title,
            source_path=excluded.source_path,
            last_updated=excluded.last_updated
        """,
        dict(row),
    )
    conn.execute(
        """
        INSERT INTO card_documents (card_id, body_text, body_hash, source_path)
        VALUES (:id, :body_text, :body_hash, :source_path)
        ON CONFLICT(card_id) DO UPDATE SET
            body_text=excluded.body_text,
            body_hash=excluded.body_hash,
            source_path=excluded.source_path
        """,
        dict(row),
    )


__all__ = [
    "build_index",
    "open_index",
    "count_cards",
    "IndexBuildError",
    "IndexBuildStats",
]
