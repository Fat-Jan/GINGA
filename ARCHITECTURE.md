# Ginga 小说创作系统架构（ARCHITECTURE v1）

**版本**：v1（融合阶段 2 蒸馏方案 + 阶段 3 Ark Jury Court 4 角法庭评审）
**取代**：`_distillation-plan.md`（保留作历史档案；本文件为权威架构）
**作者**：主 agent 综合
**完成日期**：2026-05-13
**输入**：
- 蒸馏方案 v1：`_distillation-plan.md`（47.6KB，阶段 2 输出）
- 4 角法庭评审：`.ops/jury/jury-{1-4}-*.md`（共 ~32KB，4 票 revise 一致建议修订）
- 4 Scout 实地报告：`.ops/scout-reports/scout{1-4}-*.md`（共 ~98KB）

**Jury 投票汇总**：

| 法官 | 视角 | 投票 | 核心 P0 主张 |
|---|---|---|---|
| jury-1 (架构师 / grok-4.20) | 架构合理性、边界、依赖 | revise | Platform 层职责过重 → 拆 Orchestrator + Skill Runtime；双 skill 缺正式 contract.yaml |
| jury-2 (数据工程师 / deepseek-v3.2) | schema、去重、召回 | revise | stage 枚举覆盖度缺口；双库去重无可执行规则；RAG 冷暖启动缺失 |
| jury-3 (小说编辑 / grok-4.20) | 创作灵活性、用户体验 | revise | workflow 20+ step 把创作变填表；无 raw_ideas/ 灵感逃逸通道；双 skill 气质被秩序稀释 |
| jury-4 (产品工程师 / deepseek-v3.2) | MVP、ROI、落地 | revise | S1/S2 无独立用户价值；workflow v2 29 step 超载；BLOCKER 决策 1/3/5 必先定 |

---

## 〇、核心交付承诺（Killer Use Case Manifesto）

> 一位作家开始写一部 50 万字以上的"玄幻黑暗"长篇。
> 用裸 ChatGPT，他会卡在第 18 章——资源账本失忆、伏笔回收乱套、主角动机漂移、风格在第 20 章后开始走样。
> 用 Ginga：
> 1. **双 skill 一级公民**：`dark-fantasy-ultimate-engine`（窄通道生产引擎，保黑暗哲学气质）+ `planning-with-files`（仓库协作引擎，保任务规划与续接）；二者不揉合、各管一段、互不干扰。
> 2. **runtime_state 真值**：CHARACTER_STATE / RESOURCE_LEDGER / FORESHADOW_STATE / PLOT_ARCHITECTURE 等 9 类状态文件被锁定为真值源，每章 G/H 写作必须基于真值，结算后才写回。
> 3. **灵感逃逸通道**：凌晨 3 点突发与 schema 不兼容的好点子 → 落到 `foundation/raw_ideas/`，schema 外纯文本暂存，系统只做松散索引不强制解析。
> 4. **沉浸写作专线**：dark-fantasy skill 启用 `immersive_mode` flag，连续多章不打断 state 更新，只在章节块结束时一次性结算，保黑暗连贯气质。
> 5. **个人文风不被误伤**：Meta checker 默认 `warn-only` 模式，作家保留风格最终决定权；aigc-style-detector / character-iq-checker 不再硬 block。

**差异化标语**：
> 「纪律性」（state 真值）+「气质保留」（双 skill 隔离）+「创作自由」（灵感逃逸通道）+「沉浸支持」（immersive_mode）

这是 Ginga 比 ChatGPT / Claude / Cursor 等通用助手在**长篇创作**这一窄场景下的不可替代价值。

---

## 一、四层架构（v1 含修订）

