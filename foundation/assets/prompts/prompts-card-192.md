---
id: prompts-card-generate-light_novel_title
asset_type: prompt_card
title: 日式轻小说标题生成器
topic: [轻小说]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/192.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_light_novel_title
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 192. 日式轻小说标题生成器

## 提示词内容

```json
{
  "task": "generate_light_novel_title",
  "plot": "MC is reincarnated as a vending machine in a dungeon",
  "style": "Long, descriptive, absurd",
  "examples": [
    "That Time I Got Reincarnated as a Slime",
    "Is It Wrong to Try to Pick Up Girls in a Dungeon?"
  ],
  "output": "Reborn as a Vending Machine, I Now Wander the Dungeon Selling Potions!"
}
```

## 使用场景
轻小说/二次元。生成超长、概括性强的标题。

## 最佳实践要点
1.  **一句话简介**：标题本身就是简介，包含核心爽点和设定。
2.  **荒谬感**：设定越离谱（如转生成自动售货机），越吸引点击。

## 示例输入
将 `plot` 替换为“主角转生成了一把魔剑”。
