# Ginga 蒸馏方案（Distillation Plan）

**版本**：v1 草案
**作者**：主 agent（基于 4 scout 全量证据综合）

> 历史说明：本文件是 2026-05-13 阶段 2 蒸馏草案，已被 `ARCHITECTURE.md` / `ROADMAP.md` 吸收；当前完成度与下一步以 `STATUS.md` 为准。截至 2026-05-14，S1/S2/S3 与 S4/Phase 2 native `sqlite-vec` + RAG 真实召回质量评估均已完成。

**输入**：
- `.ops/scout-reports/scout1-base.md`（30KB / 50 文件实读 / 基座 3 层结构 + schema + Top 18 模板）
- `.ops/scout-reports/scout2-doctrine.md`（25KB / 3 文件完整读 / 用户创作宪法 20 条 + 2 个完整 skill 画像）
- `.ops/scout-reports/scout3-cards.md`（28KB / 461 文件全量实读 / 12 card_intent 聚类 + 场景卡 schema）
- `.ops/scout-reports/scout4-pipeline.md`（15KB / 13 阶段 + Workflow DSL + 状态机 + 缺口分析）

**主结论**：

> 蒸馏的正确姿势不是"重做一个统一大 skill"，而是**把已有 skill 升格为系统中的一级公民**，用四层架构为它们提供约束（Meta）、数据真值（Foundation）、调度（Platform）和召回辅助（RAG）。

---

## 一、四层架构最终版

```
┌──────────────────────────────────────────────────────────────────┐
│  Meta 层 — 创作宪法 / 工作纪律 / 价值红线                          │
│  - 真源：思路 1/2/3 抽出的 20 条上位法 + 基座方法论中的硬约束       │
│  - 形态：runtime guard / 系统级 system prompt 上半 / 输出 schema   │
│  - 作用：约束所有下层输出；定义"好"与"雷"                          │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 约束
┌──────────────────────────────────────────────────────────────────┐
│  Foundation 层 — 数据本体 / 资产 schema / 状态真值                 │
│  - 真源：基座模板（state-schema, 角色卡, 大纲, 伏笔, 悬念, 世界观） │
│         + prompts/ PromptCard 资产类                              │
│         + 思路 2 的状态卡/账本/伏笔池 + 思路 3 的 task_plan 三件套  │
│  - 形态：YAML schema + Markdown 实例 + JSON 状态文件               │
│  - 作用：所有数据的统一语义层；资产注册表 / 状态真值                │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 实例化 / 引用
┌──────────────────────────────────────────────────────────────────┐
│  Platform 层 — Agent / Workflow / 已有 skill / Pipeline           │
│  - 真源：scout-4 的 A-M pipeline（编排）                          │
│         + 基座 Top 18 模板（能力）                                 │
│         + 思路 2 dark-fantasy-ultimate-engine（窄通道生产引擎）     │
│         + 思路 3 planning-with-files（仓库协作引擎）               │
│         + 方法论中的 checker / schema_ref                          │
│  - 形态：YAML workflow DSL + agent registry + skill 一级公民       │
│  - 作用：所有"小说生成"原子能力的库与编排                          │
└──────────────────────────────────────────────────────────────────┘
                                ↓ 召回
┌──────────────────────────────────────────────────────────────────┐
│  RAG 层 — 检索 / 上下文适配 / 卡片召回                             │
│  - 真源：prompts/ 461 场景卡 + 基座长文本方法论 + 题材 profile 长文 │
│  - 形态：向量库 + frontmatter 过滤器 + 三层召回策略                │
│  - 作用：根据当前创作状态动态注入合适素材，不篡改真值优先级         │
└──────────────────────────────────────────────────────────────────┘
```

### 与原始草稿（notepad 中）的差异

| 维度 | 原草稿 | 修订后（基于 scout 证据） |
|---|---|---|
| Meta 层真源 | "用户宪法 / 价值观 / 审美准则" 模糊 | **思路 1/2/3 抽出的 20 条上位法 + 基座方法论硬约束**（scout-2 证据） |
| Foundation 层 | "题材×阶段×用途三维标签 + 实体 schema" | **基座 4 类资产（profile/template/methodology/checker）+ prompts/ PromptCard + skill 状态文件 schema**（scout-1/2/3 证据） |
| Platform 层 | "可调用 agent 库 + DAG workflow + 模板引擎" 抽象 | **A-M pipeline DSL + 基座 Top 18 模板 + 思路 2/3 双 skill 一级公民 + checker 模块**（scout-2/4 证据） |
| RAG 层 | "向量库 + 元数据过滤器 + 上下文拼装" | **三层召回：frontmatter 粗筛 → 向量召回 → 上下文重排**，prompts/ 是核心召回库（scout-3 证据） |

---

## 二、Meta 层：创作宪法

### 2.1 上位法 20 条（来自 scout-2 提炼，按工作 / 创作分组）

**工作纪律组（8 条）**：

1. 不确定就查，不要装懂
2. 任何关键事实必须交叉验证（年代、政策、金融、军事、地理、术语）
3. 不能伪造已读文件、章节、资料
4. 不能机械追满 100 章；上下文读取必须服从因果闭环
5. 把文件系统当长期记忆，把上下文当易失内存
6. 最新正文高于旧设定；当前状态判断优先看当前状态文件
7. 输出不暴露思维链，只给外显自检、依据、结论、结果
8. 联网只补硬事实，不替代作品内已写明的剧情真相

**创作宪法组（12 条）**：

9. 人物行为必须服从"过往经历 + 当前利益 + 性格底色"
10. 禁止为了推剧情让主角、反派、配角突然降智
11. 拒绝机械降神；解决方案必须来自既有铺垫、资源、信息差、规则
12. Show, don't tell；设定、情绪、强大、压迫都要落到事件、动作、器物、反应
13. 配角不是工具人，必须有算盘、恐惧、筹码、误判与反扑
14. 爽点必须兑现，而且要有因果与代价，不能只喊口号
15. 风格必须去 AI 味：少空心高级词，少模板狠话，少重复句式
16. 长篇必须有账本意识：状态、资源、收益、伏笔、关系都要可追溯
17. 书名、简介、开篇三件套必须协同服务转化，不可各说各话
18. 不同章节类型应用不同压迫方式，不能全书只剩一个战斗模板
19. 女性角色可以重要，但不能被写成后宫挂件或情绪摆设
20. 所有关系变化都要有事件驱动；无理由的爱恨、结盟、背叛都不成立

