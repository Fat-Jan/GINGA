---
id: prompts-card-design_game_ui_log-162
asset_type: prompt_card
title: 游戏化叙事：UI 与系统日志设计
topic: [网游, 系统, 赛博朋克]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/162.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_game_ui_log
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 162. 游戏化叙事：UI 与系统日志设计

## 提示词内容

```json
{
  "task": "design_game_ui_log",
  "context": "Boss Battle / crafting",
  "ui_elements": [
    "[System] Health: 15% (Critical)",
    "[Alert] Boss 'Dragon' is preparing 'Breath Attack'",
    "[Buff] 'Adrenaline' activated: Speed +50%"
  ],
  "visual_layout": "Floating red text / Glitching holographic window",
  "instruction": "Integrate these UI prompts into the narrative flow."
}
```

## 使用场景
网游/系统/赛博朋克文。增强“游戏感”和紧张度。

## 最佳实践要点
1.  **节奏卡点**：系统提示应与动作同步（如挥剑时弹出暴击数字）。
2.  **视觉化**：描写 UI 的颜色、字体和动态效果（如警告红字的闪烁）。

## 示例输入
- 类型：末日生存系统
- 场景：主角首次进入污染区
- UI元素：生命值、感染度、任务弹窗、错误日志
