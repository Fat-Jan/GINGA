---
id: prompts-card-design_villain-10
asset_type: prompt_card
title: 反派仇恨值拉升
topic: [通用]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/10.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_villain
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 10. 反派仇恨值拉升

## 提示词内容

```json
{
  "task": "design_villain",
  "protagonist_profile": "{{mc_profile}}",
  "relationship": "{{relationship}}",
  "output_structure": {
    "name": "Villain Name",
    "status": "Social standing/Power level",
    "motivation": "Why they oppose the MC (Greed, Jealousy, Ideology)",
    "tactic": "How they attack (Direct, Scheme, Betrayal)",
    "hate_factor": "Specific action that triggers reader anger (e.g., kicking a dog)",
    "downfall": "Projected satisfying end"
  }
}
```

## 使用场景
设计反派时使用。确保反派能有效调动读者情绪（仇恨值）。

## 最佳实践要点
1.  **情绪工程**：专注于 `hate_factor`，设计具体的“拉仇恨”行为。
2.  **爽点铺垫**：预设 `downfall`，确保打脸时的爽感释放。

## 示例输入
将 `{{mc_profile}}` 替换为主角简述，`{{relationship}}` 替换为“势利眼前女友”。
