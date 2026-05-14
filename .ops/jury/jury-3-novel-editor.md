**## 投票**  
revise

**## 核心结论**  
这套方案把创作流程设计得过于严密，像给作家戴上了精密的脚镣，虽然能保证长篇不崩，但会显著压抑真正靠灵感驱动的写作乐趣。核心问题是四层架构和海量 schema 把“写小说”变成了“按系统走流程填资产”，对依赖突发奇想的作家极不友好；双 skill 虽名义保留，但被 workflow 强行编排后，dark-fantasy 的窄通道压抑气质很容易被秩序感稀释；最危险的是凌晨三点的灵感无处安放，容易被系统判定为“未分类冲突”而卡住。必须大幅简化才能让作家真正敢用。

**## 详细评审**

**### P0（必须改，否则作家用不下去）**  
- **问题描述**：整个 Platform 层 workflow v2 有 20+ 个 step（N0 到 V2），每个 step 都强制输入输出 contract + runtime_state 更新 + postflight checker，Foundation 层还要求所有资产加统一 frontmatter。  
- **创作影响**：作家写到兴奋处必须停下来更新 CHARACTER_STATE、RESOURCE_LEDGER、FORESHADOW_STATE 等多个 YAML 文件，灵感直接被打断，凌晨三点突发一个“跟 schema 不兼容”的支线时无处可放，创作流变成填表+自检循环。  
- **推荐做法**：把核心创作链（G/H 正文生成）简化为“可选 workflow”模式，默认走轻量路径，只在作家主动触发“存档/结算”时才走重 state 更新；增加明确“原始灵感暂存区”（raw_ideas/ 目录 + 不进 schema 的 markdown 池）。

**### P1（强烈建议改）**  
- Meta 层 20 条宪法 + 多重 checker（aigc-style-detector、character-iq-checker 等）在 postflight 强制跑，容易把作家个人文风判为“AI味”或“降智”，误伤有自己独特节奏的老作家。  
- runtime_state schema 把 locked 域锁得太死，长篇写到 30 万字后想大规模调整世界观时补丁式修订成本极高。  
- RAG 三层召回虽强大，但默认注入 top3 卡片，作家若想完全按自己感觉写，会被“合适素材”不断干扰节奏。

**### P2（可后续）**  
- 10 阶段枚举和 asset_type 注册表过于细致，新手容易迷失，老作家也懒得记住。  
- 461 张 prompt_card 的 frontmatter 标注工作量巨大，可先只对 A/A- 级卡做，剩余逐步补充。

**### 设计亮点（必列）**  
1. 把 dark-fantasy-ultimate-engine 和 planning-with-files 明确升格为一级公民，不揉合，这是真正尊重作家已有 skill 的做法。  
2. Meta 层把“创作宪法”做成可执行 guard 而非长 prompt，避免上下文污染，思路清晰。  
3. 为长篇准备的账本、伏笔池、状态卡机制，能极大降低后期崩盘风险，对想写 100 万字的作家是真帮助。

**## 关键问题回答**

**Q1（填表化风险）**：  
这套四层系统高度填表化风险极高。Platform 层的 workflow 把创作拆成 N0→A→B→C→D→E→F→G/H→R1/R2/R3 等近 30 个带 input/output contract 的 step，每个 step 还要求更新 Foundation 层的多份 YAML state 文件，作家实际体验就是不断“填资产、跑 checker、等系统确认”。当凌晨三点突然冒出一个跟现有 STORY_DNA 或 card_intent 完全不兼容的惊艳点子时，方案中**没有明确逃逸通道**：runtime_state 虽有 retrieved 域，但那是 RAG 召回后的过滤结果；workspace 里的 task_plan/findings/progress 仍是结构化三件套，未见“原始素材池”或“未分类暂存区”的独立目录描述（§3.5、§4.2、§5.3 均未提及）。结果是灵感要么强行塞进 schema（扭曲原意），要么被系统判定冲突而卡住，作家只好自己开新文件存草稿，违背了“把文件系统当长期记忆”的初衷。

