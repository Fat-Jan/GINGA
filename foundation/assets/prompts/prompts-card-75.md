---
id: prompts-card-roadmap-island-village-planet
asset_type: prompt_card
title: 种田文基建工程进度表
topic: [种田, 基建]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/75.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: infrastructure_roadmap
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 75. 种田文基建工程进度表

## 提示词内容

```json
{
  "task": "infrastructure_roadmap",
  "location": "Island / Village / Planet",
  "phases": [
    {"phase": "Survival", "goals": ["Shelter", "Water Source", "Fire"]},
    {"phase": "Agriculture", "goals": ["Farming", "Domestication", "Storage"]},
    {"phase": "Industry", "goals": ["Mining", "Smelting", "Manufacturing"]},
    {"phase": "Trade/Expansion", "goals": ["Roads", "Currency", "Diplomacy"]}
  ],
  "mc_role": "Architect / Leader"
}
```

## 使用场景
基建/种田文。规划从无到有的建设过程。

## 最佳实践要点
1.  **需求层次**：遵循马斯洛需求层次，先解决生存，再追求发展。
2.  **成就感**：每个阶段完成时，通过领民的赞叹或生活水平的提升反馈成就感。

## 示例输入
- 地点：海岛村落。
- 阶段：生存取水、开垦农田、烧砖炼铁、修港通商。
