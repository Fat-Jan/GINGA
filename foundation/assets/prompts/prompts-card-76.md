---
id: prompts-card-generate-medical_case-76
asset_type: prompt_card
title: 医生/医疗文病例生成
topic: [都市]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/76.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: generate_medical_case
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 76. 医生/医疗文病例生成

## 提示词内容

```json
{
  "task": "generate_medical_case",
  "department": "Emergency / Surgery / TCM",
  "patient_symptoms": "Chest pain, Coughing blood, Low BP",
  "diagnosis_process": [
    "Initial check (Vitals)",
    "Tests (CT, Blood work)",
    "Misdiagnosis (It looks like X but is actually Y)"
  ],
  "treatment": "Surgery details / Acupuncture points",
  "drama": "Patient's family causing trouble / VIP patient"
}
```

## 使用场景
医生文。设计具有专业性和戏剧性的病例。

## 最佳实践要点
1.  **专业性**：使用正确的医学术语和流程。
2.  **反转**：设置误诊或罕见病，体现主角的高超医术。

## 示例输入
- 科室：急诊。
- 症状：胸痛、咳血、低血压；初诊像肺炎，最终发现主动脉夹层。
