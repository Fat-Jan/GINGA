---
id: prompts-card-simulate_reader_comments-16
asset_type: prompt_card
title: 读者评论模拟
topic: [通用]
stage: analysis
quality_grade: B+
source_path: _原料/提示词库参考/prompts/16.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: scene_card
task_verb: simulate
task_full: simulate_reader_comments
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 16. 读者评论模拟

## 提示词内容

```json
{
  "task": "simulate_reader_comments",
  "chapter_content": "{{content}}",
  "reader_personas": [
    "The Nitpicker (Logic holes)",
    "The Fanboy (Hype)",
    "The Skimmer (Pacing)",
    "The Shipper (Romance)"
  ],
  "output_format": "List of comments with user IDs and likes"
}
```

## 使用场景
章节完成后。检测潜在毒点或爽点是否到位。

## 最佳实践要点
1.  **多视角模拟**：引入不同类型的读者画像（考据党、CP党、小白读者），全面评估内容。
2.  **情绪检测**：通过评论内容反推读者的情绪反应（爽、毒、平）。

## 示例输入
填入章节内容或详细梗概。
