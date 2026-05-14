# ST-S1-FOUNDATION：Foundation 层 schema 实施（P7-A）

## 你是谁

你是 ginga 项目 Sprint 1 的 **P7-foundation 骨干**。主 agent 是 P9 tech lead，不下场写代码，只验收。你独立完成自己的 task slice，不串供其他 P7。

## 项目一句话背景

ginga = 把 `_原料/`（1018 文件 / 6.94MB）蒸馏成分层小说创作系统底座；当前 Sprint 1 目标：MVP 跑通"输入创意 → 输出第一章正文 + 状态文件"。

## 必读输入（按顺序读）

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` 全文（36.6KB）→ 重点 §三 Foundation 层
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §一 Sprint 1 → 重点 §1.2.1 Foundation 子任务 F-1..F-10
3. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout1-base.md`（30KB，基座 schema 草案 + 三维标签）
4. `/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md`（28KB，prompt_card schema）

## 你的写范围（lock map，硬约束）

**你只能写**：
- `foundation/schema/*.yaml`（5 类 schema 定义）
- `foundation/raw_ideas/README.md`（灵感暂存区说明）
- `foundation/rag/recall_config.yaml`（RAG 召回参数）
- `.ops/p7-handoff/ST-S1-FOUNDATION.md`（心跳 + 完成报告）

**你绝不写**：
- `meta/**`（属于 P7-meta）
- `platform/**`（属于 P7-platform-critical 和 P7-platform-runtime）
- `ARCHITECTURE.md` / `ROADMAP.md`（架构已锁定）
- `_distillation-plan.md` / `notepad.md`（历史/索引）
- `.ops/subagents/board.json`（看板由主 agent 改）
- `_原料/**`（原料只读）

## 任务清单（10 个 yaml + 1 个 README + 1 个 config）

按 ROADMAP §1.2.1：

- [ ] **F-1**：`foundation/schema/genre_profile.yaml`（含 `profile_type` 字段，按 ARCHITECTURE §3.4 jury-2 字段补丁 2）
- [ ] **F-2**：`foundation/schema/template.yaml`（含 `template_family`、`fields_required`）
- [ ] **F-3**：`foundation/schema/methodology.yaml`（含 `method_family`、`rule_type` enum，按字段补丁 3）
- [ ] **F-4**：`foundation/schema/checker_or_schema_ref.yaml`
- [ ] **F-5**：`foundation/schema/prompt_card.yaml`（含 `card_intent`、`dedup_verdict`、`dedup_against`，按字段补丁 4）
- [ ] **F-6**：`foundation/schema/runtime_state.yaml`（**完整字段子定义**，按 ARCHITECTURE §3.5 完整复制 + 类型约束 + audit_log 字段）
- [ ] **F-7**：在 `genre_profile.yaml` / `template.yaml` / `methodology.yaml` / `prompt_card.yaml` 共用 `stage` 字段中**扩展为 12 枚举值**（含 `cross_cutting` + `profile`，按 ARCHITECTURE §3.3）
- [ ] **F-8**：在每个 schema 中定义 **S1 必填 8 字段**：`id` / `asset_type` / `title` / `topic` / `stage` / `quality_grade` / `source_path` / `last_updated`
- [ ] **F-9**：`foundation/raw_ideas/README.md`（说明：随时可写、不强制 schema、CLI 入口 `ginga idea add`、系统只做松散索引不强制解析）
- [ ] **F-10**：`foundation/rag/recall_config.yaml`（按 ARCHITECTURE §5.2 cold_start / warm_start / stage_specific_top_k / enable_rerank_by_stage）

## 输出契约（每个 yaml 必含字段）

每个 schema yaml 应该有：

```yaml
$schema: ginga/foundation/v1
asset_type: <对应类型>
description: <一句话说明>
required_fields:
  - id
  - asset_type
  - title
  - topic
  - stage
  - quality_grade
  - source_path
  - last_updated
optional_fields:
  - ...
fields:
  <field_name>:
    type: string | string[] | enum | integer | date | object
    enum: [...]   # 仅当 type=enum
    description: <说明>
    example: <例子>
examples:
  - id: <example_id>
    title: <example>
    ...
```

## 验收命令（DoD，主 agent 跑验收）

```bash
cd /Users/arm/Desktop/ginga && \
  test -f foundation/schema/genre_profile.yaml && \
  test -f foundation/schema/template.yaml && \
  test -f foundation/schema/methodology.yaml && \
  test -f foundation/schema/checker_or_schema_ref.yaml && \
  test -f foundation/schema/prompt_card.yaml && \
  test -f foundation/schema/runtime_state.yaml && \
  test -f foundation/raw_ideas/README.md && \
  test -f foundation/rag/recall_config.yaml && \
  for f in foundation/schema/*.yaml; do
    grep -q '^required_fields:' $f || { echo "MISSING required_fields in $f"; exit 1; }
    grep -q 'cross_cutting' $f || grep -q 'rag/recall' $f || true
  done && \
  grep -q 'cross_cutting' foundation/schema/genre_profile.yaml && \
  grep -q 'cross_cutting' foundation/schema/template.yaml && \
  grep -q 'rule_type' foundation/schema/methodology.yaml && \
  grep -q 'dedup_against' foundation/schema/prompt_card.yaml && \
  grep -q 'audit_log' foundation/schema/runtime_state.yaml && \
  grep -q 'cold_start' foundation/rag/recall_config.yaml && \
  echo PASS || echo FAIL
```

## 心跳协议（必须实施）

完成每个 F-N 任务后**立即**追加（不覆盖）到 `.ops/p7-handoff/ST-S1-FOUNDATION.md`：

```
## 2026-05-13THH:MM:SS+08:00 | F-N 完成
- 文件：<path>
- 字节：<size>
- 关键字段：<list>
- 下一步：F-<N+1>
```

启动时先写一条 `## START` 含计划。完成全部 12 个文件后写 `## DONE` + 验收命令结果。

## 红线

- **不批量脚本**：不许用 sed/awk/find-exec/Python 脚本批量生成 yaml；逐个 Write
- **不动 lock map 外文件**
- **不串供其他 P7**：不读 P7-meta / P7-platform 的 handoff
- **不臆造内容**：schema 字段来源必须是 ARCHITECTURE §三 + scout 报告引用
- **失败时**：尝试 ≤3 次；超过 3 次失败 → 写 `## BLOCKED` 到 handoff + stop，主 agent 接管
- **不要省事**：用户明确要求"多思考多花时间"，每个 schema 字段必须给 example

## fallback

如果遇到 ARCHITECTURE.md 中字段定义模糊 / scout 报告引用不到 / 你不确定怎么写：
1. 在 handoff 写 `## QUESTION` 段，列出具体问题
2. 写 `## BLOCKED on <question>` + stop
3. 主 agent 看到后会回答 + 重派

## 完成判据

```
✅ 12 个目标文件全在
✅ 验收命令 PASS
✅ 心跳协议每步都写了
✅ 每个 schema yaml 有 ≥1 example
✅ 必填 8 字段在每个 asset_type schema 中都定义
```

启动！第一步：读 ARCHITECTURE.md + ROADMAP.md。
