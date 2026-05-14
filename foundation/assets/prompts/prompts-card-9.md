---
id: prompts-card-create_character_profile-9
asset_type: prompt_card
title: 主角详细档案
topic: [通用]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/9.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_character_profile
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 9. 主角详细档案

## 提示词内容

```json
{
  "task": "create_character_profile",
  "role": "Protagonist",
  "archetype": "{{archetype}}",
  "output_structure": {
    "basic_info": {"name": "", "age": "", "occupation": ""},
    "appearance": "Distinctive features (e.g., scar, eyes)",
    "personality": {
      "traits": ["Positive", "Negative"],
      "motto": "Core belief",
      "fears": "What they are afraid of"
    },
    "background": "Tragic/Mysterious past",
    "goal": {
      "short_term": "Immediate objective",
      "long_term": "Ultimate dream"
    },
    "cheat_synergy": "How the cheat complements their personality"
  }
}
```

## 使用场景
角色设计阶段。构建立体、有动机的主角。

## 最佳实践要点
1.  **动机驱动**：明确 `goal`（短期与长期），这是推动剧情的核心动力。
2.  **缺陷设计**：包含 `fears` 和 `traits`（含负面），使角色更真实，避免“高大全”。

## 示例输入
将 `{{archetype}}` 替换为“腹黑智者”。
