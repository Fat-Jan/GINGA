# Ginga 实施路线图（ROADMAP v1）

**版本**：v1（融合阶段 2 蒸馏方案 + 阶段 3 4 角法庭评审 + Sprint 重排）
**取代**：`docs/archive/_distillation-plan.md` §八（保留作历史档案）
**作者**：主 agent 综合
**完成日期**：2026-05-13
**状态更新**：2026-05-16（依据 `STATUS.md`；本文件保留为历史规划 + 当前状态对照）
**对应架构**：`ARCHITECTURE.md` v1

> 当前进度：S1、S2、S3 已全部完成；S4 / Phase 2 已完成 native `sqlite-vec` 接入、RAG 真实召回质量评估、P2 可回归评估收口、RAG 质量小迭代、P2-5 agent harness 补强与 P2-7A/P2-7B/P2-7C Platform runner 收敛。P2-7C 严格状态是 `done`：真实 LLM smoke 边界切片、provider 输出可读性、`context_snapshot`、`gap_report` 与 residual risk 报告均已收口；该证据仍只证明单章 smoke 边界，不证明长篇生产质量。Layer 2 当前 `recall@5=0.614`、`expected_recall@5=0.917`。新增规划路线只更新后续定位与版本索引，不改变当前生产完成度：拆书融梗 / `ReferenceTropeDistillation` 已完成 v1.3-0 到 v1.3-5，v1.4 BookView / explorer、v1.5 Review / deslop、v1.6 Market Research Sidecar、v1.7-0 Longform Production Policy、v1.7-1 Longform Quality Gate、v1.7-2 Reviewer Queue Review 与 v1.7-3 Longform Hard Gate 已完成；RAG 残余仅观察；真实长篇生产化已通过单章正文长度 + review hard gate 探针，但 4 章恢复卡在第 4 章长输出，下一步先处理 endpoint 稳定性或切换端点后补齐 4/4。
>
> 若本文件与 `STATUS.md` 冲突，以 `STATUS.md` 为当前状态真值。

**核心调整（修订 jury-4 P0 + jury-1 Q3）**：
- 原 S1（schema only） + S2（skill 集成）→ **新 S1（schema 最小子集 + 双 skill 集成 + 端到端跑通第一章）**
- 每个 sprint 必须独立产出可感知用户价值
- workflow 在 S1 内就砍到 12 step MVP，N/P/D/V 作为 workflow deferred

---

## 〇、总览

状态枚举：`done` = 有实现与验证证据；`in_progress` = 已有切片但 DoD 未全过；`planned` = 只有规划 / 评审；`deferred` = 明确延后；`observation` = 达标后保留观察。

| Sprint | 周期 | 核心交付 | 用户能力 | 状态 |
|---|---|---|---|---|
| **S1: MVP 跑通第一章** ⭐ critical path | 1-2 周 | Foundation schema 最小子集 + 双 skill contract + workflow 12 step + 端到端 CLI demo | "输入创意，得到第一章正文 + 状态文件" | ✅ 已完成 |
| **S2: 多章连载 + 基础召回** | 1-2 周 | 完整 runtime_state + RAG Layer 1 + 461 prompts 标注（A/A- 优先） + immersive_mode | "写到第 N 章不崩 + 召回辅助卡片 + 沉浸写作模式" | ✅ 已完成 |
| **S3: RAG 增强 + 标注扩展** | 1 周 | RAG Layer 2/3 + B/B+ 卡补示例 + scout-1 风险治理 | "向量召回 + LLM rerank + 召回质量提升" | ✅ 已完成 |
| **S4: Phase 2 缺口 + 用户反馈循环** | 持续 | N/P/D/V 阶段 + 多技能扩展 + 4 scout 全部建议落地 + agent harness 补强 + Platform runner 收敛 | "完整 pipeline + 持续优化" | 🔄 持续；RAG 评估、质量小迭代、P2-5 harness 与 P2-7A/P2-7B/P2-7C 已完成，下一步以 `STATUS.md` 为准 |
| **S5: 拆书融梗支线** | 后续版本 | `ReferenceTropeDistillation`：参考作品拆章、梗核 / 爽点 / 桥段结构蒸馏、trope_recipe 候选、人工审核后 promote | "把参考网文拆成可变形的融梗配方，再安全接入 Ginga 创作链" | 🟡 planned；已完成调研、jury 评审与规划文档，尚未实现 |

**总周期估计**：MVP 上线 3-5 周（S1+S2+S3）；Phase 2 持续。

---

## 一、Sprint 1：MVP 跑通第一章（1-2 周）⭐ critical path

### 1.1 Sprint Goal

> **24 小时内** 让作家通过简化接口跑通 "输入创意 → 得到第一章正文 + 完整状态文件"。
> **2 周内** 完成 Foundation schema 最小子集、双 skill contract、workflow 12 step、端到端 demo。

### 1.2 任务清单

#### 1.2.1 Foundation 最小子集（4 天）

- [x] **F-1**：写 `foundation/schema/genre_profile.yaml`（含 `profile_type` 字段，jury-2 字段补丁 2）
- [x] **F-2**：写 `foundation/schema/template.yaml`（含 `template_family`、`fields_required`）
- [x] **F-3**：写 `foundation/schema/methodology.yaml`（含 `method_family`、`rule_type`，jury-2 字段补丁 3）
- [x] **F-4**：写 `foundation/schema/checker_or_schema_ref.yaml`
- [x] **F-5**：写 `foundation/schema/prompt_card.yaml`（基于 scout-3 schema 定稿，含 `dedup_against`，jury-2 字段补丁 4）
- [x] **F-6**：写 `foundation/schema/runtime_state.yaml`（完整字段子定义，jury-2 P1 / 见 ARCHITECTURE §3.5）
- [x] **F-7**：扩展 `stage` 枚举为 12 值（+ `cross_cutting` / `profile`，jury-2 P0）
- [x] **F-8**：定 S1 必填 frontmatter 8 字段约定（jury-1 P2）
- [x] **F-9**：建 `foundation/raw_ideas/` 目录 + README（jury-3 P0）
- [x] **F-10**：写 `foundation/rag/recall_config.yaml`（冷暖启动配置，jury-2 字段补丁 6）

