# oh-story-claudecode 参考路线规划

日期：2026-05-15

本报告参考 `worldwonderer/oh-story-claudecode` 当前公开仓库与 v0.6.1 release，目标是提炼能丰富 Ginga 的方向，而不是照搬它的 Claude hooks / skill 包结构。

## 一、参考项目可借鉴点

`oh-story-claudecode` 的强项不是单个写作 prompt，而是把网文工作流产品化成一组入口：

- `story-setup`：项目初始化、部署标记、hooks、规则、专职 agent 模板。
- `story-long-write` / `story-short-write`：长篇、短篇分别建模，写作前加载必要上下文。
- `story-long-analyze` / `story-short-analyze`：拆文库流水线，包含章节级原子提取、剧情聚合、角色/设定/关系抽取。
- `story-import`：把已有小说反向解析为标准项目结构。
- `story-review`：多视角审稿，区分 full / lean / solo。
- `story-deslop`：去 AI 味，有量化指标和删除比例保护。
- `story-long-scan` / `story-short-scan`：扫榜采集，重视数据质量状态。
- `story-cover`：封面生成，属于出版运营侧能力。

其中最值得 Ginga 吸收的不是它的文件目录本身，而是 6 个机制：

1. **显式上下文恢复**：会话开始、压缩前后、进度快照、缺口检测。
2. **只读查询 agent**：`story-explorer` 只回答角色、伏笔、设定、时间线、进度，不做创作判断。
3. **章节原子事件提取**：按章节并行提取情节点，使用动态密度、客观白描、角色提及、原文引用。
4. **拆文质量门**：置信度、覆盖率、重叠率、孤立情节兜底、`completed_with_errors`。
5. **多视角审稿**：架构、角色、文字、连续性分工，主线程综合裁决。
6. **工作流产品入口**：扫榜、导入、日更、审稿、去 AI 味、封面，用户能按目的进入系统。

## 二、Ginga 吸收原则

Ginga 当前主线是 P2-7 Platform runner 收敛，真实路径继续向 `workflow DSL + skill adapters + StateIO` 收拢。因此吸收参考项目时要守住以下原则：

- **不照搬 hooks 注入上下文**：`oh-story` 的 hooks 会把输出送进 Claude 系统上下文；Ginga 应改成显式 CLI / report / harness 产物，例如 `ginga inspect context`、`.ops/reports/context_snapshot.md`。
- **不新增第二套状态真值**：参考项目的 `设定/大纲/正文/追踪` 目录可作为导出视图，不可替代 `foundation/runtime_state/<book_id>/`。
- **不把参考原文进默认 RAG**：拆书结果必须保留在 sidecar / `.ops/book_analysis/<run_id>/`，并被标记为污染源域；只产出去来源污染的候选配方。
- **不直接接入 oh-story skill 包为第 3 skill**：它与 Ginga 已有 `dark-fantasy` / `planning-with-files` 边界重叠太大；应按机制拆成 capability provider、checker 或 sidecar workflow。
- **审稿和去 AI 味只做 warn-only**：符合 Meta checker 的既有边界，不能硬改作者风格；平台 rubric 只用于 review report，不进入创作 prompt。

### 2.1 hooks / references / 书目目录的价值与 Ginga 化落点

上一条原则不是否定 `oh-story` 的 hooks、references 或书目目录价值，而是避免原样搬入后破坏 Ginga 的状态真值和显式验证习惯。

| oh-story 机制 | 可吸收价值 | Ginga 化落点 | 不原样吸收原因 |
|---|---|---|---|
| hooks | 会话开始、compact 前后、缺口检测、提交前检查这些生命周期信号很有价值 | 显式 CLI / scripts / reports：`ginga inspect context`、`ginga inspect gaps`、`context_snapshot`、`gap_report` | `.claude/hooks` 隐式注入上下文，容易绕过可回归验证 |
| references | “知识百科”转“操作手册”的组织方式有价值：路由表、输出模板、质量清单、共享文件一致性 | Foundation methodology / prompt asset 的组织范式与 validator；必要时迁移少量结构模板，不复制整库 | Ginga 已有治理后的 assets，直接复制会造成口径冲突和维护重复 |
| 书目目录 | 对作者可读性强，适合设定、大纲、正文、伏笔、时间线的日常浏览 | `BookView` / import-export projection / 发布包；输出到 `.ops/book_views/<book_id>/<run_id>/` 或用户指定导出目录 | 不能替代 `foundation/runtime_state/`，否则形成第二状态真值 |

