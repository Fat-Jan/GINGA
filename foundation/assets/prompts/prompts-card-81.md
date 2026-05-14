---
id: prompts-card-simulate_war_strategy-81
asset_type: prompt_card
title: 大规模战争战术推演
topic: [争霸, 战争]
stage: framework
quality_grade: B+
source_path: _原料/提示词库参考/prompts/81.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: scene_card
task_verb: simulate
task_full: simulate_war_strategy
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 81. 大规模战争战术推演

## 提示词内容

```json
{
  "task": "simulate_war_strategy",
  "terrain": "Mountain Pass / Open Plain / Naval",
  "factions": [
    {"name": "Army A (MC)", "strength": "10k elites", "advantage": "Magic Artillery"},
    {"name": "Army B (Enemy)", "strength": "100k mob", "advantage": "Numbers"}
  ],
  "tactic": "Ambush / Pincer Movement / Decoy",
  "plot_twist": "Enemy general is a traitor / Sudden weather change",
  "outcome": "Detailed battle flow leading to MC's victory"
}
```

## 使用场景
争霸文/战争文。推演宏大的战争场面。

## 最佳实践要点
1.  **以少胜多**：爽文战争的核心在于主角利用奇谋或黑科技实现逆转。
2.  **地形要素**：将 `terrain` 作为战术的关键变量，增加真实感。

## 示例输入
- 地形：狭长山谷，两侧高地可布置弩车。
- 兵力：主角三千精锐对敌军两万轻骑。
- 战术：佯败诱敌入谷，夜雨后点燃油沟切断退路。
