# Ginga 当前状态

更新时间：2026-05-15

本文件是当前状态真值。`ROADMAP.md` 保留为历史/规划资料，不代表最新完成度。

## 状态判定规则

任务状态只按证据落位，不按愿望或路线图标题落位：

- `done`：已有代码 / 产物 / 报告，并通过对应验证命令或固定验收产物确认。
- `in_progress`：已有部分实现或验证产物，但 DoD 仍缺关键项。
- `planned`：只有规划、调研、jury 评审或设计文档，尚未进入实现。
- `deferred`：明确延后，或依赖上游任务完成后再触发。
- `observation`：指标已达阶段门槛，但保留后续观察项，不作为当前主线。

## 项目定位

Ginga 当前不再只是把 `_原料/` 蒸馏成资产库，而是一个以 `workflow DSL + skill adapters + StateIO` 为真实运行主线的小说创作平台底座：Foundation 负责治理资产与 schema，Platform 负责 workflow / provider / skill 编排，RAG 负责洁净资产召回，Meta 负责 guard / checker 审计边界。

新增的 oh-story 参考路线、拆书融梗 Evidence Pipeline、BookView / explorer、review / deslop、market sidecar 都属于后续能力索引，不改变当前生产完成度。它们只能作为显式 sidecar、projection、report 或 planned workflow 推进，不能替代 `StateIO` 真值、不能默认进入 RAG、不能抢 P2-7C 主线。

## 任务状态总表

| 任务线 | 严格状态 | 证据 | 边界 / 下一步 |
|---|---|---|---|
| S1-S3 基础底座 | `done` | `python3 scripts/verify_all.py`；`ROADMAP.md` §一-§三；`notepad.md` 阶段表 | 作为历史完成线维护，不再作为当前主线 |
| S4 / P2 RAG 质量线 | `done` | `.ops/reports/rag_recall_quality_report.md`；`.ops/validation/rag_recall_quality.json`；Layer 2 `recall@5=0.614` / `expected_recall@5=0.917` | RAG 残余仅留 observation |
| P2-5 agent harness | `done` | `scripts/run_agent_harness.py`；`.ops/validation/agent_harness.json`；`.ops/reports/agent_harness_report.md` | 作为后续 CLI / workflow / StateIO 改动回归门 |
| P2-7A runner 切片 | `done` | 架构契约检查；单章 mock run 的 `G_chapter_draft` 经 `skill-router` + adapter + `StateIO` 审计 | 已并入 P2-7B 完成口径 |
| P2-7B asset-backed provider 收敛 | `done` | `.ops/reports/p2_7b_runner_convergence_notes.md`；`test_asset_capability_providers*`；`CapabilityRegistry.from_defaults()` 12 providers | mock harness 仍不证明真实生产质量 |
| P2-7C provider 质量与真实 demo | `done` | `scripts/run_real_llm_smoke.py`；`.ops/validation/real_llm_demo_smoke.json`；`.ops/reports/real_llm_demo_report.md`；`test_real_llm_demo_smoke`；`test_asset_capability_providers` | 已完成 provider 可读性、真实 demo `context_snapshot` / `gap_report` / residual risk 收口；仍不声明长篇生产质量 |
| RAG 残余 `candidate_k` / `asset_type` | `observation` | `.ops/reports/rag_recall_quality_report.md` | 不抢 P2-7C 主线 |
| v1.3-0 拆书融梗污染隔离底座 | `done` | `.ops/book_analysis/contamination_check_rules.md`；`.ops/book_analysis/p0_mvp_boundary.md`；`.ops/book_analysis/schema/source_manifest.schema.yaml`；`foundation/rag/recall_config.yaml`；架构契约检查 | 已补污染规则、P0 边界、manifest schema、RAG 排除、资源上限、关键词来源与 validator DoD；实现能力另见 v1.3-1 |
| v1.3-1 Reference Corpus P0 MVP | `done` | `ginga_platform/book_analysis/`；`scripts/build_reference_corpus.py`；`scripts/validate_reference_corpus.py`；`test_book_analysis_corpus`；`.ops/book_analysis/v1-3-1-smoke-main/validation_report.json`；`python3 scripts/verify_all.py` | 已完成纯函数化 scan / split / manifest / validator / report；输出限定 `.ops/book_analysis/<run_id>/`；仍不做内容分析、D1-D12、Promote 或 Sidecar RAG |
| v1.3-2 Chapter Atom + Quality Gates | `done` | `ginga_platform/book_analysis/chapter_atoms.py`；`scripts/build_chapter_atoms.py`；`scripts/validate_chapter_atoms.py`；`test_book_analysis_corpus`；`.ops/book_analysis/v1-3-2-smoke-main/validation_report.json`；`python3 scripts/verify_all.py` | 已完成结构性 `chapter_boundary` atom、quality gates 与 validator；仍不保存标题/原文摘录，不做 D1-D12、trope recipe、Promote 或 Sidecar RAG |
| v1.4 BookView / explorer | `deferred` | `.ops/reports/oh_story_inspiration_roadmap.md` | 尚无 `.ops/book_views/` 或 inspect/query 实现；依赖 v1.3-1 P0 corpus 稳定 |
| v1.5 review / deslop | `deferred` | `.ops/reports/oh_story_inspiration_roadmap.md` | 只可作为 report sidecar，rubric 不进创作 prompt |
| v1.6 market sidecar / v2 运营线 | `deferred` | `ROADMAP.md` §九 | 外部依赖重，需显式授权和 offline fixture |

