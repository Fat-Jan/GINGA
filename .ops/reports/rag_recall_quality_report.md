# RAG 真实召回质量评估报告

- 生成时间: 2026-05-14T13:30:08+00:00
- 数据源: `['foundation/assets/prompts', 'foundation/assets/methodology']`
- 临时索引: `.ops/validation/rag_recall_eval.sqlite`
- JSON 输出: `.ops/validation/rag_recall_quality.json`

## 总体结论

- 本次从真实资产构建 Layer 1 索引 473 张卡，Layer 2 向量 473 条。
- sqlite-vec native 状态: 可用并用于全部有结果查询；构建存储: `sqlite-vec`；fallback: `none`。
- 12 条固定查询平均 Layer 1 命中 2.92，平均 Layer 2 命中 2.92，平均 overlap 1.00。

## 环境

- Python: `3.13.12`
- sqlite: `3.39.5`
- sqlite-vec module available: `True`
- vector_ready: `ready`
- quality_grade distribution: `{'A': 48, 'A-': 53, 'B': 124, 'B+': 248}`

## 方法

- 使用 `rag.index_builder.build_index()` 从 `foundation/assets/prompts` 和 `foundation/assets/methodology` 重建临时 SQLite 索引。
- 使用 `rag.layer2_vector.build_vector_index()` 构建 Layer 2，传入 `SQLiteVecBackend()` 优先尝试 native sqlite-vec。
- 每条查询先按 stage/topic/asset_type/card_intent/quality_floor 做 Layer 1 过滤；Layer 1 非空时在候选内做 Layer 2 top-k 重排，Layer 1 为空时记录一次全局 Layer 2 诊断。
- embedding 使用项目内离线 `DeterministicTextEmbedder`，不调用 LLM，不发网络请求。

## 每条查询 Top Hits

### 失忆刺客 第一章 开场

- Filters: stage=`drafting`, topics=`['悬疑', '武侠', '玄幻']`, asset_type=`prompt_card`, intent=`prose_generation`
- Layer 1: prompts-card-write_villain_last_words-272 / 反派：最终BOSS的临终遗言; prompts-card-write_auction_finale-331 / 仙侠拍卖会压轴场景生成; prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示; prompts-card-write_ascension_scene-239 / 仙侠渡劫飞升大场面描写; prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节
- Layer 2: prompts-card-write_ascension_scene-239 / 仙侠渡劫飞升大场面描写 (0.4386); prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节 (0.4312); prompts-card-write_villain_last_words-272 / 反派：最终BOSS的临终遗言 (0.4142); prompts-card-write_auction_finale-331 / 仙侠拍卖会压轴场景生成 (0.4078); prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示 (0.3923)
- Overlap: 5 / ratio 1.0
- Notes: 章节开场创作，优先看 drafting prose_generation 对刺客/失忆/悬疑的语义命中。

### 黑暗玄幻 微粒经济

- Filters: stage=`setting`, topics=`['玄幻', '黑暗']`, asset_type=`prompt_card`, intent=`structural_design`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品
- Layer 2: prompts-card-design_power_system-6 / 力量体系设计 (0.4069); prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合 (0.4054); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系 (0.4053); prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品 (0.4035); prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计 (0.3887)
- Overlap: 5 / ratio 1.0
- Notes: 世界观经济规则查询，Layer 1 用 setting+玄幻/黑暗+结构设计收窄。

### 章节悬念 回收伏笔

- Filters: stage=`framework`, topics=`['通用', '悬疑']`, asset_type=`prompt_card`, intent=`outline_planning`
- Layer 1: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版)
- Layer 2: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版) (0.0905)
- Overlap: 1 / ratio 1.0
- Notes: 结构层查询，检查伏笔、悬念、章节节奏相关资产是否被召回。

### 角色状态更新

- Filters: stage=`setting`, topics=`['通用']`, asset_type=`prompt_card`, intent=`generator`
- Layer 1: prompts-card-generate_spinoff_plot-116 / 为高人气配角生成独立支线故事
- Layer 2: prompts-card-generate_spinoff_plot-116 / 为高人气配角生成独立支线故事 (0.1015)
- Overlap: 1 / ratio 1.0
- Notes: 偏状态表/角色档案维护，验证通用 setting 生成器类卡片。

### 世界观设定 天堑 内宇宙

- Filters: stage=`setting`, topics=`['玄幻', '科幻', '通用']`, asset_type=`prompt_card`, intent=`structural_design`
- Layer 1: prompts-card-design_villain-10 / 反派仇恨值拉升; prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design_fermi_paradox_solution-141 / 费米悖论/黑暗森林法则变体设计
- Layer 2: prompts-card-design_power_system-6 / 力量体系设计 (0.4273); prompts-card-design_fermi_paradox_solution-141 / 费米悖论/黑暗森林法则变体设计 (0.4224); prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合 (0.4220); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系 (0.4142); prompts-card-design_villain-10 / 反派仇恨值拉升 (0.4142)
- Overlap: 5 / ratio 1.0
- Notes: 专名较强的世界观设定查询，观察没有精确词时的近邻质量。

