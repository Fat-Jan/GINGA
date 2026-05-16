# Agent 入口说明

给未来 agent 的短入口：先确认当前事实，再动代码。Ginga 的 Harness Engineering 目标是让 agent 通过仓库内真值、可执行验证和清晰边界独立推进任务；`AGENTS.md` 只做目录和红线，不做百科全书。当前下一步以 `STATUS.md` 为准。

## 先读顺序

1. `AGENTS.md`：本入口，确认边界和禁区。
2. `STATUS.md`：当前状态真值，优先级高于旧路线图。
3. `notepad.md` 的 `Priority Context`：读项目背景、最近主线程结论和坑点。
4. `ARCHITECTURE.md` 相关章节：按任务只读相关层级、状态、RAG、workflow 或 Meta 章节。

## 当前权威状态

- `STATUS.md` 是当前状态真值。
- `ROADMAP.md` 是历史/规划资料，不代表最新完成度；里面的待办状态可能已经过期。
- `ARCHITECTURE.md` 是架构权威，但完成度与下一步以 `STATUS.md` 为准。
- `.ops/validation/**` 和 `.ops/reports/**` 是验证证据与阶段报告落点。
- `.ops/governance/candidate_truth_gate.md` 定义 `candidate-only`、`report-only`、`truth` 晋升边界。
- `.ops/subagents/**` 是多 agent 调度、模型契约、验收清单和看板边界。

## Harness Engineering 工作法

- 人负责目标、优先级、取舍和验收；agent 负责代码、测试、文档、脚本、报告和收口。
- `AGENTS.md` 必须短而稳定：只写入口、路由、红线和默认反馈回路；细节沉到 `STATUS.md`、`ARCHITECTURE.md`、`docs/`、`.ops/`、schema、测试和脚本。
- 每个非平凡任务先确定验收标准和最短反馈命令；无法验证的要求先转成脚本、测试、schema、报告或 `.ops` 计划。
- 失败不是“再试一次”的理由；先定位缺的是工具、边界、文档、fixture、validator 还是观测面，再把补强写回仓库。
- 任务产物必须 agent-legible：状态、计划、决策、风险、验证证据和剩余问题都能从仓库文件复原，不依赖聊天记录。
- 只约束架构边界和可验证品味，不微管实现细节；能用脚本检查的规则不要靠提示词反复提醒。
- 大任务用小切片推进：计划 / 实现 / 验证 / 文档同步 / 备份点分开收口，避免一个 agent 长时间在无证据状态下漂移。
- 高吞吐不等于放松边界：可以接受短周期修正，但不得跳过 `StateIO`、污染隔离、truth gate、真实 LLM 成本边界或验证证据。

## 收尾输出规则

- 每次完成阶段性任务、修复、验证或文档同步后，最终汇报必须包含“下一步计划”或“下一步任务计划”。
- 下一步必须先从 `STATUS.md` 当前真值推导；若本轮刚更新过 `STATUS.md`，以更新后的内容为准。
- 下一步计划要区分 `done`、`deferred`、`observation` 和真正可开工的任务，避免把规划项说成已可直接执行。
- 若下一步存在红线或前置条件，必须一并写出；例如 v1.3-4 Promote Flow 需要人工审核 + 污染检查，不得把 pending candidate 自动写入 Foundation、默认 RAG、prompt、`raw_ideas` 或 `StateIO`。

## 反馈回路与证据落点

- 代码 / workflow / CLI 改动：优先跑相关 unit test，再跑 `python3 scripts/run_agent_harness.py` 和 `python3 scripts/verify_all.py`。
- 架构边界 / StateIO / sidecar / truth gate 改动：必须跑 `python3 scripts/validate_architecture_contracts.py`。
- prompt / methodology / RAG 改动：跑对应 validator，并把 JSON / Markdown 证据写回 `.ops/validation/**` 与 `.ops/reports/**`。
- 真实 LLM 只做显式小范围验证：默认 dry-run；真实调用必须说明模型、范围、成本边界、输出目录和不覆盖哪些文件。
- 文档或状态同步也要验证：至少重读相关段落，确认 `STATUS.md`、`ROADMAP.md`、`notepad.md` 与实际证据不互相冲突。
- 若验证发现 warning 噪音、过期报告或不可复现命令，优先把它们当作 Harness 缺口修掉，再宣称阶段完成。

## 阶段性备份规则

- 每完成一个阶段性任务并通过对应验证后，优先把本阶段代码、报告、验证产物和真值文件提交并推送到 GitHub，形成可回滚备份点。
- 提交前先同步 `STATUS.md` / `ROADMAP.md` / `notepad.md` / `ARCHITECTURE.md` 等真值文件；不要让提交只包含代码而遗漏状态更新。
- Commit message 必须写明本阶段更新内容、验证命令和剩余风险；不要用“更新一下”这类不可追溯描述。
- 若工作树里有与本阶段无关的用户改动，保持隔离，不要擅自回滚；只 stage 本阶段需要备份的文件。

## 核心架构边界

- 四层边界：Meta / Foundation / Platform / RAG。
- Meta：创作宪法、guard、checker；checker 结果只做审计，不注入 prompt。
- Foundation：schema、资产、runtime_state、raw_ideas 等数据本体。
- Platform：Orchestrator + Skill Runtime，负责 workflow、adapter、CLI 和状态流转。
- RAG：召回、向量索引、rerank 和上下文适配。
- `StateIO` 是 `runtime_state` 唯一写入口。任何 workflow、skill adapter、CLI、测试辅助都必须经过它或现有封装路径写状态。

## 常用验证命令

优先统一入口：

```bash
python3 scripts/verify_all.py
```

现有分项命令：

```bash
python -m unittest discover -s ginga_platform -p "test_*.py"
python3 scripts/validate_harness_contracts.py
python3 scripts/validate_architecture_contracts.py
python3 scripts/validate_prompt_frontmatter.py --strict
python3 scripts/report_prompt_quality.py foundation/assets/prompts
python3 scripts/validate_methodology_assets.py foundation/assets/methodology foundation/schema/methodology.yaml
python3 scripts/run_agent_harness.py
python3 scripts/check_dedup_evidence.py --strict
python3 scripts/run_s3_pressure_tests.py
python3 scripts/evaluate_rag_recall.py
```

真实 LLM demo 不属于轻量验证；除非用户明确要求，不要在常规收口里跑长时间真实调用。

## 禁止事项

- 不要绕过 `StateIO` 写 `foundation/runtime_state/`。
- 不要把 `foundation/raw_ideas/` 纳入 state 或 RAG；它是灵感逃逸通道，只落盘暂存。
- 不要把 guard/checker 内容或审计结果注入 prompt。
- 不要把 mock demo 当生产路径，也不要用 mock 结果声明真实生产链路已完成。
- 不要把 `ROADMAP.md` 的旧待办当作当前完成度事实。

## 真实 LLM 调用

- 单章/多章 CLI 会调用 `ask-llm`，可能产生真实成本、耗时和外部依赖波动。
- 测试应 mock LLM，或使用仓库已有测试路径与固定产物验证。
- 需要验证真实 LLM 行为时，先说明范围、输入、预计产物和不会覆盖的文件。
