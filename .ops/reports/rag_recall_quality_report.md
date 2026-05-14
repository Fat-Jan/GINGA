# RAG 真实召回质量评估报告

- 生成来源: `scripts/evaluate_rag_recall.py`
- 数据源: `['foundation/assets/prompts', 'foundation/assets/methodology']`
- 临时索引: `.ops/validation/rag_recall_eval.sqlite`
- JSON 输出: `.ops/validation/rag_recall_quality.json`

## 总体结论

- 本次从真实资产构建 Layer 1 索引 473 张卡，Layer 2 向量 473 条。
- sqlite-vec native 状态: 可用并用于全部有结果查询；构建存储: `sqlite-vec`；fallback: `none`。
- 12 条固定查询平均 Layer 1 命中 17.17，平均 Layer 2 命中 4.92，平均 overlap 1.00。
- Layer 1 gold 指标: recall@5=0.457，precision@5=0.400，MRR=0.729，nDCG@5=0.495。
- Layer 2 gold 指标: expected_recall@5=0.917，recall@5=0.614，precision@5=0.533，MRR=0.854，nDCG@5=0.636。
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
| stage | 2 |
| topic | 0 |
| asset_type | 3 |
| card_intent | 3 |
| candidate_k | 7 |
| top_k | 0 |
| quality_floor | 0 |
| missing_from_index | 0 |

## 每条查询 Top Hits

### 失忆刺客 第一章 开场

- Filters: stage=`drafting`, topics=`['悬疑', '武侠', '玄幻']`, asset_type=`prompt_card`, intent=`prose_generation`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-create-assassin_creed / 杀手/刺客组织的信条与戒律; prompts-card-write_power_transfer-282 / 仙侠师徒传功/灌顶场景生成; prompts-card-write_villain_last_words-272 / 反派：最终BOSS的临终遗言; prompts-card-write_auction_finale-331 / 仙侠拍卖会压轴场景生成; prompts-card-create_protagonist-protagonist-bgm-style / 番茄风主角人设卡; prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示; prompts-card-write_ascension_scene-239 / 仙侠渡劫飞升大场面描写; prompts-card-write_inner_personality_meeting-265 / 悬疑：多重人格会议 (Inner Meeting); prompts-card-write_currency_creation-274 / 种田：从零建立货币体系; prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节; prompts-card-write_closed_circle_setup-283 / 悬疑：暴风雪山庄模式 (Closed Circle); prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线; prompts-card-create_mythology-117 / 远古神话/传说生成器; prompts-card-write-unreliable_narrator / 不可靠叙述者; prompts-card-write-combat_scene-13 / 战斗场景生成; prompts-card-outline-underdog_rise-194 / 废柴流逆袭节奏表 (退婚流); prompts-card-create-steampunk_detective_agency-202 / 维多利亚/蒸汽朋克侦探事务所; prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索; prompts-card-write-mortician_routine-222 / 入殓师/遗体整容师日常; prompts-card-write_stalking_horror-231 / 心理惊悚：被监视的恐惧
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.333, precision@5=0.200, MRR=1.000, nDCG@5=0.469, hits=1/3
- Layer 2: prompts-card-write_mirror_horror-275 / 恐怖：镜子里的诡异细节 (0.4422); prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索 (0.4489); prompts-card-write_power_transfer-282 / 仙侠师徒传功/灌顶场景生成 (0.4301); prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线 (0.4256); prompts-card-create-assassin_creed / 杀手/刺客组织的信条与戒律 (0.4110)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.667, precision@5=0.400, MRR=0.250, nDCG@5=0.384, hits=2/3
- Layer 1 diagnostic: ok
- Overlap: 5 / ratio 1.0
- Notes: 章节开场创作，优先看 drafting prose_generation 对刺客/失忆/悬疑的语义命中。

### 黑暗玄幻 微粒经济

