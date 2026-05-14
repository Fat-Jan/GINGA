---
id: prompts-card-create-chat_group_members-72
asset_type: prompt_card
title: 聊天群/群像文成员设定
topic: [玄幻, 都市, 科幻, 历史]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/72.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_chat_group_members
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 72. 聊天群/群像文成员设定

## 提示词内容

```json
{
  "task": "create_chat_group_members",
  "theme": "Villains / Emperors / Anime Characters",
  "members": [
    {"name": "Member A", "origin": "Wuxia", "personality": "Arrogant", "needs": "Revival"},
    {"name": "Member B", "origin": "Sci-Fi", "personality": "Rational", "needs": "Magic"},
    {"name": "Member C", "origin": "History", "personality": "Paranoid", "needs": "Immortality"}
  ],
  "mc_role": "Group Owner / God (Faking it)",
  "interaction_style": "Trading info/items, cross-world help"
}
```

## 使用场景
聊天群流。设计群成员和互动模式。

## 最佳实践要点
1.  **跨界碰撞**：利用不同世界观角色的认知差异制造笑点。
2.  **忽悠大法**：主角作为群主，通常需要维持高深莫测的形象（忽悠群员）。

## 示例输入
将 `{{theme}}` 替换为“反派聊天群”。
