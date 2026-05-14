---
id: prompts-card-balance_system_data-360
asset_type: prompt_card
title: 流程：金手指数据平衡 (System Balance Check)
topic: [系统]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/360.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: balance
task_full: balance_system_data
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 360. 流程：金手指数据平衡 (System Balance Check)

## 提示词内容

```json
{
  "task": "balance_system_data",
  "current_level": "Level 10",
  "enemy_level": "Level 15",
  "mc_stats": {"STR": 50, "AGI": 30},
  "enemy_stats": {"STR": 80, "AGI": 20},
  "skill_effect": "Double damage critical hit",
  "calculation": "Can MC win logically? (50 * 2 > 80?)",
  "adjustment": "Nerf the skill / Buff the enemy HP"
}
```

## 使用场景
设定/写作。系统流必备，防止数值崩坏。

## 最佳实践要点
1.  **越级挑战**：主角可以越级，但必须有逻辑支持（如克制、暴击）。
2.  **通货膨胀**：检查数值是否膨胀过快。

## 示例输入
计算主角“练气期”能否打败“筑基期”敌人，需要什么条件。
