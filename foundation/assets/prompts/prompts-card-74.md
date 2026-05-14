---
id: prompts-card-design-pet_evolution-74
asset_type: prompt_card
title: 宠物/御兽进化路线设计
topic: [玄幻, 都市, 系统]
stage: setting
quality_grade: A-
source_path: 原料/提示词库参考/prompts/74.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_pet_evolution
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 74. 宠物/御兽进化路线设计

## 提示词内容

```json
{
  "task": "design_pet_evolution",
  "base_creature": "{{base_pet}}",
  "element": "Fire / Thunder / Ghost",
  "stages": [
    {"stage": "Baby", "name": "Ember Fox", "skill": "Spark"},
    {"stage": "Mature", "name": "Flame Tail Fox", "skill": "Fireball, Quick Attack"},
    {"stage": "Ultimate", "name": "Nine-Tailed Inferno Lord", "skill": "Meteor Shower, Domain"}
  ],
  "evolution_condition": "Rare item / Specific environment / Bond level"
}
```

## 使用场景
御兽流/宠物文。设计宠物的成长路径。

## 最佳实践要点
1.  **颜值与实力**：进化形态通常要在外观上变帅/变霸气。
2.  **特殊条件**：设置苛刻的进化条件，体现主角的知识/机缘优势。

## 示例输入
将 `{{base_pet}}` 替换为“青毛虫”。