- Filters: stage=`setting`, topics=`['玄幻', '黑暗']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟; prompts-card-generate_mutated_creatures-254 / 生成灵气复苏背景下的动植物变异图鉴; prompts-card-generate_monster_bestiary-49 / 变异生物图鉴生成; prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-generate-lottery_pool / 随机金手指/系统抽奖池; prompts-card-generate-fantasy-geography-fantasy-geography-climate / 奇幻地理与气候生成; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-write_currency_creation-274 / 种田：从零建立货币体系; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-manage_guild_resources-119 / 宗门/公会资源管理系统; prompts-card-generate-black_market_list / 拍卖行/黑市物品清单生成; prompts-card-real_estate_development_plan-136 / 房地产/地皮开发策划案; prompts-card-outline-underdog_rise-194 / 废柴流逆袭节奏表 (退婚流); prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-tournament_structure-26 / 大比黑马逆袭流; prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-write_clan_management-402 / 家族养成/种田流派设定卡，包含资源、政策、危机与角色; prompts-card-design_bloodline_evolution-405 / 设定：血脉进阶与返祖 (Bloodline Evolution)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=1.000, nDCG@5=0.485, hits=2/5
- Layer 2: prompts-card-generate-fantasy-geography-fantasy-geography-climate / 奇幻地理与气候生成 (0.4534); prompts-card-simulate_fantasy_economy-102 / 异世界经济与通货膨胀模拟 (0.4196); prompts-card-design_power_system-6 / 力量体系设计 (0.4349); prompts-card-outline-underdog_rise-194 / 废柴流逆袭节奏表 (退婚流) (0.4351); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系 (0.4260)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=0.500, nDCG@5=0.384, hits=2/5
- Layer 1 diagnostic: gold_miss; prompts-card-design_system_shop-83 blocked_by=['candidate_k']
- Overlap: 5 / ratio 1.0
- Notes: 世界观经济规则查询，Layer 1 用 setting+玄幻/黑暗+结构设计收窄。

### 章节悬念 回收伏笔

- Filters: stage=`framework`, topics=`['通用', '悬疑']`, asset_type=`prompt_card`, intent=`outline_planning`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool); prompts-card-check_foreshadowing-146 / 伏笔回收与反转设计检查表; prompts-card-inject-cliffhanger-362 / 流程：悬念钩子植入 (Cliffhanger Injector); prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff); prompts-card-generate-metaphors-112 / 创意比喻与修辞生成器; prompts-card-outline_golden_three-12 / 黄金三章细纲; prompts-card-expand_scene_to_text-353 / 将场景卡扩写为正文; prompts-card-sharpen-hook_sharpener / 流程：爽点强化 (Hook Sharpener); prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版); prompts-card-finale_checklist-100 / 全书大结局收束检查表; prompts-card-outline_amnesia_arc-109 / 失忆/身份重构剧情线; prompts-card-rewrite_show_dont_tell-111 / "Show, Don't Tell" 改写练习; prompts-card-polish_dialogue-14 / 对话优化 (潜台词注入); prompts-card-generate-cliffhanger-147 / 悬念 (Cliffhanger) 设计生成器; prompts-card-expand_outline_point-308 / 大纲细化助手 (Outline Expander); prompts-card-generate_autopsy_report-310 / 生成悬疑题材的尸检报告/法医鉴定; prompts-card-escalate_conflict_scene-342 / 细纲：冲突升级阶梯 (Conflict Escalation); prompts-card-plan_information_reveal-344 / 细纲：信息释放节奏 (Information Drip); prompts-card-check-logic_plothole / 检查逻辑漏洞; prompts-card-rewrite-sensory / 五感沉浸式改写流程
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.667, precision@5=0.800, MRR=1.000, nDCG@5=0.869, hits=4/6
- Layer 2: prompts-card-check_foreshadowing-146 / 伏笔回收与反转设计检查表 (0.4361); prompts-card-check_foreshadowing_payoff-365 / 流程：伏笔回收检查 (Foreshadowing Payoff) (0.4266); prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool) (0.4190); prompts-card-inject-cliffhanger-362 / 流程：悬念钩子植入 (Cliffhanger Injector) (0.4195); prompts-card-generate-cliffhanger-147 / 悬念 (Cliffhanger) 设计生成器 (0.4263)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.833, precision@5=1.000, MRR=1.000, nDCG@5=1.000, hits=5/6
- Layer 1 diagnostic: ok
- Overlap: 5 / ratio 1.0
- Notes: 结构层查询，检查伏笔、悬念、章节节奏相关资产是否被召回。

### 角色状态更新

- Filters: stage=`setting`, topics=`['通用']`, asset_type=`prompt_card`, intent=`generator`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-design_villain-10 / 反派仇恨值拉升; prompts-card-generate-metaphors-112 / 创意比喻与修辞生成器; prompts-card-create_gap_moe_character-294 / 角色反差萌设定 (Gap Moe); prompts-card-create_character_profile-9 / 主角详细档案; prompts-card-create_antagonist-40 / 极致反派/打脸对象设计; prompts-card-generate_spinoff_plot-116 / 为高人气配角生成独立支线故事; prompts-card-design_character_arc-122 / 角色弧光 (Character Arc) 设计; prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool); prompts-card-write_author_final_note-300 / 撰写全书完结感言; prompts-card-design-emotional_arc-340 / 情感曲线设计 (Emotional Arc); prompts-card-create_chapter_emotional_beat-341 / 细纲：单章情绪心电图 (Emotional ECG); prompts-card-escalate_conflict_scene-342 / 细纲：冲突升级阶梯 (Conflict Escalation); prompts-card-break-writers_block-380 / 卡文强制突破 (Writer's Block Breaker); prompts-card-generate_relationship_chart-80 / 人物关系图谱 (Mermaid格式); prompts-card-generate_ai_art_prompt-220 / AI 绘画提示词生成 (Book Cover); prompts-card-write_blurbs-45 / 黄金简介撰写 (三版对比)
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.250, precision@5=0.200, MRR=0.250, nDCG@5=0.168, hits=1/4
- Layer 2: prompts-card-generate_relationship_chart-80 / 人物关系图谱 (Mermaid格式) (0.4399); prompts-card-create_gap_moe_character-294 / 角色反差萌设定 (Gap Moe) (0.4377); prompts-card-design-emotional_arc-340 / 情感曲线设计 (Emotional Arc) (0.4420); prompts-card-design_villain-10 / 反派仇恨值拉升 (0.4259); prompts-card-design_character_arc-122 / 角色弧光 (Character Arc) 设计 (0.4199)
- Layer 2 metrics: expected_recall@5=0.500, recall@5=0.500, precision@5=0.400, MRR=1.000, nDCG@5=0.541, hits=2/4
- Layer 1 diagnostic: ok
- Overlap: 5 / ratio 1.0
- Notes: 偏状态表/角色档案维护，验证通用 setting 生成器类卡片。

### 世界观设定 天堑 内宇宙

- Filters: stage=`setting`, topics=`['玄幻', '科幻', '通用']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-generate_monster_bestiary-49 / 变异生物图鉴生成; prompts-card-design_power_system-6 / 力量体系设计; prompts-card-generate-lottery_pool / 随机金手指/系统抽奖池; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-generate-black_market_list / 拍卖行/黑市物品清单生成; prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计; prompts-card-design_magitech_product-230 / 设计结合灵气与科技的现代修真产品; prompts-card-design-multiverse_travel / 诸天万界穿越机制设定; prompts-card-design_villain-10 / 反派仇恨值拉升; prompts-card-generate-metaphors-112 / 创意比喻与修辞生成器; prompts-card-outline_golden_three-12 / 黄金三章细纲; prompts-card-alternate_history_scenario-165 / 历史平行时空推演 (What If); prompts-card-generate_mutated_creatures-254 / 生成灵气复苏背景下的动植物变异图鉴; prompts-card-flesh_out_side_character-364 / 流程：配角加戏 (Side Character Flesh-out); prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-generate-fantasy-geography-fantasy-geography-climate / 奇幻地理与气候生成; prompts-card-generate_conlang_slang-103 / 架空语言与黑话生成器; prompts-card-design_fermi_paradox_solution-141 / 费米悖论/黑暗森林法则变体设计; prompts-card-write_archeology_log-173 / 遗迹/古文明考古日志; prompts-card-design-underwater_civ-207 / 深海/亚特兰蒂斯文明设定
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.400, precision@5=0.400, MRR=0.500, nDCG@5=0.360, hits=2/5
- Layer 2: prompts-card-design_infinite_dungeon-21 / 原创副本世界观设计 (0.4206); prompts-card-design_power_system-6 / 力量体系设计 (0.4213); prompts-card-flesh_out_side_character-364 / 流程：配角加戏 (Side Character Flesh-out) (0.4390); prompts-card-design-multiverse_travel / 诸天万界穿越机制设定 (0.4199); prompts-card-generate-lottery_pool / 随机金手指/系统抽奖池 (0.4213)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=1.000, nDCG@5=0.553, hits=2/5
- Layer 1 diagnostic: gold_miss; base-methodology-writing-worldview-motif-catalog blocked_by=['stage', 'asset_type', 'card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 专名较强的世界观设定查询，观察没有精确词时的近邻质量。

### 反转设计 狗血女文

- Filters: stage=`framework`, topics=`['言情', '女频', '豪门']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-write_reunion_scene-223 / 破镜重圆：久别重逢场景; prompts-card-design-short_drama_twists / 短剧高能反转节点设计; prompts-card-write_dialogue_subtext-348 / 细纲：对话潜台词设计 (Subtext in Dialogue); prompts-card-write_kabedon_scene-213 / 壁咚/强吻情节描写; prompts-card-write_inheritance_battle-238 / 豪门争产风云; prompts-card-write-childhood_friend_reunion-271 / 青梅竹马的久别重逢; prompts-card-write_banquet_espionage-278 / 谍战：宴会上的微表情博弈; prompts-card-write_love_triangle_scene-28 / 多男/多女争风吃醋 (修罗场); prompts-card-write_misunderstanding_resolution-295 / 误会解除情节写作; prompts-card-write_drunken_confession-332 / 酒后吐真言 (Drunken Confession); prompts-card-generate_titles-36 / 爆款书名生成器 (女频专用); prompts-card-write_social_gala_scene-385 / 场景：社交晚宴/名利场 (Social Gala); prompts-card-write-romantic_tension / 暧昧期推拉感设计; prompts-card-write-first_kiss-214 / 初吻/定情场景生成; prompts-card-outline_identity_switch-23 / 真假千金反转剧本; prompts-card-write_group_pet_scene-421 / 团宠流场景写作提示词; prompts-card-write_stand_in_climax-95 / 替身文学情感爆发点; prompts-card-use_setting_to_drive_plot-347 / 利用环境推动剧情 (Setting as Character); prompts-card-construct_plot_twist-367 / 反转逻辑链构建 (Plot Twist Logic); prompts-card-manage-expectation_management / 细纲：期待感管理 (Expectation Management)
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.333, precision@5=0.200, MRR=0.500, nDCG@5=0.296, hits=1/3
- Layer 2: prompts-card-write_drunken_confession-332 / 酒后吐真言 (Drunken Confession) (0.4405); prompts-card-design-short_drama_twists / 短剧高能反转节点设计 (0.4180); prompts-card-write_reunion_scene-223 / 破镜重圆：久别重逢场景 (0.4232); prompts-card-construct_plot_twist-367 / 反转逻辑链构建 (Plot Twist Logic) (0.4215); prompts-card-write_kabedon_scene-213 / 壁咚/强吻情节描写 (0.4191)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.667, precision@5=0.400, MRR=0.500, nDCG@5=0.498, hits=2/3
- Layer 1 diagnostic: ok
- Overlap: 5 / ratio 1.0
- Notes: 女频反转/狗血桥段设计，检查 genre/topic 与语义共同作用。

### 规则怪谈 副本设计

- Filters: stage=`setting`, topics=`['怪谈', '悬疑', '恐怖']`, asset_type=`prompt_card`, intent=`generator`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字); prompts-card-design-time_loop / 时间循环机制设计; prompts-card-build_folk_horror_scene-18 / 中式民俗恐怖场景构建; prompts-card-create_dying_message-216 / 设计死前留言谜题; prompts-card-design_puzzle_room-387 / 设计密室逃脱/解谜场景; prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本; prompts-card-design_folk_horror_ritual-215 / 民俗恐怖仪式与禁忌; prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计; prompts-card-write_inner_personality_meeting-265 / 悬疑：多重人格会议 (Inner Meeting); prompts-card-write_closed_circle_setup-283 / 悬疑：暴风雪山庄模式 (Closed Circle); prompts-card-design_spy_code-132 / 谍战/卧底接头暗号设计; prompts-card-design_linguistic_puzzle-166 / 设计语言学/解密游戏谜题; prompts-card-create-assassin_creed / 杀手/刺客组织的信条与戒律; prompts-card-create-steampunk_detective_agency-202 / 维多利亚/蒸汽朋克侦探事务所; prompts-card-create_red_herring-206 / 红鲱鱼 (Red Herring) 误导线索; prompts-card-design_safe_house_rules-250 / 规则怪谈：安全屋规则设计; prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool); prompts-card-generate_autopsy_report-310 / 生成悬疑题材的尸检报告/法医鉴定; prompts-card-design_locked_room_trick-224 / 密室杀人：机械诡计设计; prompts-card-write_mastermind_dialogue-244 / 幕后黑手：棋盘上的对话
- Layer 1 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=1.000, nDCG@5=0.339, hits=1/5
- Layer 2: prompts-card-design_safe_house_rules-250 / 规则怪谈：安全屋规则设计 (0.4620); prompts-card-design_folk_horror_ritual-215 / 民俗恐怖仪式与禁忌 (0.4588); prompts-card-generate_rules_dungeon-8 / 生成规则怪谈/副本 (0.4431); prompts-card-generate-weird_rules / 怪谈守则生成器 (红蓝字) (0.4439); prompts-card-design_horror_clue-237 / 恐怖无限流：生路提示设计 (0.4260)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.600, precision@5=0.600, MRR=1.000, nDCG@5=0.655, hits=3/5
- Layer 1 diagnostic: gold_miss; prompts-card-write_narrative_via_notes-261 blocked_by=['stage']; prompts-card-write_scp_log-144 blocked_by=['candidate_k']
- Overlap: 5 / ratio 1.0
- Notes: 规则怪谈强标签查询，预期 Layer 1 与 Layer 2 overlap 较高。

### 多子多福 奖励机制

- Filters: stage=`setting`, topics=`['系统', '玄幻']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-generate-lottery_pool / 随机金手指/系统抽奖池; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-manage_guild_resources-119 / 宗门/公会资源管理系统; prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版); prompts-card-design_organization-59 / 势力/组织架构设计; prompts-card-write_comic_script-115 / 漫画/条漫分镜脚本描述; prompts-card-control-pacing_cycle-345 / 细纲：爽文节奏控制器 (Pacing Controller); prompts-card-design-many_children_system-401 / 设计多子多福系统; prompts-card-design_system_shop-83 / 系统商城定价策略; prompts-card-generate_mutated_creatures-254 / 生成灵气复苏背景下的动植物变异图鉴; prompts-card-design-system_panel / 设计系统面板与UI美化; prompts-card-generate_monster_bestiary-49 / 变异生物图鉴生成; prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-generate-fantasy-geography-fantasy-geography-climate / 奇幻地理与气候生成; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-write_currency_creation-274 / 种田：从零建立货币体系; prompts-card-write_system_starter_pack-291 / 系统：新手大礼包开启 (Starter Pack); prompts-card-write_myth-395 / 编造神话以获取力量; prompts-card-generate-black_market_list / 拍卖行/黑市物品清单生成
- Layer 1 metrics: expected_recall@5=0.000, recall@5=0.000, precision@5=0.000, MRR=0.000, nDCG@5=0.000, hits=0/5
- Layer 2: prompts-card-design-many_children_system-401 / 设计多子多福系统 (0.4160); prompts-card-generate-black_market_list / 拍卖行/黑市物品清单生成 (0.4474); prompts-card-write_currency_creation-274 / 种田：从零建立货币体系 (0.4413); prompts-card-design_cheat_code-tomato_custom / 金手指设计 (番茄定制版) (0.4190); prompts-card-generate-lottery_pool / 随机金手指/系统抽奖池 (0.4142)
- Layer 2 metrics: expected_recall@5=0.500, recall@5=0.200, precision@5=0.200, MRR=1.000, nDCG@5=0.339, hits=1/5
- Layer 1 diagnostic: gold_miss; prompts-card-generate_achievements-210 blocked_by=['candidate_k']; prompts-card-generate_dungeon_rewards-27 blocked_by=['candidate_k']; prompts-card-generate_exchange_list-22 blocked_by=['candidate_k']
- Overlap: 5 / ratio 1.0
- Notes: 系统奖励机制查询，检验具体流派名与系统设定资产的距离。

