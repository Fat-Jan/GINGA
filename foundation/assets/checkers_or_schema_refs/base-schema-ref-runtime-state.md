---
id: base-schema-ref-runtime-state
asset_type: checker_or_schema_ref
title: State.json 运行时状态 Schema 引用
topic: [通用]
stage: cross_cutting
quality_grade: A
source_path: _原料/基座/方法论/市场/state-schema.md
last_updated: '2026-05-14'
target_asset_type: runtime_state
output_schema:
  version: string
  meta: object
  project: object
  characters: object
  world: object
  outline: object
  foreshadow: object
  hooks: object
  platform_config: object
  audit_log: array
check_mode: warn
severity_levels: [info, warn, error, fatal]
rule_count: 9
integrates_with:
  - runtime_state
  - orchestrator/state_manager
  - audit_log
input_contract: [state.json, module_state_update]
output_contract: [schema_validation_result, missing_fields, incompatible_update_paths]
dedup_verdict: retain
dedup_against: []
reuse_scope: universal
safety_level: normal
status: active
notes:
  - 原文声明 state.json 为统一结构定义和单一事实源。
  - 按任务要求作为 checker_or_schema_ref 资产迁移，而非普通 methodology。
  - 读者吸引力分类法保留为 methodology，但通过 schema_ref 字段接入 checker。
---

# State.json 运行时状态 Schema 引用

该资产把 `_原料/基座/方法论/市场/state-schema.md` 作为运行时状态结构的 schema-ref 入口。所有模块写入状态前应引用它，避免重复定义或漂移。

## Schema Ref

`state.json` 至少覆盖版本、项目元信息、角色、世界观、大纲、伏笔、钩子、平台配置和审计日志。任何模块如需扩展字段，应通过统一 schema 演进，而不是在局部文件中私自增加不兼容结构。

## Checker 建议

状态检查器应输出缺失字段、类型不匹配、未知字段、破坏性更新路径和严重等级。默认 `warn`，在发布或长链路自动化前可切换为 `block`。
