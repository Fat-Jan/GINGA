# ST-S2-PHASE0：capability_registry + op_translator + 12 step 集成 spike（P7）

## 你是谁

你是 ginga 项目 Sprint 2 的 **P7-Phase0 骨干，critical path 单独承担者**。Sprint 1 留了 3 个技术债，你的任务是把它们清掉，让 Sprint 2 的 S/I 两路能跑完整 12 step。

## 项目一句话背景

Sprint 1 已完成：4 层架构 + 双 skill contract + workflow runner + ginga CLI demo（简化版 demo 跳过 A-F + G 直调 LLM）。Sprint 2 需要跑通完整 12 step：A-F 调 capability_registry 注册的能力，G 调 skill adapter，H/R/V 都真实跑。

## 必读输入

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` §四 Platform 层（含 4.2 Orchestrator + 4.3 contract + 4.4 workflow）
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §二 Sprint 2 总览
3. `/Users/arm/Desktop/ginga/ginga_platform/skills/dark_fantasy_ultimate_engine/adapter.py`（看 `output_transform` 返回 `[{op, path, value}]` 格式）
4. `/Users/arm/Desktop/ginga/ginga_platform/orchestrator/runner/state_io.py`（看 `apply({flat_path: value})` 接口）
5. `/Users/arm/Desktop/ginga/ginga_platform/skills/registry.yaml`（双 skill 注册示例）
6. `/Users/arm/Desktop/ginga/ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml`（12 step DSL，用 capability id）

## 写范围 lock map（硬约束）

**只能写**：
- `ginga_platform/orchestrator/registry/__init__.py`
- `ginga_platform/orchestrator/registry/capability_registry.py`
- `ginga_platform/orchestrator/runner/op_translator.py`
- `ginga_platform/orchestrator/runner/tests/test_capability_registry.py`
- `ginga_platform/orchestrator/runner/tests/test_op_translator.py`
- `ginga_platform/orchestrator/runner/tests/test_integration_12step.py`
- `.ops/p7-handoff/ST-S2-PHASE0.md`（心跳）

**绝不写**：
- 其他 P7 Track 的范围（S/R/I/L）
- ARCHITECTURE / ROADMAP / 看板 / 原料

## 任务清单

### P0-1 CapabilityRegistry 模块（150-250 行 + tests）

`ginga_platform/orchestrator/registry/capability_registry.py`：

```python
class CapabilityRegistry:
    """workflow step.uses_capability 字段的 id → 可执行函数 / 资产解析器."""

    def register(self, capability_id: str, handler: Callable[..., dict]) -> None: ...
    def list_capabilities(self) -> list[str]: ...
    def resolve(self, capability_id: str) -> Callable[..., dict]: ...
    def call(self, capability_id: str, inputs: dict) -> dict: ...

    @classmethod
    def from_defaults(cls) -> "CapabilityRegistry":
        """Sprint 2 mock 版本：注册 5-10 个最小 stub capability，足够 12 step 跑通.

        必须含的 capability id（对应 workflow_mvp.yaml 的 uses_capability 字段）：
            - base-methodology-creative-brainstorm (A_brainstorm)
            - base-template-story-dna (B_premise_lock)
            - base-template-worldview (C_world_build)
            - base-template-protagonist (D_character_seed)
            - base-template-outline (E_outline)
            - base-methodology-style-polish (R1_style_polish)
            - base-card-chapter-draft (default writer fallback)
        每个 stub 返回固定 dict（含 chapter_text='<mock>' 或对应 state seed），
        S2 不接真原料；L Track 完成后 S3 切真.
        """
```

### P0-2 op_translator 模块（100-180 行 + tests）

`ginga_platform/orchestrator/runner/op_translator.py`：

```python
def adapter_ops_to_state_updates(ops: list[dict[str, Any]]) -> dict[str, Any]:
    """adapter.output_transform 返回的 [{op, path, value}] 转成 state_io.apply 接受的 flat dict.

    op 支持：write / delta / append / append_or_update.
    path 形如 'runtime_state.entity_runtime.RESOURCE_LEDGER.particles'：
        - 'runtime_state.' 前缀剥掉 (state_io 不要这层)
        - delta: 读当前值 + 增量 → 写新值
        - append: 读当前 list + 追加 value → 写新 list
        - append_or_update: 读当前 list，按 'key' 字段 match：存在则替换，不存在则 append
        - write: 直接覆盖
    """
```

需要 state_io 引用以做 delta/append 的读 → 写，签名改成 `(ops, state_io)`。

### P0-3 integration test：完整 12 step 跑通

`ginga_platform/orchestrator/runner/tests/test_integration_12step.py`：

跑一遍 dsl_parser → workflow_mvp.yaml → step_dispatch（注入 CapabilityRegistry.from_defaults + registry.yaml + StateIO + skill_router + op_translator）→ 12 step 全部执行：
- A-F 调 capability stub
- G 调 dark-fantasy adapter（可 mock skill output 不真调 LLM）
- H 调 op_translator → state_io.apply
- R1-R3 + V1 调 capability stub
全过程不报错，audit_log 有 12 条 step entry，最后 entity_runtime.GLOBAL_SUMMARY.total_words > 0.

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  python3 -c "from ginga_platform.orchestrator.registry.capability_registry import CapabilityRegistry; reg = CapabilityRegistry.from_defaults(); caps = reg.list_capabilities(); assert len(caps) >= 7, f'only {len(caps)} capabilities'; print('caps:', caps)" && \
  python3 -m unittest \
    ginga_platform.orchestrator.runner.tests.test_capability_registry \
    ginga_platform.orchestrator.runner.tests.test_op_translator \
    ginga_platform.orchestrator.runner.tests.test_integration_12step \
    -v 2>&1 | tail -20 && \
  echo PASS
```

## 心跳协议

完成每个 P0-N 任务后追加到 `.ops/p7-handoff/ST-S2-PHASE0.md`：

```
## 2026-05-13THH:MM:SS+08:00 | P0-N 完成
- 文件：<path>
- 字节：<size>
- 关键：<eg. 7 capability stubs / delta 实施 / 12 step audit>
- 下一步：P0-<N+1>
```

启动写 `## START`，完成写 `## DONE` + 验收命令结果。

## 红线

- max_attempts = 3，超过写 `## BLOCKED` + stop
- 不批量脚本；逐文件 Write
- 不动 lock map 外
- 不串供其他 P7
- capability_registry 不要扫真原料（mock stub 即可，S3 切真）
- 全 Python 3.10+ type hints + standard lib + pyyaml only

## fallback

若 op_translator 的 path 解析需要 dot-notation 库 → 自己写解析器（不引第三方）。
若 integration test 需要 dark-fantasy adapter 实际跑 → 用 monkey-patch 让 adapter 返回固定 skill_output dict。

启动！预算：60 min wall。
