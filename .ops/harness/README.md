# Ginga Harness Map

本文件是 v2.0 Harness Map。目标是让后续 agent 先按任务类型找到真值、边界、最短验证命令和证据落点，再动代码。

## 总原则

- `STATUS.md` 是当前状态真值；`ROADMAP.md` 是历史和规划，不直接代表完成度。
- `AGENTS.md` 是短入口；细节放在本文件、`.ops/governance/**`、schema、测试和脚本里。
- `scripts/validate_harness_contracts.py` 是 v2.1 自检入口，必须被 `scripts/verify_all.py` 调用。
- `.ops/validation/**` 存机器可读验证结果；`.ops/reports/**` 存人类可读报告。
- `candidate-only` 与 `report-only` 产物不得进入默认 RAG、workflow prompt、provider input 或 `StateIO`。
- 真实 LLM 调用必须显式声明范围、模型、成本边界、隔离输出目录和不会覆盖的文件。

## 任务类型地图

| task_type | 先读 | 禁区 | 最短反馈 | 证据落点 |
|---|---|---|---|---|
| `docs_or_status` | `STATUS.md`、`AGENTS.md`、本文件 | 不把规划项写成 `done` | `python3 scripts/validate_harness_contracts.py`、重读改动段落 | `.ops/reports/**` 或对应 truth file diff |
| `architecture_boundary` | `ARCHITECTURE.md`、`.ops/governance/candidate_truth_gate.md` | 不绕过 `StateIO`，不把 sidecar 变 truth | `python3 scripts/validate_architecture_contracts.py` | `.ops/validation/**`、`.ops/reports/**` |
| `cli_or_workflow` | `AGENTS.md`、`scripts/run_agent_harness.py`、workflow DSL | 不用 mock 结果声明真实生产可用 | 相关 unit test、`python3 scripts/run_agent_harness.py` | `.ops/validation/agent_harness.json`、`.ops/reports/agent_harness_report.md` |
| `rag_or_prompt` | `foundation/rag/recall_config.yaml`、prompt / methodology validators | 不索引污染源，不把 report-only 注入 prompt | prompt / methodology / RAG validator | `.ops/validation/**`、`.ops/reports/**` |
| `sidecar_or_observability` | 对应 `.ops/**` 边界文档、`candidate_truth_gate.md` | 不写 `StateIO`，不自动改正文，不接管 workflow | 对应 unit test、`validate_architecture_contracts.py` | `.ops/reviews/**`、`.ops/model_topology/**`、`.ops/workflow_observability/**` |
| `real_llm_policy` | `STATUS.md` v1.7 / v1.9 观察项、真实 LLM 脚本 | 不扩大批量，不覆盖现有 state，不把 smoke 当 production | dry-run；真实调用前后跑 review / quality gate | `.ops/validation/*llm*.json`、`.ops/reports/*llm*.md` |
| `subagent_coordination` | `.ops/subagents/dispatch-protocol.md`、`.ops/subagents/board.json` | 子代理不写 `done`，写范围不重叠 | board / task contract 人工复核，后续接 validator | `.ops/subagents/board.json`、`.ops/reports/**` |

## 自检覆盖

v2.1 Harness self-check 必须确认：

- `AGENTS.md` 包含 Harness Engineering、truth source、验证证据、`StateIO` 和真实 LLM 边界。
- 本文件包含 `task_type`、`docs_or_status`、`architecture_boundary`、`cli_or_workflow`、`rag_or_prompt`、`sidecar_or_observability`、`real_llm_policy`、`subagent_coordination`。
- `scripts/validate_harness_contracts.py` 存在，并被 `scripts/verify_all.py` 的 baseline 命令调用。
- 本文件明确 `.ops/validation/**`、`.ops/reports/**`、`candidate-only`、`report-only` 与 `truth` 的证据 / 晋升边界。

## 后续扩展边界

- v2.2 再扩 CLI harness matrix，不在 v2.0 / v2.1 里一次性做完。
- v2.3 再统一真实 LLM preflight / postflight。
- v2.4 再做多 agent board / task contract 自动检查。
- v2.5 再做阶段收口模板与 commit message 机械检查。