### 2.2 落地形态

| Meta 项目 | 落地形态 | 强制度 |
|---|---|---|
| 工作纪律 1-8 | runtime guard（agent 行为约束）+ output schema 强制字段 | 硬约束 |
| 创作宪法 9-20 | 写作前 checker（preflight）+ 写作后 reviewer（postflight） | 软约束 + 警告 |
| 平台红线（基座方法论） | runtime guard（按平台分支加载） | 硬约束 |
| 题材 profile 禁忌 | 上下文绑定（生成时注入对应 profile 的 taboo 字段） | 硬约束 |

### 2.3 Meta 层资产清单

- `meta/constitution.yaml`：20 条上位法 + 触发条件 + 验证方式
- `meta/runtime-guards/`：
  - `no-fake-read.yaml`：检测声称读过但实际未读
  - `latest-text-priority.yaml`：最新正文优先级仲裁
  - `crosscheck-required.yaml`：关键事实交叉验证触发条件
  - `no-thinking-chain-leak.yaml`：思维链不暴露
- `meta/quality-checkers/`：
  - `aigc-style-detector.yaml`：检测 AI 腔（模板句、空心词）
  - `cool-point-payoff-checker.yaml`：爽点兑现因果闭环
  - `character-iq-checker.yaml`：人物降智检测
  - `incremental-update-verifier.yaml`：长篇账本一致性
- `meta/platform-redlines/`：按平台（番茄/七猫/起点/晋江...）配置红线

### 2.4 设计原则

- **Meta 层是 guard，不是 prompt**：不能写成长 system prompt，否则上下文污染
- **多数 Meta 项目应做成可执行规则**：YAML 触发条件 + 验证脚本 / LLM judge
- **能用工具校验的不靠 prompt 提醒**：例如"不伪造已读"应该用 fs.exists 校验，不只是写在 prompt

---

## 三、Foundation 层：数据本体

### 3.1 资产类型注册表

基于 scout-1/3 的证据，Foundation 层至少 **5 类资产**：

| asset_type | 来源 | 数量 | 形态 |
|---|---|---|---|
| `genre_profile` | 基座 `题材/网文/*.md` | ~25 | YAML profile + Markdown longform |
| `template` | 基座 `模板/*/*.md` | ~50 | YAML schema + Markdown 填空骨架 |
| `methodology` | 基座 `方法论/*` 中的指南类 | ~30 | Markdown 规则文档 |
| `checker_or_schema_ref` | 基座 `方法论/` 中的 schema/checker 类（state-schema, 黄金三章 etc） | ~10 | YAML schema / checker spec |
| `prompt_card` | prompts/ 461 文件 | 461 | YAML frontmatter + Markdown 4-H2 + JSON content |

**注**：剩余 ~444 基座文件（544 总 - 100 已分类）属编号型题材簇，归类需后续扫描。

### 3.2 统一治理 frontmatter

所有 Foundation 资产共享治理字段（scout-1 提议的 schema 收敛后）：

```yaml
id: <unique-slug>            # 必填，命名规范见下
title: <human-readable>       # 必填
asset_type: <enum>            # 必填，见 §3.1
source_path: <repo-path>      # 必填
topic: <string|null>          # 可选
topic_bucket: <enum|null>     # 可选: 网文 / 通用 / 方法论
stage: <enum|null>            # 可选，10 阶段枚举见 §3.3
use_case: <string|null>       # 可选
abstraction_level: <enum>     # 必填: macro / meso / micro / meta / runtime
platform_scope: <string[]>    # 可选
reuse_scope: <enum>           # 必填: cross_genre / genre_specific / platform_specific / era_specific
safety_level: <enum>          # 可选: normal / sensitive / redline-heavy
status: <enum>                # 可选: draft / active / deprecated
input_contract: <string[]>    # 可选
output_contract: <string[]>   # 可选
dependencies: <string[]>      # 可选，依赖的其他资产 id
quality_grade: <enum|null>    # 可选: A / A- / B+ / B / C
last_updated: <date>          # 可选
notes: <string[]>             # 可选
```

### 3.3 收敛后的 10 阶段枚举（基于 scout-1 推荐）

`stage` 字段统一收敛到（替代原始多变阶段词）：

| 阶段 | 含义 | 典型资产 |
|---|---|---|
| `ideation` | 创意 / 立项 / 市场定位 / 卖点 | 创意简报、黄金三章、市场趋势 |
| `setting` | 角色 / 世界观 / 体系 / 势力 | 角色卡、世界观构建、力量体系 |
| `outlining` | 总纲 / 卷纲 / 章纲 / 节奏 / 伏笔布局 | 主大纲、章节大纲、伏笔模板 |
| `drafting` | 章节创作 / 场景铺写 / 对话 / 感官描写 | 正文 prompt、场景卡（write_*） |
| `refinement` | 润色 / 反 AI 味 / 风格优化 / 逻辑检查 | 反 AI 味、polish_*、check_* |
| `analysis` | 留存 / 反馈 / 质量评分 / 读者吸引力 | 读者吸引力分类法、analyze_* |
| `commercialization` | 平台适配 / 投稿 / 热度与读者画像 | 投稿指南、平台分析、跨平台规范 |
| `support` | 灵感捕捉 / 卡文急救 / 辅助生成 | 卡文 break、灵感 generate |
| `runtime_state` | 角色状态、伏笔状态、关系图、state-schema | state-schema、思路 2 的状态卡 |
| `crosscutting_rule` | 平台规范、命名规则、官职 / 家族真值 | 角色命名、古代官职、平台规则 |

### 3.4 资产类专属字段（扩展）

#### 3.4.1 `genre_profile` 扩展字段

```yaml
golden_three_outline: <object>      # 黄金三章结构
retention_targets: <object>          # 留存目标
emotion_curve: <string[]>            # 情绪弧线
chapter_structure: <object>          # 章节结构参数
hook_types: <string[]>               # 钩子类型枚举
cool_point_types: <string[]>         # 爽点类型枚举
cool_point_density: <enum>           # 密度: 高 / 中 / 低
taboos: <string[]>                   # 禁忌清单
style_guide: <object>                # 风格指南
reader_profile: <object>             # 读者画像
opening_template_available: <bool>   # 是否带"附录：开篇模板库"
```

