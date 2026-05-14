---
id: prompts-card-generate_rules_dungeon-8
asset_type: prompt_card
title: 生成规则怪谈/副本
topic: [悬疑]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/8.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: generate_rules_dungeon
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 8. 规则怪谈/副本生成

## 提示词内容

```json
{
  "task": "generate_rules_dungeon",
  "theme": "{{theme}}",
  "difficulty": "{{difficulty}}",
  "output_structure": {
    "title": "Dungeon Name",
    "intro": "Atmospheric description",
    "rules": [
      {"id": 1, "text": "Rule content", "truth_value": "True/False/Conditional"},
      {"id": 2, "text": "Rule content", "truth_value": "True/False/Conditional"}
    ],
    "hidden_danger": "The entity stalking the player",
    "safe_zone": "Where the player can rest",
    "victory_condition": "How to escape/win"
  }
}
```

## 使用场景
悬疑/无限流创作中。快速生成逻辑严密的副本规则。

## 最佳实践要点
1.  **逻辑推理 (Reasoning)**：要求明确规则的 `truth_value`（真/假/条件真），帮助 AI 构建复杂的逻辑谜题。
2.  **氛围营造**：通过 `intro` 和 `hidden_danger` 强化恐怖氛围。

## 示例输入
将 `{{theme}}` 替换为“午夜游乐园”，`{{difficulty}}` 替换为“必死级”。
