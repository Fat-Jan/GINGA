# Story Truth Template Source Audit

日期：2026-05-16
范围：v1.9-1 原料字段矩阵 / source audit
产物边界：本报告只做字段归纳、来源审计和 v1.9-2 建议；不新增 schema、不写 `StateIO`、不改默认 RAG、不修改正文。

## 结论

Ginga 的 Story Truth Template 应按分层 truth surface 设计，而不是合成单一 Story Bible。可直接进入 truth 设计的字段只应来自 `_原料/基座/**` 的通用创作流程、已治理 Foundation schema 和经 `StateIO` 管理的运行状态语义；`.ops/book_analysis/**`、review / market / jury report 只能作为 gap-check、candidate-only 或 report-only 证据，不能直接进入 truth、默认 RAG、workflow prompt 或 provider input 白名单。

## 采样范围

### 规划和治理边界

- `.ops/plans/v1-9-story-truth-template-plan.md`：定义 v1.9 分期、字段矩阵、非目标和 candidate/report 禁入边界。
- `.ops/governance/candidate_truth_gate.md`：定义 `candidate-only`、`report-only`、`truth` 三类输出与晋升条件。
- `STATUS.md`：确认 v1.9 仍为 `planned`，v1.9-1 只做 source audit，不能直接写 schema / StateIO。

### 通用原料样本

- `_原料/基座/010-创意阶段-灵感收集整理.md`
- `_原料/基座/012-创意阶段-项目立项评估.md`
- `_原料/基座/017-创意阶段-题材卖点确定.md`
- `_原料/基座/021-设定阶段-世界观构建.md`
- `_原料/基座/022-设定阶段-人物角色设定.md`
- `_原料/基座/023-设定阶段-等级体系设计.md`
- `_原料/基座/030-框架阶段-大纲制作.md`
- `_原料/基座/036-框架阶段-细纲制作.md`
- `_原料/基座/038-框架阶段-创作输入包.md`
- `_原料/基座/040-创作阶段-章节创作.md`
- `_原料/基座/042-创作阶段-状态管理.md`
- `_原料/基座/045-创作阶段-风格优化.md`
- `_原料/基座/052-进阶技巧-修订润色.md`
- `_原料/基座/053-进阶技巧-悬疑伏笔.md`
- `_原料/基座/054-进阶技巧-节奏校准.md`
- `_原料/基座/061-数据分析-阅读体验审校.md`
- `_原料/基座/071-商业化-读者画像.md`
- `_原料/基座/072-商业化-热度预测.md`
- `_原料/基座/096-额外功能-写作准备清单.md`

### 题材扩展样本

- `_原料/基座/题材/网文/guize-guaitan.md`
- `_原料/基座/题材/网文/xiuxian.md`
- `_原料/基座/题材/网文/lishi-gudai.md`
- `_原料/基座/题材/网文/dushi-richang.md`
- `_原料/基座/题材/网文/zhihu-duanpian.md`
- `_原料/基座/题材/网文/moshi.md`

### 现有 schema / sidecar 反查样本

- `foundation/schema/runtime_state.yaml`
- `foundation/schema/genre_profile.yaml`
- `.ops/book_analysis/p0_mvp_boundary.md`
- `.ops/book_analysis/contamination_check_rules.md`
- `.ops/book_analysis/schema/source_manifest.schema.yaml`
- `.ops/book_analysis/v1-3-1-smoke-main/source_manifest.json`
- `.ops/book_analysis/v1-3-2-smoke-main/chapter_atoms.json`
- `.ops/book_analysis/v1-3-3-smoke-main/trope_recipes.json`
- `.ops/book_analysis/v1-3-3-smoke-main/trope_recipe_report.md`
- `.ops/reports/longform_jiujiu_v173_45_regression.md`
- `.ops/validation/longform_jiujiu_v173_45_regression.json`
- `.ops/reports/longform_jiujiu_v173_45_regression_findings.md`
- `.ops/reviews/longform-jiujiu-v173-45-regression/v1-7-3-45-regression-review/review_report.json`
- `.ops/jury/longform_reviewer_queue_2026-05-15/human_review_brief.md`

## 字段矩阵

