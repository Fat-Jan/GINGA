# ST-S1-PLATFORM-CRITICAL：workflow DSL + 双 skill contract + adapter（P7-C，critical path）

## 你是谁

你是 ginga 项目 Sprint 1 的 **P7-platform-critical 骨干**，**critical path 单独承担者**。主 agent 是 P9 tech lead，不下场写代码，只验收。你独立完成自己的 task slice，不串供其他 P7。

**为什么 critical path**：jury-1 Q3 标记 P-9/P-10/P-11 双 skill contract.yaml + adapter 是 S1 最高风险段。主 agent 把这块单独抽出来给你，让你专心做、不被其他 task 干扰。

## 项目一句话背景

ginga 系统骨干：MVP workflow 12 step (A-H + R1-R3 + V1) 跑通"输入创意 → 第一章正文"；其中 G_chapter_draft 由 skill-router 决定走 dark-fantasy 或 default writer。

## 必读输入（按顺序读）

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` 全文 → 重点 §四 Platform 层
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §1.2.3 Platform 子任务（你负责 P-2 + P-8/9/10/11 + P-12 + P-13）
3. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout2-doctrine.md`（25KB，**双 skill 完整画像 + 状态卡 + 账本字段**）
4. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout4-pipeline.md`（15KB，13 阶段 + Workflow DSL 草案）
5. `/Users/arm/Desktop/ginga/.ops/jury/jury-1-architect.md`（P0 contract.yaml 必须字段 + immersive_mode 子节点）

## 你的写范围（lock map，硬约束）

**你只能写**：
- `platform/orchestrator/workflows/novel_pipeline_mvp.yaml`（workflow DSL）
- `platform/skills/dark-fantasy-ultimate-engine/skill.md`（导入原 skill 文档，**不动原文**）
- `platform/skills/dark-fantasy-ultimate-engine/contract.yaml`（**核心产出**）
- `platform/skills/dark-fantasy-ultimate-engine/adapter.py`（**核心产出**）
- `platform/skills/planning-with-files/skill.md`（导入原 skill 文档，不动原文）
- `platform/skills/planning-with-files/contract.yaml`
- `platform/skills/planning-with-files/adapter.py`
- `platform/skills/registry.yaml`
- `.ops/p7-handoff/ST-S1-PLATFORM-CRITICAL.md`（心跳）

**你绝不写**：
- `platform/orchestrator/runner/**` 或 `meta_integration/**` 或 `router/**`（这些归 P7-platform-runtime）
- `foundation/**` / `meta/**`（其他 P7 范围）
- `_原料/思路/**`（原料只读）

## 任务清单

按 ROADMAP §1.2.3：

- [ ] **P-2**：`platform/orchestrator/workflows/novel_pipeline_mvp.yaml`
  - **12 step**（按 ARCHITECTURE §4.4）：A_brainstorm → B_premise_lock → C_world_build → D_character_seed → E_outline → F_state_init → G_chapter_draft → H_chapter_settle → R1_style_polish → R2_consistency_check → R3_final_pack → V1_release_check
  - 每个 step 字段：`id` / `uses_capability`（资产 id，**不许用文件路径**，按 jury-2 字段补丁 5）/ `uses_skill`（若 skill routing）/ `preconditions: [guard:X]` / `postconditions: [checker:Y]` / `state_reads` / `state_writes` / `description`

- [ ] **P-8**：把思路 2 文档放到 `platform/skills/dark-fantasy-ultimate-engine/skill.md`
  - 源：`_原料/思路/待整理思路 2`（路径含空格，**注意 quote**）
  - **不动原文**，原样复制（用 Read 读全文 → Write 写到目标）

- [ ] **P-9**：`platform/skills/dark-fantasy-ultimate-engine/contract.yaml`
  - 按 ARCHITECTURE §4.3 contract.yaml 完整 schema：`skill_id` / `version` / `status` / `inputs` / `outputs` / `priority`（含 score：玄幻黑暗 100，其他玄幻 30，default 0） / `forbidden_mutation`（runtime_state.locked + meta/* 全禁） / `adapter` / `immersive_mode`（含 available / trigger / behavior）
  - 必须基于 scout-2 实际读到的 skill 内容填充字段（不臆造）

- [ ] **P-10**：`platform/skills/dark-fantasy-ultimate-engine/adapter.py`
  - 实现 `input_transform()`（runtime_state → skill 内部输入格式）和 `output_transform()`（skill 输出 → runtime_state 更新）
  - 实现 `enter_immersive_mode()` / `exit_immersive_mode()`（按 ARCHITECTURE §4.5）
  - state 写入必须经过 `state_io.py`（你不实现 state_io，假设它存在并 import）
  - 写法：纯 Python 3.10+ 标准库 + 顶部 type hints + 充分 docstring

- [ ] **P-11**：把思路 3 文档放到 `platform/skills/planning-with-files/skill.md` + `contract.yaml` + `adapter.py`
  - 思路 3 = planning-with-files v9.2.0 （任务规划三件套 task_plan.md / findings.md / progress.md）
  - contract.yaml 关键差异：`inputs` = workspace ref / `outputs` = workspace 更新 / `priority` = cross-cutting 不与 dark-fantasy 抢路由（score = 0 default + condition workspace_managed=true 时 score 50）
  - `forbidden_mutation`: runtime_state.locked + runtime_state.entity_runtime（planning skill 不直接动正文 state）

- [ ] **P-12**：`platform/skills/registry.yaml`
  - 列双 skill + enabled 状态 + 路由优先级
  - 字段：`skills: { <skill_id>: { contract: <path>, enabled: true, priority_routing: ... } }`

## 输出契约（关键文件）

**contract.yaml 必填字段**（按 ARCHITECTURE §4.3 严格）：

```yaml
skill_id: string
version: string
status: enum [active, deprecated, experimental]
inputs:
  <input_name>:
    type: ...
    required: bool
    constraint: <optional>
outputs:
  <output_name>:
    type: ...
    format: <optional>
state_updates:
  <state_path>: <update_op>
priority:
  - when: <condition>
    score: int
  - default: int
forbidden_mutation:
  - <state_path or glob>
adapter:
  input_transform: <fn name>
  output_transform: <fn name>
  state_sync_mode: enum [explicit, auto]
# dark-fantasy 独有
immersive_mode:
  available: bool
  trigger: <flag path>
  behavior: <multi-line description>
```

**adapter.py 接口**：

```python
from typing import Dict, Any
from platform.orchestrator.runner.state_io import StateIO  # 假设存在

class DarkFantasyAdapter:
    def __init__(self, state_io: StateIO):
        self.state_io = state_io
        self._immersive_active = False
        self._pending_updates: list = []

    def input_transform(self, runtime_state: Dict) -> Dict:
        """runtime_state → dark-fantasy skill 输入格式"""
        ...

    def output_transform(self, skill_output: Dict) -> Dict:
        """skill 输出 → runtime_state 更新指令"""
        ...

    def enter_immersive_mode(self) -> None:
        """连续多章不打断 state 更新，pending_updates 累积"""
        self._immersive_active = True

    def exit_immersive_mode(self) -> None:
        """批量 apply pending_updates + 触发 R2 一致性"""
        self._immersive_active = False
        for update in self._pending_updates:
            self.state_io.apply(update)
        self._pending_updates.clear()
```

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  test -f platform/orchestrator/workflows/novel_pipeline_mvp.yaml && \
  [ "$(grep -c '^  - id: ' platform/orchestrator/workflows/novel_pipeline_mvp.yaml)" -eq 12 ] && \
  grep -q 'A_brainstorm' platform/orchestrator/workflows/novel_pipeline_mvp.yaml && \
  grep -q 'V1_release_check' platform/orchestrator/workflows/novel_pipeline_mvp.yaml && \
  ! grep -E 'uses_capability:.*\.md$' platform/orchestrator/workflows/novel_pipeline_mvp.yaml && \
  test -f platform/skills/dark-fantasy-ultimate-engine/skill.md && \
  test -f platform/skills/dark-fantasy-ultimate-engine/contract.yaml && \
  test -f platform/skills/dark-fantasy-ultimate-engine/adapter.py && \
  test -f platform/skills/planning-with-files/skill.md && \
  test -f platform/skills/planning-with-files/contract.yaml && \
  test -f platform/skills/planning-with-files/adapter.py && \
  test -f platform/skills/registry.yaml && \
  grep -q 'immersive_mode:' platform/skills/dark-fantasy-ultimate-engine/contract.yaml && \
  grep -q 'forbidden_mutation:' platform/skills/dark-fantasy-ultimate-engine/contract.yaml && \
  grep -q 'forbidden_mutation:' platform/skills/planning-with-files/contract.yaml && \
  python3 -c "import ast; ast.parse(open('platform/skills/dark-fantasy-ultimate-engine/adapter.py').read())" && \
  python3 -c "import ast; ast.parse(open('platform/skills/planning-with-files/adapter.py').read())" && \
  echo PASS || echo FAIL
```

## 心跳协议

完成每个 P-N 任务后立即追加（不覆盖）到 `.ops/p7-handoff/ST-S1-PLATFORM-CRITICAL.md`：

```
## 2026-05-13THH:MM:SS+08:00 | P-N 完成
- 文件：<path>
- 字节：<size>
- 关键：<eg. 12 step / contract 字段 / immersive_mode>
- 下一步：P-<N+1>
```

启动时先写一条 `## START` 含计划。完成全部 8 个文件后写 `## DONE` + 验收命令结果。

## 红线

- **不批量脚本**：每个文件 Write，不许 sed/awk/find-exec
- **思路 2/3 原文不许动**：P-8/P-11 是 Read 原料后 Write，逐字保留
- **uses_capability 必须用资产 id**（jury-2 字段补丁 5）：不许用文件路径
- **不动 lock map 外文件**
- **不串供**：不读其他 P7 handoff
- **失败 ≤3 次**：超过 → 写 `## BLOCKED` + stop

## fallback

如果遇到：
- 思路 2/3 原文太大读不完 → 分段 Read，但**必须完整复制到 skill.md**（每段 Append）
- contract.yaml 某字段无法确定 → 在 handoff 写 `## QUESTION`，按 ARCHITECTURE §4.3 默认值兜底
- adapter.py 状态读写细节模糊 → 先实现 stub（pass + TODO），保 unit test 能通过 ast.parse 即可

## 完成判据

```
✅ 8 个目标文件全在
✅ 验收命令 PASS（含 12 step + ast.parse + immersive_mode + forbidden_mutation）
✅ workflow uses_capability 全用资产 id（不是文件路径）
✅ 双 skill contract.yaml 各 ≥20 字段
✅ adapter.py 包含 4 个方法（input/output_transform + enter/exit_immersive_mode）
✅ 心跳协议每步都写了
```

启动！第一步：读 ARCHITECTURE.md §四 + scout-2-doctrine.md。
