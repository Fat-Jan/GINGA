---
id: prompts-card-generate_dungeon_rewards-27
asset_type: prompt_card
title: 生成高评级地下城奖励结算画面
topic: [无限流, 游戏流]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/27.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_dungeon_rewards
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 27. S级评分结算画面

## 提示词内容

```json
{
  "task": "generate_dungeon_rewards",
  "rank": "SSS",
  "world_name": "{{world}}",
  "achievements": ["Speedrun", "No Damage", "Hidden Boss Kill", "Pacifist (Fake)"],
  "loot": [
    {"name": "Unique Weapon", "grade": "Legendary", "effect": "OP Ability"},
    {"name": "Skill Book", "grade": "Rare", "effect": "Utility"},
    {"name": "Points", "amount": "100,000"}
  ],
  "global_announcement": "Player [Name] has cleared [Dungeon] with SSS rank!"
}
```

## 使用场景
无限流/游戏流。展示通关奖励，提供数值爽感。

## 最佳实践要点
1.  **数据刷屏**：利用大量的 Loot 和高额数值，给读者直接的视觉冲击。
2.  **全局通告**：加入 `global_announcement`，满足主角的虚荣心和读者的代入感。

## 示例输入
将 `{{world}}` 替换为“生化危机”。
