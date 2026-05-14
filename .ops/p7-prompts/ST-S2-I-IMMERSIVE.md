# ST-S2-I-IMMERSIVE：dark-fantasy immersive_mode 实施 + 5 章沉浸 demo（P7）

## 你是谁

你是 ginga 项目 Sprint 2 的 **P7-I 骨干**。依赖 ST-S2-PHASE0（需要 op_translator 才能批量 apply pending_updates）。任务是把 Sprint 1 写好的 immersive_mode 接口（adapter 已存）真正落地：连续多章不打断 state、checker 期内静默、退出时批量 apply + R2。

## 必读输入

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` §4.5 immersive_mode
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §2.2.4
3. `/Users/arm/Desktop/ginga/.ops/jury/jury-3-novel-editor.md` §改进 4（dark-fantasy 沉浸专线）
4. `/Users/arm/Desktop/ginga/ginga_platform/skills/dark_fantasy_ultimate_engine/adapter.py`（enter/exit_immersive_mode 已有 stub，扩展实施）
5. `/Users/arm/Desktop/ginga/ginga_platform/skills/dark_fantasy_ultimate_engine/contract.yaml`（immersive_mode 段定义）
6. `/Users/arm/Desktop/ginga/ginga_platform/orchestrator/meta_integration/checker_invoker.py`（看 mode 字段如何在 immersive 期被静默）

## 写范围 lock map

**可改**：
- `ginga_platform/skills/dark_fantasy_ultimate_engine/adapter.py`（扩展 immersive 实施，**Read 后 Edit**）
- `ginga_platform/orchestrator/meta_integration/checker_invoker.py`（加 immersive flag 静默 hook）

**只能新建**：
- `ginga_platform/orchestrator/cli/immersive_runner.py`
- `ginga_platform/orchestrator/runner/tests/test_immersive_mode.py`
- `.ops/p7-handoff/ST-S2-I-IMMERSIVE.md`

**绝不写**：其他 Track 范围 / 文档 / 看板

## 任务清单

### I-1 adapter.enter_immersive_mode 实施
扩展 `DarkFantasyAdapter.enter_immersive_mode`：
- `self._immersive_active = True`
- 写 `runtime_state.workflow_flags.immersive_mode = True`（state_io.apply）
- 写 `runtime_state.workflow_flags.checker_silenced = True`
- audit "immersive entered"

### I-2 chapter_block_end signal trigger
新增 `ImmersiveRunner.run_block(book_id, chapters: int)`：
- enter immersive
- 顺序跑 N 章 G_chapter_draft（adapter.output_transform 入 pending_updates，不直接 state_io.apply）
- 收到 chapter_block_end signal（默认 = run_block 末尾自动触发）
- exit immersive

### I-3 checker_invoker 期内静默
改 `checker_invoker.py`：在 invoke 时先 `state_io.read('workflow_flags.checker_silenced')`，True → 直接 return（audit 一条 silenced）；False → 正常跑。

### I-4 exit_immersive_mode 批量 apply + R2
扩展 `DarkFantasyAdapter.exit_immersive_mode`：
- 用 op_translator 把 `self._pending_updates` 转 state_updates
- state_io.transaction() 批量 apply
- 写 `runtime_state.workflow_flags.checker_silenced = False`
- 触发 R2_consistency_check（调 checker_invoker，此时不再静默）
- exception → 回退到 `self._last_safe_state` + 持久化 pending 到 `.ops/immersive_fallback/<ts>.json`

### I-5 5 章沉浸 demo
`ginga run demo-book --immersive --chapters 5` CLI 新增 flag：
- 期内 audit_log 无 checker warn entries
- 退出时一次性 apply（audit 显示 "5 chapters batch applied"）

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  rm -rf foundation/runtime_state/i-demo && \
  ginga init i-demo --topic 玄幻黑暗 && \
  ginga run i-demo --immersive --chapters 5 && \
  [ $(ls foundation/runtime_state/i-demo/chapter_*.md 2>/dev/null | wc -l) -ge 5 ] && \
  python3 -c "
import yaml
log = yaml.safe_load(open('foundation/runtime_state/i-demo/audit_log.yaml'))
entries = log.get('entries', [])
silenced = [e for e in entries if 'silenced' in e.get('msg', '')]
batch_apply = [e for e in entries if 'batch applied' in e.get('msg', '') or 'pending_updates' in str(e.get('payload', {}))]
print(f'silenced entries: {len(silenced)}, batch apply: {len(batch_apply)}')
assert len(batch_apply) >= 1, 'no batch apply audit'
" && \
  python3 -m unittest ginga_platform.orchestrator.runner.tests.test_immersive_mode -v 2>&1 | tail -10 && \
  echo PASS
```

## 心跳协议 / 红线 / fallback

**心跳节奏强约束（按 dispatch-checklist §2.15 / §1.10 新规则）**：
- 启动后 ≤5min 必须写入 `## START` 心跳 entry（含 I-1..I-5 子任务计划清单）
- 每完成一个 I-N 子任务 ≤10min 内必须追加心跳 entry
- 心跳与产物同步落盘（产物文件落盘后 ≤10min 内写心跳）

**回包检测三件套（按 §2.16）**：每个 I-N 子任务必须三件套齐（产物 + 心跳 + checkpoint/test）

**动态约束边界（按 §2.17）**：遇需越界 → handoff 写 `## QUESTION extend lock map: <path>`，等主 agent `## ACK extend` 后才允许下一轮写。看不到 ACK 前 stop。

**其他**：max_attempts=3。

**关键依赖**：必须等 ST-S2-PHASE0 DONE（用 op_translator）。可先做 I-1/I-2/I-3 单元测试段，I-4/I-5 集成段等 Phase 0。

启动！预算：60 min wall。
