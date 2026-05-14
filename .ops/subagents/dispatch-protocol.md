# Subagent Dispatch Protocol

**Scope**: Ginga project subagent dispatch, monitoring, model tiering, handoff, and board updates.
**Canonical status**: This file is the bottom-level rule source. Task-specific prompts may tighten these rules, but must not weaken them.
**Updated**: 2026-05-14

---

## 1. Executor Choice

Use the lightest executor that still gives reliable evidence.

| Work type | Preferred executor | Model tier | Must write heartbeat? |
|---|---|---|---|
| Small read-only scan / counting / document summary | `spawn_agent(agent_type=explorer)` | low-cost / mini when explicitly available | No, final callback is enough |
| Large read-only scan over many files | `codex-companion task --background --fresh` | low-cost / mini or medium | Yes |
| Bounded code edit with clear write set | `spawn_agent(agent_type=worker)` or `codex-companion --write` | coding model / medium | Yes |
| Cross-module architecture choice | main agent or high-tier explorer | strong model | Optional report file |
| Endpoint-sensitive LLM batch work | `codex-companion --background --write` | medium; failover-aware | Yes |

Rules:
- `spawn_agent` callbacks have no streaming heartbeat. Treat timeout from `wait_agent` as "no final callback yet", not failure.
- For tasks expected to run longer than 10 minutes, prefer an executor that can append a heartbeat file.
- For write tasks, every subagent brief must declare a disjoint write set.
- Claude-framework subagents, including wrappers with `codex` names, are not independent of the host API. True independent fallback is direct local `codex-companion` or manual `codex resume`.

## 2. Model Tiering

Default model inheritance is allowed only for quick one-off delegation. For planned dispatch, explicitly choose a tier:

- **Low-cost / mini**: read-only repo scans, statistics, frontmatter audits, report drafting, task decomposition.
- **Coding model / medium**: focused implementation with tests, mechanical refactors, validators, CLI glue.
- **Strong model**: architecture tradeoffs, ambiguous cross-layer design, final integration review, high-risk behavior changes.

Do not spend a strong model on pure counting, broad grep summaries, or schema coverage reports unless the task is also making architectural decisions.

## 3. Heartbeat Protocol

Any long-running or write-capable subagent must append to a task-owned heartbeat file, usually:

```text
.ops/p7-handoff/<TASK_ID>.md
.ops/reports/<TASK_ID>.md
.ops/scout-reports/<TASK_ID>-progress.md
```

Heartbeat triggers:
- START within 5 minutes of launch.
- Every 10 minutes while active.
- Within 10 minutes after each major subtask lands.
- On every blocker, dependency wait, tool failure, endpoint failure, or lock-map question.
- DONE or BLOCKED at the end.

Heartbeat entry format:

```markdown
## <ISO timestamp> | <TASK_ID> | <phase>

- Progress: <what changed since last heartbeat>
- Files touched or read: <paths or counts>
- Evidence: <test/checkpoint/output path>
- Next: <next concrete step>
- Blockers: <none or exact blocker>
```

Heartbeat files are append-only. Do not rewrite old entries.

## 4. Callback And Zombie Detection

For `spawn_agent`:
- Poll with `wait_agent` only when the result is needed for the next step.
- A timeout means no final callback yet.
- If there is no callback after the expected window, either continue with local evidence or close/re-dispatch with a smaller task.

For heartbeat-based workers:
- START missing after 5 minutes: inspect logs; if no activity, mark `stale`.
- No heartbeat for 15 minutes on normal code tasks: inspect logs before action.
- No heartbeat for 20 minutes on large read tasks: inspect logs; if no file/command progress, mark `zombie`.
- No new command/log progress for 10 minutes after a known error loop: stop and replan.
- Never infer failure from silence alone when file outputs, mtimes, or tests show progress.

## 5. Return Packet Requirements

A task is not ready for `done` until the main agent sees all three:

1. **Artifact**: expected files, reports, or code paths exist.
2. **Heartbeat/final callback**: subagent wrote DONE/BLOCKED or returned a final message.
3. **Checkpoint**: verification command, test result, byte/count check, or audit log evidence.

If any one is missing, status may be `validating`, `blocked`, or `stale`, but not `done`.

## 6. Board Update Rules

`.ops/subagents/board.json` is the task truth table.

- Subagents may request `validating`, but only the main agent may mark `done`.
- Every board update must change both the task `updated_at` and the top-level `updated_at`.
- Evidence must cite concrete files, counts, tests, or logs.
- Do not use broad text replacement on the board. Update the relevant task fields deliberately.
- Allowed states: `queued`, `assigned`, `running`, `validating`, `done`.
- Exception states: `stale`, `zombie`, `retry_wait`, `failed`, `blocked`.

## 7. Lock Map And Boundary Rules

Every dispatched task must include:

- Owned files / directories.
- Forbidden files / directories when relevant.
- Whether the task is read-only or write-capable.
- Verification command.
- Heartbeat path when applicable.

If a subagent needs to write outside its lock map:

```markdown
## QUESTION extend lock map: <path>

- Reason: <why this path is needed>
- Risk: <possible conflict>
- Alternative: <fallback without extension>
```

The subagent must stop before writing the new path until the main agent explicitly ACKs it.

## 8. Default Dispatch Template

Use this skeleton for new tasks:

```markdown
Task ID:
Executor:
Model tier:
Mode: read-only | write-capable
Owned files:
Forbidden files:
Inputs:
Expected outputs:
Verification:
Heartbeat path:
Callback packet:
Failure policy:
```

The brief must state: "You are not alone in the codebase; do not revert or overwrite unrelated work."

## 9. Current Sprint 3 Defaults

- RAG Layer 2/3 investigation: explorer, low-cost acceptable, read-only, no heartbeat required if expected <10 minutes.
- RAG Layer 2/3 implementation: worker/coding model, write set `rag/**`, RAG tests, and any explicitly named orchestrator hook files; heartbeat required.
- Prompt quality validation: low-cost scan first; write validators under `scripts/**` and reports under `.ops/validation/**`; heartbeat required for batch edits.
- Methodology asset migration: worker/coding model or medium; write set `foundation/assets/methodology/**` plus validators; heartbeat required.

