---
id: base-card-chapter-draft
asset_type: capability
title: 默认章节草稿兜底能力
topic: [通用]
stage: drafting
quality_grade: B
source_path: _原料/基座/116-玄幻小说-创作阶段-章节创作.md
last_updated: '2026-05-15'
provider_kind: deterministic_asset_provider
state_writes: [workspace.chapter_text]
---

# 默认章节草稿兜底能力

当 skill-router 没有可用 adapter 时，生成可测试的离线章节草稿。生产正文优先走 dark-fantasy adapter 或真实 LLM CLI path。