### 终稿润色 文风统一

- Filters: stage=`refinement`, topics=`['文风']`, asset_type=`prompt_card`, intent=`editing_transformation`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-lock-style_and_restrictions / 文风与禁区锁; prompts-card-differentiate-379 / 润色：群像文人物区分; prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing); prompts-card-mimic_character_voice-451 / 润色：角色语气模仿 (Character Voice Mimicry)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=1.000, precision@5=0.800, MRR=1.000, nDCG@5=1.000, hits=4/4
- Layer 2: prompts-card-lock-style_and_restrictions / 文风与禁区锁 (0.4236); prompts-card-polish_text_style-363 / 流程：风格化润色 (Style Polishing) (0.4107); prompts-card-differentiate-379 / 润色：群像文人物区分 (0.4103); prompts-card-mimic_character_voice-451 / 润色：角色语气模仿 (Character Voice Mimicry) (0.4180)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=1.000, precision@5=0.800, MRR=1.000, nDCG@5=1.000, hits=4/4
- Layer 1 diagnostic: ok
- Overlap: 4 / ratio 1.0
- Notes: 终稿润色查询，使用 schema 内 polish/rewrite 类 editing_transformation，重点看标题是否直接相关。

### 市场定位 读者画像

- Filters: stage=`business`, topics=`['business', '通用']`, asset_type=`methodology`, intent=`none`, candidate_k=`20`, top_k=`5`
- Layer 1: base-methodology-market-reading-power-taxonomy / 读者吸引力分类法; base-methodology-creative-platform-analysis / 平台分析指南; base-methodology-creative-submission-guide / 网文平台投稿规范指南; base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描; base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵
- Layer 1 metrics: expected_recall@5=1.000, recall@5=1.000, precision@5=0.800, MRR=1.000, nDCG@5=1.000, hits=4/4
- Layer 2: base-methodology-market-2026-webnovel-trends / 2026 网文市场趋势扫描 (0.4353); base-methodology-creative-platform-analysis / 平台分析指南 (0.4080); base-methodology-platform-genre-adaptation-matrix / 题材跨平台适配矩阵 (0.4232); base-methodology-market-reading-power-taxonomy / 读者吸引力分类法 (0.4047); base-methodology-creative-submission-guide / 网文平台投稿规范指南 (0.4090)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=1.000, precision@5=0.800, MRR=1.000, nDCG@5=0.956, hits=4/4
- Layer 1 diagnostic: ok
- Overlap: 5 / ratio 1.0
- Notes: 商业分析查询，验证 business 阶段是否能召回读者画像/卖点定位 methodology 资产。