**F 验收**：5 类 schema 跑 yaml lint 通过 + 8 字段标注规则文档化。

#### 1.2.2 Meta 层核心 guard + checker（2 天）

- [x] **M-1**：写 `meta/constitution.yaml`：20 条上位法主索引（来自 scout-2）
- [x] **M-2**：写 3 个核心 guard：`no-fake-read` / `latest-text-priority` / `crosscheck-required`
- [x] **M-3**：写 3 个核心 checker（默认 warn-only）：`aigc-style-detector` / `character-iq-checker` / `cool-point-payoff-checker`（jury-3 P1）
- [x] **M-4**：写 `meta/user_overrides/checker_mode.yaml` 模板（作家可调 off/warn/block）

**M 验收**：guard 在 demo workflow 中能前置硬阻断；checker 在 demo 中能 warn-only 不阻塞。

#### 1.2.3 Platform 拆子层 + 双 skill 集成（5 天，critical path）

- [x] **P-1**：建 `ginga_platform/orchestrator/` + `ginga_platform/skills/` 目录结构
- [x] **P-2**：写 `ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml`（12 step DSL，见 ARCHITECTURE §4.4）
- [x] **P-3**：实现 `ginga_platform/orchestrator/runner/dsl_parser.py`（YAML → step list）
- [x] **P-4**：实现 `ginga_platform/orchestrator/runner/step_dispatch.py`（step → capability 调用）
- [x] **P-5**：实现 `ginga_platform/orchestrator/runner/state_io.py`（唯一 state 读写入口，带事务 + audit_log）
- [x] **P-6**：实现 `ginga_platform/orchestrator/meta_integration/guard_invoker.py`（preconditions hook）
- [x] **P-7**：实现 `ginga_platform/orchestrator/meta_integration/checker_invoker.py`（postconditions hook，warn-only 默认）
- [x] **P-8**：把思路 2 文档放入 `ginga_platform/skills/dark_fantasy_ultimate_engine/skill.md`（不动原文）
- [x] **P-9**：写 `ginga_platform/skills/dark_fantasy_ultimate_engine/contract.yaml`（jury-1 P0，含 immersive_mode 子节点）
- [x] **P-10**：写 `ginga_platform/skills/dark_fantasy_ultimate_engine/adapter.py`（双向 IO 转换）
- [x] **P-11**：把思路 3 文档放入 `ginga_platform/skills/planning_with_files/skill.md` + 写 `contract.yaml` + `adapter.py`
- [x] **P-12**：写 `ginga_platform/skills/registry.yaml`（列双 skill + 路由优先级）
- [x] **P-13**：实现 `skill-router` 逻辑（按 contract.yaml priority 决定 G_chapter_draft 走哪个 skill）

**P 验收**：12 step workflow 能完整 run；双 skill contract.yaml 各 ≥30 字段定义；adapter 跑 unit test 通过。

#### 1.2.4 端到端 demo（3 天）

- [x] **D-1**：写 demo CLI：`ginga init <book_id> --topic 玄幻黑暗`
- [x] **D-2**：写 demo CLI：`ginga run <book_id>` → 触发 workflow MVP 跑通 A→H 第一章
- [x] **D-3**：用 1-2 个基座样例 + 1-2 prompts 样例做 frontmatter 标注，验证 schema 完备性
- [x] **D-4**：跑 demo：输入 "玄幻黑暗 + 主角是失忆刺客 + 50 万字目标" → 输出第一章正文 + 完整 runtime_state 文件
- [x] **D-5**：跑 jury-3 创作场景压力测试 1（新人作家 8 万字短篇从零开始）

**D 验收**：demo 不报错跑通 + 输出 1 章 ≥3000 字正文 + state 文件 ≥ 8 个（locked + entity_runtime + workspace）。

### 1.3 Sprint 1 DoD（必须全过才进 S2）

- [x] 5 类 schema yaml 全跑 lint 通过
- [x] 双 skill contract.yaml 字段完整 + adapter 跑 unit test
- [x] workflow MVP 12 step 全部 run 通过
- [x] guard 3 个 + checker 3 个全跑通
- [x] demo CLI 跑通「输入创意 → 输出第一章」端到端
- [x] 8 决策中 BLOCKER 3 个（决策 1/3/5）在代码中明示落地
- [x] foundation/raw_ideas/ 灵感暂存区可用

### 1.4 Sprint 1 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| **双 skill contract.yaml 冲突** | 中 | S1 卡 5 天 | 优先实现 dark-fantasy contract；planning-with-files 作为横切层弱耦合接入 |
| **runtime_state 字段定义争议** | 中 | F-6 拖期 | 参照 ARCHITECTURE §3.5 完整字段表，不再扩 |
| **workflow runner 工程量超估** | 中 | P-3/4/5 拖期 | runner 起步只做最小可工作版本（YAML 解析 + 顺序 dispatch），优化推 S3 |
| **demo CLI UX 拖时间** | 低 | D-1/2 拖 1 天 | 用 click 库 + 最简单接口，不做 web UI |
| **作家 schema 学习曲线高** | 高 | D-5 失败 | 提供"零配置默认值"+ 5 个常用题材预填 yaml |

### 1.5 Critical Path 标注

```
F-1..F-10 ─┐
M-1..M-4 ──┼─→ P-1..P-13 ──→ D-1..D-5 ──→ S1 DoD
P-8/9/10 ──┘  (双 skill contract.yaml + adapter，最高风险段)
```

**最高风险**：P-9 / P-10 / P-11（双 skill contract + adapter 工程量被低估，jury-1 Q3 警示）→ 主 agent 必须每日跟进。

---

## 二、Sprint 2：多章连载 + 基础召回（1-2 周）

### 2.1 Sprint Goal

> 让作家能写到第 N 章不崩，召回开始辅助卡片，dark-fantasy 沉浸专线可用。

### 2.2 任务清单

#### 2.2.1 完整 runtime_state + 多章循环（3 天）