| 模板层 | 字段族 | 证据路径 | 分类 | Truth 落点建议 | 审计判断 |
|---|---|---|---|---|---|
| 项目契约 | 作品标题、一句话故事、题材、目标平台、目标读者、总字数、更新节奏、核心卖点、差异化、风险清单 | `_原料/基座/010-创意阶段-灵感收集整理.md`, `_原料/基座/012-创意阶段-项目立项评估.md`, `_原料/基座/017-创意阶段-题材卖点确定.md` | core | `locked.PROJECT_CONTRACT` 或 `locked.STORY_DNA` 扩展 | 可作为 truth schema 核心字段，但市场评分/趋势判断需标注来源和时间，不应自动覆盖作品事实。 |
| 题材契约 | 核心爽点、读者期待、黄金三章、留存目标、情绪弧线、章节结构、钩子策略、平台策略、禁忌清单 | `_原料/基座/题材/网文/guize-guaitan.md`, `_原料/基座/题材/网文/xiuxian.md`, `_原料/基座/题材/网文/lishi-gudai.md`, `foundation/schema/genre_profile.yaml` | genre_extension | `locked.GENRE_CONTRACT` 或引用 `genre_profile` | 应保留为题材 profile 引用 + 项目级覆写，不要把所有题材字段塞入 core。 |
| 故事架构 | 总纲、阶段划分、卷/章范围、关键转折、章节功能、核心事件、情绪曲线、写作指导 | `_原料/基座/030-框架阶段-大纲制作.md`, `_原料/基座/036-框架阶段-细纲制作.md`, `foundation/schema/runtime_state.yaml` | core | `locked.PLOT_ARCHITECTURE` + outline projection | 可进核心。章节级明细应做 projection 或 workspace 输入，不应长期堆入 locked。 |
| 角色与势力 | 主角、配角、反派、身份背景、性格核心、能力、成长轨迹、关系网络、阵营/势力资源 | `_原料/基座/022-设定阶段-人物角色设定.md`, `_原料/基座/040-创作阶段-章节创作.md`, `foundation/schema/runtime_state.yaml` | core + genre_extension | `locked.CAST_CONTRACT` + `entity_runtime.CHARACTER_STATE` | 稳定设定进 locked；章节变化、情绪、关系、能力冷却进入 runtime。 |
| 世界与体系 | 世界类型、时代背景、地理、历史、社会结构、法律、经济、文化、力量来源、等级、突破条件、代价 | `_原料/基座/021-设定阶段-世界观构建.md`, `_原料/基座/023-设定阶段-等级体系设计.md`, `foundation/schema/runtime_state.yaml` | core + genre_extension | `locked.WORLD` + `locked.SYSTEM_CONTRACTS` | 通用世界字段进 core；修仙境界、古代官职、末世资源等为 extension。 |
| 爽点账本 | 爽点类型、密度、最大间隔、压抑-释放、读者回报、重复风险、后续储备 | `_原料/基座/054-进阶技巧-节奏校准.md`, `_原料/基座/题材/网文/xiuxian.md`, `_原料/基座/题材/网文/moshi.md`, `.ops/reports/longform_jiujiu_v173_45_regression_findings.md` | core + genre_extension + report_only | `entity_runtime.PAYOFF_LEDGER` | 账本字段应进 schema；review findings 只提示缺口，不直接写 ledger。 |
| 钩子 / 伏笔账本 | 伏笔 ID、类型、首次出现、表层理解、真实含义、预期回收章、状态、风险、多重解释、章末钩子类型 | `_原料/基座/053-进阶技巧-悬疑伏笔.md`, `_原料/基座/030-框架阶段-大纲制作.md`, `foundation/schema/runtime_state.yaml` | core + genre_extension | `entity_runtime.FORESHADOW_STATE` + `entity_runtime.HOOK_LEDGER` | 长篇 hard gate 已证明伏笔标记是生产风险字段，应作为核心账本。 |
| 章节输入包 | 本章目标、功能定位、场景列表、段落蓝图、关键句、角色当前状态、世界规则、素材引用、写作提示、风险清单 | `_原料/基座/038-框架阶段-创作输入包.md`, `_原料/基座/096-额外功能-写作准备清单.md`, `.ops/reports/longform_jiujiu_v173_45_regression_findings.md` | core | `workspace.CHAPTER_INPUT_BUNDLE` | v1.7-4 drift 复核显示这是下一步最关键的 truth projection，不应读取 `.ops/book_analysis/**`。 |
| 运行状态账本 | 角色状态、资源、关系、事件历史、世界规则变化、章节游标、上次安全状态、审计日志 | `_原料/基座/040-创作阶段-章节创作.md`, `_原料/基座/042-创作阶段-状态管理.md`, `foundation/schema/runtime_state.yaml` | core | 现有 `entity_runtime` / `workspace` / `audit_log` | 已有 schema 基础，v1.9-2 应优先复用，不新建第二状态真值。 |
| 风格锁 | 叙事视角、语言风格、对白风格、句式/段落密度、场景氛围、禁用腔调、反 AI 味检查项 | `_原料/基座/045-创作阶段-风格优化.md`, `_原料/基座/052-进阶技巧-修订润色.md`, `.ops/reviews/longform-jiujiu-v173-45-regression/v1-7-3-45-regression-review/review_report.json` | core + report_only | `locked.STYLE_CONTRACT` + review sidecar | 风格目标可进 truth；review 的 style fingerprint / warnings 只能 report-only。 |
| 商业与运营证据 | 读者画像、留存目标、付费触发点、热度预测、传播策略、用户分群、推广建议 | `_原料/基座/071-商业化-读者画像.md`, `_原料/基座/072-商业化-热度预测.md`, 题材 profile 样本 | genre_extension + report_only | `locked.MARKET_CONTRACT` 可选；报告落 `.ops/reports/**` | 目标读者和付费触发可作为项目契约字段；动态市场报告、热度预测不能直接成为 truth。 |
| 候选池 / 晋升门禁 | 候选来源、候选类型、人工接受、schema validation、污染检查、写入口、审计证据、默认 RAG 禁入 | `.ops/governance/candidate_truth_gate.md`, `.ops/book_analysis/contamination_check_rules.md`, `.ops/book_analysis/v1-3-3-smoke-main/trope_recipes.json` | candidate_only | `.ops/**` candidate + promote validator | 是治理核心，不是正文 truth。任何晋升必须显式走 gate。 |