## 已完成

- S1 已完成：Foundation 最小子集、Meta guard/checker、Platform workflow、双 skill 集成、首章端到端路径已落地。
- S2 已完成：多章连载、完整 `runtime_state`、RAG Layer 1、461 prompt cards 标注、immersive mode 已收口。
- S3 已完成：RAG Layer 2 native `sqlite-vec`、Layer 3 rerank、prompt audit、methodology assets、dedup evidence、弱示例修复、压力测试已收口。
- S4 / Phase 2 native `sqlite-vec` + RAG 真实召回质量评估已完成。
- P2 已完成：Layer 1 空召回 metadata/diagnostics、评估查询 `expected_ids` / `relevant_ids`、candidate pool 与可回归 JSON/Markdown 报告已收口。
- RAG 质量小迭代已完成：补充高影响 topic/stage/card_intent 扩展与候选排序先验，Layer 2 `recall@5` 提升到 0.614，`expected_recall@5` 提升到 0.917。
- P2-5 agent harness 补强已完成：`scripts/run_agent_harness.py` 离线覆盖 `ginga init`、单章 `run`、`--chapters` 多章、`--immersive` 与错误退出路径；使用 mock LLM + 临时 `state_root`，产出 `.ops/validation/agent_harness.json` 和 `.ops/reports/agent_harness_report.md`。
- P2-5A/P2-5B 已完成：章节正文通过 `StateIO.write_artifact()` 明确为 `chapter_text` artifact 并落 audit；架构验证增加 StateIO 写入边界检查；CLI/harness/report 明确区分 `mock_harness`、RAG 的 `deterministic_eval` 与 `real_llm_demo`，mock 结果不得声明生产链路完成。
- P2-7A Platform runner 收敛切片已完成：`novel_pipeline_mvp.yaml` 的 G 步可由 DSL 解析为 capability asset hint + `skill-router`，默认 `SkillRouter()` 可读取仓库 `ginga_platform/skills/registry.yaml`；单章 `ginga run --mock-llm` 进入 `step_dispatch:G_chapter_draft`，经 `dark-fantasy` adapter 写 `workspace.chapter_text`，并继续跑 H/R1/R2/R3/V1 的 workflow step 审计。
- P2-7B Platform runner 收敛已完成：A-F/H/R1/R2/R3/V1 的默认 capability 已由固定 stub 收敛为 asset-backed deterministic provider；`CapabilityRegistry.from_defaults()` 注册 12 个 provider，输出 `provider=asset-backed` / `asset_ref`，并继续由 `step_dispatch` + `StateIO` 白名单写入 state；R2 provider 的结构化 `audit_intents` 已通过 `StateIO.audit()` 落审计，G 步仍优先经 `skill-router` + dark-fantasy adapter 写 `workspace.chapter_text`。
- P2-7C provider 质量与真实 demo 收口已完成：`scripts/run_real_llm_smoke.py` 支持 dry-run、显式 `--run` 与 `--refresh-existing`；`.ops/validation/real_llm_demo_smoke.json` 记录 `passed=true`、`dry_run=false`、`refreshed_existing=true`、`execution_mode=real_llm_demo`、endpoint、`context_snapshot`、`gap_report` 与 residual risk；H/R/V provider 输出已补可读报告字段，且仍不绕过 `StateIO` 或把报告写入 runtime_state YAML。
- 新增规划路线已完成定位梳理：oh-story 参考路线、拆书融梗 / `ReferenceTropeDistillation`、BookView / explorer、review / deslop、market sidecar 已有规划与 jury 查漏补缺；其中 v1.3-0 污染隔离底座、v1.3-1 Reference Corpus P0 MVP 与 v1.3-2 Chapter Atom + Quality Gates 已完成，后续 recipe / promote / sidecar RAG 能力仍按 `planned` / `deferred` 处理。

