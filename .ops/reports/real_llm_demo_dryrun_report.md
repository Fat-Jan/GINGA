# P2-7C Real LLM Smoke Report

- execution_mode: `real_llm_demo`
- dry_run: `True`
- passed: `False`
- endpoint: `久久`
- book_id: `p2-7c-real-llm-smoke-20260515-204719`
- state_root: `/Users/arm/Desktop/ginga/.ops/real_llm_demo/p2-7c-smoke-state`
- output_path: `/Users/arm/Desktop/ginga/.ops/real_llm_demo/p2-7c-smoke-state/p2-7c-real-llm-smoke-20260515-204719/chapter_01.md`
- cost_risk: 1 ask-llm call, dynamic max_tokens based on word_target, timeout=300s; smoke quality only, not production readiness

## Commands

- `init` exit=planned: `./ginga init p2-7c-real-llm-smoke-20260515-204719 --topic 玄幻黑暗 --premise 失忆刺客醒来后发现短刃会吞吐微粒，他必须在第一重天堑前判断追杀者来自谁。 --word-target 50000 --state-root /Users/arm/Desktop/ginga/.ops/real_llm_demo/p2-7c-smoke-state`
- `run` exit=planned: `./ginga run p2-7c-real-llm-smoke-20260515-204719 --llm-endpoint 久久 --word-target 800 --state-root /Users/arm/Desktop/ginga/.ops/real_llm_demo/p2-7c-smoke-state`
- `status` exit=planned: `./ginga status p2-7c-real-llm-smoke-20260515-204719 --state-root /Users/arm/Desktop/ginga/.ops/real_llm_demo/p2-7c-smoke-state`

## Context Snapshot

- status: `planned`
- before_status: `missing`
- after_status: `missing`
- chapter_chars: `0`
- artifact_execution_mode: `None`
- audit_entries: `0`
- total_words_after: `None`
- foreshadow_pool_after: `0`

## Gap Report

- status: `planned`
- `real_call_not_executed` (info): dry-run only records scope and expected artifact paths.
- `production_quality_not_proven` (warn): a smoke run is still required before reading chapter quality evidence.

## Residual Risk

- `dry_run_has_no_quality_evidence` (high): run with --run before using this as real LLM evidence.
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
