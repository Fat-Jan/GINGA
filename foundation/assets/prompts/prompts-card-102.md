---
id: prompts-card-simulate_fantasy_economy-102
asset_type: prompt_card
title: 异世界经济与通货膨胀模拟
topic: [玄幻]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/102.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: scene_card
task_verb: simulate
task_full: simulate_fantasy_economy
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 102. 异世界经济与通货膨胀模拟

## 提示词内容

```json
{
  "task": "simulate_fantasy_economy",
  "currency_system": {
    "Base": "Copper Coin",
    "Standard": "Silver Coin (100 Copper)",
    "Premium": "Gold Coin (100 Silver)",
    "Ultra": "Spirit Stone (1000 Gold)"
  },
  "market_shock": "Dungeon discovery floods market with gold / War cuts off trade",
  "impact_on_mc": "Potion prices skyrocket / MC's loot devalues",
  "mc_opportunity": "Hoarding specific items / Currency exchange arbitrage"
}
```

## 使用场景
长篇玄幻/网游文。维持经济系统的稳定和剧情张力。

## 最佳实践要点
1.  **购买力锚点**：明确一个面包多少钱，防止后期数值崩坏。
2.  **危机即机遇**：利用经济波动（通货膨胀/紧缩）制造主角暴富的契机。

## 示例输入
- 货币：铜币、银币、金币、低阶灵石四级兑换。
- 冲击：新副本涌出大量金币，普通药剂价格三天翻倍。
- 主角机会：提前囤积治疗草，并用灵石兑换被低估的工匠契约。
