# v1.7-3 4/5 章真实回归复核

日期：2026-05-16

## 范围

- endpoint: `久久`
- book_id: `longform-jiujiu-v173-45-regression`
- state_root: `.ops/longform_smoke/v1-7-3-4-5-regression/state`
- batch_schedule: `4,5`
- requested_chapters: `9`
- word_target: `4000`

## 生成结果

`scripts/run_longform_llm_smoke.py` 完成 9/9 章真实生成，产物见：

- `.ops/validation/longform_jiujiu_v173_45_regression.json`
- `.ops/reports/longform_jiujiu_v173_45_regression.md`
- `.ops/longform_smoke/v1-7-3-4-5-regression/state/longform-jiujiu-v173-45-regression/`

脚本级 drift 指标为 `stable`：

- low_anchor_chapters: `[]`
- forbidden_hit_chapters: `[]`
- short_chapters: `[]`
- missing_foreshadow_chapters: `[]`
- production policy: recommended_batch_size=`4`，upper_bound=`5`，pressure_test_only_at_or_above=`6`

## Review 复核

已额外运行：

```bash
python3 -m ginga_platform.orchestrator.cli review longform-jiujiu-v173-45-regression \
  --run-id v1-7-3-45-regression-review \
  --state-root .ops/longform_smoke/v1-7-3-4-5-regression/state \
  --output-root .ops/reviews
```

Review 产物见：

- `.ops/reviews/longform-jiujiu-v173-45-regression/v1-7-3-45-regression-review/review_report.json`
- `.ops/reviews/longform-jiujiu-v173-45-regression/v1-7-3-45-regression-review/README.md`

`ginga review` 结论是 `warn`，并且 `longform_quality_gate.hard_gate.should_block_next_real_llm_batch=true`：

- block_reasons: `consecutive_opening_loop_risk`, `missing_low_frequency_anchor`
- inspected_chapters: `chapter_06.md`, `chapter_07.md`, `chapter_08.md`, `chapter_09.md`
- reviewer_queue: `chapter_06.md`, `chapter_07.md`, `chapter_08.md`, `chapter_09.md`

## 判定

4/5 章批量口径能完成 9 章真实生成，且没有短章、禁词、伏笔缺失。相比旧 10 连发第 19 章暴露 drift，当前小回归没有复现短章或禁词问题。

但 review hard gate 仍捕捉到连续开篇回环，且后 4 章窗口里存在低频锚点缺失。因此本轮不能据此继续扩大真实生成；下一批真实 LLM 前必须先处理章节开头续写连续性和组合题材低频锚点保持。

## 后续建议

- 不改正文、不自动修复，只把本报告作为 `report-only` 证据。
- 若继续真实长篇验证，先调整章节输入包或 prompt，让第 N 章明确承接上一章，而不是重启开篇感官模板。
- 若做 v1.9 Story Truth Template，优先把 `chapter_input_bundle`、低频题材锚点、伏笔账本和续写状态作为字段矩阵重点。
