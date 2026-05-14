---
id: prompts-card-design_character_arc-122
asset_type: prompt_card
title: 角色弧光 (Character Arc) 设计
topic: [通用]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/122.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_character_arc
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 122. 角色弧光 (Character Arc) 设计

## 提示词内容

```json
{
  "task": "design_character_arc",
  "character": "{{name}}",
  "starting_state": "Cowardly / Selfish / Naive",
  "catalyst": "Death of a mentor / Betrayal",
  "midpoint_shift": "Takes responsibility but fails",
  "climax_choice": "Sacrifices desire for the greater good",
  "ending_state": "Brave / Selfless / Mature"
}
```

## 使用场景
深度人物塑造。设计人物的成长轨迹。

## 最佳实践要点
1.  **变化**：弧光的核心是“变化”，起点和终点必须有显著反差。
2.  **催化剂**：设计具体的事件（Catalyst）推动改变，而非自然发生。

## 示例输入
将 `{{name}}` 替换为“主角”。
