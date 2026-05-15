severity | field_path | issue | suggestion
---|---|---|---
高 | 一句话方案 / 蒸馏边界 | 未明确 BookAnalysisLayer 在 Ginga 四层架构中的归属，可能导致架构边界模糊和职责冲突。 | 在“蒸馏边界”或“文件层级建议”中明确 BookAnalysisLayer 属于 Platform 层（作为 capability provider），并说明与 Foundation、RAG、Meta 的交互接口。
高 | 可蒸馏内容矩阵 / 优先级 | P0 任务包含 `reference_corpus_scan` 和 `validate_reference_corpus.py`，但未评估其与当前 P2-7C provider 质量主线的资源竞争风险。 | 在“实施批次 / Phase 0”中增加风险评估：明确本支线为实验性质，资源投入上限（如人天），并确保不影响 P2-7C 主线交付。
中 | 数据流完整性 / Phase 2: Evidence + 轻分析 | 证据片段（Evidence Snippet）的生成依赖于关键词抽取，但未定义关键词来源，可能导致分析结果主观或不一致。 | 在“Phase 2”中补充：关键词应来自可配置的清单（如基础情节要素），或作为外部输入，避免在代码中硬编码。
中 | 任务拆分 / Phase 3: D1-D12 Candidate | 计划将 `reference_pattern_candidate.yaml` 放在 `foundation/schema/`，这与“禁止写 runtime_state”原则一致，但 Foundation schema 变更需谨慎。 | 将 `reference_pattern_candidate.yaml` 的创建移至 Phase 5（Promotion Flow）之后，或先放在 `.ops/schema/` 作为实验性 schema，待稳定后再考虑迁入 Foundation。
中 | 风险控制 / 整体 | 对“版权/来源污染”仅提及检查状态（`source_contamination_check`），但未定义具体的检查方法和阈值，存在实施风险。 | 在“Phase 0：定位和防污染底座”的产出中，增加 `contamination_check_rules.md`，明确检查项（如专有名词黑名单、相似度算法阈值、人工审核清单）。
低 | 可测试性 / Phase 1 验收 | 验收条件包含 `python3 scripts/verify_all.py` 通过，但未明确 `verify_all.py` 是否已存在或需要新建，可能造成混淆。 | 将验收条件具体化为：新建 `scripts/validate_reference_corpus.py` 并通过所有单元测试；或指定运行 `pytest ginga_platform/orchestrator/runner/tests/test_book_analysis_corpus.py`。
低 | 架构边界 / Sidecar RAG | `foundation/rag/reference_sidecar_recall.yaml` 的配置若放在 Foundation 层，可能被默认 RAG 流程误读。 | 将 sidecar RAG 的配置和实现完全放在 Platform 层（如 `ginga_platform/book_analysis/sidecar_rag.py`），通过明确的 `workflow_flags` 控制，避免 Foundation 层耦合。

**总体判断**：revise
理由：计划在战略上符合 Ginga 支线定位，架构边界和数据流基本清晰，但关键风险（如污染检查具体规则、与主线资源竞争）未充分定义，需在 Phase 0 补充后才能安全推进。