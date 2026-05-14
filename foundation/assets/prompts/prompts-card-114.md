---
id: prompts-card-adapt-audio_drama
asset_type: prompt_card
title: 有声书/广播剧脚本改编
topic: [auxiliary]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/114.md
last_updated: 2026-05-13
card_intent: editing_transformation
card_kind: scene_card
task_verb: adapt
task_full: adapt_to_audio_drama
granularity: utility
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 114. 有声书/广播剧脚本改编

## 提示词内容

```json
{
  "task": "adapt_to_audio_drama",
  "scene": "{{novel_excerpt}}",
  "format": "Audio Script",
  "elements": {
    "SFX": "[Sound of footsteps on gravel], [Thunder rolling]",
    "BGM": "Tense, violin crescendo",
    "Dialogue": "Character A (Whispering): ...",
    "Narration": "Keep minimal, only for context not shown by sound"
  }
}
```

## 使用场景
IP改编/有声制作。将小说转化为适合听觉的脚本。

## 最佳实践要点
1.  **音效叙事**：用声音（脚步声、雷声）代替环境描写。
2.  **去旁白化**：尽量通过对话和音效传达信息，减少大段旁白。

## 示例输入
填入一段小说原文。
