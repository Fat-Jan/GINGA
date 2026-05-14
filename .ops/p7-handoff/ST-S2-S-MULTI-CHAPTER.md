# ST-S2-S-MULTI-CHAPTER handoff（P7-S 心跳与交付记录）

## START 2026-05-13T12:13:43Z | task_id=ST-S2-S-MULTI-CHAPTER

- agent: P7-S 骨干
- 预算: 90 min wall
- max_attempts: 3
- 写范围 lock map（严格遵守）:
  - 可改: ginga_platform/orchestrator/cli/demo_pipeline.py（Read 后 Edit）
  - 新建: ginga_platform/orchestrator/cli/multi_chapter.py
  - 新建: ginga_platform/orchestrator/cli/locked_patch.py
  - 新建: meta/patches/_template.patch.yaml
  - 新建: ginga_platform/orchestrator/runner/tests/test_multi_chapter.py
  - 新建: ginga_platform/orchestrator/runner/tests/test_locked_patch.py
  - 本文件 handoff
- 前置依赖: PHASE0 已 done（P0-1 capability_registry / P0-2 op_translator 已落盘，P0-3 12 step integration 已就绪）

## 子任务计划清单（S-1..S-5 顺序）

- [ ] S-1 entity_runtime 多章 wire-up：扩展 demo_pipeline.run_workflow（chapter_no 参数 + 滚动逻辑：events 追加 / foreshadow hook 检查 / particles delta / total_words / arc_summaries 每 5 章）
- [ ] S-2 locked 域 patch 流程：locked_patch.py CLI + meta/patches/_template.patch.yaml 模板 + apply_patch 跑 R3 + audit 提示
- [ ] S-3 R1/R2/R3 三件套：R1 风格润色（LLM/adapter）+ R2 一致性 checker（character-iq + cool-point-payoff）+ R3 写 foundation/runtime_state/<book>/chapter_NN.md
- [ ] S-4 V1_release_check checker：DoD 检查（每章 >=3000 bytes / FORESHADOW pool 条数 / total_words 累加）
- [ ] S-5 5 章 demo：multi_chapter.py runner + demo_pipeline --chapters flag + 5 章连跑

## 心跳节奏承诺

- 启动 <=5 min 写 START（本 entry）OK
- 每完成一个 S-N <=10 min 内追加心跳 entry，与产物同步落盘
- 越界需要时写 `## QUESTION extend lock map`，stop 等主 agent `## ACK extend`

## 探索阶段下一动作

- Read demo_pipeline.py（理解 Sprint 1 12 step 现状）
- Read runtime_state.yaml schema（理解 locked patch 流程定义）
- Read capability_registry + op_translator（PHASE0 产出 contract 摸清）
- 进入 S-1 实施

## 2026-05-13T12:23:00Z | S-1 完成 - entity_runtime 多章 wire-up

- 改:
  - ginga_platform/orchestrator/cli/demo_pipeline.py (564 行)：扩展 `run_workflow(chapter_no=)` + 抽出 `apply_chapter_rollup` helper（events / foreshadow / particles / total_words / arc_summaries 5 个滚动维度全部用 op_translator 串好）+ 新增 `_extract_foreshadow_hooks` / `_check_foreshadow_payoff` / `_extract_particle_delta` 三个 helper
  - 复用 PHASE0 op_translator.adapter_ops_to_state_updates，章节滚动走 list-of-ops → flat dict → state_io.apply，与 12 step integration 同一通路
- 新建:
  - ginga_platform/orchestrator/runner/tests/test_multi_chapter.py (302 行)
- checkpoint:
  - `python3 -m unittest ginga_platform.orchestrator.runner.tests.test_multi_chapter.ExtractForeshadowHooksTest ApplyChapterRollupTest ExtractParticleDeltaTest CheckForeshadowPayoffTest -v` → 16/16 PASS（0.155s）