## 下一步

当前 P2-7 Platform runner 收敛已完成到 provider 质量与真实 demo 边界报告层，P2-7C 严格状态为 `done`。P2-5 harness 已成为回归门；RAG 指标已超过阶段目标，不宜继续把主线押在 metadata 小修上。后续改 CLI / workflow / skill adapter / `StateIO` / 章节产物时，先跑离线 harness 证明边界不退化。

优先任务：

- **v1.3-3 Trope Recipe Candidate（planned）**：v1.3-2 只证明结构性 chapter atom 可检查、可拒绝、可报告；下一步若继续拆书融梗，只能在污染源 sidecar 内推进去来源污染的 `trope_recipe` 候选与人工审核前置，不得进入默认 RAG、prompt、`raw_ideas`、Foundation assets/schema 或覆盖 `StateIO` 真值。
- **RAG 残余观察**：保留 `.ops/reports/rag_recall_quality_report.md` 的 `candidate_k` / `asset_type` blocker 作为后续小修观察项；守住 Layer 2 `recall@5 >= 0.500` 与 `expected_recall@5 >= 0.875`。

## 规划索引（不代表已完成）

- **oh-story 参考路线**：详见 `.ops/reports/oh_story_inspiration_roadmap.md` 与 `ROADMAP.md` §九；当前判定是分层吸收而非原样复制。
- **可吸收机制**：hooks 的生命周期信号、references 的操作手册化组织方式、书目目录的人类可读视图，分别落到显式 context/gap report、Foundation asset 组织范式、BookView/import-export projection。
- **关键红线**：`STATUS.md` 仍只作为当前状态真值；oh-story 参考路线是 planned，不计入已完成能力；`.ops/book_analysis/`、外部榜单原文、市场采集原始数据默认不得进入 RAG 或 explorer/review 输入白名单；默认 `recall_config.yaml` 只维护污染源排除清单，不得把污染源加入 `recall_sources`。

## 架构边界

- 四层：Meta / Foundation / Platform / RAG。
- `StateIO` 是 `runtime_state` 唯一写入口。
- `foundation/raw_ideas/` 是灵感逃逸通道，不进入 state/RAG。
- guard/checker 内容与审计结果不注入 prompt。
- 拆书融梗支线不得写 `runtime_state`，不得进入默认 RAG，不得用 `raw_ideas` 暂存拆书结果；只允许从参考作品中蒸馏去来源污染的 `trope_recipe` 候选。

## 主验证命令

优先统一入口：

```bash
python3 scripts/verify_all.py
```

当前分项验证：

