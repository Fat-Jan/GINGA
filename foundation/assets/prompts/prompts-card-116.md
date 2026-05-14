---
id: prompts-card-generate_spinoff_plot-116
asset_type: prompt_card
title: 为高人气配角生成独立支线故事
topic: [通用]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/116.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: generate_spinoff_plot
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 116. 配角番外篇/支线生成

## 提示词内容

```json
{
  "task": "generate_spinoff_plot",
  "character": "The Loyal Butler / The Villain's Henchman",
  "timeline": "Before main story / Parallel to Chapter 50",
  "theme": "Tragedy / Hidden Romance / Secret Mission",
  "reveal": "Why they made that specific choice in the main story",
  "twist": "They actually saved the MC secretly"
}
```

## 使用场景
丰富世界观/回馈粉丝。为高人气配角创作独立故事。

## 最佳实践要点
1.  **补完人设**：解释配角在正文中行为的深层动机。
2.  **视角转换**：从侧面看主角，往往能衬托主角的形象。

## 示例输入
```json
{
  "character": "反派身边沉默的侍卫",
  "timeline": "正文第 50 章之前",
  "reveal": "他曾暗中放走主角母亲",
  "theme": "忠诚与亏欠"
}
```