- [x] **S-1**：实现 runtime_state.entity_runtime 完整字段（CHARACTER_STATE 全子字段 / RESOURCE_LEDGER / FORESHADOW_STATE / GLOBAL_SUMMARY）
- [x] **S-2**：实现 runtime_state.locked 域 patch 流程（jury-3 P1 / ARCHITECTURE §3.5）：`meta/patches/<patch_id>.yaml`
- [x] **S-3**：实现 R1/R2/R3 终稿三件套 step + checker 联动
- [x] **S-4**：实现 V1 验收 checker（DoD-final）
- [x] **S-5**：多章 demo：连续跑 5 章不崩 + state 一致

#### 2.2.2 RAG Layer 1 frontmatter 召回（3 天）

- [x] **R-1**：写 `rag/index_builder.py`（扫 foundation/assets/ + 生成 sqlite 索引）
- [x] **R-2**：实现 Layer 1 召回：按 stage / topic / asset_type 过滤 + quality_grade 排序
- [x] **R-3**：实现冷启动逻辑：向量库不存在时降级到 Layer 1（jury-2 P0）
- [x] **R-4**：实现 stage-specific top_k（jury-2 P0 / §5.2 配置驱动）
- [x] **R-5**：实现 `workflow.rag_mode=off` 全局关闭机制（jury-3 P1）

#### 2.2.3 461 prompts 标注（4 天，A/A- 优先）

- [x] **L-1**：写半自动化标注工具（基于 scout-3 quality.json 草稿 + LLM 辅助 + 人工 review）
- [x] **L-2**：A/A- 级卡（约 230 张）标注 frontmatter 完整（必填 8 字段）
- [x] **L-3**：B+/B 级卡（约 200 张）标注必填字段 + dedup_verdict
- [x] **L-4**：C/D 级卡（约 30 张）暂留为低优先级标记
- [x] **L-5**：跑双库去重判定（jury-2 P0 / ARCHITECTURE §3.7 三段判定流程）

#### 2.2.4 dark-fantasy immersive_mode（2 天）

- [x] **I-1**：在 dark-fantasy adapter 实现 `immersive_mode=true` 行为
- [x] **I-2**：实现 `chapter_block_end` signal 触发批量结算
- [x] **I-3**：immersive 期内 checker 全静默
- [x] **I-4**：退出 immersive 时跑 R2 一致性 + apply pending_updates
- [x] **I-5**：demo：连续 5 章 immersive 写作 → 退出时一次结算

### 2.3 Sprint 2 DoD

- [x] runtime_state 全部字段实现 + patch 流程跑通
- [x] RAG Layer 1 召回跑通 + 冷启动验证
- [x] A/A- 级 prompt 卡（约 230 张）标注完成
- [x] 双库去重三段流程跑通（≥50 对样本验证）
- [x] immersive_mode 跑通连续 5 章 demo
- [x] jury-3 创作场景压力测试 2（老作家 30 万字插新支线）跑通

### 2.4 Sprint 2 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| **prompts 标注工作量爆** | 高 | L-2 拖期 | 严格优先级：仅 A/A- 完成即可进 S3 |
| **双库去重边界 case 多** | 中 | L-5 卡 | 边界 case 标 `conflict_pending`，进 S3 处理 |
| **immersive_mode 退出时状态合并冲突** | 中 | I-4 失败 | apply 失败回退到 last_safe_state + 报错 |

---

## 三、Sprint 3：RAG 增强 + 标注扩展（1 周）

### 3.1 Sprint Goal

> RAG 召回质量从"能用"到"好用"，标注覆盖率从 A/A- 扩到全量。

### 3.2 任务清单

- [x] **V-1**：选型向量库（sqlite-vec / faiss / chromadb），写 spike
- [x] **V-2**：实现 RAG Layer 2 向量召回（top_k 默认 10）
- [x] **V-3**：实现 RAG Layer 3 LLM rerank（默认关闭，jury-1 P2 / refinement stage 强制开启）
- [x] **V-4**：B/B+ 卡补示例 + 升 A（约 200 张，scout-3 优化点）
- [x] **V-5**：基座方法论按 method_family / rule_type 拆 sub-section（决策 4）
- [x] **V-6**：scout-1 风险治理（基座中识别的命名混乱、字段冗余等）
- [x] **V-7**：jury-3 创作场景压力测试 1+2 重跑 + 对比 S2 体验提升量化

### 3.3 Sprint 3 DoD

- [x] Layer 2 召回 + Layer 3 rerank 工作（refinement stage 自动启用 rerank）
- [x] 全 461 prompts 标注完成（含 dedup_verdict）
- [x] 基座方法论拆 sub-section 完成（决策 4 落地）
- [x] 创作场景压力测试 1+2 通过率 ≥80%

---

## 四、Sprint 4：Phase 2 缺口 + 用户反馈循环（持续）

### 4.1 Sprint Goal

> 按真实需求驱动 Phase 2 缺口实施；用户反馈循环常态化。

### 4.2 已完成增补（2026-05-15）

- [x] **S4-RAG-1**：native `sqlite-vec` 接入完成。
- [x] **S4-RAG-2**：RAG 真实召回质量评估完成，可跑 `scripts/evaluate_rag_recall.py`。
- [x] **P2-1**：补 Layer 1 空召回 metadata，明确空结果原因与诊断字段。
- [x] **P2-2**：为评估查询维护 `expected_ids` / `relevant_ids`。
- [x] **P2-3**：把 RAG 质量评估从「能跑」升级为可追踪、可回归。
- [x] **P2-4**：RAG 质量小迭代完成：补充高影响 topic/stage/card_intent 扩展与候选排序先验，Layer 2 `recall@5` 从 0.425 提升到 0.614，`expected_recall@5` 从 0.875 提升到 0.917。
- [x] **P2-5**：Agent harness hardening 完成：`scripts/run_agent_harness.py` 离线覆盖 `ginga init`、单章 `run`、`--chapters` 多章、`--immersive` 和错误退出路径；mock LLM + 临时 `state_root`，检查 state 域、audit_log、chapter artifacts、错误路径与 CLI 退出码。
- [x] **P2-5A**：StateIO 写入边界审计完成：`runtime_state` YAML 域写入保持在 `StateIO` / locked patch flow；章节正文 `chapter_NN.md` 通过 `StateIO.write_artifact()` 明确标注为 `chapter_text` artifact。
- [x] **P2-5B**：demo 真实性标识完成：CLI / harness / 报告区分 `mock_harness`、`deterministic_eval` 与 `real_llm_demo`，mock harness 报告显式声明不证明 production readiness。
- [x] **P2-6**：RAG 残余小迭代完成：Layer 2 `recall@5=0.614`、`expected_recall@5=0.917`，剩余 `candidate_k` / `asset_type` blocker 转为后续观察项。
- [x] **P2-7A**：Platform runner 收敛切片完成：repo workflow DSL 的 `G_chapter_draft` 同时保留 capability asset hint 与 `skill-router`，默认 router 可读取真实 skill registry；单章 `demo_pipeline.run_workflow` 进入 `step_dispatch`，经 dark-fantasy adapter 写 `workspace.chapter_text`，并跑 H/R1/R2/R3/V1 workflow step 审计。

