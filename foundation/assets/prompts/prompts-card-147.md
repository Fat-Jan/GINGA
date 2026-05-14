---
id: prompts-card-generate-cliffhanger-147
asset_type: prompt_card
title: 悬念 (Cliffhanger) 设计生成器
topic: [通用]
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/147.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_cliffhanger
granularity: scene
output_kind: dialogue
dedup_verdict: retain
dedup_against: []
---

# 147. 悬念 (Cliffhanger) 设计生成器

## 提示词内容

```json
{
  "task": "generate_cliffhanger",
  "scene_context": "MC opens the secret door",
  "types": [
    {"type": "Discovery", "content": "The room is empty... except for a mirror reflecting someone else."},
    {"type": "Danger", "content": "A gun is pressed against MC's head."},
    {"type": "Revelation", "content": "The villain turns around... it's MC's father."}
  ],
  "instruction": "Choose the most impactful ending for the chapter."
}
```

## 使用场景
章节结尾。设计钩子，强迫读者点击下一章。

## 最佳实践要点
1.  **戛然而止**：在动作或对话的最高潮处切断，不给缓冲。
2.  **信息差**：抛出一个新问题，而不是解决旧问题。

## 示例输入
- 当前场景：主角打开父亲留下的保险箱
- 已知秘密：里面应该有遗嘱
- 结尾悬念：保险箱里传出仍在跳动的心音
