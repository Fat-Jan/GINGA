---
id: prompts-card-create-adventure_party-106
asset_type: prompt_card
title: 西幻 D&D 冒险小队配置
topic: [西幻]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/106.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_adventure_party
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 106. 西幻 D&D 冒险小队配置

## 提示词内容

```json
{
  "task": "create_adventure_party",
  "theme": "Classic D&D / Dark Fantasy",
  "members": [
    {"role": "Tank", "race": "Dwarf", "quirk": "Claustrophobic"},
    {"role": "DPS", "race": "Elf", "quirk": "Vegan (Complicates rations)"},
    {"role": "Healer", "race": "Human Priest", "quirk": "Gambling addict"},
    {"role": "Face/Leader", "race": "Bard", "quirk": "Can't lie"}
  ],
  "team_dynamic": "Dysfunctional family but loyal in battle"
}
```

## 使用场景
西幻/游戏异界文。设计性格互补、充满戏剧性的冒险团队。

## 最佳实践要点
1.  **缺陷美**：每个成员的 `quirk`（怪癖）应制造日常笑料或小麻烦。
2.  **互补性**：战斗中必须体现职业配合（战法牧铁三角）。

## 示例输入
```json
{
  "theme": "黑暗奇幻 D&D",
  "members": ["矮人盾战", "精灵游侠", "人类牧师", "半身人盗贼"],
  "team_dynamic": "平时互损，战斗时无条件补位"
}
```
