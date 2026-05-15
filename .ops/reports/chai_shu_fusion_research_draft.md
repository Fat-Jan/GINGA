# 拆书 × Ginga 融合调研草案

日期：2026-05-15
范围：`/Users/arm/Desktop/拆书` 与 `/Users/arm/Desktop/ginga` 只读调研
状态：供 ark-jury-court 第三方评审；本草案未修改代码和运行时状态。

## 结论摘要

`拆书` 可以融合进 Ginga，但不应直接塞进当前 `novel_pipeline_mvp.yaml` 的 A-H/R/V 生成主链。更合适的定位是：**参考作品分析层**，由可选 Platform workflow 或离线 capability providers 承接，输出分析 artifact / sidecar index / 人工确认后的 Foundation 派生资产。

第一梯队可融合能力：

1. 参考作品 ingest 与章节拆分。
2. D1-D12 拆书维度结构化 schema。
3. 文风指纹统计 provider。
4. 关键词场景抽取与证据样本生成。
5. 角色 / 主题词频画像。
6. 跨作品横向对比报告。
7. 参考语料自审 / 完整性检查。
8. 对话比例、句长、虚词等 style lock 校准建议。

融合原则：

- 拆书保留为输入分析层；Ginga 继续负责 workflow、adapter、`StateIO`、资产治理和验证门。
- 原书全文、逐章原文、未经审核抽取 JSON 不进入默认 RAG，不进入 `runtime_state`，不进入 prompt。
- 可复用技法必须先泛化为 methodology / reference pattern / prompt example，再人工确认后 promote。

## 当前事实

### 拆书目录

`拆书` 是一个本地网文拆书模板工具包，不是成熟运行中的分析库。

- 文件总数：19。
- `reports/` 当前只有 3 个 JSON：`data_sample.json`、`scene_extracts.json`、`stylometric_quantitative.json`。
- `chapters/`、`chapters_renamed/`、`deconstruction/`、`reports/cross_compare/` 当前为空。
- `novel.txt` 和 `config.json` 仍是模板 / 占位级输入。
- 未发现外部 LLM/API 调用；主要依赖是 Python 标准库、`jieba`、`numpy`。
- 多数脚本硬编码 `BASE_DIR`，默认直读直写当前目录，部分脚本会覆盖同名产物。

主要能力：

| 能力 | 现有脚本 | 价值 | 当前成熟度 |
|---|---|---|---|
| 章节拆分 | `split_chapters.py` / `rename_chapters.py` | 把外部小说转为章节 corpus | 需适配 |
| 全本扫描 | `scan_all.py` | 章节、标题、字数、角色出现概览 | 可作为只读原型 |
| 词频分析 | `auto_analyze.py` | 角色别名 / 主题关键词批量统计 | 需适配 |
| 场景抽取 | `extract_scenes.py` / `extract_all_scenes.py` | 按关键词截上下文证据 | 需适配 |
| 文风量化 | `stylometric_quantitative.py` | 章节 CV、句长、对话比例、TTR、虚词、POS、ngram、粗情感 | 可作为原料，需健壮化 |
| 12 维拆解 | `deconstruction_report.py` | D1-D12 手填拆书框架 | 适合作 schema 原料 |
| 跨作品对比 | `cross_compare.py` | 多作品维度横向表 | 适合作 sidecar 报告 |
| 自审 | `self_audit.py` | 项目完整性检查 | 可迁移为可选 validator |
| 展示 / 修正 | `show_results.py` / `display_results.py` / `fix_dialogue.py` | 结果展示；对话比例重算 | 展示低 ROI，修正脚本不建议直接迁移 |

### Ginga 当前架构

Ginga 当前真值来自 `STATUS.md`：P2-7A/P2-7B 已完成，主线进入 P2-7C provider 质量与真实 demo 小范围验证。

关键边界：

- Platform runner 已收敛到 workflow DSL + capability provider / skill adapter + `StateIO`。
- `CapabilityRegistry.from_defaults()` 已注册 12 个 asset-backed deterministic provider。
- `step_dispatch` 负责 guard、RAG hook、capability/skill、state 写入白名单、checker。
- `StateIO` 是 `runtime_state` YAML 域唯一写入口；非 YAML artifact 用 `StateIO.write_artifact()`。
- RAG 禁召回 Meta、runtime_state、raw_ideas；拆书产物不能直接塞进默认召回源。
- mock harness 只证明离线编排与边界，不证明生产质量。

## 融合候选矩阵

