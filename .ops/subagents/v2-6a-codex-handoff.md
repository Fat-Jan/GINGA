# v2.6a Codex Handoff: LLM Config 内置配置 + Fallback

## 任务目标

新增项目内 LLM 配置文件 + 配置加载模块 + fallback 调用封装，让端点选择、超时、max_tokens 从硬编码收敛到一个 YAML 文件。

## 背景

当前 `_call_llm()` 硬编码 timeout=300，默认端点 `"久久"` 散落在 4 个文件。久久 504 时没有自动降级。需要一个统一配置让代码和 agent 都能读到模型约束。

## 具体步骤

### 1. 新增 `llm_config.yaml`（项目根 `/Users/arm/Desktop/ginga/llm_config.yaml`）

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
    description: 章节修复
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
  jiujiu-jury:
    last_verified: 2026-05-15
    known_issues:
      - 大包连续 504
      - 只适合短输入
```

### 2. 新增 `ginga_platform/orchestrator/cli/llm_config.py`

```python
"""LLM 配置加载 + fallback 调用封装。

配置文件路径：项目根 llm_config.yaml
调用方式：
    from ginga_platform.orchestrator.cli.llm_config import load_config, call_llm_with_fallback

    # 按 role 调用（自动 fallback）
    text = call_llm_with_fallback(prompt, role="prose_writer")

    # 按显式 endpoint 调用（不 fallback，向后兼容）
    text = call_llm_with_fallback(prompt, endpoint="久久", max_tokens=8000)
"""
```

需要实现的函数：

**`load_config(config_path: Path | None = None) -> dict`**
- 默认从项目根 `llm_config.yaml` 加载
- 项目根通过向上查找 `llm_config.yaml` 或 `AGENTS.md` 定位
- 文件不存在时返回 hardcoded defaults（向后兼容，不 crash）

**`resolve_role(role: str, config: dict | None = None) -> dict`**
- 返回 `{"endpoint": str, "max_tokens": int, "timeout": int, "fallback": list[str]}`
- role 不存在时用 `defaults` 段

**`call_llm_with_fallback(prompt: str, *, role: str | None = None, endpoint: str | None = None, max_tokens: int | None = None, timeout: int | None = None) -> str`**
- 如果传了 `role`，从配置解析 endpoint/max_tokens/timeout/fallback
- 如果传了 `endpoint`，直接用（不 fallback，向后兼容旧调用方式）
- primary 调用失败（非零退出或空输出）时，依次尝试 fallback 列表
- 全部失败时 raise RuntimeError，包含所有尝试的错误信息
- 内部调用 `subprocess.run(["ask-llm", endpoint, "--max-tokens", str(max_tokens), "-s"], input=prompt, ...)`

### 3. 改 `ginga_platform/orchestrator/cli/demo_pipeline.py`

**`_call_llm()`** 改为：
```python
def _call_llm(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
    """调用 ask-llm 子进程，返回 LLM 输出。失败 raise。

    向后兼容：签名不变，但 timeout 从配置读取。
    """
    from ginga_platform.orchestrator.cli.llm_config import load_config
    config = load_config()
    timeout = config.get("defaults", {}).get("timeout", 300)
    cmd = [
        "ask-llm",
        endpoint,
        "--max-tokens",
        str(max_tokens),
        "-s",
    ]
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ask-llm {endpoint} failed (exit={proc.returncode}): {proc.stderr[:500]}"
        )
    if not proc.stdout.strip():
        raise RuntimeError(f"ask-llm {endpoint} returned empty output")
    return proc.stdout
```

**`run_workflow()` 的 `llm_endpoint` 默认值**改为从配置读：
```python
def run_workflow(
    book_id: str,
    *,
    llm_endpoint: str | None = None,  # None = 从配置读
    ...
):
    if llm_endpoint is None:
        from ginga_platform.orchestrator.cli.llm_config import load_config
        llm_endpoint = load_config().get("defaults", {}).get("endpoint", "久久")
    ...
