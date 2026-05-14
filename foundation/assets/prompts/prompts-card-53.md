---
id: prompts-card-design-locked_room_mystery-53
asset_type: prompt_card
title: 设计密室杀人诡计
topic: [悬疑, 刑侦, 推理]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/53.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_locked_room_mystery
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 53. “不可能犯罪”诡计设计

## 提示词内容

```json
{
  "task": "design_locked_room_mystery",
  "setting": "Snowy Villa / High-rise Apartment / Moving Train",
  "victim": "Rich Businessman",
  "method": "Mechanical trick / Psychological blind spot / Ice weapon",
  "clues": [
    {"item": "Wet carpet", "inference": "Melted ice"},
    {"item": "Fishing line", "inference": "Remote trigger"},
    {"item": "Broken clock", "inference": "Time manipulation"}
  ],
  "solution": "Step-by-step reconstruction of the crime"
}
```

## 使用场景
悬疑/刑侦/推理文。设计核心的杀人诡计。

## 最佳实践要点
1.  **核心诡计**：明确是机械诡计还是心理诡计。
2.  **线索铺设**：提供具体的 `clues` 及其推导逻辑，确保读者能参与推理（公平性）。

## 示例输入
- 场景：暴雪封山的别墅，书房门窗从内反锁。
- 死者：收藏家胸口中刀，壁炉旁只有一滩水迹。
- 线索：钓鱼线、停摆座钟、窗台上不该出现的盐粒。
