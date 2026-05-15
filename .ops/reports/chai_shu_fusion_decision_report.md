# 拆书 × Ginga 融合决策报告

日期：2026-05-15
范围：`/Users/arm/Desktop/拆书` 与 `/Users/arm/Desktop/ginga`
结论：**建议融合，但只作为可选 BookAnalysisLayer / reference analysis 支线融合；不要并入当前小说生成主链。**

## 第三方评审记录

使用 `ark-jury-court` / `ask-jury-safe` 对草案 `.ops/reports/chai_shu_fusion_research_draft.md` 做了外部评审。

- 默认矩阵：`.ops/jury/chai_shu_fusion_review_2026-05-15/`
  - `ioll-grok`：有效，输出 3582 bytes。
  - `wzw`：wrapper 标 OK，但输出 0 bytes，判为无效票。
- reserve 矩阵：`.ops/jury/chai_shu_fusion_review_2026-05-15_reserve/`
  - `windhub`：有效，输出 4471 bytes。
  - `xiaomi-tp`：部分有效，输出 2127 bytes，但内容截断。

有效评审共识：

- 不应让拆书支线挤压 P2-7C provider 质量与真实 demo 主线。
- `sidecar RAG` 必须有物理隔离、独立配置和显式启用机制。
- “人工确认后 promote”必须有可执行流程，不能只写口号。
- 版权 / 来源污染需要字段化约束：来源证据 hash、人工签批、相似度 / 桥段搬运检查。
- 分析层如果使用 `StateIO`，必须明确只写 artifact / audit，不写任何创作 `runtime_state` 域。

## 最终定位

定义一个可选子系统：

`BookAnalysisLayer = 参考作品资产采集与预处理层`

它的职责：

- 读取外部参考小说 / 拆书语料。
- 做章节拆分、基础扫描、轻量统计、场景证据抽取。
- 产出 sidecar artifact、分析报告、promotion candidate。
- 只把“去来源污染、结构化、人工确认”的泛化模式交给 Foundation。

它不是：

- 不是 Ginga 章节生成主链的一部分。
- 不是新的默认 RAG 来源。
- 不是 `raw_ideas` 暂存区。
- 不是能直接修改 `locked` / `entity_runtime` / `workspace` 的生产 runner。

## 能融合多少

按功能价值估算：**约 55%-65% 可以融合**。

高价值，可融合：

- 章节 ingest / split：把参考作品变成可审计 corpus。
- self-audit 思路：变成 `validate_reference_corpus.py`。
- 场景抽取：变成来源带 hash 的 evidence snippets。
- 基础角色 / 主题频次：用于参考作品画像，不写目标作品角色状态。
- D1-D12：先作为候选输出格式和人工拆书表，不立刻升为 Foundation schema。

中价值，延后融合：

- 文风指纹：有价值，但依赖 `jieba` / `numpy` 和中文标点健壮性，先 P1。
- 跨作品对比：等 D1-D12 输出稳定后再做。
- style lock 校准建议：只能生成建议或 locked patch 候选，不能自动改锁定域。

低价值或不建议融合：

- `show_results.py` / `display_results.py`：只是控制台展示。
- `fix_dialogue.py` 原脚本：会直接覆盖 JSON；可评估其中“对话比例重算”算法，但不要迁移脚本行为。
- 当前 `reports/` 产物：多为样例 / 零值，不可当证据。

## 调整后的优先级

P0 只做实验支线 MVP，避免抢主线：

1. `reference_corpus_scan`：显式输入 / 输出目录，产出章节清单、字数、标题、连续性诊断。
2. `reference_chapter_split`：纯函数化拆章，tempdir 输出，不覆盖原目录。
3. `validate_reference_corpus.py`：空输入、章节缺失、编码、重复标题、异常体量检查。
4. `.ops/book_analysis/<run_id>/analysis.json` + `analysis_report.md`。

P1 再做分析能力：

- 场景抽取 evidence snippets。
- 角色 / 主题频次画像。
- 文风指纹 provider。
- D1-D12 candidate schema。

P2 做资产化：

- `promotion_candidate.yaml`。
- source hash / evidence hash / human_review_status / signed_audit_log。
- sidecar RAG index + 独立 recall config。

P3 视情况 skill 化：

- 只有当拆书变成长期复杂能力、有独立 contract、多 provider 编排和配置状态，才注册第 3 个 skill。

## 架构落点

推荐路径：

```text
external novel.txt
  -> BookAnalysisLayer provider
  -> .ops/book_analysis/<run_id>/*
  -> promotion_candidate.yaml
  -> human review / source safety checker
  -> Foundation methodology / prompt example / reference pattern
  -> optional sidecar RAG
```

关键约束：

- P0 不新增默认 workflow 主链步骤。
- 可新增独立 CLI：`ginga analyze-book`，或独立 workflow：`book_analysis_pipeline.yaml`。
- 分析产物默认落 `.ops/book_analysis/<run_id>/`，不落 `foundation/runtime_state/<book_id>/`。
- 若为了审计复用 `StateIO.write_artifact()`，必须加 analysis-only 约束：禁止 `apply()` 写任何 YAML state 域。
- sidecar RAG 必须独立配置，例如 `foundation/rag/reference_sidecar_recall.yaml`；默认 `step_dispatch` 不读它。
- promote 到 Foundation 必须走唯一入口，例如 `ginga promote-reference-pattern`，不能手工散落复制。

## 必须补的安全字段

`promotion_candidate.yaml` 至少要包含：

```yaml
source:
  title: ""
  source_path: ""
  source_hash: ""
  license_or_usage_note: ""
evidence:
  snippets:
    - id: ""
      chapter: ""
      excerpt_hash: ""
      purpose: "structure|rhythm|dialogue|scene|trope"
derived_pattern:
  abstraction: ""
  forbidden_copy_elements:
    - character_name
    - unique_setting
    - distinctive_plot
safety:
  source_contamination_check: "pending|pass|fail"
  similarity_score: null
  human_review_status: "pending|approved|rejected"
  signed_audit_log: []
target:
  promote_to: "methodology|prompt_example|reference_pattern|none"
```

## 最小下一步

如果决定动手，建议只开一个窄任务：

> 实现 `BookAnalysisLayer P0`：纯函数化 reference corpus scan/split + validator + `.ops/book_analysis/<run_id>` 报告，禁止写 runtime_state，禁止默认 RAG 接入。

验收：

- tempdir 单测覆盖正常拆章、空输入、无“第 X 章”、重复标题、大文件截断策略。
- 验证不会改 `/Users/arm/Desktop/拆书` 原目录。
- 验证不会写 `foundation/runtime_state/`。
- 输出 artifact 带 run_id、source_hash、文件清单、章节统计。
- `python3 scripts/verify_all.py` 仍通过。

## 决策

可以融合，但不是“把拆书搬进 Ginga”。正确做法是：

- **先吸收能力，不吸收脚本形态。**
- **先做 sidecar，不进默认 RAG。**
- **先做证据和审计，不直接服务生成 prompt。**
- **先守住 P2-7C 主线，再用 P0 实验支线验证 ROI。**
