# v1.3-0 拆书融梗污染检查规则

状态：draft
适用范围：`ReferenceTropeDistillation` / `.ops/book_analysis/<run_id>/`
更新时间：2026-05-15

本文是 v1.3-0 污染隔离底层规则。它只定义规则口径和 validator / 人工审核清单，不代表 v1.3 已实现。当前第一轮只允许做 `scan / split / manifest / validator / report`，不得做 D1-D12 自动化、文风指纹、Promote、Sidecar RAG。

## 1. 目标与边界

拆书融梗的目标是把参考作品中的商业梗、节奏机制、桥段功能和读者爽点抽象成可变形的 `trope_recipe` 候选，而不是保存或复用原作的皮。

必须保留：

- 机制描述：为什么爽、何时触发、如何变形、适合放在哪个创作阶段。
- 来源证据：source hash、excerpt hash、章节定位、短摘要和用途。
- 污染标记：所有源自参考作品的 sidecar 文件必须可被 validator 识别。

必须禁止：

- 不写 `foundation/runtime_state/`，不绕过 `StateIO`，不建立第二状态真值。
- 不进默认 RAG；默认 `foundation/rag/recall_config.yaml` 只能维护污染源排除清单，不得把 `.ops/book_analysis/` 加入 `recall_sources`。
- 不使用 `foundation/raw_ideas/` 暂存拆书结果。
- 不把拆书报告、原文摘录、checker / audit 结果注入创作 prompt。
- 不进入 v1.4 explorer、v1.5 review、创作 provider 的默认输入白名单。

## 2. 文件域与污染标记

`.ops/book_analysis/<run_id>/` 是污染源域。该目录下任何源自参考作品的 manifest、章节索引、分析报告、evidence、candidate、validator 输出都必须显式标记污染来源。

最低要求：

- JSON / YAML manifest 必须包含 `pollution_source: true`。
- Markdown 或文本产物文件头必须包含 `[SOURCE_TROPE]`。
- 每个 run 必须有唯一 `run_id`、输入源路径记录、生成时间、工具版本或规则版本。
- 每个源文件必须记录 `source_hash`，推荐使用 `sha256`。
- 每个拆分章节必须记录 `chapter_hash`，并在 `chapter_index.json` 中绑定章节号、标题、字数和异常状态。
- 下游候选、报告和 validator 输出只允许引用 evidence ID / hash，不允许直接复制长摘录。

示例字段：

```yaml
run_id: ""
pollution_source: true
source:
  path: ""
  sha256: ""
  title: ""
chapters:
  - chapter_no: 1
    title: ""
    chapter_hash: ""
    char_count: 0
    anomalies: []
```

## 3. Source Hash / Excerpt Hash 规则

所有 evidence 必须同时具备 source 级和 excerpt 级可追溯性。

必填字段：

- `source_hash`：原始参考作品文件的 `sha256`。
- `chapter_no` / `chapter_title` / `chapter_hash`：章节定位与章节内容 hash。
- `excerpt_hash`：摘录文本规范化后的 hash；默认使用 `sha256(normalized_excerpt)`。
- `summary`：不超过 120 字的中文短摘要，只描述功能和机制。
- `purpose`：只能是 `structure`、`rhythm`、`dialogue`、`scene`、`trope`、`character_function`、`worldbuilding_mechanism`、`foreshadow` 之一。
- `allowed_use`：默认 `analysis_only`；未通过人工审核前不得改为可 promote。

摘录 hash 的规范化口径：

- 统一换行符为 `\n`。
- 去除首尾空白，不改正文内部文字。
- 不做同义改写后再 hash。
- hash 输入不得包含文件路径、章节号或运行时间，避免同一摘录因元数据变化产生不同 hash。

## 4. 原文摘录存储规则

默认 evidence 只能保存 hash、短摘要、章节定位和用途，不长期保存原文摘录。

允许保存：

- `excerpt_hash`
- `summary`
- `chapter_no`
- `chapter_title`
- `chapter_hash`
- `purpose`
- `source_hash`

禁止保存：

- 长段原文。
- 可连续还原原章节的多条短摘录集合。
- 原台词、金句、独特谜底、具体事件链的完整表述。
- promoted asset 内的任何原文长摘录。

临时私有摘录 cache 规则：

