# v2.6b Live Fallback Runbook

## Status

- Task ID: `v2.6b-live-fallback-runbook`
- Status: `validating`
- Scope: runbook/report only
- Live calls executed: no
- Runtime code modified: no

## Inputs Reviewed

- `.ops/plans/v2-6-llm-config-plan.md`
- `.ops/reports/stage_closeout_v2_6a_llm_config.md`
- `llm_config.yaml`
- `ginga_platform/orchestrator/cli/llm_config.py`
- `ginga_platform/orchestrator/runner/tests/test_llm_config.py`

## Minimal Live Objective

v2.6b 的最小真实调用目标是：用真实 `ask-llm` 端点证明 `call_llm_with_fallback(prompt, role=...)` 在 primary 失败时会自动尝试 fallback，并且最终输出来自可用 fallback。

必须是 no mock / no dry-run 的真实网络验证。v2.6a 的测试只 mock 了 `subprocess.run`，能证明 Python 控制流会按顺序尝试 primary 和 fallback，但不能证明以下模型端事实：

- 真实 `ask-llm` endpoint 名称是否可用。
- 真实失败形态是否会以非 0 exit 或空 stdout 被 wrapper 捕获。
- 真实 fallback endpoint 是否能在同一 prompt、同一 `max_tokens`、同一 timeout 约束下返回有效正文。
- 网络超时、504、stderr 文本和外层 runner 终止行为是否符合预期。

因此 v2.6b 不验证长篇质量，只验证真实端点 fallback 链路。

## Isolation Boundary

不要覆盖现有 artifacts。建议由主 agent 或人工在临时隔离目录记录 stdout/stderr/metadata：

```bash
export GINGA_LIVE_FALLBACK_RUN_ID="v2_6b_$(date +%Y%m%d_%H%M%S)"
export GINGA_LIVE_FALLBACK_OUT=".ops/reports/${GINGA_LIVE_FALLBACK_RUN_ID}"
mkdir -p "$GINGA_LIVE_FALLBACK_OUT"
```

允许写入的最小记录文件应只放在隔离目录或后续指定报告路径，例如：

- `${GINGA_LIVE_FALLBACK_OUT}/command.txt`
- `${GINGA_LIVE_FALLBACK_OUT}/stdout.txt`
- `${GINGA_LIVE_FALLBACK_OUT}/stderr.txt`
- `${GINGA_LIVE_FALLBACK_OUT}/result.json`

本 runbook 不建议写 `.ops/real_llm_harness/**` 或 `.ops/validation/**`，避免污染既有 validation truth。

## Safe Fallback Probe

当前 API 的关键限制：`call_llm_with_fallback(..., endpoint="...")` 会禁用 fallback；只有传 `role` 时才读取 `llm_config.yaml` 的 primary/fallback。`llm_config.yaml` 目前没有一个“故意失败 primary + 可用 fallback”的 probe role，而且本任务禁止修改 `llm_config.yaml` 和 runtime 代码。

因此当前代码可以安全验证“现有配置 role 的真实 primary 成功路径”，但不能在不改配置、不 monkeypatch、不改 runtime 的前提下安全构造“失败 primary + 可用 fallback”的真实验证。

### Blocker

v2.6b 要验证失败 primary + 可用 fallback，需要一个最小代码/配置缺口被补齐：

- 推荐：让 `load_config(config_path=...)` 的路径能通过环境变量或 `call_llm_with_fallback(..., config_path=...)` 注入，这样 live probe 可使用临时 YAML，不修改项目根 `llm_config.yaml`。
- 备选：新增一个专用 role，例如 `live_fallback_probe`，primary 指向明确不存在的 endpoint，fallback 指向低成本可用 endpoint。但这会修改 `llm_config.yaml`，不适合本任务的只读 explorer 边界。

在补齐前，不建议用 monkeypatch 伪造 config 后再调用真实 `ask-llm`，因为它能跑通 Python 进程内实验，但不能代表 CLI/runner 的正式配置路径。

## Proposed Live Command After Gap Is Closed

在具备临时 config 注入能力后，构造一个只消耗极小 token 的真实 probe：

