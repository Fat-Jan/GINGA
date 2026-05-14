---
id: prompts-card-write-unreliable_narrator
asset_type: prompt_card
title: 不可靠叙述者
topic: [悬疑, 惊悚]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/123.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_unreliable_narrator
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 123. 不可靠叙述者 (Unreliable Narrator)

## 提示词内容

```json
{
  "task": "write_unreliable_narrator",
  "narrator_type": "Insane / Liar / Child / Memory Loss",
  "scene": "A murder scene / A romantic encounter",
  "reality": "The narrator actually committed the crime",
  "narrative_distortion": "Omitting blood / Describing violence as art / Hallucinating a companion",
  "clue_for_reader": "Inconsistencies in time or physical details"
}
```

## 使用场景
悬疑/惊悚文。通过扭曲的叙述制造反转。

## 最佳实践要点
1.  **违和感**：在叙述中埋下细微的矛盾（Clue），让敏锐的读者察觉不对劲。
2.  **揭秘时刻**：最后揭示真相时，要能解释之前所有的扭曲。

## 示例输入
```json
{
  "narrator_type": "失忆的凶手",
  "scene": "他描述自己发现尸体",
  "reality": "尸体是他前一晚亲手藏下",
  "clue_for_reader": "叙述中的手套颜色前后矛盾"
}
```
