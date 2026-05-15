---
id: base-methodology-final-pack
asset_type: capability
title: R3 终稿打包 Provider Hint
stage: final_pack
quality_grade: A
status: active
input_contract:
  - workspace.chapter_text
  - entity_runtime.GLOBAL_SUMMARY
output_contract:
  - entity_runtime.GLOBAL_SUMMARY
provider: ginga_platform.orchestrator.registry.asset_providers.r3_final_pack_provider
notes:
  - Word count and summary must be derived from actual chapter_text.
  - Provider returns state_updates only; artifact writing stays in StateIO paths.
---

# R3 终稿打包 Provider Hint

R3 基于真实章节正文生成章节摘要与字数统计，更新 GLOBAL_SUMMARY。不得固定写入 5000 字，也不得把 mock metadata 当生产结果。
