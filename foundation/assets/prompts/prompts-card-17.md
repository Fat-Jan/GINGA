---
id: prompts-card-generate-weird_rules
asset_type: prompt_card
title: 怪谈守则生成器 (红蓝字)
topic: [怪谈, 悬疑, 恐怖]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/17.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_weird_rules
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 17. 怪谈守则生成器 (红蓝字)

## 提示词内容

```json
{
  "task": "generate_weird_rules",
  "scenario": "{{scenario}}",
  "pollution_level": "High (Cognitive Hazard)",
  "output_structure": {
    "title": "Rule Sheet Title (e.g., Notice to Tourists)",
    "rules": [
      {
        "id": 1,
        "text": "Normal rule (Safety)",
        "color": "Black"
      },
      {
        "id": 2,
        "text": "Subtle trap (Seems safe but deadly)",
        "color": "Red (Cognitive Corruption)"
      },
      {
        "id": 3,
        "text": "Contradictory rule (Logic puzzle)",
        "color": "Blue (Hidden Truth)"
      }
    ],
    "note": "Scrawled warning at the bottom"
  }
}
```

## 使用场景
规则怪谈流派创作。生成具有逻辑陷阱和认知污染的规则。

## 最佳实践要点
1.  **颜色编码**：利用“红蓝字”机制构建逻辑矛盾，增加解谜趣味。
2.  **认知危害**：要求 AI 生成带有暗示性、令人不安的文本，强化恐怖感。

## 示例输入
将 `{{scenario}}` 替换为“妈妈留下的纸条”。
