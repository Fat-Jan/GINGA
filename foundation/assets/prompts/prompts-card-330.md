---
id: prompts-card-check_world_building
asset_type: prompt_card
title: 写作工具：世界观检查表 (World Building Checklist)
topic: [通用]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/330.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: check_world_building
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 330. 写作工具：世界观检查表 (World Building Checklist)

## 提示词内容

```json
{
  "task": "check_world_building",
  "aspects": [
    "Geography (Maps, Climate)",
    "Culture (Religion, Taboos)",
    "Economy (Currency, Trade)",
    "Politics (Factions, Laws)",
    "Magic/Tech System (Rules, Costs)"
  ],
  "question": "Is there a contradiction? / Is it too generic?",
  "output": "List of missing elements or logical holes"
}
```

## 使用场景
通用/设定/大纲。确保世界观的完整性和逻辑自洽。

## 最佳实践要点
1.  **细节**：大到国家政体，小到百姓吃什么。
2.  **自洽**：魔法/科技水平必须影响社会形态（如会飞就不需要修路）。

## 示例输入
检查一个“蒸汽朋克+修仙”世界观的逻辑漏洞。
