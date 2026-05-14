---
id: prompts-card-generate_writing_schedule-30
asset_type: prompt_card
title: 百万字分卷日更表
topic: [auxiliary]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/30.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_writing_schedule
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 30. 百万字分卷日更表

## 提示词内容

```json
{
  "task": "generate_writing_schedule",
  "total_words": "1,000,000",
  "daily_target": "4,000 - 6,000 words",
  "structure": {
    "volume_1": "150k words (Launch + First Climax)",
    "volume_2": "350k words (Expansion)",
    "volume_3": "300k words (High Stakes)",
    "volume_4": "200k words (Resolution)"
  },
  "buffer": "10 chapters (Emergency)",
  "milestones": ["First Recommendation", "VIP Launch", "Major Event"]
}
```

## 使用场景
写作计划与管理。确保长期连载的稳定性。

## 最佳实践要点
1.  **量化目标**：设定每日字数和分卷字数，便于执行。
2.  **里程碑管理**：结合平台推荐机制（首秀、上架）规划更新节奏。

## 示例输入
- 总字数：100 万字。
- 日更：6000 字；分 4 卷，标出每卷高潮、转地图节点和休整日。
