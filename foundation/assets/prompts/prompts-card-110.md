---
id: prompts-card-design_battle_royale-110
asset_type: prompt_card
title: 大逃杀/吃鸡模式逻辑设计
topic: [无限流, 游戏]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/110.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_battle_royale
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 110. 大逃杀/吃鸡模式逻辑设计

## 提示词内容

```json
{
  "task": "design_battle_royale",
  "map": "Abandoned Island / Virtual City",
  "player_count": 100,
  "mechanic": "Safe Zone Shrinking (Poison Gas)",
  "loot_system": "Air Drops / Scavenging buildings",
  "twist": "Teaming is allowed but only one winner / The dead turn into zombies",
  "mc_strategy": "Bush camping vs. Rambo style"
}
```

## 使用场景
无限流/游戏文。设计紧张刺激的生存竞赛。

## 最佳实践要点
1.  **人性博弈**：在极端生存压力下，背叛与合作是核心看点。
2.  **随机性**：空投或轰炸区带来的随机变量，能瞬间改变战局。

## 示例输入
```json
{
  "map": "废弃海岛度假村",
  "player_count": 60,
  "mechanic": "毒雾每 20 分钟缩圈",
  "twist": "夜晚死者会变成追踪生者的感染者"
}
```
