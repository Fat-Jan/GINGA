---
id: prompts-card-design_map_logic-247
asset_type: prompt_card
title: 地图绘制辅助：区域连接逻辑
topic: [奇幻, 冒险]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/247.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_map_logic
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 247. 地图绘制辅助：区域连接逻辑

## 提示词内容

```json
{
  "task": "design_map_logic",
  "zones": ["Desert", "Ice Tundra", "Jungle"],
  "transition": [
    "Desert -> Mountain Range (Rain shadow) -> Jungle",
    "Ice Tundra -> Magic Barrier -> Lava Zone"
  ],
  "landmarks": "The Spire acts as a central hub",
  "travel_time": "3 days by horse, 1 hour by portal"
}
```

## 使用场景
奇幻/冒险文。构建地理逻辑自洽的世界地图。

## 最佳实践要点
1.  **自然过渡**：地形变化应符合地理规律（如山脉阻挡水汽形成沙漠），或者有魔法解释。
2.  **交通节点**：设计必经之路（如关隘、桥梁），方便安排剧情冲突。

## 示例输入
- 区域：北方雪原、中央王都、南部雨林、东侧火山群。
- 连接逻辑：雪原因高海拔形成寒流，火山灰滋养雨林土壤。
- 交通：王都到雨林需走七日商道，法师塔传送每月只开放一次。
