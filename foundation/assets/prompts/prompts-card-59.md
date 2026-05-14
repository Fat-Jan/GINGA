---
id: prompts-card-design_organization-59
asset_type: prompt_card
title: 势力/组织架构设计
topic: [玄幻, 都市, 末世, 系统]
stage: setting
quality_grade: B+
source_path: 原料/提示词库参考/prompts/59.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_organization
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 59. 势力/组织架构设计

## 提示词内容

```json
{
  "task": "design_organization",
  "type": "Sect / Guild / Corporation / Secret Society",
  "name": "{{name}}",
  "motto": "Organization's philosophy",
  "structure": {
    "Leader": "Mysterious / Public Figure",
    "Elites": "The 4 Kings / 7 Swordsmen",
    "Members": "Cannon fodder",
    "Entry_Requirement": "Cruel test / High fee"
  },
  "source_of_power": "Ancient Relic / Monopoly on resource"
}
```

## 使用场景
世界观补充。设计反派组织或主角所在的势力。

## 最佳实践要点
1.  **层级结构**：设计清晰的晋升阶梯（精英、普通成员），方便主角逐级打怪。
2.  **核心资源**：明确组织的立身之本（Source of Power）。

## 示例输入
将 `{{name}}` 替换为“黄昏真理会”。