```yaml
version: "1.0"
roles:
  live_fallback_probe:
    description: v2.6b live fallback probe
    primary: definitely-missing-endpoint-v2-6b
    fallback: [ioll-mix]
    max_tokens: 64
    timeout: 30
defaults:
  endpoint: definitely-missing-endpoint-v2-6b
  max_tokens: 64
  timeout: 30
  max_retries: 0
```

验证脚本应只调用：

```python
from ginga_platform.orchestrator.cli.llm_config import call_llm_with_fallback

prompt = "Return exactly: v2.6b fallback ok"
text = call_llm_with_fallback(prompt, role="live_fallback_probe")
print(text)
```

期望行为：

- primary `definitely-missing-endpoint-v2-6b` 失败。
- fallback `ioll-mix` 被调用。
- stdout 非空，且能表达 probe 指令。
- 如果全部失败，错误信息包含 primary 和 fallback endpoint 名称。

## Cost And Network Boundary

- 默认不跑真实 LLM；必须由主 agent 或人工显式确认后执行。
- 单次 probe 只允许一个 prompt、一个 role、最多 64 `max_tokens`。
- `timeout` 建议 30 秒；总 wall time 超过 90 秒即停止。
- 不做 4000 字正文、不跑 4 章批量、不触发 immersive runner。
- 不重试超过一次完整 primary + fallback 链路。
- 不把 stdout/stderr 写入 `.ops/validation/**`，除非后续阶段明确把它提升为正式 validation artifact。

## Stop Conditions

立即停止并标记 `blocked`：

- 无法安全注入临时 config，只能修改项目根 `llm_config.yaml` 才能构造失败 primary。
- `ask-llm` 不存在、不可执行或本地 endpoint 列表无法确认 fallback endpoint。
- 网络不可用、认证缺失或 provider 返回认证/配额错误。

立即停止并标记 `failed`：

- primary 失败后没有尝试 fallback。
- fallback 返回空 stdout，但 wrapper 没有报错。
- 全部失败时错误信息没有暴露各 endpoint 的失败摘要，导致不可诊断。

## Pass / Fail Fields

后续真实验证的 `result.json` 至少应包含：

```json
{
  "task_id": "v2.6b-live-fallback-runbook",
  "status": "pass | blocked | failed",
  "no_mock": true,
  "dry_run": false,
  "role": "live_fallback_probe",
  "primary_endpoint": "definitely-missing-endpoint-v2-6b",
  "fallback_endpoint": "ioll-mix",
  "primary_failed": true,
  "fallback_attempted": true,
  "fallback_succeeded": true,
  "stdout_nonempty": true,
  "max_tokens": 64,
  "timeout_seconds": 30,
  "wall_time_seconds": 0,
  "cost_boundary": "single prompt, <=64 max_tokens, no retries beyond one fallback chain",
  "artifact_dir": ".ops/reports/<run-id>"
}
```

Pass 条件：

- `no_mock=true`
- `dry_run=false`
- `primary_failed=true`
- `fallback_attempted=true`
- `fallback_succeeded=true`
- `stdout_nonempty=true`

Fail 条件：

- 任一 pass 条件为 false。
- 或真实调用需要覆盖现有 artifacts 才能完成。

## v1.7-7b Relationship

v1.7-7b 和 v2.6b 可以并行规划，但真实 4 章批量不应在 v1.7-7a 通过前执行。

原因：

- v2.6b 只证明模型 fallback 链路，不证明 v1.7-7 的 style warn 分级、quality gate 或长篇章节策略已经稳定。
- 真实 4 章批量会同时消耗网络、模型费用和长篇 pipeline 风险；如果 v1.7-7a 未通过，失败原因会混在 fallback、质量门和章节生成三层里。
- 正确顺序是先让 v1.7-7a 离线/最小验证通过，再用 v2.6b 的低成本 live fallback 证据决定是否开放 v1.7-7b 的真实批量。

## Main Recommendation

当前 v2.6b 应保持 `blocked` 在真实调用前的准备态：runbook 已明确隔离、成本、字段和停止条件，但“失败 primary + 可用 fallback”的安全真实验证需要先补一个临时 config 注入能力，或由 owner 明确批准修改 `llm_config.yaml` 增加专用 probe role。