#### 3.4.2 `template` 扩展字段

```yaml
template_family: <enum>              # character / outline / foreshadow / suspense / worldbuilding / project
fields_required: <string[]>
fields_optional: <string[]>
supports_incremental_update: <bool>  # 主角卡、伏笔、悬念都带历史/动态更新
render_format: <enum>                # yaml / markdown_table / mermaid / xml
linked_state_entities: <string[]>    # 关联的 runtime state 实体
```

#### 3.4.3 `methodology` 扩展字段

```yaml
method_family: <enum>                # writing / market / platform / creativity
normative_strength: <enum>           # guide / hard_rule / schema
targets: <object>                    # 面向哪些 stage/topic/platform
integrates_with: <string[]>          # 关联的其他方法论或 checker id
```

#### 3.4.4 `prompt_card` 扩展字段（来自 scout-3）

```yaml
card_intent: <enum>                  # 12 大: prose_generation / structural_design / generator / prototype_creation / scene_description / simulation / outline_planning / checker_diagnostic / editing_transformation / management_tracking / adaptation_specific / persona_setup
task_verb: <string>                  # write / design / generate / create / describe / ...
task_full: <string>                  # 完整 task 字段（如 write_auction_scene）
card_kind: <enum>                    # scene_card / setup_card / style_lock_card / checker_card / index_card
granularity: <enum>                  # paragraph / scene / chapter / arc / meta
output_kind: <enum>                  # prose / dialogue / schema_json / table / list / setup_persona / style_lock
requires_placeholders: <bool>
placeholders: <string[]>
dedup_verdict: <enum>                # retain / merge_with:<base_file> / drop
```

### 3.5 状态真值 schema（融合 scout-2/4 的状态系统）

**统一 runtime state schema**（合并 scout-4 的 A-M 状态实体 + scout-2 的 4 文件账本系统）：

```yaml
runtime_state:
  # 「设定常量」一旦锁定后只允许补丁式修订
  locked:
    STORY_DNA:
      topic, genre, chapter_count, core_conflict, hidden_crisis, limits
    WORLD_BUILDING:
      physical, social, metaphor, rules, loopholes
    PLOT_ARCHITECTURE:
      acts, turning_points, foreshadows, twists
    CHARACTER_DYNAMICS:
      roles, goals, arcs, relationship_graph

  # 「章节级控制」每章产出后增量更新
  per_chapter:
    CHAPTER_BLUEPRINT:
      chapter_no, function, suspense, hook, twist
    CURRENT_CHAPTER_SUMMARY:
      inherit, progress, bridge, warnings
      max_length: 800

  # 「长期记忆」全书级压缩，章节摘要折叠进来
  long_term_memory:
    GLOBAL_SUMMARY:
      timeline, active_conflicts, open_loops, world_changes
      max_length: 2000

  # 「实体运行时」M 阶段每章增量更新
  entity_runtime:
    CHARACTER_STATE:
      inventory, abilities, body, psyche, relations, events
      key: by_character_id
    FORESHADOW_STATE:                # 思路 2 的待回收伏笔池
      pending_hooks: [{id, set_at_chapter, target_chapter, status}]
    RESOURCE_LEDGER:                 # 思路 2 的微粒账本
      particles, currency, exchanges, key_resources
      precision: required            # 不允许"暴涨/海量/难以估量"
    RELATIONSHIP_GRAPH:              # 实体关系图
      nodes, edges, last_event_at

  # 「检索素材」按需调用
  retrieved:
    FILTERED_CONTEXT:
      情节燃料, 人物维度, 世界碎片, 叙事技法
      conflict_flags: <string[]>     # 与既有真值冲突时打 flag

  # 「计划文件」思路 3 的三件套
  workspace:
    task_plan_md:
      goals, phases, key_questions, decisions, errors
    findings_md:
      facts, references, character_status, setting_patches, open_questions
    progress_md:
      session_progress, actions, validations, blockers
```

**关键流转规则**：
- `read`: G/H 读取 locked + per_chapter + long_term + entity_runtime + retrieved 的受控子集
- `write`: A/B/C/D/E/F 首次写入 locked 域，进入锁定后只补丁
- `update`: I/J/M 只写增量
- `lock`: STORY_DNA + WORLD_BUILDING + PLOT_ARCHITECTURE 进入锁定后只允许补丁式修订

---

## 四、Platform 层：能力编排

### 4.1 平台资产类型

| Platform 资产 | 来源 | 形态 |
|---|---|---|
| **Workflow（流水线）** | scout-4 的 A-M | YAML workflow DSL |
| **Agent（已有 skill）** | 思路 2/3 | skill 一级公民 |
| **Capability（基座能力）** | 基座 Top 18 模板 + 编号题材簇 | 由 workflow 调用 |
| **Checker（校验模块）** | 基座方法论中的 checker 类 + Meta 层 quality checker | runtime guard / postflight |
| **Adapter（平台适配器）** | 平台分析指南 / 投稿规范 / 跨平台矩阵 | conditional routing |

### 4.2 主流水线：从开书到连载

合并 scout-4 的 A-M 13 阶段 + scout-4 缺口分析建议的补强阶段：

```
[立项] N0_market_research → N1_idea_validation         <- 新增（补 scout-4 缺口 1）
[创意] A_generate_story_dna
[设定] B_build_character_dynamics  ←─┐
       C_build_world ←─────────────────┤  并行
[框架] D_build_three_act_plot          ┘
[章节] E_build_chapter_blueprint
[状态] F_initialize_character_state
[首章] G_write_first_chapter
[续章循环] H_write_followup_chapter ←─┐
       J_summarize_current_chapter   │
       I_update_global_summary       │  循环
       M_update_character_state ─────┘
[检索辅助] L_generate_kb_keywords + K_filter_kb_context（按需）
[终稿] R1_revision_polish → R2_logic_check → R3_redline_audit  <- 新增（补 scout-4 缺口 2）
[发布] P1_title_blurb_cover → P2_publish_schedule → P3_reader_ops  <- 新增（补 scout-4 缺口 3）
[反馈] D1_retention_analysis → D2_comment_sentiment → D3_iteration_proposal  <- 新增（补 scout-4 缺口 4）
[复盘] V1_version_snapshot → V2_diff_diagnosis  <- 新增（补 scout-4 缺口 5）
```

