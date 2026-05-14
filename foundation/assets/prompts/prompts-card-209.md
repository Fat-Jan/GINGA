---
id: prompts-card-design_gacha_system-209
asset_type: prompt_card
title: 抽卡系统保底与概率设计
topic: [系统, 网游]
stage: setting
quality_grade: B
source_path: _原料/提示词库参考/prompts/209.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_gacha_system
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 209. 抽卡系统保底与概率设计

## 提示词内容

```json
{
  "task": "design_gacha_system",
  "currency": "Spirit Stones / Diamonds",
  "rates": "SSR (1%) / SR (10%) / R (89%)",
  "pity_system": "Guaranteed SSR after 90 pulls (50/50 chance for featured item)",
  "mc_luck": "E-rank luck (always hits pity) OR EX-rank luck (10 SSRs in one pull)",
  "animation": "Gold light means legendary!"
}
```

## 使用场景
系统/网游文。模拟令人上瘾的抽卡机制。

## 最佳实践要点
1.  **情绪调动**：描写抽卡时的光效、音效和心跳加速的感觉。
2.  **非酋/欧皇**：利用极端运气（极好或极坏）制造喜剧效果或爽点。

## 示例输入
- 货币：灵石。
- 概率：SSR 1%，90 抽保底；主角运气极差，总在第 90 抽出货。
