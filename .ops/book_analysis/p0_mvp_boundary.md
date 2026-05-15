# v1.3-0 / v1.3-1 P0 MVP 边界

更新时间：2026-05-15

本文定义拆书融梗 Evidence Pipeline 第一轮边界。它是 v1.3-0 文档补强与 v1.3-1 Reference Corpus P0 MVP 的底层规则，不代表 v1.3 已进入生产能力。第一轮能力边界固定为 `scan / split / manifest / validator / report`。

## 目标定位

`BookAnalysisLayer` / `ReferenceTropeDistillation` 是 Platform 层的可选 sidecar：用于把参考作品先整理成可验证的来源清单、章节索引和扫描报告，后续才可能进入 evidence / chapter atom / trope recipe 候选。第一轮只证明「参考语料可被安全扫描和隔离」，不证明「已经可用于创作」。

第一轮允许：

- `scan`：读取输入文件元信息，计算 hash，记录大小、编码、标题和运行参数。
- `split`：按章节标题切分，生成章节索引和章节连续性诊断。
- `manifest`：生成 `source_manifest.yaml` 或 `source_manifest.json`。
- `validator`：验证输出完整性、污染隔离和 RAG 排除红线。
- `report`：生成扫描 / 切分 / 验证报告，只能描述结构性诊断。

第一轮禁止：

- 不做内容分析、人物关系分析、主题画像或情节总结。
- 不生成 `chapter_atom`、剧情线聚合、coverage / overlap 质量门结果。
- 不自动化 D1-D12 拆书维度，不生成 `trope_recipe_candidate`。
- 不做文风指纹、句长分布、对话比例、TTR、POS 或 ngram 分析。
- 不做 Promote，不写入 Foundation 资产，不新增 Foundation schema。
- 不做 Sidecar RAG，不建立向量索引，不把污染源加入默认 RAG source；默认 RAG 配置只允许维护排除清单。
- 不注册新 skill，不接入创作 workflow，不把任何参考作品片段注入 prompt。

## 输出域

所有第一轮产物只能落到：

```text
.ops/book_analysis/<run_id>/
```

允许的 P0 产物：

- `source_manifest.yaml` 或 `source_manifest.json`
- `chapter_index.json`
- `scan_report.md` 或仅含结构诊断的 `analysis_report.md`
- `validation_report.json` 或 validator stdout 对应的报告文件
- `run_config.yaml`（可选，保存本轮显式配置）

禁止输出或写入：

- `foundation/runtime_state/`
- `foundation/raw_ideas/`
- `foundation/assets/`
- `foundation/schema/`
- `foundation/rag/` 的默认召回源或索引产物（排除清单维护除外）
- 任意创作 prompt、workflow 输入、provider 默认输入白名单

`.ops/book_analysis/<run_id>/` 是污染源域。所有源自参考作品的文件必须在 manifest 中标记 `pollution_source: true`，文本类文件头必须包含 `[SOURCE_TROPE]`。

## 污染隔离红线

- 不写 `foundation/runtime_state/`；任何 runtime state 真值仍只能经 `StateIO` 写入。
- 不进默认 RAG；默认索引流程必须排除 `.ops/book_analysis/`、外部采集原文和污染源文件。
- 不使用 `foundation/raw_ideas/` 暂存拆书结果；`raw_ideas` 只保留灵感逃逸通道语义。
- 不把原文、人物名、势力名、地名、能力名、桥段链路或审计结果注入创作 prompt。
- v1.4 explorer、v1.5 review、创作 provider 的默认输入白名单不得包含 `.ops/book_analysis/`。
- 后续如需 promote，必须另走人工审核、污染检查和 Foundation validator；P0 manifest 不能被当作 promote 许可。

## 资源上限

P0 默认值必须保守，可通过显式 config 覆盖；覆盖值必须写入 manifest 的 `limits.configured` 与 `resources`，不能只存在于 CLI 参数。

| 项 | 默认值 | 可配置字段 | 超限行为 |
|---|---:|---|---|
| 输入文件大小 | `10485760` bytes（10 MiB） | `limits.max_input_size_bytes` | `error`，停止运行，不生成假章节 |
| 章节数 | `500` 章 | `limits.max_chapters` | `error`，停止或只生成失败报告 |
| 单轮处理耗时 | `120` 秒 | `limits.max_elapsed_seconds` | `error`，写入超时状态，不继续分析 |
| 单章标题长度 | `120` 字符 | `limits.max_chapter_title_chars` | `warning`，保留标题但标异常 |
| P0 原文摘录长度 | `0` 字符 | `limits.max_excerpt_chars` | `error`，P0 不保存原文摘录 |
| 私有 evidence cache | 关闭 | `limits.private_cache_enabled` | `error`，P0 不创建 `.private_evidence/` |
| 私有 cache 上限 | `0` bytes | `limits.max_private_cache_bytes` | `error`，P0 不保存原文缓存 |

降级与停止规则：

