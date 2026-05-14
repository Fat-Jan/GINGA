---
id: base-methodology-writing-anti-ai-style
asset_type: methodology
title: 反 AI 味写作修订方法
topic: [通用]
stage: refinement
quality_grade: A
source_path: _原料/基座/方法论/写作/反AI味.md
last_updated: '2026-05-14'
method_family: 写作
rule_type: constraint
normative_strength: hard_rule
targets:
  topics: [通用]
  platforms: [番茄, 七猫, 起点, 晋江, 知乎, 豆瓣阅读]
  stages: [drafting, refinement]
integrates_with:
  - base-checker-aigc-style-detector
  - style_lock
  - chapter_text
input_contract: [chapter_text, 目标平台, 目标文风]
output_contract: [反AI味问题列表, 逐段修订建议, 风格一致性备注]
platform_scope: [番茄, 七猫, 起点, 晋江, 知乎, 豆瓣阅读]
sub_sections:
  hard_rule:
    - 删除填充短语，避免开场白、总结腔和强调性拐杖词。
    - 打破公式结构，避免二元对比、机械三段式和修辞性设置。
    - 用动作、感官和选择展示情绪，少用抽象情绪判词。
    - 句长、段长、段尾节奏必须变化，避免同一种收束方式连续出现。
    - 保留角色视角内的信息，不用作者旁白替角色解释动机。
  soft_rule:
    - 两项列举通常比三项列举更自然。
    - 网文正文优先口语可读性，文艺化修辞只在角色或场景需要时使用。
  checklist:
    - 是否出现连续形容词堆砌。
    - 是否用说明替代场景行动。
    - 是否每段都在解释读者已经能看懂的因果。
    - 是否存在高频 AI 连接词和套话。
  example:
    - 将“他感到无比震惊和愤怒”改为具体动作、停顿、视线和下一步选择。
dedup_verdict: retain
dedup_against: []
reuse_scope: universal
safety_level: normal
status: active
notes:
  - 可派生 checker_or_schema_ref 资产，默认 warn-only，不直接阻断正文生成。
---

# 反 AI 味写作修订方法

该方法用于正文生成后的风格修订，也可在章节验收中作为检查器规则来源。核心目标不是让文本“更华丽”，而是让叙述更像人在特定视角、特定处境下自然写出的段落。

## 最小流程

1. 先删套话和解释腔。
2. 再检查句式重复、段落节奏和三段式结构。
3. 最后补动作、感官、选择和代价，让情绪从场景里长出来。

## Checker 集成

建议输出 `score`、`issues`、`suggestions`、`severity`。平台审核强时可提高风险词和句式指纹权重，但默认只告警。
