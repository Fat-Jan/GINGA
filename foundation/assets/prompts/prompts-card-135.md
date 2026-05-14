---
id: prompts-card-simulate_trending_topics-135
asset_type: prompt_card
title: 社交媒体热搜榜单模拟
topic: [都市]
stage: setting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/135.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: setup_card
task_verb: simulate
task_full: simulate_trending_topics
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 135. 社交媒体热搜榜单模拟

## 提示词内容

```json
{
  "task": "simulate_trending_topics",
  "event": "MC's scandal / MC's heroic act",
  "platform": "Weibo / Twitter / FutureNet",
  "trends": [
    {"rank": 1, "tag": "#MC_Is_Fake#", "sentiment": "Negative"},
    {"rank": 2, "tag": "#WhoIsTheHero#", "sentiment": "Curious"},
    {"rank": 5, "tag": "#CatVideo#", "sentiment": "Neutral (Noise)"}
  ],
  "netizen_comments": "Mix of blind hate, logical analysis, and memes."
}
```

## 使用场景
娱乐圈/都市文。侧面描写舆论风向。

## 最佳实践要点
1.  **真实感**：热搜榜单中应混杂无关话题（如猫视频），模拟真实网络环境。
2.  **情绪极化**：网民评论通常是非黑即白的，情绪化严重。

## 示例输入
- 平台：修真界灵网热搜
- 事件：新晋剑修一剑斩断试炼塔
- 榜单口吻：半吃瓜半阴谋论
