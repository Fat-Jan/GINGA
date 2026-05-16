# Codex GPT-5.4 执行 Sprint 2 收尾任务

> 历史 prompt：Sprint 2 收尾任务已完成；不要按本文重新执行。当前状态以 `STATUS.md` 为准。

## 推荐配置

**模型**：GPT-5.4（OpenAI o3-mini 或同等）  
**思考强度**：**medium**（平衡速度与可靠性）

**理由**：
- Task 1（5 章 demo）：流程机械（init → run → 验收），无复杂决策，medium 足够捕获 endpoint 故障 + fallback 逻辑
- Task 2（196 张 annotate）：纯流水线，脚本已内置 failover，low 理论可行但 medium 更稳（遇异常能自主判断）
- high 过重：这两条任务都是"执行已验证流程"，不需要深度推理或架构设计

---

## 给 Codex 的完整 Prompt

```markdown
你是 Codex，负责完成 ginga 项目 Sprint 2 的两条收尾任务。

## 上下文
- 项目路径：/Users/arm/Desktop/ginga
- 主 agent（Claude Opus 4.7）已完成 Sprint 2 核心代码 + 测试（105/105 PASS），因网络中断 + endpoint 故障留下两条收尾任务
- 详细 handoff：@/Users/arm/Desktop/ginga/.ops/archive/handoff-to-codex-sprint2-remaining.md（必读）

## 你的任务（按优先级）

### Task 2（优先，立即可启动）：L Track 剩余 196 张 prompt card annotate
- 当前进度：265/461 完成
- 执行命令：
  ```bash
  cd /Users/arm/Desktop/ginga
  python3 scripts/annotate_prompt_card.py \
    .ops/sprint-2/queue-remaining.json \
    --batch-size 196 \
    --offset 155 \
    > .ops/sprint-2/L-batch-final.stdout \
    2> .ops/sprint-2/L-batch-final.stderr
  ```
- 验收：`grep -c '"status": "ok"' .ops/sprint-2/annotation-progress.jsonl` 应 = 461
- 预计耗时：30-45 min
- Fallback：脚本内置 windhub → ioll-grok 自动切换

### Task 1（次优先，endpoint 恢复后）：P7-S 真实 5 章 demo 重跑
- 前置检查：`ask-llm windhub "test" --max-tokens 64`（exit=0 才继续）
- 执行步骤：
  ```bash
  cd /Users/arm/Desktop/ginga
  rm -rf foundation/runtime_state/s2-demo
  python3 -m ginga_platform.orchestrator.cli init s2-demo \
    --topic "玄幻黑暗" \
    --premise "宗门弃徒踏入黑雾遗迹寻回血脉真相，五章呈现五个镜头" \
    --word-target 17500
  python3 -m ginga_platform.orchestrator.cli run s2-demo \
    --chapters 5 \
    --llm-endpoint windhub \
    --word-target 3500
  ```
- 验收：stdout 包含 `✅ multi_chapter done: 5/5 chapters, DoD PASS`
- 预计耗时：10-15 min
- Fallback：若 windhub 持续故障 → 切 `--llm-endpoint ioll-grok`

## 执行策略
1. **并行启动**：Task 2 先跑（后台），Task 1 等 endpoint 恢复后跑（写范围互斥，无冲突）
2. **心跳协议**：每 10 分钟或关键步骤追加心跳到 `.ops/archive/handoff-to-codex-sprint2-remaining.md`
3. **失败处理**：任一 task 失败必须写明原因 + 已尝试 fallback，不静默放弃

## 红线（P0，违反立即停止）
- 不改已完成产物（`immersive-demo/` / `demo-book/` / 代码 / 测试）
- 不跳过验证（DoD 必须跑完）
- 不静默失败（失败必须留 handoff 记录）

## 交付清单
- [ ] Task 2: 461 个 `prompts-card-*.md` + 461 行 jsonl + stderr `batch done`
- [ ] Task 1: 5 个 `chapter_NN.md`（每个 ≥3000 bytes）+ stdout `DoD PASS`
- [ ] 心跳记录：`.ops/archive/handoff-to-codex-sprint2-remaining.md` 追加进度
- [ ] 无回归：已完成产物（immersive-demo / 测试）零改动

## 开始执行
按 Task 2 → Task 1 顺序推进。遇阻塞立即写 handoff + 等主 agent 决策，不自行发散。
```

---

## 补充说明

**为什么 medium 不是 low**：
- Task 1 的 endpoint EAGAIN 是真实故障（不是代码 bug），需要 Codex 判断"重试 vs 切 endpoint"
- Task 2 的 196 张虽然流水，但若遇 3 连 fail 需要 Codex 判断是否暂停（而不是盲目重试 196 次）
- medium 思考强度能覆盖这类"执行中异常判断"，low 可能机械重试到超时

**为什么不是 high**：
- 没有架构设计、算法优化、复杂 debug 需求
- 流程已验证（18 tests PASS + 265 张已成功），只是"跑完剩下的"
- high 会浪费时间在过度思考"是否有更好的方案"上

**使用方式**：
把上面 "给 Codex 的完整 Prompt" 那段（markdown 代码块内容）粘给 Codex 即可。
