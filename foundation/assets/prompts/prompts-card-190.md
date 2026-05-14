---
id: prompts-card-generate_forum_comments-190
asset_type: prompt_card
title: 弹幕/论坛体生成器 (玩梗版)
topic: [电竞, 系统]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/190.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_forum_comments
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 190. 弹幕/论坛体生成器 (玩梗版)

## 提示词内容

```json
{
  "task": "generate_forum_comments",
  "topic": "Did you see that rookie solo the boss?",
  "users": ["NoobSlayer69", "LoreMaster", "Troll"],
  "comments": [
    "NoobSlayer69: Fake. Must be CGI.",
    "LoreMaster: Actually, that sword technique is from the Lost Era...",
    "Troll: LMAO he tripped at the end tho."
  ],
  "slang": "LOL, OP, Nerf plz, GGEZ"
}
```

## 使用场景
电竞/直播/系统文。模拟真实的玩家/观众反应。

## 最佳实践要点
1.  **ID人设**：ID 往往暴露性格（如“xx大神”、“喷子”）。
2.  **玩梗**：大量使用网络用语和缩写，增加代入感。

## 示例输入
- 话题：新人玩家单刷世界 Boss。
- 用户：考据党、阴阳怪气党、路人震惊党，各发 2 条弹幕。
