#!/usr/bin/env python3
"""ginga Sprint 2 L Track: prompt_card frontmatter 抽取脚本.

对单张 _原料/提示词库参考/prompts/<file>.md 调 ask-llm，抽出符合
foundation/schema/prompt_card.yaml 的 frontmatter，前置到原内容，落
到 foundation/assets/prompts/<id>.md.

Usage:
    python3 scripts/annotate_prompt_card.py <queue_json> [--endpoint windhub] [--batch-size 20]

行为：
    - 读 queue_json（list of dict, 每条含 src_path / target_id / pre_grade）
    - 顺序处理；每张失败超 3 endpoint failover 标 manual
    - 每张落盘 + jsonl checkpoint 一行
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "foundation" / "assets" / "prompts"
PROGRESS_LOG = REPO_ROOT / ".ops" / "sprint-2" / "annotation-progress.jsonl"
HEARTBEAT = REPO_ROOT / ".ops" / "p7-handoff" / "ST-S2-L-ANNOTATION.md"
SCHEMA_REF = REPO_ROOT / "foundation" / "schema" / "prompt_card.yaml"

ENDPOINTS_FAILOVER = [
    ("windhub", ["-s"]),
    ("ioll-grok", ["-s"]),
    ("xiaomi-tp", []),  # 非流式
]

SYSTEM_PROMPT = """你是 ginga 项目的 prompt_card frontmatter 抽取器。

从下方 JSON-style 提示词卡片原文中，抽出符合下列 YAML schema 的 frontmatter。
只输出 YAML，不要任何说明文字、代码块标记或 markdown 标题。

## frontmatter 字段（必填 + 选填）

```yaml
# 必填 8
id: prompts-card-<intent>-<slug>   # 形如 prompts-card-character-create_protagonist
asset_type: prompt_card
title: <一句话标题>
topic: [<题材标签数组，如 [玄幻, 都市, 校园, 末世, 系统]>]
stage: <enum: ideation/setting/framework/outline/drafting/refinement/analysis/advanced/business/auxiliary/cross_cutting/profile>
quality_grade: <enum: A / A- / B+ / B / C / D>
source_path: <原始路径，从 user 段读取>
last_updated: 2026-05-13

# 卡片专属
card_intent: <一句话 + 一个 verb 代表卡片做什么，如 design_villain>
card_kind: <enum: setup / scene_generator / utility / index / methodology>
task_verb: <动词，如 generate, create, design, write, analyze>
granularity: <enum: scene / character / world / methodology / utility>
output_kind: <enum: json / markdown_table / narrative_prose / structured_card>
dedup_verdict: <enum: retain / merge / drop>
dedup_against: []  # 默认空数组，留 S2 后期再填
```

## 抽取规则
1. id：用 prompts-card-<card_intent 的核心 verb 段>-<slug>，slug 从 source filename 抽（如 39.md → protagonist-bgm-style）
2. quality_grade：如果 user 段提供了 pre_grade，**直接采纳**（不要重新评估）；否则按内容质量打 A/A-/B+/B
3. topic：从卡片内容推断，多个用数组（如 [玄幻, 都市]）
4. stage：按卡片用途（角色卡 → setting；场景描写 → drafting；终稿优化 → refinement；模板/工具 → auxiliary）
5. card_intent：抽 system_instruction 段的核心动词短语
6. 输出严格 YAML，不要 markdown 包装

如果某字段无法推断，**写合理 default 而不是留空**。"""


def call_llm(prompt: str, endpoint: str, extra_flags: list[str], timeout: int = 90) -> tuple[bool, str]:
    """调一次 ask-llm。返回 (success, output)."""
    cmd = ["ask-llm", endpoint, "--max-tokens", "1024"] + extra_flags + ["--system", SYSTEM_PROMPT]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    if proc.returncode != 0:
        return False, f"exit={proc.returncode} stderr={proc.stderr[:200]}"
    if not proc.stdout.strip():
        return False, "empty stdout"
    return True, proc.stdout


def annotate_one(item: dict[str, Any]) -> dict[str, Any]:
    """处理一张卡，返回结果 dict 用于 jsonl checkpoint."""
    src_path = Path(item["src_path"])
    target_id = item.get("target_id") or src_path.stem
    pre_grade = item.get("pre_grade")
    ts = datetime.datetime.now().isoformat(timespec="seconds")

    if not src_path.exists():
        return {"ts": ts, "card": str(src_path), "status": "missing_source"}

    raw = src_path.read_text(encoding="utf-8")
    user_prompt = (
        f"## 原卡片路径\n{src_path}\n\n"
        f"## pre_grade (来自 scout3-quality.json，如果有)\n{pre_grade or '无'}\n\n"
        f"## 原卡片内容\n{raw}"
    )

    fm_yaml = None
    used_endpoint = None
    failures: list[str] = []
    for endpoint, flags in ENDPOINTS_FAILOVER:
        ok, out = call_llm(user_prompt, endpoint, flags)
        if ok:
            fm_yaml = out.strip()
            used_endpoint = endpoint
            break
        failures.append(f"{endpoint}: {out[:120]}")

    if fm_yaml is None:
        return {"ts": ts, "card": str(src_path), "status": "manual", "failures": failures}

    # 剥 ``` 代码块包装（防 LLM 不听话）
    fm_yaml = re.sub(r"^```ya?ml\s*\n", "", fm_yaml, flags=re.MULTILINE)
    fm_yaml = re.sub(r"\n```\s*$", "", fm_yaml)
    fm_yaml = fm_yaml.strip()

    # 写到 foundation/assets/prompts/<id>.md，frontmatter 加 --- 围栏
    output_path = PROMPTS_DIR / f"{target_id}.md"
    output_path.write_text(
        f"---\n{fm_yaml}\n---\n\n{raw}",
        encoding="utf-8",
    )

    return {
        "ts": ts,
        "card": str(src_path),
        "target": str(output_path),
        "endpoint": used_endpoint,
        "status": "ok",
        "frontmatter_bytes": len(fm_yaml),
    }


def append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_heartbeat(msg: str) -> None:
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with HEARTBEAT.open("a", encoding="utf-8") as f:
        f.write(f"\n## {ts} | {msg}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue_json", help="JSON file with list of {src_path, target_id, pre_grade}")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    queue = json.loads(Path(args.queue_json).read_text(encoding="utf-8"))
    end = min(args.offset + args.batch_size, len(queue))
    batch = queue[args.offset : end]

    append_heartbeat(
        f"BATCH START | offset={args.offset} size={len(batch)} (total queue {len(queue)})"
    )

    ok, manual, missing = 0, 0, 0
    for i, item in enumerate(batch, start=args.offset):
        print(f"[{i+1}/{end}] {item['src_path']}", file=sys.stderr)
        result = annotate_one(item)
        append_jsonl(PROGRESS_LOG, result)
        if result["status"] == "ok":
            ok += 1
        elif result["status"] == "manual":
            manual += 1
        else:
            missing += 1

    append_heartbeat(
        f"BATCH DONE | offset={args.offset} ok={ok} manual={manual} missing={missing} next_offset={end}"
    )
    print(f"batch done: ok={ok} manual={manual} missing={missing} next_offset={end}", file=sys.stderr)
    return 0 if manual + missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
