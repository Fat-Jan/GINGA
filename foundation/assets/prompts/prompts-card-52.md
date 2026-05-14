---
id: prompts-card-progression-tech_tree_path
asset_type: prompt_card
title: 攀科技树路径规划 (种田文)
topic: [历史, 种田, 基建]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/52.md
last_updated: 2026-05-13
card_intent: outline_planning
card_kind: scene_card
task_verb: plan
task_full: tech_tree_progression
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 52. 攀科技树路径规划 (种田文)

## 提示词内容

```json
{
  "task": "tech_tree_progression",
  "starting_era": "Stone Age / Medieval",
  "goal_era": "Industrial Revolution",
  "key_inventions": [
    {
      "name": "Cement / Glass",
      "prerequisite": "Limestone, Kiln",
      "impact": "Better housing, trade goods"
    },
    {
      "name": "Gunpowder",
      "prerequisite": "Sulfur, Charcoal, Saltpeter",
      "impact": "Military dominance"
    },
    {
      "name": "Steam Engine",
      "prerequisite": "High quality steel, Coal",
      "impact": "Production efficiency explosion"
    }
  ],
  "bottlenecks": ["Lack of rubber", "Religious opposition", "Educated workforce"]
}
```

## 使用场景
历史种田/基建文。规划科技发展的合理路径。

## 最佳实践要点
1.  **前置条件**：列出 `prerequisite`，体现科技发展的逻辑性（不是凭空捏造）。
2.  **社会影响**：关注 `impact` 和 `bottlenecks`，描写科技进步带来的社会变革和阻力。

## 示例输入
- 起点：中世纪领地，缺铁、缺玻璃、识字率低。
- 目标：三年内建立水泥路、玻璃温室和简易蒸汽抽水机。
- 阻力：教会质疑、工匠保守、硝石来源不稳定。
