---
id: base-methodology-style-polish
asset_type: capability
title: R1 离线风格润色 Provider Hint
stage: refinement
quality_grade: A
status: active
input_contract:
  - workspace.chapter_text
  - locked.GENRE_LOCKED
output_contract:
  - workspace.chapter_text
provider: ginga_platform.orchestrator.registry.asset_providers.r1_style_polish_provider
notes:
  - Offline deterministic polish; no real LLM calls.
  - HTML foreshadow comments must be preserved verbatim.
---

# R1 离线风格润色 Provider Hint

R1 做 production-safe 的轻量确定性修订：删套话、压缩解释腔、保留正文结构和所有伏笔注释。它不替代真实文学润色，只替换固定 stub 文案。