因此准确说法是：**吸收结构和时机，不原样吸收底层形态；吸收人类可读视图，不替代 StateIO 真值。**

## 三、未来路线建议

### v1.2C：provider 质量与真实 demo 收口（当前主线）

目标：继续收敛当前 asset-backed provider，让离线 harness 与小范围真实 LLM demo 的边界更清楚。

可吸收点：

- 增加 provider 输出可读性：每步输出包含 `provider`、`asset_ref`、输入摘要、质量假设、未覆盖边界。
- 引入 `context_snapshot` 报告：在真实 demo 前生成只读上下文快照，列出 locked/entity/workspace/retrieved/artifact 状态。
- 增加 `gap_report`：类似 `detect-story-gaps`，但显式运行，不做隐式 hook；检查大纲缺失、章节 artifact 缺失、伏笔/时间线空洞、StateIO 审计缺口。

验收：

- `python3 scripts/run_agent_harness.py` 继续 PASS。
- `python3 scripts/verify_all.py` 继续 PASS。
- 真实 LLM demo 报告能区分输入、endpoint、输出路径、不会覆盖的文件与 residual risk。

### v1.3：拆书融梗支线升级为 Evidence Pipeline

目标：把已有 planned 的 `ReferenceTropeDistillation` 从报告规划升级为可验证流水线。

可吸收点：

- 章节切分与 manifest：记录 source hash、chapter hash、字数、章节标题、分块策略。
- `chapter_atom` 提取：每章输出 3-40 个原子事件，保留 excerpt hash / 短引用 / 角色提及 / 事件类型。
- 两步剧情聚合：先识别故事框架，再把原子事件分配到剧情条。
- 质量门：`confidence >= 0.85`、`coverage 85%-95%`、`overlap <= 35%`；不达标时标记 `needs_review`。
- 孤立事件兜底：强相关归入、低置信归入、弱相关归档，不丢弃也不强塞。
- `completed_with_errors`：单章失败不阻断整轮，但报告必须列失败章节和重试状态。

边界：

- P0 只做 `scan / split / manifest / validator / report`。
- P1 才做 `chapter_atom` 与质量门。
- P2 才产出 `trope_recipe_candidate`。
- Promote / Sidecar RAG 仍后置，必须人工审核。
- `trope_recipe_candidate` 不能自动进入任何创作 workflow；未来如需使用，必须通过显式 promote 命令、人工审核和污染检查。
- `chapter_atom`、excerpt hash、剧情聚合结果等所有源自参考作品的文件必须在 manifest 标记 `pollution_source: true`，并在文件头标记 `[SOURCE_TROPE]`。

验收：

- 新增 validator 校验章节数、hash、coverage、overlap、污染红线。
- 输出只落 `.ops/book_analysis/<run_id>/`，不写 `foundation/runtime_state/`，不进默认 RAG。
- validator 检查所有下游模块输入白名单，确认 v1.4 explorer、v1.5 review、创作 provider 都不能隐式读取 `.ops/book_analysis/`。
- RAG 索引流程需有主动排除防护：`.ops/book_analysis/`、外部采集原文和污染源文件必须被配置或 validator 明确排除，即使未来索引源扩展也不能误入默认 RAG。

### v1.4：Book Workspace View 与只读 Explorer

目标：让 Ginga 从“能跑 workflow”进一步变成“能长期维护一部书”的系统。

可吸收点：

