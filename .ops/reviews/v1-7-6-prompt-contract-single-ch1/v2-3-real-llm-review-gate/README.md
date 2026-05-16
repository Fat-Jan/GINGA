# Review: v1-7-6-prompt-contract-single-ch1

> Warn-only sidecar. It never edits chapter text or runtime_state.

- run_id: `v2-3-real-llm-review-gate`
- status: `warn`
- rubric: `platform_cn_webnovel_v1` (report_only)
- issues: 2
- longform_gate_issues: 1
- reviewer_queue: 1
- style_fingerprint: `measured`

## Issues

- `chapter_01.md` `abrupt_transition` [anti_ai_style]: 高频突转词需要确认是否由动作因果支撑。 Evidence: 。” 无明冷笑一声，脚下的黑色岩石突然碎裂，他整个人如同一颗炮弹般冲向骑士
- `chapter_01.md` `short_chapter` [longform_quality]: 章节中文正文低于 v1.7 gate 阈值，可能是批量生成后段质量下滑。 Evidence: chinese_chars=3492 < 3500

## Suggestions

- 把抽象心理和套话改成可观察动作、身体代价、环境反馈或对手反应。
- 按 v1.7 gate 复核异常章：先看批后状态快照，再处理回环、低频题材锚点和伏笔缺失。

## Style Fingerprint

- scope: `report_only`
- auto_edit: `False`
- writes_runtime_state: `False`
- enters_creation_prompt: `False`
- chapters: 1
- chinese_chars: 3492
- avg_sentence_chars: 23.0
- dialogue_line_ratio: 0.241
- anchor_phrase_hits: {'微粒': 17, '天堑': 8, '内宇宙': 0}
- style_pattern_hits: {'generic_emotion': 0, 'cliche_metaphor': 0, 'abrupt_transition': 1, 'game_system_tone': 0, 'light_novel_meta': 0}

## Longform Quality Gate

- batch 1 `1-1`: protagonist=未命名刺客, particles=0, anchors=['繁衍契约', '血脉'], short=['chapter_01.md'], forbidden=[], missing_foreshadow=[]

### Reviewer Queue
- `chapter_01.md`: short_chapter
