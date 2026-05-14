---
id: prompts-card-generate-lottery_pool
asset_type: prompt_card
title: 随机金手指/系统抽奖池
topic: [玄幻, 科幻, 系统]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/78.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_lottery_pool
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 78. 随机金手指/系统抽奖池

## 提示词内容

```json
{
  "task": "generate_lottery_pool",
  "theme": "General / Cultivation / Tech",
  "pool_size": 10,
  "tiers": {
    "SSR (1%)": ["Time Stop", "Instant Kill"],
    "SR (5%)": ["Flight", "Invisibility"],
    "R (20%)": ["Fireball", "Strength Up"],
    "N (74%)": ["Tissue paper", "Clean water"]
  },
  "draw_result": "Simulate a 10-draw session for MC"
}
```

## 使用场景
系统流/抽奖情节。设计奖池和抽奖结果。

## 最佳实践要点
1.  **垃圾填充**：N级物品应具幽默感或生活化，反衬SSR的珍贵。
2.  **保底机制**：模拟“十连抽必出SR”等机制，符合玩家直觉。

## 示例输入
```json
{
  "theme": "末世生存系统",
  "pool_size": 12,
  "draw_result": "模拟主角第一次十连抽，必须包含 1 个看似废物的隐藏神技"
}
```