**Workflow DSL**（基于 scout-4 draft 扩展）：

```yaml
workflow:
  name: novel_pipeline_v2
  mode: serial_with_memory_loop
  state: <见 §3.5 runtime_state>
  
  preconditions:
    constitution: meta/constitution.yaml
    runtime_guards: meta/runtime-guards/*.yaml
    redlines: meta/platform-redlines/{{platform}}.yaml
  
  steps:
    # ===== 立项阶段（新增）=====
    - id: N0
      type: market_research
      uses_agent: methodology:平台分析指南 + methodology:2026网文市场趋势
      inputs: [user_goals, platform_target]
      outputs: [market_snapshot]
    
    - id: N1
      type: idea_validation
      uses_capability: methodology:跨平台适配矩阵
      uses_checker: methodology:读者吸引力分类法
      inputs: [user_idea, market_snapshot]
      outputs: [validated_premise, fit_score]
    
    # ===== A-F 创意 + 设定 + 框架（继承 scout-4）=====
    - id: A
      type: generate_story_dna
      uses_capability: base:创意简报 + methodology:世界观母题目录
      inputs: [validated_premise, topic, genre, chapter_count, word_count, user_guidance]
      outputs: [STORY_DNA]
      apply_constitution: [11, 14]
    
    - id: B
      type: build_character_dynamics
      uses_capability: base:模板/角色/角色卡通用模板.md + base:模板/角色/主角.md + base:模板/角色/反派.md
      apply_constitution: [9, 10, 13, 19]
      inputs: [STORY_DNA, user_guidance]
      outputs: [CHARACTER_DYNAMICS]
    
    - id: C
      type: build_world
      uses_capability: base:世界观构建.md + methodology:世界观母题目录
      conditional_load: [base:methodology/古代官职体系 if topic includes 古代/宫斗/历史]
      inputs: [STORY_DNA, CHARACTER_DYNAMICS, user_guidance]
      outputs: [WORLD_BUILDING]
    
    - id: D
      type: build_three_act_plot
      uses_capability: base:模板/大纲/主大纲.md
      apply_constitution: [11, 13]
      inputs: [STORY_DNA, CHARACTER_DYNAMICS, WORLD_BUILDING, user_guidance]
      outputs: [PLOT_ARCHITECTURE]
    
    - id: E
      type: build_chapter_blueprint
      uses_capability: base:模板/大纲/章节大纲.md + base:methodology/黄金三章 + base:methodology/读者吸引力分类法
      inputs: [PLOT_ARCHITECTURE, chapter_count, user_guidance]
      outputs: [CHAPTER_BLUEPRINT]
    
    - id: F
      type: initialize_character_state
      uses_capability: base:模板/角色/主角.md (动态状态部分) + skill:dark-fantasy-ultimate-engine.状态卡子模组
      inputs: [CHARACTER_DYNAMICS]
      outputs: [CHARACTER_STATE]
    
    # ===== G/H 正文生成（按 skill 路由）=====
    - id: G
      type: write_first_chapter
      uses_agent: skill:dark-fantasy-ultimate-engine if topic in [玄幻黑暗], else default_writer
      uses_rag: rag:prompts_recall(card_intent=prose_generation, granularity=chapter, topic_tags=current)
      apply_constitution: [11, 12, 13, 14, 15, 16, 18]
      inputs: [CHAPTER_BLUEPRINT, CHARACTER_STATE, WORLD_BUILDING, PLOT_ARCHITECTURE, user_guidance]
      outputs: [chapter_text]
      when: "chapter_no == 1"
      postflight_checkers:
        - meta:aigc-style-detector
        - meta:cool-point-payoff-checker
        - meta:character-iq-checker
    
    - id: H
      type: write_followup_chapter
      uses_agent: <same as G>
      uses_rag: <same as G>
      apply_constitution: [4, 5, 6, 11, 12, 13, 14, 15, 16, 18]
      inputs: [GLOBAL_SUMMARY, previous_chapter_excerpt, CHARACTER_STATE, CURRENT_CHAPTER_SUMMARY, CHAPTER_BLUEPRINT, FILTERED_CONTEXT, user_guidance]
      outputs: [chapter_text]
      when: "chapter_no > 1"
      postflight_checkers: <same as G>
    
    # ===== I/J/K/L/M 记忆与检索（继承 scout-4）=====
    - id: J
      type: summarize_current_chapter
      inputs: [combined_text, current_chapter_info, next_chapter_info]
      outputs: [CURRENT_CHAPTER_SUMMARY]
    
    - id: I
      type: update_global_summary
      inputs: [chapter_text, GLOBAL_SUMMARY]
      outputs: [GLOBAL_SUMMARY]
    
    - id: M
      type: update_character_state
      uses_agent: skill:dark-fantasy-ultimate-engine.账本子模组
      apply_constitution: [16]
      inputs: [chapter_text, CHARACTER_STATE]
      outputs: [CHARACTER_STATE, RESOURCE_LEDGER, FORESHADOW_STATE]
    
    - id: L
      type: generate_kb_keywords
      uses_capability: base:模板/项目/创意简报.md (检索词部分)
      inputs: [chapter_metadata, creation_demand]
      outputs: [KNOWLEDGE_BASE_KEYWORDS]
      optional: true
    
    - id: K
      type: filter_kb_context
      uses_rag: rag:prompts_recall(quality_grade in [A, A-, B+])
      apply_constitution: [8]  # 联网只补硬事实
      inputs: [retrieved_texts, chapter_info]
      outputs: [FILTERED_CONTEXT]
      optional: true
    
    # ===== 终稿（新增）=====
    - id: R1
      type: revision_polish
      uses_capability: base:methodology/反AI味.md + prompts:polish_* + prompts:rewrite_*
      apply_constitution: [12, 15]
      inputs: [chapter_text]
      outputs: [chapter_text_polished]
    
    - id: R2
      type: logic_check
      uses_checker: meta:character-iq-checker + meta:cool-point-payoff-checker
      inputs: [chapter_text_polished, CHARACTER_STATE, PLOT_ARCHITECTURE]
      outputs: [logic_report]
      on_fail: revisit R1
    
    - id: R3
      type: redline_audit
      uses_checker: meta:platform-redlines/{{platform}}
      inputs: [chapter_text_polished]
      outputs: [redline_report]
      on_fail: hard_block until fixed
    
    # ===== 发布（新增）=====
    - id: P1
      type: title_blurb_cover_design
      uses_capability: prompts:generate_book_titles + prompts:optimize_blurb
      apply_constitution: [17]
      inputs: [STORY_DNA, validated_premise, market_snapshot]
      outputs: [title_set, blurb_set, cover_brief]
    
    - id: P2
      type: publish_schedule
      uses_capability: base:methodology/投稿指南 + base:methodology/跨平台写作规范
      inputs: [chapter_count, platform_target, market_snapshot]
      outputs: [publish_plan]
    
    - id: P3
      type: reader_ops
      uses_capability: prompts:simulate_reader_comments + prompts:simulate_livestream_chat（如直播流）
      inputs: [published_chapters, reader_feedback]
      outputs: [ops_actions]
    
    # ===== 反馈（新增）=====
    - id: D1
      type: retention_analysis
      uses_capability: base:methodology/读者吸引力分类法 + prompts:analyze_performance_data
      inputs: [retention_metrics, chapter_text_history]
      outputs: [retention_report]
    
    - id: D2
      type: comment_sentiment
      uses_capability: prompts:simulate_reader_comments (反向用作分类器)
      inputs: [reader_comments]
      outputs: [sentiment_report]
    
    - id: D3
      type: iteration_proposal
      inputs: [retention_report, sentiment_report, current_PLOT_ARCHITECTURE]
      outputs: [plot_patch_suggestions]
      apply_constitution: [9, 10, 11]
    
    # ===== 版本治理（新增）=====
    - id: V1
      type: version_snapshot
      uses_agent: skill:planning-with-files
      inputs: [all_state_files]
      outputs: [snapshot_id, snapshot_files]
    
    - id: V2
      type: diff_diagnosis
      inputs: [snapshot_a, snapshot_b]
      outputs: [diff_report]
  
  # ===== 流转规则 =====
  transitions:
    - {from: N0, to: N1}
    - {from: N1, to: A}
    - {from: A, to: [B, C]}
    - {from: [B, C], to: D}
    - {from: D, to: [E, F]}
    - {from: E, to: G, when: "chapter_no == 1"}
    - {from: [G, H], to: [J, I, M]}
    - {from: [J, M], to: H}
    - {from: H, to: R1}
    - {from: R1, to: R2}
    - {from: R2, to: R3, on_pass: true}
    - {from: R3, to: P3, on_pass: true}
    - {from: E, to: L, optional: true}
    - {from: L, to: K}
    - {from: K, to: H}
    # 周期事件
    - {trigger: weekly, to: V1}
    - {trigger: retention_drop, to: D1}
  
  # ===== 错误处理 =====
  error_handling:
    missing_input:        {action: request_user_input}
    conflict_detected:    {action: emit_conflict_flag, stop: true}
    summary_overflow:     {action: compress, preserve: [unresolved_threads]}
    state_drift:          {action: diff_against_CHARACTER_STATE, reopen: true}
    redline_violation:    {action: hard_block, escalate: true}
```

