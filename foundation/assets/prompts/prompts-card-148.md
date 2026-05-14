---
id: prompts-card-describe_dynamic_weather-148
asset_type: prompt_card
title: 动态环境描写 (天气/光影)
topic: [通用]
stage: drafting
quality_grade: B
source_path: _原料/提示词库参考/prompts/148.md
last_updated: 2026-05-13
card_intent: scene_description
card_kind: scene_card
task_verb: describe
task_full: describe_dynamic_weather
granularity: scene
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 148. 动态环境描写 (天气/光影)

## 提示词内容

```json
{
  "task": "describe_dynamic_weather",
  "base_weather": "Storm",
  "progression": [
    "Distant thunder -> First heavy drops -> Downpour -> Eye of the storm",
    "Golden hour sunlight -> Twilight -> Pitch black night"
  ],
  "mood_link": "The storm intensifies as the argument gets heated."
}
```

## 使用场景
环境烘托。让环境随剧情发展而变化。

## 最佳实践要点
1.  **情景交融**：环境变化应与人物情绪或剧情节奏同步（如高潮时雷电交加）。
2.  **流动感**：描写过程而非静止状态（如光影的移动）。

## 示例输入
- 天气：暴雨转台风眼。
- 情绪联动：争吵越激烈，雷声越近；沉默时只剩积水滴答。
