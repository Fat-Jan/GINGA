# v1.9 Story Truth Template 规划

> 面向后续 AI 代理：本文件只定义「从原料整理小说真值模板」的规划、字段矩阵和验收边界，不实现 schema、不写 `runtime_state`、不改默认 RAG、不把拆书候选或报告自动晋升为真值。实现前必须重新读取 `STATUS.md`、`.ops/governance/candidate_truth_gate.md` 和本计划。

## 目标

把 `_原料/基座/`、Foundation schema、题材 profile、prompt card 分类、runtime_state、longform review 经验和 v1.3 拆书产物，整理成一套可实现的小说真值模板规划。

正确顺序是：

1. 先从原料归纳通用真值模板。
2. 再用拆书产物、题材系列和长篇 drift 证据做缺口校验。
3. 最后才设计 schema、validator、StateIO 写入和 workflow 接入。

## 当前结论

单一 Story Bible 不够。Ginga 需要的是分层真值模板：

- 项目契约
- 题材契约
- 故事架构
- 角色与势力
- 世界与体系
- 爽点 / 钩子 / 伏笔账本
- 章节输入包
- 运行状态账本
- 风格锁
- 候选池与晋升门禁

其中只有经过确认的作品事实和运行状态能进入 `truth`。`trope_recipe_candidate`、review report、market report、jury 原文和 `.ops/book_analysis/**` 仍是 `candidate-only` 或 `report-only`，不能默认进入 `StateIO`、默认 RAG、workflow prompt 或 provider input 白名单。

## 原料字段矩阵

| 模板层 | 字段族 | 主要来源 | 是否核心 | 是否题材扩展 | 真值落点建议 |
|---|---|---|---|---|---|
| 项目契约 | 作品定位、目标平台、目标读者、总字数、更新频率、核心卖点、付费点、留存目标 | `010-018` 创意阶段、`071-075` 商业化、题材指南 | 是 | 部分是 | `locked.PROJECT_CONTRACT` |
| 题材契约 | 核心爽点、读者期待、黄金三章、情绪弧线、钩子策略、章节结构、平台策略、禁忌清单 | `_原料/基座/题材/网文/*.md`、`foundation/schema/genre_profile.yaml` | 是 | 是 | `locked.GENRE_CONTRACT` |
| 故事架构 | 总纲、卷纲、章纲、三幕结构、关键转折、冲突升级、主题载体 | `020` 故事框架、`030-038` 框架阶段 | 是 | 否 | `locked.PLOT_ARCHITECTURE` + 新增 outline projection |
| 角色与势力 | 主角、配角、反派、阵营、势力资源、关系网络、行为模式、成长弧线 | `022`、`024-029`、题材系列角色文件 | 是 | 是 | `locked.CAST_CONTRACT` + `entity_runtime.CHARACTER_STATE` |
| 世界与体系 | 世界类型、地理、历史、文化、法律、经济、力量体系、官职 / 宗门 / 家族、金手指 | `021`、`023`、`027`、古代官职 / 亲族 methodology | 是 | 是 | `locked.WORLD` + `locked.SYSTEM_CONTRACTS` |
| 爽点账本 | 爽点类型、密度、读者回报、压抑-释放、重复风险、后续爽点储备 | 题材指南、`052` 爽点设计、`054` 节奏校准、v1.7 review | 是 | 是 | `entity_runtime.PAYOFF_LEDGER` |
| 钩子 / 伏笔账本 | 章末钩子、悬念、伏笔 ID、埋设章、回收章、状态、多重解释、遗忘风险 | `053` 悬疑伏笔、题材指南、runtime_state | 是 | 部分是 | `entity_runtime.FORESHADOW_STATE` + `entity_runtime.HOOK_LEDGER` |
| 章节输入包 | 本章目标、场景纲、段落蓝图、关键句、出场角色状态、相关世界规则、风险提示 | `038` 创作输入包、`096` 写作准备清单 | 是 | 否 | `workspace.CHAPTER_INPUT_BUNDLE` |
| 运行状态账本 | 角色状态、资源、关系、事件历史、全局摘要、章节游标、上次安全状态 | `042` 状态管理、`foundation/schema/runtime_state.yaml` | 是 | 部分是 | 现有 `entity_runtime` / `workspace` |
| 风格锁 | 叙事视角、文风、对白风格、句式密度、禁用腔调、低频题材锚点、反 AI 味指标 | `045`、`049`、`060`、v1.8 style fingerprint | 是 | 是 | `locked.STYLE_CONTRACT` + report-only review |
| 候选池 / 晋升门禁 | 候选来源、人工接受、schema 校验、污染检查、写入口、审计证据 | v1.3 trope recipe、`.ops/governance/candidate_truth_gate.md` | 是 | 否 | `.ops/**` candidate + promote validator |

## 题材扩展槽

通用模板只定义扩展口，不把所有题材字段硬塞进核心 schema。初始扩展槽按题材族划分：

