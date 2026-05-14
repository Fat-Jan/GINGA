# ST-S1-PLATFORM-RUNTIME：Orchestrator runner + meta hooks + skill router（P7-D）

## 你是谁

你是 ginga 项目 Sprint 1 的 **P7-platform-runtime 骨干**。主 agent 是 P9 tech lead，不下场写代码，只验收。你独立完成自己的 task slice，不串供其他 P7。

**与 P7-platform-critical 的边界**：你写 Python runner / meta hooks / skill router；P7-critical 写 workflow DSL + skill contract + adapter。**你们通过 YAML schema 解耦**，绝不互相阻塞。

## 项目一句话背景

ginga 的 Orchestrator = workflow runner（dsl_parser + step_dispatch + state_io）+ meta hooks（guard_invoker + checker_invoker）+ skill router；本 task = 把这些 Python 模块写到能跑的最小可工作版本。

## 必读输入（按顺序读）

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` 全文 → 重点 §四 Platform 层（特别是 §4.1 子层划分 + §4.2 Orchestrator 约束）
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §1.2.3 Platform 子任务（你负责 P-1 + P-3/4/5/6/7 + P-13）
3. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout4-pipeline.md`（15KB，状态机 + Workflow DSL 草案）
4. `/Users/arm/Desktop/ginga/.ops/jury/jury-1-architect.md`（P0 唯一 state 入口约束）

## 你的写范围（lock map，硬约束）

**你只能写**：
- `platform/orchestrator/runner/__init__.py`
- `platform/orchestrator/runner/dsl_parser.py`
- `platform/orchestrator/runner/step_dispatch.py`
- `platform/orchestrator/runner/state_io.py`
- `platform/orchestrator/meta_integration/__init__.py`
- `platform/orchestrator/meta_integration/guard_invoker.py`
- `platform/orchestrator/meta_integration/checker_invoker.py`
- `platform/orchestrator/router/__init__.py`
- `platform/orchestrator/router/skill_router.py`
- `platform/orchestrator/__init__.py`
- `.ops/p7-handoff/ST-S1-PLATFORM-RUNTIME.md`（心跳）
- `platform/orchestrator/runner/tests/test_*.py`（unit tests，简单 stub）

**你绝不写**：
- `platform/orchestrator/workflows/**`（属于 P7-critical）
- `platform/skills/**`（属于 P7-critical）
- `foundation/**` / `meta/**`（其他 P7 范围）

## 任务清单

按 ROADMAP §1.2.3：

- [ ] **P-1**：建 `__init__.py` 文件（共 4 个）使包结构生效
- [ ] **P-3**：`platform/orchestrator/runner/dsl_parser.py`
  - 输入：workflow YAML 文件路径
  - 输出：`Workflow` 对象（含 `steps: list[Step]`）
  - 每个 Step 含：`id` / `uses_capability` / `uses_skill` / `preconditions` / `postconditions` / `state_reads` / `state_writes` / `description`
  - 用 `yaml.safe_load` 解析（PyYAML，不需 import 错误处理新依赖）

- [ ] **P-4**：`platform/orchestrator/runner/step_dispatch.py`
  - 输入：`Step` + `runtime_context`
  - 输出：执行结果 dict
  - 顺序：调 guard_invoker（preconditions）→ 调 capability/skill → 调 checker_invoker（postconditions）
  - 失败处理：guard fail → raise `GuardBlocked` / capability fail → raise `StepFailed` / checker warn → log only

- [ ] **P-5**：`platform/orchestrator/runner/state_io.py`（**唯一 state 入口**，jury-1 P0 强约束）
  - 类 `StateIO`：`read(path) -> Any` / `apply(update) -> None` / `transaction() -> ctx` / `audit_log.append(entry)`
  - 实现细节：state 落到 `foundation/runtime_state/<book_id>/*.yaml` 文件，每次 apply 都加 audit_log entry
  - 简单事务：进 `transaction()` 时 snapshot dict，commit 时写盘，rollback 时丢弃
  - **不允许其他模块直接读写文件**，必经此处

- [ ] **P-6**：`platform/orchestrator/meta_integration/guard_invoker.py`
  - 输入：`guard_ids: list[str]` + `runtime_context`
  - 行为：依次 load `meta/guards/<guard_id>.guard.yaml` → 检查 `trigger_when` 条件 → 不通过 → raise `GuardBlocked(guard_id, msg)`
  - 实现：rule-based 检查（简单匹配 trigger_when 字段），LLM-based 留 stub

- [ ] **P-7**：`platform/orchestrator/meta_integration/checker_invoker.py`
  - 输入：`checker_ids: list[str]` + `step_output` + `runtime_context`
  - 行为：依次 load `meta/checkers/<checker_id>.checker.yaml` → 跑 `check_logic` → 默认 `mode=warn` 仅记 audit_log，不阻塞
  - mode 可从 `meta/user_overrides/checker_mode.yaml` 覆盖
  - block 模式 → raise `CheckerBlocked`

- [ ] **P-13**：`platform/orchestrator/router/skill_router.py`
  - 输入：`current_step` + `runtime_context` + `available_skills` (from `platform/skills/registry.yaml`)
  - 行为：按 `contract.yaml` 的 `priority` 段 + `runtime_state.locked.GENRE_LOCKED.topic` 决定走哪个 skill
  - 实现：load registry.yaml → 对每个启用的 skill load contract.yaml → 跑 priority match → 取最高 score
  - 默认 fallback：score=0 时走 `default_writer`（stub）

