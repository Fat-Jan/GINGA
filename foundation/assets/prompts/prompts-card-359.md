---
id: prompts-card-check-logic_plothole
asset_type: prompt_card
title: 检查逻辑漏洞
topic: [通用]
stage: refinement
quality_grade: B+
source_path: _原料/提示词库参考/prompts/359.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: check_scene_logic
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 359. 流程：检查逻辑漏洞 (Logic Plothole Check)

## 提示词内容

```json
{
  "task": "check_scene_logic",
  "scene_text": "[Paste Scene Text Here]",
  "checklist": [
    "Character motivation consistency",
    "Power level consistency",
    "Timeline accuracy",
    "Inventory check (Does he still have the item?)"
  ],
  "output": "List of potential errors"
}
```

## 使用场景
润色/自查。写完一章后，检查有没有硬伤。

## 最佳实践要点
1.  **物品管理**：主角之前获得的道具是不是忘了用？
2.  **战力崩坏**：反派是不是突然降智或变弱了？

## 示例输入
检查这一章：主角明明腿断了，为什么还能跑？
