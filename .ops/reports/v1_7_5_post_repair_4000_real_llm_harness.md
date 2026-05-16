# v2.3 Real LLM Harness Report

- generated_at: `2026-05-16T06:10:44+00:00`
- profile: `longform-small-batch`
- dry_run: `False`
- passed: `False`
- real_llm_executed: `True`
- endpoint: `久久`
- book_id: `v1-7-5-post-repair-v23-4000-small-batch`

## Preflight

- status: `PASS`

## Cost Boundary

- estimated_real_llm_calls: `4`
- max_real_llm_calls: `4`
- requested_chapters: `4`
- max_chapters: `5`
- word_target: `4000`

## Isolation

- state_root: `.ops/real_llm_harness/v1-7-5-post-repair-4000-state`
- json_output: `.ops/validation/v1_7_5_post_repair_4000_real_llm_harness.json`
- report_output: `.ops/reports/v1_7_5_post_repair_4000_real_llm_harness.md`
- review_output_root: `.ops/reviews`

## Postflight

- status: `PASS`
- generation_summary: `{'requested_chapters': 4, 'completed_chapters': 4, 'drift_status': 'needs_review', 'short_chapters': [2, 3, 4], 'missing_foreshadow_chapters': []}`

## Review Gate

- status: `blocked`
- report: `.ops/reviews/v1-7-5-post-repair-v23-4000-small-batch/v2-3-real-llm-review-gate/review_report.json`
- issue_count: `16`
- hard_gate_blocks_next_batch: `True`
- warning `review_hard_gate_blocks_next_batch`: block_reasons=['consecutive_opening_loop_risk']

## Residual Risk

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