### 4.3 已有 skill 作为一级公民

**核心原则**：思路 2/3 是用户已经跑通的生产级 skill，**蒸馏不重写，只升格**。

#### 4.3.1 `skill:dark-fantasy-ultimate-engine`

注册为 Platform 层一级 agent。它的内部 8 个 sub-skill（正文创作 / 设定整理 / 质量审查 / 状态卡 / 微粒账本 / 伏笔池 / 章节结算 / 自检器）映射到 workflow 节点：

| Sub-skill | 映射到 workflow |
|---|---|
| 正文创作引擎 | G / H |
| 设定整理器 | B / C |
| 质量审查器 | R1 / R2 + postflight checkers |
| 状态卡维护器 | F + M |
| 微粒账本维护器 | M (RESOURCE_LEDGER) |
| 伏笔池维护器 | M (FORESHADOW_STATE) |
| 章节结算器 | M + J |
| 自检器 | postflight_checkers |

**集成方式**：
- 当 `topic in [玄幻黑暗]`，workflow 优先 dispatch 到此 skill
- 此 skill 的输出格式与 §3.5 runtime_state schema 兼容（adapter 层）
- 此 skill 的"四重文档协同"（正文 / 状态卡 / 资源账本 / 伏笔池）= Foundation 层的 4 个 entity_runtime 实例

**不能动**：
- 风格锁定（玄幻黑暗 9 项 + 8 项禁止）
- 信息源优先级（思路 2 的 7 层）
- 微粒数值真值（840000000 硬锚点）
- 4 类任务判定逻辑

#### 4.3.2 `skill:planning-with-files v9.2.0`

注册为 Platform 层**横切层 agent**（不进 workflow 串行链，而是覆盖所有 step 的工作流元行为）：

| 思路 3 能力 | 映射到 |
|---|---|
| `task_plan.md` 维护 | workspace.task_plan_md（§3.5）+ V1/V2 step |
| `findings.md` 维护 | workspace.findings_md + R2 logic_check 落 findings |
| `progress.md` 维护 | workspace.progress_md，每 step 完成时回写 |
| 全量冷启动模式 | workflow 的 "fresh_session" 模式 |
| 增量热更新模式（默认） | workflow 的 "default_session" 模式 |
| allowed-tools 白名单 | agent runtime 强制约束 |
| 不伪造已读 / 不机械追读 | meta:no-fake-read 等 guard 实例化 |
| 真值优先级 7 层 | runtime read priority（覆盖 G/H 的 read 选择） |

**集成方式**：
- 每个 workflow step 启动时，agent runtime 自动调用 `planning-with-files` 检查三件套是否存在
- 每个 step 完成后，自动 append progress.md
- 当出现新约束/事实，自动 append findings.md

**不能动**：
- 三件套文件名（用户已耦合 repo）
- 真值优先级（联网结果不能覆盖正文）
- 路径真实主义（用户给的路径优先）
- 不暴露思维链

### 4.4 基座 Top 18 模板的归位

