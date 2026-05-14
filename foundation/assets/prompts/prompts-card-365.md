---
id: prompts-card-check_foreshadowing_payoff-365
asset_type: prompt_card
title: 流程：伏笔回收检查 (Foreshadowing Payoff)
topic: [通用]
stage: refinement
quality_grade: B
source_path: _原料/提示词库参考/prompts/365.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: check_foreshadowing_payoff
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 365. 流程：伏笔回收检查 (Foreshadowing Payoff)

## 提示词内容

```json
{
  "task": "check_foreshadowing_payoff",
  "setup": "Chapter 5: MC finds a strange key.",
  "current_chapter": "Chapter 100",
  "opportunity": "MC reaches the Ancient Gate",
  "action": "MC remembers the key and uses it.",
  "narration": "Highlighting the connection ('So that's what it was for!')"
}
```

## 使用场景
大纲/写作。确保之前的坑都能填上，产生“草蛇灰线”的效果。

## 最佳实践要点
1.  **跨度**：跨度越大的伏笔回收，读者越有成就感。
2.  **提醒**：回收时要稍微提醒一下读者伏笔埋下的位置。

## 示例输入
检查“主角第一章捡到的戒指”是否在“第一百章”用上了。
