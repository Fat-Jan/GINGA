---
id: prompts-card-generate_exchange_list-22
asset_type: prompt_card
title: 主神空间强化兑换列表
topic: [系统流, 无限流, 奖励]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/22.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_exchange_list
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 22. 主神空间强化兑换列表

## 提示词内容

```json
{
  "task": "generate_exchange_list",
  "points_budget": "1000 - 5000 points",
  "categories": [
    "Bloodline (e.g., Vampire, Saiyan)",
    "Skill (e.g., Gun Kata, Fireball)",
    "Item (e.g., Infinite Ammo Desert Eagle)"
  ],
  "recommendation": "Best combo for the MC's current build"
}
```

## 使用场景
无限流/系统流。设计主角的升级奖励和购物清单。

## 最佳实践要点
1.  **组合策略**：不仅仅列出物品，还要求推荐 `Best combo`，体现策略性。
2.  **数值平衡**：设定点数预算，模拟资源管理游戏。

## 示例输入
- 点数：3000 奖励点。
- 类别：血统、技能、武器各 3 项，适合刚过第一场恐怖片的新手。