- `BookView` 导出：从 `runtime_state` 和 chapter artifacts 生成可读视图：设定、角色、关系、章节、伏笔、时间线、上下文；默认只输出到 `.ops/book_views/<book_id>/<run_id>/`。
- `.active-book` 等价能力：不新增隐藏状态，优先用 CLI 参数或环境变量；如未来需要本地指针，只能放在 `.ops/local/` 这类 sidecar，且不得参与 state 写入决策。
- `ginga inspect context`：读取 StateIO 和 artifacts，输出下一章上下文包。
- `ginga inspect gaps`：只读缺口检查，输出 `.ops/validation/book_gap_report.json`。
- `ginga query` / read-only explorer：支持角色状态、伏笔状态、设定出现位置、进度、时间线、context_load。

边界：

- 导出视图是 projection，不是真值。
- explorer 不做创作建议，不修改文件。
- explorer 数据源必须是洁净白名单：`foundation/runtime_state/` 经 StateIO 读取、chapter artifacts、已验证的 Foundation assets；默认禁止读取 `.ops/book_analysis/`、外部榜单原文、污染源 sidecar。
- 查询来源必须列 `source_files` / `state_domains` / `gaps`。
- 所有 `BookView` 和 explorer 输出必须显著标注：派生视图，不是状态真值；真值以 `foundation/runtime_state/` 和 StateIO 审计为准。

验收：

- explorer 有 deterministic tests。
- gap report 能被 agent harness 覆盖。
- StateIO 仍是 YAML state 域唯一写入口。
- validator 确认 BookView 输出不写 `foundation/runtime_state/`、不进默认 RAG，且不建立长期缓存索引。

### v1.5：Story Review 与 Anti-AI Style Gate

目标：把审稿、去 AI 味、平台评分变成可重复的质量门，但保持 warn-only。

可吸收点：

- `review mode`: `solo` / `lean` / `full`，分别对应单线程检查、结构+连续性检查、多视角评审。
- 四类 reviewer：结构节奏、角色对话、文字 AI 味、状态连续性。
- 平台 rubric：番茄、起点、晋江、知乎盐言等作为 review sidecar，只能被 review report 读取；不作为创作 methodology 注入生成 prompt。
- 去 AI 味量化：禁用词密度、段落句数、对话标签密度、心理词占比、连续排比。
- 删除保护：单次改写不得删除超过阈值；涉及伏笔、钩子、角色特征时只能标注人工审核。

边界：

- checker 默认 warn-only。
- 不自动改正文；若未来实现 rewrite，必须写为新 artifact 或 patch review，不覆盖原章。
- AI 味检测不能压制用户个人文风。
- review / deslop 的输入白名单默认不包含 `.ops/book_analysis/`；需要审查参考拆书报告时必须显式指定污染源模式，并在报告中标注。

验收：

- review report 分 S1-S4 / 高中低，保留 agent 分歧。
- anti-AI style checker 有固定文本 fixture，避免只凭主观判断。
- data-flow test 确认 review rubric 只进入报告生成路径，不进入 G/R/H/R 写作 prompt 组装路径。

### v1.6：Market / Research Sidecar

目标：把扫榜和外部研究变成可审计 sidecar，服务立项但不污染创作状态。

可吸收点：

- 数据来源优先级：浏览器/平台采集 > 用户提供 > 内置历史趋势。
- 采集质量头：有效条目数、字段一致性、数据稀疏、解析异常、登录态缺失。
- 平台差异：起点看付费/追读，番茄看流量/完读，晋江看收藏/积分/营养液，短篇看情绪趋势和传播。
- `market_signal` 报告：题材分布、新题材信号、经典题材变化、书名模式、开头卖点。

边界：

- 外部数据易变，所有报告必须带采集时间和来源。
- 不把榜单原始数据进入默认 RAG。
- 登录态采集需要用户明确授权。

验收：

- 采集失败可标记 `SKIP` / `partial`，不阻断整体报告。
- 报告能被后续立项 workflow 引用，但引用时必须注明时效性。
- 增加 offline mock fixture / deterministic tests，覆盖字段缺失、登录态缺失、解析异常和 partial report。

### v2：出版运营线

目标：当创作主线稳定后，再扩展到发布、封面、数据复盘和版本管理。

候选能力：

- `cover_brief`：从书名、题材、平台、目标读者生成封面 brief。
- `publish_pack`：章节格式、简介、标签、投稿材料。
- `post_publish_analysis`：发布后数据复盘，和原 D1-D3 对齐。
- `versioned_book_release`：长篇多版本、多平台发布记录。