### 第一章 黄金三章 爽点钩子

- Filters: stage=`framework`, topics=`['通用']`, asset_type=`prompt_card`, intent=`outline_planning`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-generate-metaphors-112 / 创意比喻与修辞生成器; prompts-card-outline_golden_three-12 / 黄金三章细纲; prompts-card-expand_scene_to_text-353 / 将场景卡扩写为正文; prompts-card-sharpen-hook_sharpener / 流程：爽点强化 (Hook Sharpener); prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版); prompts-card-finale_checklist-100 / 全书大结局收束检查表; prompts-card-rewrite_show_dont_tell-111 / "Show, Don't Tell" 改写练习; prompts-card-polish_dialogue-14 / 对话优化 (潜台词注入); prompts-card-generate-cliffhanger-147 / 悬念 (Cliffhanger) 设计生成器; prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool); prompts-card-expand_outline_point-308 / 大纲细化助手 (Outline Expander); prompts-card-escalate_conflict_scene-342 / 细纲：冲突升级阶梯 (Conflict Escalation); prompts-card-check-logic_plothole / 检查逻辑漏洞; prompts-card-rewrite-sensory / 五感沉浸式改写流程; prompts-card-polish-final_checklist / 完稿最终检查清单; prompts-card-replace_said_tags / 润色：甚至不用“说”字 (Dialogue Tags); prompts-card-generate_relationship_chart-80 / 人物关系图谱 (Mermaid格式); prompts-card-expand_sensory_details-113 / 五感环境氛围扩写; prompts-card-check_foreshadowing-146 / 伏笔回收与反转设计检查表; prompts-card-generate_ai_art_prompt-220 / AI 绘画提示词生成 (Book Cover)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.400, MRR=0.500, nDCG@5=0.397, hits=2/4
- Layer 2: prompts-card-outline_golden_three_chapters-41 / 黄金三章细纲生成 (番茄版) (0.4072); prompts-card-outline_golden_three-12 / 黄金三章细纲 (0.3984); prompts-card-sharpen-hook_sharpener / 流程：爽点强化 (Hook Sharpener) (0.4198); prompts-card-generate_foreshadowing-292 / 伏笔埋设技巧 (Foreshadowing Tool) (0.4221); prompts-card-escalate_conflict_scene-342 / 细纲：冲突升级阶梯 (Conflict Escalation) (0.4187)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.500, precision@5=0.400, MRR=1.000, nDCG@5=0.637, hits=2/4
- Layer 1 diagnostic: gold_miss; base-methodology-creative-golden-three blocked_by=['asset_type', 'card_intent']; base-methodology-market-reading-power-taxonomy blocked_by=['asset_type', 'card_intent']
- Overlap: 5 / ratio 1.0
- Notes: 黄金三章/开篇节奏查询，补充常见章节设计场景。

