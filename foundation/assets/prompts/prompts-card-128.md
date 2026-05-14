---
id: prompts-card-simulate_tarot_reading-128
asset_type: prompt_card
title: 塔罗牌/占卜结果生成
topic: [奇幻, 神秘学]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/128.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: simulate_tarot_reading
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 128. 塔罗牌/占卜结果生成

## 提示词内容

```json
{
  "task": "simulate_tarot_reading",
  "question": "{{question}}",
  "spread": "Three Card Spread (Past, Present, Future)",
  "cards": [
    {"position": "Past", "card": "The Tower (Reversed)", "interpretation": "Avoided disaster"},
    {"position": "Present", "card": "The Fool", "interpretation": "New beginning, naivety"},
    {"position": "Future", "card": "Death", "interpretation": "Transformation, end of an era"}
  ],
  "mystic_advice": "Cryptic warning based on the spread."
}
```

## 使用场景
奇幻/神秘学。为剧情提供预言或暗示。

## 最佳实践要点
1.  **象征意义**：准确使用塔罗牌含义（正/逆位），增加神秘学的专业感。
2.  **模糊性**：预言必须模糊，方便后续剧情灵活解释（填坑）。

## 示例输入
将 `{{question}}` 替换为“这次任务会顺利吗？”。