### 4.3 当前下一步

- [x] **P2-7B**：Platform runner 收敛完成：以 P2-5 harness 为回归门，把 `demo_pipeline` 中剩余 A-F/H/R1/R2/R3/V1 stub capability 替换为 asset-backed deterministic capability provider，provider 输出带 `asset_ref` / `provider=asset-backed`，真实路径继续向 workflow DSL + skill adapters + `StateIO` 收拢。
- [x] **P2-7C-0**：真实 LLM smoke 边界切片完成：`scripts/run_real_llm_smoke.py` 可 dry-run 或显式 `--run`，`.ops/validation/real_llm_demo_smoke.json` 记录 `passed=true`、endpoint、输出路径与不会覆盖的文件；该切片不证明生产质量。
- [x] **P2-7C-1**：provider 质量与真实 demo 收口：H/R/V provider 输出可读性已补强，真实 demo 报告已补 `context_snapshot`、`gap_report`、residual risk，并保持 mock harness 与真实 demo 边界清晰。
- [x] **v1.4**：BookView / explorer 完成：从 `StateIO` / chapter artifacts 派生只读书目视图，输出限定 `.ops/book_views/<book_id>/<run_id>/`，并提供 `ginga inspect` / `ginga query`。
- [x] **v1.5**：Review / deslop 完成：输出 `.ops/reviews/<book_id>/<run_id>/review_report.json` 与 `README.md`，只做 warn-only report，不自动改正文，rubric 不进入创作 prompt。
- [x] **v1.6**：Market Research Sidecar 完成：`ginga market --fixture --authorize` 输出 `.ops/market_research/<book_id>/<run_id>/market_report.json` 与 `README.md`，保留来源 / 采集时间 / 数据质量状态，剥离外部原文，默认不进 RAG。
- [x] **v1.7-3**：Longform Hard Gate 完成：正式真实 LLM 批量推荐 4 章、上限 5 章，6 章及以上只作压力测试；CLI 在真实 LLM 调用前阻断连续开篇回环、低频锚点缺失或伏笔标记缺失；`ginga review` 同步输出 `longform_quality_gate.hard_gate`。

### 4.4 任务清单（按触发条件优先级，尚未触发）

- [ ] **F2-1**：N0/N1 立项市场层（决策 6 / 触发：用户主动需要立项调研）
- [ ] **F2-2**：P1-P3 后处理与排版（触发：用户发布到 Coding/CNB）
- [ ] **F2-3**：D1-D3 数据分析与复盘（触发：已有发布数据可分析）
- [ ] **F2-4**：V2 版本管理（触发：项目 ≥10 部作品）
- [ ] **F2-5**：第 3+ skill 接入（按用户需求）
- [x] **F2-6**：拆书融梗 / `ReferenceTropeDistillation` Phase 0 文档补强完成：污染检查规则、P0 MVP 边界、manifest schema、RAG 排除规则、资源上限、关键词来源规则、validator DoD 已落位；下一步进入 v1.3-1 P0 MVP。

### 4.5 用户反馈循环（持续）

- 每周收 jury-3 / jury-4 类压力测试反馈
- 每月做 1 轮 ark-jury-court 多模型评审检查"是否漂移"
- 每季度 review ARCHITECTURE.md（看哪些 Phase 2 项已被触发）

---

## 五、风险登记册（4 jury 共识汇总）

| ID | 风险 | 概率 | 影响 | 触发 sprint | 缓解策略 |
|---|---|---|---|---|---|
| R-01 | 双 skill contract.yaml 工程量被低估 | 中 | 高 | S1 | 优先 dark-fantasy；planning-with-files 弱耦合 |
| R-02 | runtime_state 字段定义争议 | 中 | 中 | S1 | 参照 ARCHITECTURE §3.5 不再扩 |
| R-03 | demo CLI UX 太复杂吓退新人作家 | 高 | 中 | S1 | 零配置默认 + 5 题材预填 |
| R-04 | RAG 召回质量不达预期 | 中 | 中 | S2/S3 | Layer 1 先稳；Layer 2/3 渐进 |
| R-05 | 461 prompts 标注耗时高 | 高 | 中 | S2 | A/A- 优先；其他 Phase 2 |
| R-06 | workflow checker 误伤作家文风 | 中 | 高 | S1/S2 | 默认 warn-only；user_overrides 暴露 |
| R-07 | 灵感逃逸通道 raw_ideas/ 被遗忘 | 低 | 中 | S2/S3 | README + CLI subcommand `ginga idea add` 显式入口 |
| R-08 | dark-fantasy 气质被工程秩序稀释 | 中 | 高 | S1/S2 | immersive_mode 必须落地（不许 deferred） |
| R-09 | 长篇 locked 域修改成本高 | 中 | 中 | S2 | patch 流程必须落地（jury-3 P1） |
| R-10 | 第 3 个 skill 接入冲突 | 低 | 中 | Phase 2 | contract.yaml 已经标准化，新 skill 只需补 contract |

---

## 六、依赖矩阵

