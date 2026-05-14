#!/usr/bin/env python3
"""Report sampled dedup evidence for migrated prompt cards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


MIN_STRICT_SAMPLE = 24
MAX_SAMPLES = 36
TOP_CANDIDATES = 5
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}")
STOPWORDS = {
    "a",
    "an",
    "and",
    "card",
    "for",
    "md",
    "prompt",
    "prompts",
    "the",
    "to",
    "with",
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text):
        if "_" in raw:
            tokens.extend(part.lower() for part in raw.split("_") if len(part) > 1)
        tokens.append(raw.lower())
    return tokens


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + 5 :]
    if yaml is not None:
        try:
            data = yaml.safe_load(block) or {}
            return data if isinstance(data, dict) else {}, body
        except yaml.YAMLError:
            pass
    data = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        if value == "[]":
            data[key.strip()] = []
        elif value:
            data[key.strip()] = value
    return data, body


def prompt_number(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 999999


def read_cards(prompts_dir: Path) -> list[dict]:
    cards = []
    for path in sorted(prompts_dir.glob("*.md"), key=prompt_number):
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        title = str(meta.get("title") or "").strip()
        if not title:
            heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = heading.group(1).strip() if heading else path.stem
        cards.append(
            {
                "path": path,
                "file": path.name,
                "title": title,
                "task": str(meta.get("card_intent") or meta.get("id") or ""),
                "verdict": str(meta.get("dedup_verdict") or "unknown").strip() or "unknown",
                "declared_against": meta.get("dedup_against") if isinstance(meta.get("dedup_against"), list) else [],
                "text": text,
            }
        )
    return cards


def read_base(base_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(base_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(base_dir).as_posix()
        docs.append({"path": path, "file": rel, "title": path.stem, "text": text, "tokens": Counter(tokenize(path.stem + "\n" + text))})
    return docs


def keywords(card: dict) -> list[str]:
    source = " ".join([card["title"], card["task"], card["file"]])
    seen = []
    for token in tokenize(source):
        if token not in seen and len(token) > 1 and not token.isdigit() and token not in STOPWORDS:
            seen.append(token)
    return seen[:10]


def score_candidates(words: list[str], base_docs: list[dict]) -> list[dict]:
    scored = []
    for doc in base_docs:
        hits = [word for word in words if doc["tokens"].get(word, 0)]
        if not hits:
            continue
        title_hits = sum(1 for word in hits if word in tokenize(doc["title"]))
        score = len(set(hits)) * 3 + sum(min(doc["tokens"][word], 5) for word in set(hits)) + title_hits * 5
        scored.append({"file": doc["file"], "score": score, "matched_keywords": sorted(set(hits))})
    scored.sort(key=lambda item: (-item["score"], item["file"]))
    return scored[:TOP_CANDIDATES]


def choose_sample(cards: list[dict]) -> list[dict]:
    by_verdict: dict[str, list[dict]] = {}
    for card in cards:
        by_verdict.setdefault(card["verdict"], []).append(card)
    sample = []
    for verdict in sorted(by_verdict):
        bucket = by_verdict[verdict]
        step = max(1, len(bucket) // 8)
        sample.extend(bucket[::step][:8])
    if len(sample) < MIN_STRICT_SAMPLE:
        step = max(1, len(cards) // MIN_STRICT_SAMPLE)
        sample.extend(cards[::step])
    deduped = {card["file"]: card for card in sample}
    return sorted(deduped.values(), key=lambda card: prompt_number(card["path"]))[:MAX_SAMPLES]


def classify_counts(cards: list[dict]) -> dict:
    counts = Counter(card["verdict"] for card in cards)
    return {
        "retain": sum(count for verdict, count in counts.items() if "retain" in verdict),
        "merge": sum(count for verdict, count in counts.items() if "merge" in verdict),
        "drop": sum(count for verdict, count in counts.items() if "drop" in verdict or "basetypeize" in verdict),
        "unknown": counts.get("unknown", 0),
        "raw": dict(sorted(counts.items())),
    }


def build_report(prompts_dir: Path, base_dir: Path) -> tuple[dict, str]:
    cards = read_cards(prompts_dir)
    base_docs = read_base(base_dir)
    sample = choose_sample(cards)
    evidence = []
    for card in sample:
        words = keywords(card)
        candidates = score_candidates(words, base_docs)
        evidence.append(
            {
                "file": card["file"],
                "title": card["title"],
                "dedup_verdict": card["verdict"],
                "declared_dedup_against": card["declared_against"],
                "sample_keywords": words,
                "possible_dedup_against": candidates,
                "evidence_note": "retain decision has independent lexical/title sample" if card["verdict"] == "retain" else "sampled for non-retain comparison",
            }
        )

    data = {
        "status": "ok",
        "inputs": {"prompts_dir": prompts_dir.as_posix(), "base_dir": base_dir.as_posix()},
        "prompt_card_count": len(cards),
        "base_doc_count": len(base_docs),
        "sample_count": len(evidence),
        "decision_counts": classify_counts(cards),
        "sample_method": "deterministic per-verdict spread; title/card_intent/file keywords scored against base filenames and content token counts",
        "samples": evidence,
        "limitations": [
            "Lexical overlap is evidence for review, not semantic duplicate proof.",
            "Chinese tokenization uses simple contiguous Han-character chunks and does not perform word segmentation.",
            "Retain labels are validated by sampled candidate absence/weakness only; source prompt cards are not modified.",
        ],
    }
    md_lines = [
        "# Dedup Evidence Report",
        "",
        f"- Prompt cards scanned: {len(cards)}",
        f"- Base documents scanned: {len(base_docs)}",
        f"- Sampled cards: {len(evidence)}",
        f"- Retain / merge / drop / unknown: {data['decision_counts']['retain']} / {data['decision_counts']['merge']} / {data['decision_counts']['drop']} / {data['decision_counts']['unknown']}",
        "",
        "## Method",
        "",
        data["sample_method"],
        "",
        "## Sample Evidence",
        "",
    ]
    for item in evidence:
        cands = item["possible_dedup_against"]
        top = ", ".join(f"{c['file']} ({'/'.join(c['matched_keywords'])})" for c in cands[:3]) or "none"
        md_lines.extend(
            [
                f"### {item['file']} - {item['title']}",
                "",
                f"- verdict: {item['dedup_verdict']}",
                f"- sampled keywords: {', '.join(item['sample_keywords'])}",
                f"- possible dedup_against candidates: {top}",
                "",
            ]
        )
    md_lines.extend(["## Limitations", ""])
    md_lines.extend(f"- {line}" for line in data["limitations"])
    return data, "\n".join(md_lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompts_dir", nargs="?", default="foundation/assets/prompts")
    parser.add_argument("base_dir", nargs="?", default="_原料/基座")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    prompts_dir = Path(args.prompts_dir)
    base_dir = Path(args.base_dir)
    missing = [path.as_posix() for path in (prompts_dir, base_dir) if not path.exists()]
    if missing:
        print(f"missing input paths: {', '.join(missing)}", file=sys.stderr)
        return 2 if args.strict else 0

    data, markdown = build_report(prompts_dir, base_dir)
    Path(".ops/validation").mkdir(parents=True, exist_ok=True)
    Path(".ops/reports").mkdir(parents=True, exist_ok=True)
    Path(".ops/validation/dedup_evidence.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(".ops/reports/dedup_evidence.md").write_text(markdown, encoding="utf-8")
    print(f"wrote dedup evidence: samples={data['sample_count']} cards={data['prompt_card_count']} base_docs={data['base_doc_count']}")
    if args.strict and data["sample_count"] < MIN_STRICT_SAMPLE:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