- 关键点:
  - foreshadow 抽取兼容两种格式：HTML 注释 `<!-- foreshadow: id=fh-x planted_ch=N expected_payoff=M summary=... -->`（prompt 主推）+ 中文行式 `【伏笔】id=...`（fallback）
  - particles delta 用 op="delta"（op_translator 算 add 语义），未结算 = 0 不动账本
  - arc_summaries 每 5 章追一条（chapter_no % 5 == 0 触发），含 anchor_ch 字段便于后续 retrieval
  - 既有 foreshadow hook expected_payoff 到期自动切 status=tickled + tickled_at_ch 标记，留给 R2 复核
- 下一步: S-2 locked 域 patch CLI

## 2026-05-13T12:25:00Z | S-1 confirmed + S-2 进展

- 回复 coordinator §2.15 心跳节奏巡查：S-1 心跳已于 12:23:05Z 落盘（见上一 entry），现按模板要求补一条 incremental 进展
- 改 demo_pipeline.py：apply_chapter_rollup helper 抽出 + chapter_no 参数加入；564 行
- S-1 16 测试 PASS（0.155s）
- 正在 S-2 locked patch：locked_patch.py + meta/patches/_template.patch.yaml 已落盘；测试待写
- 下一步：写 test_locked_patch.py，跑 PASS 后追加 S-2 完成心跳

## 2026-05-13T23:35:00+0800 | 主 agent 续接 P7-S（断网后 reconciliation）

P7-S 子代理断网未回，主 agent 按 §1.0.1 看板真值 + §M2 白盒回放接管。

### Reconciliation 摸底
- S-1 ✅ 已 done（demo_pipeline 多章 wire-up + 16 helper test PASS，2026-05-13T12:23Z 落盘）
- S-2 ✅ 已 done（locked_patch.py + meta/patches/_template.patch.yaml + test_locked_patch.py 18/18 PASS）；本轮额外修了 1 个 mock bug（见下）
- S-3 / S-4 / S-5 主 agent 接管完成

### 本轮关键修复（A3 防陷阱）
locked_patch 原 `test_cli_applies_with_approve_flag` FAIL 不是 CLI bug，是测试踩到 Python 默认参数绑定陷阱：
- `state_io.py` 把模块级常量 `_DEFAULT_STATE_ROOT` 改成函数 `_default_state_root()`，`StateIO.__init__` 签名 `state_root=None` lazy lookup
- `test_locked_patch.py` / `test_multi_chapter.py` 的 mock 切到 `mock.patch("...state_io._default_state_root", return_value=tmp)`
- 顺手清了测试遗留脏数据 `foundation/runtime_state/cli-book/`
- 预防：模块属性 `_DEFAULT_STATE_ROOT` 不存在了，任何复用旧 mock 模式会 fail-fast AttributeError

### S-3/S-4/S-5 落盘（一次性实施）
新建 `ginga_platform/orchestrator/cli/multi_chapter.py`（266 行）：
- `_call_llm_for_polish(text, endpoint)` → R1 风格润色
- `_r2_consistency_check(sio, ch_no, polished)` → R2 跑 character-iq + cool-point-payoff，CheckerLoadError 容忍（aigc-style-detector schema 不匹配落 audit warn 不阻塞）
- `_r3_final_pack(sio, ch_no, polished, r2_results)` → R3 polished 正文 + 元数据表格 overwrite chapter_NN.md
- `_v1_release_check(sio, *, min_bytes, min_pool)` → V1 DoD（每章 ≥3000 bytes + foreshadow ≥1 + total_words > 0）
- `run_multi_chapter(book_id, chapters, ...)` → N 章 runner 主入口

CLI flag：`ginga_platform/orchestrator/cli/__main__.py` 让 `ginga run <book> --chapters N`（非 immersive）走 multi_chapter；`--chapters 1`（默认）仍走 demo_pipeline 单章 stub。

### 验证
- `python3 -m unittest ginga_platform.orchestrator.runner.tests.test_multi_chapter -v` → **18/18 PASS**（含 5 章 mock LLM e2e + DoD fail 检测）
- 全仓 `python3 -m unittest discover -s ginga_platform` → **105/105 PASS**（零回归）

### 剩余
- 真实 LLM 5 章 demo `ginga init s2-demo + ginga run s2-demo --chapters 5`（等 P7-I 收尾后跑，避免 endpoint 三家抢）
- 看板 ST-S2-S-MULTI-CHAPTER → done（demo PASS 后由主 agent 写）
