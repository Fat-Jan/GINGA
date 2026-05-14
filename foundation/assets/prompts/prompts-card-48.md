---
id: prompts-card-design_shelter_upgrade_tree-48
asset_type: prompt_card
title: 末世避难所升级树设计
topic: [末世]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/48.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_shelter_upgrade_tree
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 48. 末世避难所升级树

## 提示词内容

```json
{
  "task": "design_shelter_upgrade_tree",
  "theme": "{{theme}}",
  "tech_level": "Near Future / Scavenger / High Tech",
  "upgrade_path": {
    "level_1": {
      "name": "Basic Survival",
      "facilities": ["Rainwater Collector", "Wooden Fence", "Simple Bed"],
      "resource_cost": "Wood, Scrap Metal"
    },
    "level_2": {
      "name": "Self-Sufficiency",
      "facilities": ["Hydroponic Farm", "Solar Panel", "Watchtower"],
      "resource_cost": "Circuit Board, Seeds, Glass"
    },
    "level_3": {
      "name": "Fortress",
      "facilities": ["Automated Turret", "Water Purification System", "Infirmary"],
      "resource_cost": "Steel, CPU, Medicine"
    },
    "level_4": {
      "name": "{{ultimate_form}}",
      "facilities": ["Fusion Reactor", "Force Field", "Clone Vat"],
      "resource_cost": "Rare Earth, Alien Core"
    }
  },
  "visual_feedback": "Describe the visual change of the shelter from Lvl 1 to Lvl 4"
}
```

## 使用场景
末世/生存流小说。设计避难所或基地的建设路线。

## 最佳实践要点
1.  **资源循环**：明确每个等级的 `resource_cost`，推动主角外出探索（推剧情）。
2.  **视觉反馈**：描述避难所外观的变化，增强读者的成就感（种田的快乐）。

## 示例输入
将 `{{theme}}` 替换为“冰河世纪”，`{{ultimate_form}}` 替换为“地下生态城”。