```
S1 任务依赖：
  F-1..F-10 (foundation schema) ──┐
  M-1..M-4 (meta) ─────────────────┤
                                   ├──→ P-1..P-13 (platform) ──→ D-1..D-5 (demo) ──→ S1 DoD
  scout-1/2/3/4 报告 ───────────────┘                                   ↑
                                                                       │
                                                            jury 1/2/3/4 修订点

S2 依赖 S1（runtime_state + workflow runner + skill contract 必须已就位）
S3 依赖 S2（Layer 1 索引必须已建；prompts A/A- 必须已标）
S4 依赖 S3（治理完成 + RAG 稳定才能加 Phase 2 复杂阶段）
```

---

## 七、Jury 修订追踪表

每条 jury 修订建议在哪个 sprint 落地：

| Jury # | 建议 | Sprint | 任务编号 |
|---|---|---|---|
| jury-1 P0 #1 | Platform 拆 Orchestrator + Skill Runtime | S1 | P-1 |
| jury-1 P0 #2 | 补 skill contract.yaml | S1 | P-9 / P-11 |
| jury-1 P1 #1 | guard 与 checker 显式划分 | S1 | M-2 / M-3 / P-6 / P-7 |
| jury-1 P1 #2 | workflow 砍到 12 step | S1 | P-2 |
| jury-2 P0 #1 | stage 枚举扩展 | S1 | F-7 |
| jury-2 P0 #2 | 双库去重三段流程 | S2 | L-5 |
| jury-2 P0 #3 | RAG 冷暖启动 | S2 | R-3 / R-4 |
| jury-2 P1 #1 | runtime_state 字段子定义 | S1 | F-6 |
| jury-2 P1 #2 | uses_capability 改资产 id | S1 | P-2 |
| jury-2 字段补丁 1-6 | 6 个具体字段补丁 | S1 | F-1..F-10 / 见 ARCHITECTURE §3.2-3.4 |
| jury-3 P0 | workflow 可选轻模式 + raw_ideas/ | S1 / S2 | F-9 / I-1..I-5 |
| jury-3 P1 #1 | checker 默认 warn-only | S1 | M-3 / P-7 |
| jury-3 P1 #2 | locked 域 patch 流程 | S2 | S-2 |
| jury-3 P1 #3 | RAG 可全局关闭 | S2 | R-5 |
| jury-3 改进 4 | dark-fantasy immersive_mode | S2 | I-1..I-5 |
| jury-4 P0 | Sprint 重排 / S1 端到端 demo | S1 | D-1..D-5 |
| jury-4 P1 | workflow 砍 N/R/P/D/V | S1 | P-2（Phase 2 显式标 deferred） |
| jury-4 P2 #1 | MVP 仅 Layer 1 | S2 | R-1..R-5 |
| jury-4 P2 #2 | Top 18 + A/A- 优先标注 | S2 | L-2 |
| jury-4 改进 5 | MVP 用例宣言 | S1 | ARCHITECTURE §〇 |
| jury-4 决策分类 | 8 决策最终判决 | 全 sprint | ARCHITECTURE §七 |

---

## 八、验收（ROADMAP DoD v1）

阶段 4（本文件）完成的判据：
- [x] 本文件存在
- [x] ARCHITECTURE.md 存在
- [x] 4 sprint 任务清单全部明示（§一-§四）
- [x] Critical path 标注（S1）
- [x] 风险登记册（10 条，§五）
- [x] Jury 修订追踪表（jury 23 条建议全部归属到具体任务编号，§七）
- [x] 8 决策落地到 ARCHITECTURE §七 + 本文件任务编号

**当前下一步**：以 `STATUS.md` 为准；截至 2026-05-16，P2-7C Platform runner 收敛、v1.3-0 到 v1.3-5 的拆书融梗支线、v1.4 BookView / explorer、v1.5 Review / deslop、v1.6 Market Research Sidecar、v1.7-0 Longform Production Policy、v1.7-1 Longform Quality Gate、v1.7-2 Reviewer Queue Review 与 v1.7-3 Longform Hard Gate 均已收口。RAG 残余 `candidate_k` / `asset_type` blocker 仅作为观察项，只有指标回退或新 gold query 暴露问题时再修；真实长篇生产化下一步是处理 `久久` 长输出 504 / 中断问题，补齐第 4 章并导出 4/4 review gate。

---

## 九、版本划分与后续路线

本节用于把已完成主线和后续支线拆开，避免把历史 Sprint、当前真值和未来想法混在一起。

项目定位随新增路线收敛为两层：当前主线是可回归的小说创作 runtime（`workflow DSL + skill adapters + StateIO`），后续路线是围绕它展开的 sidecar / projection / review / research 能力；后者只提供证据、视图或报告，不建立第二状态真值。