- 编码识别失败：允许在显式配置 `encoding` 后重跑；本轮状态为 `error`。
- 无章节标题：不得生成「第 1 章」这类假章节；状态为 `error`，报告写明未识别章节模式。
- 章节跳号、重复标题、疑似番外 / 序章 / 后记：状态可为 `warning`，但必须记录到 `chapters.anomalies`。
- 单章失败不应伪装成功；未来允许 `completed_with_errors` 时，必须列出失败章节和重试状态。
- 输入超限、写入越界、缺 hash、污染标记缺失、默认 RAG 未排除：均为 `error`。

## 关键词来源规则

Phase 2 才会使用 evidence 关键词，但 P0 底层规则和 manifest 必须预留并记录关键词来源。

允许来源：

- 显式 config：例如 `run_config.yaml` 中的 `keyword_sources`。
- 用户输入：本轮命令或交互输入中明确声明的关键词。
- 已审核 pattern seed：已经通过人工审核和污染检查的泛化 seed。

禁止来源：

- 禁止在代码中硬编码关键词。
- 禁止把未审核参考原文中抽出的词自动升级为创作关键词。
- 禁止从人物名、势力名、地名、能力名等专有名词直接生成创作关键词。
- 禁止从 `.ops/book_analysis/` 污染源域自动反哺默认 prompt、默认 RAG 或 Foundation 资产。

记录要求：

- 每次 evidence run 都必须记录 `keyword_sources`，即使关键词为空。
- P0 run 必须保留 `keyword_sources.active: false` 或等价字段，证明本轮未执行 evidence 抽取。
- 每个关键词条目必须记录 `source_type`、`value` 或 `value_hash`、`review_status`、`created_by`、`created_at`。
- 未达到 `review_status: approved` 的 seed 只能用于 sidecar 实验，不能进入 promote 或创作 workflow。

## Manifest 要求

`.ops/book_analysis/<run_id>/source_manifest.yaml` 或 `.json` 至少包含：

- `run_id`、`schema_version`、`created_at`
- `source.path`、`source.sha256`、`source.encoding`、`source.title`、`source.input_size_bytes`
- `output.root`、`output.chapter_index_path`、`output.report_path`
- `chapters.count`、`chapters.numbering_ok`、`chapters.anomalies`、`chapters.chapter_index_path`
- `resources.input_size_bytes`、`resources.chapter_count`、`resources.elapsed_seconds`
- `keyword_sources`
- `pollution.pollution_source: true`
- `pollution.source_marker: "[SOURCE_TROPE]"`
- `pollution.default_rag_excluded: true`
- `validation.validator`、`validation.status`、`validation.errors`、`validation.warnings`
- `limits`

字段草案见 `.ops/book_analysis/schema/source_manifest.schema.yaml`。

## Validator DoD

P0 validator 至少检查：

- 文件存在性：run 目录、manifest、`chapter_index.json`、报告文件。
- 路径边界：所有输出路径都在 `.ops/book_analysis/<run_id>/` 下；源文件未被覆盖或改写。
- 必填字段：manifest 必填结构完整，字段类型可解析。
- hash：`source.sha256` 存在且格式为 64 位 hex；章节索引中如记录 chapter hash，也必须可解析。
- 章节：`chapters.count` 与 `chapter_index.json` 一致；无章节标题时不能生成假章节。
- 章节异常：重复标题、跳号、倒序、空标题、超长标题必须进入 `chapters.anomalies` 或 warnings。
- 污染标记：`pollution_source: true`、`source_marker: "[SOURCE_TROPE]"`、`default_rag_excluded: true` 必须存在。
- RAG 排除：默认 RAG source / recall 配置不得包含 `.ops/book_analysis/`；如未来新增索引源，validator 必须复查排除规则。
- StateIO 边界：本轮不得写 `foundation/runtime_state/`，不得生成 runtime_state patch。
- raw_ideas 边界：本轮不得写 `foundation/raw_ideas/`。
- prompt 边界：本轮不得生成或修改创作 prompt，不得把污染源路径加入 provider 默认输入白名单。
- 关键词来源：`keyword_sources` 结构存在；Phase 2 evidence run 中每个关键词都有来源和审核状态。
- 资源上限：输入大小、章节数、耗时、摘录长度和 cache 设置均写入 manifest；超限时状态不能为 `passed`。

`error` 规则：

- 缺 manifest / 章节索引 / source hash。
- 输出越界或覆盖源文件。
- 无章节标题却生成假章节。
- 缺污染标记或默认 RAG 排除标记。
- 写入 `foundation/runtime_state/`、`foundation/raw_ideas/`、默认 RAG 或 prompt 相关目录。
- P0 保存原文摘录或私有 evidence cache。

`warning` 规则：

- 章节跳号、重复标题、疑似番外 / 序章 / 后记。
- 标题超长、章节字数异常、章节编号格式混用。
- 用户提供了关键词但本轮处于 P0，未执行 evidence 抽取。

目标验证命令：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_book_analysis_corpus
python3 scripts/validate_reference_corpus.py .ops/book_analysis/<run_id>
python3 scripts/verify_all.py
```

当前 v1.3-0 文档阶段尚未要求上述脚本存在；进入 v1.3-1 实现后，这三条命令是最低验收门。
