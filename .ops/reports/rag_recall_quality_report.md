# RAG 真实召回质量评估报告

- 生成来源: `scripts/evaluate_rag_recall.py`
- 数据源: `['foundation/assets/prompts', 'foundation/assets/methodology']`
- 临时索引: `.ops/validation/rag_recall_eval.sqlite`
- JSON 输出: `.ops/validation/rag_recall_quality.json`

## 总体结论

- 本次从真实资产构建 Layer 1 索引 473 张卡，Layer 2 向量 473 条。
- sqlite-vec native 状态: 可用并用于全部有结果查询；构建存储: `sqlite-vec`；fallback: `none`。
- 12 条固定查询平均 Layer 1 命中 11.58，平均 Layer 2 命中 4.42，平均 overlap 1.00。
- Layer 1 gold 指标: recall@5=0.303，precision@5=0.250，MRR=0.590，nDCG@5=0.340。
- Layer 2 gold 指标: expected_recall@5=0.875，recall@5=0.425，precision@5=0.367，MRR=0.708，nDCG@5=0.461。
- Layer 1 给 Layer 2 的候选池 candidate_k=20；最终评估 metrics 固定按 top_k=5。

## 环境

- Python: `3.13.12`
- sqlite: `3.39.5`
- sqlite-vec module available: `True`
- vector_ready: `ready`
- quality_grade distribution: `{'A': 48, 'A-': 53, 'B': 124, 'B+': 248}`

## 方法

- 使用 `rag.index_builder.build_index()` 从 `foundation/assets/prompts` 和 `foundation/assets/methodology` 重建临时 SQLite 索引。
- 使用 `rag.layer2_vector.build_vector_index()` 构建 Layer 2，传入 `SQLiteVecBackend()` 优先尝试 native sqlite-vec。
- 每条查询先按 stage/topic/asset_type/card_intent/quality_floor 做 Layer 1 过滤；Layer 1 产出 candidate_k=20 候选池，Layer 2 在候选内做 top_k=5 重排；Layer 1 为空时记录一次全局 Layer 2 诊断。
- embedding 使用项目内离线 `DeterministicTextEmbedder`，不调用 LLM，不发网络请求。

## Layer 1 Blocker Summary

| blocked_by | gold id count |
|---|---:|
| stage | 10 |
| topic | 7 |
| asset_type | 3 |
| card_intent | 20 |
| candidate_k | 2 |
| top_k | 0 |
| quality_floor | 0 |
| missing_from_index | 0 |

## 每条查询 Top Hits

### 失忆刺客 第一章 开场

- Filters: stage=`drafting`, topics=`['悬疑', '武侠', '玄幻']`, asset_type=`prompt_card`, intent=`prose_generation`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-write_villain_last_words-272 / 反派：最终BOSS的临终遗言; prompts-card-write_auction_finale-331 / 仙侠拍卖会压轴场景生成; prompts-card-create_protagonist-protagonist-bgm-style / 番茄风主角人设卡; prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示; prompts-card-write_ascension_scene-239 / 仙侠渡劫飞升大场面描写; prompts-card-write_inner_personality_meeting-265 / 悬疑：多重人格会议 (Inner Meeting); prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节; prompts-card-write_closed_circle_setup-283 / 悬疑：暴风雪山庄模式 (Closed Circle); prompts-card-write_npc_survival-268 / 无限流：扮演路人甲求生; prompts-card-write_power_transfer-282 / 仙侠师徒传功/灌顶场景生成; prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线; prompts-card-create_mythology-117 / 远古神话/传说生成器; prompts-card-write-unreliable_narrator / 不可靠叙述者; prompts-card-write-combat_scene-13 / 战斗场景生成; prompts-card-outline-underdog_rise-194 / 废柴流逆袭节奏表 (退婚流); prompts-card-create-steampunk_detective_agency-202 / 维多利亚/蒸汽朋克侦探事务所; prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索; prompts-card-write-mortician_routine-222 / 入殓师/遗体整容师日常; prompts-card-write_stalking_horror-231 / 心理惊悚：被监视的恐惧; prompts-card-write_auction_scene-25 / 拍卖会捡漏与打脸场景生成
- Layer 1 metrics: expected_recall@5=0.000, recall@5=0.000, precision@5=0.000, MRR=0.000, nDCG@5=0.000, hits=0/3
- Layer 2: prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索 (0.4489); prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节 (0.4422); prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线 (0.4256); prompts-card-write_power_transfer-282 / 仙侠师徒传功/灌顶场景生成 (0.4301); prompts-card-write_auction_scene-25 / 拍卖会捡漏与打脸场景生成 (0.4272)
- Layer 2 metrics: expected_recall@5=0.500, recall@5=0.333, precision@5=0.200, MRR=0.333, nDCG@5=0.235, hits=1/3
- Layer 1 diagnostic: gold_miss; prompts-card-create-assassin_creed blocked_by=['topic']
- Overlap: 5 / ratio 1.0
- Notes: 章节开场创作，优先看 drafting prose_generation 对刺客/失忆/悬疑的语义命中。

