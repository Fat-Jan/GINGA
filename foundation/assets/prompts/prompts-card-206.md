---
id: prompts-card-create_red_herring-206
asset_type: prompt_card
title: 红鲱鱼 (Red Herring) 误导线索
topic: [悬疑, 推理]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/206.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_red_herring
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 206. 红鲱鱼 (Red Herring) 误导线索

## 提示词内容

```json
{
  "task": "create_red_herring",
  "mystery": "Who stole the diamond?",
  "true_culprit": "The Butler",
  "false_lead": "The Maid (who was seen running away)",
  "explanation": "The Maid was running because she broke a vase, not because she stole the diamond.",
  "clue_placement": "Focus heavily on the Maid's nervousness in Chapter 3"
}
```

## 使用场景
悬疑/推理文。设计误导读者和主角的假线索。

## 最佳实践要点
1.  **合理性**：假线索必须有合理解释（如女仆跑是因为别的事），不能强行误导。
2.  **分散注意力**：利用显眼的嫌疑人掩盖真正低调的凶手。

## 示例输入
- 案件：密室毒杀案
- 误导对象：案发前争吵过的继承人
- 真相方向：真正线索藏在茶杯温度里
