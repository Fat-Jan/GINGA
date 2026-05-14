# Ginga 小说系统蒸馏项目

## Priority Context（开新会话先读这一段）

- 项目目标：把 `_原料/` 蒸馏成一个**分层**的小说创作系统底座，不是堆成单一 RAG。
- 四层目标：**Meta（用户宪法）→ Foundation（数据本体）→ Platform（agent + workflow）→ RAG（检索）**。
- **当前阶段**：阶段 0..4 全部完成 ✅ + **Sprint 1 全部完成 ✅** + **Sprint 2 全部完成 ✅** + **Sprint 3 全部收口 ✅** + **S4/Phase 2 native sqlite-vec 接入 + RAG 真实召回质量评估完成 ✅** + **P2 可回归评估收口 ✅** + **RAG 质量小迭代完成 ✅** + **P2-5 agent harness 补强完成 ✅**；当前 Layer 2 `recall@5=0.614`、`expected_recall@5=0.917`。下一步主线：以 agent harness 作为回归门，收敛真实 runner 到 workflow DSL + skill adapter + StateIO 统一编排。
- 最终架构：`ARCHITECTURE.md` v1（36.5KB / 8 章节 + Killer Use Case + 8 决策最终判决 + Jury 判决归属表 23 条）
- 实施路线：`ROADMAP.md` v1（已补 2026-05-14 状态更新；历史规划 + 当前状态对照）
- **Sprint 2 进度（2026-05-14 02:35 收口复核）**：
  - ✅ ST-S2-PHASE0（capability_registry + op_translator + 12 step integration，33 tests PASS）
  - ✅ ST-S2-R-RAG-LAYER1（RAG Layer 1，53 tests PASS）
  - ✅ ST-S2-I-IMMERSIVE（I-1..I-5 + 真实 LLM 5 章沉浸 demo，16 tests + audit_log 全证据 PASS；产物 `foundation/runtime_state/immersive-demo/chapter_01..05.md` 13-19K bytes 每章）
  - ✅ ST-S2-S-MULTI-CHAPTER（S-1..S-5 + 真实 LLM 5 章 demo PASS；产物 `foundation/runtime_state/s2-demo/chapter_01..05.md`，`total_words=15245`，`foreshadow_pool=5`）
  - ✅ ST-S2-L-ANNOTATION（461/461 prompt cards 标注完成；`annotation-progress.jsonl` 中 `status=ok` = 461，`foundation/assets/prompts/prompts-card-*.md` = 461）
- **Sprint 2 关键代码新增**：
  - `ginga_platform/orchestrator/cli/multi_chapter.py`（266 行）：R1/R2/R3 + V1 DoD + run_multi_chapter runner
  - `ginga_platform/orchestrator/cli/locked_patch.py` + `meta/patches/_template.patch.yaml`：locked 域 patch CLI
  - `ginga_platform/orchestrator/cli/immersive_runner.py` + adapter 沉浸 enter/exit + checker_invoker silenced hook
  - **重要 bug 修复（A3 防陷阱）**：`state_io.py` 把模块级常量 `_DEFAULT_STATE_ROOT` 改成函数 `_default_state_root()` + lazy lookup，杜绝"Python 默认参数绑定 + mock.patch 模块属性失效"陷阱；同步改了 2 处测试 mock 路径
- **Sprint 3 收口完成（2026-05-14 复核）**：
  - ✅ ST-S3-R-LAYER23：Layer 2 native sqlite-vec 向量召回 + Layer 3 rerank fail-open；`rag/layer2_vector.py` / `rag/reranker.py` / `rag/retriever.py`；`SQLiteVecBackend` native vec0 integration test 真跑通过（不再 skip）
  - ✅ ST-S3-Q-PROMPT-AUDIT + ST-S3-Q-PROMPT-SCHEMA-FIX：461 prompt frontmatter strict 校验 `0 violations`
  - ✅ ST-S3-M-METHODOLOGY-ASSETS：12 methodology assets + 1 schema-ref asset；validators PASS；`写作/平台审核.md` 暂按报告记录为 deferred ambiguity
  - ✅ ST-S3-D-DEDUP-EVIDENCE：461 prompt cards / 541 base docs / 25 样本 dedup evidence；strict PASS
  - ✅ ST-S3-Q-WEAK-EXAMPLES-A..D：202 个弱示例 prompt card 已补具体 `## 示例输入`；`report_prompt_quality.py` 复核 `weak_examples=0`
  - ✅ ST-S3-P-PRESSURE-TEST：本地压力测试 `100% PASS (7/7)`；`immersive-demo` 章号标题序列已修复为 `[1,2,3,4,5]`