```bash
python -m unittest discover -s ginga_platform -p "test_*.py"
python3 scripts/validate_architecture_contracts.py
python3 scripts/validate_prompt_frontmatter.py --strict
python3 scripts/report_prompt_quality.py foundation/assets/prompts
python3 scripts/validate_methodology_assets.py foundation/assets/methodology foundation/schema/methodology.yaml
python3 scripts/run_agent_harness.py
python3 scripts/check_dedup_evidence.py --strict
python3 scripts/run_s3_pressure_tests.py
python3 scripts/evaluate_rag_recall.py
```

## 最近主线程结果

- Unit tests：新增 agent harness / StateIO artifact 边界覆盖；完整数量以最新 `verify_all.py` 输出为准。
- Architecture contracts：PASS，含 StateIO 写入边界检查（runtime_state YAML 写入限制在 StateIO / locked patch flow）。
- Agent harness：mock_harness PASS，覆盖 init / single run / multi_chapter / immersive / missing_state_error；报告 `.ops/reports/agent_harness_report.md`。
- P2-7A runner 收敛：单章 mock run 可经 workflow DSL `G_chapter_draft` + `skill-router` + `dark-fantasy` adapter 写 `workspace.chapter_text`，并留下 H/R1/R2/R3/V1 `step_dispatch` 审计。
- P2-7B runner 收敛：12 个默认 capability provider 契约测试通过；A-F/H/R1/R2/R3/V1 provider metadata 可审计，A 步读取运行参数，H/R/V 基于真实 inputs 生成 state_updates / release report；agent harness 继续覆盖 G/V1 dispatch 与 adapter 路径。
- P2-7C real LLM demo 收口：`scripts/run_real_llm_smoke.py --refresh-existing` 已基于既有真实 smoke 产物刷新 `.ops/validation/real_llm_demo_smoke.json` 与 `.ops/reports/real_llm_demo_report.md`，记录 `context_snapshot` / `gap_report` / residual risk；chapter artifact 标记 `execution_mode=real_llm_demo`，该证据只覆盖单章 smoke 边界，不证明长篇生产质量。
- Prompt frontmatter：461 cards，violations=0。
- Prompt quality：weak_examples=0。
- Methodology assets：12 methodology OK。
- RAG recall eval：473 cards / 473 vectors，native sqlite-vec used，fallback=none；Layer 1/2 空召回均为 0；Layer 2 `expected_recall@5=0.917` / `recall@5=0.614`。
- 当前代码观察：`StateIO` 是 YAML state 域的唯一写入口；单章、多章、immersive CLI 的 `chapter_NN.md` 通过 `StateIO.write_artifact()` 标注为 `chapter_text` artifact，不再伪装成 YAML state 域。
- v1.3-0 污染隔离底座：已新增 `.ops/book_analysis/contamination_check_rules.md`、`.ops/book_analysis/p0_mvp_boundary.md`、`.ops/book_analysis/schema/source_manifest.schema.yaml`，并在 `foundation/rag/recall_config.yaml` / 架构契约检查中要求 `.ops/book_analysis/**`、`.ops/market_research/**`、`.ops/external_sources/**` 默认排除。
- v1.3-1 Reference Corpus P0 MVP：已新增 `ginga_platform/book_analysis/` 纯函数核心、`scripts/build_reference_corpus.py`、`scripts/validate_reference_corpus.py`、`test_book_analysis_corpus` 和固定 smoke run `.ops/book_analysis/v1-3-1-smoke-main`；`validate_reference_corpus.py .ops/book_analysis/v1-3-1-smoke-main` 已纳入 `verify_all.py`，仍只覆盖 P0 结构扫描边界，不证明拆书分析或创作可用性。
- v1.3-2 Chapter Atom + Quality Gates：已新增 `ginga_platform/book_analysis/chapter_atoms.py`、`scripts/build_chapter_atoms.py`、`scripts/validate_chapter_atoms.py` 和固定 smoke run `.ops/book_analysis/v1-3-2-smoke-main`；`validate_chapter_atoms.py .ops/book_analysis/v1-3-2-smoke-main` 已纳入 `verify_all.py`，只证明结构性 chapter_boundary atom 与 quality gates，不证明 D1-D12 拆书分析、融梗配方或创作可用性。
