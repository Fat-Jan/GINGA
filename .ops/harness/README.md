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

v2.2 CLI Harness Matrix 已确认：

- `scripts/run_agent_harness.py` 离线覆盖 `init`、单章 `run`、多章 `run`、`immersive`、错误退出、`review`、`inspect`、`query`、`market`、`observability workflow-stages`、`observability evidence-pack`、`observability migration-audit`、`model-topology observe`。
- 新增 sidecar / projection / observability case 均使用临时 `state_root` 同级 `.ops` 输出根，只写最终 `.ops/validation/agent_harness.json` 与 `.ops/reports/agent_harness_report.md` 作为汇总证据。
- `review`、`inspect`、`query` 必须证明只读 / report-only 边界；`market` 必须证明显式授权、offline fixture 和 raw_text 剥离；`observability` 必须证明不跑 workflow、不迁移文件、不写 `StateIO`；`model-topology` 默认不得 live probe。
- v2.2 仍是 `mock_harness` / `cli_report_only` 验证，不证明真实 LLM 生产质量。

v2.3 Real LLM Harness 已确认：

- `scripts/run_real_llm_harness.py` 固定真实 LLM preflight / postflight、成本边界、隔离输出和 review gate。
- 默认命令：`python3 scripts/run_real_llm_harness.py --dry-run --json-output .ops/validation/real_llm_harness.json --report-output .ops/reports/real_llm_harness_report.md`。
- 默认只 dry-run，不调用 ask-llm；真实运行必须显式 `--run`，且 preflight 必须通过隔离 `state_root`、批量上限、word target 和 review gate 检查。
- `longform-small-batch` 只允许小批隔离验证，默认 4 章，硬上限 5 章；6 章及以上仍只可作为压力测试，不得直接扩大生产批量。
- review gate 只读 `StateIO` 和章节 artifact，输出 warn-only `.ops/reviews/**` sidecar；若 hard gate 阻断下一批，只能作为停止信号，不能自动改正文或写 truth。

v2.4 Multi-Agent Harness 已确认：

- `scripts/validate_multi_agent_harness.py` 自动检查 `.ops/subagents/board.json` 的可解析性、顶层 `updated_at`、`tasks` 列表、任务必填字段、状态枚举、模型契约、写范围、`forbidden_files` 边界和 `done` 主控复核证据。
- 默认命令：`python3 scripts/validate_multi_agent_harness.py --json .ops/validation/multi_agent_harness.json --report .ops/reports/multi_agent_harness_report.md`。
- `done` 必须有非空 `evidence`，并且 `owner`、`handoff_note` 或 `evidence` 中体现 main-agent / 主控复核；子代理不能成为唯一 done 权威。
- write-capable / active 任务必须有 `model_contract.provider`、`model` 或 `model_tier`、`reason`、`fallback`；历史 `done` 任务缺新增契约时先作为 warning，不阻断当前看板验证。
- 触及 harness、agent、real LLM 或 model topology 边界的任务必须声明 `forbidden_files`。

v2.5 Stage Closeout Harness 已确认：

- `scripts/validate_stage_closeout.py` 检查 `.ops/harness/stage_closeout_template.md`，并可通过 `--commit-message` 机械检查阶段备份提交说明。
- 默认命令：`python3 scripts/validate_stage_closeout.py --json .ops/validation/stage_closeout_harness.json --report .ops/reports/stage_closeout_harness_report.md --commit-message "<stage update; verification; residual risk>"`。
- 模板必须覆盖 Objective、Scope、Truth Sync、Verification Summary、Residual Risks、Commit Message、Next Step，并显式提到 `STATUS.md`、`ROADMAP.md`、`notepad.md`、`.ops/validation/**`、`.ops/reports/**`。
- commit message 必须说明阶段更新内容、验证证据和剩余风险；live commit / push 仍需主控按当前 diff 白名单执行，不自动化。

## 后续扩展边界

- v2.3 / v2.4 / v2.5 均已接入 `scripts/verify_all.py` baseline；后续扩展要保持 dry-run 默认和独立证据落点。
