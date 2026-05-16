# Ginga 文档地图

本页用于按状态归类项目文档。除非特别说明，路径都按仓库根目录解释。

## 当前入口和真值

- `README.md`：人类入口。
- `AGENTS.md`：agent 入口、边界、验证命令和禁区。
- `STATUS.md`：当前状态真值；优先级高于 `ROADMAP.md`。
- `notepad.md`：续接笔记和 Priority Context；应跟随 `STATUS.md` 同步。

## 架构和稳定边界

- `ARCHITECTURE.md`：架构权威；完成度和下一步仍以 `STATUS.md` 为准。
- `docs/execution-modes.md`：mock / deterministic eval / real LLM demo / future production 的执行边界。
- `.ops/governance/candidate_truth_gate.md`：candidate-only / report-only / truth 晋升规则。
- `.ops/subagents/dispatch-protocol.md`：子代理调度协议。
- `.ops/book_analysis/contamination_check_rules.md`：拆书污染隔离规则。
- `.ops/book_analysis/p0_mvp_boundary.md`：拆书 P0 MVP 边界。

## 规划和历史状态

- `ROADMAP.md`：历史规划和版本对照；不作为当前完成度真值。
- `.ops/plans/`：仍作为任务规格和计划证据目录保留，不迁入 `docs/`。
- `docs/archive/_distillation-plan.md`：阶段 2 蒸馏草案历史档案。
- `.ops/archive/`：已收口的 Codex handoff / prompt 历史档案。
- `.ops/p7-handoff/`、`.ops/p7-prompts/`：P7 阶段历史交接和派发 prompt。
- `.ops/scout-prompts/`、`.ops/scout-reports/`：早期 scout 输入和报告。

## 报告和验证产物

- `.ops/reports/`：生成报告和决策报告；大量 truth 文件引用这里，保持原路径。
- `.ops/validation/`：验证 JSON / txt 产物；保持原路径。
- `.ops/reviews/`：`ginga review` warn-only sidecar 报告。
- `.ops/model_topology/`、`.ops/migration_audit/`、`.ops/workflow_observability/`：report-only 观察产物。

## Jury 和候选证据

- `.ops/jury/`：外部模型评审、人工 brief、evidence pack 和候选证据；默认不进入 truth、prompt 或 RAG。
- `.ops/jury-prompts/`：jury prompt 模板。
- `.ops/book_analysis/`：拆书 sidecar / candidate / generated evidence；这是污染源边界，不迁移。

## 外部原料和运行样本

- `_原料/`：原始材料，保持独立只读原料域。
- `.ops/longform_smoke/`、`.ops/real_llm_demo/`：真实 LLM 样本和隔离 state root。
- `foundation/runtime_state/`：demo/runtime state 真值样本，只能经 `StateIO` 或既有封装写入。

## 归档原则

- 根目录只保留入口、真值、架构和路线图。
- `.ops/reports/`、`.ops/validation/`、`.ops/jury/`、`.ops/book_analysis/` 是证据边界，不为了好看移动。
- 历史手工交接和已废弃 prompt 进入 `.ops/archive/`。
- 历史设计草案进入 `docs/archive/`，但正文内路径仍按仓库根目录解释。
