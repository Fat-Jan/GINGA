---
id: prompts-card-design_linguistic_puzzle-166
asset_type: prompt_card
title: 设计语言学/解密游戏谜题
topic: [悬疑, 探险, 科幻]
stage: auxiliary
quality_grade: B+
source_path: _原料/提示词库参考/prompts/166.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: scene_card
task_verb: design
task_full: design_linguistic_puzzle
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 166. 语言学/解密游戏设计

## 提示词内容

```json
{
  "task": "design_linguistic_puzzle",
  "language": "Ancient Runes / Alien Signal",
  "clues": [
    {"symbol": "△", "meaning": "Fire/Up"},
    {"symbol": "▽", "meaning": "Water/Down"},
    {"symbol": "O", "meaning": "World/Life"}
  ],
  "puzzle": "Translate: △ + O + ▽",
  "solution": "Cycle of Life (Fire creates, Water destroys)",
  "mc_insight": "Noticing the pattern based on star constellations"
}
```

## 使用场景
悬疑/探险/科幻。设计基于符号和逻辑的谜题。

## 最佳实践要点
1.  **象形逻辑**：符号的含义应具有直观的联想性，方便读者参与解谜。
2.  **文化背景**：谜题的答案往往隐藏在该文明的历史或神话中。

## 示例输入
- 谜题场景：古墓石门铭文
- 语言规则：每个元音代表方向，每个辅音代表步数
- 目标：让玩家推导出开门顺序
