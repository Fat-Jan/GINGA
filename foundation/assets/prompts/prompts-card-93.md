---
id: prompts-card-generate_survival_inventory-93
asset_type: prompt_card
title: 荒野求生资源列表
topic: [末世, 生存]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/93.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_survival_inventory
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 93. 荒野求生资源列表

## 提示词内容

```json
{
  "task": "generate_survival_inventory",
  "biome": "Jungle / Desert / Arctic",
  "mc_gear": ["Knife", "Flint", "Paracord"],
  "resources_found": [
    {"item": "Edible berries", "use": "Food"},
    {"item": "Dry moss", "use": "Tinder"},
    {"item": "Bamboo", "use": "Building material/Container"}
  ],
  "crafting_goal": "Build a rainproof shelter before nightfall"
}
```

## 使用场景
荒野求生文。列出真实的求生资源和合成路线。

## 最佳实践要点
1.  **知识硬核**：引用的求生知识（如什么植物能吃）必须准确。
2.  **目标驱动**：资源收集必须服务于当下的生存目标（如避雨、生火）。

## 示例输入
- 环境：雨林，主角只剩小刀、打火石和半卷伞绳。
- 资源：竹子、干苔藓、可疑浆果、溪边黏土。
- 目标：天黑前搭出避雨庇护所并找到安全饮水。
