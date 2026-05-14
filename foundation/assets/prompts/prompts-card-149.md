---
id: prompts-card-fix_power_creep-149
asset_type: prompt_card
title: 战斗力崩坏补救方案
topic: [玄幻, 奇幻, 科幻, 战斗]
stage: refinement
quality_grade: A-
source_path: _原料/提示词库参考/prompts/149.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: fix
task_full: fix_power_creep
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 149. 战斗力崩坏补救方案

## 提示词内容

```json
{
  "task": "fix_power_creep",
  "current_problem": "MC is too strong, one-shots everyone",
  "solutions": [
    "Introduce a new power system (Magic -> Soul)",
    "Change the victory condition (Protect weak NPC instead of kill)",
    "Disable MC's power temporarily (Curse/Poison)",
    "Introduce a counter-type enemy (e.g., Anti-magic)"
  ]
}
```

## 使用场景
长篇连载中期。解决战力膨胀导致的可看性下降。

## 最佳实践要点
1.  **限制而非削弱**：不要直接削弱主角数值，而是通过环境或规则限制其发挥。
2.  **维度升级**：引入更高维度的力量体系，让主角重新变成“新手”。

## 示例输入
```json
{
  "problem": "主角第 80 章已能秒杀同阶所有敌人",
  "fix_direction": "引入规则压制、资源代价和跨境界克制",
  "constraint": "不能直接削弱主角已获得的能力"
}
```
