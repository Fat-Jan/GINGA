---
id: prompts-card-write_courtroom_drama-131
asset_type: prompt_card
title: 庭审/辩论对决脚本
topic:
  - 都市
stage: drafting
quality_grade: B+
source_path: _原料/提示词库参考/prompts/131.md
last_updated: 2026-05-13
card_intent: prose_generation
card_kind: scene_card
task_verb: write
task_full: write_courtroom_drama
granularity: scene
output_kind: schema_json
dedup_verdict: retain
dedup_against: []
---

# 131. 庭审/辩论对决脚本

## 提示词内容

```json
{
  "task": "write_courtroom_drama",
  "case": "Murder / Intellectual Property Theft",
  "prosecutor_point": "Irrefutable DNA evidence / Timestamped logs",
  "defense_tactic": "Technicality / Framing the witness / Emotional appeal",
  "turnabout": "New evidence presented at the last second (Objection!)",
  "verdict": "Not Guilty / Mistrial"
}
```

## 使用场景
律政/都市文。描写紧张的法庭交锋。

## 最佳实践要点
1.  **逻辑攻防**：重点描写证据链的建立与推翻，而非单纯的吵架。
2.  **戏剧性**：设置“异议！”（Objection）时刻，引入关键证人或证据反转局势。

## 示例输入
```json
{
  "case": "密室谋杀案",
  "prosecutor_point": "监控时间戳证明被告进过房间",
  "defense_tactic": "证明时间戳被远程篡改",
  "turnabout": "最后一分钟提交服务器日志"
}
```