| 版本线 | 范围 | 状态 | 当前判定 |
|---|---|---|---|
| **v1 / S1-S3** | Foundation / Meta / Platform / RAG MVP；第一章、多章、immersive、RAG Layer 1-3、prompt / methodology 治理 | ✅ 已完成 | 已达到可回归基础底座 |
| **v1.1 / P2 质量线** | RAG 真实召回质量评估、RAG 小迭代、agent harness、StateIO artifact 边界、mock / real demo 标识 | ✅ 已完成 | 以 `STATUS.md` 和验证产物为准 |
| **v1.2 / P2-7 Platform runner 收敛** | workflow DSL + skill adapters + `StateIO`，12 step asset-backed deterministic provider | ✅ P2-7A/P2-7B/P2-7C 已完成 | 已完成真实 LLM smoke 边界切片、provider 可读性、context/gap report 与 residual risk；仍不声明长篇生产质量 |
| **v1.3 / 拆书融梗 Evidence Pipeline** | `ReferenceTropeDistillation`：参考作品拆章、manifest、污染检查、章节原子事件、质量门、trope_recipe 候选、人工审核 promote、显式 opt-in sidecar 召回 | 🟢 v1.3-0 done；v1.3-1 done；v1.3-2 done；v1.3-3 done；v1.3-4 done；v1.3-5 done | 已完成污染隔离底座、Reference Corpus P0 MVP、结构性 Chapter Atom + Quality Gates、去来源 `trope_recipe` candidate sidecar、approved-only Promote Flow 与 Reference Sidecar RAG；默认 RAG 仍不读污染域 |
| **v1.4 / Book Workspace View + Explorer** | 从 StateIO/artifacts 派生可读书目视图与只读查询，不产生第二状态真值 | ✅ done | 已完成 `BookView` projection、`ginga inspect` 与 `ginga query`；输出限定 `.ops/book_views/<book_id>/<run_id>/`，默认输入白名单不包含 `.ops/book_analysis/**` |
| **v1.5 / Review + Anti-AI warn-only gate** | 审稿、去 AI 味、平台 rubric 报告化；只做审计/报告，不自动改正文 | ✅ done | 已完成 `ginga review` 与 `.ops/reviews/<book_id>/<run_id>/` sidecar；rubric 只用于 review report，不进入创作 prompt |
| **v1.6 / Market Research Sidecar** | 扫榜、外部研究、市场信号报告，带采集时间、来源和数据质量状态 | ✅ done | 已完成显式授权 + offline fixture sidecar；外部原文剥离，默认不进 RAG |
| **v1.7 / Longform Production Policy + Gate** | 真实 LLM 长篇批量策略、成本/质量 smoke、jury 评审、CLI 上限保护、正式质量 gate、queue 外部评审与人工终审 brief、生成前 hard gate、prompt 连续性修复 | 🟢 v1.7-0 done；v1.7-1 done；v1.7-2 done；v1.7-3 done；v1.7-4 observation；v1.7-5 done | `久久` 30 章真实 smoke 显示 10 连发开始 drift；当前正式批量生成推荐 4 章、上限 5 章，6 章及以上只作压力测试；v1.7-4 已按 4+5 生成 9/9 章且脚本级 drift=stable，但 `ginga review` hard gate 仍因第 6-9 章连续开篇回环阻断下一批；v1.7-5 已修 prompt 消费 `CHAPTER_INPUT_BUNDLE`、hard gate 低频锚点同源和沉浸批内上一章摘要承接；继续真实生成前仍需小批隔离验证 |
| **v1.8 / Genm 治理机制吸收** | 从 Genm 吸收 role/stage/provider 观察矩阵、candidate/report/truth 门禁语言、style fingerprint 与可选可观测性指标，先做报告和治理规则，不接管 runtime | 🟢 v1.8-0 done；v1.8-1 done；v1.8-2 done；v1.8-3 done | 已完成 `ginga model-topology observe`、`.ops/governance/candidate_truth_gate.md`、`ginga review` 的 report-only style fingerprint，以及 `ginga observability` 的 evidence pack / workflow stage / migration audit 三类只读报告；默认 `probe_live=false`，不写 `StateIO`，不改变 workflow/provider 路由；candidate 晋升 truth 必须先过人工接受、schema、污染检查、写入口和审计证据 |
| **v1.9 / Story Truth Template** | 从原料整理小说真值模板，再用拆书产物、题材系列和长篇 drift 证据做缺口校验 | 🟢 v1.9-1 done；🟢 v1.9-2 done；🟢 v1.9-3 done；🟢 v1.9-4 done；🟢 v1.9-5 done + observation | 已完成 source audit、只读 schema / validator、`StateIO` 项目/题材契约窄切片、`workspace.CHAPTER_INPUT_BUNDLE` 与 4 章真实小样本回归；回归 drift=`needs_review`，不得扩大批量 |
| **v2 / 完整创作运营线** | N/P/D/V 阶段、发布后数据分析、版本管理、第 3+ skill 接入、封面/发布包 | ⏳ 按触发条件推进 | 不抢 v1.2 / v1.3 前置 |

### 9.1 v1.3：拆书融梗 Evidence Pipeline

定位：

`ReferenceTropeDistillation` 不是读书报告，也不是默认参考语料 RAG；它是把参考网文拆成可复用、可换皮、可审计的融梗配方。

已完成规划产物：

- `.ops/reports/chai_shu_fusion_research_draft.md`
- `.ops/reports/chai_shu_fusion_decision_report.md`
- `.ops/reports/book_analysis_distillation_fusion_plan.md`
- `.ops/jury/book_analysis_distillation_plan_review_2026-05-15/`
- `.ops/reports/oh_story_inspiration_roadmap.md`
- `.ops/jury/oh_story_roadmap_review_2026-05-15/`
- `.ops/jury/oh_story_roadmap_review_2026-05-15_reserve/`

版本拆分：

| 阶段 | 名称 | 目标 | 状态 |
|---|---|---|---|
| v1.3-0 | 文档补强 + 污染隔离前置 | 补 `contamination_check_rules.md`、P0 MVP 边界、manifest schema、RAG 排除规则、资源上限、关键词来源规则 | ✅ done；证据见 `.ops/book_analysis/` 与架构验证 |
| v1.3-1 | Reference Corpus P0 MVP | 纯函数化 scan / split / manifest / validator / report，输出 `.ops/book_analysis/<run_id>/`；不做内容分析，不进 `StateIO`、默认 RAG、prompt、`raw_ideas`、Foundation assets/schema | ✅ done；证据见 `test_book_analysis_corpus`、`.ops/book_analysis/v1-3-1-smoke-main/validation_report.json` 与 `verify_all.py` |
| v1.3-2 | Chapter Atom + Quality Gates | 结构性 `chapter_boundary` atom、可拒绝 quality gates、validator / report，所有产物标 `pollution_source: true`，不保存标题或原文摘录 | ✅ done；证据见 `test_book_analysis_corpus`、`.ops/book_analysis/v1-3-2-smoke-main/validation_report.json` 与 `verify_all.py` |
| v1.3-3 | Trope Recipe Candidate | D1-D12 转为 `trope_recipe` 候选：梗核、读者爽点、触发条件、变形参数、禁搬元素；不得自动进入创作 workflow | ✅ done；证据见 `trope_recipes.py`、`validate_trope_recipes.py`、`.ops/book_analysis/v1-3-3-smoke-main/validation_report.json` 与 `verify_all.py` |
| v1.3-4 | Promote Flow | 人工审核 + 污染检查后 promote 到白名单 Foundation methodology 资产 | ✅ done；证据见 `promote.py`、`promote_trope_recipes.py`、`validate_promoted_trope_assets.py`、`TropeRecipePromoteFlowV134ContractTest` 与 `verify_all.py --quick` |
| v1.3-5 | Reference Sidecar RAG | 显式启用的 sidecar 召回；不污染默认 RAG | ✅ done；证据见 `rag/reference_sidecar.py`、`build_reference_sidecar_index.py`、`ReferenceSidecarRagTest` 与 `verify_all.py --quick` |

