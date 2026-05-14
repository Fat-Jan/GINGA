# weak_examples_batch_B

## Summary

- Batch: B
- Listed cards: 51
- Changed count: 51
- Skipped count: 0
- Remaining weak cases in batch: 0 by local section audit

## Work Performed

- Replaced weak `## 示例输入` content (`无。` / direct-use placeholder) with concise concrete examples.
- Kept changes limited to the final `## 示例输入` sections of the 51 files listed in `.ops/validation/weak_examples_batch_B.txt`.
- Preserved frontmatter, prompt bodies, headings, and existing Chinese markdown style.

## Uncertainties

- None for the owned batch.

## Verification

- Local batch audit: 51/51 listed files have concrete bullet examples under `## 示例输入`; no weak first-line placeholders remained in batch.
- Required command: `python3 scripts/report_prompt_quality.py foundation/assets/prompts`
- Result: exit 0; wrote `.ops/validation/prompt_quality_report.json` with `total=461` and `weak_examples=50` globally.
- Batch B remaining weak cases: 0 found in the report's remaining weak candidates.
