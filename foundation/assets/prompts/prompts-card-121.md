---
id: prompts-card-structure-121
asset_type: prompt_card
title: 群像文多线叙事结构
topic: [战争, 灾难, 校园]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/121.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: structure
task_full: structure_ensemble_cast
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 121. 群像文多线叙事结构

## 提示词内容

```json
{
  "task": "structure_ensemble_cast",
  "theme": "War / Disaster / School Life",
  "plot_lines": [
    {"character": "A (Soldier)", "arc": "Survival"},
    {"character": "B (Politician)", "arc": "Power struggle"},
    {"character": "C (Civilian)", "arc": "Protecting family"}
  ],
  "convergence_point": "Chapter 50: The Siege of the Capital",
  "pacing": "Switch perspectives every chapter / Interwoven scenes"
}
```

## 使用场景
群像文/史诗文。处理多条并行的时间线和人物命运。

## 最佳实践要点
1.  **汇聚点**：所有支线最终必须汇聚到一个大事件（Convergence Point），避免剧情散乱。
2.  **视角切换**：明确切换节奏，保持不同视角的悬念感。

## 示例输入
```json
{
  "theme": "王都沦陷前夜",
  "plot_lines": ["守城将军", "逃难医女", "叛逃王子"],
  "convergence_point": "第 40 章三人在南门火场相遇"
}
```