边界：

- 封面生成涉及外部图像 API 和成本，必须显式触发。
- 发布数据属于运营侧，不能反向覆盖锁定设定。

## 四、优先级排序

| 优先级 | 方向 | 原因 |
|---|---|---|
| P0 主线 | v1.2C provider 质量 + context/gap report | 贴合当前主线，风险低，能强化真实 demo 边界 |
| P1-前置 | v1.3-0 Evidence Pipeline 文档补强 + P0 validator | 只能在 P2-7C 后启动；先补污染检查、manifest schema、RAG 排除和 validator，不做内容分析 |
| P1 | v1.3-1/2 chapter_atom + quality gates | 高价值但污染风险高；必须在 v1.3-0 红线通过后推进 |
| P1 | v1.4 read-only explorer / inspect CLI | 长篇维护价值高，但要先保证 StateIO projection 和洁净数据源白名单 |
| P1 | v1.5 review / anti-AI warn-only checker | 能提升成稿质量，但必须防止风格误伤与 rubric 误入 prompt |
| P2 | v1.6 market sidecar | 外部依赖波动大，适合等主线稳定后做 |
| P2 | v2 cover / publish / analytics | 产品化价值高，但不是当前 runner 收敛的前置条件 |

## 五、不原样吸收的部分

- 不原样把 `.claude/hooks` 作为 Ginga 默认机制；吸收其生命周期信号，改成显式 `scripts/` / `ginga inspect` / `.ops/reports`。
- 不原样复制 `oh-story` 的 references 知识库；吸收“操作手册化”的组织方式、模板化输出和一致性校验。
- 不原样引入中文 `设定/大纲/追踪` 为主存储；吸收为 `BookView`、import/export、发布包等人类可读 projection。
- 不把原文拆书库作为默认 RAG source。只允许 sidecar、hash、污染检查、人工 promote。

## 六、建议落地顺序

1. 本报告和 jury 结果只同步到 `ROADMAP.md` / `notepad.md` 的 planned 路线；`STATUS.md` 保持当前状态真值，不写未来规划细节。
2. 下一轮仍优先做 P2-7C，不让新路线抢主线。
3. P2-7C 完成后，启动 v1.3-0 文档补强：污染检查规则、P0 MVP 边界、manifest schema、RAG 排除规则、validator DoD。
4. v1.3-0 验收后，再决定是否进入 v1.3-1 chapter_atom；v1.3-1 通过污染隔离后，才评估 v1.4 explorer 是否进入主线。

## 七、需要 jury 重点评估的问题

- 这些版本线是否和当前 `STATUS.md` 的主线冲突？
- `BookView` / explorer 是否会无意制造第二套状态真值？
- `chapter_atom` / quality gates 是否能降低拆书融梗污染风险？
- review / deslop 是否应该进入 Meta checker，还是作为 Platform report sidecar 更稳？
- market / cover / publish 是否应继续延后到 v2？

## 八、Jury 吸收记录

本路线经过 `ark-jury-court` 风格 feasibility review：

- 默认矩阵：`.ops/jury/oh_story_roadmap_review_2026-05-15/`
- reserve 矩阵：`.ops/jury/oh_story_roadmap_review_2026-05-15_reserve/`

已吸收的高 / 中风险：

- `STATUS.md` 只保留当前状态真值；规划同步到 `ROADMAP.md` / `notepad.md`。
- v1.3 不再与 v1.2C 同列 P0 主线；先做 P2-7C，再做 v1.3-0 文档与 validator。
- `BookView` 输出限定为 `.ops/book_views/<book_id>/<run_id>/` projection，禁止成为第二状态真值。
- explorer 使用洁净数据源白名单，默认禁止读取 `.ops/book_analysis/`。
- `book_analysis` 产物必须标记 `pollution_source: true` / `[SOURCE_TROPE]`，并由 validator 与 RAG 排除机制双重保护。
- 平台 rubric 只用于 review report，不进入创作 prompt。
- market sidecar 必须有 offline mock fixture / deterministic tests。
