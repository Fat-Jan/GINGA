---
id: prompts-card-design_faction_war_dungeon-221
asset_type: prompt_card
title: 无限流：阵营对抗副本设计
topic: [无限流, 网游]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/221.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_faction_war_dungeon
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 221. 无限流：阵营对抗副本设计

## 提示词内容

```json
{
  "task": "design_faction_war_dungeon",
  "setting": "WWII Stalingrad / Three Kingdoms / Future Mars Colony",
  "factions": [
    {"name": "Red Team", "objective": "Defend the core", "bonus": "High defense"},
    {"name": "Blue Team", "objective": "Destroy the core", "bonus": "High mobility"}
  ],
  "twist": "A third neutral faction (Yellow Team) wins by killing everyone",
  "mc_strategy": "Infiltrate enemy base disguised as a minion"
}
```

## 使用场景
无限流/网游文。设计紧张刺激的团队PVP副本。

## 最佳实践要点
1.  **非对称对抗**：攻守双方的目标和资源应有所区别（如守方有地利，攻方有人数）。
2.  **搅局者**：引入第三方势力（如中立怪或第三方阵营）打破平衡。

## 示例输入
```json
{
  "setting": "废弃月面基地",
  "factions": ["守卫核心的工程组", "夺取氧气塔的突击组"],
  "twist": "基地 AI 暗中诱导双方互相消耗"
}
```
