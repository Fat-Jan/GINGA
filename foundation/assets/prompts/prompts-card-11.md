---
id: prompts-card-planning-macro_plot
asset_type: prompt_card
title: 百万字节奏规划
topic: [高武, 玄幻]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/11.md
last_updated: 2026-05-13
card_intent: outline_planning
card_kind: scene_card
task_verb: plan
task_full: macro_plot_planning
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 11. 百万字节奏规划

## 提示词内容

```json
{
  "task": "macro_plot_planning",
  "total_word_count": "1 Million+",
  "genre": "{{genre}}",
  "output_structure": {
    "arcs": [
      {
        "arc_name": "Arc 1: Beginner Village",
        "word_range": "0-150k",
        "key_event": "Awakening -> First Conflict -> Local Tournament",
        "boss": "Local Bully/Rival",
        "power_level": "Level 1-10"
      },
      {
        "arc_name": "Arc 2: City Stage",
        "word_range": "150k-400k",
        "key_event": "Academy Entrance -> Secret Realm -> City War",
        "boss": "City Lord/Organization",
        "power_level": "Level 11-30"
      }
    ]
  }
}
```

## 使用场景
全书大纲规划。防止长篇连载后期崩坏。

## 最佳实践要点
1.  **分卷管理**：将长篇拆解为多个 Arcs，每个 Arc 有独立的 Boss 和升级目标。
2.  **节奏把控**：明确 `word_range`，辅助作者控制剧情进度。

## 示例输入
将 `{{genre}}` 替换为“高武玄幻”。
