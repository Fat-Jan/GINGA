# v1.7-7 Style Warn Productionization — 修订计划

## 问题诊断

v1.7-7 卡住的根因不是代码能力不足，而是**设计决策层面的矛盾**：

1. `abrupt_transition` 正则 `r"突然|猛然|下一秒"` 把中文动作叙事的常用词当作 hard fail
2. LLM 无法可靠地在 4000+ 字动作玄幻正文中完全避免这三个词（两次真实验证均失败）
3. 确定性后处理 `_rewrite_style_warn_terms` 已写好且第 1 章验证通过，但替换策略过于简单（`"突然" → "这时"` 可能造成语义断裂）

**核心决策**：`abrupt_transition` 不应该是 hard fail。它和 `generic_emotion`、`cliche_metaphor` 不同——后两者确实是 AI 味标志，而"突然/猛然/下一秒"是正常中文叙事用词，只是频率过高时才有问题。

## 修订方案

把 style warn 分为两级：

- **hard_style_warn**（阻断生成）：`generic_emotion` + `cliche_metaphor` — 这些是真正的 AI 味标志
- **soft_style_warn**（只报告不阻断）：`abrupt_transition` — 正常用词，高频时报 warn

同时保留 `_rewrite_style_warn_terms` 作为 best-effort 后处理：对 hard 类做确定性替换（必须清零），对 soft 类做 best-effort 替换（能替则替，不阻断）。

## 拆分为两个子任务

### v1.7-7a：代码修改（可派 Codex，纯离线）

**目标**：修改 quality gate 逻辑，把 style warn 分级 + 完善确定性后处理

**具体改动**：

1. `immersive_runner.py` 的 `_style_warn_hits()` 返回值增加 severity 信息
2. `_quality_gate_failure()` 只把 hard_style_warn（generic_emotion + cliche_metaphor）计入 failure
3. `_rewrite_style_warn_terms()` 改进：
   - hard 类（generic_emotion / cliche_metaphor）：保持现有替换，这些必须清零
   - soft 类（abrupt_transition）：做 best-effort 替换但不要求清零
   - 替换 `"突然"` 时检查是否在句首（句首 → `"这时"` 合理）vs 句中（句中 → 删除或改为 `"倏地"`）
4. `longform_policy.py` 的 `longform_chapter_gate_check()` 增加 `soft_style_warn` 字段（只报告）
5. 更新所有相关单测

**DoD**：
```bash
python -m unittest discover -s ginga_platform -p "test_*.py"
python3 scripts/verify_all.py --quick
```
两个命令 exit 0。

**写范围**（lock map）：
- `ginga_platform/orchestrator/cli/immersive_runner.py`
- `ginga_platform/orchestrator/cli/longform_policy.py`
- `ginga_platform/orchestrator/runner/tests/test_immersive_mode.py`
- `ginga_platform/orchestrator/runner/tests/test_story_truth_template.py`（如果有 style warn 相关断言）

**禁止**：
- 不改 `demo_pipeline.py` 的 prompt 构造逻辑（那是 v1.7-6 已验证的）
- 不改 `review.py`（review 的 style fingerprint 是 report-only，不受影响）
- 不跑真实 LLM
- 不改 `StateIO` 或 `state_io.py`
- 不改 `longform_policy.py` 的 hard gate（opening_loop / low_frequency_anchor / foreshadow）

### v1.7-7b：真实 LLM 验证（需要主 agent 或人工执行）

**前置条件**：v1.7-7a 的代码已提交且 `verify_all.py` 通过

**执行**：
```bash
cd /Users/arm/Desktop/ginga
python3 scripts/run_real_llm_harness.py --run --chapters 4 --state-root .ops/real_llm_harness/v1-7-7b-final-state
```

**DoD**：
- 4/4 章落盘
- 每章正文汉字数 ≥ 3500
- hard_style_warn hits = 0（generic_emotion + cliche_metaphor 清零）
- soft_style_warn 可以有少量 hits（只报告）
- review hard gate `should_block_next_real_llm_batch=false`
- drift_report.status = stable 或 needs_review（不是 failed）

**fallback**：
- 如果 4 章中有章节因 hard_style_warn 失败 → 检查 `_rewrite_style_warn_terms` 的 hard 类替换是否覆盖了新出现的变体，补充替换表
- 如果因 short_chapter 失败 → 这是独立问题，不属于 v1.7-7 范围
- 如果因 opening_loop 失败 → 这是独立问题，不属于 v1.7-7 范围
- 如果久久 504 → 等模型恢复后重跑，不改代码

## 为什么这个方案不会让 Codex 死循环

1. **v1.7-7a 是纯离线任务**：不依赖真实 LLM，不依赖网络，不依赖模型稳定性。Codex 只需要改代码 + 跑单测。
2. **DoD 是确定性的**：`unittest` + `verify_all.py` exit 0，没有模糊判断。
3. **写范围明确**：4 个文件，不会踩到其他模块。
4. **设计决策已经做好**：不需要 Codex 判断"突然应不应该是 hard fail"——这个决策已经在本计划里定了。
5. **v1.7-7b 不派 Codex**：真实 LLM 验证由主 agent 或人工执行，避免 Codex 因网络/模型问题卡死。

## 状态

`planned` → 等用户确认后派 v1.7-7a 给 Codex
