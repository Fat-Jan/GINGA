# ST-S2-R-RAG-LAYER1：RAG Layer 1 frontmatter 召回 + 冷启动 + 全局关闭（P7）

## 你是谁

你是 ginga 项目 Sprint 2 的 **P7-R 骨干**，独立于 Phase 0（不依赖 capability_registry）。任务是搭起 RAG 召回最小可工作版本，让 workflow step 在 drafting/refinement 阶段能召回 prompt cards 注入 prompt context。

## 项目一句话背景

Sprint 2 仅做 RAG Layer 1（frontmatter 标签过滤 + quality_grade 排序）；Layer 2/3 留 S3。冷启动（资产库空）必须降级到纯 frontmatter 过滤，不报错。

## 必读输入

1. `/Users/arm/Desktop/ginga/ARCHITECTURE.md` §五 RAG 层（5.1 三层策略 + 5.2 冷暖启动 + 5.3 召回禁忌）
2. `/Users/arm/Desktop/ginga/ROADMAP.md` §2.2.2
3. `/Users/arm/Desktop/ginga/foundation/rag/recall_config.yaml`（冷暖启动 + stage_specific_top_k 配置）
4. `/Users/arm/Desktop/ginga/foundation/schema/prompt_card.yaml`（卡片 frontmatter schema）
5. `/Users/arm/Desktop/ginga/ginga_platform/orchestrator/runner/step_dispatch.py`（找 rag_mode hook 插入点）

## 写范围 lock map

**只能写**：
- `rag/__init__.py`
- `rag/index_builder.py`
- `rag/layer1_filter.py`
- `rag/cold_start.py`
- `ginga_platform/orchestrator/runner/tests/test_rag_layer1.py`
- `.ops/p7-handoff/ST-S2-R-RAG-LAYER1.md`

**可改一个文件**：`ginga_platform/orchestrator/runner/step_dispatch.py`（仅插入 rag_mode 检查 hook，**不重写**；改前先 Read 全文）

**绝不写**：其他 P7 Track 范围 / 文档 / 看板

## 任务清单

### R-1 index_builder.py：扫 foundation/assets/prompts/ 建 sqlite 索引

输入：`foundation/assets/prompts/*.md`（含 frontmatter）
输出：`rag/index.sqlite`（含 id / stage / topic / asset_type / quality_grade / card_intent / source_path）
冷启动行为：源目录不存在或空 → 不报错，建空索引文件 + 日志记录。

### R-2 layer1_filter.py：召回 API

```python
def recall(
    stage: str | None = None,
    topic: str | list[str] | None = None,
    asset_type: str | None = None,
    card_intent: str | None = None,
    top_k: int = 5,
    quality_floor: str = "B",
) -> list[dict]:
    """按 frontmatter 字段过滤召回卡片，按 quality_grade 排序.

    冷启动（index 空）→ 返回 []，记 audit_log warn 'rag cold-start, empty result'.
    """
```

支持 topic 部分匹配（list 含一个值即命中），quality_grade 排序 A > A- > B+ > B（C/D 默认过滤）。

### R-3 cold_start.py：暖/冷状态检测 + 降级

```python
def detect_state(index_path: Path) -> Literal["cold", "warm"]: ...
def cold_recall_fallback(...) -> list[dict]: ...
```

冷启动时 disable Layer 2/3（按 `recall_config.yaml.cold_start.enabled_layers=[1]`）。

### R-4 stage-specific top_k：从 recall_config.yaml 读

在 `layer1_filter.recall` 中：若 caller 未传 top_k，读 `foundation/rag/recall_config.yaml.stage_specific_top_k[stage]`，缺省用 `default_top_k`。

### R-5 step_dispatch.py 加 rag_mode hook

在 step_dispatch 跑 step 前检查 `runtime_state.workflow_flags.rag_mode`：
- `off` → skip 召回，audit 'rag disabled by user'
- `on`（默认）→ 调 `layer1_filter.recall(step.retrieval_hint)` 注入 retrieved.cards

**改 step_dispatch.py 时只追加 hook 段，不动现有 dispatch_step / fan_out 逻辑**。

### tests

`test_rag_layer1.py` ≥4 cases：
1. 空 index 冷启动返回 []
2. 已建 index 按 topic 过滤命中
3. quality_grade 排序正确
4. rag_mode=off 时 step_dispatch 不调召回

## 验收命令（DoD）

```bash
cd /Users/arm/Desktop/ginga && \
  python3 -c "
from rag.layer1_filter import recall
result = recall(stage='drafting', topic='玄幻黑暗', top_k=5)
print(f'recall returned {len(result)} cards (cold-start OK)')
" && \
  python3 -m unittest ginga_platform.orchestrator.runner.tests.test_rag_layer1 -v 2>&1 | tail -10 && \
  grep -q rag_mode ginga_platform/orchestrator/runner/step_dispatch.py && \
  echo PASS
```

## 心跳协议 / 红线 / fallback

同 Sprint 1 P7 模板。max_attempts=3。

**红线**：
- `step_dispatch.py` 改前必须 Read 全文，新增 hook 不破坏现有 dispatch_step / 异常处理
- 不引第三方包（sqlite 用 stdlib `sqlite3`）

启动！预算：45 min wall。
