# v1.7-0 久久 30 章长篇生成质量汇总

## 结论

- 推荐一次生成: 5 章。
- 可接受上限: 7 章，但必须批后状态刷新和审稿。
- 不建议: 10 章连发；本轮第一次 10 连发即出现短章、伏笔缺失、禁词命中和语义回环。

## 版本定位

- 版本线: v1.7 Longform Production Policy。
- 证据版本: v1.7-0。
- 性质: 真实 LLM 长篇生产化策略 smoke，不是单章 demo，也不是正式连载内容。
- 项目动作: 正式真实 LLM 批量生成默认 5 章、上限 7 章；10 章及以上仅作为压力测试。

## 生成耗时

- 初始化到第 30 章落盘: 约 48 分 40 秒。
- 第 1 章正文落盘到第 30 章正文落盘: 约 47 分 07 秒。
- 平均正文落盘节奏: 约 1 分 34 秒 / 章。
- jury 评审: ask-jury-safe 两格约 49 秒；其中 wzw 文件为空，已补跑 ioll-mix 约 21 秒。

## 自动指标

- completed: 30/30
- drift_status: needs_review
- first_drift: ch19, batch4_size10
- short_chapters: [19]
- forbidden_hit_chapters: [25]
- missing_foreshadow_chapters: [24]
- anchor_totals: 无明 860, 短刃 448, 微粒 615, 天堑 130, 规则 78, 血脉 23, 末日 12

## 批次表现

| batch | chapters | avg_zh | min_zh | result |
| --- | --- | ---: | ---: | --- |
| 3 连发 | 1-3 | 3504.3 | 3246 | 稳定 |
| 5 连发 | 4-8 | 3372.4 | 3026 | 稳定 |
| 7 连发 | 9-15 | 3127.6 | 2679 | 可用但字数下滑 |
| 10 连发 | 16-25 | 3525.9 | 2367 | 首次 drift，出现短章/禁词/伏笔缺失/语义回环 |
| 5 章补跑 | 26-30 | 3537.2 | 2718 | 恢复稳定 |

## Jury 共识

- ioll-grok: 10 连发稳定性显著下降；recommended_batch_size=5，upper_bound=7。
- ioll-mix: 10 连发禁用；recommended_batch_size=5，upper_bound=7。
- wzw: ask-jury-safe 标记 OK，但落盘文件为空，未纳入有效共识。

## 必要检查

- 每批生成后写主线状态快照: 位置、目标、微粒余额、短刃状态、已知规则、记忆进度。
- 每章强制检查低频题材锚点: 血脉、末日、多子多福/繁衍契约。
- 检查首段回环: 醒来、睁开眼、天堑边缘、体内微粒、失忆刺客同时高频出现时暂停。
- 禁词、伏笔标记、字数阈值必须批后自动检查。

## 证据文件

- .ops/validation/longform_jiujiu_smoke.json
- .ops/reports/longform_jiujiu_smoke_report.md
- .ops/jury/longform_jiujiu_30_review_2026-05-15/longform_jiujiu_30_review_packet.md
- .ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-grok__longform_jiujiu_30_review_packet.md
- .ops/jury/longform_jiujiu_30_review_2026-05-15/ioll-mix__longform_jiujiu_30_review_packet.md
