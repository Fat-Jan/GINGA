# P2-7B Platform Runner 收敛侧车记录

生成日期：2026-05-15

更新：主 agent owner pass 已完成实现与验证；本报告下方保留初始侧车观察作为历史记录，最终结论以“Owner pass 后状态”为准。

## 范围

本记录沉淀 P2-7B runner 收敛的侧车观察、owner pass 后状态与验证口径。当前完成度仍以 `STATUS.md` 为准。

## Owner pass 后状态

- P2-7B 已完成到 asset-backed deterministic provider 层：`CapabilityRegistry.from_defaults()` 注册 12 个默认 capability，输出 `provider=asset-backed` / `asset_ref`。
- A-F/H/R1/R2/R3/V1 已从固定 stub 收敛为 provider；G 步仍优先经 `skill-router` + dark-fantasy adapter 写 `workspace.chapter_text`。
- R2 provider 的结构化 `audit_intents` 已由 `step_dispatch` 经 `StateIO.audit()` 落审计；provider 不通过 `state_updates` 写 `audit_log`。
- `STATUS.md`、`ROADMAP.md`、`notepad.md`、`ARCHITECTURE.md` 已同步到 P2-7B 完成口径，同时保留 mock harness 不等同真实 LLM production readiness 的边界。

已通过验证：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_asset_capability_providers ginga_platform.orchestrator.runner.tests.test_asset_capability_providers_af ginga_platform.orchestrator.runner.tests.test_capability_registry ginga_platform.orchestrator.runner.tests.test_integration_12step
python3 scripts/validate_architecture_contracts.py
python3 scripts/run_agent_harness.py
python3 scripts/verify_all.py
```

## 初始侧车观察（实现前）

以下内容是实现完成前的侧车审查记录，用于保留当时的风险面；不再代表当前完成度。

### 当时文档口径

- `STATUS.md`：当时停在 P2-7A，P2-7B 被定义为把 `demo_pipeline` 中 A-F/H/R1/R2/R3/V1 的 stub capability 替换为 asset-backed capability provider，并保持 workflow DSL + skill adapters + `StateIO` 统一编排。
- `ROADMAP.md`：当时已把 P2-7A 标为完成，P2-7B 还在规划区；文件本身声明为历史/规划资料，不应反压 `STATUS.md`。
- `notepad.md` Priority Context：与 `STATUS.md` 一致，当前阶段止于 P2-7A；下一步是 P2-7B。
- `ARCHITECTURE.md`：§4.4 给的是目标架构：MVP 12 step 使用资产 id，G 步走 `skill-router`；附录当前实施状态止于 P2-7A，尚未加入 P2-7B 完成表述。
- `AGENTS.md`：当前主线已经指向 P2-7 Platform runner 收敛，并明确 mock 结果不得声明 production path 完成。

### 当时代码 / 验证观察

- `ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml` 已为 12 step 配置 `uses_capability`，G 步同时保留 `uses_capability: base-card-chapter-draft` 与 `uses_skill: skill-router`。
- `ginga_platform/orchestrator/registry/capability_registry.py` 仍自称 `from_defaults()` 是 mock harness / backward-compatible test registry，并明确写着未来 production path 应替换为 asset-backed capability providers。
- `ginga_platform/orchestrator/cli/demo_pipeline.py` 的 `_workflow_step_dispatch()` 已开始传入 `CapabilityRegistry.from_defaults()`，H/R1/R2/R3/V1 不再只是完全空 registry 的 noop fallback；但 `CapabilityRegistry.from_defaults()` 当时还是固定 stub 输出。
- 工作树中已有 P2-7B 方向的验收测试改动：`ginga_platform/orchestrator/runner/tests/test_capability_registry.py` 要求 provider 返回 `asset_ref`、`provider=asset-backed`，并要求 A 步读取运行参数；`ginga_platform/orchestrator/runner/tests/test_asset_capability_providers.py` 要求 `asset_providers` 暴露 H/R provider、capability id 常量，并指向 capability asset 文件。这些测试已在 owner pass 后转绿。

已运行的目标检查：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_capability_registry
```

结果：失败。关键失败点：

- `base-card-chapter-draft` 输出缺少 `asset_ref`，且没有 `provider=asset-backed`。
- `base-methodology-creative-brainstorm` 输出的 `retrieved.brainstorm` 缺少 `topic`，说明 A 步仍未按新测试消费本次运行参数。

