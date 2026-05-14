---
id: prompts-card-build_political_factions-51
asset_type: prompt_card
title: 朝堂党争关系网构建
topic: [历史, 架空]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/51.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: build
task_full: build_political_factions
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 51. 朝堂党争关系网构建

## 提示词内容

```json
{
  "task": "build_political_factions",
  "era_style": "Ming/Qing Dynasty / Game of Thrones",
  "central_conflict": "Succession / Reform vs Tradition",
  "factions": [
    {
      "name": "The Royalists / Emperor's Party",
      "leader": "The Emperor / Chief Eunuch",
      "core_interest": "Centralize power",
      "key_members": ["General A", "Scholar B"]
    },
    {
      "name": "The Reformists",
      "leader": "Prime Minister",
      "core_interest": "New policies, weaken aristocracy",
      "weakness": "Lacks military support"
    },
    {
      "name": "The Aristocracy",
      "leader": "Grand Duke",
      "core_interest": "Maintain privileges",
      "hidden_card": "Private army / Foreign alliance"
    }
  ],
  "mc_position": "Caught in between / Double agent"
}
```

## 使用场景
历史/架空权谋文。构建复杂的政治斗争舞台。

## 最佳实践要点
1.  **利益驱动**：明确每个派系的 `core_interest`，这是结盟或背叛的根本原因。
2.  **平衡态势**：设计三方或多方博弈，避免一边倒，增加主角的操作空间。

## 示例输入
```json
{
  "era_style": "架空明代",
  "central_conflict": "新税法改革 vs 勋贵特权",
  "mc_position": "寒门御史，被两派同时拉拢"
}
```
