# Review: story-truth-v195-regression

> Warn-only sidecar. It never edits chapter text or runtime_state.

- run_id: `v1-9-5-story-truth-review`
- status: `warn`
- rubric: `platform_cn_webnovel_v1` (report_only)
- issues: 17
- longform_gate_issues: 11
- reviewer_queue: 4
- style_fingerprint: `measured`

## Issues

- `chapter_01.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 髓的虚弱感竟奇迹般地消退了几分。 突然，一阵细微的沙沙声打破了寂静。无明的
- `chapter_02.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 有眼睛，只靠嗅觉追踪活人的热量。 突然，一阵剧烈的痉挛从腹部炸开。无明闷哼
- `chapter_03.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 而是一种需要不断支付代价的诅咒。 突然，一阵细微的摩擦声打破了寂静。声音来
- `chapter_03.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 的晶体，发出满足的呜咽声。然而，就在下一秒，他的动作僵住了。他猛地抬头，浑浊的
- `chapter_04.md` `generic_emotion` [anti_ai_style]: 抽象情绪替代具体动作。 Evidence: 掌心中那三颗微小的光点，心中涌起一股难以言喻的渴望。他知道，这只是开始。在这个总
- `chapter_04.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 尸体上的菌落，闪烁着诡异的光芒。 突然，一阵剧烈的眩晕袭来，无明单膝跪地，
- `chapter_01.md` `opening_loop_risk` [longform_continuity]: 章节开头疑似回到醒来/失忆/体内微粒/天堑边缘模板，可能把续写误判为重新开篇。 Evidence: 寒冷并非来自空气，而是从骨髓深处渗出的锈蚀感。无明睁开眼时，视野是一片浑浊的灰白，仿佛整个世界都被浸泡在陈年的尸水中。他试图坐起，脊椎发出令人牙酸的脆响，像是生锈的铁链被强行拉扯。记忆是一片空白，没有名字，没有过往，只有此刻剧烈跳动的太阳穴和喉咙里涌上的血腥味。他低头看向自己的双手，指节粗大，皮肤苍白如纸，上面布满了细
- `chapter_01.md` `missing_low_frequency_anchor` [longform_topic_lock]: 低频题材锚点缺失，组合题材可能被玄幻黑暗主轴稀释。 Evidence: missing any of: 血脉, 末日, 多子多福, 繁衍契约
- `chapter_01.md` `short_chapter` [longform_quality]: 章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。 Evidence: chinese_chars=1421 < 2400
- `chapter_02.md` `opening_loop_risk` [longform_continuity]: 章节开头疑似回到醒来/失忆/体内微粒/天堑边缘模板，可能把续写误判为重新开篇。 Evidence: 寒冷并非来自外界，而是从骨髓深处渗出的铁锈味。无明睁开眼时，视野被一层灰败的薄膜覆盖，那是天堑边缘特有的尘埃，混合着腐烂的孢子，黏腻地附着在视网膜上。他试图动弹，却发现四肢百骸如同灌满了铅汞，沉重得令人作呕。记忆是一片空白，只有胸腔里那颗心脏在疯狂撞击肋骨，发出沉闷如战鼓般的回响。他低头看向自己的右手，那柄刻有古老符文
- `chapter_02.md` `short_chapter` [longform_quality]: 章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。 Evidence: chinese_chars=1354 < 2400
- `chapter_03.md` `opening_loop_risk` [longform_continuity]: 章节开头疑似回到醒来/失忆/体内微粒/天堑边缘模板，可能把续写误判为重新开篇。 Evidence: 黑暗并非虚无，而是粘稠的、带有铁锈味的实体。无明睁开眼时，瞳孔尚未适应光线，鼻腔里先一步灌满了腐烂与硫磺混合的恶臭。他躺在一片灰白色的废墟之上，身下是碎裂的石板，每一道裂纹都像是大地干涸后留下的伤疤。天空呈现出一种病态的紫红色，云层低垂，仿佛随时会坍塌下来，将这片被遗弃的土地彻底碾碎。 记忆是一片空白，只有剧烈的头痛如
- `chapter_03.md` `missing_low_frequency_anchor` [longform_topic_lock]: 低频题材锚点缺失，组合题材可能被玄幻黑暗主轴稀释。 Evidence: missing any of: 血脉, 末日, 多子多福, 繁衍契约
- `chapter_03.md` `short_chapter` [longform_quality]: 章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。 Evidence: chinese_chars=1679 < 2400
- `chapter_04.md` `opening_loop_risk` [longform_continuity]: 章节开头疑似回到醒来/失忆/体内微粒/天堑边缘模板，可能把续写误判为重新开篇。 Evidence: 痛觉不是从皮肤表面传来的，而是像无数根烧红的铁针，从骨髓深处向外穿刺。无明在黑暗中睁开眼，视野里没有光，只有灰败的尘埃在空气中缓慢沉降。他躺在一片碎裂的黑曜石地面上，四周是断裂的石柱和扭曲的金属残骸，仿佛某种巨大生物死后腐烂的骨架。空气粘稠得令人窒息，带着铁锈和陈旧血液混合的腥甜味。他试图起身，肌肉却像灌了铅一样沉重，
- `chapter_04.md` `missing_low_frequency_anchor` [longform_topic_lock]: 低频题材锚点缺失，组合题材可能被玄幻黑暗主轴稀释。 Evidence: missing any of: 血脉, 末日, 多子多福, 繁衍契约
- `chapter_04.md` `short_chapter` [longform_quality]: 章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。 Evidence: chinese_chars=1580 < 2400

## Suggestions

- 把抽象心理和套话改成可观察动作、身体代价、环境反馈或对手反应。
- 按 v1.7 gate 复核异常章：先看批后状态快照，再处理回环、低频题材锚点和伏笔缺失。

## Style Fingerprint

- scope: `report_only`
- auto_edit: `False`
- writes_runtime_state: `False`
- enters_creation_prompt: `False`
- chapters: 4
- chinese_chars: 6034
- avg_sentence_chars: 29.0
- dialogue_line_ratio: 0.065
- anchor_phrase_hits: {'微粒': 40, '天堑': 10, '内宇宙': 5}
- style_pattern_hits: {'generic_emotion': 1, 'cliche_metaphor': 0, 'abrupt_transition': 5, 'game_system_tone': 0, 'light_novel_meta': 0}

## Longform Quality Gate

- batch 1 `1-4`: protagonist=未命名刺客, particles=0, anchors=['末日', '繁衍契约'], short=['chapter_01.md', 'chapter_02.md', 'chapter_03.md', 'chapter_04.md'], forbidden=[], missing_foreshadow=[]

### Reviewer Queue
- `chapter_01.md`: short_chapter
- `chapter_02.md`: short_chapter
- `chapter_03.md`: short_chapter
- `chapter_04.md`: short_chapter
