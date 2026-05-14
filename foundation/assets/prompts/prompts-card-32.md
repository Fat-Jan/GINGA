---
id: prompts-card-generate_comment_replies-32
asset_type: prompt_card
title: 神回复段评生成器
topic: [社区运营]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/32.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_comment_replies
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 32. 神回复段评生成器

## 提示词内容

```json
{
  "task": "generate_comment_replies",
  "comment_types": [
    {"type": "Plot Hole", "reply_style": "Tease / Explain without spoiling"},
    {"type": "Simp (Wife!)", "reply_style": "In-character (Roleplay)"},
    {"type": "Hate", "reply_style": "Ignore / Classy roast"},
    {"type": "Prediction", "reply_style": "Wink emoji / 'Maybe...'"}
  ],
  "goal": "Increase interaction rate and fan loyalty"
}
```

## 使用场景
社区运营。回复读者评论，增加粉丝粘性。

## 最佳实践要点
1.  **人设互动**：如果是角色粉，用书中角色的口吻回复，增强沉浸感。
2.  **高情商处理**：对于负面评论，选择忽视或幽默化解，避免争吵。

## 示例输入
- 评论：读者吐槽“主角这都不死太离谱了”。
- 回复风格：不剧透、轻松自嘲、顺手埋一个后续伏笔。
