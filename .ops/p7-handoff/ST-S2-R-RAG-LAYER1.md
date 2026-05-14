# P7 Handoff — ST-S2-R-RAG-LAYER1

**完成时间**：2026-05-13 (Sprint 2)
**执行 P7**：P7-R
**任务**：RAG Layer 1 frontmatter 召回 + 冷启动降级 + step_dispatch rag_mode hook
**Prompt**：`.ops/p7-prompts/ST-S2-R-RAG-LAYER1.md`

## 交付清单

新建文件:
- `rag/__init__.py` (24 行) — 包入口
- `rag/index_builder.py` (261 行) — 扫 foundation/assets → sqlite 索引（R-1）
- `rag/layer1_filter.py` (267 行) — `recall()` API（R-2 + R-4）
- `rag/cold_start.py` (139 行) — `detect_state` / `cold_recall_fallback` / `load_recall_config` / `enabled_layers`（R-3）
- `ginga_platform/orchestrator/runner/tests/test_rag_layer1.py` (300 行) — 6 case 单测

修改文件:
- `ginga_platform/orchestrator/runner/step_dispatch.py` — **只追加** 1 行 hook 调用 + 1 个新 helper `_inject_rag_cards`（R-5）；4 步主流程完整保留

## 任务对账（R-1..R-5）

| 任务 | 输出 | 验证 |
|---|---|---|
| R-1 index_builder | `rag/index_builder.py:build_index` 扫 `foundation/assets/prompts/*.md` → sqlite | 冷启动空目录建空索引文件 + log（test_cold_start_empty_index_returns_empty） |
| R-2 layer1_filter.recall | `recall(stage, topic, asset_type, card_intent, top_k, quality_floor, ...)` 按 frontmatter 过滤 + quality_grade 排序 | A > A- > B+ > B 顺序（test_quality_grade_ordering_a_first）；topic list 部分匹配（test_topic_filter_partial_match） |
| R-3 cold_start | `detect_state` 按 count_cards 判 cold/warm；`cold_recall_fallback` 走 Layer 1 only；`enabled_layers` 按 recall_config.cold_start.enabled_layers=[1] | test_cold_start_empty_index_returns_empty / 默认兜底 `_builtin_defaults()` |
| R-4 stage_specific_top_k | `recall(top_k=None)` 自动读 `recall_config.yaml.stage_specific_top_k[stage]`，缺省回 `default_top_k` | test_stage_specific_top_k_from_config |
| R-5 step_dispatch hook | `_inject_rag_cards()` 检查 `ctx.workflow_flags.rag_mode`：off → audit "rag disabled by user" + inputs["retrieved.cards"]=[]；on → 调 layer1_filter.recall 注入 inputs["retrieved.cards"] | test_step_dispatch_rag_mode_off_skips_recall + test_step_dispatch_rag_mode_on_invokes_recall |

## DoD 验收命令输出

```
$ python3 -c "from rag.layer1_filter import recall; r=recall(stage='drafting', topic='玄幻黑暗', top_k=5); print(f'recall returned {len(r)} cards (cold-start OK)')"
rag.layer1_filter: index rag/index.sqlite missing (cold-start, empty result)
recall returned 0 cards (cold-start OK)

$ python3 -m unittest ginga_platform.orchestrator.runner.tests.test_rag_layer1 -v
Ran 6 tests in 0.164s
OK

$ grep -q rag_mode ginga_platform/orchestrator/runner/step_dispatch.py && echo PASS
PASS

$ python3 -m unittest discover -s ginga_platform/orchestrator/runner/tests -v
Ran 53 tests in 1.449s
OK   # 全量回归：14 旧 + 33 同期 + 6 新，全过
```

## 审查三问

**Q1 接口兼容**：通过。`dispatch_step` 公共签名未改；`_gather_inputs / _execute_body / _apply_state_writes` 未动；新加 `_inject_rag_cards` 通过 ctx 的可选键 `workflow_flags` 沟通，不破坏既有 ctx 协议。Grep 确认 `rag/` 仅由 step_dispatch.py (lazy import) + 测试调用；53 个测试全过证明零接口破坏。

**Q2 边界处理**：通过。
- index 文件缺失 / 表损坏 / 0 记录 → recall 走 warn 日志 + 返回 []（已测）
- frontmatter 缺失/坏 yaml/缺 id → build_index 跳过 + stats.skipped_*（fail-safe，default 模式）
- recall_config.yaml 缺失 → `_builtin_defaults()` 兜底
- topic None/str/list 三态 → `_coerce_topic` 统一（str + list 两种已测）
- ctx.workflow_flags 缺失 → 视作 `{}`，默认 rag_mode=on（向后兼容）
- step.raw 不是 Mapping → hint={}（防御性）
- rag 模块 import 失败 / recall 抛异常 → audit warn + retrieved.cards=[]（fail-safe，step 主流程不受 RAG 故障影响）
- quality_floor 非法 → 抛 `Layer1RecallError`（fail-loud，数据合约违规）

**Q3 Proper fix**：通过。
- 全程 stdlib：`sqlite3` / `re` / `json` / `pathlib`；唯一第三方是项目早就用的 PyYAML
- step_dispatch.py 严守"只追加"红线：4 步主流程编号 1→2→2.5→3→4 完整保留
- hook 用 lazy import 实现 RAG ↔ runner 解耦：删 rag/ runner 仍可跑（已用 ImportError 分支覆盖）
- 排序混排 ASC/DESC 用 `_NegStr` wrapper，避免两次 sort（正经技巧，非 hack）
- 没有 try-except 吞核心异常：quality_floor 非法走 fail-loud；rag 故障走 fail-safe + audit 留痕

## 红线对账

- [x] sqlite3 用 stdlib，未引第三方
- [x] step_dispatch.py 改前完整 Read（239 行已读），新增 hook 不破坏现有 dispatch_step / _gather_inputs / _execute_body / _safe_call / _apply_state_writes / audit_log 写入逻辑
- [x] hook fail-safe：RAG 故障不让 step 主流程失败
- [x] 未动 lock map 外文件
- [x] max_attempts ≤ 3：实际 1 attempt 完成
- [x] 未串供其他 P7（写范围严格在 prompt §写范围 lock map）

## 技术债 / 后续

历史说明：这些是 ST-S2-R 完成时的后续建议；S3 Layer 2/3、461 prompts 标注、native sqlite-vec 与真实召回评估后续已完成，当前下一步见 `STATUS.md`。

无新增技术债。后续建议（不在 ST-S2-R 范围）：
1. S3 接入 Layer 2 向量召回时，`cold_start.enabled_layers` 会自动切到 `[1, 2]`，本任务的 `cold_recall_fallback` 保留 Layer 1 only 兜底路径
2. workflow YAML 需在 G_chapter_draft / R1 / R2 等 step 上加 `retrieval_hint:` 字段（stage/topic/asset_type/...），dispatch hook 才能取到 hint；空 hint 时 hook 仍会调 recall 但全 wildcard（落到全表 + quality_floor 过滤）
3. `foundation/assets/prompts/` 目前为空，等 ST-S2-L (461 prompts 标注) 完成后跑 `build_index` 即可填表，无需改 layer1 代码
