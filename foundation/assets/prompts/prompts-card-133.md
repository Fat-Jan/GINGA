---
id: prompts-card-generate-black_market_list
asset_type: prompt_card
title: 拍卖行/黑市物品清单生成
topic: [玄幻, 科幻, 历史]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/133.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_black_market_list
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 133. 拍卖行/黑市物品清单生成

## 提示词内容

```json
{
  "task": "generate_black_market_list",
  "theme": "Magic / Cyberpunk / Historical",
  "items": [
    {"name": "Slave Contract (Elf)", "price": "1000 Gold", "risk": "Illegal"},
    {"name": "Stolen Military Chip", "price": "50k Credits", "risk": "Tracked by Gov"},
    {"name": "Cursed Dagger", "price": "Cheap", "risk": "Drains user's life"}
  ],
  "atmosphere": "Shadowy, hushed voices, masked figures"
}
```

## 使用场景
玄幻/科幻文。展示地下世界的丰富度。

## 最佳实践要点
1.  **禁忌感**：黑市物品必须是正规渠道买不到的（违禁品、赃物、诅咒物）。
2.  **风险提示**：每个物品都应附带潜在风险，增加购买的决策成本。

## 示例输入
- 主题：玄幻王都地下拍卖会
- 物品方向：禁术残页、王室赃物、带诅咒的炼金器
- 氛围：低声竞价，面具客互相试探
