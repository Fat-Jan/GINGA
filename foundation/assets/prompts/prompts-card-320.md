---
id: prompts-card-check_villain_logic-320
asset_type: prompt_card
title: 反派智商检测器
topic: [通用]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/320.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: check_villain_logic
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 320. 写作工具：反派智商检测器 (Villain Logic Check)

## 提示词内容

```json
{
  "task": "check_villain_logic",
  "villain_plan": "Capture MC and explain the plan before killing him",
  "flaw": "Why not just kill him?",
  "fix": "Villain needs MC's blood to open the door / Villain is livestreaming the execution",
  "rating": "Low IQ (Generic) -> High IQ (Machiavellian)",
  "suggestion": "Make the villain attack MC's loved ones instead"
}
```

## 使用场景
通用/大纲/润色。避免反派降智，提升剧情逻辑。

## 最佳实践要点
1.  **合理化**：为反派的“废话”或“拖延”找到合理的理由。
2.  **危机感**：高智商反派带来的压迫感更强。

## 示例输入
检查反派“把主角关进牢房而不是直接杀掉”的逻辑漏洞。
