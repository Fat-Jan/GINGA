---
id: prompts-card-write_group_dialogue-150
asset_type: prompt_card
title: 多人对话场面调度 (谁在说话)
topic: [群像, 对话]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/150.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_group_dialogue
granularity: scene
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 150. 多人对话场面调度 (谁在说话)

## 提示词内容

```json
{
  "task": "write_group_dialogue",
  "participants": ["A (Leader)", "B (Joker)", "C (Traitor)", "D (Silent type)"],
  "topic": "Planning a heist",
  "dynamics": [
    "A gives orders",
    "B interrupts with jokes",
    "C agrees too quickly (suspicious)",
    "D observes and notices C's sweat"
  ],
  "instruction": "Ensure distinct voices and track movement/actions during speech."
}
```

## 使用场景
群像/会议情节。处理多人对话的混乱感。

## 最佳实践要点
1.  **动作伴随**：说话时伴随动作（喝水、敲桌子），既标示身份又体现心理。
2.  **沉默的声音**：关注不说话的人在做什么（观察、紧张），往往更有戏。

## 示例输入
- 人物：队长、黑客、雇佣兵、被救人质
- 场景：电梯断电后四人挤在狭窄轿厢
- 冲突：人质认出雇佣兵是通缉犯