关键红线：

- 不写 `foundation/runtime_state/`。
- 不进默认 RAG。
- 不使用 `foundation/raw_ideas/` 暂存拆书结果。
- 不把原文、人物、设定、桥段直接喂给生成 prompt。
- `.ops/book_analysis/<run_id>/` 是污染源域，产物 manifest 必须标记 `pollution_source: true`，源自参考作品的文件头必须标 `[SOURCE_TROPE]`。
- v1.4 explorer、v1.5 review、创作 provider 的默认输入白名单不得包含 `.ops/book_analysis/`。
- 默认 RAG 索引流程必须主动排除 `.ops/book_analysis/` 与外部采集原文；未来扩展索引源时也要由 validator 复查。
- 第一轮历史边界是 scan / split / manifest / validator / report；当前 v1.3 已推进到 Promote Flow 与 Reference Sidecar RAG，但仍不得把 `.ops/book_analysis/**`、外部榜单原文或市场采集原始数据放入默认 RAG / prompt / explorer 输入白名单。

### 9.2 oh-story 参考路线的分层吸收机制

参考 `worldwonderer/oh-story-claudecode` v0.6.1 后，当前结论不是“hooks / references / 书目目录没有价值”，而是“吸收价值，改造成 Ginga 形态”：

- v1.2C 可吸收：显式 `context_snapshot`、`gap_report`、provider 输出可读性，服务真实 demo 边界。
- v1.3 可吸收：章节切分、manifest、章节原子事件、剧情聚合质量门、`completed_with_errors`，但全部放在污染源 sidecar。
- v1.4 可吸收：`BookView` projection 与 read-only explorer；输出限定 `.ops/book_views/<book_id>/<run_id>/`，真值仍是 StateIO。
- v1.5 已吸收：warn-only review sidecar、AI 味量化雏形与平台风格 rubric 报告；rubric 只用于报告，不进入创作 prompt。
- v1.6 已吸收：扫榜数据质量头、采集时间与来源；当前只支持显式授权的 offline fixture，外部原文剥离且默认 RAG 禁入。

分层吸收表：

| oh-story 机制 | Ginga 吸收方式 | 红线 |
|---|---|---|
| hooks | 吸收生命周期信号，改造成显式 `ginga inspect` / scripts / `.ops/reports` | 不做隐式上下文注入 |
| references | 吸收“操作手册化”组织方式、输出模板、质量清单和 validator | 不复制整套知识库，不制造口径冲突 |
| `设定/大纲/正文/追踪` 书目目录 | 吸收为 `BookView`、import/export、发布包等人类可读 projection | 不替代 StateIO，不成为第二状态真值 |
| 拆文库 / 市场原始数据 | 吸收为 sidecar 证据与报告 | 不进默认 RAG，不进 explorer/review 默认白名单 |

### 9.3 v1.9：Story Truth Template

定位：

Story Truth Template 不是把 Story Bible 写成一个大文件，而是先从原料归纳小说系统必须记住的字段，再用拆书产物和长篇质量证据反向校验字段缺口。它服务后续 schema / validator / StateIO 窄切片，不直接替代现有 `runtime_state`。

当前规划产物：

- `.ops/plans/v1-9-story-truth-template-plan.md`
- `.ops/reports/story_truth_template_source_audit.md`

计划拆分：

| 阶段 | 名称 | 目标 | 状态 |
|---|---|---|---|
| v1.9-1 | 原料字段矩阵固定 | 抽样读取创意、设定、框架、创作、进阶、数据分析、商业化和题材系列原料，生成 source audit；标清 core / genre_extension / candidate_only / report_only | ✅ done；证据见 `.ops/reports/story_truth_template_source_audit.md` |
| v1.9-2 | schema 草案与 validator 设计 | 草拟 `story_truth_template` schema 与只读 validator，拒绝 candidate / report 直接进入 truth | ✅ done；证据见 `foundation/schema/story_truth_template.yaml`、`scripts/validate_story_truth_template.py`、`.ops/validation/story_truth_template_schema.json` |
| v1.9-3 | StateIO 窄切片 | 只选择一个安全落点，例如 `locked.PROJECT_CONTRACT` 或 `locked.GENRE_CONTRACT`，经 `StateIO` 写入 | ✅ done；证据见 `demo_pipeline.init_book`、`ginga init --target-platform/--target-reader/--update-frequency` 与 `test_story_truth_template` |
| v1.9-4 | 章节输入包接入 | 构建 `workspace.CHAPTER_INPUT_BUNDLE`，在生成前检查角色状态、世界规则、伏笔操作、爽点目标、风格锁和风险提示 | ✅ done；证据见 `build_chapter_input_bundle()`、`run_workflow` 生成前 StateIO 写入、`test_story_truth_template` 与 `test_multi_chapter` |
| v1.9-5 | 长篇质量回归 | 基于 v1.7-3 的 4 / 5 章口径做小规模真实 LLM 回归，review 只作为 report-only 证据 | ✅ done + observation；4/4 章真实生成，脚本 passed，但 drift=`needs_review`、review warn/17 issues、短章为低成本设置观测 |

模板层：

