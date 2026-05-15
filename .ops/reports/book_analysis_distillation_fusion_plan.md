# 拆书逻辑蒸馏融合规划

日期：2026-05-15
目标：从 `/Users/arm/Desktop/拆书` 蒸馏有用逻辑和内容，融合为 Ginga 的可选参考作品拆书 / 融梗能力，而不是原样搬运拆书脚本。

## 一句话方案

把拆书蒸馏成 Ginga 的 `BookAnalysisLayer`，更准确地说是 `ReferenceTropeDistillation`：

```text
参考作品 / novel.txt
  -> 只读扫描与拆章
  -> 梗核 / 爽点 / 桥段结构 / 节奏公式抽取
  -> 去来源污染的 trope / pattern candidate
  -> 人工确认 / 安全审计
  -> Foundation methodology / prompt example / reference_pattern / trope_recipe
  -> 可选 sidecar RAG
```

## 核心定位修正：拆书是为了融梗

这里的“拆书”不是学术式作品分析，也不是只产一份读书报告。它的真正价值是：

```text
把参考网文里的可复用商业梗、爽点机制、桥段结构、节奏安排拆出来，
去掉原作专名和具体表达，
变成 Ginga 能在新作品里重新组合、变形使用的创作配方。
```

因此蒸馏对象优先级应从“分析完整性”转为“可融梗性”：

1. **梗核**：这个桥段为什么爽、为什么能驱动读者继续读。
2. **触发条件**：什么人物关系、局势压力、资源缺口会让这个梗成立。
3. **变形参数**：题材、身份、力量体系、冲突规模、情绪颜色如何替换。
4. **节奏位置**：适合黄金三章、卷中反转、阶段高潮、章末钩子还是伏笔回收。
5. **禁搬元素**：原作人物名、势力名、地名、能力名、原台词、独特谜底和具体事件链。
6. **Ginga 落点**：进入 outline、chapter_draft、cool_point、foreshadow、dialogue、worldbuilding 中哪一类能力。

一句话：**保留梗的机制，丢掉原作的皮。**

## 蒸馏边界

保留：

- 拆章、扫描、统计、场景抽取、文风指标、D1-D12 拆解框架、跨作品对比、自审思路。
- 参考作品作为“分析对象”的价值。
- 从参考作品中抽象结构、节奏、技法、模式的能力。

丢弃：

- 硬编码 `BASE_DIR` 的脚本形态。
- 直接覆盖 `chapters/`、`reports/`、`deconstruction/` 的写法。
- 当前空产物 / 样例产物。
- 控制台展示脚本作为核心能力。
- 任何把原文、人物、设定、桥段直接喂给生成主链的路径。

禁止：

- 不写 `foundation/runtime_state/`。
- 不进默认 RAG。
- 不使用 `foundation/raw_ideas/` 暂存拆书结果。
- 不把拆书报告 / checker / audit 注入 prompt。
- 不自动改 `locked.GENRE_LOCKED`、`STORY_DNA`、`CHARACTER_STATE`。

## 可蒸馏内容矩阵

