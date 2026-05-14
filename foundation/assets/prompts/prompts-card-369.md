---
id: prompts-card-rewrite-sensory
asset_type: prompt_card
title: 五感沉浸式改写流程
topic: [通用]
stage: refinement
quality_grade: B+
source_path: _原料/提示词库参考/prompts/369.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: rewrite
task_full: rewrite_with_senses
granularity: utility
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 369. 流程：五感沉浸式改写 (Sensory Rewrite)

## 提示词内容

```json
{
  "task": "rewrite_with_senses",
  "original": "He walked into the forest. It was scary.",
  "senses": {
    "Sight": "Twisted shadows stretching like claws",
    "Sound": "Twigs snapping underfoot like breaking bones",
    "Smell": "The stench of rotting leaves and damp earth",
    "Touch": "Cold mist clinging to his skin"
  },
  "result": "Cold mist clung to his skin as he stepped into the gloom. Twisted shadows stretched like claws, and every step snapped twigs that sounded disturbingly like breaking bones. The air reeked of rot."
}
```

## 使用场景
润色/文笔。提升代入感的终极杀招。

## 最佳实践要点
1.  **多维**：至少包含三种感官描写。
2.  **具体**：用具体的名词（如腐烂的叶子）代替抽象的形容词（如可怕）。

## 示例输入
改写“那碗面很好吃”，加入五感描写。
