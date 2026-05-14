---
id: prompts-card-write_post_mortem-34
asset_type: prompt_card
title: 完本总结与新书预告
topic: [通用]
stage: business
quality_grade: B
source_path: _原料/提示词库参考/prompts/34.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_post_mortem
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 34. 完本总结与新书预告

## 提示词内容

```json
{
  "task": "write_post_mortem",
  "book_title": "{{title}}",
  "performance": "Hit / Flop / Average",
  "lessons_learned": ["Pacing was too slow in mid-game", "Female lead was popular"],
  "next_book_teaser": {
    "genre": "Similar but upgraded",
    "hook": "One sentence pitch",
    "release_date": "Coming soon"
  }
}
```

## 使用场景
完结阶段。总结经验并为新书引流。

## 最佳实践要点
1.  **经验沉淀**：诚实复盘优缺点，作为下一本书的养分。
2.  **流量承接**：在完本感言中顺滑植入新书预告，最大化保留老读者。

## 示例输入
填入书名。
