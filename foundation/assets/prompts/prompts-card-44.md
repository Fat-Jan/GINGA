---
id: prompts-card-optimize_dialogue-44
asset_type: prompt_card
title: 对话优化 (避免水词)
topic: [通用]
stage: refinement
quality_grade: B
source_path: 原料/提示词库参考/prompts/44.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: optimize
task_full: optimize_dialogue
granularity: scene
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 44. 对话优化 (避免水词)

## 提示词内容

```json
{
  "task": "optimize_dialogue",
  "context": "{{context}}",
  "characters": ["A (性格)", "B (性格)"],
  "draft_dialogue": "{{draft}}",
  "goals": [
    "去除无效寒暄",
    "增加潜台词",
    "体现地位差/冲突"
  ]
}
```

## 使用场景
对话修整。去除废话，增加信息密度和冲突。

## 最佳实践要点
1.  **去水词**：明确要求“去除无效寒暄”，适应快节奏阅读。
2.  **体现冲突**：通过对话体现“地位差”或“冲突”，推动剧情。

## 示例输入
填入上下文和原始对话。
