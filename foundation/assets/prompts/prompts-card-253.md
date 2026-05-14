---
id: prompts-card-design_werewolf_game-253
asset_type: prompt_card
title: 无限流狼人杀副本逻辑设计
topic: [无限流, 智斗]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/253.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_werewolf_game
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 253. 无限流：狼人杀副本逻辑

## 提示词内容

```json
{
  "task": "design_werewolf_game",
  "roles": ["Villager", "Seer", "Werewolf", "Witch"],
  "setting": "An isolated snow mountain lodge",
  "mechanic": "Real death at night / Voting executes players",
  "mc_role": "Werewolf (needs to blend in)",
  "strategy": "Framing the Seer as a Werewolf"
}
```

## 使用场景
无限流/智斗文。经典的身份推理游戏。

## 最佳实践要点
1.  **身份反转**：主角拿到反派牌（如狼人）往往比拿好人牌更有看点。
2.  **心理博弈**：利用言语漏洞和微表情进行攻防，而非单纯靠技能。

## 示例输入
- 副本：暴雪封山的旅馆，天亮前必须投出一名狼人。
- 身份：主角是预言家，但第一晚查到的好人已被杀。
- 机制：投票失败会随机处决两人，女巫药剂只能用一次。
