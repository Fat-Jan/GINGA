---
id: prompts-card-polish_text_style-363
asset_type: prompt_card
title: 流程：风格化润色 (Style Polishing)
topic: [通用, 文风]
stage: refinement
quality_grade: B
source_path: _原料/提示词库参考/prompts/363.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: polish
task_full: polish_text_style
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 363. 流程：风格化润色 (Style Polishing)

## 提示词内容

```json
{
  "task": "polish_text_style",
  "target_style": "Dark Fantasy / Humorous / Ancient Chinese",
  "original_text": "He killed the monster.",
  "polished_text": {
    "Dark Fantasy": "His blade sang a dirge as it severed the beast's foul head.",
    "Humorous": "He poked the monster with his stick until it stopped moving. Ideally.",
    "Ancient Chinese": "剑光一闪，那妖兽便身首异处，血溅五步。"
  }
}
```

## 使用场景
润色/文笔。统一全书画风，提升文笔逼格。

## 最佳实践要点
1.  **词汇选择**：不同风格需要不同的词汇库（如古风多用四字成语）。
2.  **句式**：长短句的搭配影响阅读节奏。

## 示例输入
将这段“主角吃饭”的描写润色成“古龙风”。
