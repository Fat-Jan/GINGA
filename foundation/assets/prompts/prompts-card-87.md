---
id: prompts-card-generate_detective-board-87
asset_type: prompt_card
title: 侦探/解谜游戏线索板
topic: [悬疑, 推理]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/87.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_detective_board
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 87. 侦探/解谜游戏线索板

## 提示词内容

```json
{
  "task": "generate_detective_board",
  "case": "The Phantom Thief",
  "suspects": [
    {"name": "Butler", "motive": "Debt", "alibi": "Fake"},
    {"name": "Heir", "motive": "Inheritance", "alibi": "Witnessed"}
  ],
  "connections": "Red string connecting The Heir to the Black Market",
  "missing_piece": "The murder weapon is still missing"
}
```

## 使用场景
悬疑/推理文。整理案件的人物关系和证据链。

## 最佳实践要点
1.  **可视化思维**：模拟侦探在墙上贴照片、连红线的场景。
2.  **关键缺失**：明确 `missing_piece`，指引接下来的调查方向。

## 示例输入
- 案件：博物馆夜间失窃，馆长次日死在监控盲区。
- 嫌疑人：保安、修复师、赞助商、馆长女儿。
- 缺口：失窃展品未找到，但玻璃柜里多了一枚旧船票。
