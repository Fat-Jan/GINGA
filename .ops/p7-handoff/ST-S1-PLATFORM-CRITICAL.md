# ST-S1-PLATFORM-CRITICAL Handoff（P7-C，critical path）

## 2026-05-13T18:20:00+08:00 | START

**P7-C 启动**，task_id = ST-S1-PLATFORM-CRITICAL，单承担 critical path。

**计划**（按 prompt 任务清单顺序）：
1. P-2  → `platform/orchestrator/workflows/novel_pipeline_mvp.yaml`（12 step）
2. P-8  → `platform/skills/dark-fantasy-ultimate-engine/skill.md`（导入思路 2 原文）
3. P-9  → `platform/skills/dark-fantasy-ultimate-engine/contract.yaml`（含 immersive_mode + forbidden_mutation + priority）
4. P-10 → `platform/skills/dark-fantasy-ultimate-engine/adapter.py`（4 个方法，ast.parse 通过）
5. P-11a → `platform/skills/planning-with-files/skill.md`（导入思路 3 原文）
6. P-11b → `platform/skills/planning-with-files/contract.yaml`
7. P-11c → `platform/skills/planning-with-files/adapter.py`
8. P-12 → `platform/skills/registry.yaml`（双 skill + 路由优先级）

**红线复述**：
- workflow 12 step、uses_capability 用资产 id（不许文件路径）
- contract.yaml 必须含 forbidden_mutation + immersive_mode（dark-fantasy 独有）+ priority 段
- adapter.py ast.parse 通过 + 4 个方法（input/output_transform + enter/exit_immersive_mode）
- 思路 2/3 skill.md 原文不动
- 写范围只动 platform/orchestrator/workflows/* + platform/skills/** + 本 handoff

**预算**：60 分钟 wall-time / 3 次失败上限。
**工具约束**：subagent 工具集无 Write/Edit，使用 Bash heredoc 等价单文件写入，符合"逐文件直接修改"精神，便于人工 diff 审阅。

## 2026-05-13T18:36:00+08:00 | P-2 完成
- 文件：platform/orchestrator/workflows/novel_pipeline_mvp.yaml
- 字节：~5.2KB
- 关键：12 step（A-H + R1-R3 + V1），uses_capability 全用资产 id（base-template-* / base-methodology-* / base-card-* / base-checker-*），preconditions 用 guard:、postconditions 用 checker:
- 验证：grep -c '^  - id: ' = 12，! grep 'uses_capability:.*\.md$' 通过
- 下一步：P-8

## 2026-05-13T18:36:30+08:00 | P-8 完成
- 文件：platform/skills/dark-fantasy-ultimate-engine/skill.md
- 字节：23107（与原料一致）
- 关键：cp 原子拷贝，diff -q 确认 identical，原文不动
- 下一步：P-9

## 2026-05-13T18:37:00+08:00 | P-9 完成
- 文件：platform/skills/dark-fantasy-ultimate-engine/contract.yaml
- 字节：~5.4KB
- 关键：9 个 required key 齐（skill_id/version/status/inputs/outputs/priority/forbidden_mutation/adapter/immersive_mode），字段数 34（≥30 达标），immersive_mode 含 available + trigger + behavior + exit_signal + fallback，priority 含玄幻黑暗 100 / 玄幻 30 / default 0，forbidden_mutation 含 locked.* + meta/* 全锁
- 下一步：P-10

## 2026-05-13T18:38:00+08:00 | P-10 完成
- 文件：platform/skills/dark-fantasy-ultimate-engine/adapter.py
- 字节：~9.5KB
- 关键：DarkFantasyAdapter 类，4 方法齐（input_transform / output_transform / enter_immersive_mode / exit_immersive_mode），ast.parse 通过；type hints + docstring 充分；HARD_PARTICLE_ANCHOR=840000000 锚点常量；immersive 累积 pending_updates + exit 时批量 apply + 失败 restore + 复盘 persist
- 下一步：P-11a

## 2026-05-13T18:38:30+08:00 | P-11a 完成
- 文件：platform/skills/planning-with-files/skill.md
- 字节：13784（与原料一致）
- 关键：cp 原子拷贝，diff -q identical，原文不动（含 frontmatter + hooks）
- 下一步：P-11b

## 2026-05-13T18:39:00+08:00 | P-11b 完成
- 文件：platform/skills/planning-with-files/contract.yaml
- 字节：~4.4KB
- 关键：8 个 required key 齐，无 immersive_mode（正确，仅 dark-fantasy 独有），priority cross-cutting（规划维护 50 / 历史考据 50 / 正文创作 0），forbidden_mutation 含 locked.* + entity_runtime.* + chapter_text + meta/*（planning 不动正文 state）
- 下一步：P-11c

## 2026-05-13T18:40:00+08:00 | P-11c 完成
- 文件：platform/skills/planning-with-files/adapter.py
- 字节：~8.3KB
- 关键：PlanningWithFilesAdapter 类，4 方法齐（input/output_transform + enter/exit_immersive_mode 实现为 no-op + audit_log，保接口契约）；TASK_CATEGORIES 常量；workspace 三件套双向同步；按思路 3 mode 双模式切片章节窗口（增量 10 / 长线 30 / 跨卷 40）；ast.parse 通过
- 下一步：P-12

## 2026-05-13T18:41:00+08:00 | P-12 完成
- 文件：platform/skills/registry.yaml
- 字节：~4.8KB
- 关键：双 skill 注册（dark-fantasy primary_writer / planning-with-files cross_cutting_tool），priority_routing 段含硬绑题材 + score_by_topic / score_by_task_category，routing_rules 含算法描述 + default_writer 回退（base-card-chapter-draft），compatibility 段明示双 skill 平行不揉合，registration_guide 给新 skill 接入步骤
- 下一步：DoD 验收

## 2026-05-13T18:42:00+08:00 | DoD 验收

**验收命令**（prompt §"验收命令（DoD）"完整链）：
```
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

**结果**：`PASS`

## DONE

**8 个目标文件全在**（按写范围 lock map）：
1. platform/orchestrator/workflows/novel_pipeline_mvp.yaml（5.2KB / 12 step）
2. platform/skills/dark-fantasy-ultimate-engine/skill.md（23107 字节 / 原文）
3. platform/skills/dark-fantasy-ultimate-engine/contract.yaml（5.4KB / 34 字段 / 含 immersive_mode）
4. platform/skills/dark-fantasy-ultimate-engine/adapter.py（9.5KB / 4 方法 / ast.parse 通过）
5. platform/skills/planning-with-files/skill.md（13784 字节 / 原文）
6. platform/skills/planning-with-files/contract.yaml（4.4KB / 36 字段 / 无 immersive_mode）
7. platform/skills/planning-with-files/adapter.py（8.3KB / 4 方法 no-op 兼容 / ast.parse 通过）
8. platform/skills/registry.yaml（4.8KB / 双 skill 注册 + 路由规则）

**完成判据复核**：
- [x] 8 个目标文件全在
- [x] 验收命令 PASS（含 12 step + ast.parse + immersive_mode + forbidden_mutation）
- [x] workflow uses_capability 全用资产 id（不是文件路径）
- [x] 双 skill contract.yaml 各 ≥20 字段（dark-fantasy 34 / planning 36）
- [x] adapter.py 包含 4 个方法（input/output_transform + enter/exit_immersive_mode）
- [x] 心跳协议每步都写了

**审查三问**：
- Q1 接口兼容：runtime_state 全用 .get() + or {} 防空；adapter 内对 state_io 方法全 try/except 兜底（state_io 由其他 P7 实现，stub 阶段也能 ast.parse）；TYPE_CHECKING 包裹避免循环 import
- Q2 边界处理：immersive enter 幂等；exit 部分失败可继续 + restore + persist 兜底；planning enter/exit no-op 但记 audit_log；中文字数估算剔除表格与代码块
- Q3 proper-fix：skill.md 用 cp 原子拷贝（diff -q identical）；adapter 用 `from __future__ import annotations` + TYPE_CHECKING；planning no-op 是显式接口契约不是 workaround

**技术债（向 P8 报告）**：
1. **Python 模块路径连字符问题**：contract.yaml 声明 `adapter.module = platform.skills.dark_fantasy_ultimate_engine.adapter`（下划线），但目录名是 `dark-fantasy-ultimate-engine`（连字符）。Python 不允许连字符模块名。建议 P-13 skill-router 或 P-3 dsl_parser 实现 dash-to-underscore normalize 层（如 importlib.util.spec_from_file_location 按 contract.adapter.module 字段路径加载）。归 P7-platform-runtime 处理。
2. **state_io 接口未冻结**：adapter 假设 state_io 有 `apply / snapshot / restore / trigger_check / dump_immersive_fallback / append_audit` 等方法。这些方法签名未由 P-5 正式定义。当前 adapter 全 try/except 兜底，未来 state_io 落地后需做接口契约联调。建议 S1 末做一次 adapter ↔ state_io 集成 spike。
3. **registry priority_routing 与 contract priority 信息冗余**：registry 给 router 快查表（score_by_topic / score_by_task_category），contract 给 audit 详细 when/score 列表。重复 = 维护风险。建议 S2 实现 contract 为 single source of truth，registry 自动派生 priority cache。
4. **immersive_mode 仅 dark-fantasy 独有，但接口在两个 adapter 上都实现**：planning 是 no-op 兼容。未来若有第 3 个 skill 不需要 immersive，建议引入 ABC（abc.ABCMeta）让 immersive 方法成可选 mixin，而不是强制接口。
