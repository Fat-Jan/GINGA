# v2.3 Real LLM Harness Report

- generated_at: `2026-05-16T08:29:42+00:00`
- profile: `longform-small-batch`
- dry_run: `False`
- passed: `False`
- real_llm_executed: `True`
- endpoint: `久久`
- book_id: `v1-7-6-body-contract-single-ch1`

## Preflight

- status: `PASS`

## Cost Boundary

- estimated_real_llm_calls: `3`
- max_real_llm_calls: `3`
- requested_chapters: `1`
- max_chapters: `5`
- word_target: `4000`

## Isolation

- state_root: `.ops/real_llm_harness/v1-7-6-body-contract-single-ch1-state`
- json_output: `.ops/validation/v1_7_6_body_contract_single_ch1_real_llm_harness.json`
- report_output: `.ops/reports/v1_7_6_body_contract_single_ch1_real_llm_harness.md`
- review_output_root: `.ops/reviews`

## Postflight

- status: `FAIL`
- generation_summary: `{'requested_chapters': 1, 'completed_chapters': 0, 'drift_status': 'stable', 'failed_chapter': 1, 'failure_reason': 'RuntimeError: chapter 1 failed quality gate after repair: short_chapter body_chinese_chars=3340 < 4200', 'failed_batches': [1], 'short_chapters': [], 'missing_foreshadow_chapters': []}`

## Review Gate

- status: `PASS`
- report: `.ops/reviews/v1-7-6-body-contract-single-ch1/v2-3-real-llm-review-gate/review_report.json`
- issue_count: `0`
- hard_gate_blocks_next_batch: `False`

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
