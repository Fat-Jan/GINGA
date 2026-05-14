---
id: prompts-card-differentiate-379
asset_type: prompt_card
title: 润色：群像文人物区分
topic: [通用, 文风]
stage: refinement
quality_grade: A
source_path: _原料/提示词库参考/prompts/379.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: differentiate
task_full: differentiate_characters
granularity: character
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 379. 润色：群像文人物区分 (Character Differentiation)

## 提示词内容

```json
{
  "task": "differentiate_characters",
  "scene": "A team meeting",
  "characters": ["Leader", "Smart Guy", "Strong Guy", "Funny Guy"],
  "dialogue_check": "Can you tell who is speaking without tags?",
  "adjustments": [
    "Leader: Uses imperatives, short sentences",
    "Smart Guy: Uses technical terms, long sentences",
    "Strong Guy: Grunts, simple words",
    "Funny Guy: Uses slang, jokes"
  ]
}
```

## 使用场景
群像/润色。确保每个角色说话都有自己的风格。

## 最佳实践要点
1.  **口癖**：给每个角色设计独特的口头禅或说话习惯。
2.  **关注点**：面对同一件事，不同性格的人关注点完全不同。

## 示例输入
修改一段“四人小队讨论战术”的对话，区分每个人的性格。
