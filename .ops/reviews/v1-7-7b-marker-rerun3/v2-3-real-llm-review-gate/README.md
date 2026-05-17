# Review: v1-7-7b-marker-rerun3

> Warn-only sidecar. It never edits chapter text or runtime_state.

- run_id: `v2-3-real-llm-review-gate`
- status: `warn`
- rubric: `platform_cn_webnovel_v1` (report_only)
- issues: 9
- longform_gate_issues: 2
- reviewer_queue: 2
- style_fingerprint: `measured`

## Issues

- `chapter_01.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 吞噬他人的生命精华。 短刃上的符文突然亮起，一股灼热的气流顺着掌心涌入手臂
- `chapter_01.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 无明即将支撑不住的时候，短刃上的符文突然爆发出一阵强烈的光芒，一股无形的冲击
- `chapter_01.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 观察着四周，手中的短刃随时准备出鞘。突然，一阵风吹过，卷起地上的尘土，形成一
- `chapter_01.md` `game_system_tone` [platform_genre_fit]: 游戏系统播报腔与当前风格锁冲突。 Evidence: 是直接烙印在他的意识深处，仿佛是某种系统提示，但又带着浓厚的血腥味。无明感到一阵
- `chapter_02.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 皮肤，探查他体内的异常。短刃上的符文突然剧烈闪烁了一下，一股无形的波动扩散开
- `chapter_02.md` `game_system_tone` [platform_genre_fit]: 游戏系统播报腔与当前风格锁冲突。 Evidence: 了细小的黑点，那是刚才逃亡时被昆虫群叮咬留下的痕迹，但现在，那些伤口正在以
- `chapter_04.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 系。 就在这时，无明体内的黑色雾气突然剧烈波动起来，一股强烈的渴望从他心底
- `chapter_01.md` `forbidden_style_hit` [longform_topic_lock]: 章节命中长篇正式 gate 禁词，需进入异常章 reviewer。 Evidence: 系统提示=1
- `chapter_02.md` `forbidden_style_hit` [longform_topic_lock]: 章节命中长篇正式 gate 禁词，需进入异常章 reviewer。 Evidence: 叮=1

## Suggestions

- 把抽象心理和套话改成可观察动作、身体代价、环境反馈或对手反应。
- 平台风格冲突只做人工复核提示；如需改文，另开编辑流程，不由 review 自动写回。
- 按 v1.7 gate 复核异常章：先看批后状态快照，再处理回环、低频题材锚点和伏笔缺失。

## Style Fingerprint

- scope: `report_only`
- auto_edit: `False`
- writes_runtime_state: `False`
- enters_creation_prompt: `False`
- chapters: 4
- chinese_chars: 16997
- avg_sentence_chars: 28.3
- dialogue_line_ratio: 0.306
- anchor_phrase_hits: {'微粒': 65, '天堑': 9, '内宇宙': 13}
- style_pattern_hits: {'generic_emotion': 0, 'cliche_metaphor': 0, 'abrupt_transition': 5, 'game_system_tone': 2, 'light_novel_meta': 0}

## Longform Quality Gate

- batch 1 `1-4`: protagonist=未命名刺客, particles=0, anchors=['多子多福', '末日', '繁衍契约', '血脉'], short=[], forbidden=['chapter_01.md', 'chapter_02.md'], missing_foreshadow=[]

### Reviewer Queue
- `chapter_01.md`: forbidden_style_hit
- `chapter_02.md`: forbidden_style_hit
