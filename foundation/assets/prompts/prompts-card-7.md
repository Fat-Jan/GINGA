---
id: prompts-card-design_golden_finger-7
asset_type: prompt_card
title: 金手指 (Cheat) 深度定制
topic: [系统]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/7.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_golden_finger
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 7. 金手指 (Cheat) 深度定制

## 提示词内容

```json
{
  "task": "design_golden_finger",
  "type": "{{type}}",
  "protagonist_role": "{{role}}",
  "requirements": {
    "visual_feedback": "How the user sees progress (Panel, Aura, etc.)",
    "constraints": "Limitations to prevent boredom (e.g., Cooldown, Cost)",
    "interaction": "How the MC interacts with it (Voice, Touch, Thought)",
    "evolution": "Potential future upgrades"
  }
}
```

## 使用场景
设定主角核心能力时使用。设计既强大又有爽感反馈的金手指。

## 最佳实践要点
1.  **交互设计**：关注 `visual_feedback` 和 `interaction`，增强读者的代入感（UI/UX 思维）。
2.  **平衡性控制**：通过 `constraints` 防止主角开局即无敌，保持剧情张力。

## 示例输入
将 `{{type}}` 替换为“深蓝加点系统”，`{{role}}` 替换为“落魄武馆馆主”。
