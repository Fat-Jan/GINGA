# Ginga 当前状态

更新时间：2026-05-16

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

新增的 oh-story / Genm 参考路线、拆书融梗 Evidence Pipeline、BookView / explorer、review / deslop、market sidecar、model topology observation 都属于后续能力索引，不改变当前生产完成度。它们只能作为显式 sidecar、projection、report 或 planned workflow 推进，不能替代 `StateIO` 真值、不能默认进入 RAG、不能抢 P2-7C 主线。

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
| v1.3-3 Trope Recipe Candidate | `done` | `ginga_platform/book_analysis/trope_recipes.py`；`scripts/build_trope_recipes.py`；`scripts/validate_trope_recipes.py`；`test_book_analysis_corpus`；`.ops/book_analysis/v1-3-3-smoke-main/validation_report.json`；`python3 scripts/verify_all.py` | 已完成去来源污染的 `trope_recipe_candidate` sidecar、quality gates 与 validator；仍不自动 promote，不进默认 RAG / prompt / `raw_ideas` / Foundation assets/schema / `StateIO` |
| v1.3-4 Promote Flow | `done` | `ginga_platform/book_analysis/promote.py`；`scripts/promote_trope_recipes.py`；`scripts/validate_promoted_trope_assets.py`；`test_book_analysis_corpus.TropeRecipePromoteFlowV134ContractTest`；`python3 scripts/verify_all.py --quick` | 已完成人工审核 + 污染检查通过后才允许 promote 到白名单 Foundation methodology 资产；仍不进默认 RAG、prompt、`raw_ideas` 或 `StateIO` |
| v1.3-5 Reference Sidecar RAG | `done` | `rag/reference_sidecar.py`；`scripts/build_reference_sidecar_index.py`；`ReferenceSidecarRagTest`；`python3 scripts/verify_all.py --quick` | 已新增显式 opt-in 的 sidecar index / recall 入口；只索引 `foundation/assets/methodology/promoted-*.md` 中 approved + contamination pass + `default_rag_eligible=false` 的 methodology 资产；默认 RAG 仍按 `source_path=.ops/book_analysis/**` 排除 |
| v1.4 BookView / explorer | `done` | `ginga_platform/orchestrator/book_view.py`；`ginga inspect` / `ginga query`；`test_book_view`；`validate_architecture_contracts.py` | 已完成从 `StateIO` / chapter artifacts 派生只读 projection，输出限定 `.ops/book_views/<book_id>/<run_id>/`；不写 `runtime_state`，不建立第二状态真值，不默认读 `.ops/book_analysis/**` |
| v1.5 review / deslop | `done` | `ginga_platform/orchestrator/review.py`；`ginga review`；`test_review_deslop`；`validate_architecture_contracts.py` | 已完成审稿、去 AI 味、平台 rubric 的 warn-only report sidecar；不自动改正文，rubric 不进创作 prompt，默认不读 `.ops/book_analysis/**` |
| v1.6 market sidecar / v2 运营线 | `done` | `ginga_platform/orchestrator/market_research.py`；`ginga market --fixture --authorize`；`test_market_research_sidecar`；`validate_architecture_contracts.py` | 已完成显式授权 + offline fixture 的市场报告 sidecar；报告带数据来源、采集时间、数据质量状态，剥离外部原文，默认不进 RAG |
| v1.7-0 Longform Production Policy | `done` | `scripts/run_longform_llm_smoke.py`；`ginga_platform/orchestrator/cli/longform_policy.py`；`.ops/validation/longform_jiujiu_smoke.json`；`.ops/reports/v1_7_longform_production_policy.md`；`.ops/reports/longform_jiujiu_30_quality_summary.md`；`.ops/jury/longform_jiujiu_30_review_2026-05-15/`；`test_longform_llm_smoke` / `test_agent_harness` | 已用 `久久` 完成 30 章真实长篇 smoke 与 jury 评审；原始证据显示 10 连发开始 drift；当前正式批量口径已由 v1.7-3 收紧 |
| v1.7-1 Longform Quality Gate | `done` | `ginga_platform/orchestrator/review.py`；`test_longform_quality_gate`；`test_review_deslop`；`validate_architecture_contracts.py`；`.ops/reviews/longform-jiujiu-combo-smoke/v1-7-1-longform-gate/review_report.json` | 已把批后状态快照、回环检测、低频题材锚点检测、短章/伏笔/禁词检测与异常章 reviewer 队列接入 `ginga review` sidecar；v1.7-3 已让 review 与生成前 hard gate 共享检测口径 |
| v1.7-2 Longform Reviewer Queue Review | `done` | `.ops/jury/longform_reviewer_queue_2026-05-15/reviewer_queue_packet.md`；`.ops/jury/longform_reviewer_queue_2026-05-15/ioll-grok__reviewer_queue_packet.md`；`.ops/jury/longform_reviewer_queue_2026-05-15/human_review_brief.md`；`ask-llm list jiujiu-jury`；`ask-jury-safe --help` | 已按“先外部、再人工”把 21 个异常章交给外部模型评审并生成人工终审 brief；`jiujiu-jury` 已注册为久久评审 alias，但多章包连续 504，本轮不作为有效 jury 结论；`wzw` 输出为空，未纳入共识 |
| v1.7-3 Longform Hard Gate | `done` | `ginga_platform/orchestrator/cli/longform_policy.py`；`ginga_platform/orchestrator/cli/__main__.py`；`ginga_platform/orchestrator/review.py`；`scripts/run_longform_llm_smoke.py`；`test_agent_harness` / `test_longform_quality_gate` / `test_longform_llm_smoke`；`.ops/reports/v1_7_longform_production_policy.md` | 已采纳人工裁决：正式真实 LLM 批量推荐 4 章、上限 5 章，6 章及以上只作压力测试；CLI 在真实 LLM 调用前 hard gate 阻断连续回环、低频锚点缺失或伏笔标记缺失，mock harness 不受影响；仍不自动改正文 |
| v1.8-0 Model Topology Observation | `done` | `ginga_platform/orchestrator/model_topology.py`；`ginga model-topology observe`；`test_model_topology_observation`；`validate_architecture_contracts.py`；`.ops/model_topology/v1-8-0-smoke-main/model_topology_report.json` | 已新增只读 role/stage/provider 观察矩阵与可选 `--probe-live` 探针；默认 live probe 关闭，报告只写 `.ops/model_topology/<run_id>/`，不接管 runtime provider、不写 `StateIO`、不改变 workflow |
| v1.8-1 Candidate Truth Gate Wording | `done` | `.ops/governance/candidate_truth_gate.md`；`test_architecture_contracts`；`validate_architecture_contracts.py` | 已统一 `candidate-only` / `report-only` / `truth` 术语和晋升规则；这是治理文档与架构检查，不新增通用 accept/refill 写入链，不改变 `StateIO` |
| v1.8-2 Review Style Fingerprint | `done` | `ginga_platform/orchestrator/review.py`；`test_review_deslop`；`validate_architecture_contracts.py` | 已把 style fingerprint 接入 `ginga review` report-only sidecar，输出句长、段落、对话占比、锚点命中和风格模式命中；不自动改正文、不写 `StateIO`、不进入创作 prompt、不作为 hard fail |

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
- 新增规划路线已完成定位梳理：oh-story 参考路线、拆书融梗 / `ReferenceTropeDistillation`、BookView / explorer、review / deslop、market sidecar 已有规划与 jury 查漏补缺；其中 v1.3-0 污染隔离底座、v1.3-1 Reference Corpus P0 MVP、v1.3-2 Chapter Atom + Quality Gates、v1.3-3 Trope Recipe Candidate、v1.3-4 Promote Flow、v1.3-5 Reference Sidecar RAG、v1.4 BookView / explorer、v1.5 Review / deslop 与 v1.6 Market Research Sidecar 已完成。
- v1.3-3 Trope Recipe Candidate 已完成：新增 `trope_recipes.py`、build / validate 脚本、validator 与固定 smoke run `.ops/book_analysis/v1-3-3-smoke-main`；候选只由结构性 chapter atoms 派生，包含 `trope_core`、`reader_payoff`、`trigger_conditions`、`variation_axes`、`forbidden_copy_elements` 与 safety / promotion 边界，状态保持 `not_promoted`。
- 架构缝隙修复已完成：`step_dispatch` 缺 capability / skill / router 默认 fail-loud，仅 `execution_mode=dev/noop_allowed` 保留旧 noop；`planning-with-files` adapter 输出可经 `op_translator` 转为 `StateIO` updates / audit intents；`rag/index_builder.py` 已按 `recall_forbidden_paths` 过滤文件路径和 `source_path`，避免 `.ops/book_analysis/**` 误入默认索引。
- v1.3-4 Promote Flow 已完成最小可验证实现：`promote_trope_recipes()` 只接受 `human_review_status=approved` 且 `source_contamination_check=pass` 的 candidate，并只写入 `foundation/assets/methodology/promoted-*.md`；`validate_promoted_trope_assets()` 校验白名单落点、审批字段、污染检查字段和默认 RAG 禁入标记。
- v1.3-5 Reference Sidecar RAG 已完成最小可验证实现：`build_reference_sidecar_index()` 只从白名单 Foundation methodology promoted 资产构建独立 sqlite index，`recall_reference_sidecar()` 作为显式 opt-in 召回入口；默认 `build_index()` 仍过滤 `source_path=.ops/book_analysis/**`，默认 RAG / `evaluate_rag_recall.py` 不读污染域。
- v1.4 BookView / explorer 已完成最小可验证实现：`export_book_view()` 从 `StateIO` 与 `chapter_*.md` 生成 `.ops/book_views/<book_id>/<run_id>/book_view.json`、`README.md` 与章节副本；`query_book_view()` / `ginga query` 只读洁净 state 与章节 artifact，不读 `.ops/book_analysis/**`，且架构契约禁止 BookView 调用 `StateIO.apply()` / `audit()` / `write_artifact()`。
- v1.5 Review / deslop 已完成最小可验证实现：`export_review_report()` 从 `StateIO` 与 `chapter_*.md` 生成 `.ops/reviews/<book_id>/<run_id>/review_report.json` 与 `README.md`；报告覆盖 anti-AI style、平台风格风险和可读性提示，固定 `mode=warn_only` / `auto_edit=false`，不写 `runtime_state`，不调用 LLM，不读取 `.ops/book_analysis/**`。
- v1.6 Market Research Sidecar 已完成最小可验证实现：`export_market_research_report()` 只在显式 `authorized=True` / `ginga market --authorize` 后读取 offline fixture，生成 `.ops/market_research/<book_id>/<run_id>/market_report.json` 与 `README.md`；报告保留 source_id / platform / url / collected_at / data_quality，剥离 `raw_text`，标记 `default_rag_eligible=false`，不写 `runtime_state`。
- v1.7-0 Longform Production Policy 已完成：`久久` 30 章真实 smoke 覆盖 3 / 5 / 7 / 10 / 5 批次，生成耗时约 48 分 40 秒；首个 drift 出现在 10 连发第 19 章，并在第 24 / 25 章暴露伏笔缺失和禁词命中；原始 jury 共识为 recommended_batch_size=5、upper_bound=7，后续 v1.7-3 已按人工裁决收紧。
- v1.7-1 Longform Quality Gate 已完成：`build_review_report()` 现在输出 `longform_quality_gate`，包含每 4 章 `batch_state_snapshots`、`quality_snapshot`、回环风险、低频题材锚点缺失、短章、伏笔标记缺失、禁词命中、`reviewer_queue` 与 `hard_gate`；已对 v1.7-0 真实 30 章样本生成 `.ops/reviews/longform-jiujiu-combo-smoke/v1-7-1-longform-gate/review_report.json`。
- v1.7-2 Longform Reviewer Queue Review 已完成：`.ops/jury/longform_reviewer_queue_2026-05-15/` 保留完整 queue 评审包、外部模型意见和人工终审 brief。有效外部意见确认多章开头回到“痛觉 / 睁眼 / 灰白视野 / 天堑边缘 / 体内微粒 / 短刃”模板，P0/P1 聚焦第 19、24、25 章；`jiujiu-jury` 已接入 ask-llm 但对 132KB / 22KB / 5.5KB 包均 504，保留为短输入手动 juror，不进入默认 jury 主力。
- v1.7-3 Longform Hard Gate 已完成：正式真实 LLM 批量生成推荐 4 章、上限 5 章，6 章及以上只作压力测试；`ginga run` 在真实 LLM 调用前检查最近窗口，若连续 2 章命中 `opening_loop_risk`、任一章缺低频题材锚点、或任一章缺伏笔标记，则 fail-loud 阻断下一批真实生成；`ginga review` 的 `longform_quality_gate.hard_gate` 使用同一套检测函数。
- v1.8-0 Model Topology Observation 已完成：`ginga model-topology observe` 生成 `.ops/model_topology/<run_id>/model_topology_report.json` 与 `README.md`，记录 showrunner / prose_writer / state_settler / style_reviewer / longform_critic 的 role matrix、capability surface 与 probe summary；默认 `probe_live=false`，只有显式 `--probe-live` 才调用 `ask-llm` 最小探针；架构契约已禁止 runtime takeover、StateIO 写入和 workflow 接管。
- v1.8-1 Candidate Truth Gate Wording 已完成：`.ops/governance/candidate_truth_gate.md` 将 `candidate-only`、`report-only`、`truth` 分成三类，并规定 `operator_accept`、`schema_validation`、`source_contamination_check`、`StateIO_or_validator_entrypoint`、`audit_evidence` 作为 candidate 晋升 truth 的必要条件；架构契约会检查这些固定术语，防止后续报告或候选产物绕过默认 RAG / prompt / StateIO 边界。
- v1.8-2 Review Style Fingerprint 已完成：`build_review_report()` 现在输出 `style_fingerprint`，包含 `scope=report_only`、`auto_edit=false`、`writes_runtime_state=false`、`enters_creation_prompt=false` 以及章节数、中文字符数、平均句长、句长桶、段落数、对话行占比、style anchor 命中和 anti-AI / 平台风格模式命中；该指标只给人工审稿和后续 jury evidence pack 使用，不改变 `passed` / hard gate 语义。