| 优先级 | 候选能力 | 推荐落点 | 需要适配 | 不应做 |
|---|---|---|---|---|
| P0 | 参考作品 ingest / 章节拆分 | 新可选 workflow：`book_analysis_pipeline.yaml`；或 `ginga analyze-book` CLI | 脚本改纯函数；显式输入/输出目录；dry-run；tempdir 测试 | 不写目标作品 `runtime_state` |
| P0 | D1-D12 schema | `foundation/schema/reference_pattern.yaml` 或先放 `.ops/book_analysis/schema` | 定义维度字段、证据引用、人工确认状态 | 不把手填报告直接当资产 |
| P0 | 文风指纹 provider | `ginga_platform/orchestrator/registry/book_analysis_providers.py` | 返回 JSON + audit intent；处理空 corpus；中文引号；依赖检查 | 不让 `fix_dialogue.py` 直接改 JSON |
| P1 | 场景抽取 adapter | sidecar artifact / RAG eval fixture / prompt example 候选 | 把关键词命中转为证据片段，保留来源引用 | 不把原文片段直接注入生成 prompt |
| P1 | 角色 / 主题词频画像 | analysis provider | 支持别名归一、章节趋势、空结果诊断 | 不写目标书 `CHARACTER_STATE` |
| P1 | cross-work compare | `.ops/reports` 或 sidecar report | 从 D1-D12 schema 读结构化字段，减少正则脆弱性 | 不覆盖默认工程报告 |
| P2 | reference corpus self-audit | `verify_all.py` 可选项或独立 `scripts/validate_reference_corpus.py` | 检查章节连续性、报告完整性、schema 合法性 | 不另起不可回归自检孤岛 |
| P2 | style lock 校准建议 | 初始化建议 / locked patch 候选 | 只给建议；改锁定域必须走 init 或 locked patch | 不自动改 `locked.GENRE_LOCKED` |

## 推荐架构

新增一个可选分析 workflow，而不是修改当前主生成 workflow：

```yaml
name: book_analysis_pipeline
steps:
  - BK_document_scan
  - BK_chapter_split
  - BK_style_fingerprint
  - BK_scene_extract
  - BK_pattern_report
  - BK_compare_eval
  - BK_source_safety_check
```

推荐执行边界：

- 初期用 capability provider，不急着注册第 3 个 skill。
- 若后续拆书发展为复杂、长期维护、带独立 contract 的能力，再作为第 3 个 skill adapter 接入。
- 分析 run 的报告可以用独立 `StateIO(book_id="analysis-<source>")` 写 artifact 和 audit，也可以先落 `.ops/book_analysis/<run_id>/`。
- 任何进入 Foundation 的内容都必须是“去来源污染、人工确认、可复用”的派生资产。
- RAG 先做 sidecar index，不加入默认 `foundation/rag/recall_config.yaml`。

## 风险清单

1. **版权 / 来源污染**：拆书可分析结构、节奏、技法；不能把人物、设定、桥段改名搬运到正文。
2. **StateIO 边界**：拆书脚本默认直写目录；迁入前必须改成纯函数 / 显式输出 / provider 返回值。
3. **RAG 污染**：原文和未审核片段不能进入默认召回；只允许 sidecar 或人工确认派生卡。
4. **Meta 注入风险**：自审 / checker / guard 结果只进 audit，不进 prompt。
5. **空产物误判**：当前拆书 reports 多为样例或零值，不能作为有效融合证据。
6. **统计稳健性**：文风脚本当前对空章节、中文引号、章节名异常、分词依赖缺失等情况不够健壮。
7. **覆盖风险**：原脚本会覆盖 `chapters/`、`reports/`、`deconstruction/` 同名文件。
8. **主线挤压风险**：Ginga 当前主线是 P2-7C provider 质量 / 真实 demo；拆书应作为支线能力，不应打断主链收敛。

## 分阶段方案

### Phase 0：冻结定位

- 不搬代码。
- 确认拆书定位为 reference analysis，不是 production writer。
- 记录禁止项：不进默认 RAG、不写目标 runtime_state、不注入 prompt。

### Phase 1：离线纯函数化

- 从拆书复制算法思想，不直接复制硬编码脚本。
- 产出 `book_analysis` provider 原型：scan、split、style_fingerprint、scene_extract。
- 给每项能力加 tempdir tests 和空输入测试。

### Phase 2：可选 workflow / CLI

- 新增 `book_analysis_pipeline.yaml` 或 `ginga analyze-book`。
- 输出 `.ops/book_analysis/<run_id>/analysis.json`、`analysis_report.md`、`audit.json`。
- `verify_all.py` 默认不跑真实大文本；单独 validator 可选。

### Phase 3：资产 promote

- D1-D12 schema 稳定后，把人工确认的泛化规律 promote 到 Foundation methodology / prompt example。
- 建 sidecar RAG index 和 eval，不污染默认创作 RAG。

### Phase 4：长期 skill 化

- 只有当拆书能力具备独立 contract、长期维护需求、复杂交互时，再作为第 3 个 skill 接入 registry。

## 初步决策建议

建议融合，但只融合 **约 60% 的功能价值**，不是照搬 100% 的脚本。

- 直接高价值：章节 ingest、文风指纹、场景证据、D1-D12 schema、自审。
- 中价值：角色/主题词频、跨作品对比。
- 低价值或不建议：展示脚本、`fix_dialogue.py`、当前空 reports、当前硬编码写文件模式。

最小可落地任务：

1. 做 `book_analysis` 离线 provider 原型。
2. 定义 D1-D12 `reference_pattern` schema。
3. 写 `validate_reference_corpus.py`。
4. 产出 sidecar report，不进入默认 RAG。
5. 用 mock / tempdir 验证所有输出路径和无覆盖行为。