## 分类口径

### core

可进入 v1.9-2 schema 草案的通用字段族：

- 项目契约：标题、题材、premise、目标读者、目标平台、核心卖点、风险清单。
- 故事架构：三幕 / 阶段、章节范围、关键转折、主线冲突、章节功能。
- 角色与势力：角色静态设定、关系网络、阵营、成长目标。
- 世界与体系：世界规则、力量系统、社会结构、资源/制度约束。
- 爽点、钩子、伏笔账本：ID、状态、章节位置、回收计划、读者回报。
- 章节输入包：本章目标、场景/段落蓝图、角色状态引用、世界规则引用、写作风险。
- 运行状态：复用 `foundation/schema/runtime_state.yaml` 的 `locked`、`entity_runtime`、`workspace`、`audit_log`。
- 风格锁：目标文风、视角、对白、句式、禁用腔调。

### genre_extension

应通过题材 profile 或扩展槽承载，不能硬编码进 core：

- 规则怪谈：规则、违反后果、副本、漏洞、真相层级、推理链。
- 修仙 / 玄幻：境界、资源、突破条件、战力差、宗门、功法、代价。
- 历史 / 古代：官职、礼法、亲族、实权链、证据链、制度门槛。
- 都市 / 日常：生活资源、职业场景、关系温度、现实细节、舒缓钩子。
- 知乎短篇：问题引入、第一人称、段落钩子、结尾反转、完整闭环。
- 末世：资源账本、基地发展、生存威胁、人性考验、危险等级。

### candidate_only

以下只可作为候选，不代表当前作品事实：

- `.ops/book_analysis/v1-3-3-smoke-main/trope_recipes.json` 中的 `trope_recipe_candidate`。
- `.ops/book_analysis/v1-3-2-smoke-main/chapter_atoms.json` 派生出的结构性 atom。
- 任何由 `.ops/book_analysis/**` 生成、带 `pollution_source: true` 或 `[SOURCE_TROPE]` 的产物。
- 人工尚未 `operator_accept`、未过 `schema_validation`、未过 `source_contamination_check` 的桥段、方法论或题材变体。

