---
id: prompts-card-simulate_livestream_chat-67
asset_type: prompt_card
title: 直播间弹幕刷屏模拟
topic: [都市, 系统]
stage: drafting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/67.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: scene_card
task_verb: simulate
task_full: simulate_livestream_chat
granularity: scene
output_kind: prose
dedup_verdict: retain
dedup_against: []
---

# 67. 直播间弹幕刷屏模拟

## 提示词内容

```json
{
  "task": "simulate_livestream_chat",
  "streamer_action": "{{action}}",
  "viewer_count": "100k -> 1M",
  "chat_styles": [
    "Simps: 'Husband/Wife!', 'Take my money!'",
    "Trolls: 'Fake', 'Scripted'",
    "Shocked: '??', 'OMG'",
    "Donations: 'User X sent 10 Rockets'"
  ],
  "output_format": "Waterfall of chat messages with timestamps"
}
```

## 使用场景
直播流/网红文。模拟直播间的热闹氛围。

## 最佳实践要点
1.  **梗密度**：大量使用网络热梗和颜文字。
2.  **打脸互动**：黑粉质疑 -> 主角打脸 -> 黑粉转粉/消失。

## 示例输入
将 `{{action}}` 替换为“徒手抓蛇”。
