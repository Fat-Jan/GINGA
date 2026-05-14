---
id: prompts-card-generate_conlang_slang-103
asset_type: prompt_card
title: 架空语言与黑话生成器
topic: [奇幻, 科幻]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/103.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_conlang_slang
granularity: world
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 103. 架空语言与黑话生成器

## 提示词内容

```json
{
  "task": "generate_conlang_slang",
  "culture": "Thieves Guild / Cyberpunk Street / Ancient Elves",
  "keywords": ["Police", "Money", "Friend", "Enemy", "Magic"],
  "output_format": [
    {"word": "Smog", "meaning": "Police (Cyberpunk)", "origin": "They cloud the truth"},
    {"word": "Shinies", "meaning": "Money (Thieves)", "origin": "Visual trait"},
    {"word": "Root-brother", "meaning": "Friend (Elves)", "origin": "Shared tree roots"}
  ],
  "usage_example": "A sentence using these slang terms naturally."
}
```

## 使用场景
沉浸式世界观构建。增加对话的地域特色和职业感。

## 最佳实践要点
1.  **文化投射**：黑话反映了该群体的价值观（如精灵重视自然）。
2.  **适度使用**：不要通篇黑话，仅在关键名词上使用，避免阅读障碍。

## 示例输入
```json
{
  "culture": "赛博贫民窟黑客帮",
  "keywords": ["警察", "钱", "朋友", "背叛", "芯片"],
  "usage_example": "写 1 句自然夹杂黑话的交易对白"
}
```
