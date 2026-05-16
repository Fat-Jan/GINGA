# Ginga 蒸馏项目 — 交接给 Codex（Scout 阶段救火 · 第 2 版）

## 当前状态（2026-05-13 02:00）

| Scout | 状态 | 证据 |
|---|---|---|
| scout-1-base | ✅ validating | `.ops/scout-reports/scout1-base.md` 30420B / 8 H2 / 50 文件实读，Codex 12m51s 完成 |
| scout-2-doctrine | ✅ validating | `.ops/scout-reports/scout2-doctrine.md` 25139B / 7 H2 / 3 文件全读，Codex 10m50s 完成 |
| scout-3-cards | ❌ zombie | Codex job `task-mp2wvstc-dbrd5c` 卡 `Turn started` 27 分钟无 log 推进，主 agent kill；attempt 2/2 用尽，**用户已批准破例第 3 次手动重派** |
| scout-4-pipeline | ✅ 已完成（首轮就过了） | `.ops/scout-reports/scout4-pipeline.md` 14822B |

主 agent 自此交接：**仅剩 scout-3 一项**。

---

## 你（Codex）这次只干一件事

把 `_原料/提示词库参考/prompts/` 475 个 JSON-style md 横扫完，产出 `.ops/scout-reports/scout3-cards.md`。

任务 brief 完整版：`.ops/scout-prompts/scout3.md`（自包含、深度详尽，**第一步读这个**）。

---

## 启动命令（用户手动执行）

**Scope override**：本次重派把 scout3.md 中"不要全部 475 读（不现实）"的原抽样指令**升级为全量 475 实读**（用户 2026-05-13 02:30 决策）。原因：分层抽样会漏掉低频但高价值的 task 类型，全量才能把任务类型聚类和质量分级做实。Codex 子进程有独立 200K 上下文窗，475 文件 × 平均 1.5KB ≈ 700KB ≈ 175K tokens，刚好能装下，写报告时压力较大但可行。

时间估算：~90-150 分钟（按 scout-1 的 12m51s/50 文件单位时间外推），超过 30 分钟无 log 推进 = zombie。

```bash
cd /Users/arm/Desktop/ginga && \
node "/Users/arm/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs" \
  task --background --write --fresh \
  "你是 ginga 小说蒸馏项目的 Scout 3。工作目录 /Users/arm/Desktop/ginga。

第一步：读 /Users/arm/Desktop/ginga/notepad.md 的 ## Priority Context 段。
第二步：读 /Users/arm/Desktop/ginga/.ops/scout-prompts/scout3.md（完整 brief）。**但本次 scope override：scout3.md 写的'不要全部 475 读'已被用户推翻，本次必须全量 475 文件每个都实读全文**。
第三步：全量横扫 _原料/提示词库参考/prompts/ 全部 475 个 md，**每一个都打开读全文**（不是只看文件名/只读前几行）。建议工作节奏：批量 ls + 排序 → 分段（如每 50 个一段）顺序读完，期间用 grep 抽 task 字段、标题、JSON header 做汇总台账。写报告到 /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md。

核心产出：
- **任务类型聚类**：覆盖全部 475 文件的 task 字段值（频次表 + 长尾低频 type 单列）
- **JSON-style schema 抽取**：必填/可选/类型/取值范围，基于全量统计
- **场景卡片 schema 草案**：YAML frontmatter + JSON content
- **与基座去重分析**：抽 30-50 个 prompts/ 题材/场景，grep /Users/arm/Desktop/ginga/_原料/基座/ 看是否对应，给 retain/merge/drop 标记（数量从原 20 升到 30-50，匹配全量 scope）
- **质量分级**：≥40 个文件 A/B/C 评分 + 理由（数量从原 20 升到 40，匹配全量 scope）
- **RAG 召回元数据设计**：按 task 类型 / 题材 / 使用场景的过滤建议

报告必须包含以下 H2 章节：
## 任务类型聚类 / ## JSON-style schema 抽取 / ## 场景卡片 schema / ## 与基座去重分析 / ## 质量分级与 retain/merge/drop 建议 / ## RAG 召回元数据设计 / ## 关键发现与建议

参考深度模板：.ops/scout-reports/scout4-pipeline.md（14KB）和 .ops/scout-reports/scout1-base.md（30KB）。目标输出深度：35-50KB（因为全量 scope 比 scout-1 更广）。

红线：
- 必须全量 475，不允许漏读任何一个文件
- 不允许只看文件名做聚类（task 字段在 JSON 内容里，必须实读）
- 不允许扩范围到基座 / 思路 / 小说提示词 2 目录
- 不允许改 .ops/subagents/board.json（看板由主 agent 改）
- 上下文压力大时可以分批做：第一遍 grep 全量抽 task 字段做台账，第二遍按 task 类型分桶逐个读完整文件
- 用户原话：不要省事，多花时间

完成后报告：报告路径 + 实际读取的文件总数（确认 = 475）+ Top 10 task 类型频次 + 总字数 + 长尾低频 task 类型清单。

【强制】干活过程中持续追加进度到 /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md（文件不存在就建，存在只 append 不覆盖，绝不用 sed/awk 改写）。触发条件：(1) 启动时写一条 START；(2) 每读完 50 个文件；(3) 每个 H2 章节开始/完成草拟；(4) 每发现新的或罕见的 task 类型；(5) 每发现一处与基座的明显重叠/冲突；(6) 任何工具失败或上下文压力告警；(7) 完成时写一条 DONE。格式协议（包含里程碑标题、已读 N/475、当前阶段、累计发现、下一步、异常）的完整版见 /Users/arm/Desktop/ginga/.ops/archive/handoff-to-codex.md 的『进度流式回写协议』章节——你必须先读那段，然后照样追加。主 agent 会用 tail 监控；20 分钟没新 entry 视同 zombie。" 2>&1
```

