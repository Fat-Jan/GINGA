---
id: prompts-card-generate_autopsy-report
asset_type: prompt_card
title: 刑侦/法医尸检报告生成
topic: [刑侦]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/77.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_autopsy_report
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 77. 刑侦/法医尸检报告生成

## 提示词内容

```json
{
  "task": "generate_autopsy_report",
  "victim_info": "Male, 30s, Found in river",
  "findings": {
    "Time of Death": "24-36 hours ago",
    "Cause of Death": "Drowning / Blunt Force Trauma / Poison",
    "Trace Evidence": "Skin under fingernails, Specific pollen in lungs",
    "Hidden Clue": "Old scar, Tattoo, Surgery mark"
  },
  "deduction": "The victim was killed elsewhere and dumped here."
}
```

## 使用场景
法医/刑侦文。生成关键的尸检线索。

## 最佳实践要点
1.  **客观描述**：报告本身应客观冷静，推理由主角完成。
2.  **关键细节**：埋设一个打破常规认知的线索（如“死后伤”）。

## 示例输入
- 死者：男性，约 32 岁，被发现于城郊河道。
- 发现：肺内无河水，指甲缝有蓝色纤维，后颈有针孔。
- 推论：先被药物控制并杀害，再抛尸伪装溺水。
