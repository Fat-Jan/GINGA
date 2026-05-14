---
id: prompts-card-generate_dungeon_map-126
asset_type: prompt_card
title: 随机地下城地图生成 (ASCII/文字版)
topic: [奇幻, 科幻, DND, 网游]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/126.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_dungeon_map
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 126. 随机地下城地图生成 (ASCII/文字版)

## 提示词内容

```json
{
  "task": "generate_dungeon_map",
  "theme": "Catacombs / Space Station / Forest Maze",
  "size": "5x5 grid",
  "legend": {
    "S": "Start",
    "E": "Exit/Boss",
    "T": "Trap",
    "L": "Loot",
    "M": "Monster",
    "#": "Wall"
  },
  "layout_description": "A textual representation of the grid with a brief description of key rooms."
}
```

## 使用场景
DND/无限流/网游文。辅助设计副本结构。

## 最佳实践要点
1.  **路径规划**：确保起点到终点有路可走，且必须经过挑战（怪/陷阱）。
2.  **探索感**：设置分支路线和隐藏房间（Loot）。

## 示例输入
```json
{
  "theme": "地下墓穴",
  "size": "5x5 grid",
  "must_include": ["起点", "陷阱", "隐藏宝箱", "Boss 出口"],
  "layout_description": "给出 ASCII 地图和每个关键房间 1 句说明"
}
```
