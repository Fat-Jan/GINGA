---
id: prompts-card-analyze_performance_data-33
asset_type: prompt_card
title: 首秀数据分析与剧情微调
topic: [通用]
stage: business
quality_grade: B
source_path: _原料/提示词库参考/prompts/33.md
last_updated: 2026-05-13
card_intent: simulation
card_kind: scene_card
task_verb: analyze
task_full: analyze_performance_data
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 33. 首秀数据分析与剧情微调

## 提示词内容

```json
{
  "task": "analyze_performance_data",
  "metrics": {
    "ctr": "{{ctr}}",
    "retention_100k": "{{retention}}",
    "comments": "{{comment_sentiment}}"
  },
  "benchmarks": {"ctr": "8%", "retention": "15%"},
  "diagnosis": [
    "If CTR < 8% -> Change Title/Cover/Intro",
    "If Retention < 15% -> Check Golden 3 pacing",
    "If Comments = 'Boring' -> Speed up pacing",
    "If Comments = 'Confusing' -> Clarify setting"
  ],
  "action_plan": "Specific changes for next 10 chapters"
}
```

## 使用场景
运营复盘。根据真实数据调整后续剧情。

## 最佳实践要点
1.  **数据驱动**：建立“数据-问题-对策”的映射关系，理性调整。
2.  **动态优化**：根据反馈及时调整节奏（加速/解释），防止数据进一步下滑。

## 示例输入
填入真实的 CTR、留存率和评论风向。
