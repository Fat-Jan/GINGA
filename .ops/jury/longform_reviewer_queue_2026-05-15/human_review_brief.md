# v1.7-1 reviewer queue 人工终审 brief

> 流程：先外部模型评审，再交人工终审。本 brief 不改正文、不写 runtime_state。

## 外部评审执行结果

- 完整输入包：`reviewer_queue_packet.md`，21 个异常章，约 132KB。
- 有效外部意见：`ioll-grok__reviewer_queue_packet.md`，完整输出 6539 bytes。
- `jiujiu-jury`：已加入 ask-llm alias，模型 `qwen3.6-max-preview-thinking`；短探针能返回干净中文评审，但 132KB 完整包、22KB 核心包、5.5KB P0 包均 HTTP 504。本轮不把它作为有效 jury 结论。
- `wzw`：wrapper 标 OK 但输出文件 0 bytes，本轮不纳入有效共识。
- `jiujiu-jury__reviewer_queue_packet.md` 文件存在，但该格在完整包中触发 fallback 到 `ioll-mix`，署名不干净；只作为参考，不作为久久证据。

## 外部模型共识摘要

- 确认存在批量生成漂移：多章开头重复“痛觉/睁眼/灰白视野/天堑边缘/体内微粒/短刃”模板，像续写被误判为重新开篇。
- P0/P1 优先级集中在第 19、24、25 章：第 19 章短章且锚点缺失，第 24 章伏笔标记缺失，第 25 章禁词/系统播报腔命中。
- 外部意见认为 5 章推荐 / 7 章上限在当前样本上偏乐观；人工应重点判断是将上限临时收紧到 3-4，还是保留 5 章但增加每批状态锚点和开头反回环约束。

## 人工终审优先顺序

| Priority | Chapter | Why | Human decision needed |
|---|---|---|---|
| P0 | `chapter_19.md` | `short_chapter` + `opening_loop_risk` + 低频锚点缺失 | 是否从第 19 章重写，或回滚到第 18 章后重新续写 |
| P0 | `chapter_25.md` | `forbidden_style_hit`，命中“叮”，且开头回环、锚点缺失 | 是否丢弃并重写；禁词规则是否需要进入生成前约束 |
| P0 | `chapter_24.md` | `missing_foreshadow_marker` + 开头回环 | 是否补伏笔并修开头，还是整章重写 |
| P1 | `chapter_08.md`-`chapter_11.md` | 漂移起点区间 | 判断 drift 是否实际从 8 开始；决定是否把批量上限压到 7 以下 |
| P1 | `chapter_13.md`-`chapter_18.md` | 中段重复模板和锚点缺失 | 判断能否只修 prompt/state anchor，还是需要重写区间 |
| P1 | `chapter_20.md`-`chapter_30.md` | 后段持续回环，含 P0 章节 | 判断第 19 章后是否整体失控 |

## 人工裁决问题

1. 是否接受外部意见，把生产批量从“推荐 5 / 上限 7”临时收紧为“推荐 3-4 / 上限 5”，直到反回环 prompt 和状态锚点验证通过？
2. 是否将 `opening_loop_risk` 从 reviewer queue 提升为批后硬 gate：同一批内连续 2 章命中即停止下一批生成？
3. 是否把低频题材锚点做成每章/每批最小覆盖约束，而不是只在 review 后报警？
4. 是否要求每章必须带 `<!-- foreshadow: ... -->`，缺失则不进入下一批？

## 当前数据

- reviewer_queue_count: 21
- longform_gate_issue_count: 44
- low_frequency_anchors: 血脉, 末日, 多子多福, 繁衍契约
- batch_snapshots: 6

## 证据路径

- `.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_core_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_p0_mini_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/ioll-grok__reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/jiujiu-jury__reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/wzw__reviewer_queue_packet.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/summary.md`
- `.ops/jury/longform_reviewer_queue_2026-05-15/core_jiujiu/summary.md`
