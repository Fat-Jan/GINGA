---
id: prompts-card-write-combat_scene-13
asset_type: prompt_card
title: 战斗场景生成
topic: [玄幻, 仙侠]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/13.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: setup_card
task_verb: write
task_full: write_combat_scene
granularity: scene
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 13. 战斗场景生成

## 提示词内容

```json
{
  "task": "write_combat_scene",
  "participants": ["{{attacker}}", "{{defender}}"],
  "setting": "{{location}}",
  "style": "Visceral, Fast-paced",
  "requirements": {
    "sensory_details": "Sound of impact, smell of blood, visual effects",
    "move_set": "Use specific skill names defined in world building",
    "reaction": "Spectator shock or inner monologue",
    "outcome": "Clear winner with consequence"
  }
}
```

## 使用场景
正文写作。生成高燃、画面感强的打斗描写。

## 最佳实践要点
1.  **感官描写**：强制要求包含声、光、嗅觉细节，提升沉浸感。
2.  **侧面烘托**：通过“Spectator shock”描写，侧面体现主角的强大（装逼）。

## 示例输入
将 `{{attacker}}` 替换为“主角（练气期）”，`{{defender}}` 替换为“反派（筑基期）”，`{{location}}` 替换为“宗门擂台”。
