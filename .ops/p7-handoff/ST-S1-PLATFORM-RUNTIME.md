# P7-D: ST-S1-PLATFORM-RUNTIME 心跳

## START 2026-05-13T18:26:32+08:00

**计划**：
- P-1：4 个 `__init__.py`（orchestrator/runner/meta_integration/router + tests）
- P-5：state_io.py（唯一 state 入口，jury-1 P0，最先写，其他模块依赖）
- P-6：guard_invoker.py（前置硬阻断，rule-based）
- P-7：checker_invoker.py（后置软审计，default warn-only + user_overrides 支持）
- P-3：dsl_parser.py（YAML → Workflow + Step dataclass）
- P-4：step_dispatch.py（guard → capability/skill → checker）
- P-13：skill_router.py（registry.yaml + contract.yaml priority match）
- tests：≥3 个 unit test（dsl_parser / state_io / skill_router）

**红线**：state_io 是唯一入口；只用标准库 + pyyaml；type hints 全用；ast.parse 必过；写范围严格在 lock map 内；不写 workflows/ 或 skills/。

**完成顺序**（依赖驱动）：P-1 → P-5 → P-6 → P-7 → P-3 → P-4 → P-13 → tests → DoD。

## 2026-05-13T18:28:30+08:00 | P-1 完成
- 文件：5 个 `__init__.py`（orchestrator/、runner/、meta_integration/、router/、runner/tests/）
- 字节：11 + 20 + 18 + 10 + 1 行
- 关键：包结构生效；runner/__init__.py 导出 Workflow/Step/parse_workflow/StateIO/dispatch_step/StepFailed；meta_integration 导出 invoke_guards/GuardBlocked/invoke_checkers/CheckerBlocked；router 导出 SkillRouter/RoutingDecision/RouterError
- 下一步：P-5（state_io，最关键依赖项）

## 2026-05-13T18:30:05+08:00 | P-5 完成
- 文件：platform/orchestrator/runner/state_io.py（341 行）
- 关键：StateIO 类含 read/apply/transaction/audit/snapshot；AuditEntry 数据类；StateIOError；事务用 @contextmanager + deep-copy snapshot；落盘按 §3.5 五个分域分文件（locked/entity_runtime/workspace/retrieved/audit_log.yaml），原子写（tempfile + os.replace）；apply 禁止改 audit_log（强制走 audit()）；smoke 测试已通过（包含 reload）
- 下一步：P-6（guard_invoker）

## 2026-05-13T18:31:20+08:00 | P-6 完成
- 文件：platform/orchestrator/meta_integration/guard_invoker.py（206 行）
- 关键：GuardBlocked 异常；GuardLoadError；GuardSpec 数据类；invoke_guards(guard_ids, runtime_context) → list[str]；rule-based trigger_when 支持 state_eq/state_ne/state_missing/state_in/context_truthy；命中 guard 抛 GuardBlocked 前先写 audit_log；llm_check enabled=true 当 S1 stub 处理（记 audit 不阻塞）；guard YAML 缺失 → S1 noop fallback
- 下一步：P-7（checker_invoker）

## 2026-05-13T18:32:45+08:00 | P-7 完成
- 文件：platform/orchestrator/meta_integration/checker_invoker.py（246 行）
- 关键：CheckerBlocked 异常；CheckerLoadError；CheckerSpec 数据类；invoke_checkers(checker_ids, step_output, runtime_context) → list[dict]；三种 mode：off/warn/block，warn 默认；从 meta/user_overrides/checker_mode.yaml 加载 override；规则集 output_contains/output_missing/state_eq/output_word_count_lt；block 模式命中 → 写 error 级 audit + 抛 CheckerBlocked
- 下一步：P-3（dsl_parser）

