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
- P2-5 agent harness 补强已完成：`scripts/run_agent_harness.py` 离线覆盖 `ginga init`、单章 `run`、`--chapters` 多章、`--immersive` 与错误退出路径；使用 mock LLM + 临时 `state_root`，产出 `.ops/validation/agent_harness.json` 和 `.ops/reports/agent_harness_report.md`。
- P2-5A/P2-5B 已完成：章节正文通过 `StateIO.write_artifact()` 明确为 `chapter_text` artifact 并落 audit；架构验证增加 StateIO 写入边界检查；CLI/harness/report 明确区分 `mock_harness`、RAG 的 `deterministic_eval` 与 `real_llm_demo`，mock 结果不得声明生产链路完成。

## 下一步

当前主线从「agent harness 补强」转入「用 harness 守住后续真实 workflow / skill adapter 收敛」。RAG 指标已超过阶段目标，不宜继续把主线押在 metadata 小修上；后续改 CLI / workflow / skill adapter / `StateIO` / 章节产物时，先跑离线 harness 证明边界不退化。

优先任务：

- **下一轮 Platform 收敛**：逐步把单章 `demo_pipeline` 的简化 wire-up 向 workflow DSL + skill adapters + `StateIO` 统一编排收拢，每次改动必须跑 `scripts/run_agent_harness.py`。
- **RAG 残余观察**：保留 `.ops/reports/rag_recall_quality_report.md` 的 `candidate_k` / `asset_type` blocker 作为后续小修观察项；守住 Layer 2 `recall@5 >= 0.500` 与 `expected_recall@5 >= 0.875`。

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
python3 scripts/run_agent_harness.py
python3 scripts/check_dedup_evidence.py --strict
python3 scripts/run_s3_pressure_tests.py
python3 scripts/evaluate_rag_recall.py
```

## 最近主线程结果

- Unit tests：新增 agent harness / StateIO artifact 边界覆盖；完整数量以最新 `verify_all.py` 输出为准。
- Architecture contracts：PASS，含 StateIO 写入边界检查（runtime_state YAML 写入限制在 StateIO / locked patch flow）。
- Agent harness：mock_harness PASS，覆盖 init / single run / multi_chapter / immersive / missing_state_error；报告 `.ops/reports/agent_harness_report.md`。
- Prompt frontmatter：461 cards，violations=0。
- Prompt quality：weak_examples=0。
- Methodology assets：12 methodology OK。
- RAG recall eval：473 cards / 473 vectors，native sqlite-vec used，fallback=none；Layer 1/2 空召回均为 0；Layer 2 `expected_recall@5=0.917` / `recall@5=0.614`。
- 当前代码观察：`StateIO` 是 YAML state 域的唯一写入口；单章、多章、immersive CLI 的 `chapter_NN.md` 通过 `StateIO.write_artifact()` 标注为 `chapter_text` artifact，不再伪装成 YAML state 域。