- 项目契约：作品定位、目标平台、目标读者、总字数、更新频率、核心卖点、付费点、留存目标。
- 题材契约：核心爽点、读者期待、黄金三章、情绪弧线、钩子策略、章节结构、平台策略、禁忌清单。
- 故事架构：总纲、卷纲、章纲、三幕结构、关键转折、冲突升级、主题载体。
- 角色与势力：主角、配角、反派、阵营、势力资源、关系网络、行为模式、成长弧线。
- 世界与体系：世界类型、地理、历史、文化、法律、经济、力量体系、官职 / 宗门 / 家族、金手指。
- 爽点 / 钩子 / 伏笔账本：读者回报、触发条件、章末钩子、伏笔 ID、回收状态和遗忘风险。
- 章节输入包：本章目标、场景纲、段落蓝图、关键句、出场角色状态、相关世界规则和风险提示。
- 运行状态账本：角色状态、资源、关系、事件历史、全局摘要、章节游标。
- 风格锁：叙事视角、文风、对白风格、句式密度、禁用腔调、低频题材锚点、反 AI 味指标。
- 候选池与晋升门禁：候选来源、人工接受、schema 校验、污染检查、写入口和审计证据。

关键红线：

- 不把 `.ops/book_analysis/**`、review report、market report、jury 原文或外部原文自动写入 truth。
- 不把 `trope_recipe_candidate` 直接注入创作 prompt；它只能作为 `candidate-only`，经人工接受和污染检查后再讨论 promote。
- 不新增第二状态真值；`BookView` 仍是 projection，`StateIO` 仍是 `runtime_state` 唯一写入口。
- v1.9-1 source audit 已完成；v1.9-2 才允许新增只读 schema / validator，且不得接入 `StateIO` 写链。

### 9.4 v2.0 - v2.5：Harness Engineering 底座

定位：

Harness Engineering 不是继续加长 prompt，而是把 agent 的工作环境做成可读、可验证、可续接的仓库协议。v2.0 / v2.1 负责规则地图和自检，v2.2 负责离线 CLI matrix，v2.3-v2.5 分别把真实 LLM、小队调度和阶段收口做成可回归 gate。

版本拆分：

| 阶段 | 名称 | 目标 | 状态 |
|---|---|---|---|
| v2.0 | Harness Map | 把任务类型映射到先读文件、禁区、最短反馈命令和证据落点 | ✅ done；证据见 `.ops/harness/README.md` 与 `scripts/validate_harness_contracts.py` |
| v2.1 | Harness Self-check | 检查 `AGENTS.md`、Harness Map 和 `verify_all.py` wiring，并接入架构契约 | ✅ done；证据见 `test_architecture_contracts`、`.ops/validation/harness_contracts.json`、`.ops/validation/architecture_contracts.json` |
| v2.2 | CLI Harness Matrix | 扩展 `run_agent_harness.py` 覆盖 review / inspect / query / market / observability / model-topology | ✅ done；证据见 `.ops/validation/agent_harness.json`、`.ops/reports/agent_harness_report.md`、`test_agent_harness` |
| v2.3 | Real LLM Harness | 固定真实 LLM preflight / postflight、成本边界、隔离输出和 review gate | ✅ done；证据见 `scripts/run_real_llm_harness.py`、`.ops/validation/real_llm_harness.json`、`.ops/reports/real_llm_harness_report.md`、`test_real_llm_demo_smoke`；v1.7-6 后已把 repair retry 计入真实调用预算，让 postflight/report 明确记录 fail-fast 章节与原因，并把无章节 artifact 的 review gate 标为 `no_chapters` |
| v2.4 | Multi-Agent Harness | 检查 board / task contract / provider model / 写范围 / done 归属 | ✅ done；证据见 `scripts/validate_multi_agent_harness.py`、`.ops/validation/multi_agent_harness.json`、`.ops/reports/multi_agent_harness_report.md`、`test_agent_harness` |
| v2.5 | Stage Closeout Harness | 固定阶段收口模板、truth sync、验证摘要和 commit message 检查 | ✅ done；证据见 `scripts/validate_stage_closeout.py`、`.ops/harness/stage_closeout_template.md`、`.ops/validation/stage_closeout_harness.json`、`.ops/reports/stage_closeout_harness_report.md`、`test_architecture_contracts` |

关键红线：

- v2.2 只证明 CLI matrix 的离线覆盖与 sidecar / projection 边界，不证明真实 LLM 生产质量。
- v2.3 把真实 LLM 调用变成可回归流程，但 dry-run 不证明质量；真实小批必须显式 `--run`、独立 `.ops/real_llm_harness/**` 输出并复跑 review gate；若启用质量修复重试，成本边界必须按每章最多 3 次生成估算，失败报告必须保留 fail-fast 章节与原因。
- v2.4 只检查 board / task contract / provider model / 写范围 / done 归属，不替主控做任务取舍。
- v2.5 只检查阶段收口模板、truth sync、验证摘要和 commit message，live commit / push 仍需主控按 diff 白名单执行。

---

## 附录 A：阶段 0-4 全流水线回顾

| 阶段 | 内容 | 状态 | 产出 | 完成日期 |
|---|---|---|---|---|
| 0 | 项目骨架（notepad + 看板 + 草稿） | ✅ | `notepad.md` | 2026-05-12 |
| 1 | 4 Scout 并行深扫 | ✅ | `.ops/scout-reports/scout{1,2,3,4}-*.md` | 2026-05-13 03:30 |
| 2 | 主 agent 综合蒸馏方案 | ✅ | `docs/archive/_distillation-plan.md` 47.6KB | 2026-05-13 10:07 |
| 3 | Ark Jury Court 4 角法庭 | ✅ | `.ops/jury/jury-{1-4}-*.md` 共 32KB / 4 票 revise | 2026-05-13 17:43 |
| 4 | 综合判决与交付 | ✅ | `ARCHITECTURE.md` + `ROADMAP.md` | 2026-05-13 17:55 |

**全程时间线**：2026-05-12 22:40 → 2026-05-13 17:55，约 19 小时（含中断与多轮 endpoint 救火）。

**用户偏好实践**：
- ✅ "不要省事的简单方案"：阶段 3 跑了完整 4 角法庭，未压成 2 角
- ✅ "多思考多花时间"：scout-3 破例第 3 次重派 + 阶段 3 经历 3 轮 endpoint 救火
- ✅ "保留双 skill 一级公民地位"：ARCHITECTURE §〇 / §四 / §六 三处明示
- ✅ "兼容并增强已有 skill"：Skill Runtime 子层专设 + immersive_mode 新增气质保护
