# v2.6 LLM Config — 项目内置模型配置

## 目标

把 LLM 端点选择、超时、max_tokens、fallback 策略从硬编码和 CLI 参数收敛到一个项目内配置文件，让代码、agent、Codex 都能读到统一的模型约束。

## 触发原因

- 久久 504 频发，没有自动 fallback
- 端点默认值散落在 `__main__.py`、`demo_pipeline.py`、`immersive_runner.py`、`multi_chapter.py` 四处硬编码 `"久久"`
- Codex 和未来 agent 无法从项目文件了解模型约束（超时、max_tokens 上限、已知问题）
- 换模型需要改代码或每次传 `--llm-endpoint`

## 设计

### 配置文件：`llm_config.yaml`（项目根）

```yaml
version: "1.0"

roles:
  prose_writer:
    description: 正文生成（4000+ 字中文长篇）
    primary: 久久
    fallback: [ioll-mix]
    max_tokens: 12000
    timeout: 300

  reviewer:
    description: 质量评审
    primary: jiujiu-jury
    fallback: [ioll-grok]
    max_tokens: 4096
    timeout: 120

  repair:
    description: 章节修复 / rewrite
    primary: 久久
    fallback: [ioll-mix]
    max_tokens: 12000
    timeout: 300

  probe:
    description: model-topology 最小探针
    primary: 久久
    fallback: []
    max_tokens: 64
    timeout: 30

defaults:
  endpoint: 久久
  max_tokens: 4096
  timeout: 300
  max_retries: 1

health:
  久久:
    last_verified: 2026-05-16
    known_issues:
      - 长输出偶发 504
      - 第 4 章曾触发外层终止
  jiujiu-jury:
    last_verified: 2026-05-15
    known_issues:
      - 大包（>50KB）连续 504
      - 只适合短输入
```

### 代码改动：新增 `ginga_platform/orchestrator/cli/llm_config.py`

```python
"""LLM 配置加载 + fallback 调用封装。"""

def load_llm_config() -> dict:
    """从项目根 llm_config.yaml 加载配置。"""

def resolve_endpoint(role: str) -> tuple[str, int, int]:
    """按 role 返回 (endpoint, max_tokens, timeout)。"""

def call_llm_with_fallback(prompt: str, *, role: str, max_tokens: int | None = None) -> str:
    """调用 LLM，primary 失败时自动尝试 fallback。"""
```

### 改动 `_call_llm()`

`demo_pipeline._call_llm()` 保持签名不变（向后兼容），但内部改为读配置的 timeout：

```python
def _call_llm(prompt: str, endpoint: str, max_tokens: int = 4096, timeout: int | None = None) -> str:
    if timeout is None:
        timeout = _resolve_timeout(endpoint)
    ...
```

### CLI 参数兼容

`--llm-endpoint` 保留，作为 override。不传时从 `llm_config.yaml` 的 `defaults.endpoint` 读取。

## 实现范围

| 文件 | 改动 |
|---|---|
| `llm_config.yaml`（新增） | 配置文件 |
| `ginga_platform/orchestrator/cli/llm_config.py`（新增） | 配置加载 + fallback 封装 |
| `ginga_platform/orchestrator/cli/demo_pipeline.py` | `_call_llm` 读配置 timeout；`_call_llm_or_mock` 可选读 role |
| `ginga_platform/orchestrator/cli/immersive_runner.py` | `_default_llm_caller` 改为走 `call_llm_with_fallback` |
| `ginga_platform/orchestrator/cli/multi_chapter.py` | `_call_llm_for_polish` 走配置 |
| `ginga_platform/orchestrator/cli/__main__.py` | 默认 endpoint 从配置读取 |
| `ginga_platform/orchestrator/model_topology.py` | probe 调用走配置 |
| 测试文件 | 新增 `test_llm_config.py` |

## 不做什么

- 不改 `ask-llm` CLI 本身（它是外部工具）
- 不做自动健康检测（health 字段手动更新）
- 不做模型路由（那是 v1.8-0 model topology 的后续）
- 不改 StateIO 或 workflow DSL
- 不改 quality gate 逻辑（那是 v1.7-7a）

## 拆分

### v2.6a（可派 Codex，纯离线）

1. 新增 `llm_config.yaml`
2. 新增 `ginga_platform/orchestrator/cli/llm_config.py`（load + resolve + call_with_fallback）
3. 改 `_call_llm()` 支持从配置读 timeout
4. 改 `__main__.py` 默认 endpoint 从配置读
5. 新增 `test_llm_config.py`（mock subprocess，验证 fallback 逻辑）
6. `verify_all.py` 通过

### v2.6b（需要真实网络，主 agent 或人工）

- 用真实端点验证 fallback：故意传一个不存在的 primary，确认自动降级到 fallback
- 验证久久 504 时是否正确降级到 ioll-mix

## DoD

```bash
python -m unittest discover -s ginga_platform -p "test_*.py"
python3 scripts/verify_all.py --quick
```

exit 0 = v2.6a 完成。

## 状态

`planned`
