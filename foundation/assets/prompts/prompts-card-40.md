---
id: prompts-card-create_antagonist-40
asset_type: prompt_card
title: 极致反派/打脸对象设计
topic: [通用]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/40.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_antagonist
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 40. 极致反派/打脸对象设计

## 提示词内容

```json
{
  "task": "create_antagonist",
  "relation_to_mc": "{{relation}}",
  "output_structure": {
    "name": "姓名",
    "social_status": "社会地位 (通常高于前期的主角)",
    "offense_type": "冒犯类型 (如: 夺宝、退婚、羞辱)",
    "psychology": "作恶心理逻辑 (自洽的歪理)",
    "weakness": "被主角针对的弱点",
    "face_slap_outcome": "被打脸后的下场 (结局)"
  }
}
```

## 使用场景
反派设计。制造完美的“沙包”以供打脸。

## 最佳实践要点
1.  **逻辑自洽**：即使是无脑反派，也需要 `psychology`（自洽的歪理），避免人物过于纸片化。
2.  **地位差**：设定高于主角的 `social_status`，增强打脸时的爽感（下克上）。

## 示例输入
将 `{{relation}}` 替换为“看不起主角的富二代”。
