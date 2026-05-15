# v1.3-4 Promote Flow 规格计划

> 面向 AI 代理的工作者：本计划只定义 Promote Flow 的规格、DoD 与 validator 设计，不实现 promote CLI，不写 Foundation 资产，不修改默认 RAG / prompt / raw_ideas / StateIO。后续真正实现前，应重新从 `STATUS.md` 校准状态，并优先使用 TDD。

## 目标

为 v1.3-4 Promote Flow 定义可执行规格：只有经过人工审核、污染检查和目标白名单验证的 v1.3-3 `trope_recipe_candidate`，未来才允许进入 promote 讨论；本计划不把任何 pending candidate 自动写入 Foundation。

## 当前依据

- `STATUS.md`：v1.3-4 仍是 `deferred`；不得把 v1.3-3 的 `pending` candidate 自动写入 Foundation、默认 RAG、prompt、`raw_ideas` 或 `StateIO`。
- `.ops/book_analysis/contamination_check_rules.md`：candidate / promoted asset 必须通过人工审核清单、hash 追溯、污染检查和默认排除规则。
- `.ops/reports/book_analysis_distillation_fusion_plan.md`：Promote Flow 必须有唯一入口，pending / rejected 不能 promote，promote 后必须跑对应 Foundation validator。
- `.ops/reports/chai_shu_fusion_decision_report.md`：`promotion_candidate.yaml` 需要 source / evidence / derived_pattern / safety / target / signed_audit_log。

## 非目标

- 不实现 `ginga reference promote` 或任何 promote CLI。
- 不新增 `ginga_platform/book_analysis/promote.py`。
- 不新增或修改 `foundation/assets/**`、`foundation/schema/**`。
- 不修改 `foundation/rag/recall_config.yaml`，不新增默认 RAG source。
- 不写 `foundation/runtime_state/**`、`foundation/raw_ideas/**`。
- 不把 `.ops/book_analysis/**` 加入 explorer / review / provider 默认输入白名单。

## 规格草案

Promote Flow 的输入必须是污染源域内的候选文件：

```text
.ops/book_analysis/<run_id>/promotion_candidate.yaml
```

候选最小字段：

```yaml
schema_version: "0.4.0"
candidate_id: ""
source:
  source_hash: ""
  license_or_usage_note: ""
evidence:
  refs:
    - evidence_id: ""
      chapter_hash: ""
      excerpt_hash: ""
      locator: ""
derived_pattern:
  candidate_type: "trope_recipe_candidate"
  trope_core: ""
  reader_payoff: ""
  trigger_conditions: []
  variation_axes: []
  forbidden_copy_elements: []
safety:
  source_contamination_check: "pending"
  similarity_score: null
  human_review_status: "pending"
  signed_audit_log: []
target:
  promote_to: "none"
  output_path: ""
```

允许的 `target.promote_to` 初始白名单只作为未来讨论项：

- `none`
- `methodology`
- `prompt_example`
- `reference_pattern`

本轮计划不允许任何默认 promote。后续实现时，`none` 以外的目标必须先补目标资产 schema、加载协议、validator 与回滚策略。

## Validator 设计

建议未来新增：

```text
ginga_platform/book_analysis/promotion_spec.py
scripts/validate_promotion_candidate.py
ginga_platform/orchestrator/runner/tests/test_book_analysis_promotion_spec.py
```

validator 必须失败的情况：

- `promotion_candidate.yaml` 不在 `.ops/book_analysis/<run_id>/` 下。
- 缺 `source_hash`、`chapter_hash`、`excerpt_hash` 或 evidence locator。
- `source_contamination_check != pass`。
- `human_review_status != approved`。
- `similarity_score >= 0.80`。
- `variation_axes` 少于 2 个。
- `forbidden_copy_elements` 为空。
- `target.promote_to` 不在白名单。
- `target.output_path` 指向 `foundation/runtime_state/**`、`foundation/raw_ideas/**`、默认 RAG 配置或 prompt 组装路径。
- candidate、audit 或 report 引用 `.private_evidence/**`。
- candidate 或 promoted preview 含原文长摘录、原台词、原专名、原能力名、独特谜底或可复原原作的具体事件链。

validator 输出建议：

```json
{
  "status": "failed|passed|needs_review",
  "candidate_path": ".ops/book_analysis/<run_id>/promotion_candidate.yaml",
  "target": {"promote_to": "none", "output_path": ""},
  "errors": [],
  "warnings": [],
  "blocked_writes": []
}
```

`needs_review` 只允许用于相似度 `0.65 - 0.79` 或人工审核备注不充分；不得视为 promote 通过。

## DoD

v1.3-4 进入实现前，至少要满足：

- 计划文档存在并明确非目标、红线、字段规范、validator 失败条件。
- `STATUS.md` 仍明确 v1.3-4 不可自动 promote。
- 未来实现任务只先做 validator，不做真实 promote 写入。
- validator 测试覆盖 approved / pending / rejected、缺 hash、相似度失败、路径越界、`.private_evidence` 引用、默认 RAG 污染、Foundation 未声明目标。
- 完整验证至少包含：

```bash
python -m unittest ginga_platform.orchestrator.runner.tests.test_book_analysis_promotion_spec
python3 scripts/validate_promotion_candidate.py .ops/book_analysis/<run_id>/promotion_candidate.yaml
python3 scripts/validate_architecture_contracts.py
python3 scripts/verify_all.py
```

## 后续任务拆分

### 任务 1：Promotion Candidate schema + fixture

**范围：** 只在 `.ops/book_analysis/schema/` 和 `.ops/book_analysis/<fixture-run>/` 定义候选 fixture，不写 Foundation。

**验收：** fixture 表达 approved / pending / rejected 三种状态，并保留 `[SOURCE_TROPE]` 污染边界。

### 任务 2：Validator 纯函数

**范围：** 新增纯函数校验 promotion candidate 字段、路径、hash、人工审核状态和 target 白名单。

**验收：** pending / rejected / 缺 hash / 越界路径全部 fail；approved + pass + whitelist 才 passed。

### 任务 3：Validator CLI

**范围：** 新增 `scripts/validate_promotion_candidate.py`，只读输入并输出 JSON 报告。

**验收：** CLI 不写 Foundation，不修改 RAG，不写 StateIO。

### 任务 4：状态文件同步

**范围：** validator 完成并通过后，才同步 `STATUS.md` / `ROADMAP.md` / `notepad.md`。

**验收：** 只能声明 v1.3-4 validator/spec 完成；若没有真实 promote 实现，不得声明 Promote Flow 完成。

## 下一步任务计划

下一轮最小可开工任务是“v1.3-4 Promotion Candidate schema + validator fixture”，不是 promote CLI。先写失败测试和 fixture，再实现只读 validator。