### 黑暗玄幻 微粒经济

- Filters: stage=`setting`, topics=`['玄幻', '黑暗']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design-time_loop / 时间循环机制设计; prompts-card-design_faction_war_dungeon-221 / 无限流：阵营对抗副本设计; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-tournament_structure-26 / 大比黑马逆袭流; prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution); prompts-card-design_organization-59 / 势力/组织架构设计; prompts-card-design-multiverse_travel / 诸天万界穿越机制设定; prompts-card-design_battle_royale-110 / 大逃杀/吃鸡模式逻辑设计; prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-design_werewolf_game-253 / 无限流狼人杀副本逻辑设计; prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟; prompts-card-write_seal_ritual-178 / 封印/解封仪式咒语设计; prompts-card-design-ring_spirit / 老爷爷/随身系统性格设定; prompts-card-design-many_children_system-401 / 设计多子多福系统
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=1.000, nDCG@5=0.339, hits=1/5
- Layer 2: prompts-card-design-ring_spirit / 老爷爷/随身系统性格设定 (0.4385); prompts-card-design_organization-59 / 势力/组织架构设计 (0.4354); prompts-card-design_power_system-6 / 力量体系设计 (0.4349); prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟 (0.4196); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系 (0.4260)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=0.333, nDCG@5=0.316, hits=2/5
- Layer 1 diagnostic: gold_miss; prompts-card-design_system_shop-83 blocked_by=['topic']; prompts-card-manage_guild_resources-119 blocked_by=['stage', 'card_intent']; prompts-card-write_currency_creation-274 blocked_by=['card_intent', 'topic']
- Overlap: 5 / ratio 1.0
- Notes: 世界观经济规则查询，Layer 1 用 setting+玄幻/黑暗+结构设计收窄。

### 章节悬念 回收伏笔

- Filters: stage=`framework`, topics=`['通用', '悬疑']`, asset_type=`prompt_card`, intent=`outline_planning`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-outline_golden_three-12 / 黄金三章细纲; prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版); prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线; prompts-card-plan_information_reveal-344 / 细纲：信息释放节奏 (Information Drip); prompts-card-check-logic_plothole / 检查逻辑漏洞; prompts-card-polish-final_checklist / 完稿最终检查清单; prompts-card-check_foreshadowing-146 / 伏笔回收与反转设计检查表; prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff)
- Layer 1 metrics: expected_recall@5=0.000, recall@5=0.167, precision@5=0.200, MRR=0.500, nDCG@5=0.214, hits=1/6
- Layer 2: prompts-card-check_foreshadowing-146 / 伏笔回收与反转设计检查表 (0.4361); prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff) (0.4266); prompts-card-check-logic_plothole / 检查逻辑漏洞 (0.4305); prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版) (0.4196); prompts-card-outline_golden_three-12 / 黄金三章细纲 (0.4158)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.600, MRR=1.000, nDCG@5=0.699, hits=3/6
- Layer 1 diagnostic: gold_miss; prompts-card-generate-cliffhanger-147 blocked_by=['stage', 'card_intent']; prompts-card-generate_foreshadowing-292 blocked_by=['stage', 'card_intent']; prompts-card-inject-cliffhanger-362 blocked_by=['stage', 'card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 结构层查询，检查伏笔、悬念、章节节奏相关资产是否被召回。

### 角色状态更新

- Filters: stage=`setting`, topics=`['通用']`, asset_type=`prompt_card`, intent=`generator`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_villain-10 / 反派仇恨值拉升; prompts-card-create_gap_moe_character-294 / 角色反差萌设定 (Gap Moe); prompts-card-create_character_profile-9 / 主角详细档案; prompts-card-create_antagonist-40 / 极致反派/打脸对象设计; prompts-card-generate_spinoff_plot-116 / 为高人气配角生成独立支线故事; prompts-card-design_character_arc-122 / 角色弧光 (Character Arc) 设计
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.500, precision@5=0.400, MRR=0.333, nDCG@5=0.346, hits=2/4
- Layer 2: prompts-card-create_gap_moe_character-294 / 角色反差萌设定 (Gap Moe) (0.4377); prompts-card-design_character_arc-122 / 角色弧光 (Character Arc) 设计 (0.4199); prompts-card-design_villain-10 / 反派仇恨值拉升 (0.4259); prompts-card-create_character_profile-9 / 主角详细档案 (0.4068); prompts-card-create_antagonist-40 / 极致反派/打脸对象设计 (0.4142)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.400, MRR=0.500, nDCG@5=0.414, hits=2/4
- Layer 1 diagnostic: gold_miss; prompts-card-generate_relationship_chart-80 blocked_by=['stage']
- Overlap: 5 / ratio 1.0
- Notes: 偏状态表/角色档案维护，验证通用 setting 生成器类卡片。

### 世界观设定 天堑 内宇宙

- Filters: stage=`setting`, topics=`['玄幻', '科幻', '通用']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_villain-10 / 反派仇恨值拉升; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design-time_loop / 时间循环机制设计; prompts-card-design_faction_war_dungeon-221 / 无限流：阵营对抗副本设计; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design_fermi_paradox_solution-141 / 费米悖论/黑暗森林法则变体设计; prompts-card-design-underwater_civ-207 / 深海/亚特兰蒂斯文明设定; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-design-multiverse_travel / 诸天万界穿越机制设定; prompts-card-design_character_arc-122 / 角色弧光 (Character Arc) 设计; prompts-card-design_parallel_universe-160 / 平行宇宙差异点设计; prompts-card-xenolinguistics_scenario-171 / 跨物种沟通语言学; prompts-card-design_space_fleet_tactics-241 / 星际战争：舰队阵型与指挥; prompts-card-tournament_structure-26 / 大比黑马逆袭流; prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution); prompts-card-design_organization-59 / 势力/组织架构设计
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=1.000, nDCG@5=0.339, hits=1/5
- Layer 2: prompts-card-design_parallel_universe-160 / 平行宇宙差异点设计 (0.4340); prompts-card-design_organization-59 / 势力/组织架构设计 (0.4272); prompts-card-design_power_system-6 / 力量体系设计 (0.4213); prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution) (0.4330); prompts-card-design-underwater_civ-207 / 深海/亚特兰蒂斯文明设定 (0.4110)
- Layer 2 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=0.333, nDCG@5=0.170, hits=1/5
- Layer 1 diagnostic: gold_miss; base-methodology-writing-worldview-motif-catalog blocked_by=['stage', 'asset_type', 'card_intent']; prompts-card-design_infinite_dungeon-21 blocked_by=['candidate_k']
- Overlap: 5 / ratio 1.0
- Notes: 专名较强的世界观设定查询，观察没有精确词时的近邻质量。

