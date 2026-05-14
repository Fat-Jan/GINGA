"""Thin raw-idea CLI helpers.

`ginga idea add` deliberately only writes a markdown note under
foundation/raw_ideas. It does not parse, promote, index, or touch runtime state.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


RAW_IDEAS_DIR = Path("foundation") / "raw_ideas"


def _current_time() -> datetime:
    return datetime.now()


def slugify_title(title: str, now: datetime) -> str:
    """Return an ASCII slug, falling back for Chinese/non-ASCII titles."""

    words = re.findall(r"[A-Za-z0-9]+", title.lower())
    if words:
        return "-".join(words)
    return f"idea-{now:%H%M%S}"


def _available_path(raw_dir: Path, date_prefix: str, slug: str) -> Path:
    candidate = raw_dir / f"{date_prefix}-{slug}.md"
    suffix = 2
    while candidate.exists():
        candidate = raw_dir / f"{date_prefix}-{slug}-{suffix}.md"
        suffix += 1
    return candidate


def _idea_content(title: str, body: str, now: datetime) -> str:
    return (
        f"# {title}\n\n"
        f"时间：{now:%Y-%m-%d %H:%M:%S}\n"
        "来源：ginga idea add\n\n"
        f"{body.rstrip()}\n"
    )


def add_idea(
    title: str,
    *,
    body: str | None = None,
    stdin_text: str | None = None,
    root: Path | str | None = None,
    now: datetime | None = None,
) -> Path:
    """Write a raw idea and return its repo-relative path."""

    repo_root = Path(root) if root is not None else Path.cwd()
    timestamp = now or _current_time()
    raw_dir = repo_root / RAW_IDEAS_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    parts = []
    if body:
        parts.append(body)
    if stdin_text:
        parts.append(stdin_text)
    text = "\n".join(part.rstrip() for part in parts)

    slug = slugify_title(title, timestamp)
    path = _available_path(raw_dir, timestamp.strftime("%Y-%m-%d"), slug)
    path.write_text(_idea_content(title, text, timestamp), encoding="utf-8")
    return path.relative_to(repo_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ginga idea", description="Raw idea capture helpers")
    sub = parser.add_subparsers(dest="idea_cmd", required=True)

    p_add = sub.add_parser("add", help="写入一条 raw idea，不解析、不进入 state/RAG")
    p_add.add_argument("title", help="灵感标题")
    p_add.add_argument("--body", help="正文")
    p_add.add_argument("--stdin", action="store_true", help="从标准输入读取正文")
    return parser

