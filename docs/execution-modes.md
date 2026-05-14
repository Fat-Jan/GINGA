# Execution Modes 最小边界

本页只用于快速区分 mock / real / future production 三类执行路径，避免把 demo harness 误认为生产编排。

## 1. Mock harness

- 入口：`CapabilityRegistry.from_defaults()` + `step_dispatch` unit / integration tests。
- 用途：验证 workflow step、capability id 解析、state_updates 写入等结构契约。
- 边界：所有 capability 是固定 stub / mock 输出；可证明管线形状正确，不代表真实创作质量，也不调用真实 LLM。

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
- 只有端到端演示、压力测试、质量抽样时才运行真实 `ask-llm`。
- 不要在普通验证脚本中默认调用真实 LLM；真实模型调用应由显式命令或参数触发。
