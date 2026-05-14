---
id: prompts-card-write_auction_scene-25
asset_type: prompt_card
title: 拍卖会捡漏与打脸场景生成
topic: [玄幻, 都市, 爽文]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/25.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_auction_scene
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 25. 拍卖会捡漏与打脸

## 提示词内容

```json
{
  "task": "write_auction_scene",
  "items": ["{{trash_item}} (Secret Treasure)", "{{hot_item}} (Decoy)", "{{finale_item}}"],
  "participants": ["MC (Low key)", "Young Master (Arrogant)", "Mysterious Elder"],
  "conflict": "Bidding War / Provocation",
  "twist": "MC sees true value of trash item via cheat",
  "outcome": "MC wins item cheaply or makes Young Master overpay",
  "reaction": "Crowd mocks MC initially, then shocked later"
}
```

## 使用场景
玄幻/都市爽文。构建经典的拍卖会冲突。

## 最佳实践要点
1.  **欲扬先抑**：先写 crowd mocks，再写 shocked，增强爽感。
2.  **物品设计**：设计明珠蒙尘的 `trash_item`，体现主角的特殊能力。

## 示例输入
将 `{{trash_item}}` 替换为“烧火棍”，`{{hot_item}}` 替换为“延寿丹”。
