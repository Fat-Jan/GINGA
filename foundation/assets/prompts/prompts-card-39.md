---
id: prompts-card-create_protagonist-protagonist-bgm-style
asset_type: prompt_card
title: 番茄风主角人设卡
topic: [玄幻, 都市, 校园, 末世, 系统]
stage: setting
quality_grade: A
source_path: _原料/提示词库参考/prompts/39.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_protagonist
granularity: character
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 39. 番茄风主角人设卡

## 提示词内容

```json
{
  "task": "create_protagonist",
  "gender": "{{gender}}",
  "archetype": "{{archetype}}",
  "output_structure": {
    "name": "姓名",
    "tagline": "一句话人设 (如: 表面废柴实则无敌的...)",
    "core_desire": "核心欲望 (推动剧情的动力)",
    "golden_finger": "金手指简述",
    "personality_traits": ["性格关键词1", "性格关键词2"],
    "flaw": "致命弱点/反差萌点",
    "backstory_hook": "前史悬念 (身世之谜等)"
  }
}
```

## 使用场景
人设构建。打造有标签感、易记住的主角。

## 最佳实践要点
1.  **标签化 (Tagline)**：用一句话总结人设，方便读者记忆（如“表面...实则...”）。
2.  **悬念植入**：通过 `backstory_hook` 埋下长线伏笔。

## 示例输入
将 `{{gender}}` 替换为“男”，`{{archetype}}` 替换为“苟道流大师”。
