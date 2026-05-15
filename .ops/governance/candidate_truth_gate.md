# Candidate Truth Gate

日期：2026-05-16

本文件是 v1.8-1 的治理真值：统一 Ginga 里 `candidate-only`、`report-only` 与 `truth` 的边界语言。它只定义门禁术语，不新增 runtime 写入链。

## 三类输出

| 类别 | 定义 | 默认落点 | 允许用途 | 禁止事项 |
|---|---|---|---|---|
| `candidate-only` | 可以被人工评审的候选，不代表当前事实 | `.ops/**` candidate / sidecar；promote 前的候选文件 | 等待 `operator_accept`、污染检查、schema validation、人工备注 | 不写 `runtime_state`，不进入默认 RAG，不进入创作 prompt，不当成事实给 workflow |
| `report-only` | 只读分析、审稿、jury、市场、model topology 或质量报告 | `.ops/reports/**`、`.ops/reviews/**`、`.ops/jury/**`、`.ops/market_research/**`、`.ops/model_topology/**` | 提供证据、风险、建议、人工裁决材料 | 不自动改正文，不写 `StateIO`，不进入默认 RAG，不反向注入 prompt |
| `truth` | 当前创作运行真值或白名单 Foundation 资产 | `foundation/runtime_state/**` 经 `StateIO`；`foundation/assets/**` 经对应 validator | 作为 workflow / RAG / provider 的可信输入 | 不接受 LLM 自由文本直写，不接受未审核 candidate，不接受 report 直接 promotion |

## 晋升规则

任何候选从 `candidate-only` 进入 `truth`，必须同时满足：

1. `operator_accept`：人工明确接受，不能由 LLM 或 validator 代签。
2. `schema_validation`：目标 truth surface 的 schema / validator 通过。
3. `source_contamination_check`：涉及外部作品、市场资料、jury 原文或 Genm 参考时，必须证明无原文污染。
4. `StateIO_or_validator_entrypoint`：写 `runtime_state` 必须经 `StateIO`；写 `foundation/assets/**` 必须经对应 promote / asset validator。
5. `audit_evidence`：必须留下可追踪证据，说明来源、裁决人、校验命令和目标落点。

任一条件缺失时，状态保持 `candidate-only` 或 `blocked`。

## Report 边界

`report-only` 产物永远不是 truth。以下目录默认只提供证据或建议：

- `.ops/reports/**`
- `.ops/reviews/**`
- `.ops/jury/**`
- `.ops/market_research/**`
- `.ops/book_analysis/**`
- `.ops/model_topology/**`

这些产物可以被人读，可以生成后续任务，但不得被默认 RAG、workflow prompt、provider input 白名单自动消费。Rule marker: report-only outputs must not enter default RAG. 需要吸收时，必须先转成 `candidate-only`，再走晋升规则。

## Default RAG 边界

默认 RAG 只能读取已经治理的洁净资产。以下内容不得进入 default RAG：

- `candidate-only` 候选。
- `report-only` 报告。
- `.ops/book_analysis/**`、`.ops/market_research/**`、`.ops/external_sources/**`。
- jury 原文、外部榜单原文、Genm `基座/` 或 `Example writing style/` 原文。
- 未通过 `operator_accept` 与污染检查的 promoted 候选。

显式 sidecar RAG 只能作为 opt-in evidence surface，不改变 default RAG 边界。

## 当前映射

| 能力 | 当前分类 | 可晋升路径 |
|---|---|---|
| `trope_recipe_candidate` | `candidate-only` | `human_review_status=approved` + `source_contamination_check=pass` + `promote_trope_recipes.py` + promoted asset validator |
| `ginga review` / longform quality gate | `report-only` | 人工裁决后另开 candidate 或代码任务；报告本身不写 truth |
| `ginga market` | `report-only` | 人工提炼为 methodology candidate，不能复制 raw_text |
| `ginga model-topology observe` | `report-only` | 后续 router 任务必须另走设计、测试、probe 证据和架构验证 |
| `foundation/raw_ideas/**` | raw idea / escape hatch | 人工整理为 candidate；不能直接进入 RAG 或 StateIO |

## Validator 口径

架构验证必须能检查到这些固定词：

- `candidate-only`
- `report-only`
- `truth`
- `operator_accept`
- `schema_validation`
- `source_contamination_check`
- `StateIO`
- `default RAG`
- `.ops/model_topology/**`
- `.ops/book_analysis/**`
