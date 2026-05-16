# v2.3 Real LLM Harness Report

- generated_at: `2026-05-16T08:08:47+00:00`
- profile: `longform-small-batch`
- dry_run: `True`
- passed: `True`
- real_llm_executed: `False`
- endpoint: `久久`
- book_id: `v2-3-real-llm-harness`

## Preflight

- status: `PASS`

## Cost Boundary

- estimated_real_llm_calls: `12`
- max_real_llm_calls: `12`
- requested_chapters: `4`
- max_chapters: `5`
- word_target: `4000`

## Isolation

- state_root: `.ops/real_llm_harness/state`
- json_output: `.ops/validation/real_llm_harness.json`
- report_output: `.ops/reports/real_llm_harness_report.md`
- review_output_root: `.ops/reviews`

## Postflight

- status: `planned`
- generation_summary: `{}`

## Review Gate

- status: `planned`

## Residual Risk

- `dry_run_has_no_quality_evidence` (high): run with --run only after preflight is PASS and the operator accepts the cost boundary.
- `real_llm_variability` (medium): record endpoint, isolated state_root, generated artifacts, and review gate output for each run.
- `review_gate_is_report_only` (medium): treat review hard-gate blocks as stop signals; do not auto-edit story text or write truth from reports.
- `longform_quality_not_proven_by_harness` (medium): use small isolated batches and compare review output before widening any production run.
- `v1_7_5_followup_still_required` (medium): after prompt continuity repair, only run isolated small-batch validation and rerun review; do not expand batch size directly.

## Gates

- `preflight`
- `cost_boundary`
- `isolated_output`
- `postflight`
- `review_gate`

This harness makes real calls repeatable; it does not make smoke evidence equal production readiness.
