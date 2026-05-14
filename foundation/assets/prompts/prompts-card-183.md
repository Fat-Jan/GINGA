---
id: prompts-card-adapt-character_power-183
asset_type: prompt_card
title: 综漫/无限流角色能力适配
topic: [综漫, 无限流]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/183.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: adapt
task_full: adapt_character_power
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 183. 综漫/无限流角色能力适配

## 提示词内容

```json
{
  "task": "adapt_character_power",
  "character": "Pikachu",
  "target_world": "Dark Souls / Cyberpunk 2077",
  "adaptation": {
    "Skill": "Thunderbolt -> Bio-electric Overload Hack",
    "Appearance": "Yellow fur -> Yellow neon tactical vest",
    "Role": "Combat Pet -> Autonomous Drone"
  },
  "balance": "Nerfed speed, buffed damage against machines"
}
```

## 使用场景
综漫/同人文。将知名角色融入不同画风的世界。

## 最佳实践要点
1.  **画风统一**：角色的能力表现形式必须符合目标世界的规则（如宝可梦在赛博世界变成黑客软件）。
2.  **保留神韵**：虽然外形变了，但核心特征（如皮卡丘的黄色、电属性）不能丢。

## 示例输入
- 原角色能力：火焰炼金术
- 新世界规则：所有能力需消耗精神值
- 适配目标：保留招牌感，但加入冷却与代价
