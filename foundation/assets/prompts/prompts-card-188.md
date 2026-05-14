---
id: prompts-card-create_power_scale-188
asset_type: prompt_card
title: 战斗力单位换算表
topic: [玄幻, 系统]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/188.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: scene_card
task_verb: create
task_full: create_power_scale
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 188. 战斗力单位换算表

## 提示词内容

```json
{
  "task": "create_power_scale",
  "base_unit": "1 Combat Power = An adult male with a stick",
  "tiers": [
    {"level": "E", "value": "10 CP", "feat": "Break a brick wall"},
    {"level": "A", "value": "10,000 CP", "feat": "Destroy a tank"},
    {"level": "S", "value": "1,000,000 CP", "feat": "Level a city"}
  ],
  "mc_current": "500 CP (Hidden: 999,999 CP)"
}
```

## 使用场景
系统/玄幻文。直观展示战力差距。

## 最佳实践要点
1.  **具象化**：不要只给数字，要对应具体的破坏力（碎砖、碎坦克、碎城）。
2.  **指数膨胀**：后期数值通常呈指数级增长，需注意控制崩坏。

## 示例输入
- 基准：1 战力 = 成年人拿木棍。
- 档位：E 级碎砖、A 级毁坦克、S 级摧毁城市街区。
