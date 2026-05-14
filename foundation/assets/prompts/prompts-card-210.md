---
id: prompts-card-generate_achievements-210
asset_type: prompt_card
title: 成就系统与称号设计
topic: [系统, 网游, 奖励]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/210.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_achievements
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 210. 成就系统与称号设计

## 提示词内容

```json
{
  "task": "generate_achievements",
  "context": "MC just killed a dragon with a frying pan",
  "achievements": [
    {"name": "Dragon Slayer", "desc": "Kill a dragon.", "reward": "+10 STR"},
    {"name": "Kitchen Nightmare", "desc": "Kill a boss with a cooking utensil.", "reward": "Title: Chef of Death"},
    {"name": "David vs. Goliath", "desc": "Kill an enemy 100 levels higher.", "reward": "Skill: Giant Killer"}
  ],
  "hidden_achievement": "Unlocked for doing something stupid but brave."
}
```

## 使用场景
系统/网游文。通过成就奖励反馈主角的行为。

## 最佳实践要点
1.  **吐槽风**：成就名称和描述可以带有系统的吐槽或玩梗。
2.  **即时反馈**：行为完成后立即弹出成就，增强爽感。

## 示例输入
- 系统类型：仙侠修炼成就
- 玩家行为：越级击败心魔、救下敌宗弟子
- 输出：成就名、称号、触发条件、奖励