### 战斗场景 节奏 动作描写

- Filters: stage=`drafting`, topics=`['玄幻', '动作']`, asset_type=`prompt_card`, intent=`structural_design`, candidate_k=`20`, top_k=`5`
- Layer 1: prompts-card-action-beat_sheet-219 / 动作戏节奏表; prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography); prompts-card-generate_mutated_creatures-254 / 生成灵气复苏背景下的动植物变异图鉴; prompts-card-write_villain_last_words-272 / 反派：最终BOSS的临终遗言; prompts-card-write_auction_finale-331 / 仙侠拍卖会压轴场景生成; prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示; prompts-card-generate_monster_bestiary-49 / 变异生物图鉴生成; prompts-card-design_power_system-6 / 力量体系设计; prompts-card-design_academy_curriculum-73 / 设计学院流课程表与考核体系; prompts-card-generate-fantasy-geography-fantasy-geography-climate / 奇幻地理与气候生成; prompts-card-design_cyber_cultivation-105 / 赛博修仙体系融合; prompts-card-write_ascension_scene-239 / 仙侠渡劫飞升大场面描写; prompts-card-write_currency_creation-274 / 种田：从零建立货币体系; prompts-card-construct_misunderstanding_chain-69 / 迪化流误解链构建; prompts-card-design-pet_evolution-74 / 宠物/御兽进化路线设计; prompts-card-write-combat_scene-13 / 战斗场景生成; prompts-card-generate-black_market_list / 拍卖行/黑市物品清单生成; prompts-card-design_exam_questions-134 / 设计用于学院流/学霸文的硬核考试题目; prompts-card-real_estate_development_plan-136 / 房地产/地皮开发策划案; prompts-card-outline-underdog_rise-194 / 废柴流逆袭节奏表 (退婚流)
- Layer 1 metrics: expected_recall@5=1.000, recall@5=0.400, precision@5=0.400, MRR=1.000, nDCG@5=0.553, hits=2/5
- Layer 2: prompts-card-action-beat_sheet-219 / 动作戏节奏表 (0.4761); prompts-card-choreograph_fight_scene-355 / 流程：打斗动作细化 (Combat Choreography) (0.4714); prompts-card-generate_monster_bestiary-49 / 变异生物图鉴生成 (0.4504); prompts-card-write_revenge_scene-418 / 弃徒/退婚流复仇场景写作提示 (0.4543); prompts-card-write-combat_scene-13 / 战斗场景生成 (0.4256)
- Layer 2 metrics: expected_recall@5=1.000, recall@5=0.600, precision@5=0.600, MRR=1.000, nDCG@5=0.684, hits=3/5
- Layer 1 diagnostic: gold_miss; prompts-card-write_combat_choreography-456 blocked_by=['candidate_k']; prompts-card-write_combat_psychology-376 blocked_by=['candidate_k']
- Overlap: 5 / ratio 1.0
- Notes: 动作戏场景查询，检验 drafting 与 structural_design 的交叉召回。

## 观察到的问题

- Layer 1 非空但漏掉 gold id 的查询: ['黑暗玄幻 微粒经济', '世界观设定 天堑 内宇宙', '规则怪谈 副本设计', '多子多福 奖励机制', '第一章 黄金三章 爽点钩子', '战斗场景 节奏 动作描写']。这通常是 stage/topic/card_intent 过窄或 top_k 截断。
- DeterministicTextEmbedder 是 token hashing，适合复现 smoke/趋势评估，但不等价于生产级语义 embedding。

## 下一步建议

- 把本脚本纳入后续资产变更后的固定评估入口，用 JSON diff 跟踪召回质量漂移。
- 持续维护 expected/relevant id 集合；新增资产或重标 metadata 时同步更新 gold set。
- 针对 Layer 1 空召回或明显窄召回的 query，优先补 metadata topic/card_intent，而不是先改检索代码。
- Layer 2 expected_recall@5 已达到 0.917，recall@5 已达到 0.614；下一轮优先压低 candidate_k 残余 blocker 并守住 0.500+。
- 对专名强、资产未覆盖的题材词建立同义词/领域词表，降低 Layer 1 过滤漏召回。
