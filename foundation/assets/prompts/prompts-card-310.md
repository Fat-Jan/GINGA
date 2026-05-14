---
id: prompts-card-generate_autopsy_report-310
asset_type: prompt_card
title: 生成悬疑题材的尸检报告/法医鉴定
topic: [悬疑, 刑侦, 推理]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/310.md
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

# 310. 悬疑：尸检报告/法医鉴定 (Autopsy Report)

## 提示词内容

```json
{
  "task": "generate_autopsy_report",
  "victim": "Male, 30s, found in river",
  "cause_of_death": "Drowning (fake) / Blunt force trauma",
  "time_of_death": "24-36 hours ago",
  "findings": [
    "Water in lungs matches a bathtub, not the river",
    "Defense wounds on forearms",
    "Trace of rare pollen under fingernails"
  ],
  "conclusion": "Homicide staged as suicide"
}
```

## 使用场景
刑侦/悬疑/推理。提供专业的线索，推动破案。

## 最佳实践要点
1.  **专业术语**：尸斑、尸僵、生活反应等词汇的使用。
2.  **关键反转**：鉴定结果往往推翻之前的推测。

## 示例输入
受害者看似上吊自杀，但尸检发现舌骨未骨折。
