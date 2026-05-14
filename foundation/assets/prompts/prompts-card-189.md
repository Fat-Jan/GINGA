---
id: prompts-card-manage-timeline
asset_type: prompt_card
title: 时间线管理工具
topic: [通用]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/189.md
last_updated: 2026-05-13
card_intent: management_tracking
card_kind: scene_card
task_verb: manage
task_full: manage_timeline
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 189. 时间线管理工具 (Timeline)

## 提示词内容

```json
{
  "task": "manage_timeline",
  "events": [
    {"date": "Year 1", "event": "MC transmigrates"},
    {"date": "Year 3", "event": "War begins (MC must be General by now)"},
    {"date": "Year 10", "event": "Demon King awakens"}
  ],
  "pacing_check": "Is Year 1-3 too slow? Do we need a time skip?",
  "consistency": "Ensure MC's age matches the events."
}
```

## 使用场景
长篇小说/大纲规划。梳理关键节点，防止时间线混乱。

## 最佳实践要点
1.  **倒推法**：根据结局（第10年打魔王）倒推主角每年的成长目标。
2.  **时间跳跃**：合理的“三年后”可以略过枯燥的修炼期，加快节奏。

## 示例输入
- 故事跨度：三代家族复仇
- 关键节点：婚约、谋杀、流放、归来
- 输出要求：标出因果关系与潜在时间矛盾
