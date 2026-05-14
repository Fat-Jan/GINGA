---
id: prompts-card-manage_guild_resources-119
asset_type: prompt_card
title: 宗门/公会资源管理系统
topic: [玄幻, 都市, 系统, 经济]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/119.md
last_updated: 2026-05-13
card_intent: management_tracking
card_kind: scene_card
task_verb: manage
task_full: manage_guild_resources
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 119. 宗门/公会资源管理系统

## 提示词内容

```json
{
  "task": "manage_guild_resources",
  "organization": "Sect / Guild",
  "resources": {
    "Manpower": "Disciples/Members",
    "Wealth": "Gold/Spirit Stones",
    "Reputation": "Fame"
  },
  "crisis": "Nearby mine depleted / Rival guild poaching members",
  "solution": "Launch an expedition / Host a tournament / Alliance",
  "outcome": "Resource redistribution and growth"
}
```

## 使用场景
经营/掌门流。模拟组织的运营和扩张。

## 最佳实践要点
1.  **资源制衡**：资源总是有限的，迫使主角做出取舍（如牺牲财富换名声）。
2.  **外部压力**：通过危机（资源枯竭、竞争对手）推动组织升级。

## 示例输入
```json
{
  "organization": "新建修仙宗门",
  "resources": {"Manpower": "外门弟子 80 人", "Wealth": "灵石不足", "Reputation": "击退妖潮后上升"},
  "crisis": "灵矿枯竭且邻宗挖人"
}
```
