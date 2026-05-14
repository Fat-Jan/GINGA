# ST-S1-META：Meta 层 constitution + guards + checkers（P7-B）

## 你是谁

你是 ginga 项目 Sprint 1 的 **P7-meta 骨干**。主 agent 是 P9 tech lead，不下场写代码，只验收。你独立完成自己的 task slice，不串供其他 P7。

## 项目一句话背景

ginga = 把 `_原料/` 蒸馏成分层小说创作系统底座；Meta 层 = 创作宪法 + guard（前置硬阻断）+ checker（后置软审计 warn-only 默认）。

## 必读输入（按顺序读）

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` §二 Meta 层 + §〇 Killer Use Case
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §1.2.2 Meta 子任务 M-1..M-4
3. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout2-doctrine.md`（25KB，**20 条上位法的真源**，重点读 §2 创作宪法段）
4. `/Users/arm/Desktop/ginga/.ops/jury/jury-3-novel-editor.md`（P1 要求 checker warn-only 默认）

## 你的写范围（lock map，硬约束）

**你只能写**：
- `meta/constitution.yaml`
- `meta/guards/*.yaml`（3 个核心 guard）
- `meta/checkers/*.yaml`（3 个核心 checker）
- `meta/user_overrides/checker_mode.yaml`
- `.ops/p7-handoff/ST-S1-META.md`（心跳 + 完成报告）

**你绝不写**：
- `foundation/**`（P7-foundation 范围）
- `platform/**`（P7-platform-* 范围）
- 任何架构 / 路线图 / 看板 / 原料

## 任务清单

按 ROADMAP §1.2.2：

- [ ] **M-1**：`meta/constitution.yaml`：20 条上位法主索引
  - 字段：`version` / `articles[]`（每条含 `id` / `category` / `text` / `triggers` / `enforcement_via`）
  - 来源：scout-2 §2 创作宪法 20 条（按工作纪律 4 条 + 创作约束 16 条分组）
  - **不许复制粘贴**，必须读完 scout-2 提炼

- [ ] **M-2**：3 个 guard YAML 文件（前置硬阻断，不可关闭）：
  - `meta/guards/no-fake-read.guard.yaml`（防伪造：声称读了但没读）
  - `meta/guards/latest-text-priority.guard.yaml`（防过时：用陈旧上下文）
  - `meta/guards/crosscheck-required.guard.yaml`（防迷信：单源结论无交叉验证）
  - 每个 guard 字段：`id` / `description` / `trigger_when` / `enforcement` (`block` / `error`) / `error_message` / `bypass_allowed: false`

- [ ] **M-3**：3 个 checker YAML 文件（后置软审计，默认 warn-only）：
  - `meta/checkers/aigc-style-detector.checker.yaml`
  - `meta/checkers/character-iq-checker.checker.yaml`
  - `meta/checkers/cool-point-payoff-checker.checker.yaml`
  - 每个 checker 字段：`id` / `description` / `target_state_field` / `check_logic` (LLM-prompt-based 或 rule-based) / `default_mode: warn` / `severity_levels: [info, warn, block]` / `override_via: meta/user_overrides/checker_mode.yaml`

- [ ] **M-4**：`meta/user_overrides/checker_mode.yaml`：作家个性化开关模板
  - 字段：`checker_overrides: { <checker_id>: { mode: off | warn | block } }`
  - 默认值：3 个 checker 全 mode=warn
  - 含注释说明"作家可以把任何 checker 设为 off 或升级为 block"

## 输出契约

**constitution.yaml 范例**（必读 scout-2 后填充真实条款）：

```yaml
version: "1.0"
source: scout-2-doctrine.md §2
articles:
  - id: const-001
    category: 工作纪律
    text: "禁伪造：声称读了文件但实际未读，必触发 no-fake-read.guard"
    triggers:
      - file_read_claim_without_evidence
    enforcement_via: meta/guards/no-fake-read.guard.yaml

  - id: const-014
    category: 创作约束 / 爽点节奏
    text: "爽点必须有因果闭环，不能空降结果"
    triggers:
      - chapter_climax_payoff
    enforcement_via: meta/checkers/cool-point-payoff-checker.checker.yaml
  # ... 共 20 条
```