### report_only

以下只能提供证据、风险或建议：

- `.ops/reports/**` 中的长文回归、拆书规划、Genm / oh-story 吸收报告。
- `.ops/reviews/**` 中的 review / deslop / style fingerprint / longform quality gate。
- `.ops/jury/**` 中的外部模型意见、人工终审 brief、jury summary。
- `.ops/market_research/**` 中的市场报告；当前采样时该目录不存在，但 `.ops/governance/candidate_truth_gate.md` 已把它列为 report-only 域。

## 拆书 / 长文 Drift 反向校验发现

### 拆书产物只证明 gap-check 价值

`.ops/book_analysis/p0_mvp_boundary.md` 把第一轮能力限定为 `scan / split / manifest / validator / report`，并明确 `.ops/book_analysis/<run_id>/` 是污染源域。`.ops/book_analysis/contamination_check_rules.md` 要求污染标记、默认 RAG 禁入和 provider 输入白名单禁入。`.ops/book_analysis/v1-3-3-smoke-main/trope_recipes.json` 的候选包含 `trope_core`、`reader_payoff`、`trigger_conditions`、`variation_axes`、`forbidden_copy_elements`，这些字段能反向检查 truth template 是否有承载槽，但不能直接写入 truth。

反向校验结果：

- `trope_core` 要求 Story Truth Template 至少有“桥段抽象 / 读者承诺 / 触发条件”的候选槽。
- `reader_payoff` 要求 `PAYOFF_LEDGER` 显式记录读者回报，而不是只记录剧情事件。
- `trigger_conditions` 要求 `CHAPTER_INPUT_BUNDLE` 能引用前置状态和触发条件。
- `variation_axes` 要求 `genre_extension` 支持题材、身份、冲突规模和场景载体替换。
- `forbidden_copy_elements` 要求 v1.9-2 validator 能拒绝原文实体、原文事件链、谜底、专名、台词进入 truth。

### 长文 drift 反查指向章节输入包和账本

`.ops/validation/longform_jiujiu_v173_45_regression.json` 显示 4+5 共 9 章真实生成脚本级 `passed=true`，短章、禁词、伏笔缺失均未命中；但 `.ops/reports/longform_jiujiu_v173_45_regression_findings.md` 记录 review hard gate 仍因 `consecutive_opening_loop_risk` 和 `missing_low_frequency_anchor` 阻断下一批真实 LLM。

反向校验结果：

- 仅有 `runtime_state` 不足以防止续写重启感官模板；`workspace.CHAPTER_INPUT_BUNDLE` 需要包含“上一章结尾承接点 / 本章开头禁止重启模式 / 场景连续性”字段。
- 组合题材需要 `low_frequency_anchor_ledger` 或等价字段，记录低频但关键的题材锚点，例如末日、规则、血脉等，防止长文过程中被高频主线吞掉。
- `FORESHADOW_STATE` 已经是 hard gate 口径的一部分，应在 truth template 中作为 core，不应只放在报告里。
- review 结论只能作为 `report-only` 缺口证据；不能自动改正文，也不能直接写入 `StateIO`。

## 遗漏字段清单

v1.9-2 schema 草案前建议补齐以下字段族：

