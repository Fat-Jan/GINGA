# v3.0 Agent Interface 规划

## 目标

把 Ginga 封装为 Claude Code 和 Codex 都能直接使用的创作智能体，通过 CLI 子命令 + agent contract 文件实现，不依赖 MCP 或 SDK。

## 触发条件（全部满足才启动实现）

1. v1.7-7 style warn 自动路径落地且单章复验通过
2. 连续 2 轮 4 章真实批量不触发 hard gate 阻断（证明底层接口语义已收敛）
3. 模型端稳定（久久 504 问题解决，或 fallback 端点确认可用）
4. 补长 / 开篇修复 / style warn rewrite 已纳入可审计自动流程

## 设计概要

### 三层架构

```
Layer 3: GINGA_AGENT.md (agent contract)
  → 告诉 AI agent 身份、能力、决策规则、禁区
  → Claude Code 通过 CLAUDE.md 引用，Codex 通过 AGENTS.md 引用

Layer 2: ginga agent <command> (新增 agent 子命令)
  → 对 agent 友好的 JSON 输出 + 高层编排命令
  → 内部调用现有 CLI，封装 gate 检查 / retry / diagnose 逻辑

Layer 1: 现有 ginga CLI (不改动)
  → init / run / review / inspect / query / market
```

### Layer 2 命令清单

| 命令 | 作用 | 输出格式 |
|---|---|---|
| `ginga agent status` | 当前书完整状态摘要 | JSON：章节数、gate 状态、阻塞项、下一步建议 |
| `ginga agent next` | 写下一章（自动 gate + retry） | JSON：成功/失败 + 章节路径 + review 摘要 |
| `ginga agent batch N` | 连续写 N 章（immersive） | JSON：每章结果 + drift 报告 |
| `ginga agent diagnose` | 分析当前阻塞原因 | JSON：问题列表 + 建议修复动作 |
| `ginga agent repair` | 执行自动修复 | JSON：修复结果 + 是否可继续 |
| `ginga agent review` | 最近批次质量审查 | JSON：review 摘要 + hard gate 状态 |
| `ginga agent plan` | 输出创作计划 | JSON：已完成、剩余规划、风险项 |

### Layer 3: Agent Contract 核心内容

- 身份：Ginga 小说创作系统操作者
- 工作流：status → next/batch → review → diagnose → repair 循环
- 决策规则：hard gate 阻断先 diagnose、drift=needs_review 停手报告、连续 2 次同类失败停手
- 禁区：不直接改 YAML state、不跳过 hard gate、不把污染源喂 prompt、不超 5 章批量

### 为什么选 CLI 而不是 MCP/SDK

- Codex 不支持 MCP
- CLI 是松耦合：底层 demo_pipeline 怎么改，只要 `ginga agent next` 的输入输出契约不变，上层不用动
- 零额外进程、零配置，任何能跑 bash 的 AI agent 都能用
- 后续加新功能只需加新子命令，不需要重新封装已有命令

## 实现路径（触发条件满足后）

1. 新增 `ginga_platform/orchestrator/cli/agent_commands.py`（~200-300 行）
2. 在 `__main__.py` 注册 `agent` 子命令组
3. 新增 `GINGA_AGENT.md`（agent contract）
4. 在 `AGENTS.md` 和项目 `CLAUDE.md` 引用 contract
5. 补 agent 子命令的 unit test + 接入 `verify_all.py`

## 不做什么

- 不改现有 CLI 接口
- 不引入 MCP server 进程
- 不引入新的外部依赖
- 不在底层未稳定前提前实现

## 风险

- 底层接口语义如果持续变化，agent 子命令的 retry/fallback 逻辑需要跟着调整
- 模型端如果长期不稳定，agent 层的自动化程度会受限（需要更多人工介入点）
- JSON 输出契约一旦发布给外部 agent 使用，变更成本会升高——所以要等底层稳定再定义

## 状态

`planned` — 等待触发条件满足