来自 scout-1 的 18 个高价值模板，按 §3.1 资产类型注册到 Foundation 层，并被 workflow 通过 `uses_capability` 字段引用：

| 基座模板 | 归类 | workflow 调用点 |
|---|---|---|
| 模板/项目/创意简报.md | template (project) | A |
| 模板/大纲/主大纲.md | template (outline) | D |
| 模板/大纲/章节大纲.md | template (outline) | E |
| 模板/世界观/世界观构建.md | template (worldbuilding) | C |
| 模板/角色/角色卡通用模板.md | template (character) | B |
| 模板/角色/主角.md | template (character) | B + F |
| 模板/角色/反派.md | template (character) | B |
| 模板/角色/实体关系图.md | template (relationship) | B + M |
| 模板/伏笔/伏笔模板.md | template (foreshadow) | E + M |
| 模板/悬念/悬念模板.md | template (suspense) | E + M |
| 方法论/市场/state-schema.md | checker_or_schema_ref | 所有 state-touching step |
| 方法论/市场/读者吸引力分类法.md | checker_or_schema_ref | E + R2 + D1 |
| 方法论/创意/黄金三章.md | methodology | E |
| 方法论/写作/世界观母题目录.md | methodology | A + C |
| 方法论/平台/题材跨平台适配矩阵.md | methodology | N1 |
| 方法论/创意/平台分析指南.md | methodology | N0 |
| 题材/网文/guize-guaitan.md | genre_profile | 当 topic=规则怪谈时整体注入 |
| 题材/网文/niandai.md | genre_profile | 当 topic=年代时整体注入 |

---

## 五、RAG 层：召回设计

### 5.1 三层召回策略（来自 scout-3）

```
[Layer 1: 粗筛 / frontmatter 过滤]
  - 无需向量化，直接 SQL/index filter
  - 字段: card_intent, task_verb, topic_tags, genre_match, granularity,
         output_kind, card_kind, quality_grade, requires_placeholders
  - 输出: ~50-200 张候选卡

[Layer 2: 向量召回 / embedding similarity]
  - 在 Layer 1 候选集上做向量相似度
  - 向量来源: card_title + snippet + json_keys + h2_sections 拼接
  - top_k: 10

[Layer 3: 重排 / context-aware rerank]
  - 用 LLM judge 或 cross-encoder
  - 输入: top_k cards + current chapter state + user preference
  - 输出: top_3 inject to prompt
```

### 5.2 召回源（不只是 prompts/）

| 召回源 | 资产数 | 主要触发场景 |
|---|---|---|
| prompts/ PromptCard | 461 | 写作具体场景时（write_*/design_*/describe_*） |
| 基座长文方法论 | ~30 | 需要规则参考时（如反 AI 味、命名、古代官职） |
| 基座题材 profile 长文 | ~25 | 题材确定后整体注入 |
| 思路 2/3 文档 | 3 | 仅 Meta 层启动时调用，不应运行时召回 |

### 5.3 元数据索引建议

预计算 JSON 索引文件 `rag/prompt_card_index.json`：

```json
{
  "version": "v1",
  "indexed_at": "...",
  "total_cards": 461,
  "by_card_intent": {
    "prose_generation": [...card_ids],
    "structural_design": [...],
    ...
  },
  "by_task_verb": {...},
  "by_topic_tag": {...},
  "by_quality": {"A": [...], "B+": [...], ...}
}
```

### 5.4 召回禁忌

按 scout-2 的真值优先级 / 思路 3 的硬约束：

1. **召回不能覆盖真值**：召回的卡只能"补素材"，不能改 STORY_DNA / WORLD_BUILDING / PLOT_ARCHITECTURE
2. **联网召回只补硬事实**：现实世界的年代、政策、地理可以联网；作品内的剧情真相不行
3. **召回结果走 K 阶段过滤**：必经 `filter_kb_context` 步骤检测冲突
4. **召回卡片的 `prohibited_content` 触发 Meta:platform-redlines**：自动跳过敏感卡

---

## 六、与已有 skill 的集成策略

### 6.1 集成路径总览

```
┌───────────────────────────────────────────────────────┐
│                    用户输入                            │
└───────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────┐
│  Meta 层 guard 检查（不伪造已读 / 平台红线 / 等）        │
└───────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────┐
│  Platform: planning-with-files agent（横切层）         │
│  - 自动加载 task_plan / findings / progress            │
│  - 决定全量冷启动 or 增量热更新                         │
└───────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────┐
│  Platform: workflow router                            │
│  - 根据 topic / stage 路由到对应 workflow step          │
│  - 玄幻黑暗 → dark-fantasy-ultimate-engine             │
│  - 其他题材 → default workflow                          │
└───────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────┐
│  Foundation: 调用 template / state / checker           │
│  + RAG: 召回 prompts/ 场景卡补素材                      │
└───────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────┐
│  生成 / 修改 / 校验                                    │
│  - 输出走 Meta 层 postflight checker                   │
│  - planning-with-files 自动 append progress.md         │
└───────────────────────────────────────────────────────┘
                          ↓
                    输出给用户
```

### 6.2 兼容性边界

| 边界 | 必须保留 | 可以增强 | 不能替代 |
|---|---|---|---|
| 思路 2 风格锁定 | ✅ | 通过 adapter 让其他题材 skill 学这套锁定方式 | ❌ |
| 思路 2 信息源 7 层 | ✅ | 可作为通用真值仲裁器 | ❌ |
| 思路 2 微粒数值锚点 | ✅ | 可标准化为 RESOURCE_LEDGER schema | ❌ |
| 思路 3 三件套文件 | ✅ | 提供更稳定模板 | ❌ |
| 思路 3 增量热更新默认模式 | ✅ | 把"3-10 章默认窗口"参数化 | ❌ |
| 思路 3 allowed-tools 白名单 | ✅ | 可扩为通用 agent runtime 默认白名单 | ❌ |
| 基座题材 profile 内字段 | ✅ | 抽 YAML profile，留 longform notes | ❌ |
| prompts/ 卡片 4 H2 结构 | ✅ | 加 YAML frontmatter | ❌ |

### 6.3 双 skill 关系明示

