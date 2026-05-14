---
id: base-methodology-writing-character-naming
asset_type: methodology
title: 角色命名智能生成指南
topic: [通用]
stage: setting
quality_grade: A-
source_path: _原料/基座/方法论/写作/角色命名.md
last_updated: '2026-05-14'
method_family: 写作
rule_type: constraint
normative_strength: hard_rule
targets:
  topics: [通用]
  platforms: [番茄, 七猫, 起点, 晋江]
  stages: [setting, drafting]
integrates_with:
  - character_card
  - genre_profile
  - platform-config
input_contract: [内容桶, tagpack, 角色功能, 题材风味, 平台优先级]
output_contract: [角色姓名候选, 命名理由, 可读性风险, 同名冲突检查]
platform_scope: [番茄, 七猫, 起点, 晋江]
sub_sections:
  hard_rule:
    - Fanqie-first 场景优先判断内容桶、tagpack、平台可读性，再判断名字美感。
    - 主角、反派、配角命名必须区分功能，不用同一风格批量套名。
    - 同项目中避免音近、字形近、身份近的角色名同时出现。
    - 古代、年代、都市、玄幻等题材必须匹配时代和社会阶层。
  soft_rule:
    - 免费阅读平台优先高可读、低理解成本的名字。
    - 付费订阅平台可适度保留文化感或象征意义，但不能牺牲辨识度。
  checklist:
    - 名字是否一眼能读。
    - 名字是否暗示角色功能或气质。
    - 名字是否与题材、时代、地域冲突。
    - 名字是否与已有角色混淆。
  example:
    - 数据线验证期先选“像这个桶”的名字，再做细腻审美优化。
dedup_verdict: retain
dedup_against: []
reuse_scope: cross_genre
safety_level: normal
status: active
notes:
  - 可与角色卡模板和题材 profile 联合路由。
---

# 角色命名智能生成指南

角色名是读者识别角色功能的第一层界面。命名时先保证平台可读、题材可信、角色功能清楚，再追求诗意或隐喻。

## 默认优先级

番茄优先或数据验证期：

1. 当前内容桶
2. 当前 tagpack
3. 平台可读性
4. 题材风味

## 验收口径

生成角色名后，应同步输出命名理由和冲突检查。若名字需要解释很久才能成立，通常说明它不适合放在高频阅读场景里。
