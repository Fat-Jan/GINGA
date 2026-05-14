---
id: prompts-card-generate_feudal_ranks-152
asset_type: prompt_card
title: 生成历史文官制与爵位体系
topic: [历史, 权谋, 架空]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/152.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: generate_feudal_ranks
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 152. 历史文官制与爵位生成

## 提示词内容

```json
{
  "task": "generate_feudal_ranks",
  "culture": "Chinese Dynasty / Medieval Europe",
  "ranks": [
    {"title": "Duke / Gong", "power": "Owns province", "duty": "Protect border"},
    {"title": "Marquis / Hou", "power": "Owns city", "duty": "Pay taxes"},
    {"title": "Knight / Shi", "power": "None", "duty": "Serve in army"}
  ],
  "mc_promotion_path": "From peasant to General via meritocracy"
}
```

## 使用场景
历史/架空权谋。构建严谨的等级晋升体系。

## 最佳实践要点
1.  **权责对应**：爵位不仅是荣誉，更意味着具体的权力和义务（如兵役、税收）。
2.  **晋升逻辑**：明确主角向上爬的路径（军功、科举、裙带）。

## 示例输入
- 朝代气质：架空北境王朝
- 体系重点：文官九品、军功爵、外戚封号
- 冲突：寒门状元被破格授爵引发争议
