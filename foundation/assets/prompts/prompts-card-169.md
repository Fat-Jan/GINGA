---
id: prompts-card-generate_death_scenarios-169
asset_type: prompt_card
title: 死亡循环中的花样死法
topic: [无限流, 时间循环]
stage: drafting
quality_grade: B
source_path: _原料/提示词库参考/prompts/169.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_death_scenarios
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 169. 死亡循环中的花样死法

## 提示词内容

```json
{
  "task": "generate_death_scenarios",
  "setting": "Haunted Mansion / Space Station",
  "loop_count": 5,
  "deaths": [
    "Accidental: Tripped and broke neck",
    "Trap: Laser grid slice",
    "Betrayal: Stabbed by 'ally'",
    "Environment: Oxygen suffocation",
    "Sacrifice: Holding the door for others"
  ],
  "mc_learning": "Memorizing the floor plan and enemy patrol routes"
}
```

## 使用场景
无限流/时间循环。展示主角试错的过程。

## 最佳实践要点
1.  **死得有价值**：每一次死亡都必须换取关键信息（密码、路线、内鬼身份）。
2.  **黑色幽默**：在惨烈的死亡中穿插一些荒谬的死法，调节节奏。

## 示例输入
- 场景：废弃空间站，循环次数 5 次。
- 死法方向：误触气闸、同伴背刺、维修机器人误判、氧气耗尽。