追加检查：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_capability_registry ginga_platform.orchestrator.runner.tests.test_asset_capability_providers
```

结果：失败。除上述两点外，`test_asset_capability_providers` 当前因 `ImportError: cannot import name 'H_CHAPTER_SETTLE_ID' from 'ginga_platform.orchestrator.registry.asset_providers'` 无法加载；`asset_providers.py` 已出现，但目前未暴露测试要求的 H/R provider 符号，asset-backed provider 面尚未合拢。

## P2-7B 真值同步结果

### STATUS.md

已同步“已完成”表述：

> P2-7B Platform runner 收敛已完成：A-F/H/R1/R2/R3/V1 的默认 capability 已由固定 stub 收敛为 asset-backed provider；单章 mock harness 路径可经 workflow DSL 解析 capability asset id，provider 输出 `asset_ref` / `provider=asset-backed`，并通过 `StateIO` 写入允许的 state 域；G 步继续经 `skill-router` + dark-fantasy adapter 写 `workspace.chapter_text`。

已把“下一步”中的 P2-7B 待办移除，并改为后续观察项：

> 后续主线转入 provider 质量与真实 LLM demo 小范围验证；mock harness 仍只证明离线编排与写入边界，不证明真实生产质量。

最近主线程结果已补充：

> P2-7B runner 收敛：capability provider 契约测试通过，provider metadata 可审计；agent harness 继续覆盖 init / single run / multi_chapter / immersive / missing_state_error。

### ROADMAP.md

已把 P2-7B 勾选为完成，并保留历史性质说明：

> [x] **P2-7B**：Platform runner 收敛完成：`demo_pipeline` 剩余 A-F/H/R1/R2/R3/V1 简化能力已替换为 asset-backed capability provider，provider 输出带 `asset_ref` / `provider=asset-backed`，真实路径继续向 workflow DSL + skill adapters + `StateIO` 收拢。

顶部进度摘要已从“下一步主线是 P2-7B”改成“P2-7B 已完成，下一步以 `STATUS.md` 为准”。

### notepad.md

Priority Context 的当前阶段已追加 P2-7B 完成，并把下一步改成最新主线：

> + **P2-7B Platform runner 收敛完成 ✅**；当前 runner 真实路径已从 P2-7A 的 G 步切片扩展到 12 step capability provider 契约，mock harness 仍只作为离线回归门。

主验证命令段保持 `verify_all.py` + `run_agent_harness.py`，provider gate 已通过本报告记录。

### ARCHITECTURE.md

§4.2 / §4.4 未大改目标架构；附录 C 当前实施状态已补充为：

> ... + P2-7A/P2-7B Platform runner 收敛已完成。当前 12 step capability provider 契约已落地，mock harness 仍不等同于真实 LLM production readiness。下一步以 `STATUS.md` 为准。

## Gate 建议

### 最小 gate（P2-7B 完成当轮必须跑）

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_capability_registry
python -m unittest ginga_platform.orchestrator.runner.tests.test_integration_12step
python3 scripts/validate_architecture_contracts.py
python3 scripts/run_agent_harness.py
```

验收重点：

- 12 个默认 capability id 全注册。
- provider 输出含 `result`、`state_updates`、`asset_ref`、`provider=asset-backed`。
- A 步读取本次运行 `params.topic` / `params.premise`，不再固定 demo 文案。
- 单章 mock harness 仍有 G 步 `skill-router`、dark-fantasy adapter、V1 dispatch 审计。
- 所有 state 写入仍经 `StateIO`，章节正文仍作为 `chapter_text` artifact 或 `workspace.chapter_text`，不绕写 YAML state。

### 完整 gate（真值文件更新前建议跑）

```bash
python3 scripts/verify_all.py
python3 scripts/run_agent_harness.py
python3 scripts/verify_all.py --include-pressure --include-rag-eval
```

说明：

- `verify_all.py` 默认 quick gate 不包含 agent harness，也不包含 pressure / RAG eval；P2-7B 收口时必须单独跑 `scripts/run_agent_harness.py`。
- RAG 指标不是 P2-7B 的直接完成条件，但真值文件更新前跑 `--include-rag-eval` 可防止 runner 改动意外影响召回链路。
- 真实 LLM demo 不属于常规轻量 gate；如需验证，应单独说明 endpoint、成本、输入 book、输出路径和不会覆盖的文件。

## 初始结论（已被 owner pass 更新）

实现前不应宣称 P2-7B 已完成。当前 owner pass 已把 provider 契约、CLI/harness 覆盖和最小 gate 跑通，并已统一同步 `STATUS.md`、`ROADMAP.md`、`notepad.md` 与 `ARCHITECTURE.md`。