- 只能位于 `.ops/book_analysis/<run_id>/.private_evidence/`。
- 只能用于人工核验、hash 复算或 debug。
- manifest 中不得把 private cache 路径列为长期 evidence source。
- promote 前必须删除该目录，或由 validator 证明没有 promoted candidate / asset / report 引用其中任何文件路径。
- `.private_evidence/` 下文件不得进入 RAG、StateIO、raw_ideas、prompt 或 explorer/review 默认白名单。

## 5. 专有名词黑名单

以下原作元素不得进入 candidate 主体或 promoted asset。candidate 只能在 `forbidden_copy_elements` 或人工审核备注中记录类别，不得记录可复用的原文实体本身。

黑名单类别：

- 原人物名、外号、称号、角色组合名。
- 原势力名、组织名、宗门名、公司名、家族名。
- 原地名、国名、城市名、秘境名、建筑名、地图结构。
- 原能力名、招式名、等级名、道具体系名、货币名。
- 独特设定：只要能让读者直接定位原作的世界观、制度、身份、代价、仪式或限制。
- 原台词、金句、标志性口癖、可搜索的独特句式。
- 独特谜底、反转真相、伏笔回收答案。
- 具体事件链：按原作顺序复述的冲突、误会、升级、揭示、结局组合。
- 特定人物关系皮：原作中高度可识别的师徒、血缘、CP、仇怨、背叛链。

允许保留的只能是机制层描述，例如：

- 「弱势主角被低估后，用公开验证场景反转地位」。
- 「资源缺口制造短期压力，再通过代价型突破换取阶段胜利」。
- 「误导线索先服务读者预期，后在高潮前转为身份反差」。

## 6. Candidate 主体规则

`trope_recipe_candidate` / `reference_pattern_candidate` 是污染源候选，不是可直接创作资产。未通过人工审核与污染检查前，不得进入任何创作 workflow。

必填安全字段：

```yaml
pollution_source: true
source_refs:
  - evidence_id: ""
    source_hash: ""
    excerpt_hash: ""
trope_core: ""
reader_payoff: ""
trigger_conditions: []
variation_axes: []
forbidden_copy_elements: []
safety:
  source_contamination_check: pending
  similarity_score: null
  human_review_status: pending
target:
  promote_to: none
```

`trope_core` 必须是机制描述：

- 必须回答「这个梗如何产生读者爽点」和「它依赖什么触发条件」。
- 不得保留原作人物名、势力名、地名、能力名或具体事件链。
- 不得用「把 A 改名成 B」这类替换写法。
- 不得包含连续剧情步骤到足以复原原作桥段。

`variation_axes` 至少包含 2 个替换方向，用来证明候选不是改名搬运。推荐方向：

- `genre_swap`：题材或时代替换。
- `identity_swap`：角色身份、阶层、职业或关系功能替换。
- `power_system_swap`：力量体系、资源体系或代价机制替换。
- `conflict_scale_swap`：个人、家族、组织、城市、世界级冲突规模替换。
- `emotional_tone_swap`：热血、悬疑、喜剧、压抑、温情等情绪颜色替换。
- `plot_position_swap`：黄金三章、卷中反转、阶段高潮、章末钩子、伏笔回收位置替换。

validator 口径：

- `variation_axes` 有效方向少于 2 个：fail。
- `trope_core` 含黑名单实体或原作事件链：fail。
- `forbidden_copy_elements` 为空：fail。
- 缺 source / excerpt hash：fail。
- `human_review_status != approved` 时尝试 promote：fail。

## 7. 相似度阈值口径

当前 v1.3-0 不实现算法，只先定义检查口径。后续 validator / promote 可按以下阈值落地。

文本相似度：

- `>= 0.80`：fail。candidate 或 promoted asset 与原文表达高度相似，必须退回重写或删除。
- `0.65 - 0.79`：needs_review。必须人工确认是否仍保留原句式、原台词或具体事件链。
- `< 0.65`：仅代表表达层低相似，不自动视为安全，仍需检查专名和事件链。

结构相似度：

- 原作连续事件链保留超过 3 个关键节点：fail。
- 原作人物功能组合、冲突对象、谜底和回收顺序同时保留：fail。
- 章节节奏表、高潮间隔、伏笔回收顺序与单一原作高度一致：needs_review 或 fail。
- 跨多个参考作品抽象出的通用机制，且 variation_axes 足够：可进入人工审核。

专名相似度：

- candidate 主体或 promoted asset 出现黑名单实体：fail。
- 仅在 `forbidden_copy_elements` 中记录类别而非实体：pass。
- 需要保留证据时只能通过 evidence hash 与章节定位追溯，不在主体复写实体。

