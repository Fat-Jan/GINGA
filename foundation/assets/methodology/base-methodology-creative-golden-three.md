---
id: base-methodology-creative-golden-three
asset_type: methodology
title: 黄金三章架构设计指南
topic: [通用]
stage: framework
quality_grade: A
source_path: _原料/基座/方法论/创意/黄金三章.md
last_updated: '2026-05-14'
method_family: 创意
rule_type: constraint
normative_strength: hard_rule
targets:
  topics: [通用]
  platforms: [起点, 番茄, 七猫]
  stages: [ideation, framework, drafting]
integrates_with:
  - base-template-project-creative-brief
  - bees-golden-three-checker
  - genre_profile
input_contract: [题材, 目标平台, 主角核心欲望, 第一个冲突, 读者承诺]
output_contract: [前三章结构, 章末钩, 首个代价, 平台适配建议]
platform_scope: [起点, 番茄, 七猫]
sub_sections:
  hard_rule:
    - 第一章必须快速给出主角处境、核心冲突或可追读问题。
    - 三章内必须完成至少一次读者承诺兑现或明确代价展示。
    - 开局避免设定倾倒、慢热铺垫和无目标日常。
    - 每章章末必须留下可追读的下一步问题。
  soft_rule:
    - 男频更强调目标、危机、升级和收益预期。
    - 女频更强调关系张力、身份落差、情绪承诺和处境反转。
  checklist:
    - 第一屏是否出现钩子。
    - 主角是否有明确欲望或被迫选择。
    - 读者是否知道继续读能得到什么。
    - 第三章是否出现代价、反差、收益或更大问题。
  example:
    - 危机钩 + 身份反差 + 小兑现，适合免费阅读强开篇。
  platform_variant:
    - 番茄、七猫：更早出钩子，更快反馈，更少背景解释。
    - 起点：类型逻辑和长期升级预期要更稳。
dedup_verdict: retain
dedup_against: []
reuse_scope: universal
safety_level: normal
status: active
notes:
  - 原文基于 2020-2025 平台榜单结构分析，并补充 2026 平台差异。
---

# 黄金三章架构设计指南

黄金三章是读者决定是否追读的结构入口。它应同时完成设定最小化、主角立住、冲突启动、读者承诺展示和第一次追读理由。

## 结构口径

前三章不是三章背景介绍，而是三次连续的读者说服：为什么这个人值得看，为什么这个局面必须继续看，为什么后面会持续有收益或代价。

## Checker 集成

建议黄金三章 checker 检查钩子位置、主角目标、章末悬念、信息倾倒、首次兑现和平台适配。默认输出建议，不阻断创作。
