---
id: prompts-card-generate-metaphors-112
asset_type: prompt_card
title: 创意比喻与修辞生成器
topic: [通用]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/112.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_metaphors
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 112. 创意比喻与修辞生成器

## 提示词内容

```json
{
  "task": "generate_metaphors",
  "subject": "{{subject}}",
  "tone": "Dark / Romantic / Humorous",
  "count": 3,
  "examples": [
    "Dark: His smile was a裂 wound in a corpse.",
    "Humorous: He danced like a drunk giraffe on ice."
  ],
  "instruction": "Create unique, vivid metaphors avoiding clichés."
}
```

## 使用场景
文笔提升。为文章增添文学色彩或幽默感。

## 最佳实践要点
1.  **陌生化**：将两个看似不相关的意象连接起来，制造新鲜感。
2.  **风格匹配**：比喻必须符合全书的基调（如恐怖文用尸体、伤口做喻体）。

## 示例输入
将 `{{subject}}` 替换为“孤独”。
