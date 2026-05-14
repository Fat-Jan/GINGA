---
id: prompts-card-convert_broad_outline_to_chapters-351
asset_type: prompt_card
title: 将粗纲事件拆解为章纲
topic: [通用]
stage: outline
quality_grade: B
source_path: _原料/提示词库参考/prompts/351.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: convert
task_full: convert_broad_outline_to_chapters
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 351. 流程：粗纲转章纲 (Broad to Chapter)

## 提示词内容

```json
{
  "task": "convert_broad_outline_to_chapters",
  "broad_event": "MC enters the Secret Realm and finds the Fire Essence",
  "chapter_count": 3,
  "structure": {
    "Chapter 1": "Setup & Entry (Conflict at the gate)",
    "Chapter 2": "Exploration & Danger (Fighting the guardian beast)",
    "Chapter 3": "Climax & Reward (Obtaining the Fire Essence)"
  },
  "hooks": "End each chapter with a cliffhanger"
}
```

## 使用场景
大纲/细纲。将一句话的粗略剧情拆解为具体的章节安排。

## 最佳实践要点
1.  **拆分**：一个大事件通常需要3-5章来铺垫和解决。
2.  **钩子**：每章结尾必须留住读者。

## 示例输入
将“主角参加宗门大比获得冠军”拆分为5章细纲。
