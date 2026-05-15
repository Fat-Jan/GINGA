---
id: base-template-state-init
asset_type: capability
title: runtime_state 初始化模板
topic: [通用]
stage: setting
quality_grade: B+
source_path: foundation/schema/runtime_state.yaml
last_updated: '2026-05-15'
provider_kind: deterministic_asset_provider
state_writes: [entity_runtime.RESOURCE_LEDGER, entity_runtime.FORESHADOW_STATE, entity_runtime.GLOBAL_SUMMARY, workspace.task_plan, workspace.findings, workspace.progress]
---

# runtime_state 初始化模板

根据 locked 与角色状态初始化 RESOURCE_LEDGER、FORESHADOW_STATE、GLOBAL_SUMMARY 与 planning-with-files 三件套。
