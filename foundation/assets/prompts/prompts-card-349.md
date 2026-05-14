---
id: prompts-card-track-villain_actions-349
asset_type: prompt_card
title: 反派行动逻辑表
topic: [通用]
stage: outline
quality_grade: B
source_path: _原料/提示词库参考/prompts/349.md
last_updated: 2026-05-13
card_intent: management_tracking
card_kind: scene_card
task_verb: track
task_full: track_villain_actions
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 349. 细纲：反派行动逻辑表 (Villain Action Plan)

## 提示词内容

```json
{
  "task": "track_villain_actions",
  "timeline": "While MC is leveling up in the forest (Chapters 10-20)",
  "villain_location": "Dark Fortress",
  "villain_goal": "Summon the Demon Lord",
  "actions": [
    "Sacrificing a village",
    "Sending assassins to find MC",
    "Bribing the King's advisor"
  ],
  "intersection": "MC finds the destroyed village in Chapter 21"
}
```

## 使用场景
细纲/大纲。世界是动态的，反派不会挂机等主角。

## 最佳实践要点
1.  **平行线**：主角发育的同时，反派也在推进阴谋。
2.  **交汇**：两条线索最终必须交汇，引爆冲突。

## 示例输入
规划反派BOSS在主角“闭关修炼三年”期间的行动轨迹。
