# Ginga 实施路线图（ROADMAP v1）

**版本**：v1（融合阶段 2 蒸馏方案 + 阶段 3 4 角法庭评审 + Sprint 重排）
**取代**：`_distillation-plan.md` §八（保留作历史档案）
**作者**：主 agent 综合
**完成日期**：2026-05-13
**状态更新**：2026-05-14（依据 `STATUS.md`；本文件保留为历史规划 + 当前状态对照）
**对应架构**：`ARCHITECTURE.md` v1

> 当前进度：S1、S2、S3 已全部完成；S4 / Phase 2 已完成 native `sqlite-vec` 接入与 RAG 真实召回质量评估。下一步 P2：补 Layer 1 空召回 metadata，并为评估查询维护 `expected_ids` / `relevant_ids`。
>
> 若本文件与 `STATUS.md` 冲突，以 `STATUS.md` 为当前状态真值。

**核心调整（修订 jury-4 P0 + jury-1 Q3）**：
- 原 S1（schema only） + S2（skill 集成）→ **新 S1（schema 最小子集 + 双 skill 集成 + 端到端跑通第一章）**
- 每个 sprint 必须独立产出可感知用户价值
- workflow 在 S1 内就砍到 12 step MVP，N/P/D/V 作为 workflow deferred

---

## 〇、总览

| Sprint | 周期 | 核心交付 | 用户能力 | 状态 |
|---|---|---|---|---|
| **S1: MVP 跑通第一章** ⭐ critical path | 1-2 周 | Foundation schema 最小子集 + 双 skill contract + workflow 12 step + 端到端 CLI demo | "输入创意，得到第一章正文 + 状态文件" | ✅ 已完成 |
| **S2: 多章连载 + 基础召回** | 1-2 周 | 完整 runtime_state + RAG Layer 1 + 461 prompts 标注（A/A- 优先） + immersive_mode | "写到第 N 章不崩 + 召回辅助卡片 + 沉浸写作模式" | ✅ 已完成 |
| **S3: RAG 增强 + 标注扩展** | 1 周 | RAG Layer 2/3 + B/B+ 卡补示例 + scout-1 风险治理 | "向量召回 + LLM rerank + 召回质量提升" | ✅ 已完成 |
| **S4: Phase 2 缺口 + 用户反馈循环** | 持续 | N/P/D/V 阶段 + 多技能扩展 + 4 scout 全部建议落地 | "完整 pipeline + 持续优化" | 🔄 持续；native `sqlite-vec` + RAG 真实召回质量评估已完成 |

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

### 4.2 已完成增补（2026-05-14）

- [x] **S4-RAG-1**：native `sqlite-vec` 接入完成。
- [x] **S4-RAG-2**：RAG 真实召回质量评估完成，可跑 `scripts/evaluate_rag_recall.py`。

### 4.3 当前下一步

- [ ] **P2-1**：补 Layer 1 空召回 metadata，明确空结果原因与诊断字段。
- [ ] **P2-2**：为评估查询维护 `expected_ids` / `relevant_ids`。
- [ ] **P2-3**：把 RAG 质量评估从「能跑」升级为可追踪、可回归。

### 4.4 任务清单（按触发条件优先级，尚未触发）

- [ ] **F2-1**：N0/N1 立项市场层（决策 6 / 触发：用户主动需要立项调研）
- [ ] **F2-2**：P1-P3 后处理与排版（触发：用户发布到 Coding/CNB）
- [ ] **F2-3**：D1-D3 数据分析与复盘（触发：已有发布数据可分析）
- [ ] **F2-4**：V2 版本管理（触发：项目 ≥10 部作品）
- [ ] **F2-5**：第 3+ skill 接入（按用户需求）

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

**当前下一步**：以 `STATUS.md` 为准；截至 2026-05-14，下一步是 P2：补 Layer 1 空召回 metadata，并维护评估查询的 `expected_ids` / `relevant_ids`。

---

## 附录 A：阶段 0-4 全流水线回顾

| 阶段 | 内容 | 状态 | 产出 | 完成日期 |
|---|---|---|---|---|
| 0 | 项目骨架（notepad + 看板 + 草稿） | ✅ | `notepad.md` | 2026-05-12 |
| 1 | 4 Scout 并行深扫 | ✅ | `.ops/scout-reports/scout{1,2,3,4}-*.md` | 2026-05-13 03:30 |
| 2 | 主 agent 综合蒸馏方案 | ✅ | `_distillation-plan.md` 47.6KB | 2026-05-13 10:07 |
| 3 | Ark Jury Court 4 角法庭 | ✅ | `.ops/jury/jury-{1-4}-*.md` 共 32KB / 4 票 revise | 2026-05-13 17:43 |
| 4 | 综合判决与交付 | ✅ | `ARCHITECTURE.md` + `ROADMAP.md` | 2026-05-13 17:55 |

**全程时间线**：2026-05-12 22:40 → 2026-05-13 17:55，约 19 小时（含中断与多轮 endpoint 救火）。

**用户偏好实践**：
- ✅ "不要省事的简单方案"：阶段 3 跑了完整 4 角法庭，未压成 2 角
- ✅ "多思考多花时间"：scout-3 破例第 3 次重派 + 阶段 3 经历 3 轮 endpoint 救火
- ✅ "保留双 skill 一级公民地位"：ARCHITECTURE §〇 / §四 / §六 三处明示
- ✅ "兼容并增强已有 skill"：Skill Runtime 子层专设 + immersive_mode 新增气质保护
