**## 投票**  
revise

**## 核心结论**  
四层架构整体骨架合理、边界基本清晰、双 skill 升格策略符合“已有资产优先”原则，但 Platform 层职责聚合度过高、双 skill 拼接面定义仍偏描述性而非契约化、S2 集成风险被低估，需针对性重构后才能进入实施。  
三条主因：1) Meta-Foundation-Platform 三层存在部分职责模糊（guard 与 checker 重叠、state schema 与 skill 内部记录耦合）；2) 双 skill 作为一级公民缺乏显式 adapter contract 与状态共享协议，存在未来子系统割裂隐患；3) 4 sprint 依赖链中 S2 是 critical path，但其对现有 skill 零修改承诺与 workflow DSL 复杂度结合，构成最高技术债务风险。

**## 详细评审**

**### P0（必须改，否则不能进 sprint）**  
- 问题描述：Platform 层同时承载“workflow DSL + 双 skill 一级公民 + checker + adapter”，导致职责过重且与 Foundation 层 state schema 存在隐性重叠（§4.2 workflow steps 中大量直接操作 runtime_state 实体，而 skill 自身又维护相同 4 类文档）。  
  影响：后续 sprint 演化时，任何 state schema 变更都会同时冲击 workflow、dark-fantasy 子模块、planning-with-files 三处，维护性崩盘。  
  推荐做法：将 Platform 层拆为 Orchestrator（workflow DSL + runner）与 Skill Runtime（双 skill registry + adapter）两个子层，state 操作必须经 Orchestrator 统一入口，skill 只暴露标准 contract 接口。

- 问题描述：双 skill 集成仅给出“映射表 + 不能动列表”（§4.3.1/4.3.2），缺少正式的 Input/Output Contract、版本兼容声明和冲突仲裁协议。  
  影响：S2 集成后若发现微粒账本与 runtime_state.RESOURCE_LEDGER 字段不一致，将无处下手。  
  推荐做法：立即补充 `platform/skills/*/contract.yaml`（含 io schema、true-source priority、forbidden mutation list），并要求 adapter 层做双向转换。

**### P1（强烈建议改）**  
- 问题描述：四层边界中 Meta 层的 runtime guard 与 Platform 层的 postflight_checkers 职责描述重叠（§2.2 与 §4.2），且 guard 实现方式（YAML + 脚本 vs checker）未明确优先级。  
  影响：运行时可能出现双重校验或漏判，增加调试复杂度。  
  推荐做法：明确 guard 为前置硬阻断，checker 为后置软审计，统一归属 Meta 层输出。

- 问题描述：workflow v2 列出近 29 个 step（§4.2），包含大量新增 N/P/D/V 阶段，超出 MVP 必要范围。  
  影响：S2 周期被过度拉长，demo 难以快速验证核心闭环。  
  推荐做法：MVP 精简至 N0-H + R1-R3 + V1 共 12 step，其余明确 deferred 到 S4。

**### P2（可后续迭代）**  
- 问题描述：RAG 三层召回策略（§5.1）在当前规模下 Layer 3（LLM rerank）性价比待验证。  
  影响：若向量库选型后性能不足，会拖累 S3。  
  推荐做法：S3 先实现 Layer 1+2，Layer 3 作为可选插件。

- 问题描述：资产 frontmatter schema 字段过多（§3.2 近 20 字段），部分字段（如 quality_grade、reuse_scope）在 S1 难以全部填充。  
  影响：标注工作量激增。  
  推荐做法：S1 必填字段精简至 8 个，其余迭代补充。

**### 设计亮点（必须列出，避免单边批判）**  
1. 四层架构的“约束→真值→调度→召回”分层逻辑与数据流向（Meta ↓ Foundation ↓ Platform ↓ RAG）非常清晰，符合经典架构分层原则，易于后续水平扩展。  
2. 将已有 dark-fantasy-ultimate-engine 与 planning-with-files 明确升格为 Platform 一级公民而非重写，体现了“最小改动、最大复用”的务实架构思路，避免了常见蒸馏项目“一锅端重构”的陷阱。  
3. runtime_state schema 对 scout-2/4 状态系统的融合（§3.5）以及 workflow DSL 的 preconditions + transitions 设计，为状态一致性提供了较好的机器可执行基础。

**## 关键问题回答**

**Q1（四层边界）**：四层边界总体清晰，Meta 负责上位法与 guard（§2），Foundation 负责统一资产 schema 与 state true-source（§3），Platform 负责 agent/workflow 编排（§4），RAG 负责动态素材注入（§5），数据流向单向且约束明确。  
但存在两处轻微重叠：Meta 的 quality-checkers 与 Platform postflight_checkers 职责描述交叉（§2.2 vs §4.2 G/H step）；Foundation runtime_state schema 与 Platform 内双 skill 自身维护的 4 类文档（状态卡/账本/伏笔池/task_plan 等）未完全解耦。  
未见明显漏层，但 Platform 层内部聚合度过高，建议拆子层以强化边界。

**Q2（双 skill 一级公民）**：同时升格为 Platform 一级公民不会必然导致两个不兼容子系统，但当前拼接面定义不够契约化。  
资产共享通过 Foundation schema 间接实现，状态共享依赖 runtime_state 适配，agent 复用靠 workflow conditional dispatch（§4.3.1 “topic in [玄幻黑暗]”）。  
但缺少显式 adapter contract 与冲突仲裁规则（仅“不能动”列表），若 dark-fantasy 的微粒账本与 planning-with-files 的 findings.md 在字段语义上冲突，未来会形成割裂；需补充正式接口定义才能确保可演化性。

**Q3（实施路线）**：4 sprint 依赖关系基本合理，S1（schema）→ S2（集成）→ S3（RAG）→ S4（治理）呈线性递进。  
critical path 是 S2（双 skill 集成 + workflow runner），因其直接决定后续所有 demo 与状态一致性。  
风险最高的是 S2：零修改集成已有 skill 与复杂 workflow DSL 结合，一旦出现 contract 不匹配，将导致返工量最大；S1 风险次之（标注工作量），S3/S4 可并行或延后。

**## 改进建议清单**  
1. 立即拆分 Platform 层为 Orchestrator 与 Skill Runtime 两个子层，并为双 skill 补充 contract.yaml。  
2. 将 workflow v2 精简至 MVP 12 step，明确 deferred 清单。  
3. Meta guard 与 checker 职责做显式划分与优先级定义。  
4. runtime_state 与 skill 内部记录的映射关系用 adapter 层强制转换，而非直接复用。  
5. S1 schema 必填字段精简至核心 8 个，减少标注阻力。