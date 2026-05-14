# Ginga 当前状态

更新时间：2026-05-15

本文件是当前状态真值。`ROADMAP.md` 保留为历史/规划资料，不代表最新完成度。

## 已完成

- S1 已完成：Foundation 最小子集、Meta guard/checker、Platform workflow、双 skill 集成、首章端到端路径已落地。
- S2 已完成：多章连载、完整 `runtime_state`、RAG Layer 1、461 prompt cards 标注、immersive mode 已收口。
- S3 已完成：RAG Layer 2 native `sqlite-vec`、Layer 3 rerank、prompt audit、methodology assets、dedup evidence、弱示例修复、压力测试已收口。
- S4 / Phase 2 native `sqlite-vec` + RAG 真实召回质量评估已完成。
- P2 已完成：Layer 1 空召回 metadata/diagnostics、评估查询 `expected_ids` / `relevant_ids`、candidate pool 与可回归 JSON/Markdown 报告已收口。

## 下一步

RAG 质量下一轮：基于 `.ops/reports/rag_recall_quality_report.md` 的 blocker summary，优先补 topic/card_intent/stage metadata 与少量领域同义词，把 Layer 2 `recall@5` 从 0.425 往 0.500+ 推；`expected_recall@5` 当前已达 0.875。

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

- Unit tests：154 tests OK。
- Architecture contracts：PASS，warnings=0（workflow 已统一使用 `workspace.chapter_text`）。
- Prompt frontmatter：461 cards，violations=0。
- Prompt quality：weak_examples=0。
- Methodology assets：12 methodology OK。
- RAG recall eval：473 cards / 473 vectors，native sqlite-vec used，fallback=none；Layer 1/2 空召回均为 0。
