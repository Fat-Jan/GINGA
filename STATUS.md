# Ginga 当前状态

更新时间：2026-05-15

本文件是当前状态真值。`ROADMAP.md` 保留为历史/规划资料，不代表最新完成度。

## 已完成

- S1 已完成：Foundation 最小子集、Meta guard/checker、Platform workflow、双 skill 集成、首章端到端路径已落地。
- S2 已完成：多章连载、完整 `runtime_state`、RAG Layer 1、461 prompt cards 标注、immersive mode 已收口。
- S3 已完成：RAG Layer 2 native `sqlite-vec`、Layer 3 rerank、prompt audit、methodology assets、dedup evidence、弱示例修复、压力测试已收口。
- S4 / Phase 2 native `sqlite-vec` + RAG 真实召回质量评估已完成。
- P2 已完成：Layer 1 空召回 metadata/diagnostics、评估查询 `expected_ids` / `relevant_ids`、candidate pool 与可回归 JSON/Markdown 报告已收口。
- RAG 质量小迭代已完成：补充高影响 topic/stage/card_intent 扩展与候选排序先验，Layer 2 `recall@5` 提升到 0.614，`expected_recall@5` 提升到 0.917。

## 下一步

当前主线从「RAG 能力补强」转入「agent harness 补强」。RAG 上轮指标已超过阶段目标，下一步不宜继续把主线押在 metadata 小修上，而应先把真实 CLI / workflow / skill adapter / `StateIO` / 章节产物纳入可复现离线演练与边界审计。

优先任务：

- **P2-5 Agent harness hardening**：补一个不调用真实 LLM 的离线 harness，覆盖 `ginga init`、单章 `run`、`--chapters` 多章、`--immersive` 四条路径；使用 mock LLM + 临时 `state_root`，断言 state 域、audit_log、chapter artifacts 与错误路径。
- **P2-5A StateIO 写入边界审计**：把 `runtime_state` YAML 域写入统一压到 `StateIO` 或现有封装路径；章节正文 `chapter_NN.md` 作为 artifact 明确标注，避免未来把直接写 YAML 当成捷径。
- **P2-5B demo 真实性标识**：在 harness / CLI 结果中区分 mock、deterministic eval 与真实 LLM demo，继续遵守「mock 结果不能声明真实生产链路已完成」。
- **P2-6 RAG 残余小迭代**：作为 sidecar 处理 `.ops/reports/rag_recall_quality_report.md` 的残余 `candidate_k` / `asset_type` blocker，守住 Layer 2 `recall@5 >= 0.500` 与 `expected_recall@5 >= 0.875`；再决定是否允许部分 methodology 跨资产类型进入评估候选。

## 架构边界

- 四层：Meta / Foundation / Platform / RAG。
- `StateIO` 是 `runtime_state` 唯一写入口。
- `foundation/raw_ideas/` 是灵感逃逸通道，不进入 state/RAG。
- guard/checker 内容与审计结果不注入 prompt。

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
python3 scripts/check_dedup_evidence.py --strict
python3 scripts/run_s3_pressure_tests.py
python3 scripts/evaluate_rag_recall.py
```

## 最近主线程结果

- Unit tests：155 tests OK。
- Architecture contracts：PASS，warnings=0（workflow 已统一使用 `workspace.chapter_text`）。
- Prompt frontmatter：461 cards，violations=0。
- Prompt quality：weak_examples=0。
- Methodology assets：12 methodology OK。
- RAG recall eval：473 cards / 473 vectors，native sqlite-vec used，fallback=none；Layer 1/2 空召回均为 0；Layer 2 `expected_recall@5=0.917` / `recall@5=0.614`。
- 当前代码观察：`StateIO` 是 YAML state 域的唯一写入口；单章、多章、immersive CLI 仍会直接写章节正文 artifact（`chapter_NN.md`），下一步需要用 harness 明确 artifact 边界和离线演练口径。
