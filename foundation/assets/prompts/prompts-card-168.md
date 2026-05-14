---
id: prompts-card-design_interactive_choices-168
asset_type: prompt_card
title: 互动式小说分支选项设计
topic: [通用]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/168.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_interactive_choices
granularity: scene
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 168. 互动式小说分支选项设计

## 提示词内容

```json
{
  "task": "design_interactive_choices",
  "scene": "The villain offers a deal",
  "choices": [
    {
      "option": "A: Accept the deal",
      "consequence": "Gain wealth, lose ally",
      "flag": "Bad_End_Route"
    },
    {
      "option": "B: Refuse and fight",
      "consequence": "Injury, gain reputation",
      "flag": "Hero_Route"
    },
    {
      "option": "C: Feign acceptance (Requires INT > 50)",
      "consequence": "Learn secret, betray later",
      "flag": "True_End_Route"
    }
  ]
}
```

## 使用场景
互动小说/游戏剧本。设计有意义的剧情分支。

## 最佳实践要点
1.  **属性门槛**：设置隐藏选项（需高智力/特定道具），奖励探索型读者。
2.  **蝴蝶效应**：现在的选择必须在后续剧情中产生实质性影响（不仅仅是几句对话不同）。

## 示例输入
- 当前节点：主角偷听到王子与刺客交易
- 分支数量：3 个
- 选项倾向：揭发、跟踪、假装没听见