- 主验证命令：`python3 scripts/verify_all.py`（quick gate）+ `python3 scripts/run_agent_harness.py`（mock_harness 离线覆盖 init / single run / multi_chapter / immersive / missing_state_error）+ `python3 scripts/evaluate_rag_recall.py`（473 cards / 473 vectors / sqlite-vec native / fallback=none；Layer 1/2 空召回均为 0；Layer 2 expected_recall@5=0.917 / recall@5=0.614）
- 灵感逃逸通道：`ginga idea add` 已实现；`foundation/raw_ideas/` 只落盘，仍禁止进入 state/RAG。
- 历史档案：`_distillation-plan.md`（阶段 2 草稿，47.6KB，保留）
- 4 jury 评审：`.ops/jury/jury-{1-4}-*.md`（4 票 revise / ~32KB）→ 100% 吸收到 ARCHITECTURE
- 4 scout 报告：`.ops/scout-reports/scout{1-4}-*.md`（~98KB）
- 子代理底层规范：`.ops/subagents/dispatch-protocol.md`（executor 选择、模型分级、心跳、回包检测、zombie 判定、看板权限）
- 关键约束：用户已有完整 skill 体系（思路 2 = `dark-fantasy-ultimate-engine`，思路 3 = `planning-with-files`），系统**兼容并增强**双 skill，**保留双 skill 一级公民地位，禁止揉合**；`immersive_mode` 保护 dark-fantasy 气质。
- 用户偏好：不要省事的"简单方案"；多思考多花时间；自利偏差导致标准滑坡。
- **Executor 教训（2026-05-13 双救火 + 续接）**：
  - 阶段 1 scout-3：`Agent(subagent_type=codex:codex-rescue)` 是 Claude wrapper 仍走 Claude API/dzzzz 网关；真独立 codex 只有直接 Bash 调 `codex-companion task --background --write`。
  - 阶段 3 jury：endpoint 大规模故障潮，2 族矩阵（xAI + DeepSeek）完成；jury 独立性靠 4 persona prompt 保住。
  - Sprint 2 续接：P7 子代理断网后 handoff 心跳停滞 ≠ 工作没完成；必须 §M2 白盒回放跑测试 + 看产物文件 mtime/bytes 才能判断真实进度（P7-I 实际全 done 但 handoff 没汇报 I-5）。
- **mock 陷阱预防**：测试要重定向默认 state_root **必须** mock 函数 `_default_state_root` 不能 mock 旧常量；旧常量已删除，复用旧 mock 模式会 fail-fast AttributeError。

## 项目定位

把 `_原料/` 里 **1002 个 md + 13 txt + 3 思路文件**（总约 6.94 MB）蒸馏成可复用的小说创作底座。

**核心判断**：
- 这堆原料异质性极高：结构化模板（基座）+ 创作哲学（思路）+ 场景卡片（prompts）+ 流水线（阶段 A~M），不能用单一方法处理。
- 简单做法 = 全部塞向量库做 RAG，会丢失结构、丢失依赖、丢失用户已有 skill 的兼容性。
- 正确做法 = 先建数据本体（schema），再建 agent 平台（registry + workflow），最后才上 RAG。

## 原料地图

```
_原料/
├── 基座/                            544 md，结构化"系统角色+思维链+输出要求"模板
│   ├── 题材/网文/                   题材模板（替身文/规则怪谈/多子多福/黑暗多子多福/狗血女文/知乎短篇/情满四合院/欲念描写专家 等）
│   ├── 模板/                        通用模板：伏笔 / 大纲 / 悬念 / 角色 / 项目 / 世界观
│   └── 方法论/                      写作 / 创意 / 市场 / 平台
├── 思路/                            3 文件（用户原始创作哲学 + 已有 skill）
│   ├── 待整理思路1                  10 条 AI 专家 SOP（搜索/答题/排版）
│   ├── 待整理思路 2                 dark-fantasy-ultimate-engine 完整 skill
│   └── 待整理思路 3                 planning-with-files v9.2.0 完整 skill
└── 提示词库参考/
    ├── prompts/                     475 数字编号 md，JSON-style 场景化提示词
    └── 小说提示词 2/                13 txt，阶段 A→M 完整创作 pipeline
```

## 入口

- 总览（本文件）：`notepad.md`
- **Agent 入口**：`AGENTS.md`（新会话先读顺序、边界、验证命令、禁区）
- **当前状态真值**：`STATUS.md`（最新完成度与下一步；优先级高于 `ROADMAP.md`）
- **架构最终版**：`ARCHITECTURE.md`（v1，已完成；完成度与下一步以 `STATUS.md` 为准）
- **路线图**：`ROADMAP.md`（v1，已补当前状态对照；历史待办不作为真值）
- 蒸馏方案历史档案：`_distillation-plan.md`（阶段 2 草稿，47.6KB，保留）
- 看板：`.ops/subagents/board.json`（全 done）
- Scout 扫描报告：`.ops/scout-reports/scout{1-4}-*.md`
- Jury 评审：`.ops/jury/jury-{1-4}-*.md`
- Jury prompt 模板：`.ops/jury-prompts/jury-{1-4}-*.md`

## 四层架构（摘要；权威版本见 `ARCHITECTURE.md`）

