# P2-7C Real LLM Smoke Report

- execution_mode: `real_llm_demo`
- dry_run: `False`
- passed: `True`
- endpoint: `xiaomi-tp`
- book_id: `p2-7c-real-llm-smoke-20260515`
- state_root: `.ops/real_llm_demo/p2-7c-smoke-state`
- output_path: `.ops/real_llm_demo/p2-7c-smoke-state/p2-7c-real-llm-smoke-20260515/chapter_01.md`
- cost_risk: 1 ask-llm call, max_tokens=4096, timeout=300s; smoke quality only, not production readiness

## Commands

- `refresh_existing` exit=0: `./ginga refresh-existing p2-7c-real-llm-smoke-20260515 --state-root .ops/real_llm_demo/p2-7c-smoke-state`

## Context Snapshot

- status: `captured`
- before_status: `present`
- after_status: `present`
- chapter_chars: `2553`
- artifact_execution_mode: `real_llm_demo`
- audit_entries: `61`
- total_words_after: `5793`
- foreshadow_pool_after: `1`

## Gap Report

- status: `needs_review`
- `production_quality_not_proven` (warn): single smoke does not prove long-form production readiness.
- `single_chapter_scope` (info): this gate covers one chapter only; multi-chapter continuity remains outside scope.

## Residual Risk

- `real_llm_variability` (medium): record endpoint, prompt scope, artifact path, and rerun only with explicit approval.
- `single_chapter_scope` (medium): treat this as smoke evidence, not a multi-chapter quality claim.
- `provider_quality_not_longform_proven` (medium): keep mock harness as boundary regression and use real demo reports for quality review.
- `endpoint_cost_dependency` (low): default to dry-run; real calls require explicit --run.

## will_not_overwrite

- `foundation/runtime_state/demo-book`
- `foundation/runtime_state/s2-demo`
- `foundation/runtime_state/immersive-demo`
- `.ops/reports/agent_harness_report.md`

A dry run records scope only. A real smoke run is not production readiness or long-chapter quality evidence.
