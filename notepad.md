# Ginga 小说系统蒸馏项目

## Priority Context

- 定位：Ginga 是以 workflow DSL + skill adapters + StateIO 为真实运行主线的小说创作平台底座，STATUS.md 是当前状态真值。
- 入口：先看 AGENTS.md、STATUS.md、notepad.md、ARCHITECTURE.md。
- 验证：常用 python3 scripts/verify_all.py、python3 scripts/run_agent_harness.py、python3 scripts/evaluate_rag_recall.py。
- 坑点：P2-7C 已收口但仍只证明单章 smoke 边界；v1.7-0 已证明 `久久` 30 章真实 smoke，首个 drift 出现在 10 连发第 19 章；v1.7-1 已把批后状态快照、回环检测、低频题材锚点检测和异常章 reviewer queue 接入 `ginga review`；v1.7-2 已把 queue 先交外部模型评审并生成人工终审 brief；v1.7-3 已收紧正式真实 LLM 批量并启用生成前 hard gate；v1.7-4 已按 4+5 跑完 9 章真实回归，脚本级 drift=stable，但 `ginga review` 仍因第 6-9 章连续开篇回环和第 7/9 章低频锚点缺失阻断下一批，所以不能继续扩大真实生成；v1.8-3 `ginga observability` 只是 report-only evidence pack / workflow stage / migration audit，不跑 workflow、不迁移文件、不写 StateIO；v1.9-1 source audit、v1.9-2 只读 schema / validator、v1.9-3 StateIO 项目/题材契约窄切片、v1.9-4 `workspace.CHAPTER_INPUT_BUNDLE` 已完成，下一步只做小范围回归证据，仍不改默认 RAG；v1.3-5 Reference Sidecar RAG 只证明显式 opt-in 可召回 approved promoted methodology 资产，不证明它会自动进入创作 workflow、默认 RAG 或 prompt 注入；v1.5 Review / deslop 只写 `.ops/reviews/<book_id>/<run_id>/` sidecar，不自动改正文、不写 StateIO、不调用 LLM、rubric 不进入创作 prompt；v1.6 Market Research Sidecar 只在显式授权下读 offline fixture，剥离 raw_text，默认不进 RAG；book_analysis 与市场原文仍不得默认进入 StateIO、RAG、prompt、raw_ideas、Foundation assets/schema 或 explorer/review 白名单。
- 模型：内容生成默认走 ask-llm 端点 `久久`（qwen3.6-max-preview-nothinking，key 在 macOS Keychain）；评审别名 `jiujiu-jury` 已注册为 qwen3.6-max-preview-thinking，但 2026-05-15 对 132KB / 22KB / 5.5KB queue 包均 504，只保留为短输入手动 juror，不进默认 `ask-jury-safe` 主力；每章默认 4000 字；正式真实 LLM 批量生成推荐 4 章、上限 5 章，6 章及以上只作压力测试。

## 项目定位

把 `_原料/` 里 **1002 个 md + 13 txt + 3 思路文件**（总约 6.94 MB）蒸馏成可复用的小说创作底座，并继续收敛为以 `workflow DSL + skill adapters + StateIO` 为真实运行主线的创作平台。

**核心判断**：
- 这堆原料异质性极高：结构化模板（基座）+ 创作哲学（思路）+ 场景卡片（prompts）+ 流水线（阶段 A~M），不能用单一方法处理。
- 简单做法 = 全部塞向量库做 RAG，会丢失结构、丢失依赖、丢失用户已有 skill 的兼容性。
- 正确做法 = 先建数据本体（schema），再建 agent 平台（registry + workflow），最后才上 RAG；新增的 Evidence Pipeline、BookView / explorer、review / deslop、market sidecar 都是围绕主线的 sidecar / projection / report 能力，不替代 `StateIO` 真值，不默认进入 RAG。

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

**下一步**：P2-7C provider 质量与真实 demo 已收口；v1.3-0 到 v1.3-5 拆书融梗支线、v1.4 BookView / explorer、v1.5 Review / deslop、v1.6 Market Research Sidecar、v1.7-0 Longform Production Policy、v1.7-1 Longform Quality Gate、v1.7-2 Reviewer Queue Review 与 v1.7-3 Longform Hard Gate 已完成。v1.7-4 真实 4+5 章回归已给出观察结论：脚本级稳定，但 review hard gate 阻断下一批；真实长篇继续前先修续写输入包和低频锚点保持，仍不自动改正文。