### 反转设计 狗血女文

- Filters: stage=`framework`, topics=`['言情', '女频', '豪门']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design-short_drama_twists / 短剧高能反转节点设计; prompts-card-use_setting_to_drive_plot-347 / 利用环境推动剧情 (Setting as Character); prompts-card-construct_plot_twist-367 / 反转逻辑链构建 (Plot Twist Logic)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.667, precision@5=0.400, MRR=1.000, nDCG@5=0.704, hits=2/3
- Layer 2: prompts-card-construct_plot_twist-367 / 反转逻辑链构建 (Plot Twist Logic) (0.4215); prompts-card-design-short_drama_twists / 短剧高能反转节点设计 (0.4180); prompts-card-use_setting_to_drive_plot-347 / 利用环境推动剧情 (Setting as Character) (0.3856)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.667, precision@5=0.400, MRR=1.000, nDCG@5=0.765, hits=2/3
- Layer 1 diagnostic: gold_miss; prompts-card-outline_identity_switch-23 blocked_by=['card_intent']
- Overlap: 3 / ratio 1.0
- Notes: 女频反转/狗血桥段设计，检查 genre/topic 与语义共同作用。

### 规则怪谈 副本设计

- Filters: stage=`setting`, topics=`['怪谈', '悬疑', '恐怖']`, asset_type=`prompt_card`, intent=`generator`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design-time_loop / 时间循环机制设计; prompts-card-build_folk_horror_scene-18 / 中式民俗恐怖场景构建; prompts-card-design_puzzle_room-387 / 设计密室逃脱/解谜场景; prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本; prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字); prompts-card-design_folk_horror_ritual-215 / 民俗恐怖仪式与禁忌; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-design_spy_code-132 / 谍战/卧底接头暗号设计; prompts-card-create-steampunk_detective_agency-202 / 维多利亚/蒸汽朋克侦探事务所; prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索; prompts-card-design_locked_room_trick-224 / 密室杀人：机械诡计设计; prompts-card-design-murder_mystery_script-375 / 剧本杀/谋杀之谜案件结构设计
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=0.250, nDCG@5=0.277, hits=2/5
- Layer 2: prompts-card-design_folk_horror_ritual-215 / 民俗恐怖仪式与禁忌 (0.4588); prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本 (0.4431); prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字) (0.4439); prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计 (0.4260); prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索 (0.4355)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=0.500, nDCG@5=0.384, hits=2/5
- Layer 1 diagnostic: gold_miss; prompts-card-design_safe_house_rules-250 blocked_by=['topic']; prompts-card-write_narrative_via_notes-261 blocked_by=['stage', 'card_intent']; prompts-card-write_scp_log-144 blocked_by=['card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 规则怪谈强标签查询，预期 Layer 1 与 Layer 2 overlap 较高。

### 多子多福 奖励机制

- Filters: stage=`setting`, topics=`['系统', '玄幻']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design-time_loop / 时间循环机制设计; prompts-card-design_faction_war_dungeon-221 / 无限流：阵营对抗副本设计; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-design_organization-59 / 势力/组织架构设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-tournament_structure-26 / 大比黑马逆袭流; prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution); prompts-card-design-multiverse_travel / 诸天万界穿越机制设定; prompts-card-design_battle_royale-110 / 大逃杀/吃鸡模式逻辑设计; prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-design_werewolf_game-253 / 无限流狼人杀副本逻辑设计; prompts-card-design-many_children_system-401 / 设计多子多福系统; prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟; prompts-card-design_branching_skill_tree-120 / 设计分支技能树; prompts-card-write_seal_ritual-178 / 封印/解封仪式咒语设计
- Layer 1 metrics: expected_recall@5=0.000, recall@5=0.000, precision@5=0.000, MRR=0.000, nDCG@5=0.000, hits=0/5
- Layer 2: prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution) (0.4216); prompts-card-design-many_children_system-401 / 设计多子多福系统 (0.4160); prompts-card-design_branching_skill_tree-120 / 设计分支技能树 (0.4503); prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟 (0.4336); prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合 (0.4332)
- Layer 2 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=0.500, nDCG@5=0.214, hits=1/5
- Layer 1 diagnostic: gold_miss; prompts-card-design_system_shop-83 blocked_by=['candidate_k']; prompts-card-generate_achievements-210 blocked_by=['card_intent']; prompts-card-generate_dungeon_rewards-27 blocked_by=['stage', 'card_intent']; +1 more
- Overlap: 5 / ratio 1.0
- Notes: 系统奖励机制查询，检验具体流派名与系统设定资产的距离。

