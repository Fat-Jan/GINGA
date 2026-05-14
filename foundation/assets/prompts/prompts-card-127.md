---
id: prompts-card-generate-loot_affixes-127
asset_type: prompt_card
title: 装备随机词条生成器 (暗黑风)
topic: [网游, 系统流]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/127.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_loot_affixes
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 127. 装备随机词条生成器 (暗黑风)

## 提示词内容

```json
{
  "task": "generate_loot_affixes",
  "item_base": "Sword / Armor / Ring",
  "rarity": "Legendary / Epic",
  "affixes": [
    {"prefix": "Vampiric", "effect": "Life steal on hit"},
    {"suffix": "of the Bear", "effect": "+Vitality"},
    {"unique": "Explodes enemies on death dealing 100% weapon damage"}
  ],
  "flavor_text": "A short lore description."
}
```

## 使用场景
网游/系统流。生成具有随机感的装备属性。

## 最佳实践要点
1.  **词缀组合**：前缀决定攻击属性，后缀决定基础属性，Unique 决定特效。
2.  **黄字描述**：Flavor text 增加装备的史诗感和收藏价值。

## 示例输入
- 物品：史诗长弓。
- 需求：生成 2 条前缀、2 条后缀、1 条传奇唯一词条。