## 8. 人工审核清单

promote 前必须人工逐项确认：

- 已运行对应 validator，且 `source_contamination_check: pass`。
- 所有 evidence 都有 `source_hash`、`chapter_hash`、`excerpt_hash` 和章节定位。
- promoted asset 不包含长摘录、原台词、原专名、原能力名、独特谜底或具体事件链。
- `trope_core` 是机制描述，不是原作剧情摘要。
- `variation_axes` 至少 2 个有效替换方向，且能产生不同题材、身份或冲突结构。
- `forbidden_copy_elements` 覆盖本候选涉及的专名、事件链、谜底、设定和台词风险。
- `.private_evidence/` 已清理，或 validator 证明没有 promoted asset / candidate 引用该目录路径。
- 目标落点在白名单内，且不会加入默认 RAG source、修改 `runtime_state` 或写入 `raw_ideas`。
- 审核记录写入 `.ops/book_analysis/<run_id>/audit.json` 或同级 report，不写入创作 prompt。

## 9. 默认排除规则

以下路径和产物默认不得被任何主链读取：

- `.ops/book_analysis/`
- `.ops/book_analysis/<run_id>/.private_evidence/`
- 外部参考作品原文。
- 外部榜单原始数据。
- 带 `pollution_source: true` 的 JSON / YAML / Markdown。
- 文件头包含 `[SOURCE_TROPE]` 的文本或 Markdown。

默认禁止进入：

- RAG 默认索引与召回。
- `StateIO` / `foundation/runtime_state/`。
- `foundation/raw_ideas/`。
- 创作 prompt 组装路径。
- explorer / review 默认输入白名单。
- 默认 `workflow DSL` 步骤输入。

未来若新增 Reference Sidecar RAG，必须是显式开启模式，返回结果必须标 `source=reference_sidecar`，且 sidecar 配置不得写入默认 `foundation/rag/recall_config.yaml` 的 `recall_sources`。

## 10. Phase 0 / P0 第一轮限制

第一轮只允许：

- `scan`：识别输入文件、大小、编码、章节模式和基本异常。
- `split`：拆分章节并生成章节索引，不覆盖源文件。
- `manifest`：记录 source hash、chapter hash、章节数、字数、异常和污染标记。
- `validator`：检查 hash、路径域、污染标记、章节连续性、RAG / StateIO / raw_ideas 排除口径。
- `report`：输出面向人工的分析报告，只描述扫描结果和风险。

第一轮禁止：

- D1-D12 自动化。
- chapter atom 自动抽取。
- 文风指纹。
- 角色 / 世界观画像。
- Promote。
- Sidecar RAG。
- 将候选写入 Foundation schema / assets。
- 将任何拆书结果写入 `foundation/runtime_state/`、`foundation/raw_ideas/` 或创作 prompt。

## 11. Validator 最低检查项

v1.3-0 validator 至少应检查：

- `.ops/book_analysis/<run_id>/` 下 manifest 存在且 `pollution_source: true`。
- Markdown / 文本污染源文件头包含 `[SOURCE_TROPE]`。
- source file、chapter、evidence 均有 hash。
- `.private_evidence/` 不被 manifest、candidate、report 或 promoted asset 引用。
- candidate 缺 `variation_axes`、`forbidden_copy_elements`、`source_contamination_check` 时 fail。
- 输出路径不在 `foundation/runtime_state/`、`foundation/raw_ideas/`、默认 RAG 配置或创作 prompt 目录。
- 默认 RAG / explorer / review / provider 白名单不包含 `.ops/book_analysis/`。
- 第一轮 run 中没有 D1-D12、文风指纹、Promote、Sidecar RAG 产物。

## 12. 通过标准

一个候选最多只能在以下条件全部满足后进入 promote 讨论：

- 所有来源证据可通过 hash 和章节定位追溯。
- 主体文本没有黑名单实体、原台词、独特谜底、具体事件链和长摘录。
- `trope_core` 是机制描述。
- `variation_axes` 至少 2 个有效替换方向。
- 相似度检查未触发 fail，人工审核清单全部通过。
- promoted asset 目标路径在白名单内，并经过对应 Foundation validator。
- 默认 RAG、StateIO、raw_ideas、创作 prompt、explorer/review 默认白名单均未被污染。

若任一条无法确认，状态必须保持 `BLOCKED` 或 `needs_review`，不得猜测通过。
