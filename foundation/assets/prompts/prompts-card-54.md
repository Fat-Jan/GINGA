---
id: prompts-card-build_investigation_logic_chain-54
asset_type: prompt_card
title: 刑侦案件线索逻辑链
topic: [刑侦]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/54.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: build
task_full: build_investigation_logic_chain
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 54. 刑侦案件线索逻辑链

## 提示词内容

```json
{
  "task": "build_investigation_logic_chain",
  "crime": "Serial Killing",
  "red_herrings": ["Stalker Ex-boyfriend", "Suspicious Janitor"],
  "evidence_chain": [
    "Discovery of Body -> Trace Evidence (Soil/Fiber)",
    "Trace Evidence -> Specific Location (Abandoned Factory)",
    "Location -> Witness/CCTV -> Suspect Vehicle",
    "Vehicle -> Suspect ID -> Arrest"
  ],
  "plot_twist": "The suspect is a copycat; real killer is still watching"
}
```

## 使用场景
刑侦/警察文。构建案件侦破的流程和逻辑。

## 最佳实践要点
1.  **干扰项 (Red Herrings)**：设计合理的干扰线索，增加破案难度。
2.  **逻辑闭环**：`evidence_chain` 必须环环相扣，经得起推敲。

## 示例输入
```json
{
  "crime": "雨夜连环失踪案",
  "red_herrings": ["前男友", "夜班保安"],
  "evidence_chain": ["泥点", "废弃花市", "冷链车牌", "嫌疑人仓库"],
  "plot_twist": "被捕者只是模仿犯"
}
```