返回会立刻给你一个 `task-XXXXXXXX-XXXXXX` job id。

## 进度流式回写协议

codex 在干活过程中**必须**实时往 `.ops/scout-reports/scout3-progress.md` 追加进度。这是给主 agent 远程监控用的，不进 codex 上下文也能看推进。

### 文件位置
`/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md`（不存在则首次追加时自动创建）

### 写入约束
- **只能 append**，绝不覆盖已有内容
- 推荐工具：codex 的 Edit 工具在文件末尾插入，或 `zsh -lc 'cat >> /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md << "EOF"'`
- 严禁 sed / awk / Write 整体重写
- 时间戳用 `date +%Y-%m-%dT%H:%M:%S%z`

### 触发条件（达到任一立刻追加）
1. **启动**：写 `## START`，确认 scope（全量 475）+ 工作计划
2. **每读完 50 个文件**：累计 ~10 条这类 entry（475/50 ≈ 9.5）
3. **每个 H2 章节**：开始草拟 + 完成草拟，各一条
4. **每发现新 / 罕见 task 类型**：单独一条，附文件 id
5. **每发现一处与基座的明显重叠 / 冲突**：单独一条，附两端文件 id
6. **任何工具失败 / 上下文压力 / 决策犹豫**：单独一条
7. **完成**：写 `## DONE`，汇总最终统计

### Entry 格式

```
## [ISO 时间戳] [里程碑标题]
- 已读：N/475 文件
- 阶段：[文件扫描 / task 聚类 / schema 抽取 / 去重分析 / 质量分级 / RAG 元数据 / 报告写作]
- 累计发现：[简短列表，如"新 task 类型 +3：xxx / yyy / zzz"]
- 下一步：[一句话]
- 异常 / 阻塞：[无 或 描述]
```

### 主 agent 端监控

主 agent 周期跑：
```bash
tail -60 /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md
wc -l /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md
date -r /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-progress.md +%Y-%m-%dT%H:%M:%S%z
```

20 分钟无新 entry → 视同 zombie，kill 并诊断。

## 跟踪与回收

```bash
# 看进度（替换 <jobid>）
node "/Users/arm/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs" status <jobid>

# 看全部
node "/Users/arm/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs" status --all

# 拿最终输出
node "/Users/arm/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs" result <jobid>

# zombie 时强 kill
node "/Users/arm/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs" cancel <jobid>
```

**Zombie 判定**（全量 scope 调整版）：
- 启动后 ≥15 分钟仍 `phase: starting`、无 `Running command` log → kill（真没动）
- 跑动后任意时刻 log 无新 `Running command` / `Reasoning summary` 推进 **≥20 分钟** → kill（卡死中段，全量 scope 阅读密集，正常情况下应该每分钟都有命令）
- 总 elapsed 超过 **180 分钟** 且未完成 → kill 并人工介入决策

日志路径在 status 输出的 `Log:` 字段，用 `tail -50 <log>` 直接看。如果看见持续的 `Running command: ... cat /Users/arm/Desktop/ginga/_原料/...` 不要 kill，那是正常进度。

