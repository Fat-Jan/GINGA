---
id: prompts-card-design_academy_curriculum-73
asset_type: prompt_card
title: 设计学院流课程表与考核体系
topic: [玄幻, 奇幻]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/73.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_academy_curriculum
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 73. 学院流课程表与考核

## 提示词内容

```json
{
  "task": "design_academy_curriculum",
  "type": "Magic / Cultivation / Superpower",
  "year_1_courses": [
    {"name": "Basic Meditation", "content": "Sensing mana/qi"},
    {"name": "Beast Anatomy", "content": "Weaknesses of common monsters"},
    {"name": "Combat Sparring", "content": "Practical application"}
  ],
  "exams": "Monthly ranking battle / Wilderness survival",
  "factions": "Houses / Clubs / Student Council"
}
```

## 使用场景
学院流。构建具体的学习和竞争环境。

## 最佳实践要点
1.  **学以致用**：课程内容应在后续剧情中得到应用（伏笔）。
2.  **阶级对立**：通过分院或排名制造学生间的竞争和冲突。

## 示例输入
```json
{
  "type": "御兽学院",
  "year_1_courses": ["灵兽习性", "野外追踪", "契约反噬急救"],
  "exams": "月末秘境生存排名赛"
}
```
