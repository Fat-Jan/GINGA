# Stage Closeout: v2.6a LLM Config

## Objective

- Stage: `v2.6a LLM Config`
- Objective: Add project-local LLM endpoint config, loading helpers, and a fallback call wrapper without real network calls.
- Backup boundary: Code-layer only; live fallback validation remains `v2.6b`.

## Scope

- Files changed:
  - `llm_config.yaml`
  - `ginga_platform/orchestrator/cli/llm_config.py`
  - `ginga_platform/orchestrator/cli/__main__.py`
  - `ginga_platform/orchestrator/cli/demo_pipeline.py`
  - `ginga_platform/orchestrator/cli/immersive_runner.py`
  - `ginga_platform/orchestrator/runner/tests/test_llm_config.py`
  - `STATUS.md`
  - `ROADMAP.md`
  - `notepad.md`
- Explicitly excluded files:
  - `ginga_platform/orchestrator/cli/multi_chapter.py`
  - `ginga_platform/orchestrator/model_topology.py`
  - `ginga_platform/orchestrator/review.py`
  - `ginga_platform/orchestrator/runner/state_io.py`
  - `ginga_platform/orchestrator/cli/longform_policy.py`
- Related validation artifacts in `.ops/validation/**`: existing baseline artifacts only; this closeout did not persist refreshed timestamp-only validation JSON.
- Related report artifacts in `.ops/reports/**`: this closeout report.

## Truth Sync

- `STATUS.md`: v2.6 moved from `planned` to `in_progress`; v2.6a code layer is verified, v2.6b live fallback remains open.
- `ROADMAP.md`: current-status paragraph now records v2.6a offline closeout and v2.6b live fallback boundary.
- `notepad.md`: next-step paragraph now records v2.6a verified code layer and keeps v1.7-7 as the next main task.
- Sync note: v2.6 is not marked `done` because no real endpoint fallback validation was run.

## Verification Summary

- Verification command(s):
  - `python -m unittest ginga_platform.orchestrator.runner.tests.test_llm_config ginga_platform.orchestrator.runner.tests.test_immersive_mode -v`
  - `git diff --check`
  - `python3 scripts/verify_all.py --quick`
- Exit code(s):
  - focused unittest: `0` (`35 tests OK`)
  - diff check: `0`
  - quick baseline: `0` (`13/13 PASS`, `287 tests OK`)
- Evidence path(s):
  - `ginga_platform/orchestrator/runner/tests/test_llm_config.py`
  - `.ops/reports/stage_closeout_v2_6a_llm_config.md`

## Residual Risks

- Residual risk: role-based fallback is tested with mocked `subprocess.run`; real endpoint fallback remains unverified.
- Operator review needed before widening scope: run v2.6b with isolated output and explicit real-call budget before declaring model-side stability.

## Commit Message

- Proposed commit message: `feat(platform): 收口 v2.6a LLM 配置入口`
- Must state stage/update content, verification evidence, and residual risk or remaining risk.

## Next Step

- Next step: v1.7-7a style warn 分级离线实现，或单独开 v2.6b live fallback smoke.
- Owner: main agent for integration and verification; real LLM verification remains main-agent/operator owned.
