# Workflow Stage Observation: v1-8-3-main-workflow

> Report-only workflow observability. It never runs the workflow.

- workflow: `ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml`
- stage_count: 12
- runs_workflow: `False`

## Stages

- 1. `A_brainstorm` capability=base-methodology-creative-brainstorm skill=None writes=['retrieved.brainstorm']
- 2. `B_premise_lock` capability=base-template-story-dna skill=None writes=['locked.STORY_DNA']
- 3. `C_world_build` capability=base-template-worldview skill=None writes=['locked.GENRE_LOCKED', 'locked.WORLD']
- 4. `D_character_seed` capability=base-template-protagonist skill=None writes=['entity_runtime.CHARACTER_STATE']
- 5. `E_outline` capability=base-template-outline skill=None writes=['locked.PLOT_ARCHITECTURE']
- 6. `F_state_init` capability=base-template-state-init skill=None writes=['entity_runtime.RESOURCE_LEDGER', 'entity_runtime.FORESHADOW_STATE', 'entity_runtime.GLOBAL_SUMMARY', 'workspace.task_plan', 'workspace.findings', 'workspace.progress']
- 7. `G_chapter_draft` capability=base-card-chapter-draft skill=skill-router writes=['workspace.chapter_text', 'entity_runtime.GLOBAL_SUMMARY.total_words']
- 8. `H_chapter_settle` capability=base-template-chapter-settle skill=None writes=['entity_runtime.CHARACTER_STATE', 'entity_runtime.RESOURCE_LEDGER', 'entity_runtime.FORESHADOW_STATE', 'workspace.progress']
- 9. `R1_style_polish` capability=base-methodology-style-polish skill=None writes=['workspace.chapter_text']
- 10. `R2_consistency_check` capability=base-methodology-consistency-check skill=None writes=['audit_log']
- 11. `R3_final_pack` capability=base-methodology-final-pack skill=None writes=['entity_runtime.GLOBAL_SUMMARY']
- 12. `V1_release_check` capability=base-checker-dod-final skill=None writes=['audit_log']
