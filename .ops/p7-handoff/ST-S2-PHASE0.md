# ST-S2-PHASE0 心跳记录

## START

- 时间：2026-05-13T19:52:30+08:00
- 任务：capability_registry + op_translator + 12 step 集成 spike
- 计划：P0-1 (registry/capability_registry.py + 7 stub) → P0-2 (runner/op_translator.py + 4 op) → P0-3 (test_integration_12step.py)
- 写范围：registry/ + runner/op_translator.py + tests/ (lock map 内)
- 关键设计：
  - capability stub 返回 {result, state_updates: flat dict} 走 step_dispatch._apply_state_writes
  - op_translator 用于 G_chapter_draft 调 dark-fantasy adapter 后的转换；签名 (ops, state_io) 支持 delta/append 读旧值
  - chapter_text 顶层无对应 state_io 域，integration 用 workspace.chapter_text；op_translator 提供 chapter_text → workspace.chapter_text 映射


## 2026-05-13T19:54:00+08:00 | P0-1 完成

- 文件：
  - ginga_platform/orchestrator/registry/__init__.py (10 行)
  - ginga_platform/orchestrator/registry/capability_registry.py (374 行)
  - ginga_platform/orchestrator/runner/tests/test_capability_registry.py (123 行)
- 关键：
  - CapabilityRegistry 支持 register / list_capabilities / resolve / call + Mapping 协议 (__contains__/get/__len__)，可直接喂 step_dispatch 的 capability_registry 参数
  - from_defaults() 注册 12 个 mock stub（>= 7 要求）：A_brainstorm / B-F / G default writer / H / R1-3 / V1 全覆盖
  - stub 输出 {result, state_updates: flat dict}，state path 顶层全部在合法 state_io 域 (locked / entity_runtime / workspace / retrieved)
  - deepcopy 隔离每次 call 的 state_updates，避免共享引用
- 验证：9 unit test PASS，from_defaults().list_capabilities() = 12 caps
- 下一步：P0-2 op_translator

## 2026-05-13T19:56:00+08:00 | P0-2 完成

- 文件：
  - ginga_platform/orchestrator/runner/op_translator.py (242 行)
  - ginga_platform/orchestrator/runner/tests/test_op_translator.py (375 行)
- 关键：
  - 签名 `adapter_ops_to_state_updates(ops, state_io)` 接 dark-fantasy adapter.output_transform 返回的 list-of-ops
  - 4 op 全实现：write / delta(numeric+dict merge) / append / append_or_update(by key match)
  - path 规范化三规则：剥 `runtime_state.` 前缀 / 顶层合法域原样 / 裸 chapter_text 映射到 workspace.chapter_text
  - 同 path 多 op 链式合并：pending dict 内中间值参与后续算（避免 apply 时被覆盖）
  - fail-loud：未知 op / 路径非法 / 类型不兼容都抛 OpTranslationError
- 验证：22 unit test PASS（含 E2E adapter-shape 模拟）
- 下一步：P0-3 12 step integration test