| 拆书来源 | 蒸馏后能力 | Ginga 落点 | 优先级 | 说明 |
|---|---|---|---|---|
| `split_chapters.py` | `reference_chapter_split` | `book_analysis` provider / CLI | P0 | 纯函数化拆章，输出到 `.ops/book_analysis/<run_id>/chapters/` |
| `rename_chapters.py` | 章节规范化索引 | provider 内部函数 | P0 | 生成 `chapter_index.json`，不复制覆盖原目录 |
| `scan_all.py` | `reference_corpus_scan` | provider / validator | P0 | 章节数、字数、标题、连续性、异常章节 |
| `self_audit.py` | `validate_reference_corpus.py` | `scripts/` 可选 validator | P0 | 验证输入、输出、章节、报告完整性 |
| `extract_all_scenes.py` | `reference_scene_evidence` | sidecar artifact | P1 | 带 source hash / excerpt hash 的证据片段 |
| `auto_analyze.py` | 角色 / 主题画像 | analysis artifact | P1 | 只描述参考作品，不写目标作品角色状态 |
| `stylometric_quantitative.py` | 文风指纹 | analysis provider | P1 | 句长、对话比例、虚词、TTR、ngram；先处理依赖和异常 |
| `deconstruction_report.py` | D1-D12 候选结构 | `reference_pattern` candidate | P1 | 先做 `.ops` candidate，稳定后再进 Foundation schema |
| `cross_compare.py` | 多作品模式对比 | `.ops/book_analysis` report | P2 | 基于结构化 D1-D12，不继续用脆弱正则截取 |
| `fix_dialogue.py` | 对话比例校准函数 | style fingerprint 子函数 | P2 | 只抽算法，不迁移覆盖 JSON 行为 |
| `show_results.py` / `display_results.py` | 报告渲染参考 | report renderer | P3 | 低优先级，只保留展示思路 |

## 蒸馏后的资产类型

### 1. Reference Corpus Artifact

外部参考作品的只读分析结果，不进入默认 RAG。

建议路径：

```text
.ops/book_analysis/<run_id>/
  source_manifest.json
  chapter_index.json
  analysis.json
  analysis_report.md
  audit.json
  chapters/
```

关键字段：

```yaml
source:
  path: ""
  sha256: ""
  encoding: "utf-8"
  title: ""
chapters:
  count: 0
  numbering_ok: true
  anomalies: []
stats:
  total_chars: 0
  chapter_length:
    mean: 0
    min: 0
    max: 0
```

### 2. Evidence Snippet

用于证明某个模式来自哪些参考证据，但不能直接进入生成 prompt。

```yaml
id: evidence-001
source_hash: ""
chapter_no: 1
excerpt_hash: ""
purpose: "structure|rhythm|dialogue|scene|trope"
summary: ""
excerpt_storage: "hash_only"
private_excerpt_cache: null
allowed_use: "analysis_only"
```

### 3. Reference Pattern Candidate

D1-D12 蒸馏结果，默认仍是候选，必须人工确认。对网文融梗场景，推荐把候选细分为 `trope_recipe`。

```yaml
id: ref-pattern-001
dimension: D2
name: "黄金三章节奏"
abstraction: ""
trope_core: ""
reader_payoff: ""
trigger_conditions:
  - ""
variation_axes:
  genre: []
  identity_swap: []
  power_system_swap: []
  emotional_tone: []
applicable_stage:
  - outline
  - chapter_draft
evidence_refs:
  - evidence-001
forbidden_copy_elements:
  - character_name
  - unique_setting
  - distinctive_plot
safety:
  source_contamination_check: pending
  similarity_score: null
  human_review_status: pending
target:
  promote_to: none
```

### 4. Promoted Foundation Asset

只有通过人工确认和污染检查后，才进入：

- `foundation/assets/methodology/`
- `foundation/assets/prompts/`
- 未来可选：`foundation/assets/reference_patterns/`

## D1-D12 蒸馏规划

| 维度 | 蒸馏目标 | 可进入 Ginga 的形态 | 禁止项 |
|---|---|---|---|
| D1 剧情结构 | 开篇钩子、三幕结构、卷结构 | outline methodology / trope_recipe | 搬原书事件链 |
| D2 节奏控制 | 爽点间隔、高潮密度、章末钩子 | rhythm trope / validator hint | 复制原章节节拍表 |
| D3 人物体系 | 主角公式、配角功能、关系张力 | character trope / design methodology | 搬人物关系和人设名词 |
| D4 爽点类型 | 打脸、升级、反转、身份差 | cool-point trope taxonomy | 搬桥段原皮 |
| D5 金句体系 | 金句功能、位置、句式类型 | synthetic quote pattern | 保存原句 |
| D6 战斗/冲突 | 冲突分镜、升级层次 | conflict trope / scene template | 搬具体战斗设计 |
| D7 世界构建 | 地理/制度/经济/宗教闭环 | worldbuilding trope checklist | 搬世界观专名 |
| D8 力量体系 | 等级、代价、突破机制 | power-system trope | 搬等级名和能力名 |
| D9 对话技法 | 潜台词、冲突推进、信息差 | dialogue trope / methodology | 保存原对话 |
| D10 环境描写 | 场景功能、氛围锚点 | setting trope / atmosphere recipe | 搬特定地名/建筑 |
| D11 伏笔/悬念 | 铺设/误导/回收周期 | foreshadow trope | 搬谜底 |
| D12 情感线 | CP 节奏、虐甜分布、关系推进 | relationship trope | 搬关系设定 |