### 终稿润色 文风统一

- Filters: stage=`refinement`, topics=`['文风']`, asset_type=`prompt_card`, intent=`editing_transformation`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.250, precision@5=0.200, MRR=1.000, nDCG@5=0.390, hits=1/4
- Layer 2: prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing) (-0.0297)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.250, precision@5=0.200, MRR=1.000, nDCG@5=0.390, hits=1/4
- Layer 1 diagnostic: narrow; prompts-card-differentiate-379 blocked_by=['card_intent', 'topic']; prompts-card-lock-style_and_restrictions blocked_by=['stage', 'card_intent', 'topic']; prompts-card-mimic_character_voice-451 blocked_by=['card_intent', 'topic']
- Overlap: 1 / ratio 1.0
- Notes: 终稿润色查询，使用 schema 内 polish/rewrite 类 editing_transformation，重点看标题是否直接相关。

### 市场定位 读者画像

- Filters: stage=`business`, topics=`['business', '通用']`, asset_type=`methodology`, intent=`none`, candidate_k=`20`, top_k=`5`
- Layer 1: base-methodology-creative-platform-analysis / 平台分析指南; base-methodology-creative-submission-guide / 网文平台投稿规范指南; base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描; base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.750, precision@5=0.600, MRR=1.000, nDCG@5=0.832, hits=3/4
- Layer 2: base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描 (0.4353); base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵 (0.4232); base-methodology-creative-platform-analysis / 平台分析指南 (0.4080); base-methodology-creative-submission-guide / 网文平台投稿规范指南 (0.4090)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.750, precision@5=0.600, MRR=1.000, nDCG@5=0.754, hits=3/4
- Layer 1 diagnostic: gold_miss; base-methodology-market-reading-power-taxonomy blocked_by=['stage']
- Overlap: 4 / ratio 1.0
- Notes: 商业分析查询，验证 business 阶段是否能召回读者画像/卖点定位 methodology 资产。

