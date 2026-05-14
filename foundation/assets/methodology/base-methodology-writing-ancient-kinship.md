---
id: base-methodology-writing-ancient-kinship
asset_type: methodology
title: 古代宅门亲疏谱系校验指南
topic: [古代, 宫斗宅斗, 家族权力]
stage: setting
quality_grade: A-
source_path: _原料/基座/方法论/写作/古代家族亲缘.md
last_updated: '2026-05-14'
method_family: 写作
rule_type: constraint
normative_strength: hard_rule
targets:
  topics: [古代, 宫斗宅斗, 古代言情, 家族权力]
  platforms: [番茄, 七猫, 晋江]
  stages: [setting, drafting, refinement]
integrates_with:
  - character_card
  - entity_relation_graph
  - historical-fact-checker
input_contract: [家族谱系, 婚姻关系, 子女排序, 称谓规则]
output_contract: [谱系闭合检查, 称谓风险, 权力关系备注]
platform_scope: [番茄, 七猫, 晋江]
sub_sections:
  hard_rule:
    - 生成书名、总纲、包装、角色卡、正文前先补齐最小亲缘表。
    - 原配、继室、妾室、通房、嫡庶、长幼必须互相闭合。
    - 称谓必须与辈分、婚姻、嫡庶和场景身份一致。
  enumeration:
    - father
    - wives
    - children
    - siblings
    - marriage_links
    - inheritance_order
  checklist:
    - 是否存在角色关系词好看但谱系不闭合。
    - 是否把嫡庶、继室、妾室权力写成同一层。
    - 是否忽略婚姻带来的称谓变化。
dedup_verdict: retain
dedup_against: []
reuse_scope: single_genre
safety_level: normal
status: active
notes:
  - 与实体关系图模板强相关。
---

# 古代宅门亲疏谱系校验指南

该资产只解决一件事：避免古代家族叙事中关系词成立、谱系却不闭合。它应在角色卡和实体关系图之前使用。

## 最小表

至少记录父系、婚姻关系、子女、嫡庶、长幼、继承顺位。正文生成时称谓和权力行为必须能回到这张表。
