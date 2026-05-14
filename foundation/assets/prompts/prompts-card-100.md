---
id: prompts-card-finale_checklist-100
asset_type: prompt_card
title: 全书大结局收束检查表
topic: [通用]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/100.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: finale_checklist
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 100. 全书大结局收束检查表

## 提示词内容

```json
{
  "task": "finale_checklist",
  "loose_ends": [
    "Main Villain Defeated?",
    "Romance Resolved?",
    "Origin of System Explained?",
    "Side Characters' Fate?"
  ],
  "epilogue_scenes": [
    "Wedding / Coronation",
    "Time Skip (Years later)",
    "Hint at Sequel / New Adventure"
  ],
  "emotional_tone": "Bittersweet / Triumphant / Open-ended"
}
```

## 使用场景
完结篇。确保所有坑都填上，给读者一个满意的交代。

## 最佳实践要点
1.  **填坑**：强制检查系统来源、配角结局等容易遗忘的伏笔。
2.  **余韵**：通过“多年后”的番外或彩蛋，让故事在读者心中延续。

## 示例输入
```json
{
  "loose_ends": ["系统来源", "反派残党", "女主承诺", "师父下落"],
  "epilogue_scenes": ["三年后开宗大典", "旧队友重逢"],
  "emotional_tone": "圆满中保留新旅程余韵"
}
```
