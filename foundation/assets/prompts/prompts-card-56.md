---
id: prompts-card-design-short_drama_twists
asset_type: prompt_card
title: 短剧高能反转节点设计
topic: [短剧, 女频]
stage: framework
quality_grade: A
source_path: _原料/提示词库参考/prompts/56.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_short_drama_twists
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 56. 短剧高能反转节点设计

## 提示词内容

```json
{
  "task": "design_short_drama_twists",
  "episode_duration": "1-2 minutes",
  "total_episodes": 5,
  "plot_arc": {
    "Ep 1": "Humiliation -> Twist (Identity Reveal)",
    "Ep 2": "Slap Face -> New Crisis (Kidnapping)",
    "Ep 3": "Rescue -> Misunderstanding (Cheating?)",
    "Ep 4": "Truth -> Reconciliation",
    "Ep 5": "Proposal -> Villain Returns (Cliffhanger)"
  },
  "hook_density": "At least one reversal every 30 seconds"
}
```

## 使用场景
短剧大纲。规划每集的看点和反转。

## 最佳实践要点
1.  **极速反转**：短剧节奏极快，要求每集甚至每半分钟都有反转。
2.  **钩子结尾**：每集结尾必须有悬念（Cliffhanger），诱导用户滑向下一集。

## 示例输入
```json
{
  "total_episodes": 6,
  "plot_arc": "假千金被逐出家门后，每集 30 秒一次身份反转",
  "hook_density": "每集结尾留下新证据或新背叛"
}
```
