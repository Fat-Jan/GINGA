---
id: prompts-card-design-time_loop
asset_type: prompt_card
title: 时间循环机制设计
topic: [无限流, 悬疑]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/108.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_time_loop
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 108. 时间循环机制设计 (开端流)

## 提示词内容

```json
{
  "task": "design_time_loop",
  "trigger": "Death / Falling asleep / Specific time (12:00 PM)",
  "reset_point": "Start of the day / 5 minutes before disaster",
  "memory_rule": "Only MC remembers / MC + Villain remember",
  "exit_condition": "Save everyone / Find the killer / Break the artifact",
  "debuff": "Each loop reduces MC's stamina / sanity"
}
```

## 使用场景
无限流/悬疑文。构建严谨的时间循环规则。

## 最佳实践要点
1.  **代价递增**：循环次数不能无限，需设置 `debuff` 增加紧迫感。
2.  **变量控制**：每次循环主角的微小改变引发蝴蝶效应，推动剧情。

## 示例输入
```json
{
  "trigger": "每天 23:17 主角在公交爆炸中死亡",
  "reset_point": "当天 07:30 醒来",
  "exit_condition": "找出携带炸弹的乘客并让全车存活"
}
```
