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

- 批后状态快照仍需产品化为正式 artifact。
- 回环检测、低频题材锚点检测和异常章 reviewer 还需接入正式 review gate。
- 10 章压力测试结果保留为风险证据，不作为推荐生产路径。

## 证据文件

- `.ops/validation/longform_jiujiu_smoke.json`
- `.ops/reports/longform_jiujiu_smoke_report.md`
- `.ops/reports/longform_jiujiu_30_quality_summary.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/longform_jiujiu_30_review_packet.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-grok__longform_jiujiu_30_review_packet.md`
- `.ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-mix__longform_jiujiu_30_review_packet.md`
