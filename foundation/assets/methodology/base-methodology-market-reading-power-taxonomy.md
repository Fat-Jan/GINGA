---
id: base-methodology-market-reading-power-taxonomy
asset_type: methodology
title: 读者吸引力分类法
topic: [通用]
stage: analysis
quality_grade: A
source_path: _原料/基座/方法论/市场/读者吸引力分类法.md
last_updated: '2026-05-14'
method_family: 市场
rule_type: enumeration
normative_strength: hard_rule
targets:
  topics: [通用]
  platforms: [番茄, 七猫, 起点, 晋江]
  stages: [ideation, framework, drafting, analysis]
integrates_with:
  - reading-power-checker
  - hook-checker
  - cool-point-payoff-checker
  - chapter_text
input_contract: [chapter_text, chapter_outline, target_reader, platform]
output_contract: [钩子类型, 爽点类型, 微兑现等级, 追读力问题]
platform_scope: [番茄, 七猫, 起点, 晋江]
sub_sections:
  hard_rule:
    - 钩子、爽点、微兑现必须使用统一分类，避免各 checker 自造枚举。
    - 章末钩要对应明确的未完成问题或待兑现承诺。
    - 爽点必须有前置压迫、行动或代价，不能只写结果。
  enumeration:
    - 危机钩
    - 悬念钩
    - 情绪钩
    - 利益钩
    - 身份反差
    - 爽点兑现
    - 微兑现
  checklist:
    - 当前章节钩子是否能被分类。
    - 分类强度是否与平台节奏匹配。
    - 是否存在承诺但无兑现。
  schema_ref:
    - reading_power.hook_type
    - reading_power.cool_point_type
    - reading_power.payoff_level
dedup_verdict: retain
dedup_against: []
reuse_scope: universal
safety_level: normal
status: active
notes:
  - 原文声明为 shared 单一事实源；迁移后作为 checker 枚举来源。
---

# 读者吸引力分类法

该资产为追读力工程提供统一词表。下游 checker 应引用这里的钩子、爽点和微兑现分类，避免同义词扩散导致评分不可比较。

## 集成方式

章节分析应先识别吸引力单元，再判断强度、位置和兑现关系。输出应能被章节修订器消费，而不是只给抽象评价。
