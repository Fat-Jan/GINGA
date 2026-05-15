"""Explicit opt-in RAG path for promoted reference sidecar assets.

This module is intentionally separate from the default RAG retriever.  It only
indexes manually promoted Foundation methodology assets and never scans
``.ops/book_analysis`` directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .index_builder import IndexBuildStats, build_index
from .layer1_filter import recall as layer1_recall


PROMOTED_METHODOLOGY_DIR = Path("foundation/assets/methodology")
PROMOTED_METHODOLOGY_GLOB = "promoted-*.md"
DEFAULT_INDEX_PATH = Path(".ops/validation/reference_sidecar_rag.sqlite")


def build_reference_sidecar_index(
    *,
    repo_root: str | Path = ".",
    index_path: str | Path = DEFAULT_INDEX_PATH,
) -> IndexBuildStats:
    """Build an isolated index from approved promoted methodology assets."""

    root = Path(repo_root)
    promoted_paths = list(iter_promoted_methodology_assets(root))
    return build_index(
        promoted_paths,
        Path(index_path),
        repo_root=root,
        forbidden_paths=[".ops/book_analysis/**"],
        filter_source_path=False,
    )


def recall_reference_sidecar(
    *,
    stage: str | None = "ideation",
    topic: Any = "reference_trope",
    asset_type: str = "methodology",
    top_k: int | None = 5,
    quality_floor: str = "B",
    index_path: str | Path = DEFAULT_INDEX_PATH,
) -> dict[str, Any]:
    """Recall from the isolated reference sidecar index.

    Calling this function is the explicit opt-in boundary.  The default
    ``rag.retriever.recall_cards`` path is not changed by this module.
    """

    cards = layer1_recall(
        stage=stage,
        topic=topic,
        asset_type=asset_type,
        top_k=top_k,
        quality_floor=quality_floor,
        index_path=index_path,
    )
    return {
        "cards": cards,
        "diagnostics": {
            "execution_mode": "reference_sidecar_rag",
            "explicit_opt_in_required": True,
            "index_path": str(index_path),
            "source_glob": (PROMOTED_METHODOLOGY_DIR / PROMOTED_METHODOLOGY_GLOB).as_posix(),
            "default_rag_eligible": False,
        },
    }


def iter_promoted_methodology_assets(repo_root: str | Path = ".") -> Iterable[Path]:
    """Yield only approved promoted methodology markdown assets."""

    root = Path(repo_root)
    assets_root = root / PROMOTED_METHODOLOGY_DIR
    if not assets_root.exists():
        return []
    return [
        path
        for path in sorted(assets_root.glob(PROMOTED_METHODOLOGY_GLOB))
        if _is_sidecar_eligible(path)
    ]


def _is_sidecar_eligible(path: Path) -> bool:
    meta = _read_frontmatter(path)
    return (
        meta.get("asset_type") == "methodology"
        and meta.get("human_review_status") == "approved"
        and meta.get("source_contamination_check") == "pass"
        and meta.get("default_rag_eligible") is False
        and str(meta.get("promoted_from", "")).startswith("trope-")
    )


def _read_frontmatter(path: Path) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    try:
        parsed = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


__all__ = [
    "DEFAULT_INDEX_PATH",
    "PROMOTED_METHODOLOGY_DIR",
    "PROMOTED_METHODOLOGY_GLOB",
    "build_reference_sidecar_index",
    "iter_promoted_methodology_assets",
    "recall_reference_sidecar",
]