### 第一章 黄金三章 爽点钩子

- Filters: stage=`framework`, topics=`['通用']`, asset_type=`prompt_card`, intent=`outline_planning`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-outline_golden_three-12 / 黄金三章细纲; prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版); prompts-card-check-logic_plothole / 检查逻辑漏洞; prompts-card-polish-final_checklist / 完稿最终检查清单; prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.400, MRR=1.000, nDCG@5=0.637, hits=2/4
- Layer 2: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版) (0.4072); prompts-card-outline_golden_three-12 / 黄金三章细纲 (0.3984); prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff) (0.4104); prompts-card-check-logic_plothole / 检查逻辑漏洞 (0.4082); prompts-card-polish-final_checklist / 完稿最终检查清单 (0.3986)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.400, MRR=1.000, nDCG@5=0.637, hits=2/4
- Layer 1 diagnostic: gold_miss; base-methodology-creative-golden-three blocked_by=['asset_type', 'card_intent']; base-methodology-market-reading-power-taxonomy blocked_by=['asset_type', 'card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 黄金三章/开篇节奏查询，补充常见章节设计场景。

### 战斗场景 节奏 动作描写

- Filters: stage=`drafting`, topics=`['玄幻', '动作']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-design-time_loop / 时间循环机制设计; prompts-card-design_faction_war_dungeon-221 / 无限流：阵营对抗副本设计; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-construct_misunderstanding_chain-69 / 迪化流误解链构建; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-action-beat_sheet-219 / 动作戏节奏表; prompts-card-design_exam_questions-134 / 设计用于学院流/学霸文的硬核考试题目; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-tournament_structure-26 / 大比黑马逆袭流; prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography); prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution); prompts-card-design_organization-59 / 势力/组织架构设计; prompts-card-design-multiverse_travel / 诸天万界穿越机制设定; prompts-card-design_battle_royale-110 / 大逃杀/吃鸡模式逻辑设计; prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-design_werewolf_game-253 / 无限流狼人杀副本逻辑设计
- Layer 1 metrics: expected_recall@5=0.000, recall@5=0.000, precision@5=0.000, MRR=0.000, nDCG@5=0.000, hits=0/5
- Layer 2: prompts-card-action-beat_sheet-219 / 动作戏节奏表 (0.4761); prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography) (0.4714); prompts-card-tournament_structure-26 / 大比黑马逆袭流 (0.4485); prompts-card-design_battle_royale-110 / 大逃杀/吃鸡模式逻辑设计 (0.4436); prompts-card-design_organization-59 / 势力/组织架构设计 (0.4397)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=1.000, nDCG@5=0.553, hits=2/5
- Layer 1 diagnostic: gold_miss; prompts-card-write-combat_scene-13 blocked_by=['card_intent']; prompts-card-write_combat_choreography-456 blocked_by=['card_intent']; prompts-card-write_combat_psychology-376 blocked_by=['card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 动作戏场景查询，检验 drafting 与 structural_design 的交叉召回。

## 观察到的问题

- Layer 1 窄召回查询: ['终稿润色 文风统一']。请查看每条 query 的 gold_blockers。
- Layer 1 非空但漏掉 gold id 的查询: ['失忆刺客 第一章 开场', '黑暗玄幻 微粒经济', '章节悬念 回收伏笔', '角色状态更新', '世界观设定 天堑 内宇宙', '反转设计 狗血女文', '规则怪谈 副本设计', '多子多福 奖励机制', '市场定位 读者画像', '第一章 黄金三章 爽点钩子', '战斗场景 节奏 动作描写']。这通常是 stage/topic/card_intent 过窄或 top_k 截断。
- DeterministicTextEmbedder 是 token hashing，适合复现 smoke/趋势评估，但不等价于生产级语义 embedding。

## 下一步建议

- 把本脚本纳入后续资产变更后的固定评估入口，用 JSON diff 跟踪召回质量漂移。
- 持续维护 expected/relevant id 集合；新增资产或重标 metadata 时同步更新 gold set。
- 针对 Layer 1 空召回或明显窄召回的 query，优先补 metadata topic/card_intent，而不是先改检索代码。
- Layer 2 expected_recall@5 已达到 0.875；下一轮优先把 recall@5 从 0.425 往 0.500+ 推。
- 对专名强、资产未覆盖的题材词建立同义词/领域词表，降低 Layer 1 过滤漏召回。
