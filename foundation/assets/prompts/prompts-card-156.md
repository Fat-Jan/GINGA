---
id: prompts-card-write_uncanny_valley-156
asset_type: prompt_card
title: 恐怖谷效应 (Uncanny Valley) 描写
topic: [惊悚, 科幻]
stage: drafting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/156.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_uncanny_valley
granularity: scene
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 156. 恐怖谷效应 (Uncanny Valley) 描写

## 提示词内容

```json
{
  "task": "write_uncanny_valley",
  "subject": "Android / Doppelganger / Corpse",
  "feature": "Smile doesn't reach eyes / Skin looks like wax / Movements are too smooth",
  "reaction": "Deep primal revulsion, hair standing up",
  "instruction": "Describe why it looks human but feels wrong."
}
```

## 使用场景
惊悚/科幻文。描写似人非人的恐怖感。

## 最佳实践要点
1.  **细节违和**：抓住那些“过于完美”或“稍显僵硬”的细节。
2.  **本能排斥**：描写人类基因中对“伪人”的本能恐惧。

## 示例输入
```json
{
  "subject": "仿生人保姆",
  "near_human_traits": ["微笑晚半拍", "眼球追踪过于精准", "皮肤没有毛孔"],
  "scene_goal": "让主角从安心逐渐转为警觉"
}
```
