---
id: prompts-card-convert-chapter_to_scenes
asset_type: prompt_card
title: 将章纲转换为场景卡
topic: [通用]
stage: outline
quality_grade: B
source_path: _原料/提示词库参考/prompts/352.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: convert
task_full: convert_chapter_to_scenes
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 352. 流程：章纲转场景卡 (Chapter to Scenes)

## 提示词内容

```json
{
  "task": "convert_chapter_to_scenes",
  "chapter_summary": "MC fights the Wolf King",
  "scenes": [
    {
      "location": "Dark Forest",
      "characters": ["MC", "Wolf King"],
      "goal": "Survive the ambush",
      "action": "MC dodges the first bite",
      "emotion": "Panic -> Calm"
    },
    {
      "location": "Cliff edge",
      "characters": ["MC", "Wolf King"],
      "goal": "Kill the Wolf King",
      "action": "MC uses the trap he set earlier",
      "emotion": "Triumph"
    }
  ]
}
```

## 使用场景
细纲/写作。将一章拆分为具体的场景（通常一章2-3个场景）。

## 最佳实践要点
1.  **场景三要素**：地点、人物、目的。
2.  **变化**：每个场景结束时，主角的状态必须发生改变（受伤、获得信息等）。

## 示例输入
将“主角在拍卖会与反派竞价”这一章拆分为3个场景。