**guard 范例**：

```yaml
id: no-fake-read
description: "防伪造：禁止声称读了某文件但实际未读"
trigger_when:
  step.preconditions.includes: guard:no-fake-read
enforcement: block
error_message: "Step <step_id> 声明读取 <file>，但 audit_log 中无对应 read_event"
bypass_allowed: false
```

**checker 范例**：

```yaml
id: aigc-style-detector
description: "检测章节正文是否带 AI 套话（'综上所述' / '总而言之' / '让我们' 等）"
target_state_field: runtime_state.entity_runtime.chapter_text
check_logic:
  type: rule-based
  rules:
    - pattern: "综上所述|总而言之|让我们一起"
      severity: warn
default_mode: warn
severity_levels: [info, warn, block]
override_via: meta/user_overrides/checker_mode.yaml
```

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  test -f meta/constitution.yaml && \
  test -f meta/guards/no-fake-read.guard.yaml && \
  test -f meta/guards/latest-text-priority.guard.yaml && \
  test -f meta/guards/crosscheck-required.guard.yaml && \
  test -f meta/checkers/aigc-style-detector.checker.yaml && \
  test -f meta/checkers/character-iq-checker.checker.yaml && \
  test -f meta/checkers/cool-point-payoff-checker.checker.yaml && \
  test -f meta/user_overrides/checker_mode.yaml && \
  grep -q 'articles:' meta/constitution.yaml && \
  [ "$(grep -c 'id: const-' meta/constitution.yaml)" -ge 20 ] && \
  for f in meta/guards/*.yaml; do
    grep -q 'enforcement: block' $f || { echo "guard $f 不是 block"; exit 1; }
    grep -q 'bypass_allowed: false' $f || { echo "guard $f 允许 bypass"; exit 1; }
  done && \
  for f in meta/checkers/*.yaml; do
    grep -q 'default_mode: warn' $f || { echo "checker $f 默认 mode 不是 warn"; exit 1; }
  done && \
  echo PASS || echo FAIL
```

## 心跳协议

完成每个 M-N 任务后立即追加（不覆盖）到 `.ops/p7-handoff/ST-S1-META.md`：

```
## 2026-05-13THH:MM:SS+08:00 | M-N 完成
- 文件：<path>
- 字节：<size>
- 关键：<eg. 20 条宪法 / 3 个 guard / mode 默认 warn>
- 下一步：M-<N+1>
```

启动时先写一条 `## START` 含计划。完成全部 8 个文件后写 `## DONE` + 验收命令结果。

## 红线

- **不批量脚本**：不许用 sed/awk/Python 脚本批量生成；逐个 Write
- **20 条宪法必须真实提炼**：从 scout-2 §2 读全文 → 提炼 20 条，不许凑数 / 编造
- **不动 lock map 外文件**
- **不串供**：不读其他 P7 的 handoff
- **失败 ≤3 次**：超过 → 写 `## BLOCKED` + stop

## fallback

scout-2 §2 创作宪法段长达 ~5KB，可能 20 条不止 / 不全。处理：
1. 优先抽 jury-3 + jury-1 引用的核心条款（如"角色降智""爽点兑现因果闭环""窄通道气质"等）
2. 若发现不足 20 条 → 补"工作纪律 4 条（防伪造 / 防过时 / 防迷信 / 防 emoji）"
3. 仍不够 → 写 `## QUESTION` 给主 agent 决策

## 完成判据

```
✅ 8 个目标文件全在
✅ 验收命令 PASS
✅ constitution.yaml ≥20 条 articles
✅ 3 guard 都 enforcement=block + bypass=false
✅ 3 checker 都 default_mode=warn
✅ user_overrides 模板完整
✅ 心跳协议每步都写了
```

启动！第一步：读 scout-2-doctrine.md §2 创作宪法段。
