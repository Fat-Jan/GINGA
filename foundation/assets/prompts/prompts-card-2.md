---
id: prompts-card-lock-style_and_restrictions
asset_type: prompt_card
title: 文风与禁区锁
topic: [通用]
stage: auxiliary
quality_grade: A
source_path: _原料/提示词库参考/prompts/2.md
last_updated: 2026-05-13
card_intent: persona_setup
card_kind: style_lock_card
task_verb: lock
task_full: lock_style_and_restrictions
granularity: utility
output_kind: style_lock
dedup_verdict: retain
dedup_against: []
---

# 2. 文风与禁区锁

## 提示词内容

```json
{
  "style_lock": {
    "narrative_voice": "Third-person limited (focus on MC)",
    "sentence_structure": "Short, Punchy, Action-oriented",
    "vocabulary_level": "Accessible (Grade 6-8), High Imagery",
    "pacing": "Fast (Cut unnecessary transitions)",
    "prohibited_content": [
      "Political Sensitivity",
      "Explicit Sexual Content",
      "Excessive Gore",
      "Depressing/Tragic Endings (unless specified)",
      "Slow-burn Romance (in non-romance genres)"
    ]
  }
}
```

## 使用场景
在正式开始写作正文或大纲前使用。此提示词用于锁定番茄小说特有的“小白文”风格（快节奏、短句、强画面感）并设置内容红线。

## 最佳实践要点
1.  **负向约束 (Negative Constraints)**：明确列出 `prohibited_content`，防止 AI 生成违规内容，减少后期修改成本。
2.  **风格具体化**：将“文风”拆解为叙事视角、句式结构、词汇等级，使 AI 更易执行。
3.  **节奏控制**：明确要求“Fast pacing”，符合移动端碎片化阅读习惯。

## 示例输入
```json
{
  "narrative_voice": "第三人称限知，贴近男主",
  "pacing": "快节奏，短句推进",
  "prohibited_content": ["露骨色情", "过度血腥", "悲剧结局"]
}
```
