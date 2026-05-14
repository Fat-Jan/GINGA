---
id: prompts-card-generate_mutated_creatures-254
asset_type: prompt_card
title: 生成灵气复苏背景下的动植物变异图鉴
topic: [玄幻, 末世]
stage: setting
quality_grade: A
source_path: 原料/提示词库参考/prompts/254.md
last_updated: 2026-05-13
card_intent: generator
card_kind: setup_card
task_verb: generate
task_full: generate_mutated_creatures
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 254. 灵气复苏：动植物变异图鉴

## 提示词内容

```json
{
  "task": "generate_mutated_creatures",
  "base": "Willow Tree / Stray Cat / Ant",
  "mutation": [
    "Willow: Iron bark, branches act like spears",
    "Cat: Two tails, sonic scream",
    "Ant: Size of a dog, acid spit"
  ],
  "threat_level": "Low (Individual) -> High (Swarm)",
  "drop": "Spirit Core / Mutated Material"
}
```

## 使用场景
灵气复苏/末世文。设计初期的小怪和精英怪。

## 最佳实践要点
1.  **熟悉又陌生**：基于常见生物进行变异，增加代入感和恐怖感。
2.  **资源化**：变异生物不仅是威胁，也是资源（材料、晶核），驱动主角狩猎。

## 示例输入
```json
{
  "base": "城市银杏树、流浪犬、白蚁群",
  "threat_level": "低阶个体到中阶群体",
  "drop": "木灵髓、变异犬牙、蚁酸晶囊"
}
```
