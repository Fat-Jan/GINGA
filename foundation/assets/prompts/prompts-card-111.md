---
id: prompts-card-rewrite_show_dont_tell-111
asset_type: prompt_card
title: "\"Show, Don't Tell\" 改写练习"
topic: [通用]
stage: refinement
quality_grade: B+
source_path: _原料/提示词库参考/prompts/111.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: rewrite
task_full: rewrite_show_dont_tell
granularity: scene
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 111. "Show, Don't Tell" 改写练习

## 提示词内容

```json
{
  "task": "rewrite_show_dont_tell",
  "telling_sentence": "{{sentence}} (e.g., 'He was angry.')",
  "instruction": "Rewrite this using sensory details, body language, and action to convey the emotion without naming it.",
  "example_output": "His knuckles turned white as he gripped the table, veins throbbing in his neck. The glass in his hand shattered."
}
```

## 使用场景
写作润色。将干瘪的叙述转化为生动的描写。

## 最佳实践要点
1.  **动作化**：用具体的肢体动作（握拳、咬牙）替代形容词。
2.  **侧面烘托**：通过环境或物品的变化（杯子碎裂）体现情绪强度。

## 示例输入
将 `{{sentence}}` 替换为“她感到非常害怕”。