## 实施批次

### Phase 0：定位和防污染底座

目标：先把规则写清楚，不动主链。

产出：

- `.ops/reports/book_analysis_distillation_fusion_plan.md`
- `promotion_candidate.yaml` 字段规范草案
- `BookAnalysisLayer` 禁止事项清单

验收：

- 明确“不进默认 RAG / 不写 runtime_state / 不进 raw_ideas / 不注入 prompt”。
- 明确 P0 是实验支线，不抢 P2-7C 主线。

### Phase 1：Reference Corpus P0 MVP

目标：把拆章和扫描能力安全接入。

建议新增：

```text
ginga_platform/book_analysis/
  __init__.py
  chapter_splitter.py
  corpus_scan.py
  manifest.py
  report.py
scripts/validate_reference_corpus.py
ginga_platform/orchestrator/runner/tests/test_book_analysis_corpus.py
```

能力：

- 输入 `novel.txt` 和可选 config。
- 自动识别 `第X章`。
- 输出 `.ops/book_analysis/<run_id>/chapter_index.json`。
- 输出 `analysis_report.md`。
- 计算 source sha256。
- 不改源目录。

验收：

- 空输入报清晰错误。
- 无章节标题时给诊断，不生成假章节。
- 重复标题 / 章节序号跳号有 warning。
- tempdir 测试证明不覆盖源文件。
- `python3 scripts/verify_all.py` 通过。

### Phase 2：Evidence + 轻分析

目标：把场景抽取、角色/主题画像接上，但仍只产 sidecar。

建议新增：

```text
ginga_platform/book_analysis/evidence.py
ginga_platform/book_analysis/profile.py
ginga_platform/orchestrator/runner/tests/test_book_analysis_evidence.py
```

能力：

- 根据关键词抽取证据片段。
- 每个片段保存 hash 和来源章节。
- 角色别名 / 主题关键词统计。
- 生成 `evidence_index.json` 和 `profile.json`。

验收：

- 原文片段不会进入默认 prompt。
- 所有 evidence 都有 source hash。
- 可配置最大摘录长度。
- 空关键词不会失败。

### Phase 3：D1-D12 Candidate

目标：把拆书 12 维变成结构化候选，不急着进 Foundation。

建议新增：

```text
.ops/book_analysis/schema/reference_pattern_candidate.yaml
ginga_platform/book_analysis/pattern_candidate.py
scripts/validate_reference_patterns.py
```

能力：

- 生成 D1-D12 空白或半自动候选。
- 候选绑定 evidence refs。
- 强制包含 forbidden_copy_elements。
- 强制 human_review_status。

验收：

- 未 approved 的 candidate 不能 promote。
- 缺 evidence hash 不能通过 validator。
- 原文长摘录不能进入 candidate 主体。
- 实验 schema 稳定前不得放入 `foundation/schema/`。

### Phase 4：文风指纹

目标：蒸馏 `stylometric_quantitative.py` 的指标，而不是照搬脚本。

建议新增：

```text
ginga_platform/book_analysis/style_fingerprint.py
ginga_platform/orchestrator/runner/tests/test_book_analysis_style.py
```

能力：

- 章节长度 CV。
- 句长分布。
- 对话比例，支持中文引号和 ASCII 引号。
- 高频虚词。
- 可选 jieba 指标：TTR、POS、ngram。
- 依赖缺失时降级，不让整条 pipeline 崩。

