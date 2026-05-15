---
id: base-template-chapter-settle
asset_type: capability
title: H 章节结算 Provider Hint
stage: chapter_settle
quality_grade: A
status: active
input_contract:
  - workspace.chapter_text
  - entity_runtime.CHARACTER_STATE
  - entity_runtime.RESOURCE_LEDGER
  - entity_runtime.FORESHADOW_STATE
output_contract:
  - entity_runtime.CHARACTER_STATE
  - entity_runtime.RESOURCE_LEDGER
  - entity_runtime.FORESHADOW_STATE
  - workspace.progress
provider: ginga_platform.orchestrator.registry.asset_providers.h_chapter_settle_provider
notes:
  - Provider must return state_updates only; StateIO applies the writes.
  - Foreshadow and particle parsing should stay aligned with demo_pipeline rollup semantics.
---

# H 章节结算 Provider Hint

章节结算读取最新正文和滚动状态，产出角色事件、微粒账本、伏笔池与进度更新。该资产只描述能力边界；运行时代码不得直接写 runtime_state YAML。
