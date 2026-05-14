---
id: prompts-card-design-multiverse_travel
asset_type: prompt_card
title: 诸天万界穿越机制设定
topic: [玄幻, 都市, 科幻]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/71.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_multiverse_travel
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 71. 诸天万界穿越机制设定

## 提示词内容

```json
{
  "task": "design_multiverse_travel",
  "method": "System / Door / Reincarnation",
  "constraints": [
    "Cooldown time",
    "Item restrictions (Can't bring tech to magic world)",
    "Mission requirement to return"
  ],
  "world_types": ["Wuxia", "Marvel", "Harry Potter", "Cthulhu"],
  "time_flow": "1 day in main world = 1 year in sub-world"
}
```

## 使用场景
诸天流/综漫。设定穿越的规则和限制。

## 最佳实践要点
1.  **时间流速**：明确主世界与副本的时间比例，处理好年龄和时间线问题。
2.  **能力体系兼容**：设定不同世界力量体系的转化规则（如内力转查克拉）。

## 示例输入
- 穿越方式：主角通过青铜门进入不同世界完成任务。
- 限制：每次只能带一件物品返回，科技物品进玄幻世界会失效。
- 时间流速：主世界一天等于副本世界三个月。
