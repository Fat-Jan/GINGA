---
id: prompts-card-balance_game_skills-155
asset_type: prompt_card
title: 游戏技能冷却与资源循环设计
topic: [系统]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/155.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: balance
task_full: balance_game_skills
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 155. 游戏技能冷却与资源循环设计

## 提示词内容

```json
{
  "task": "balance_game_skills",
  "class": "Mage / Rogue",
  "resource": "Mana / Energy",
  "skills": [
    {"name": "Big Nuke", "cost": "High", "cd": "Long", "role": "Finisher"},
    {"name": "Small Poke", "cost": "Low", "cd": "Short", "role": "Filler"},
    {"name": "Resource Regen", "cost": "None", "cd": "Medium", "role": "Sustain"}
  ],
  "rotation": "Poke -> Regen -> Nuke"
}
```

## 使用场景
网游/系统文。设计合理的战斗循环（Rotation）。

## 最佳实践要点
1.  **节奏感**：战斗应有张有弛（爆发期vs填充期），避免无限丢技能。
2.  **资源限制**：通过蓝耗或能量条限制主角的爆发频率。

## 示例输入
- 职业：法师。
- 资源：法力值；技能含低耗填充技、高耗爆发技、回蓝技。
