---
id: prompts-card-design_branching_skill_tree-120
asset_type: prompt_card
title: 设计分支技能树
topic: [系统, 游戏]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/120.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_branching_skill_tree
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 120. 黄金三章/金手指升级树 (分支版)

## 提示词内容

```json
{
  "task": "design_branching_skill_tree",
  "base_power": "Fire Control",
  "branches": [
    {
      "path": "Destruction",
      "skills": ["Fireball", "Explosion", "Nuclear Flame"],
      "style": "Glass Cannon"
    },
    {
      "path": "Utility/Control",
      "skills": ["Heat Vision", "Fire Wall", "Temperature Manipulation"],
      "style": "Tactician"
    },
    {
      "path": "Fusion",
      "skills": ["Fire + Sword", "Fire + Healing (Phoenix)"],
      "style": "Hybrid"
    }
  ],
  "choice_moment": "MC must choose a path at Level 10"
}
```

## 使用场景
系统/游戏文。设计多样化的成长路线。

## 最佳实践要点
1.  **差异化**：不同分支必须有截然不同的战斗风格（输出vs控制）。
2.  **不可逆**：选择往往是不可逆的，增加决策的重量感。

## 示例输入
- 基础能力：控火。
- 分支：爆破输出、炼器辅助、治疗净化；每支给 3 个技能节点。