验收：

- 没有 `jieba` / `numpy` 时基础指标仍可输出。
- 空文本不除零。
- 中文引号测试通过。
- 大文本有最大采样和超时保护。

### Phase 5：Promotion Flow

目标：从候选到 Foundation 资产有唯一入口。

建议新增：

```text
ginga_platform/book_analysis/promote.py
ginga_platform/orchestrator/cli/reference.py
ginga_platform/orchestrator/runner/tests/test_book_analysis_promote.py
```

CLI 形态：

```bash
./ginga reference promote .ops/book_analysis/<run_id>/promotion_candidate.yaml
```

规则：

- `human_review_status` 必须是 `approved`。
- `source_contamination_check` 必须是 `pass`。
- `similarity_score` 若存在必须低于阈值。
- 只允许输出到 whitelist 目录。
- 生成 audit / changelog。
- promote 前必须运行 `validate_reference_patterns.py`。
- promote 后必须运行对应 Foundation validator；若新增 `reference_patterns` 资产类型，必须先定义资产加载协议和命名空间。

验收：

- pending / rejected 不能 promote。
- 缺 hash 不能 promote。
- promote 后 Foundation validator 通过。
- 不修改默认 RAG 配置。

### Phase 6：Sidecar RAG

目标：让参考模式可以被显式查询，但不污染默认创作召回。

建议新增（仅在 Phase 5 promote 闭环稳定后启动）：

```text
ginga_platform/book_analysis/reference_sidecar.py
.ops/book_analysis/<run_id>/reference_sidecar_recall.yaml
ginga_platform/orchestrator/runner/tests/test_reference_sidecar_rag.py
```

规则：

- 物理索引和默认 RAG 分离。
- 只有 `workflow_flags.reference_rag_mode=on` 时启用。
- 默认 `novel_pipeline_mvp.yaml` 不启用。
- 返回结果必须带 `source=reference_sidecar`。
- 不把 sidecar 配置放入默认 `foundation/rag/recall_config.yaml`。
- 实现前先明确：复用现有 RAG 组件的显式配置模式，还是完全独立索引；禁止半接入。

验收：

- 默认 `step_dispatch` 不召回 reference sidecar。
- 显式开启才召回。
- sidecar 结果不能包含原文长摘录。

## 文件层级建议

短期不放进 `foundation/assets`：

```text
.ops/book_analysis/<run_id>/
```

稳定后可新增：

```text
foundation/schema/reference_pattern_candidate.yaml
foundation/assets/reference_patterns/
```

代码建议：

```text
ginga_platform/book_analysis/
scripts/validate_reference_corpus.py
scripts/validate_reference_patterns.py
```

不建议：

```text
foundation/raw_ideas/book_analysis/
foundation/runtime_state/<book_id>/reference_analysis.yaml
```

## 最小可执行路线

第一轮只做 5 件：

1. `chapter_splitter.py`
2. `corpus_scan.py`
3. `manifest.py`
4. `validate_reference_corpus.py`
5. `.ops/book_analysis/<run_id>/analysis_report.md`

暂不做：

- D1-D12 自动生成。
- 文风指纹。
- sidecar RAG。
- promote 到 Foundation。
- 新 skill 注册。

## 成功标准

技术成功：

- 不改源目录。
- 不写 runtime_state。
- 不接默认 RAG。
- 可重复运行，run_id 隔离。
- 有 tempdir 单测和异常输入测试。

产品成功：

- 能把一本参考小说变成清晰的章节清单和基础画像。
- 能告诉用户“这份参考语料适不适合继续拆”。
- 能为下一步 D1-D12 / 场景抽取提供稳定输入。

架构成功：

- Ginga 的主生成链不变。
- BookAnalysisLayer 成为可选支线。
- 只有人工确认的泛化结果才能进入 Foundation。

## Ark Jury 查漏补缺 Addendum

