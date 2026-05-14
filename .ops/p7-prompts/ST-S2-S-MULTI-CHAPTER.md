# ST-S2-S-MULTI-CHAPTER：完整 runtime_state + 多章循环 + locked patch + R1-R3（P7）

## 你是谁

你是 ginga 项目 Sprint 2 的 **P7-S 骨干**。依赖 ST-S2-PHASE0（需要 capability_registry + op_translator）。任务是让 ginga 从"跑通一章"升级到"连续 5 章不崩 + locked patch 流程 + R1-R3 终稿三件套"。

## 必读输入

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` §3.5 runtime_state + §4.4 workflow + §4.5 immersive_mode
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §2.2.1
3. `/Users/arm/Desktop/ginga/foundation/schema/runtime_state.yaml`（含 locked patch 流程定义）
4. `/Users/arm/Desktop/ginga/ginga_platform/orchestrator/cli/demo_pipeline.py`（Sprint 1 demo 基础，需扩展不是重写）
5. `.ops/p7-handoff/ST-S2-PHASE0.md`（等 Phase 0 DONE 后再做集成测试段）

## 写范围 lock map

**可改**：`ginga_platform/orchestrator/cli/demo_pipeline.py`（扩展，**Read 后 Edit**）

**只能新建**：
- `ginga_platform/orchestrator/cli/multi_chapter.py`（多章循环 runner）
- `ginga_platform/orchestrator/cli/locked_patch.py`（locked 域 patch CLI）
- `meta/patches/_template.patch.yaml`（patch 文件 schema 示例）
- `ginga_platform/orchestrator/runner/tests/test_multi_chapter.py`
- `ginga_platform/orchestrator/runner/tests/test_locked_patch.py`
- `.ops/p7-handoff/ST-S2-S-MULTI-CHAPTER.md`

**绝不写**：其他 Track 范围 / 文档 / 看板

## 任务清单

### S-1 entity_runtime 多章 wire-up
扩展 `demo_pipeline.run_workflow` → 加 `chapter_no` 参数；每章生成后正确滚动：
- `CHARACTER_STATE.protagonist.events` 追加本章关键事件
- `FORESHADOW_STATE.pool` 既有 hook 检查 expected_payoff 是否触发；新增 hook 由 LLM 输出抽取
- `RESOURCE_LEDGER.particles` delta 累加（用 op_translator）
- `GLOBAL_SUMMARY.total_words` delta 累加
- `GLOBAL_SUMMARY.arc_summaries` 每 5 章追加一条 arc 总结

### S-2 locked 域 patch 流程
`locked_patch.py`：CLI 命令 `ginga patch <book_id> --field <path> --reason <text> --new-value <yaml>`：
- 写 `meta/patches/<patch_id>.yaml`（含 ts / scope / affected_chapters / approval_required）
- apply_patch 后跑 R3 一致性 checker
- 不允许直接绕过 patch 修改 `runtime_state.locked.*`（state_io 已有 audit；这里加 CLI 层友好提示）

### S-3 R1/R2/R3 终稿三件套实施
- R1_style_polish：调 LLM（dark-fantasy adapter or ask-llm 直调）做风格润色
- R2_consistency_check：跑 character-iq + cool-point-payoff checker（已存在），警告记 audit
- R3_final_pack：合并 chapter 正文 + 表格 → 写到 `foundation/runtime_state/<book>/chapter_NN.md`

### S-4 V1_release_check checker
最后一个 step，跑 DoD 检查：每章 ≥3000 bytes / FORESHADOW pool 至少 N 条 / total_words 累加正确。

### S-5 5 章 demo
`ginga run demo-book --chapters 5`（新增 `--chapters` flag），连续生成 5 章；每章经过完整 12 step。
LLM endpoint 默认 windhub，可 `--llm-endpoint` 切换。

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  rm -rf foundation/runtime_state/s2-demo && \
  ginga init s2-demo --topic 玄幻黑暗 && \
  ginga run s2-demo --chapters 5 && \
  [ $(ls foundation/runtime_state/s2-demo/chapter_*.md 2>/dev/null | wc -l) -ge 5 ] && \
  ls meta/patches/_template.patch.yaml && \
  python3 -m unittest ginga_platform.orchestrator.runner.tests.test_multi_chapter ginga_platform.orchestrator.runner.tests.test_locked_patch -v 2>&1 | tail -10 && \
  echo PASS
```

## 心跳协议 / 红线 / fallback

**心跳节奏强约束（按 dispatch-checklist §2.15 / §1.10 新规则）**：
- 启动后 ≤5min 必须写入 `## START` 心跳 entry（含 S-1..S-5 子任务计划清单）
- 每完成一个 S-N 子任务 ≤10min 内必须追加心跳 entry（不许聚批最后一刻一次性写）
- 心跳格式：`## <ISO ts> | S-N 完成` + 文件路径 + 字节 + 关键产物 + 下一步
- 与产物同步落盘：心跳 entry 必须在该子任务的产物文件落盘后 ≤10min 内写

**回包检测三件套（按 §2.16）**：每个 S-N 子任务必须三件套齐：
- 产物文件（lock map 内目标输出，bytes > 0）
- 心跳 entry（handoff 累加）
- 累计 checkpoint（test_*.py 测试结果 或 audit_log 一条）

**动态约束边界（按 §2.17）**：
- 写范围严格按上方 lock map；遇需越界 → handoff 写 `## QUESTION extend lock map: <path> reason: <text>`，等主 agent 回写 `## ACK extend: <path>` 后下一轮才允许写
- 看不到 ACK 前 stop（按 BLOCKED 处理）

**其他**：max_attempts=3，同 Sprint 1 P7 模板。

**关键依赖**：必须等 `.ops/p7-handoff/ST-S2-PHASE0.md` 出现 `## DONE` 后再开始集成测试段（S-3/S-4 涉及 capability_registry + op_translator 真调用）；S-1/S-2/S-5 单元测试段不依赖，可先做。

启动！预算：90 min wall。