```

### 4. 改 `ginga_platform/orchestrator/cli/immersive_runner.py`

**`_default_llm_caller()`** 改为走 fallback：
```python
def _default_llm_caller(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
    from ginga_platform.orchestrator.cli.llm_config import call_llm_with_fallback
    return call_llm_with_fallback(prompt, endpoint=endpoint, max_tokens=max_tokens)
```

注意：这里传了 `endpoint=`（显式端点），所以不会自动 fallback。如果要启用 fallback，调用方应该改为传 `role="prose_writer"`。但这个改动留给 v2.6b，v2.6a 只做基础设施，不改调用方的行为。

### 5. 改 `ginga_platform/orchestrator/cli/__main__.py`

`--llm-endpoint` 的 default 改为 None，实际默认值在运行时从配置读：
```python
p_run.add_argument(
    "--llm-endpoint",
    default=None,
    help="ask-llm 端点 alias（默认从 llm_config.yaml 读取）",
)
```

在 dispatch 逻辑里：
```python
llm_endpoint = args.llm_endpoint
if llm_endpoint is None:
    from ginga_platform.orchestrator.cli.llm_config import load_config
    llm_endpoint = load_config().get("defaults", {}).get("endpoint", "久久")
```

### 6. 新增测试 `ginga_platform/orchestrator/runner/tests/test_llm_config.py`

测试用例：
- `test_load_config_from_project_root`：验证能加载 `llm_config.yaml`
- `test_load_config_missing_file_returns_defaults`：文件不存在时返回 hardcoded defaults
- `test_resolve_role_prose_writer`：验证 prose_writer role 解析正确
- `test_resolve_role_unknown_falls_back_to_defaults`：未知 role 用 defaults
- `test_call_llm_with_fallback_primary_success`：mock subprocess，primary 成功直接返回
- `test_call_llm_with_fallback_primary_fails_uses_fallback`：mock primary 失败，验证尝试 fallback
- `test_call_llm_with_fallback_all_fail_raises`：全部失败时 raise，错误信息包含所有尝试

所有测试 mock `subprocess.run`，不调用真实 `ask-llm`。

## 写范围（lock map）

允许改的文件：
- `llm_config.yaml`（新增）
- `ginga_platform/orchestrator/cli/llm_config.py`（新增）
- `ginga_platform/orchestrator/cli/demo_pipeline.py`（只改 `_call_llm` 和 `run_workflow` 默认值）
- `ginga_platform/orchestrator/cli/immersive_runner.py`（只改 `_default_llm_caller`）
- `ginga_platform/orchestrator/cli/__main__.py`（只改 `--llm-endpoint` default 和 dispatch）
- `ginga_platform/orchestrator/runner/tests/test_llm_config.py`（新增）

## 禁止

- 不改 `multi_chapter.py`（v2.6a 不改它的调用方式，留给后续）
- 不改 `model_topology.py`（probe 调用留给后续）
- 不改 `review.py`、`state_io.py`、`longform_policy.py`
- 不跑真实 LLM
- 不改 quality gate 逻辑
- 不改 workflow DSL
- 不删除现有的 `_call_llm` 函数（保持向后兼容）

## 验证命令（DoD）

```bash
cd /Users/arm/Desktop/ginga
python -m unittest discover -s ginga_platform -p "test_*.py" 2>&1 | tail -5
python3 scripts/verify_all.py --quick 2>&1 | tail -10
```

两个命令都 exit 0 = 任务完成。

## 关键约束

- `llm_config.yaml` 不包含 API key（key 在 macOS Keychain，由 `ask-llm` 自己管理）
- 配置文件不存在时代码必须正常工作（fallback 到 hardcoded defaults），不能因为缺配置就 crash
- `call_llm_with_fallback` 的 fallback 逻辑：只在 subprocess 非零退出或空输出时触发，不在 timeout 时触发（timeout 直接 raise，因为 fallback 端点大概率也会 timeout）
- 保持所有现有测试通过——现有测试 mock 了 `_call_llm`，签名不变所以不受影响