## 2026-05-13T18:33:50+08:00 | P-3 完成
- 文件：platform/orchestrator/runner/dsl_parser.py（175 行）
- 关键：Workflow + Step dataclass；parse_workflow(path) / parse_workflow_dict(raw)；按 ARCHITECTURE §4.4 字段（id/uses_capability/uses_skill/preconditions/postconditions/state_reads/state_writes/description）；guard_ids()/checker_ids() helper 切分 "guard:" / "checker:" 前缀；uses_capability 与 uses_skill 互斥；duplicate id 拒绝；未识别字段透传到 Step.raw 兼容 P7-critical 未来扩字段
- 下一步：P-4（step_dispatch）

## 2026-05-13T18:34:55+08:00 | P-4 完成
- 文件：platform/orchestrator/runner/step_dispatch.py（238 行）
- 关键：StepFailed 异常；DispatchResult 数据类；dispatch_step(step, runtime_context, capability_registry, skill_registry, skill_router) 按 §4.2 顺序：guards → 解析 capability/skill → safe_call → apply state_writes（rejected 写 audit） → checkers；uses_skill="skill-router" 时调用注入的 skill_router 回调；state_writes 支持 wildcard ".*"；capability/skill 未注册 → S1 noop fallback；任何 capability 异常包成 StepFailed；任一 GuardBlocked/CheckerBlocked 直接向上抛
- 下一步：P-13（skill_router）

## 2026-05-13T18:36:00+08:00 | P-13 完成
- 文件：platform/orchestrator/router/skill_router.py（293 行）
- 关键：SkillRouter 类（可调用，__call__ 返回 skill_id）；RoutingDecision + SkillEntry dataclass；RouterError；读 registry.yaml + 每个 enabled skill 的 contract.yaml priority 段；受限 when 表达式解析器支持 `==/!=/in/not in`（不上 eval()）；变量映射 topic→locked.GENRE_LOCKED.topic / style_lock / premise，未映射的变量回落 runtime_context；list 在 list 用 any-in 语义（"玄幻黑暗" in topic[]）；fallback score=0 → default_writer；priority 缓存
- 下一步：unit tests

## 2026-05-13T18:36:36+08:00 | Tests 完成
- 文件：3 个 unit test
  - tests/test_dsl_parser.py（117 行，5 cases）
  - tests/test_state_io.py（97 行，5 cases）
  - tests/test_skill_router.py（147 行，4 cases）
- 关键：避开 stdlib `platform` 冲突（importlib.util.spec_from_file_location 加载）；全部 14 cases 都跑通；覆盖 read/apply/transaction/rollback/disk-reload + dsl roundtrip + duplicate-id + 互斥 + topic 路由 + fallback
- 下一步：跑 DoD + integration smoke

## DONE 2026-05-13T18:36:36+08:00

**交付文件清单（14 个 .py）**：

| 文件 | 行数 | P-N |
|---|---|---|
| platform/orchestrator/__init__.py | 11 | P-1 |
| platform/orchestrator/runner/__init__.py | 20 | P-1 |
| platform/orchestrator/runner/dsl_parser.py | 175 | P-3 |
| platform/orchestrator/runner/step_dispatch.py | 238 | P-4 |
| platform/orchestrator/runner/state_io.py | 341 | P-5 |
| platform/orchestrator/runner/tests/__init__.py | 1 | P-1 |
| platform/orchestrator/runner/tests/test_dsl_parser.py | 117 | Tests |
| platform/orchestrator/runner/tests/test_state_io.py | 97 | Tests |
| platform/orchestrator/runner/tests/test_skill_router.py | 147 | Tests |
| platform/orchestrator/meta_integration/__init__.py | 18 | P-1 |
| platform/orchestrator/meta_integration/guard_invoker.py | 206 | P-6 |
| platform/orchestrator/meta_integration/checker_invoker.py | 246 | P-7 |
| platform/orchestrator/router/__init__.py | 10 | P-1 |
| platform/orchestrator/router/skill_router.py | 293 | P-13 |
| **合计** | **1920 行** | |

**DoD 命令结果**：PASS（10 个目标文件全在 + 6 个核心模块 ast.parse 全过 + StateIO/transaction/audit_log/GuardBlocked/CheckerBlocked grep 全命中 + 3 个 test_*.py 列出）

