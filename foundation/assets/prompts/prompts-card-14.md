---
id: prompts-card-polish_dialogue-14
asset_type: prompt_card
title: 对话优化 (潜台词注入)
topic: [通用]
stage: refinement
quality_grade: B+
source_path: _原料/提示词库参考/prompts/14.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: polish
task_full: polish_dialogue
granularity: scene
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 14. 对话优化 (潜台词注入)

## 提示词内容

```json
{
  "task": "polish_dialogue",
  "context": "{{context}}",
  "raw_dialogue": "{{dialogue}}",
  "characters": [
    {"name": "A", "mood": "Arrogant"},
    {"name": "B", "mood": "Calm/Mocking"}
  ],
  "goals": [
    "Remove filler words",
    "Add subtext (Power dynamics)",
    "Show character voice (Slang, tone)",
    "Advance plot via dialogue"
  ]
}
```

## 使用场景
润色阶段。优化平淡、无信息的对话。

## 最佳实践要点
1.  **潜台词 (Subtext)**：强调对话背后的权力动态和隐喻，避免直白的大白话。
2.  **性格化**：为不同角色设定 `mood` 和 `voice`，避免千人一面。

## 示例输入
将 `{{context}}` 替换为“反派上门退婚”，`{{dialogue}}` 替换为原始草稿。
