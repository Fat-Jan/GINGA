# v1.7-7a Codex Handoff: Style Warn 分级 + 确定性后处理

## 任务目标

把 `_style_warn_hits()` 的检测结果分为 hard（阻断）和 soft（只报告）两级，只有 hard 类计入 quality gate failure。同时完善 `_rewrite_style_warn_terms()` 的替换策略。

## 背景

当前 `_quality_gate_failure()` 把所有 style warn hits 都当 hard fail，导致 `abrupt_transition`（"突然/猛然/下一秒"）阻断生成。但这三个词是中文动作叙事常用词，LLM 无法可靠避免。真正的 AI 味标志是 `generic_emotion`（"说不出的感觉"等）和 `cliche_metaphor`（"命运的齿轮"等）。

## 具体改动

### 1. `ginga_platform/orchestrator/cli/immersive_runner.py`

**改 `_style_warn_hits()`**：返回值不变（仍是 `dict[str, int]`），但新增一个函数区分 severity：

```python
HARD_STYLE_WARN_NAMES = frozenset({"generic_emotion", "cliche_metaphor"})
SOFT_STYLE_WARN_NAMES = frozenset({"abrupt_transition"})

def _hard_style_warn_hits(body_text: str) -> dict[str, int]:
    """只返回 hard 级别的 style warn hits（阻断生成）。"""
    all_hits = _style_warn_hits(body_text)
    return {k: v for k, v in all_hits.items() if k in HARD_STYLE_WARN_NAMES}

def _soft_style_warn_hits(body_text: str) -> dict[str, int]:
    """只返回 soft 级别的 style warn hits（只报告不阻断）。"""
    all_hits = _style_warn_hits(body_text)
    return {k: v for k, v in all_hits.items() if k in SOFT_STYLE_WARN_NAMES}
```

**改 `_quality_gate_failure()`**：只用 `_hard_style_warn_hits` 判定 failure：

```python
# 原来：
style_hits = _style_warn_hits(body_text)
if style_hits:
    failures.append(...)

# 改为：
hard_hits = _hard_style_warn_hits(body_text)
if hard_hits:
    failures.append(
        "style_warn " + ", ".join(f"{name}={count}" for name, count in sorted(hard_hits.items()))
    )
```

**改 `_rewrite_style_warn_terms()`**：改进 `"突然"` 的替换策略，区分句首和句中：

```python
def _rewrite_style_warn_terms(chapter_text: str) -> str:
    # hard 类：必须清零
    hard_replacements = {
        "说不出的感觉": "刺痛沿着骨缝扩散",
        "难以言喻": "压得喉间发涩",
        "复杂的情绪": "迟疑被掌心冷汗压住",
        "命运的齿轮": "城门深处的绞盘",
        "内心深处": "胸骨后方",
    }
    rewritten = chapter_text
    for old, new in hard_replacements.items():
        rewritten = rewritten.replace(old, new)
    rewritten = re.sub(r"仿佛([^。！？\n]{0,24})命运", r"像\1血契", rewritten)

    # soft 类：best-effort，不要求清零
    # 句首"突然" → "这时"；句中"突然" → "倏地"
    rewritten = re.sub(r"(?<=[。！？\n])([^。！？\n]{0,2})突然", r"\1这时", rewritten)
    rewritten = rewritten.replace("突然", "倏地")
    rewritten = re.sub(r"(?<=[。！？\n])([^。！？\n]{0,2})猛然", r"\1随即", rewritten)
    rewritten = rewritten.replace("猛然", "骤然")
    rewritten = rewritten.replace("下一秒", "下一息")
    return rewritten
```

注意：`_rewrite_style_warn_terms` 在 `run_block` 里的调用位置不变（repair 循环之后、RuntimeError 之前），但现在它主要服务于 hard 类清零。soft 类替换是 bonus，不影响 gate 判定。

### 2. `ginga_platform/orchestrator/cli/longform_policy.py`

**改 `longform_chapter_gate_check()`**：增加 `soft_style_warn` 报告字段：

在现有 return dict 里加一个字段：
```python
from ginga_platform.orchestrator.cli.immersive_runner import _soft_style_warn_hits

# 在 return dict 里加：
"soft_style_warn": _soft_style_warn_hits(body_text),
```

注意避免循环 import：如果 `longform_policy.py` 不能 import `immersive_runner.py`，就把 `_style_warn_hits` 和 `HARD_STYLE_WARN_NAMES` / `SOFT_STYLE_WARN_NAMES` 移到 `longform_policy.py`（它是更底层的模块），然后 `immersive_runner.py` 从 `longform_policy` import。

### 3. 测试更新

**`test_immersive_mode.py`**：

- 现有 `test_run_block_deterministically_rewrites_residual_style_warn_before_writing` 需要更新：mock LLM 返回的文本应该包含 hard 类词（如 "命运的齿轮"），验证 rewrite 后这些词消失
- 新增测试：mock LLM 返回只含 soft 类词（"突然"）的文本，验证 quality gate 不阻断、章节正常落盘
- 新增测试：mock LLM 返回同时含 hard + soft 类词的文本，验证 rewrite 后 hard 清零、soft best-effort 替换

**`test_story_truth_template.py`**：如果有 style warn 相关断言，确认它们与新的分级逻辑一致。

## 写范围（lock map）

只允许改这些文件：
- `ginga_platform/orchestrator/cli/immersive_runner.py`
- `ginga_platform/orchestrator/cli/longform_policy.py`
- `ginga_platform/orchestrator/runner/tests/test_immersive_mode.py`
- `ginga_platform/orchestrator/runner/tests/test_story_truth_template.py`

## 禁止

- 不改 `demo_pipeline.py`
- 不改 `review.py`
- 不改 `state_io.py`
- 不改 `__main__.py`
- 不跑真实 LLM（`ask-llm`）
- 不改 hard gate 的 opening_loop / low_frequency_anchor / foreshadow 逻辑
- 不新增文件
- 不改 prompt 构造逻辑（`_build_chapter_prompt` / `_repair_prompt`）

## 验证命令（DoD）

```bash
cd /Users/arm/Desktop/ginga
python -m unittest discover -s ginga_platform -p "test_*.py" 2>&1 | tail -5
python3 scripts/verify_all.py --quick 2>&1 | tail -10
```

两个命令都 exit 0 = 任务完成。

## 注意事项

- 当前 `immersive_runner.py` 有未提交的改动（`_rewrite_style_warn_terms` 初版 + 集成 + 测试）。在此基础上修改，不要丢弃已有的集成逻辑。
- `_style_warn_hits()` 函数签名和返回格式不变，只新增 `_hard_style_warn_hits` / `_soft_style_warn_hits` 辅助函数。
- 如果遇到循环 import 问题，把 pattern 定义和分级常量移到 `longform_policy.py`（更底层），`immersive_runner.py` 从那里 import。
