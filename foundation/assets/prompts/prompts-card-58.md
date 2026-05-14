---
id: prompts-card-generate_skill_names-58
asset_type: prompt_card
title: 功法/技能取名生成器
topic: [玄幻, 奇幻]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/58.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_skill_names
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 58. 功法/技能取名生成器

## 提示词内容

```json
{
  "task": "generate_skill_names",
  "genre": "Xianxia / Wuxia / Magic",
  "element": "Fire / Sword / Time",
  "style": "Chuuni (Cool/Overpowered) / Daoist (Abstract) / Brutal",
  "count": 5,
  "output_format": [
    {"name": "Nine Dragons Burning Heaven", "effect": "Summons 9 fire dragons"},
    {"name": "...", "effect": "..."}
  ]
}
```

## 使用场景
玄幻/奇幻/游戏文。批量生成好听、有逼格的技能名。

## 最佳实践要点
1.  **风格适配**：根据流派选择中二、道家或暴力风格。
2.  **意象组合**：组合“龙、天、灭、神”等高能词汇。

## 示例输入
- 题材：仙侠剑修。
- 元素：风、雷、因果。
- 输出：生成 8 个技能名，每个附一句效果说明，风格要古雅但有压迫感。
