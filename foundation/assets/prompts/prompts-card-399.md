---
id: prompts-card-evaluate_ip_potential-399
asset_type: prompt_card
title: IP改编潜力评估 (IP Adaptation Check)
topic: [运营, IP改编, 作者自查]
stage: business
quality_grade: B
source_path: _原料/提示词库参考/prompts/399.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: evaluate
task_full: evaluate_ip_potential
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 399. 写作工具：IP改编潜力评估 (IP Adaptation Check)

## 提示词内容

```json
{
  "task": "evaluate_ip_potential",
  "story_elements": {
    "Visuals": "Are there iconic scenes? (High/Low)",
    "Characters": "Are they marketable/merchandisable?",
    "Plot": "Is it episodic (TV) or linear (Movie)?",
    "Budget": "CGI cost estimation"
  },
  "verdict": "Suitable for Anime / Live Action / Game / Audio Drama",
  "suggestion": "Simplify the magic system to save budget"
}
```

## 使用场景
运营/策划/作者自查。评估作品适合改编成什么形式。

## 最佳实践要点
1.  **视觉化**：文字是否容易转化为画面。
2.  **成本**：太宏大的场面（如星际战争）改编成本极高。

## 示例输入
评估一本“慢热型凡人修仙传”改编成短剧的可行性。
