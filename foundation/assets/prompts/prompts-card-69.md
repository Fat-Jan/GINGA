---
id: prompts-card-construct_misunderstanding_chain-69
asset_type: prompt_card
title: 迪化流误解链构建
topic: [玄幻, 都市, 系统]
stage: drafting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/69.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: construct
task_full: construct_misunderstanding_chain
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 69. 迪化流误解链构建

## 提示词内容

```json
{
  "task": "construct_misunderstanding_chain",
  "mc_action": "Doing something mundane (e.g., watering plants)",
  "bystander_perspective": "Overanalyzing (e.g., 'He is nurturing the World Tree!')",
  "logic_leap": [
    "Fact: MC uses a weird bottle",
    "Interpretation: That must be the Holy Grail",
    "Conclusion: MC is a hidden god living in seclusion"
  ],
  "outcome": "Bystander kneels/offers tribute, MC is confused but accepts"
}
```

## 使用场景
迪化流/脑补流。构建“主角由于太强而被误解”的爽点。

## 最佳实践要点
1.  **信息差**：主角视角（普通）vs 配角视角（恐怖/神圣）。
2.  **逻辑自洽**：配角的脑补逻辑在他们的世界观里必须是合理的。

## 示例输入
```json
{
  "mc_action": "主角随手给枯树浇水",
  "bystander_perspective": "长老认定他在唤醒上古神木",
  "outcome": "全宗门跪拜，主角以为大家在感谢他打扫庭院"
}
```
