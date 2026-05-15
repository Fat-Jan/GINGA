---
id: base-methodology-consistency-check
asset_type: capability
title: R2 一致性检查 Provider Hint
stage: refinement
quality_grade: A
status: active
input_contract:
  - workspace.chapter_text
  - locked
  - entity_runtime
output_contract:
  - consistency_report
  - audit_intents
provider: ginga_platform.orchestrator.registry.asset_providers.r2_consistency_check_provider
notes:
  - Provider must not write audit_log through state_updates.
  - step_dispatch or an orchestrator layer may turn audit_intents into StateIO.audit entries.
---

# R2 一致性检查 Provider Hint

R2 输出结构化检查报告，用于审计摘要和后置 checker 观察。检查结果默认 warn-only，不进入下一轮 prompt，也不通过 state_updates 写 audit_log。