```
┌──────────────────────────────────────────────────────────────────┐
│  Meta 层 — 创作宪法 / 工作纪律 / guard + checker                  │
│  - 真源：思路 1/2/3 抽出的 20 条上位法 + 基座方法论中的硬约束       │
│  - 形态：runtime guard（前置硬阻断）+ checker（后置软审计，默认 warn-only）│
│  - 作用：约束所有下层输出；定义"好"与"雷"                          │
│  - 修订（jury-1 P1）：guard 与 checker 职责显式划分               │
│  - 修订（jury-3 P1）：checker 默认 warn-only，作家可开 block       │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 约束
┌──────────────────────────────────────────────────────────────────┐
│  Foundation 层 — 数据本体 / 资产 schema / 状态真值                 │
│  - 真源：基座 544 模板 + prompts/ 461 卡 + 思路 2 状态卡/账本/伏笔池 + 思路 3 task_plan │
│  - 形态：YAML schema + Markdown 实例 + JSON 状态文件               │
│  - 新增（jury-3 P0）：foundation/raw_ideas/ 灵感暂存区             │
│  - 修订（jury-2 P0）：stage 枚举扩展（+ cross_cutting / profile）   │
│  - 修订（jury-2 P1）：runtime_state 字段子定义 + 类型约束           │
│  - 修订（jury-2 字段补丁 6 条）：见 §3.2                          │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 实例化 / 引用
┌──────────────────────────────────────────────────────────────────┐
│  Platform 层 — 拆为 Orchestrator + Skill Runtime 两子层（jury-1 P0） │
│  ┌────────────────────────────────────────────────┐               │
│  │ Orchestrator: workflow DSL + runner            │               │
│  │  - 唯一 state 操作入口                           │               │
│  │  - workflow MVP 12 step (A-H + R1-R3 + V1)     │               │
│  │  - N/P/D 阶段全部 Phase 2 deferred             │               │
│  └────────────────────────────────────────────────┘               │
│  ┌────────────────────────────────────────────────┐               │
│  │ Skill Runtime: skill registry + adapter        │               │
│  │  - dark-fantasy-ultimate-engine（含 immersive_mode）│         │
│  │  - planning-with-files                          │               │
│  │  - 每个 skill 必须有 contract.yaml              │               │
│  │  - skill 只暴露标准 contract，不直接操作 state  │               │
│  └────────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 召回
┌──────────────────────────────────────────────────────────────────┐
│  RAG 层 — 召回 / 上下文适配 / 卡片注入                             │
│  - Phase 1（MVP）：Layer 1 frontmatter 标签过滤 + top 3 召回       │
│  - Phase 2：Layer 2 向量召回 + Layer 3 LLM rerank                │
│  - 修订（jury-2 P0）：冷启动 / 暖启动状态区分 + stage-specific top_k │
│  - 修订（jury-3 P1）：召回默认可关闭，作家可选"不要打扰我"模式      │
└──────────────────────────────────────────────────────────────────┘
```

### 与 plan v1 草稿的关键修订（4 法官共识）