### 反转设计 狗血女文

- Filters: stage=`framework`, topics=`['言情', '女频', '豪门']`, asset_type=`prompt_card`, intent=`structural_design`
- Layer 1: prompts-card-design-short_drama_twists / 短剧高能反转节点设计
- Layer 2: prompts-card-design-short_drama_twists / 短剧高能反转节点设计 (0.1466)
- Overlap: 1 / ratio 1.0
- Notes: 女频反转/狗血桥段设计，检查 genre/topic 与语义共同作用。

### 规则怪谈 副本设计

- Filters: stage=`setting`, topics=`['怪谈', '悬疑', '恐怖']`, asset_type=`prompt_card`, intent=`generator`
- Layer 1: prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本; prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字)
- Layer 2: prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字) (0.4142); prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本 (0.4078)
- Overlap: 2 / ratio 1.0
- Notes: 规则怪谈强标签查询，预期 Layer 1 与 Layer 2 overlap 较高。

### 多子多福 奖励机制

- Filters: stage=`setting`, topics=`['系统', '玄幻']`, asset_type=`prompt_card`, intent=`structural_design`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品
- Layer 2: prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品 (0.4714); prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合 (0.4586); prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计 (0.4242); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系 (0.4239); prompts-card-design_power_system-6 / 力量体系设计 (0.4142)
- Overlap: 5 / ratio 1.0
- Notes: 系统奖励机制查询，检验具体流派名与系统设定资产的距离。

### 终稿润色 文风统一

- Filters: stage=`refinement`, topics=`['文风']`, asset_type=`prompt_card`, intent=`editing_transformation`
- Layer 1: prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing)
- Layer 2: prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing) (-0.0729)
- Overlap: 1 / ratio 1.0
- Notes: 终稿润色查询，使用 schema 内 polish/rewrite 类 editing_transformation，重点看标题是否直接相关。

### 市场定位 读者画像

- Filters: stage=`business`, topics=`['business', '通用']`, asset_type=`methodology`, intent=`none`
- Layer 1: base-methodology-creative-platform-analysis / 平台分析指南; base-methodology-creative-submission-guide / 网文平台投稿规范指南; base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描; base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵
- Layer 2: base-methodology-creative-submission-guide / 网文平台投稿规范指南 (0.4142); base-methodology-creative-platform-analysis / 平台分析指南 (0.4142); base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵 (0.4142); base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描 (0.3965)
- Overlap: 4 / ratio 1.0
- Notes: 商业分析查询，验证 business 阶段是否能召回读者画像/卖点定位 methodology 资产。

### 第一章 黄金三章 爽点钩子

- Filters: stage=`framework`, topics=`['通用']`, asset_type=`prompt_card`, intent=`outline_planning`
- Layer 1: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版)
- Layer 2: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版) (0.0000)
- Overlap: 1 / ratio 1.0
- Notes: 黄金三章/开篇节奏查询，补充常见章节设计场景。

### 战斗场景 节奏 动作描写

- Filters: stage=`drafting`, topics=`['玄幻', '动作']`, asset_type=`prompt_card`, intent=`structural_design`
- Layer 1: prompts-card-construct_misunderstanding_chain-69 / 迪化流误解链构建; prompts-card-design_exam_questions-134 / 设计用于学院流/学霸文的硬核考试题目; prompts-card-action-beat_sheet-219 / 动作戏节奏表; prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography)
- Layer 2: prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography) (0.4326); prompts-card-construct_misunderstanding_chain-69 / 迪化流误解链构建 (0.4309); prompts-card-action-beat_sheet-219 / 动作戏节奏表 (0.4216); prompts-card-design_exam_questions-134 / 设计用于学院流/学霸文的硬核考试题目 (0.4077)
- Overlap: 4 / ratio 1.0
- Notes: 动作戏场景查询，检验 drafting 与 structural_design 的交叉召回。

## 观察到的问题

- DeterministicTextEmbedder 是 token hashing，适合复现 smoke/趋势评估，但不等价于生产级语义 embedding。

## 下一步建议

- 把本脚本纳入后续资产变更后的固定评估入口，用 JSON diff 跟踪召回质量漂移。
- 为高频业务查询维护 expected/relevant id 集合，后续可计算 recall@k、MRR、nDCG 等更硬的指标。
- 针对 Layer 1 空召回或明显窄召回的 query，优先补 metadata topic/card_intent，而不是先改检索代码。
- 对专名强、资产未覆盖的题材词建立同义词/领域词表，降低 Layer 1 过滤漏召回。
