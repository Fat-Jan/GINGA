---
id: prompts-card-alternate_history_scenario-165
asset_type: prompt_card
title: 历史平行时空推演 (What If)
topic: [历史, 科幻, 架空]
stage: setting
quality_grade: A
source_path: 原料/提示词库参考/prompts/165.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: alternate_history_scenario
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 165. 历史平行时空推演 (What If)

## 提示词内容

```json
{
  "task": "alternate_history_scenario",
  "point_of_divergence": "Gunpowder was never invented",
  "year": "2024 AD",
  "technology": "Super-advanced steam engines / Crossbow snipers / Bio-engineered mounts",
  "society": "Feudalism persisted / Martial arts rule the world",
  "mc_goal": "Reinvent gunpowder to overthrow the regime"
}
```

## 使用场景
架空历史/科幻。推演一个蝴蝶效应后的新世界。

## 最佳实践要点
1.  **逻辑链**：技术停滞会导致社会制度的停滞（如没有火药，城堡依然坚固，封建制可能延续）。
2.  **替代科技**：人类总会寻找出路，设计一种替代火药的高级技术（如气动武器）。

## 示例输入
```json
{
  "point_of_divergence": "秦朝提前掌握蒸汽机关术",
  "year": "公元 2026 年",
  "mc_goal": "用失传电学打破机关贵族的技术垄断"
}
```
