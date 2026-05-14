---
id: prompts-card-optimize-blurb-5
asset_type: prompt_card
title: 优化小说简介，遵循黄金三行法则
topic: [通用]
stage: business
quality_grade: B+
source_path: _原料/提示词库参考/prompts/5.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: optimize
task_full: optimize_blurb
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 5. 简介优化 (黄金三行法则)

## 提示词内容

```json
{
  "task": "optimize_blurb",
  "book_title": "{{title}}",
  "plot_summary": "{{summary}}",
  "requirements": {
    "golden_three_lines": "Must hook the reader immediately (Conflict/Cheat/Mystery)",
    "body": "Expand on the world and stakes",
    "closing": "Leave a lingering question or promise of satisfaction",
    "tags": "Generate 5-8 relevant tags for algorithm matching"
  }
}
```

## 使用场景
在书名确定后，上架前使用。优化简介的前三行，这是决定读者是否点开的关键。

## 最佳实践要点
1.  **结构化输出**：强制要求包含“黄金三行”、“正文”、“结尾”和“标签”，符合平台推荐算法需求。
2.  **注意力经济**：强调 `golden_three_lines` 的重要性，利用 AI 的总结能力提炼最强钩子。

## 示例输入
将 `{{title}}` 替换为“我的治愈系游戏”，`{{summary}}` 替换为大纲摘要。