**额外验证**：
1. `python3 platform/orchestrator/runner/tests/test_dsl_parser.py` → 5 cases OK
2. `python3 platform/orchestrator/runner/tests/test_state_io.py` → 5 cases OK
3. `python3 platform/orchestrator/runner/tests/test_skill_router.py` → 4 cases OK
4. Integration smoke：dsl_parser → dispatch_step → guard → fake skill adapter → state_writes 越权拦截 → audit_log 记录全链路 OK

**审查三问**：
- **Q1 接口兼容**：内部互调全部走显式 import；对外 P7-critical 的 capability/skill adapter 通过 dispatch_step 的 ``capability_registry`` / ``skill_registry`` / ``skill_router`` 参数注入，未注册时走 S1 noop fallback（不阻塞 P7-C）。skill_router 接受任何带 ``id`` 属性的对象作为 step（duck typing），不强绑 Step 类。dsl_parser 透传未知字段到 Step.raw，兼容 P7-C 未来扩 workflow YAML 字段。
- **Q2 边界处理**：StateIO 拒绝 ``audit_log.*`` 走 apply；拒绝未知顶层域；book_id 含 "/" 或 ".." 拒绝；空 path 拒绝；事务异常 rollback 并写 audit；apply 时整域替换要求 dict 类型；atomic write 用 tempfile + os.replace 防半截写。step_dispatch 越权 state_writes 被 reject 并写 audit。guard_invoker / checker_invoker 在 YAML 文件缺失时走 S1 noop（不抛错，保流水线在 meta 资产未齐时仍能跑）。skill_router 在 registry.yaml 不存在时返回空候选 → fallback。受限 when 解析器不上 eval()，避免代码注入。
- **Q3 Proper fix**：state_io 是 jury-1 P0 唯一入口，所有写操作必经它，audit_log 只能通过 ``audit()`` 追加而非 apply 改——这是工程红线 proper fix，不是 workaround。事务用 deep-copy snapshot + os.replace，是事务真实现而非"加个 try"。step_dispatch 的 state_writes 越权检测用白名单（含 wildcard）+ audit_log 记录，是 proper fix。唯一一处 fallback：`platform` 包名与 stdlib `platform` 冲突 → 测试用 `spec_from_file_location` 绕过 import 链。**这是技术债（见下方），不是 fix**。

**技术债记录（上报 P9）**：
1. **`platform` 顶层包名与 Python stdlib `platform` 模块同名**：导致 `from platform.orchestrator import ...` 在 Python ≥3.10 失败（stdlib 不是 namespace package，会被先解析）。当前测试通过 `importlib.util.spec_from_file_location` 直接按路径加载绕过。
   - **建议修复**（属于 P9 决策）：
     - 方案 A：在仓库根加 `platform/__init__.py`（lock map 内但属于 P7-D 未明示职责），需 P9 拍板谁来写。
     - 方案 B：把顶层包改名为 `ginga_platform/`，配合 ROADMAP 同步改 D-1/D-2 demo CLI 路径。
     - 方案 C：把 `platform/` 子树打包成 pip-installable package，pyproject.toml 暴露 `ginga_platform` 别名。
   - **影响范围**：D-1/D-2/D-4 demo CLI、所有 P7-critical 的 adapter（其 `from .skill_router import ...` 在 contract 里必经此路径）、未来 RAG 层接 platform 时也撞上。
2. **`meta/guards/` 与 `meta/checkers/` 目录现存空**：guard_invoker / checker_invoker 已实现 S1 noop fallback（文件缺失 → 视为永不命中），但 ROADMAP M-2 / M-3 的 P7-meta 任务出产后，需端到端联调一次。
3. **capability_registry / skill_registry 的注册机制目前是 dispatch_step 的参数**：S1 够用，S2 升级时建议 P7-D-2 改成 ``platform/orchestrator/registry.py`` 集中模块（避免 demo CLI 每次组装 dict）。
