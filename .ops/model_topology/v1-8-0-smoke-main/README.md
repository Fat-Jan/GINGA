# Model Topology Observation

- run_id: `v1-8-0-smoke-main`
- mode: `report_only`
- runtime_takeover: `False`
- output_boundary: `.ops/model_topology/<run_id>/`

## Role Matrix

| role | stage_refs | primary_tier | output_boundary |
|---|---|---|---|
| showrunner | A_brainstorm, B_premise_lock, E_outline | strong reasoning | proposal_only |
| prose_writer | G_chapter_draft | cn prose anchor | chapter_text_artifact |
| state_settler | H_chapter_settle, R2_consistency_check | deterministic asset-backed provider | candidate_or_audit_intent |
| style_reviewer | R1_style_polish, review | report-only reviewer | report_only |
| longform_critic | review, longform_quality_gate | long-context critic | report_only |

## Probe Summary

- live_probe_enabled: `False`
- ok_count: `0`
- failed_count: `0`
- not_run_count: `4`

## Redlines

- observation report must not select runtime providers
- probe results must not write StateIO or runtime_state
- critic/reviewer roles remain report-only
- provider snapshots are dated evidence, not long-term truth