- `PROJECT_CONTRACT.target_platform`、`target_reader`、`commercial_promise`、`update_cadence`：原料中反复出现，现有 runtime_state 只有 `topic` / `stage` 不够表达项目契约。
- `GENRE_CONTRACT.profile_ref`、`genre_overrides`、`taboo_checklist`：复用 `foundation/schema/genre_profile.yaml`，并允许项目级覆写。
- `PLOT_ARCHITECTURE.outline_projection_ref`：locked 不应塞完整章纲，需要引用 projection / workspace。
- `CAST_CONTRACT.static_profile` 与 `CHARACTER_STATE.runtime_delta` 的分界：避免角色初设和章节变化互相覆盖。
- `SYSTEM_CONTRACTS.cost_and_limitations`：力量体系、金手指、资源、制度门槛都需要代价字段。
- `PAYOFF_LEDGER.payoff_type`、`density_target`、`delivered_at`、`repeat_risk`、`reserve_pool`。
- `HOOK_LEDGER.hook_type`、`placement`、`strength`、`resolved_by`。
- `FORESHADOW_STATE.surface_meaning`、`true_meaning`、`expected_recovery_range`、`status`、`forgetting_risk`。
- `CHAPTER_INPUT_BUNDLE.previous_chapter_bridge`、`opening_continuity_guard`、`low_frequency_anchors`、`state_refs`、`world_rule_refs`、`risk_prompts`。
- `STYLE_CONTRACT.narrative_pov`、`dialogue_profile`、`sentence_density`、`anti_ai_smell_rules`、`forbidden_tones`.
- `PROMOTION_GATE.source_class`、`operator_accept`、`schema_validation`、`source_contamination_check`、`StateIO_or_validator_entrypoint`、`audit_evidence`。

## 禁止晋升红线

以下内容不得直接晋升为 truth：

- `.ops/book_analysis/**` 下任何 manifest、chapter atom、trope recipe、report、validator 输出。
- 带 `pollution_source: true`、`source_marker: "[SOURCE_TROPE]"` 或 `[SOURCE_TROPE]` 的文件内容。
- `trope_recipe_candidate` 在 `human_review_status != approved` 或 `source_contamination_check != pass` 时。
- review / market / jury report 的原文、外部榜单原文、模型评审原文。
- `.ops/reviews/**` 的 style fingerprint、longform hard gate 结果、reviewer queue 结论。
- `.ops/jury/**` 的模型意见和人工 brief。
- `.ops/market_research/**` 的 raw text、平台采集原文、动态趋势判断。
- 未经 `StateIO` 的 runtime_state 写入，或绕过 Foundation asset validator 的资产写入。
- 任何“为了方便创作”把 candidate/report 加入默认 RAG、workflow prompt 或 provider input 白名单的改动。

## v1.9-2 Schema 建议

建议 v1.9-2 只做 schema 草案和只读 validator，不接 StateIO 写入链：

1. 新增 `foundation/schema/story_truth_template.yaml` 时，使用四层结构：`locked`、`entity_runtime`、`workspace_projection`、`promotion_gate`。
2. core 字段只覆盖跨题材通用契约；题材差异通过 `genre_profile_ref` 和 `genre_extensions` 扩展。
3. validator 必须拒绝 `source_class in [candidate_only, report_only]` 直接进入 truth。
4. validator 必须拒绝路径来自 `.ops/book_analysis/**`、`.ops/reviews/**`、`.ops/jury/**`、`.ops/market_research/**` 的 truth payload。
5. validator 必须区分 `locked` 事实、`entity_runtime` 滚动状态和 `workspace.CHAPTER_INPUT_BUNDLE` 临时输入包。
6. `CHAPTER_INPUT_BUNDLE` 应优先覆盖 v1.7-4 暴露的 drift 缺口：上一章承接、开篇连续性、低频题材锚点、伏笔状态、风格锁引用。
7. `PROMOTION_GATE` 应直接复用 `.ops/governance/candidate_truth_gate.md` 的五条件：`operator_accept`、`schema_validation`、`source_contamination_check`、`StateIO_or_validator_entrypoint`、`audit_evidence`。
8. 单元测试建议至少覆盖：core 必填、genre extension 合法、candidate 禁入、report 禁入、污染路径禁入、章节输入包不读取 `.ops/book_analysis/**`。

## 剩余风险

- 本轮是抽样审计，不是 `_原料/基座/**` 全量字段解析；未覆盖的题材专项文件可能提供新的 extension 字段，但不应改变 core / candidate / report 边界。
- `.ops/market_research/**` 当前采样时不存在，但治理文档已定义其 report-only 边界；后续若目录出现，仍需按 report-only 处理。
- Foundation 现有 `runtime_state.yaml` 已有 `locked.GENRE_LOCKED`、`locked.WORLD`、`entity_runtime` 等结构；v1.9-2 若新增 schema，需避免与现有 schema 形成第二套状态真值。
