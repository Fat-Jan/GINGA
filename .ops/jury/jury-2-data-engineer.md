## 投票
revise

## 核心结论
方案在数据架构层面蓝图宏大，但在具体工程实现上存在关键字段缺失、去重规则模糊、召回策略不完整等P0问题，必须修订。其亮点在于四层架构清晰，并对基座资产进行了深刻的三层分类，为工程化提供了坚实基础。

## 详细评审

### P0（必须改）
- **问题描述**：Foundation层统一frontmatter的`stage`字段（§3.3）与基座资产实际阶段分布（scout-1报告）存在覆盖度缺口。
  - **影响**：大量“方法论”和“题材profile”资产将无法被正确分类，导致后续召回和路由失效。例如，`方法论/市场/state-schema.md`和`题材/网文/guize-guaitan.md`在方案定义的10阶段枚举中找不到合适位置。
  - **推荐做法**：扩展`stage`枚举，至少增加`cross_cutting`（横切规则，如state-schema）、`profile`（题材配置）等类别，或为`asset_type`为`methodology`和`genre_profile`的资产定义独立的`method_family`、`profile_type`字段，而非强行套用创作阶段。

- **问题描述**：双库去重策略（`dedup_verdict`）仅在`prompt_card`资产中提及，且未定义明确的执行规则和冲突裁决机制。
  - **影响**：scout-1基座（544模板）与scout-3 prompts库（461卡片）之间，以及基座内部（如`主角.md`与`角色卡通用模板.md`）存在大量近似同义或包含关系的模板，方案未给出可执行的合并/保留/丢弃判定逻辑，工程上无法落地。
  - **推荐做法**：明确去重判定流程，例如：1) 基于`asset_type`、`template_family`、`card_intent`进行粗筛；2) 定义关键字段（如`output_contract`、`fields_required`）相似度阈值；3) 设立优先级规则（如基座模板优先级高于prompt卡片，`genre_specific`高于`cross_genre`）。

- **问题描述**：RAG三层召回策略（§5.1）缺乏冷启动和暖启动的状态区分，且未定义召回率与精确率的权衡点（如top_k取值、重排模型选择）。
  - **影响**：系统启动时（向量库空）无法工作；运行时无法根据场景（如大纲构思需高召回，章节润色需高精度）调整检索策略，可能导致召回噪声过大或素材不足。
  - **推荐做法**：1) 定义冷启动策略：纯依赖frontmatter过滤和规则（如`quality_grade`）排序，并记录缺失向量导致的召回降级。2) 为不同`stage`或`card_intent`定义不同的召回参数配置（如`ideation`阶段top_k=20，`refinement`阶段top_k=5）。

### P1（强烈建议改）
- **问题描述**：`runtime_state` schema（§3.5）试图融合scout-2的4文件账本和scout-4的A-M实体，但字段定义过于笼统（如`entity_runtime.CHARACTER_STATE`仅用“inventory, abilities, body, psyche, relations, events”描述），未给出具体子字段和类型约束。
  - **影响**：无法直接作为数据契约指导开发，与现有skill（如思路2的“状态卡”）集成时需要大量适配逻辑，易产生歧义。
  - **推荐做法**：至少为关键实体（`CHARACTER_STATE`, `RESOURCE_LEDGER`）提供示例性的详细子字段定义和数据类型（如`RESOURCE_LEDGER.particles: integer`）。

- **问题描述**：Workflow DSL中大量使用`uses_capability: base:模板/角色/主角.md`这类基于原始路径的引用，而非治理后的资产`id`。
  - **影响**：与Foundation层通过`id`和`source_path`管理资产的理念背离，造成两套引用系统，维护混乱。
  - **推荐做法**：将`uses_capability`等字段的值改为引用资产的`id`（如`uses_capability: base-template-protagonist`），通过注册表解析为具体路径。

### P2（可后续）
- 对prompts库461张卡片的`quality_grade`自动化标注方案。
- RAG层Layer 3重排的LLM judge或cross-encoder的具体选型和实现细节。
- 为所有历史资产批量生成frontmatter的自动化工具链。

### 设计亮点（必列）
1. **四层架构（Meta/Foundation/Platform/RAG）职责分离清晰**，特别是将“数据本体”（Foundation）与“能力编排”（Platform）分离，符合数据工程最佳实践。
2. **对基座资产的三层分类（题材profile/模板/方法论）** 精准捕捉了原始材料的本质，为schema设计提供了坚实基础。
3. **将已有skill升格为一级公民**，采用“适配器”集成而非重写的策略，最大化保留了现有价值并降低了集成风险。
4. **明确提出了“向量库+frontmatter过滤”的双路召回架构**，兼顾了精确匹配与语义泛化。
5. **runtime_state schema尝试统一状态管理**，为长篇创作的“账本意识”提供了可行的数据模型方向。

