# v1.7 Longform Production Policy

## 结论

Ginga 正式真实 LLM 长篇生成采用 5 章批次；7 章为生产上限；10 章及以上只允许作为压力测试。

## v1.7-0 证据

- 端点: `久久`
- 模型: `qwen3.6-max-preview-nothinking`
- 题材组合: 玄幻黑暗 + 规则怪谈 + 末日多子多福
- 范围: 30 章真实生成，批次为 3 / 5 / 7 / 10 / 5
- 生成耗时: 初始化到第 30 章落盘约 48 分 40 秒
- 首次 drift: 第 4 批 10 连发，第 19 章
- 触发项: 第 19 章短章，第 24 章缺伏笔标记，第 25 章命中禁词 `叮`
- Jury 共识: `ioll-grok` 与 `ioll-mix` 均建议 recommended_batch_size=5、upper_bound=7

## 项目策略

- CLI 真实 LLM 多章/沉浸生成超过 7 章时 fail-loud。
- `ginga run --immersive` 未显式指定章节数时默认 5 章。
- mock harness 不受生产上限限制，用于边界和压力测试。
- 长篇 smoke 脚本默认 30 章，报告写入 production_policy 字段。

## 后续缺口

- v1.7-1 已把批后状态快照、回环检测、低频题材锚点检测和异常章 reviewer 队列接入 `ginga review` warn-only sidecar。
- v1.7-2 已把异常章 reviewer queue 先交外部模型评审，再生成供人工终审的 brief。
- 剩余缺口是不自动修文；异常章 reviewer 已有外部意见与人工 brief，但仍不调用 LLM 改正文、不写 `runtime_state`。
- 10 章压力测试结果保留为风险证据，不作为推荐生产路径。

## v1.7-1 正式 gate

- 入口: `ginga review <book_id>`
- 输出: `.ops/reviews/<book_id>/<run_id>/review_report.json`
- 固定边界: warn-only、`auto_edit=false`、不写 `runtime_state`、不调用 LLM
- 新增字段: `longform_quality_gate`
- 覆盖项:
  - `batch_state_snapshots`: 每 5 章生成状态快照与质量快照
  - `opening_loop_risk`: 检测疑似重新开篇 / 醒来模板回环
  - `missing_low_frequency_anchor`: 检测血脉、末日、多子多福、繁衍契约稀释
  - `short_chapter`: 检测短章
  - `missing_foreshadow_marker`: 检测伏笔标记缺失
  - `forbidden_style_hit`: 检测 `系统提示` / `叮` / `恭喜获得` 等禁词
  - `reviewer_queue`: 汇总需要人工或外部 reviewer 复核的异常章

v1.7-0 真实 30 章样本的 v1.7-1 gate 报告：`.ops/reviews/longform-jiujiu-combo-smoke/v1-7-1-longform-gate/`。

## v1.7-2 Reviewer Queue Review

已按“先外部模型评审，再人工终审”的流程处理 v1.7-1 `reviewer_queue`：

- 完整 queue 评审包：`.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_packet.md`
- 有效外部意见：`.ops/jury/longform_reviewer_queue_2026-05-15/ioll-grok__reviewer_queue_packet.md`
- 人工终审 brief：`.ops/jury/longform_reviewer_queue_2026-05-15/human_review_brief.md`

外部意见确认多章开头重复“痛觉 / 睁眼 / 灰白视野 / 天堑边缘 / 体内微粒 / 短刃”模板，P0/P1 优先聚焦第 19、24、25 章。该意见建议人工考虑把生产批量从“推荐 5 / 上限 7”临时收紧为“推荐 3-4 / 上限 5”，直到反回环 prompt、低频锚点覆盖和伏笔标记硬 gate 验证通过。

模型配置备注：

- 内容生成主端点仍是 `久久` / `qwen3.6-max-preview-nothinking`。
- 已新增评审别名 `jiujiu-jury` / `qwen3.6-max-preview-thinking`，但 2026-05-15 对 132KB 完整包、22KB 核心包、5.5KB P0 包均返回 HTTP 504；只保留为短输入手动 juror，不进入默认 `ask-jury-safe` 主力。
- `wzw` 本轮 wrapper 标 OK 但输出文件为空，不纳入有效共识。

## 证据文件

- `.ops/validation/longform_jiujiu_smoke.json`
- `.ops/reports/longform_jiujiu_smoke_report.md`
- `.ops/reports/longform_jiujiu_30_quality_summary.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/longform_jiujiu_30_review_packet.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-grok__longform_jiujiu_30_review_packet.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-mix__longform_jiujiu_30_review_packet.md`
- `.ops/reviews/longform-jiujiu-combo-smoke/v1-7-1-longform-gate/review_report.json`
- `.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/ioll-grok__reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/human_review_brief.md`