评审时间：2026-05-15
评审产物：本规划文件
评审目录：`.ops/jury/book_analysis_distillation_plan_review_2026-05-15/`

有效票：

- `windhub`：有效，判定 `revise`。
- `xiaomi-tp`：有效但输出截断，判定倾向 `revise`。
- `ioll-grok`：wrapper 标 OK，但输出 0 bytes，判为无效票。

总体判断：

规划方向合理，值得作为 Ginga 支线推进；但 Phase 0 必须补足边界和安全规则后再开实现。

已采纳补缺：

1. **明确架构归属**
   - `BookAnalysisLayer` 归 Platform 层，是可选 capability provider / CLI 子系统。
   - 它只向 Foundation 输出已 promote 的泛化资产，不直接成为 Foundation 数据源。
   - 它不属于 Meta，不属于默认 RAG，不属于 runtime_state。

2. **限制资源投入**
   - P0 是实验支线，不能抢 P2-7C 主线。
   - 第一轮只允许做 scan / split / manifest / validator / report。
   - D1-D12、文风、sidecar RAG、promote 都不得进入第一轮。

3. **补关键词来源**
   - Phase 2 evidence 关键词不得硬编码。
   - 关键词来源只能是显式 config、用户输入、或已审核的 pattern seed。
   - 每次 evidence run 必须记录 keyword source。

4. **调整 schema 落点**
   - `reference_pattern_candidate.yaml` 先放 `.ops/book_analysis/schema/`。
   - 稳定前不进入 `foundation/schema/`。
   - 只有 promote 流程和 validator 稳定后，才讨论新增 Foundation schema。

5. **补污染检查规则**
   - Phase 0 必须新增 `contamination_check_rules.md` 草案。
   - 至少覆盖：
     - source hash / excerpt hash。
     - 专有名词黑名单。
     - 原人物名 / 势力名 / 地名 / 能力名禁止进入 candidate 主体。
     - 长摘录禁止进入 promoted asset。
     - 相似度阈值和人工审核清单。
     - `trope_core` 必须是机制描述，不得保留原作具体事件链。
     - `variation_axes` 必须至少给出 2 种替换方向，证明它不是改名搬运。

6. **收紧 Evidence 存储**
   - 默认 evidence 只保存 hash、短摘要、章节定位和用途。
   - 不长期保存原文摘录路径。
   - 如需临时原文 cache，只能放 `.ops/book_analysis/<run_id>/.private_evidence/`，并在 promote 前清理或验证不被引用。

7. **补 Promote 闭环**
   - `promote.py` 不能只检查 candidate 字段。
   - 必须先跑 `validate_reference_patterns.py`。
   - promote 后必须跑对应 Foundation validator。
   - 若新增 `foundation/assets/reference_patterns/`，必须先定义资产类型、命名空间、加载协议和 RAG 默认排除规则。

8. **Sidecar RAG 延后**
   - Phase 6 不应和 P0/P1 并行推进。
   - sidecar RAG 必须等 promote flow 稳定后再设计。
   - 配置先放 `.ops/book_analysis/<run_id>/reference_sidecar_recall.yaml`，不放默认 `foundation/rag/recall_config.yaml`。
   - 实现前必须明确是复用现有 RAG 的显式配置模式，还是独立索引，不允许半接入污染默认召回。

9. **补具体测试命令**
   - Phase 1 实现后至少运行：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_book_analysis_corpus
python3 scripts/validate_reference_corpus.py .ops/book_analysis/<run_id>
python3 scripts/verify_all.py
```

10. **补大文本和依赖风险**
    - Phase 1 要记录输入文件大小、章节数、处理耗时。
    - Phase 4 文风指纹必须支持缺少 `jieba` / `numpy` 的降级路径。
    - 大文本分析需要采样上限、超时或进度输出。

修订后优先级结论：

- **现在可以做 Phase 0 文档补强。**
- **可以谨慎做 Phase 1 P0 MVP。**
- **暂不做 D1-D12 自动化、文风指纹、Promote、Sidecar RAG。**
