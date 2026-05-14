---
id: prompts-card-generate_wasteland_trade_list-99
asset_type: prompt_card
title: 生成废土势力交易清单
topic: [末世, 废土]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/99.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_wasteland_trade_list
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 99. 末世/废土势力交易清单

## 提示词内容

```json
{
  "task": "generate_wasteland_trade_list",
  "settlement": "Raider Camp / Vault / Mutant Tribe",
  "currency": "Bottle Caps / Bullets / Water",
  "goods": [
    {"item": "RadAway", "price": "High", "stock": "Low"},
    {"item": "Old Comic Book", "price": "Low (Useless)", "stock": "High"},
    {"item": "Pre-war Tech", "price": "Very High", "stock": "Rare"}
  ],
  "mc_strategy": "Buying low, selling high using knowledge"
}
```

## 使用场景
末世/废土文。设计以物易物的经济系统。

## 最佳实践要点
1.  **稀缺性**：在末世，干净的水和药比黄金贵，漫画书可能一文不值。
2.  **倒爷爽点**：主角利用两地差价或知识优势（知道旧电池有用）暴富。

## 示例输入
```json
{
  "settlement": "地铁站幸存者集市",
  "currency": "净水券和子弹",
  "goods": ["抗辐射药", "旧电池", "罐头肉"],
  "mc_strategy": "低价收旧电池，转卖给缺电哨站"
}
```
