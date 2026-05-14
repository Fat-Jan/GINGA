---
id: prompts-card-describe_spaceship_interior-174
asset_type: prompt_card
title: 战舰内部结构图 (文字版)
topic: [科幻]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/174.md
last_updated: 2026-05-13
card_intent: scene_description
card_kind: setup_card
task_verb: describe
task_full: describe_spaceship_interior
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 174. 战舰内部结构图 (文字版)

## 提示词内容

```json
{
  "task": "describe_spaceship_interior",
  "zones": [
    {"name": "Bridge", "desc": "Glass dome, holographic displays, captain's chair"},
    {"name": "Engine Room", "desc": "Roaring reactor, heat, radiation warnings"},
    {"name": "Living Quarters", "desc": "Cramped bunks, smell of recycled air"}
  ],
  "flow": "MC runs from Quarters to Bridge during red alert"
}
```

## 使用场景
科幻/星际文。构建飞船内部的空间感。

## 最佳实践要点
1.  **功能分区**：明确生活区、工作区和动力区的区别（噪音、温度、气味）。
2.  **动线设计**：描写主角在紧急情况下的移动路线，增加紧迫感。

## 示例输入
- 区域：舰桥、动力炉、货舱、医疗湾、逃生舱。
- 动线：主角在红色警报中从货舱冲向舰桥。
