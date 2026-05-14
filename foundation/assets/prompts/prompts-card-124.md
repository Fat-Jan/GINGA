---
id: prompts-card-structure_nonlinear_plot-124
asset_type: prompt_card
title: 倒叙/插叙结构编排
topic: [悬疑, 刑侦]
stage: framework
quality_grade: A-
source_path: _原料/提示词库参考/prompts/124.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: structure
task_full: structure_nonlinear_plot
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 124. 倒叙/插叙结构编排

## 提示词内容

```json
{
  "task": "structure_nonlinear_plot",
  "opening_scene": "The protagonist's funeral / The final boss battle",
  "timeline_a": "Present day (Investigation/Aftermath)",
  "timeline_b": "Past (How we got here)",
  "thematic_link": "An object (e.g., a broken watch) appearing in both timelines",
  "merge_point": "The final revelation rewriting the opening scene"
}
```

## 使用场景
悬疑/刑侦文。通过非线性叙事增加悬念。

## 最佳实践要点
1.  **开头即高潮**：用最具冲击力的结局作为开头（倒叙），抓住读者。
2.  **双线交织**：过去线解释现在线，现在线推进对过去的理解。

## 示例输入
```json
{
  "opening_scene": "主角葬礼上有人偷走棺中戒指",
  "timeline_a": "现在：女警追查盗墓案",
  "timeline_b": "过去：主角如何假死脱身",
  "merge_point": "戒指里的录音推翻死亡真相"
}
```
