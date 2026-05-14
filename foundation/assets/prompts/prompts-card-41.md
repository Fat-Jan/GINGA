---
id: prompts-card-outline_golden_three_chapters-41
asset_type: prompt_card
title: 黄金三章细纲生成 (番茄版)
topic: [通用]
stage: framework
quality_grade: A-
source_path: _原料/提示词库参考/prompts/41.md
last_updated: 2026-05-13
card_intent: outline_planning
card_kind: scene_card
task_verb: outline
task_full: outline_golden_three_chapters
granularity: methodology
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 41. 黄金三章细纲生成 (番茄版)

## 提示词内容

```json
{
  "task": "outline_golden_three_chapters",
  "book_info": {
    "title": "{{title}}",
    "genre": "{{genre}}",
    "hook": "{{hook}}"
  },
  "chapter_1": {
    "goal": "确立主角现状 + 遭遇极致压抑/危机 + 金手指到账",
    "cliffhanger": "结尾留钩子 (金手指初显灵/危机迫在眉睫)"
  },
  "chapter_2": {
    "goal": "金手指探索/验证 + 第一次小规模反击/震惊 + 铺垫大冲突",
    "cliffhanger": "矛盾升级 (反派骑脸输出)"
  },
  "chapter_3": {
    "goal": "高潮爆发 (彻底打脸/解决危机) + 收获奖励 + 开启新地图/目标",
    "cliffhanger": "新的悬念/长线目标引入"
  },
  "output_requirement": "详细到每个场景的动作和情绪变化"
}
```

## 使用场景
开篇大纲。严格遵循番茄“压抑-金手指-高潮”的三章定律。

## 最佳实践要点
1.  **情绪曲线**：第一章压抑，第二章期待，第三章爆发，情绪节奏极为紧凑。
2.  **细节要求**：要求“详细到每个场景的动作和情绪变化”，指导性更强。

## 示例输入
填入书名、流派和核心梗。