## 下一步

当前 P2-7 Platform runner 收敛已完成到 provider 质量与真实 demo 边界报告层，P2-7C 严格状态为 `done`。v1.3 Reference Sidecar 链路、v1.4 BookView / explorer、v1.5 Review / deslop、v1.6 Market Research Sidecar、v1.7 Longform Production Policy / Quality Gate / Reviewer Queue / Hard Gate 与 v1.8-0/v1.8-1/v1.8-2 Genm 机制吸收已收口。后续改 CLI / workflow / skill adapter / `StateIO` / 章节产物时，先跑离线 harness 证明边界不退化。

优先任务：

- **RAG 残余观察**：2026-05-16 已刷新 `.ops/reports/rag_recall_quality_report.md` 与 `.ops/validation/rag_recall_quality.json`；473 cards / 473 vectors，native sqlite-vec used，fallback=none，Layer 1/2 空召回均为 0，Layer 2 `expected_recall@5=0.917` / `recall@5=0.614`。保留 `candidate_k` / `asset_type` blocker 作为观察项；只有指标回退或新 gold query 暴露问题时再修。
- **真实长篇生产化后续**：v1.7-3 已完成批量收紧与生成前 hard gate；下一步若继续长篇验证，应基于新口径跑小规模真实 LLM 回归，优先验证 4 章默认批次与 5 章上限下的 drift 延迟效果；仍不得自动改正文。
- **Model topology 后续**：v1.8-0 只做 observation，不接管 runtime；若后续要做 provider router，必须先补 live probe 证据、失败降级策略、same-chapter-single-writer 边界和 agent harness 回归。
- **Candidate Truth Gate 后续**：v1.8-1 只统一术语；若后续要做通用候选接受链，必须先选一个现有 candidate surface 做窄切片，不得一次性重写 `StateIO` 或 promote flow。
- **Style Fingerprint 后续**：v1.8-2 只在 `ginga review` 输出 report-only 指标；若后续要把它接入 jury evidence pack 或 stage runner 观测，仍必须保持候选证据身份，不得进入创作 prompt、默认 RAG 或自动改文链。

