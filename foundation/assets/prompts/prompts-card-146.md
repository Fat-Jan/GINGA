---
id: prompts-card-check_foreshadowing-146
asset_type: prompt_card
title: 伏笔回收与反转设计检查表
topic: [悬疑]
stage: analysis
quality_grade: B
source_path: _原料/提示词库参考/prompts/146.md
last_updated: 2026-05-13
card_intent: checker_diagnostic
card_kind: checker_card
task_verb: check
task_full: check_foreshadowing
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 146. 伏笔回收与反转设计检查表

## 提示词内容

```json
{
  "task": "check_foreshadowing",
  "plot_point": "The butler is the killer",
  "setup_scenes": [
    "Chapter 3: Butler mentioned he hates the victim",
    "Chapter 10: Butler was absent during the murder time"
  ],
  "payoff_scene": "Chapter 50: MC reveals the evidence",
  "instruction": "Ensure the clues are subtle enough to be missed but obvious in hindsight."
}
```

## 使用场景
悬疑/大纲优化。检查伏笔是否埋设得当。

## 最佳实践要点
1.  **草蛇灰线**：伏笔应伪装成无关紧要的背景描述或闲聊。
2.  **回溯感**：真相大白时，读者应能瞬间联想起之前的线索（恍然大悟）。

## 示例输入
- 伏笔：第 5 章管家避开银器。
- 回收：第 80 章揭示管家是狼人，并用早期细节完成反转。
