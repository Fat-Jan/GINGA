---
id: prompts-card-create_dying_message-216
asset_type: prompt_card
title: 设计死前留言谜题
topic: [悬疑, 推理]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/216.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: scene_card
task_verb: create
task_full: create_dying_message
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 216. 死前留言 (Dying Message) 谜题

## 提示词内容

```json
{
  "task": "create_dying_message",
  "victim": "Professor / Detective",
  "clue": "Wrote 'J-O-N' in blood / Pointed at a clock",
  "interpretation": [
    "Surface: The name 'Jon'",
    "True meaning: Periodic table elements / Clock hands pointing to a location"
  ],
  "solution": "The killer is NOT Jon, but someone associated with the decoded meaning."
}
```

## 使用场景
悬疑/推理文。设计经典的死前讯息。

## 最佳实践要点
1.  **不完整性**：受害者通常来不及写完，导致信息残缺或变形。
2.  **双重解答**：表面意思往往是陷阱，深层意思才指向真凶。

## 示例输入
```json
{
  "victim": "研究古钟的教授",
  "clue": "临死前把钟针拨到 4:12",
  "solution": "4 和 12 对应书架编号，藏着真凶交易记录"
}
```