| 题材族 | 专属字段例子 | 风险 |
|---|---|---|
| 规则怪谈 / 悬疑 | 规则、违反后果、副本、漏洞、真相层级、推理链 | 规则可随意改、恐怖氛围被消解、主角无视规则 |
| 修仙 / 高武 / 玄幻 | 境界、资源、突破条件、战力差、禁忌力量、宗门 / 家族 | 越级无因果、战力膨胀、突破无代价 |
| 宫斗 / 历史 / 古代 | 官职、礼法、亲族、家族资源、证据链、制度门槛 | 现代口吻、官职错位、一句话开路 |
| 都市 / 直播 / 电竞 | 平台数据、粉丝、战队、比赛、商业资源、舆论 | 数据无账本、职业细节悬浮、爽点重复 |
| 替身 / 狗血 / 女频情感 | 误认、白月光、情感债、真相揭露、追妻 / 反转节点 | 情感推进过快、虐点无回报、角色动机断裂 |
| 种田 / 年代 / 现实 | 生活资源、邻里关系、产业、时代约束、细节素材 | 现实悬浮、资源变化无账本、日常无钩子 |

## 与拆书产物的关系

拆书产物不决定模板底座，只用于缺口校验：

- `trope_core` 检查模板是否能承载桥段抽象。
- `reader_payoff` 检查爽点账本是否有读者回报字段。
- `trigger_conditions` 检查章节输入包是否有触发条件和前置状态。
- `variation_axes` 检查题材扩展槽是否支持换题材 / 换身份 / 换冲突规模。
- `forbidden_copy_elements` 检查候选晋升门禁是否能阻断原文污染。

任何拆书候选进入 truth 前，仍必须满足 `.ops/governance/candidate_truth_gate.md` 的 `operator_accept`、`schema_validation`、`source_contamination_check`、`StateIO_or_validator_entrypoint` 和 `audit_evidence`。

## 非目标

- 不在本轮新增 `foundation/schema/story_truth_template.yaml`。
- 不新增或修改 `StateIO` 写入域。
- 不把 `.ops/book_analysis/**` 纳入默认 RAG。
- 不让 review / market / jury report 反向注入创作 prompt。
- 不把 `BookView` projection 当第二状态真值。
- 不做真实 LLM 生成验证。

## 后续实现拆分

### v1.9-1：原料字段矩阵固定

产物：

- `.ops/plans/v1-9-story-truth-template-plan.md` 补齐字段矩阵。
- `.ops/reports/story_truth_template_source_audit.md` 记录抽样来源、覆盖范围和遗漏风险。

验收：

- 每个模板层至少有 1 个原料来源。
- 明确字段归属：core / genre_extension / candidate_only / report_only。
- 不修改 schema、不写 StateIO。

### v1.9-2：schema 草案与 validator 设计

产物：

- `foundation/schema/story_truth_template.yaml` 草案。
- `scripts/validate_story_truth_template.py` 只读 validator。
- 单元测试覆盖必填字段、题材扩展、候选禁入、report 禁入。

验收：

- validator 能拒绝 candidate/report 直接进入 truth。
- validator 能区分通用核心字段和题材扩展字段。
- 架构契约仍通过。

### v1.9-3：StateIO 窄切片

产物：

- 只选择 1 个安全落点做窄切片，例如 `locked.PROJECT_CONTRACT` 或 `locked.GENRE_CONTRACT`。
- 对应初始化 provider / CLI 参数 / 单元测试。

验收：

- 写入必须经 `StateIO`。
- 不扩大默认 RAG。
- `scripts/run_agent_harness.py` 通过。

### v1.9-4：章节输入包接入

产物：

- `workspace.CHAPTER_INPUT_BUNDLE` 只读构建器。
- 章节生成前 preflight 检查：角色状态、世界规则、伏笔操作、爽点目标、风格锁、风险提示。

验收：

- mock harness 能看到输入包。
- 输入包不得读取 `.ops/book_analysis/**`、market raw text 或 report-only 目录。

### v1.9-5：长篇质量回归

产物：

- 基于 v1.7-3 的 4 章默认 / 5 章上限，跑小规模真实 LLM 回归。
- review report 只做 report-only 证据。

验收：

- 不自动改正文。
- 不把 review report 写入 truth。
- 对比是否改善开篇回环、低频锚点缺失和伏笔缺失。

## 最小下一步

下一步不是直接写 schema。最小可开工任务是 **v1.9-1 原料字段矩阵固定**：

1. 抽样读取 `_原料/基座/` 的创意、设定、框架、创作、进阶、数据分析、商业化、题材系列文件。
2. 生成 `.ops/reports/story_truth_template_source_audit.md`。
3. 只同步 `STATUS.md` / `ROADMAP.md` / `notepad.md` 的 planned 索引。
4. 再决定是否进入 v1.9-2 schema 草案。