- **思路 2 管"作品内运行时"**：风格、人物、状态、账本、伏笔、爽点、章节结算
- **思路 3 管"仓库外工作流"**：规划、发现、进度、考据、跨会话接力、路径纪律

**禁止揉合**：scout-2 警告不要"把二者揉成一个大而泛的超级 prompt"。蒸馏方案严格保留两者的独立 skill 形态。

---

## 七、缺口与补强

### 7.1 scout-4 识别的 5 大缺口（已被 workflow v2 补上）

| 缺口 | 原 A-M 是否覆盖 | v2 补充阶段 |
|---|---|---|
| 1. 立项与市场层 | ❌ | N0 + N1 |
| 2. 终稿编辑层 | ❌ | R1 + R2 + R3 |
| 3. 发布与运营层 | ❌ | P1 + P2 + P3 |
| 4. 数据反馈闭环 | ❌ | D1 + D2 + D3 |
| 5. 版本治理 | ❌ | V1 + V2（接思路 3 planning-with-files） |

### 7.2 scout-1 识别的风险（需治理）

| 风险 | 治理动作 |
|---|---|
| 文件命名体系不统一 | 强制 frontmatter，不再靠文件名解析（§3.2） |
| 方法论文本太长，污染上下文 | 拆 rules/checks/schema 子段，按需召回（§5） |
| 题材 profile 与方法论重复表达 | 显式标 "上游真源" vs "下游实例化"（dependencies 字段） |
| 部分依赖指向仓内不存在路径 | 蒸馏时映射成逻辑依赖（dependencies 字段），不死认文件路径 |

### 7.3 scout-3 识别的优化点

- B+/B 级卡 ~200 张可通过"补示例输入"升 A → 阶段 4 后做（不阻塞 v1）
- 目录页.md 作 RAG 失败回退的主题地图 → 阶段 4 实施

---

## 八、实施路线图

> 历史快照：以下路线图是阶段 2 草案，不代表当前待办。当前状态见 `STATUS.md`；下一步 P2 是补 Layer 1 空召回 metadata，并维护 `expected_ids` / `relevant_ids`。

### 8.1 阶段分割

按"先骨架后补肉"原则，分 4 个 sprint：

