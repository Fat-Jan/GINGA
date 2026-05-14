---
id: prompts-card-generate-fantasy-geography-fantasy-geography-climate
asset_type: prompt_card
title: 奇幻地理与气候生成
topic: [奇幻, 玄幻]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/101.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_fantasy_geography
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 101. 奇幻地理与气候生成

## 提示词内容

```json
{
  "task": "generate_fantasy_geography",
  "biome": "Floating Islands / Underground Ocean / Crystal Forest",
  "climate_anomaly": "Rains fire / Perpetual twilight / Gravity fluctuations",
  "resources": ["Mana Crystals", "Dragon Bones", "Singing Stones"],
  "hazards": ["Sky Sharks", "Acid Mist", "Time Distortion Zones"],
  "civilization_adaptation": "How locals build homes and farm in this environment"
}
```

## 使用场景
奇幻/玄幻文。构建独特、令人印象深刻的地理环境。

## 最佳实践要点
1.  **生存逻辑**：文明必须适应环境（如浮空岛居民使用滑翔翼），增加真实感。
2.  **视觉奇观**：强调反常识的自然现象（如倒流的瀑布），提升史诗感。

## 示例输入
```json
{
  "biome": "倒悬雪山群",
  "climate_anomaly": "雪向天空飘落，重力每天反转一次",
  "civilization_adaptation": "居民用双面房屋和锚索农田生活"
}
```