## 关键问题回答
**Q1（三维标签覆盖度）**：不能完全覆盖。方案中的“阶段”维度（10阶段枚举）主要针对创作流程，但基座中存在大量横切规则和配置类资产，无法归类。**具体漏分例子**：1) `方法论/市场/state-schema.md`：属于“运行时状态定义”，既非`ideation`也非`setting`，应属`cross_cutting`或`schema`。2) `题材/网文/guize-guaitan.md`：作为题材配置全集，其内容贯穿所有阶段，方案中的`stage`字段设为`null`会导致召回缺失。3) `方法论/写作/古代官职体系.md`：是领域特定真值表，方案枚举中无`era_specific_rule`或`domain_knowledge`阶段对应，易被误标或漏标。

**Q2（双库去重策略）**：方案中提出的`retain/merge/drop`三态缺乏可执行规则。**关键边界条件及处理缺失**：1) **同名不同schema**：基座`模板/角色/主角.md`与prompts库中可能存在的`write_protagonist_intro`卡片，前者是结构化schema，后者是场景描写prompt，方案未规定按`asset_type`或`granularity`优先保留哪个。2) **近似同义但用法相反**：基座`反派.md`（强调动机合理性）与prompts库中可能存在的“快速生成脸谱化反派”卡片，在“角色降智”宪法下应丢弃后者，但方案未将Meta层约束链接到去重逻辑。3) **包含关系**：`角色卡通用模板.md`可能包含`主角.md`字段的子集，方案未定义基于字段集比较的合并规则。

**Q3（召回策略）**：方案未明确定义召回率与精确率的权衡点，也未区分冷热启动状态。**权衡点缺失**：未说明Layer 1 frontmatter过滤的松紧度（如是否允许`topic_tag`部分匹配）、Layer 2向量召回的top_k值、以及Layer 3重排是否在所有场景启用。**冷热启动策略缺失**：1) **冷启动（向量库空）**：应明确降级为纯frontmatter过滤+基于`quality_grade`或`last_updated`的排序，并记录日志。2) **暖启动**：应能根据当前`stage`动态调整策略，例如在`drafting`阶段可提高召回率（top_k=15），在`refinement`阶段应提高精确率（top_k=3，强制启用重排）。

## 改进建议清单
1.  **扩展`stage`枚举或为`methodology`/`genre_profile`增加专用分类字段**，以覆盖基座中横切规则和题材配置类资产。
2.  **制定可执行的双库去重规则**，明确基于资产类型、字段相似度、优先级（如基座>prompts）的判定流程和冲突裁决机制。
3.  **为RAG召回定义冷热启动策略及不同场景（stage）的参数配置**（如top_k, 是否重排）。
4.  **细化`runtime_state` schema中关键实体（CHARACTER_STATE, RESOURCE_LEDGER）的字段定义与数据类型**，提供至少一个完整示例。
5.  **将Workflow DSL中对资产的能力引用（uses_capability）从文件路径改为资产`id`**，确保引用统一。

## 字段补丁清单（你独有的产出）
- `foundation.schema.unified_frontmatter.stage`：当前=10阶段枚举，建议=增加`cross_cutting`（横切规则，如state-schema）、`profile`（题材全集配置）两个枚举值，理由=覆盖scout-1报告中大量方法论和题材profile资产的实际阶段属性。
- `foundation.schema.genre_profile`：当前=无`profile_type`字段，建议=增加`profile_type: enum`（可取`full_spectrum`如题材指南、`parameter_only`如爽点配置），理由=区分是贯穿全流程的配置全集还是特定参数包，优化召回精度。
- `foundation.schema.methodology`：当前=有`method_family`，但无`rule_type`，建议=增加`rule_type: enum`（可取`constraint`/`enumeration`/`schema`/`guide`），理由=更精细地区分方法论的工程用途，便于Platform层按需调用（如checker调用`constraint`，创意生成调用`enumeration`）。
- `foundation.schema.prompt_card`：当前=有`dedup_verdict`，但无`dedup_against`，建议=增加`dedup_against: string[]`字段，列出可能重复的基座模板`id`，理由=为去重提供显式、可维护的映射关系，避免运行时计算。
- `platform.workflow.step`：当前=`uses_capability: string`（文件路径），建议=`uses_capability: string`（资产id），理由=实现与Foundation层资产注册表的解耦和统一引用，提升可维护性。
- `rag.recall_config`：当前=未见，建议=新增配置文件，包含`cold_start_top_k`、`default_top_k`、`stage_specific_top_k`（映射表）、`enable_rerank_by_stage`等字段，理由=使召回策略参数化、可配置，明确权衡点。
  *(注：此为建议新增的配置实体路径)*