---
id: prompts-card-generate-125
asset_type: prompt_card
title: 心理侧写报告生成
topic: [刑侦, 心理罪]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/125.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_psychological_profile
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 125. 心理侧写 (Profiler) 报告生成

## 提示词内容

```json
{
  "task": "generate_psychological_profile",
  "subject": "Serial Killer / Mysterious Hacker",
  "crime_scene_evidence": "Organized / Overkill / Souvenirs taken",
  "profile": {
    "Age/Gender": "Male, 25-35",
    "Social Skills": "Loner but charming",
    "Job": "Menial labor or highly technical",
    "Trigger": "Rejection by a mother figure"
  },
  "prediction": "He will strike again at [Location] because [Reason]"
}
```

## 使用场景
刑侦/心理罪。通过侧写推动案情分析。

## 最佳实践要点
1.  **证据支撑**：每一条侧写结论都必须基于现场证据（如“过度杀戮”推导“仇恨动机”）。
2.  **预测性**：侧写不仅是描述过去，更是为了预测未来。

## 示例输入
```json
{
  "subject": "留下纸鹤的连环纵火犯",
  "crime_scene_evidence": "现场整洁、只烧书房、带走受害者合照",
  "prediction": "下一次目标可能是旧城区心理诊所"
}
```
