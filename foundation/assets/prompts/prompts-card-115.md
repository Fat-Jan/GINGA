---
id: prompts-card-write_comic_script-115
asset_type: prompt_card
title: 漫画/条漫分镜脚本描述
topic: [都市, 末世, 系统, 玄幻]
stage: auxiliary
quality_grade: B
source_path: 原料/提示词库参考/prompts/115.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_comic_script
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 115. 漫画/条漫分镜脚本描述

## 提示词内容

```json
{
  "task": "write_comic_script",
  "scene": "{{novel_excerpt}}",
  "format": "Panel-by-Panel Description",
  "panels": [
    {"Panel 1": "Wide shot of the city. Text box: 'Year 2077'."},
    {"Panel 2": "Close up on MC's eyes. Sound FX: *Blink*"},
    {"Panel 3": "Action shot: MC jumps off building. Speed lines."},
    {"Panel 4": "Impact. Dust cloud. Sound FX: *BOOM*"}
  ],
  "pacing": "Fast / Slow / Cinematic"
}
```

## 使用场景
IP改编/漫改。将小说转化为可视化的漫画脚本。

## 最佳实践要点
1.  **镜头语言**：明确景别（全景、特写）和动态线，指导画师构图。
2.  **拟声词**：设计具体的 SFX（Boom, Slash），增强画面冲击力。

## 示例输入
填入一段动作戏。
