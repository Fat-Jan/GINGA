# Execution Modes 最小边界

本页只用于快速区分 mock / real / future production 三类执行路径，避免把 demo harness 误认为生产编排。

## 1. Mock harness

- 入口：`scripts/run_agent_harness.py`；底层调用 `ginga init` / `ginga run --mock-llm` / `ginga run --chapters ... --mock-llm` / `ginga run --immersive ... --mock-llm`。
- 用途：验证 CLI 退出码、临时 `state_root`、`StateIO` state 域、audit_log、chapter artifacts、错误路径；也覆盖 workflow step / capability id / state_updates 的 unit / integration tests。
- 边界：章节正文是固定 mock 输出；可证明管线形状和写入边界正确，不代表真实创作质量，也不调用真实 LLM。
- 报告：`.ops/validation/agent_harness.json` + `.ops/reports/agent_harness_report.md`，必须保留 `mock_harness does not prove production readiness` 声明。

## 1.5 Deterministic eval

- 入口：`scripts/evaluate_rag_recall.py`。
- 用途：用真实资产 + 本地 deterministic embedder 评估 RAG 召回质量漂移。
- 边界：这是离线 deterministic eval，不是 mock LLM demo，也不是生产级语义 embedding。

## 2. CLI real LLM demo

- 入口：`ginga init` / `ginga run`、`multi_chapter.py`、`immersive_runner.py`。
- 用途：通过 `ask-llm` 跑真实模型，适合端到端演示、章节滚动验证和压力测试。
- 边界：这是 real LLM demo path，部分 wire-up 保持简化；单章 `demo_pipeline` 仍不等于完整 workflow DSL production runner。

## 3. Future production path

- 目标：由 workflow DSL + skill adapters + StateIO + RAG hook 统一编排。
- 方向：把 capability provider 收拢为 asset-backed 实现，并进一步收拢 `demo_pipeline` 的简化路径。
- 当前状态：生产路径尚未完全成形，不能把 mock harness 或单章 demo 直接标记为 production runner。

## 推荐默认

- 普通测试和验证默认使用 mock harness。
- RAG 指标报告默认标记为 deterministic eval。
- 只有端到端演示、压力测试、质量抽样时才运行真实 `ask-llm`。
- 不要在普通验证脚本中默认调用真实 LLM；真实模型调用应由显式命令或参数触发。