| Sprint | 周期 | 产出 | 验收 |
|---|---|---|---|
| **S1: Meta + Foundation Schema** | 1 周 | meta/constitution.yaml + foundation/schema/*.yaml + 资产类型注册表 | 4 类 schema 跑通 yaml lint + 任一基座文件能落 frontmatter |
| **S2: Platform 双 skill 集成** | 1-2 周 | 思路 2/3 接入 agent registry + workflow v2 YAML | 主流程 N0-G 跑通一个 demo 章节 |
| **S3: RAG 召回** | 1 周 | rag/prompt_card_index.json + 三层召回实现 + frontmatter 反推 | prompts/ 461 卡 + 基座方法论建索引 + demo 召回 |
| **S4: 治理与优化** | 持续 | B/B+ 卡补示例 + 缺口阶段 R/P/D/V 全跑通 + Jury 反馈整合 | 4 scout 报告中所有 "建议"项落地或显式 deferred |

### 8.2 S1 任务清单

- [ ] 写 `meta/constitution.yaml`：20 条上位法（scout-2）+ 触发条件 + 验证方式
- [ ] 写 `foundation/schema/genre_profile.yaml`
- [ ] 写 `foundation/schema/template.yaml`
- [ ] 写 `foundation/schema/methodology.yaml`
- [ ] 写 `foundation/schema/checker_or_schema_ref.yaml`
- [ ] 写 `foundation/schema/prompt_card.yaml`（基于 scout-3 schema 定稿）
- [ ] 写 `foundation/schema/runtime_state.yaml`（基于 scout-2/4 融合 §3.5）
- [ ] 用 1-2 个基座样例文件 + 1-2 个 prompts/ 样例文件做 frontmatter 标注，验证 schema 完备性

### 8.3 S2 任务清单

- [ ] 把思路 2/3 文档放入 `platform/skills/`，写 metadata.yaml（skill 边界、sub-skill 映射、状态文件契约）
- [ ] 写 `platform/workflows/novel_pipeline_v2.yaml`（§4.2）
- [ ] 实现 workflow runner 基础（YAML 解析 + step dispatch + state 读写）
- [ ] 实现 Meta 层 runtime guards 的基础 3 项（no-fake-read / latest-text-priority / crosscheck-required）
- [ ] N0 → A → B → C → D → E → F → G demo 跑通

### 8.4 S3 任务清单

- [ ] 写 `rag/prompt_card_index.json` 生成脚本（基于 frontmatter 推导索引）
- [ ] 写三层召回的简单实现（不需要立刻完美，能 demo 即可）
- [ ] 接入 K/L 阶段
- [ ] Demo：给定章节状态 → 召回 top 3 prompts → 注入 prompt → 比对纯无 RAG 输出

### 8.5 S4 任务清单（持续）

- [ ] B/B+ 卡补示例（200 张，可半自动化）
- [ ] R1/R2/R3 终稿三件套补全
- [ ] P/D/V 后处理流水线（按真实需求驱动，不必一次全做）
- [ ] 接 Jury Court 4 角法庭评审反馈（阶段 3）

---

## 九、给 Jury Court 的评审输入（阶段 3）

> 历史快照：Jury Court 已在阶段 3 完成并吸收到 `ARCHITECTURE.md` / `ROADMAP.md`，本节仅保留当时评审输入。

按 notepad 设计，阶段 3 由 4 角法庭评审本蒸馏方案。建议评审重点：

### Jury 1 - 架构师视角
- 四层架构边界是否清晰？Meta/Platform 是否有职责重叠？
- workflow v2 的 29 个 step 是否过度设计？有没有可合并的？
- 双 skill 一级公民是否合理？还是应该收编为 sub-component？

### Jury 2 - 数据工程师视角
- 5 类资产 schema 是否完备？字段是否冗余？
- runtime_state schema 把 scout-2/4 融合是否安全？真值优先级冲突如何裁决？
- RAG 三层召回是否过工程化？小项目可能用不上 Layer 3

### Jury 3 - 小说编辑视角
- 20 条创作宪法是否误伤创作灵活性？
- workflow 是否绑死了"番茄/七猫"风格？文学性 / 严肃文学路线如何兼容？
- 思路 2 的"风格锁定"放进 workflow 是否会让其他题材作品被错误带偏？

### Jury 4 - 产品工程师视角
- 4 sprint 是否实际可执行？MVP 边界在哪？
- 哪些 step 可以延后到 v2？S1+S2 能否独立交付 demo？
- ROI 排序：461 prompts/ 入 RAG vs 思路 2/3 集成 vs 基座 schema，先做哪个收益最大？

---

## 十、风险与依赖

### 10.1 蒸馏层面风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| frontmatter 标注耗时高 | 高 | S1 拖期 | 半自动化 + LLM 辅助标注 + 仅高价值资产先做 |
| 思路 2/3 集成时发现细节冲突 | 中 | S2 卡 | 不修改 skill 文档本身，写 adapter 层 |
| RAG 召回质量不达预期 | 中 | S3 重做 | 先 Layer 1+2，Layer 3 暂时手工或跳过 |
| 用户偏好与方案差异大 | 中 | 全局返工 | 阶段 3 Jury Court 早期识别 |
| workflow 复杂度撑爆 demo agent | 低 | S2 demo 卡 | 分步骤跑，不要求一次全流程 |

### 10.2 外部依赖

- LLM 调用（用于 schema 验证 / checker 实现）→ 已有渠道
- 向量库（用于 RAG）→ 需选型（可 sqlite + faiss 起步）
- agent runtime（执行 workflow）→ 需基础实现（不依赖第三方 framework）

---

## 十一、关键决策（待 Jury 审）

> 历史快照：这些决策已在 `ARCHITECTURE.md` §七落定；本节仅记录阶段 2 待审输入。

以下 8 个决策需要 Jury 表态：

1. **是否保留双 skill 独立形态**（vs 合并为统一 writer agent）？方案推荐：保留
2. **prompts/ 461 卡是否全部入 RAG**（vs 仅 A/A- 入）？方案推荐：全部入，按 quality_grade 排序
3. **runtime_state 是单一 store 还是分布式 store**（vs scout-2 的 4 文件 + scout-4 的 9 entity 各自落地）？方案推荐：合一 schema，物理上分文件（兼容思路 2/3 现状）
4. **基座方法论是否拆 sub-section**（vs 整篇召回）？方案推荐：拆，按 method_family 标注
5. **workflow v2 是否一次实现 29 step**（vs MVP 仅 N0-H + R1-R3）？方案推荐：MVP 仅核心 12 step，其余 deferred
6. **是否补 N0/N1 立项市场层**（scout-4 缺口 1）？方案推荐：是
7. **思路 2 风格锁定是否硬绑定 topic=玄幻黑暗**（vs 允许覆盖）？方案推荐：默认硬绑定，仅显式 override 时解锁
8. **terminal-output 是 Markdown 还是带 frontmatter 的 .md**？方案推荐：长篇用 .md+frontmatter，章节正文用纯文本

---

## 十二、验收（DoD）

阶段 2 完成的判据：
- [x] 本文件存在
- [x] 四层架构具体方案明确（§1）
- [x] Meta/Foundation/Platform/RAG 各层的资产清单 + schema 草案完备（§2-5）
- [x] 与已有 skill 集成边界明确（§6）
- [x] scout-4 5 大缺口补强方案到位（§7）
- [x] 实施路线图分 sprint（§8）
- [x] 给 Jury 的评审输入清单（§9）
- [x] 8 个待审决策点明确（§11）

---

## 附录 A：资产路径约定

```
project_root/
├── meta/
│   ├── constitution.yaml
│   ├── runtime-guards/
│   ├── quality-checkers/
│   └── platform-redlines/
├── foundation/
│   ├── schema/                     # 5 类 schema 定义
│   ├── assets/
│   │   ├── genre_profiles/         # 基座 题材/网文/*.md → 标注 frontmatter
│   │   ├── templates/              # 基座 模板/*/*.md → 标注 frontmatter
│   │   ├── methodologies/          # 基座 方法论/*/*.md（指南类）
│   │   ├── checkers/               # 基座 方法论/* 中的 checker / schema_ref
│   │   └── prompt_cards/           # prompts/ 461 卡 → 标注 frontmatter
│   └── runtime_state_examples/     # state schema 实例样本
├── platform/
│   ├── skills/
│   │   ├── dark-fantasy-ultimate-engine/   # 思路 2 原样保留
│   │   └── planning-with-files/            # 思路 3 原样保留
│   ├── workflows/
│   │   └── novel_pipeline_v2.yaml
│   ├── agents/
│   ├── adapters/                   # 平台/题材 adapter
│   └── runner/                     # workflow 执行引擎
├── rag/
│   ├── prompt_card_index.json
│   ├── methodology_index.json
│   └── vector_store/
└── _原料/                          # 原始资产（只读 archive）
    ├── 基座/
    ├── 思路/
    └── 提示词库参考/
```

## 附录 B：信息源映射（4 scout 报告核心结论 → 本方案章节）

| Scout 结论 | 本方案章节 |
|---|---|
| 基座 3 层结构（profile / template / methodology+checker） | §3.1 资产类型 / §4.4 Top 18 归位 |
| 基座统一 frontmatter schema | §3.2 治理 frontmatter |
| 基座 10 阶段枚举 | §3.3 收敛阶段 |
| 思路 1-3 用户创作宪法 20 条 | §2.1 Meta 上位法 |
| 思路 2 dark-fantasy-ultimate-engine 画像 | §4.3.1 + §6.2 兼容边界 |
| 思路 3 planning-with-files 画像 | §4.3.2 + §6.2 |
| 思路 2/3 不揉合 | §6.3 双 skill 关系明示 |
| prompts/ 是 Foundation 层场景卡库 | §3.4.4 + §5.2 |
| prompts/ 12 大 card_intent 聚类 | §3.4.4 字段定义 |
| prompts/ 与基座垂直分工不重叠 | §5.2 召回源分类 |
| scout-4 A-M pipeline + 状态机 | §3.5 runtime_state + §4.2 workflow v2 |
| scout-4 5 大缺口 | §7.1 + workflow v2 新增阶段 |
| scout-4 Workflow DSL 草案 | §4.2 workflow v2（扩展版） |

---

**本方案已落地，等阶段 3 Jury Court 评审。**
