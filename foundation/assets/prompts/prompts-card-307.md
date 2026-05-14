---
id: prompts-card-generate_character_names-naming-tool
asset_type: prompt_card
title: 角色名字生成器
topic: [玄幻, 西方奇幻, 赛博朋克, 现代]
stage: auxiliary
quality_grade: B
source_path: _原料/提示词库参考/prompts/307.md
last_updated: 2026-05-13
card_intent: generator
card_kind: scene_card
task_verb: generate
task_full: generate_character_names
granularity: utility
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 307. 写作工具：角色名字生成器 (Naming Tool)

## 提示词内容

```json
{
  "task": "generate_character_names",
  "genre": "Xianxia / Western Fantasy / Cyberpunk / Modern",
  "gender": "Male / Female / Neutral",
  "meaning": "Related to fire / Noble / Tragic",
  "count": 5,
  "format": [
    "Name: [Name]",
    "Origin: [Etymology/Meaning]",
    "Vibe: [First impression]"
  ]
}
```

## 使用场景
通用/起名废救星。生成有寓意、符合画风的名字。

## 最佳实践要点
1.  **风格统一**：仙侠要古风（如“萧炎”），西幻要译制腔（如“阿拉贡”）。
2.  **寓意**：名字最好暗含角色的命运或性格。

## 示例输入
生成5个带有“冰雪”寓意的仙侠女角色名字。