## 验证（codex 完成后跑）

```bash
test -f /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md && \
grep -q '## 与基座去重分析' /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md && \
grep -q '## 场景卡片 schema' /Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md && \
echo PASS || echo FAIL
```

主 agent（Claude）后续会做的事：
1. 跑 verification（结构）
2. Read 报告抽样 20-50 行（内容质量）
3. 看板 `scout-3-cards.status` 推 `validating → done`
4. 顶层 `updated_at` + `evidence` 数组追加
5. 触发阶段 2（综合 4 scout 报告 → `_distillation-plan.md`）

---

## Executor 选择规则（本次救火的核心教训）

底层真源：`.ops/subagents/dispatch-protocol.md`。本节只保留 Scout 救火时期的具体事故记录；后续派活以 dispatch protocol 为准。

### 同一波 Claude API 故障下的真独立 fallback 路径

| 路径 | 是否真独立 sandbox | 是否会被 Claude API/dzzzz 网关 502 拖垮 |
|---|---|---|
| `Agent(subagent_type=general-purpose)` | ❌ 走 Claude API | ✅ 会 |
| `Agent(subagent_type=codex:codex-rescue)` | ❌ **仍走 Claude API**（Claude wrapper 调 codex via Bash） | ✅ 会 |
| 直接 Bash 调 `codex-companion task --background --write` | ✅ 真独立（自定义 OpenAI 端 + unix socket broker） | ❌ 不会 |
| `codex resume <session-id>` 手动直跑 | ✅ 真独立 | ❌ 不会 |

**口诀**：Claude 框架内的子代理（包括叫 codex- 名字的）都走 Claude API；真独立 = 跳出 Claude 命令链，直接 Bash 启动本机 codex CLI 进程。

### codex-companion task 命令的关键 flag

- `--write`：**必须显式加**，否则 codex CLI 默认是只读沙箱，写不了报告
- `--background`：后台执行，立刻拿到 job id，不阻塞当前 Claude 会话
- `--fresh`：新建 thread；省略默认沿用上一个 task 的 thread（会污染上下文）
- `--resume`：续上一个 thread；只在显式续命时用

### 本次救火完整时间线（避免下次踩坑）

- 22:50（5/12）：4 scouts 首派，全 `assigned` 但实际未真正进入 running（Claude harness 调度问题）
- 23:30：原 checkpoint_due_at 过期，scout-1/2/3 stale 25h（scout-4 凌晨 23:52 莫名补完）
- 01:06（5/13）：主 agent 用 `Agent(subagent_type=general-purpose)` 重派 3 个 scout
- 01:18：三个 agent 同一波 Cloudflare 502 在 ai.dzzzz.cf 上集中故障，0 token / 0 tool_uses，10 分钟全死
- 01:21：看板回滚 `attempt_count`，切换 executor
- 01:33：错误选了 `Agent(subagent_type=codex:codex-rescue)`，**它本质是 Claude wrapper**，再 502
- 01:35：识别错误，改用直接 Bash 调 `codex-companion task --background --write`
- 01:46–01:48：scout-1/2 codex CLI 跑通完成，质量过关
- 02:00：scout-3 codex CLI 卡 27 分钟 zombie，kill
- **未来**：用户手动跑上述启动命令重派 scout-3

---

## 看板更新协议（保留原协议）

主 agent / codex 任何角色更新 `.ops/subagents/board.json` 必须：
1. 用 Edit 工具逐字段改，**不用 sed/awk/jq -e 批量替换**
2. 更新 `tasks[i].updated_at` + 顶层 `updated_at`
3. 子代理只能写到 `validating`，`done` 由主 agent 复核证据后写

状态机：`queued → assigned → running → validating → done`，异常 `stale / zombie / retry_wait / failed`。

## 红线

- 不要自判 done
- 不要扩范围（4 层架构 / jury 法庭 / 阶段 2~4 不归本任务）
- 不要批量脚本改文件
- 不要伪造证据（没有报告文件就不能标 validating）
- 保留 `.ops/scout-prompts/` 只读

## 完成判据

- `ls .ops/scout-reports/` 显示 scout{1,2,3,4} 全在
- `jq '.tasks[] | select(.task_id|startswith("scout"))|{id:.task_id,status}' .ops/subagents/board.json` 全部 `validating` 或 `done`
- scout-3 报告过 verification 命令
- 给一句话总结：哪些异常需要主 agent 注意
