---
id: prompts-card-create_mythology-117
asset_type: prompt_card
title: 远古神话/传说生成器
topic: [玄幻, 奇幻, 神话]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/117.md
last_updated: 2026-05-13
card_intent: prototype_creation
card_kind: setup_card
task_verb: create
task_full: create_mythology
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 117. 远古神话/传说生成器

## 提示词内容

```json
{
  "task": "create_mythology",
  "culture_style": "Norse / Greek / Chinese / Lovecraftian",
  "creation_myth": "The world was formed from the corpse of a giant",
  "pantheon": [
    {"god": "Sun God", "domain": "Justice", "symbol": "Golden Scales"},
    {"god": "Trickster", "domain": "Chaos", "symbol": "Broken Mask"}
  ],
  "prophecy": "The Trickster will return when the three moons align"
}
```

## 使用场景
世界观背景。为故事增加历史厚重感。

## 最佳实践要点
1.  **隐喻**：神话往往是现实剧情的映射或预言（伏笔）。
2.  **风格化**：根据世界观类型选择合适的神话原型（如修仙选盘古女娲类）。

## 示例输入
```json
{
  "culture_style": "中式上古神话",
  "creation_myth": "天地由一枚破裂的黑玉蛋分开",
  "prophecy": "三月同天时，失名之神会归来索取真名"
}
```
