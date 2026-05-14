---
id: prompts-card-design_power_system-6
asset_type: prompt_card
title: 力量体系设计
topic: [玄幻, 科幻, 奇幻]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/6.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_power_system
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 6. 力量体系设计

## 提示词内容

```json
{
  "task": "design_power_system",
  "genre": "{{genre}}",
  "scale": "{{scale}}",
  "output_structure": {
    "levels": [
      {
        "name": "Level Name (e.g., Qi Refining)",
        "characteristics": "Physical/Magical changes",
        "combat_power": "Benchmark (e.g., crush a boulder)",
        "bottleneck": "Requirement to advance"
      }
    ],
    "resource_economy": "Currency/Items needed for cultivation",
    "power_gap": "Can a lower level defeat a higher level? How?"
  }
}
```

## 使用场景
在世界观构建阶段使用。设计清晰、有成长感的等级体系。

## 最佳实践要点
1.  **逻辑自洽**：通过 `power_gap` 字段检查体系是否崩坏（数值膨胀）。
2.  **可视化描述**：要求 `characteristics` 和 `combat_power` 具体化，避免抽象描述。

## 示例输入
将 `{{genre}}` 替换为“赛博修仙”，`{{scale}}` 替换为“星系级”。