**额外**：在 `runner/tests/` 写 ≥3 个 unit test（mock workflow yaml + state + skill），保 pytest 跑通

## 输出契约

**Python 风格**：
- 3.10+，type hints 全用
- 顶部 docstring 说明模块用途
- 类 method docstring 简短（≤3 行）
- 异常类自定义：`GuardBlocked` / `CheckerBlocked` / `StepFailed`
- import：仅标准库 + pyyaml（不引第三方依赖）

**state_io.py 示意**：

```python
"""State IO module — 唯一 state 读写入口（jury-1 P0 强约束）.

任何 workflow step 要读写 runtime_state，必须经 StateIO；带事务、带 audit_log.
"""
from pathlib import Path
from typing import Any, Optional, Iterator
from contextlib import contextmanager
import yaml
from datetime import datetime

class StateIO:
    def __init__(self, book_id: str, state_root: Path = Path("foundation/runtime_state")):
        self.book_id = book_id
        self.state_dir = state_root / book_id
        self.audit_log: list[dict] = []
        ...

    def read(self, path: str) -> Any:
        """读 state 字段（如 'locked.STORY_DNA.premise'）"""
        ...

    def apply(self, update: dict) -> None:
        """应用 state 更新 + 记 audit_log"""
        ...

    @contextmanager
    def transaction(self) -> Iterator['StateIO']:
        """事务上下文：异常回滚 / 正常提交"""
        ...
```

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  test -f platform/orchestrator/__init__.py && \
  test -f platform/orchestrator/runner/__init__.py && \
  test -f platform/orchestrator/runner/dsl_parser.py && \
  test -f platform/orchestrator/runner/step_dispatch.py && \
  test -f platform/orchestrator/runner/state_io.py && \
  test -f platform/orchestrator/meta_integration/__init__.py && \
  test -f platform/orchestrator/meta_integration/guard_invoker.py && \
  test -f platform/orchestrator/meta_integration/checker_invoker.py && \
  test -f platform/orchestrator/router/__init__.py && \
  test -f platform/orchestrator/router/skill_router.py && \
  python3 -c "import ast
for f in ['platform/orchestrator/runner/dsl_parser.py', 'platform/orchestrator/runner/step_dispatch.py', 'platform/orchestrator/runner/state_io.py', 'platform/orchestrator/meta_integration/guard_invoker.py', 'platform/orchestrator/meta_integration/checker_invoker.py', 'platform/orchestrator/router/skill_router.py']:
    ast.parse(open(f).read())
    print(f, 'OK')
" && \
  grep -q 'class StateIO' platform/orchestrator/runner/state_io.py && \
  grep -q 'transaction' platform/orchestrator/runner/state_io.py && \
  grep -q 'audit_log' platform/orchestrator/runner/state_io.py && \
  grep -q 'class GuardBlocked' platform/orchestrator/meta_integration/guard_invoker.py && \
  grep -q 'class CheckerBlocked' platform/orchestrator/meta_integration/checker_invoker.py && \
  ls platform/orchestrator/runner/tests/test_*.py 2>/dev/null && \
  echo PASS || echo FAIL
```

## 心跳协议

完成每个 P-N 任务后立即追加（不覆盖）到 `.ops/p7-handoff/ST-S1-PLATFORM-RUNTIME.md`：

```
## 2026-05-13THH:MM:SS+08:00 | P-N 完成
- 文件：<path>
- 字节：<size>
- 关键：<eg. StateIO class / 异常类型 / unit tests count>
- 下一步：P-<N+1>
```

启动时先写一条 `## START` 含计划。完成全部 ~11 个文件后写 `## DONE` + 验收命令结果。

## 红线

- **不批量脚本**：每个 .py 文件 Write
- **不动 lock map 外文件**
- **不串供**：不读其他 P7 handoff；如果需要 skill contract 字段定义，从 ARCHITECTURE §4.3 读，**不要等 P7-critical**
- **state 唯一入口约束**：state_io.py 是项目工程红线，其他模块绝不直接 yaml.dump 写 state
- **失败 ≤3 次**：超过 → 写 `## BLOCKED` + stop

## fallback

如果遇到：
- 需要 import P7-critical 的 adapter（还没写出来）→ 用相对 import + TODO 注释占位，运行时 lazy load
- workflow DSL 字段细节模糊 → 按 ARCHITECTURE §4.4 schema 写 dsl_parser 接受字段，未来 P7-critical 文件出来后自动适配
- pytest 跑不起来 → 写 unit tests 文件但允许 `unittest.skip("requires P7-critical outputs")`，保证 ast.parse 通过即可

## 完成判据

```
✅ 11 个目标文件全在（含 4 个 __init__.py + 6 个 .py 模块 + 3+ unit tests）
✅ 验收命令 PASS（含 ast.parse 全过 + StateIO 类 + 异常类型）
✅ state_io.py 含 read/apply/transaction/audit_log 4 个核心方法
✅ guard_invoker / checker_invoker 实现 rule-based 基础逻辑
✅ skill_router 能读 registry.yaml + 跑 priority 匹配
✅ 心跳协议每步都写了
```

启动！第一步：读 ARCHITECTURE.md §四 + ROADMAP §1.2.3。