**新增规划**：v1.9 Story Truth Template 已落 `.ops/plans/v1-9-story-truth-template-plan.md`。v1.9-1 source audit、v1.9-2 schema / validator、v1.9-3 `StateIO` 项目/题材契约窄切片、v1.9-4 `workspace.CHAPTER_INPUT_BUNDLE` 已完成；下一步 v1.9-5 只做小范围回归和 report-only 证据。

## 验证

- 4 个 Scout 报告全部存在且包含核心字段 → 阶段 1 完成
- `_distillation-plan.md` 存在且包含 4 层架构具体方案 → 阶段 2 完成
- 4 份陪审意见齐全且包含投票 → 阶段 3 完成
- `ARCHITECTURE.md` + `ROADMAP.md` 存在 → 项目交付

## 坑点

- **Ark Jury Court 不是 CLI**：需用 `ask-codex` + `ask-llm` 各扮 2 角色组装 4 角法庭。
- **规划不能写混 STATUS**：`STATUS.md` 是当前真值，只写已验证完成状态；oh-story 参考路线这类 planned 内容主要进 `ROADMAP.md` / `notepad.md`。
- **oh-story 要分层吸收**：hooks 有生命周期信号价值，references 有操作手册化价值，中文书目目录有人类可读价值；Ginga 要把它们改造成显式 context/gap report、Foundation asset 组织范式、BookView/import-export projection，而不是原样复制为隐式机制或主存储。
- **拆书 / 市场 sidecar 是污染源域**：`.ops/book_analysis/`、外部榜单原文、市场采集原始数据默认不得进入 RAG 或 explorer/review 输入白名单；如要 promote 必须人工审核 + 污染检查。
- **v1.3-0 已有底线文件**：污染检查看 `.ops/book_analysis/contamination_check_rules.md`，P0 边界看 `.ops/book_analysis/p0_mvp_boundary.md`，manifest 草案看 `.ops/book_analysis/schema/source_manifest.schema.yaml`；默认 `recall_config.yaml` 只维护排除清单，不把污染源加入 `recall_sources`。
- **BookView 是 projection**：`ginga inspect` 只输出 `.ops/book_views/<book_id>/<run_id>/`，显著标注真值仍是 StateIO，不得建立第二状态真值。
- **Review 是 warn-only sidecar**：`ginga review` 只输出 `.ops/reviews/<book_id>/<run_id>/review_report.json` 与 `README.md`，用于审稿、去 AI 味和平台 rubric 报告；不得自动改正文，不得写 `runtime_state`，rubric 不得进入创作 prompt。
- **Market Research 是授权 sidecar**：`ginga market --fixture <json> --authorize` 只输出 `.ops/market_research/<book_id>/<run_id>/market_report.json` 与 `README.md`，保留来源、采集时间和数据质量状态；不得复制外部 raw_text，不得进入默认 RAG。
- **用户已有 skill 必须先识别**：思路 2/3 是完整 skill，蒸馏产物必须做差异分析（哪些已有/哪些是新增/哪些可增强）。
- **1002 md 不能塞主上下文**：必须用 Scout 子代理隔离扫描，Scout 把详细报告 Write 到文件，只回主 agent 摘要。
- **基座 vs 提示词库参考有重叠**：必须做去重分析（同样的场景在两个地方都出现，用哪个？合并还是 drop？）。
- **三层标签体系初稿**：题材（网文 + 题材名） × 阶段（设定/框架/创作/数据分析/进阶/微观/中观/宏观/势力/辅助/商业化） × 用途（角色/情节/世界/伏笔/...）—— 字段需 Scout 1 验证标准化。
- **阶段 A~M 与基座的关系**：A~M 是流水线（pipeline），基座是能力库（agents）；两者是垂直关系不是替代关系。
- **派活 executor 选择坑**：救火 Claude API 故障时，`Agent(subagent_type=codex:codex-rescue)` 没用——它本质是 Claude wrapper，仍走 Claude API/dzzzz 网关，跟 `general-purpose` 同源 502。真独立 fallback 只有直接 Bash 调本机 `codex-companion task --background --write`（自定义 OpenAI 端，不过 dzzzz 网关）。完整规则、启动命令、跟踪命令在 `.ops/handoff-to-codex.md`。
- **codex CLI 默认只读沙箱**：派写任务必须显式加 `--write`，否则 codex 知道任务但写不了报告。
- **codex zombie 判定**：`status --all` 看 `phase: starting` 持续 ≥15 分钟、log 无新 `Running command` 推进 ≥10 分钟 → kill 重派。Big brief（如 475 文件横扫）zombie 风险显著高于 small brief（如 3 文件深读）。
