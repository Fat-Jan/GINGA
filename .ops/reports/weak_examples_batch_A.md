# weak_examples_batch_A

- Task ID: ST-S3-Q-WEAK-EXAMPLES-A
- Batch: A
- Listed cards: 51
- Changed count: 51
- Skipped count: 0
- Remaining weak cases in batch: 0

## Scope

Only files listed in `.ops/validation/weak_examples_batch_A.txt` were edited, plus this report and the task handoff heartbeat.

## Changes

Replaced weak `## 示例输入` content (`无。` / `直接复制...`) with concise, concrete JSON-ish examples matching each card's prompt shape. Prompt bodies and frontmatter were not intentionally rewritten.

## Uncertainties

- Workspace is not a Git repository at `/Users/arm/Desktop/ginga`, so `git diff --name-only` could not be used for changed-file verification.
- Validation relies on direct file scans and `scripts/report_prompt_quality.py`.

## Verification

- Batch direct audit: 51 listed files, 0 missing `## 示例输入`, 0 remaining weak sections in batch.
- `python3 scripts/report_prompt_quality.py foundation/assets/prompts`: `total=461 weak_examples=0`.