**Q2（双 skill 气质保留）**：  
dark-fantasy-ultimate-engine 的窄通道、慢节奏、暗黑哲学气质**极大概率会被工程秩序稀释**。方案虽在 §4.3.1 强调“风格锁定 9 项 + 8 项禁止不能动”“仅 topic in [玄幻黑暗] 时路由”，但整个 Platform 层用统一的 workflow DSL 串行编排（G/H 节点强制走 RAG + postflight checkers + state 更新），planning-with-files 又作为横切层要求每步回写 progress.md，这套“秩序+可追踪”的重度协作逻辑会不断打断 dark-fantasy 原本的“沉浸式压抑写作流”。作家原本可能连续写三小时只改状态卡一次，现在每章都要经过 Meta checker + RAG 注入 + ledger 更新，暗黑氛围的连贯性被频繁“系统干预”打碎，哲学思辨也容易被“爽点兑现因果闭环”（宪法14条）等规则压成标准网文模板。§6.3 虽说禁止揉合，但实际集成后，窄通道气质被宽平台框架包裹，稀释几乎必然。

**Q3（拖慢点）**：  
在“设定 → 框架 → 大纲 → 章节 → 修改”全流程里，**章节创作（drafting）到修改（refinement）环节最容易被拖慢**，我最担心的卡点正是 G/H 正文生成后的 R1/R2/R3 终稿三件套 + 多重 postflight checker。作家写完一章兴奋劲正高时，系统要先跑 aigc-style-detector、cool-point-payoff-checker、character-iq-checker，还要更新 GLOBAL_SUMMARY 和 entity_runtime 多个文件，再走 RAG 重排，实际体验是“写完立刻被审稿+填表”，灵感冷却极快。相比之下立项和设定阶段虽繁琐但可一次性完成，章节循环才是每日高频操作，最容易让作家弃用。

**## 改进建议清单**  
1. 在 foundation/ 下新增 raw_ideas/ 目录，作为 schema 外的纯文本灵感暂存区，任何不兼容点子可先扔进去，系统只做松散索引不强制解析。  
2. 把 G/H 正文生成节点的 workflow 改为“可选轻模式”，默认只调用 dark-fantasy 或 default_writer + 必要 RAG，不强制每章 state 全更新。  
3. Meta checker 改为作家可开关的“温和模式”，默认只警告不硬 block，保留作家对个人风格的最终决定权。  
4. 为 dark-fantasy skill 增加“沉浸写作专线”：连续多章不打断状态更新，只在章节块结束时一次性结算。  
5. 简化 runtime_state，只保留作家真正关心的 CHARACTER_STATE 和 FORESHADOW_STATE，RESOURCE_LEDGER 等可选。

**## 创作场景压力测试（你独有的产出）**

1. **新人作家想写一篇 8 万字短篇，从零开始**：系统能给出工作流——N0/N1 立项市场验证 + A-D 设定框架走完后，E 章节大纲 + G 首章生成基本能用，RAG 也能召回合适 scene_card 辅助。但最大卡点在 F 初始化 state 和后续每章 M 更新时，新手会被要求填一大堆 YAML（locked 域、per_chapter、entity_runtime），根本不知道怎么填，灵感被 schema 吓退；若中途想改设定，补丁修订流程又复杂，极可能前三章后就放弃，转回纯手动写。整体成功率低，主要失败在 Foundation 层资产填充门槛太高。

2. **老作家正在写到 30 万字大长篇第 18 章，临时想插入新支线**：planning-with-files 能接住（自动加载三件套，append findings.md），dark-fantasy 的状态卡和伏笔池也能更新，但 workflow 要求先走 E 重新 build_chapter_blueprint，再更新 PLOT_ARCHITECTURE（locked 域），再走 RAG 召回相关卡，最后 R2/R3 checker。老作家最讨厌的就是“已写 30 万字还要被系统重新架构一遍”，新支线若跟原有 STORY_DNA 有冲突，会触发 conflict_flag 硬 block，必须走补丁流程，严重打断连载节奏。系统能“接住”但会把老作家最怕的“临时起意”变成高成本操作，体验很差。