```
┌────────────────────────────────────────────────────────────┐
│  Meta 层（用户创作宪法 / 价值观 / 审美准则）               │
│  来源：思路/ 3 文件 + 用户偏好积累                          │
│  形态：system rules / 全局约束 / 创作宪法                   │
│  作用：约束所有下层输出；定义"什么是好"和"什么是雷"         │
└────────────────────────────────────────────────────────────┘
                          ↓ 约束
┌────────────────────────────────────────────────────────────┐
│  Foundation 层（数据本体 + 知识 schema）                    │
│  来源：基座/ 元数据 + 提示词库 字段抽取                     │
│  形态：题材×阶段×用途三维标签体系 + 实体 schema             │
│  作用：所有数据的统一语义层；标签 / frontmatter / 关系图     │
└────────────────────────────────────────────────────────────┘
                          ↓ 实例化
┌────────────────────────────────────────────────────────────┐
│  Platform 层（Agent Registry + Workflow Engine）            │
│  来源：基座/ 544 模板 + 阶段 A~M pipeline                   │
│  形态：可调用 agent 库 + DAG workflow + 模板引擎            │
│  作用：所有"小说生成"原子能力的库与编排                     │
└────────────────────────────────────────────────────────────┘
                          ↓ 召回
┌────────────────────────────────────────────────────────────┐
│  RAG 层（检索 + 上下文适配）                                │
│  来源：foundation/assets 中已治理资产；不召回 Meta / raw_ideas│
│  形态：native sqlite-vec + 元数据过滤器 + 上下文适配         │
│  作用：按当前创作状态提供候选卡片 / 方法论上下文            │
└────────────────────────────────────────────────────────────┘
```

## 5 阶段执行流水线

| 阶段 | 内容 | 状态 | 产出 |
|------|------|------|------|
| 0 | 项目骨架（notepad + 看板 + 草稿） | ✅ 完成 | 本文件 |
| 1 | 4 Scout 并行深扫 | ✅ 完成 | `.ops/scout-reports/scout{1,2,3,4}-*.md` |
| 2 | 主 agent 综合蒸馏方案 | ✅ 完成 | `_distillation-plan.md`（47.6KB） |
| 3 | Ark Jury Court 4 角法庭 | ✅ 完成 | `.ops/jury/jury-{1-4}-*.md`（4 票 revise） |
| 4 | 综合判决与交付 | ✅ 完成 | `ARCHITECTURE.md` + `ROADMAP.md` |

**下一步**：主线做 agent harness 补强；RAG 残余 `candidate_k` / `asset_type` blocker 作为 sidecar 处理；当前完成度以 `STATUS.md` 为准。

## 验证

- 4 个 Scout 报告全部存在且包含核心字段 → 阶段 1 完成
- `_distillation-plan.md` 存在且包含 4 层架构具体方案 → 阶段 2 完成
- 4 份陪审意见齐全且包含投票 → 阶段 3 完成
- `ARCHITECTURE.md` + `ROADMAP.md` 存在 → 项目交付

## 坑点

- **Ark Jury Court 不是 CLI**：需用 `ask-codex` + `ask-llm` 各扮 2 角色组装 4 角法庭。
- **用户已有 skill 必须先识别**：思路 2/3 是完整 skill，蒸馏产物必须做差异分析（哪些已有/哪些是新增/哪些可增强）。
- **1002 md 不能塞主上下文**：必须用 Scout 子代理隔离扫描，Scout 把详细报告 Write 到文件，只回主 agent 摘要。
- **基座 vs 提示词库参考有重叠**：必须做去重分析（同样的场景在两个地方都出现，用哪个？合并还是 drop？）。
- **三层标签体系初稿**：题材（网文 + 题材名） × 阶段（设定/框架/创作/数据分析/进阶/微观/中观/宏观/势力/辅助/商业化） × 用途（角色/情节/世界/伏笔/...）—— 字段需 Scout 1 验证标准化。
- **阶段 A~M 与基座的关系**：A~M 是流水线（pipeline），基座是能力库（agents）；两者是垂直关系不是替代关系。
- **派活 executor 选择坑**：救火 Claude API 故障时，`Agent(subagent_type=codex:codex-rescue)` 没用——它本质是 Claude wrapper，仍走 Claude API/dzzzz 网关，跟 `general-purpose` 同源 502。真独立 fallback 只有直接 Bash 调本机 `codex-companion task --background --write`（自定义 OpenAI 端，不过 dzzzz 网关）。完整规则、启动命令、跟踪命令在 `.ops/handoff-to-codex.md`。
- **codex CLI 默认只读沙箱**：派写任务必须显式加 `--write`，否则 codex 知道任务但写不了报告。
- **codex zombie 判定**：`status --all` 看 `phase: starting` 持续 ≥15 分钟、log 无新 `Running command` 推进 ≥10 分钟 → kill 重派。Big brief（如 475 文件横扫）zombie 风险显著高于 small brief（如 3 文件深读）。
