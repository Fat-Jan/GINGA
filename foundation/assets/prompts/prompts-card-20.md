---
id: prompts-card-create_toxic_relatives-20
asset_type: prompt_card
title: 极品亲戚生成器 (打脸专用)
topic: [种田文, 年代文]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/20.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_toxic_relatives
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 20. 极品亲戚生成器 (打脸专用)

## 提示词内容

```json
{
  "task": "create_toxic_relatives",
  "relationship": "Aunt / Mother-in-law",
  "archetype": "The Greedy Leech / The Moral Kidnapper",
  "behavior_pattern": [
    "Stealing food/money",
    "Gaslighting the MC",
    "Publicly shaming the MC"
  ],
  "weakness": "Fear of authority / Reputation in village",
  "slap_face_scenario": "How the MC exposes them in public"
}
```

## 使用场景
种田文/年代文。设计制造冲突的反派角色（极品亲戚）。

## 最佳实践要点
1.  **原型设计 (Archetype)**：使用经典的“吸血鬼”或“道德绑架”原型，快速建立读者仇恨。
2.  **爽点闭环**：同时生成 `weakness` 和 `slap_face_scenario`，确保冲突有解且解气。

## 示例输入
- 关系：贪心大伯母
- 行为：偷拿粮票、当众哭穷、逼主角让出工作名额
- 弱点：怕村支书查账
