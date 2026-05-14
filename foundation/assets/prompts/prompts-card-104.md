---
id: prompts-card-design-steam-diesel-punk-gadget
asset_type: prompt_card
title: 设计蒸汽/柴油朋克风格的机械装置
topic: [蒸汽朋克, 诡秘]
stage: setting
quality_grade: A-
source_path: _原料/提示词库参考/prompts/104.md
last_updated: 2026-05-13
card_intent: structural_design
card_kind: setup_card
task_verb: design
task_full: design_steampunk_gadget
granularity: world
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 104. 蒸汽/柴油朋克机械设计

## 提示词内容

```json
{
  "task": "design_steampunk_gadget",
  "item_type": "Weapon / Vehicle / Prosthetic",
  "power_source": "Steam Core / Clockwork / Whale Oil",
  "aesthetic": "Brass, Gears, Hissing pipes, Exposed mechanics",
  "function": {
    "Primary": "Shoot steam-powered spikes",
    "Secondary": "Create smoke screen"
  },
  "flaw": "Overheats easily / Requires manual winding every 10 shots"
}
```

## 使用场景
蒸汽朋克/诡秘流。设计充满复古机械美感的道具。

## 最佳实践要点
1.  **感官描写**：强调齿轮咬合声、蒸汽喷出的嘶嘶声和机油味。
2.  **不完美感**：机械必须有故障率或维护需求，体现技术的原始粗犷。

## 示例输入
```json
{
  "item_type": "义肢左臂",
  "power_source": "微型蒸汽炉",
  "function": {"Primary": "发射链钩", "Secondary": "喷出高温白雾"},
  "flaw": "连续使用会烫伤肩部接口"
}
```
