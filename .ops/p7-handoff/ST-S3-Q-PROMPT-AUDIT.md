# ST-S3-Q-PROMPT-AUDIT Heartbeat

Task: prompt card frontmatter quality audit scripts and reports.
Protocol: `.ops/subagents/dispatch-protocol.md`.
Write set:
- `scripts/validate_prompt_frontmatter.py`
- `scripts/report_prompt_quality.py`
- `.ops/validation/prompt_frontmatter_report.json`
- `.ops/validation/prompt_quality_report.json`
- this heartbeat file

Do not edit `foundation/assets/prompts/*.md` in this task; this is audit/report only.


## 2026-05-14T17:44:46+08:00 | ST-S3-Q-PROMPT-AUDIT | START

- Progress: Started prompt quality audit/report script task.
- Files touched or read: .ops/subagents/dispatch-protocol.md; skill docs
- Evidence: Dispatch protocol read; heartbeat initialized.
- Next: Inspect prompt schema, sample cards, Sprint 3 context, then implement report-only scripts.
- Blockers: none

## 2026-05-14T17:51:00+08:00 | ST-S3-Q-PROMPT-AUDIT | DONE

- Progress: Added report-only prompt frontmatter validator and prompt quality reporter; generated both validation JSON reports.
- Files touched or read: scripts/validate_prompt_frontmatter.py; scripts/report_prompt_quality.py; .ops/validation/prompt_frontmatter_report.json; .ops/validation/prompt_quality_report.json; .ops/p7-handoff/ST-S3-Q-PROMPT-AUDIT.md; read schema, sample prompt cards, scout report, ROADMAP Sprint 3.
- Evidence: python3 scripts/validate_prompt_frontmatter.py -> total=461 violations=1904; python3 scripts/report_prompt_quality.py foundation/assets/prompts -> total=461 weak_examples=202.
- Next: Main agent can use JSON reports to prioritize Sprint 3 prompt-card cleanup.
- Blockers: none