| 修订点 | 来源法官 | plan v1 | v1 final |
|---|---|---|---|
| Platform 拆子层 | jury-1 P0 | 单层聚合 4 职责 | Orchestrator + Skill Runtime 显式划分 |
| 双 skill contract | jury-1 P0 | "映射表 + 不能动列表" | ginga_platform/skills/*/contract.yaml（io schema / 优先级 / forbidden mutation list） |
| workflow 砍至 12 step | jury-1/3/4 三票 | 29 step (N0-V2) | MVP 12 step (A-H + R1-R3 + V1) / 其余 Phase 2 |
| stage 枚举扩展 | jury-2 P0 | 10 阶段 | 12 阶段（+ cross_cutting + profile） |
| 双库去重可执行规则 | jury-2 P0 | "retain/merge/drop" 三态描述 | 三段判定流程（asset_type 粗筛 → 字段相似度 → 优先级裁决） |
| RAG 冷暖启动 | jury-2 P0 | 单一三层召回 | 冷启动降级 + stage-specific top_k 配置 |
| Meta guard vs checker 显式划分 | jury-1 P1 | 职责描述交叉 | guard 前置硬阻断、checker 后置软审计默认 warn-only |
| raw_ideas/ 灵感暂存区 | jury-3 P0 | 未见 | foundation/raw_ideas/ 新增 |
| dark-fantasy immersive_mode | jury-3 #4 | 每章打断 state | 连续多章不打断，章节块结束才结算 |
| Killer Use Case 宣言 | jury-3/4 #5 | 散落各章 | §〇 开头集中陈述 |

---

## 二、Meta 层：创作宪法

### 2.1 20 条上位法（保持，来自 plan v1 §2.1）

20 条不变。详见 `meta/constitution.yaml`（S1 落地，源 scout-2 思路 1/2/3 提炼）。
按工作 / 创作分组：工作纪律 4 条（防伪造、防过时、防迷信、防 emoji）+ 创作约束 16 条（节奏、感官、对话、角色、伏笔、风格、世界观）。

### 2.2 落地形态（v1 final）

**显式职责划分**（修订 jury-1 P1）：

- **guard（前置硬阻断）**：归 Meta 层；在 step 执行前检查；不通过 → 中断 workflow + 报错。
  - 例：`no-fake-read.guard.yaml`（防伪造）、`latest-text-priority.guard.yaml`（防过时）、`crosscheck-required.guard.yaml`（防迷信）
- **checker（后置软审计）**：归 Meta 层；在 step 输出后检查；不通过 → 默认仅 `warn-only`，作家可主动设 `block`。
  - 例：`aigc-style-detector.checker.yaml`、`character-iq-checker.checker.yaml`、`cool-point-payoff-checker.checker.yaml`

**调用约定**：
- guard 由 Orchestrator 在 step `preconditions` 阶段触发，与 step DSL 联动
- checker 由 Orchestrator 在 step `postconditions` 阶段触发，结果只写入 `runtime_state.audit_log`，不阻塞 workflow（除非作家显式开 `block`）

### 2.3 Meta 层资产清单

```
meta/
├── constitution.yaml                  # 20 条上位法主索引
├── guards/                            # 前置硬阻断（默认全开）
│   ├── no-fake-read.guard.yaml
│   ├── latest-text-priority.guard.yaml
│   └── crosscheck-required.guard.yaml
├── checkers/                          # 后置软审计（默认 warn-only）
│   ├── aigc-style-detector.checker.yaml
│   ├── character-iq-checker.checker.yaml
│   ├── cool-point-payoff-checker.checker.yaml
│   └── ... (按需扩展)
└── user_overrides/                    # 作家个性化关停/开启
    └── checker_mode.yaml              # 每个 checker 的 mode (off / warn / block)
```

### 2.4 设计原则

1. **guard 不可关，checker 可关**：创作宪法的工作纪律不容妥协，创作风格的偏好交还作家
2. **checker 输出不进 prompt**：避免 checker 反馈污染下一轮 LLM 上下文
3. **个人文风优先**：默认 warn-only，杜绝"系统判我 AI 味"的体验

---

## 三、Foundation 层：数据本体

### 3.1 资产类型注册表（保持，5 类）

| asset_type | 来源 | 用途 | S1 schema 文件 |
|---|---|---|---|
| `genre_profile` | 基座 题材/网文/* | 题材全集配置 | `foundation/schema/genre_profile.yaml` |
| `template` | 基座 模板/* | 结构化生成模板（人物、伏笔、悬念、世界观、大纲） | `foundation/schema/template.yaml` |
| `methodology` | 基座 方法论/* | 写作 / 创意 / 市场 / 平台方法论 | `foundation/schema/methodology.yaml` |
| `checker_or_schema_ref` | 基座 方法论/aigc/... | 检查器 / schema 引用 | `foundation/schema/checker_or_schema_ref.yaml` |
| `prompt_card` | prompts/ 461 | JSON-style 场景卡片 | `foundation/schema/prompt_card.yaml` |

### 3.2 统一治理 frontmatter（v1 final，修订 jury-2 6 字段补丁）

**S1 必填字段精简至 8 条**（修订 jury-1 P2 + jury-3 P2 + jury-4 P2）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 全局唯一 id（命名规范见附录 A） |
| `asset_type` | enum | 5 类资产类型之一 |
| `title` | string | 资产标题 |
| `topic` | string[] | 题材标签（如 `[替身, 多子多福, 玄幻黑暗]`） |
| `stage` | enum | **扩展为 12 枚举值**（见 §3.3） |
| `quality_grade` | enum | A / A- / B+ / B / C / D（jury-3 提议 A/A- 优先标注） |
| `source_path` | string | 原始文件路径（基座目录或 prompts/ 目录） |
| `last_updated` | date | ISO 日期 |

**选填字段（S2-S3 渐进补全）**：
- `dedup_verdict` (enum): retain / merge / drop
- **`dedup_against` (string[])** ← jury-2 字段补丁 4：列出可能重复的基座模板 id
- `reuse_scope` (enum): single_genre / cross_genre / universal
- `domain_knowledge_required` (string[])
- `output_contract` (object): 用于召回时匹配
- `fields_required` (string[]): 模板字段清单
- 等

### 3.3 stage 枚举（v1 final，扩展至 12 枚举值）

**修订（jury-2 P0 / 字段补丁 1）**：原 10 阶段枚举遗漏横切规则和题材配置类资产，扩展为 12 枚举值：

```yaml
stage:
  enum:
    # 创作流程阶段（10 个，原方案）
    - ideation        # 立项 / 创意
    - setting         # 世界观 / 设定
    - framework       # 故事框架 / 三幕结构
    - outline         # 大纲
    - drafting        # 章节起稿
    - refinement      # 章节润色 / 终稿
    - analysis        # 数据分析 / 复盘
    - advanced        # 进阶技巧 / 高级模式
    - business        # 商业化 / 市场
    - auxiliary       # 辅助工具
    # 新增 2 个（jury-2 P0）
    - cross_cutting   # 横切规则（如 state-schema、风格锁定、宪法）
    - profile         # 题材全集配置（如 替身文/规则怪谈/欲念描写 等指南）
```

**asset_type → stage 默认映射**（jury-2 字段补丁 2-3 改良）：
- `genre_profile` → `stage=profile`（不再强行套创作阶段）
- `methodology` → `stage` 按 method_family 路由（写作 → drafting / 创意 → ideation / 市场 → business / 平台 → advanced）
- `checker_or_schema_ref` → `stage=cross_cutting`
- `template`, `prompt_card` → 按内容显式标注

### 3.4 资产类专属字段（保持 + jury-2 补丁 2/3）

每个 asset_type 在共用 frontmatter 之上加专属字段：

```yaml
# genre_profile 专属（jury-2 字段补丁 2）
profile_type:
  enum: [full_spectrum, parameter_only]    # 全集指南 / 参数包

# methodology 专属（jury-2 字段补丁 3）
method_family:
  enum: [写作, 创意, 市场, 平台]
rule_type:
  enum: [constraint, enumeration, schema, guide]    # checker 调 constraint，生成器调 enumeration

# template 专属
template_family:
  enum: [角色, 伏笔, 悬念, 大纲, 项目, 世界观]
fields_required: string[]

# prompt_card 专属
card_intent: string                        # 12 大聚类之一（来自 scout-3）
dedup_verdict: enum
dedup_against: string[]                    # 可能重复的基座模板 id（新增）

# checker_or_schema_ref 专属
target_asset_type: string
output_schema: object
```

### 3.5 状态真值 schema（v1 final，修订 jury-2 P1 + jury-3 P1）

**runtime_state 完整字段定义**（修订 jury-2 P1，给具体子字段 + 类型）：

```yaml
runtime_state:
  # locked 域：长篇定稿后锁定，修改需走 patch 流程
  locked:
    STORY_DNA:
      premise: string
      conflict_engine: string
      payoff_promise: string
    PLOT_ARCHITECTURE:
      acts: array<{name: string, chapters: range}>
      pivot_points: array<{ch: int, type: enum, beat: string}>
    GENRE_LOCKED:
      topic: string[]
      style_lock: ref<dark-fantasy-skill.style_lock>

  # entity_runtime：按章节滚动更新
  entity_runtime:
    CHARACTER_STATE:                       # jury-2 P1 要求的字段示例
      <character_id>:
        inventory: array<{item: string, count: int}>
        abilities: array<{skill: string, level: int, cooldown: int}>
        body: {hp: int, mp: int, status: string[]}
        psyche: {mood: string, beliefs: string[], traumas: string[]}
        relations: array<{target: string, type: enum, score: int}>
        events: array<{ch: int, type: string, impact: string}>
    RESOURCE_LEDGER:
      particles: integer                   # 微粒（dark-fantasy 核心）
      currency: integer
      items: array
    FORESHADOW_STATE:
      pool: array<{id: string, planted_ch: int, expected_payoff: int, status: enum}>
    GLOBAL_SUMMARY:
      arc_summaries: array<{arc: string, summary: string, words: int}>
      total_words: integer

  # workspace：planning-with-files 三件套（保持思路 3 原样）
  workspace:
    task_plan: ref<task_plan.md>
    findings: ref<findings.md>
    progress: ref<progress.md>

  # retrieved：RAG 召回结果（每章生成时填充）
  retrieved:
    cards: array<ref<prompt_card>>
    methodology_refs: array<ref<methodology>>

  # audit_log：checker / guard 输出（新增，jury-1 P1 配套）
  audit_log:
    entries: array<{ts: datetime, source: string, severity: enum, msg: string, action: enum}>
```

**locked 域 patch 流程**（修订 jury-3 P1：长篇 30 万字后想改世界观成本太高）：
- 不允许直接覆盖 `runtime_state.locked`
- 修改必须走 `meta/patches/<patch_id>.yaml`：包含 reason / scope / affected_chapters / approval_required
- patch 生效后自动跑 R3 一致性 checker

### 3.6 灵感逃逸通道（新增，jury-3 P0）

```
foundation/raw_ideas/
├── README.md                            # 用法说明：随时可写、不强制 schema
├── <YYYY-MM-DD>-<short-slug>.md         # 单条灵感
└── _index.md                            # 自动维护的索引（标题 + 时间 + 是否已采纳）
```

**约定**：
- 任何 schema 不兼容的点子先扔这里
- 系统只做松散索引（按时间 / 标题 / 关键字），不强制解析
- 作家随时可手动 promote 一条为正式资产（template / prompt_card / runtime_state patch）
- workflow 不会自动消费 raw_ideas/（避免污染 state）

### 3.7 双库去重规则（v1 final，修订 jury-2 P0）

**三段判定流程**（jury-2 P0 推荐）：

```
Step 1 - 粗筛（基于元数据）：
  - 比较 (asset_type, template_family, card_intent, topic) 是否高度重合
  - 不重合 → 直接 retain（独立保留）

Step 2 - 字段相似度（基于内容）：
  - 计算 fields_required / output_contract 的 Jaccard 相似度
  - 相似度 < 0.3 → retain
  - 0.3-0.7 → 进入 Step 3
  - > 0.7 → 走 merge 流程（jury-2 字段补丁 4 dedup_against）

Step 3 - 优先级裁决（基于约定）：
  - 基座模板优先级 > prompts/ 卡片（基座 schema 化更深）
  - genre_specific > cross_genre > universal
  - quality_grade 高者优先
  - 仍冲突 → 标 conflict_pending，进 Phase 2 人工裁决
```

**约束**（jury-2 Q2 补充）：
- 同名不同 schema：保留 `granularity` 高者（template > prompt_card）
- 近似同义但用法相反：链接 Meta 层约束（如"角色降智"宪法 → 自动 drop 脸谱化反派卡片）
- 包含关系：基于字段集比较，超集保留 / 子集 merge

---

## 四、Platform 层：拆 Orchestrator + Skill Runtime 两子层

### 4.1 子层划分（v1 final，修订 jury-1 P0）

```
ginga_platform/
├── orchestrator/                       # workflow runner（唯一 state 操作入口）
│   ├── workflows/
│   │   ├── novel_pipeline_mvp.yaml     # MVP 12 step（A-H + R1-R3 + V1）
│   │   └── novel_pipeline_phase2.yaml  # Phase 2 全量（含 N/P/D/V）
│   ├── runner/
│   │   ├── dsl_parser.py
│   │   ├── step_dispatch.py
│   │   └── state_io.py                 # 所有 state 读写必经此处
│   └── meta_integration/
│       ├── guard_invoker.py            # preconditions hook
│       └── checker_invoker.py          # postconditions hook
└── skills/                             # skill registry + adapter
    ├── dark_fantasy_ultimate_engine/
    │   ├── skill.md                    # 原 skill 文档（不动）
    │   ├── contract.yaml               # 新增：io schema / 优先级 / forbidden mutation
    │   └── adapter.py                  # 调用 skill + 转换 IO 到 runtime_state
    ├── planning_with_files/
    │   ├── skill.md
    │   ├── contract.yaml
    │   └── adapter.py
    └── registry.yaml                   # 列出所有已注册 skill + 启用状态
```

### 4.2 Orchestrator 核心约束

1. **唯一 state 入口**：任何 workflow step 要读写 runtime_state，必须经 `state_io.py`（带事务、带 audit_log）。skill 本身不直接动 state。
2. **DSL → runtime 拆离**：workflow YAML 是声明式，runner 是命令式；DSL 演化不影响 runner，runner 优化不破坏 DSL。
3. **uses_capability 用资产 id**（修订 jury-2 P1）：原方案用文件路径，改为 `uses_capability: base-template-protagonist`，由 registry 解析为路径。

### 4.3 Skill Runtime + 双 skill contract（v1 final，修订 jury-1 P0）

**contract.yaml schema**（必填）：

```yaml
# ginga_platform/skills/dark_fantasy_ultimate_engine/contract.yaml
skill_id: dark-fantasy-ultimate-engine
version: "1.0"
status: active

# 输入契约
inputs:
  topic:
    type: string[]
    required: true
    constraint: "must include one of [玄幻黑暗, 暗黑奇幻]"
  runtime_state.locked.GENRE_LOCKED.style_lock:
    type: ref<style_lock>
    required: true

# 输出契约
outputs:
  chapter_text:
    type: string
    format: markdown
  state_updates:
    runtime_state.entity_runtime.RESOURCE_LEDGER.particles: delta<int>
    runtime_state.entity_runtime.FORESHADOW_STATE: append<foreshadow>

# 优先级（多 skill 共存时仲裁）
priority:
  - when: topic in [玄幻黑暗, 暗黑奇幻]
    score: 100                          # 强绑定
  - when: topic in [其他玄幻]
    score: 30
  - default: 0

# forbidden mutation：skill 不能改的字段
forbidden_mutation:
  - runtime_state.locked.*               # 锁定域只能走 patch
  - meta/constitution.yaml
  - meta/guards/*

# 双向 adapter 约定
adapter:
  input_transform: skill_specific_to_runtime
  output_transform: runtime_to_skill_specific
  state_sync_mode: explicit               # 不自动同步，必须 step DSL 显式调用

# immersive_mode（jury-3 新增）
immersive_mode:
  available: true
  trigger: workflow_flag.immersive_mode=true
  behavior: |
    连续多章不打断 state 更新；
    只在 chapter_block_end signal 时批量结算；
    适用于"沉浸写作专线"。
```

**planning-with-files 的 contract.yaml** 结构相同，关键差异：
- inputs: workspace 三件套 ref
- outputs: workspace 更新 + audit
- forbidden_mutation: runtime_state.locked / runtime_state.entity_runtime
- priority: cross-cutting（不与 dark-fantasy 抢路由）

### 4.4 workflow v2 MVP（v1 final，砍至 12 step，修订 jury-1/3/4 共识）

**MVP 12 step**（A-H 创作主干 + R1-R3 终稿 + V1 验证）：

```yaml
# ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml
name: novel_pipeline_mvp
version: "1.0"
steps:
  # 立项与设定（A-D）
  - id: A_brainstorm
    uses_capability: base-methodology-creative-brainstorm
    preconditions: [guard:no-fake-read]
  - id: B_premise_lock
    uses_capability: base-template-story-dna
    state_writes: [locked.STORY_DNA]
  - id: C_world_build
    uses_capability: base-template-worldview
    state_writes: [locked.GENRE_LOCKED, locked.WORLD]
  - id: D_character_seed
    uses_capability: base-template-protagonist
    state_writes: [entity_runtime.CHARACTER_STATE]

  # 大纲与初始化（E-F）
  - id: E_outline
    uses_capability: base-template-outline
    state_writes: [locked.PLOT_ARCHITECTURE]
  - id: F_state_init
    state_writes: [entity_runtime.*, workspace.*]

  # 章节循环（G-H，可走 immersive_mode）
  - id: G_chapter_draft
    uses_skill: skill-router                 # 由路由决定 dark-fantasy or default
    preconditions: [guard:latest-text-priority]
    state_reads: [locked.*, entity_runtime.*, retrieved.*]
    state_writes: [chapter_text]
  - id: H_chapter_settle
    state_writes: [entity_runtime.*, workspace.progress]
    postconditions: [checker:character-iq, checker:cool-point-payoff]  # warn-only 默认

  # 终稿三件套（R1-R3）
  - id: R1_style_polish
    uses_capability: base-methodology-style-polish
  - id: R2_consistency_check
    postconditions: [checker:aigc-style, checker:consistency]
  - id: R3_final_pack
    state_writes: [GLOBAL_SUMMARY.arc_summaries[]]

  # 版本验证（V1）
  - id: V1_release_check
    postconditions: [checker:dod-final]
```

**Phase 2 deferred 阶段**（明示，不在 MVP）：

- N0 / N1 立项市场调研（jury-4 决策 6 DEFER）
- P1-P3 后处理 / 排版 / 发布
- D1-D3 数据分析 / 复盘
- V2 版本管理

### 4.5 dark-fantasy immersive_mode（新增，jury-3 #4）

启用条件：workflow 调用时传 `immersive_mode=true` flag。
行为变更：
- G_chapter_draft → G_chapter_draft：连续 N 章不打断
- H_chapter_settle → 推迟到 `chapter_block_end` signal（作家显式触发）
- runtime_state.entity_runtime 在沉浸期内只 append `pending_updates`，不立即结算
- checker 全部静默（不 warn）
- 退出沉浸期：批量 apply pending_updates + 跑一次 R2 一致性

**用途**：dark-fantasy 长篇连续作业的「窄通道」气质保护。

---

## 五、RAG 层：分 Phase 实施

### 5.1 三层召回策略（v1 final，修订 jury-2 P0 + jury-3 P1）

```
Layer 1 — frontmatter 标签过滤（MVP 必做）
  - 输入：当前 stage / topic / asset_type 过滤器
  - 输出：候选集（按 quality_grade 排序）
  - 冷启动：✅ 直接可用
  - 实现：sqlite + JSON-Path

Layer 2 — 向量召回（Phase 2）
  - 输入：当前 prompt context 嵌入向量
  - 输出：top_k 召回（按余弦相似度）
  - 冷启动：❌ 需先嵌入 461 卡 + 部分基座
  - 实现：sqlite-vec 或 faiss

Layer 3 — LLM rerank（Phase 2，可选）
  - 输入：Layer 2 输出 top 10
  - 输出：rerank top 3
  - 性价比：jury-1 P2 提示待验证，默认关闭
```

### 5.2 冷暖启动策略（v1 final，修订 jury-2 P0）

```yaml
# foundation/rag/recall_config.yaml（新增，jury-2 字段补丁 6）
cold_start:
  enabled_layers: [1]
  fallback_sort_by: [quality_grade, last_updated]
  log_degradation: true

warm_start:
  enabled_layers: [1, 2]
  layer3_optional: true

stage_specific_top_k:
  ideation: 20                            # 高召回，需要广撒网
  setting: 15
  framework: 10
  outline: 10
  drafting: 5                             # 高精度，避免素材打断节奏
  refinement: 3                           # 强制重排
  default: 5

enable_rerank_by_stage:
  refinement: true
  drafting: false
  default: false
```

### 5.3 召回禁忌（保持 + 新增 jury-3 P1）

- 不召回 Meta 层资产到 LLM context（guard / checker 不进 prompt）
- 不召回 runtime_state.locked 到 LLM 输入（避免重写锁定域）
- 不召回 raw_ideas/（保持灵感原始形态）
- **新增**：作家可全局关闭召回（`workflow.rag_mode=off`），系统不主动注入卡片

### 5.4 召回源（保持）

```yaml
recall_sources:
  - prompts/                              # 461 卡（quality_grade A/A- 优先标注）
  - 基座/方法论/                          # 写作 / 创意 / 市场 / 平台
  - 基座/题材/网文/                       # 题材 profile（jury-2 字段补丁 2 区分 full_spectrum / parameter_only）
```

---

## 六、与已有 skill 的集成策略（保持 + 修订 jury-1 P0）

### 6.1 集成路径

1. **不修改 skill 文档**：思路 2/3 文档原样进 `ginga_platform/skills/<skill>/skill.md`
2. **写 contract.yaml**：每个 skill 必须有正式 contract（§4.3）
3. **写 adapter**：双向 IO 转换 + state 边界保护
4. **registry.yaml**：列出所有 skill + 启用状态 + 路由优先级

### 6.2 兼容性边界（保持 jury-1 P0 强化）

- skill 不直接读写 runtime_state（必经 adapter → state_io.py）
- skill 内部维护的 4 类文档（思路 2 状态卡 / 账本 / 伏笔池 / 思路 3 task_plan）通过 adapter 双向同步到 runtime_state
- 冲突仲裁：以 runtime_state 为 true source，skill 内部表述为缓存

### 6.3 双 skill 关系（保持）

- 平行关系，不揉合
- 路由由 `skill-router`（ginga_platform/orchestrator）基于 contract.yaml priority 决定
- 默认硬绑定（决策 7）：topic=玄幻黑暗 强制路由 dark-fantasy；其他 topic 走 default_writer

---

## 七、8 决策最终判决

| # | 决策 | plan 推荐 | jury-4 | 最终判决 | 关键约束 |
|---|---|---|---|---|---|
| 1 | 双 skill 是否保留独立 | 保留 | **BLOCKER** | **APPROVE 保留** | 必须补 contract.yaml（jury-1 P0） |
| 2 | prompts/ 461 是否全入 RAG | 全入 | DEFER | **APPROVE 全入**（按 quality_grade 排序） | MVP 只用 Layer 1 + A/A- 优先标注 |
| 3 | runtime_state 单一/分布式 | 合一 schema 物理分文件 | **BLOCKER** | **APPROVE 合一** | 字段子定义 §3.5 完整化（jury-2 P1） + locked patch 流程（jury-3 P1） |
| 4 | 方法论是否拆 sub-section | 拆 | DEFER | **APPROVE 拆** | 加 rule_type 字段（jury-2 字段补丁 3） |
| 5 | workflow 29 step vs MVP 12 step | MVP 12 step | **BLOCKER** | **APPROVE MVP 12 step** | 三票一致；N/P/D/V Phase 2 deferred |
| 6 | 补 N0/N1 立项市场层 | 是 | DEFER | **DEFER Phase 2** | 不在 MVP；用户可手动跑 |
| 7 | 风格锁定硬绑定 玄幻黑暗 | 默认硬绑 + override | IMPORTANT | **APPROVE 默认硬绑 + 显式 override** | checker 默认 warn-only（jury-3 P1） |
| 8 | terminal output 格式 | .md + frontmatter / 章节正文纯文本 | IMPORTANT | **APPROVE 双轨格式** | 默认输出位置在 workspace/output/ |

**3 个 BLOCKER 全已落地**：S1 任务清单（ROADMAP §一）已包含决策 1/3/5 的实施任务。
**3 个 DEFER 明示**：决策 2/4/6 不卡 MVP，Phase 2 落地。
**2 个 IMPORTANT 已对齐**：决策 7/8 在 S1 内已有默认值。

---

## 八、MVP 边界 vs Phase 2 deferred 清单

### MVP（Sprint 1-3 完成，~3-5 周）

**包含**：
- ✅ Meta 层：20 条宪法 + 3 个核心 guard + 5 个常用 checker（warn-only 默认）
- ✅ Foundation 层：5 类 schema + raw_ideas/ + runtime_state 完整字段
- ✅ Platform 层：Orchestrator + Skill Runtime + 12 step workflow + 双 skill contract.yaml
- ✅ RAG 层：Layer 1 frontmatter 过滤 + 冷启动策略 + stage-specific top_k
- ✅ 双 skill immersive_mode（dark-fantasy 沉浸专线）
- ✅ 端到端 demo：从创意输入到第一章产出（S1 末尾）+ 多章连载（S2 末尾）

**不包含**（明示）：
- ❌ workflow N0/N1 立项市场层（决策 6 DEFER）
- ❌ workflow P/D/V 后处理与版本管理（决策 5 配套 DEFER）
- ❌ RAG Layer 2/3（向量召回 + rerank，Phase 2）
- ❌ 461 prompts 全量 quality_grade 标注（A/A- 优先，其他迭代）
- ❌ B/B+ 卡补示例（scout-3 优化点，Phase 2）
- ❌ 第 3 个 skill 接入（仅双 skill MVP）

### Phase 2（持续，按需推进）

| Phase 2 项 | 触发条件 | 预估投入 |
|---|---|---|
| RAG Layer 2 向量召回 | MVP 跑通 5+ 长篇 / 召回不准抱怨 | 1-2 周 |
| RAG Layer 3 rerank | Layer 2 召回精度不达标 | 1 周（可选） |
| N0/N1 市场层 | 用户主动需要立项调研 | 1 周 |
| P1-P3 后处理 | 用户开始发布到 Coding/CNB | 1 周 |
| D1-D3 数据分析 | 已有发布数据可分析 | 1-2 周 |
| V2 版本管理 | 项目 ≥10 部作品 | 1 周 |
| 第 3+ skill 接入 | 用户提出新需求 | 1-2 周 / skill |
| B/B+ 卡补示例 | RAG 召回质量提升需要 | 持续 |

---

## 附录 A：资产路径约定（保持）

```
ginga/
├── meta/
│   ├── constitution.yaml
│   ├── guards/
│   ├── checkers/
│   └── user_overrides/
├── foundation/
│   ├── schema/                          # 5 类 schema 定义
│   ├── assets/                          # 治理后的资产（含 frontmatter）
│   │   ├── base/                        # 来自 _原料/基座/
│   │   ├── prompts/                     # 来自 _原料/提示词库参考/prompts/
│   │   └── doctrine/                    # 来自 _原料/思路/
│   ├── runtime_state/                   # 单部作品的 state 真值
│   │   └── <book_id>/
│   └── raw_ideas/                       # 灵感暂存区（jury-3 P0）
├── ginga_platform/
│   ├── orchestrator/
│   └── skills/
└── rag/
    ├── recall_config.yaml
    ├── prompt_card_index.json           # Phase 2
    └── vector_store/                    # Phase 2
```

**asset_id 命名规范**（jury-2 P1 配套）：
- `base-template-<family>-<slug>`（如 `base-template-character-protagonist`）
- `base-methodology-<family>-<slug>`
- `base-profile-<topic>-<slug>`
- `prompts-card-<intent>-<slug>`
- `doctrine-skill-<skill-id>`

---

## 附录 B：Jury 判决归属表

每条 jury 建议在本架构中的落地位置 / 是否吸收：

| # | jury | 建议 | 落地章节 / 状态 |
|---|---|---|---|
| 1 | jury-1 P0 | Platform 拆 Orchestrator + Skill Runtime | §1 / §4.1 ✅ 吸收 |
| 2 | jury-1 P0 | 补 skill contract.yaml | §4.3 ✅ 吸收 |
| 3 | jury-1 P1 | guard 与 checker 显式划分 | §2.2 ✅ 吸收 |
| 4 | jury-1 P1 | workflow 砍到 12 step | §4.4 ✅ 吸收（三票共识） |
| 5 | jury-1 P2 | Layer 3 rerank 性价比待验证 | §5.1 ✅ 吸收（默认关闭） |
| 6 | jury-1 P2 | S1 必填字段精简至 8 | §3.2 ✅ 吸收 |
| 7 | jury-2 P0 | stage 枚举扩展 + 专用分类 | §3.3 ✅ 吸收 |
| 8 | jury-2 P0 | 双库去重三段判定流程 | §3.7 ✅ 吸收 |
| 9 | jury-2 P0 | RAG 冷暖启动 + stage-specific top_k | §5.2 ✅ 吸收 |
| 10 | jury-2 P1 | runtime_state 字段子定义 + 类型 | §3.5 ✅ 吸收 |
| 11 | jury-2 P1 | uses_capability 改资产 id | §4.2 ✅ 吸收 |
| 12 | jury-2 字段补丁 1-6 | 6 个具体字段补丁 | §3.2 / §3.3 / §3.4 / §5.2 ✅ 全吸收 |
| 13 | jury-3 P0 | workflow 改可选轻模式 + raw_ideas/ | §3.6 / §4.5 ✅ 吸收 |
| 14 | jury-3 P1 | checker 默认 warn-only | §2.2 ✅ 吸收 |
| 15 | jury-3 P1 | locked 域 patch 流程 | §3.5 ✅ 吸收 |
| 16 | jury-3 P1 | RAG 可关闭 | §5.3 ✅ 吸收 |
| 17 | jury-3 改进 4 | dark-fantasy immersive_mode | §4.5 ✅ 吸收（新增子层特性） |
| 18 | jury-3 改进 5 | 简化 runtime_state | ⚠️ 部分吸收（locked 不变，但 patch 流程降低修改成本） |
| 19 | jury-4 P0 | Sprint 重排 / S1 端到端 demo | ROADMAP §一 ✅ 吸收 |
| 20 | jury-4 P1 | workflow 砍 N/R/P/D/V | §4.4 ✅ 吸收（仅保 R1-R3 + V1） |
| 21 | jury-4 P2 | MVP 仅 Layer 1 + Top 18 标注 | §5 / §8 ✅ 吸收 |
| 22 | jury-4 #5 | MVP 用例宣言 | §〇 ✅ 吸收（开头集中陈述） |
| 23 | jury-4 8 决策分类 | BLOCKER/IMPORTANT/DEFER | §七 ✅ 吸收（全盘采纳分类） |

**未吸收 / 部分吸收**：1 项（jury-3 改进 5：完全简化 runtime_state，因 jury-2 提议加强字段定义，二者部分矛盾 → 折中：字段加强 + locked patch 简化）

---

## 附录 C：验收（DoD v1）

阶段 4（本架构）完成的判据：
- [x] 本文件存在
- [x] ROADMAP.md 存在
- [x] 8 个待审决策全部落定（§七）
- [x] 4 jury 23 条建议全部归属表对齐（附录 B）
- [x] MVP 边界明示（§八）
- [x] Phase 2 deferred 清单明示（§八）
- [x] Killer Use Case 集中陈述（§〇）

**最终阶段**：S1 实施启动，进入 Sprint 1（MVP 跑通第一章）。
