---
id: prompts-card-generate_relationship_chart-80
asset_type: prompt_card
title: 人物关系图谱 (Mermaid格式)
topic: [通用]
stage: outline
quality_grade: B+
source_path: _原料/提示词库参考/prompts/80.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_relationship_chart
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 80. 人物关系图谱 (Mermaid格式)

## 提示词内容

```json
{
  "task": "generate_relationship_chart",
  "characters": ["MC", "Heroine", "Villain", "Rival"],
  "format": "Mermaid Code",
  "relationships": [
    "MC -- Loves --> Heroine",
    "Villain -- Hates --> MC",
    "Rival -- Competes with --> MC",
    "Heroine -- Secretly protects --> MC"
  ],
  "instruction": "Output a Mermaid flowchart code block visualizing these connections."
}
```

## 使用场景
大纲梳理/复杂关系整理。生成可视化的关系图。

## 最佳实践要点
1.  **可视化**：利用 Mermaid 语法，可直接在支持 Markdown 的编辑器中渲染为图表。
2.  **动态更新**：随着剧情发展，随时更新关系连线（如“敌人”变为“盟友”）。

## 示例输入
- 人物：沈砚、林照雪、顾衡、陆夫人。
- 关系：沈砚暗恋林照雪；顾衡与沈砚竞争；陆夫人秘密资助顾衡。
- 输出：生成 Mermaid flowchart，并在连线上标注关系动词。