## 规划索引（不代表已完成）

- **oh-story 参考路线**：详见 `.ops/reports/oh_story_inspiration_roadmap.md` 与 `ROADMAP.md` §九；当前判定是分层吸收而非原样复制。
- **可吸收机制**：hooks 的生命周期信号、references 的操作手册化组织方式、书目目录的人类可读视图、Genm 的 model topology / registry-as-reference / report-only 机制，分别落到显式 context/gap report、Foundation asset 组织范式、BookView/import-export projection、`.ops/model_topology` 观察报告、review style fingerprint 与后续 planned 能力。
- **关键红线**：`STATUS.md` 仍只作为当前状态真值；oh-story 参考路线是 planned，不计入已完成能力；`.ops/book_analysis/`、外部榜单原文、市场采集原始数据默认不得进入 RAG 或 explorer/review 输入白名单；默认 `recall_config.yaml` 只维护污染源排除清单，不得把污染源加入 `recall_sources`。

## 架构边界

- 四层：Meta / Foundation / Platform / RAG。
- `StateIO` 是 `runtime_state` 唯一写入口。
- `foundation/raw_ideas/` 是灵感逃逸通道，不进入 state/RAG。
- guard/checker 内容与审计结果不注入 prompt。
- 拆书融梗支线不得写 `runtime_state`，不得进入默认 RAG，不得用 `raw_ideas` 暂存拆书结果；只允许从参考作品中蒸馏去来源污染的 `trope_recipe` 候选。
- model topology observation 只写 `.ops/model_topology/<run_id>/` 报告；默认不 live probe，不接管 runtime provider，不写 `StateIO`。
- `candidate-only` 和 `report-only` 产物不得进入 default RAG、workflow prompt 或 provider input 白名单；晋升 `truth` 必须先满足 `.ops/governance/candidate_truth_gate.md` 的人工接受、schema、污染检查、写入口和审计证据要求。

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
- RAG recall eval：2026-05-16 刷新，473 cards / 473 vectors，native sqlite-vec used，fallback=none；Layer 1/2 空召回均为 0；Layer 2 `expected_recall@5=0.917` / `recall@5=0.614`；`candidate_k` / `asset_type` blocker 继续作为 observation。
- 当前代码观察：`StateIO` 是 YAML state 域的唯一写入口；单章、多章、immersive CLI 的 `chapter_NN.md` 通过 `StateIO.write_artifact()` 标注为 `chapter_text` artifact，不再伪装成 YAML state 域。
- v1.3-0 污染隔离底座：已新增 `.ops/book_analysis/contamination_check_rules.md`、`.ops/book_analysis/p0_mvp_boundary.md`、`.ops/book_analysis/schema/source_manifest.schema.yaml`，并在 `foundation/rag/recall_config.yaml` / 架构契约检查中要求 `.ops/book_analysis/**`、`.ops/market_research/**`、`.ops/external_sources/**` 默认排除。
- v1.3-1 Reference Corpus P0 MVP：已新增 `ginga_platform/book_analysis/` 纯函数核心、`scripts/build_reference_corpus.py`、`scripts/validate_reference_corpus.py`、`test_book_analysis_corpus` 和固定 smoke run `.ops/book_analysis/v1-3-1-smoke-main`；`validate_reference_corpus.py .ops/book_analysis/v1-3-1-smoke-main` 已纳入 `verify_all.py`，仍只覆盖 P0 结构扫描边界，不证明拆书分析或创作可用性。
- v1.3-2 Chapter Atom + Quality Gates：已新增 `ginga_platform/book_analysis/chapter_atoms.py`、`scripts/build_chapter_atoms.py`、`scripts/validate_chapter_atoms.py` 和固定 smoke run `.ops/book_analysis/v1-3-2-smoke-main`；`validate_chapter_atoms.py .ops/book_analysis/v1-3-2-smoke-main` 已纳入 `verify_all.py`，只证明结构性 chapter_boundary atom 与 quality gates，不证明 D1-D12 拆书分析、融梗配方或创作可用性。
- v1.3-3 Trope Recipe Candidate：已新增 `ginga_platform/book_analysis/trope_recipes.py`、`scripts/build_trope_recipes.py`、`scripts/validate_trope_recipes.py` 和固定 smoke run `.ops/book_analysis/v1-3-3-smoke-main`；`validate_trope_recipes.py .ops/book_analysis/v1-3-3-smoke-main` 已纳入 `verify_all.py`，只证明去来源污染的 candidate sidecar 与红线 validator，不证明 promote、Sidecar RAG 或创作可用性。
- v1.3-4 Promote Flow：已新增 `ginga_platform/book_analysis/promote.py`、`scripts/promote_trope_recipes.py`、`scripts/validate_promoted_trope_assets.py` 与 `TropeRecipePromoteFlowV134ContractTest`；只证明 approved + contamination pass 的候选可转为白名单 Foundation methodology 资产，不证明 Sidecar RAG 或创作链默认可用。
- v1.3-5 Reference Sidecar RAG：已新增 `rag/reference_sidecar.py`、`scripts/build_reference_sidecar_index.py` 与 `ReferenceSidecarRagTest`；只证明显式 opt-in sidecar 可召回 approved promoted methodology 资产，不证明它会自动进入创作 workflow、默认 RAG 或 prompt 注入。
