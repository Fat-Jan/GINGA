# Prompt Schema Fix Report

Task: ST-S3-Q-PROMPT-SCHEMA-FIX  
Generated: 2026-05-14 18:03 CST

## Summary

Used `.ops/validation/prompt_frontmatter_report.json` as the repair source of truth and edited prompt asset frontmatter only. Prompt bodies were not rewritten.

## Changes

- Prompt files touched: 461
- YAML frontmatter parse errors fixed: 4
  - `prompts-card-111.md`
  - `prompts-card-429.md`
  - `prompts-card-433.md`
  - `prompts-card-436.md`
- `task_full` populated: 461
  - 458 derived from body JSON `"task"` values.
  - 3 derived from stable non-task frontmatter/id signals:
    - `prompts-card-1.md`: `load_senior_web_novel_editor`
    - `prompts-card-2.md`: `lock_style_and_restrictions`
    - `prompts-card-目录页.md`: `catalog_prompt_library_contents`
- Illegal `stage` values normalized: 20
  - `scene` and `scene_generator` -> `drafting`
  - `character` and `world` -> `setting`
- `card_intent` normalized to schema enums: 461
- `card_kind` normalized to schema enums: 460
  - The index card was already schema-compliant.
- `output_kind` normalized to schema enums: 460
  - The index card's `list` value was already schema-compliant.
- Empty topics fixed: 11 audit cases cleared
  - 4 were cleared by repairing YAML parse errors on cards that already had non-empty topic arrays.
  - 7 explicit `topic: []` files received tags from title/usage-context signals:
    - `prompts-card-150.md`
    - `prompts-card-343.md`
    - `prompts-card-347.md`
    - `prompts-card-367.md`
    - `prompts-card-399.md`
    - `prompts-card-456.md`
    - `prompts-card-79.md`

## Deferred Cases

None. All validator-tracked parse, required-field, empty-topic, missing-`task_full`, and checked enum violations are cleared.

## Verification

Command run:

```bash
python3 scripts/validate_prompt_frontmatter.py --output /tmp/prompt_frontmatter_after_schema_fix.json --strict
```

Observed output:

```text
wrote /tmp/prompt_frontmatter_after_schema_fix.json: total=461 violations=0
```

Parsed verification summary from `/tmp/prompt_frontmatter_after_schema_fix.json`:

- `total_files`: 461
- `violation_count`: 0
- `parse_errors`: 0
- `empty_topic_files`: 0
- `missing_task_full_files`: 0
- `illegal_enum_values`: `{}`
