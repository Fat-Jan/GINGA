# Ginga LLM 端点评估表

> 用途：供用户决策哪些端点/模型纳入 `llm_config.yaml`，哪些剔除。
> 生成时间：2026-05-16
> 评估标准：能否稳定输出 4000+ 中文字长篇正文、是否有已知限制、是否适合 Ginga 的角色

## 端点总览

| 端点 | 默认模型 | 模型数 | 模式 | 适合 Ginga 角色 | 备注 |
|---|---|---|---|---|---|
| **久久** | qwen3.6-max-preview-nothinking | 8 | auto | ✅ prose_writer (primary) | 当前主力；偶发 504；nothinking 避免推理痕迹混入正文 |
| **ioll-mix** | deepseek-chat | 46 | auto | ✅ fallback / 评审 | 模型池最大；有 qwen3.6-max-preview、deepseek-v3.2、kimi-k2.6 等 |
| **wzw** | GLM-4.7 | 64 | auto | ⚠️ 备选 fallback | 模型多但 GLM 系中文长文质量待验证；有 deepseek-v3.2、gemini-3-pro |
| **ioll-grok** | grok-4.20-auto | 7 | stream-only | ⚠️ 评审/jury | Grok 擅长分析不擅长中文创作；适合做 reviewer 不适合 prose |
| **windhub** | deepseek-v3-2-251201 | 8 | auto | ✅ fallback | 有 deepseek-v3.2、mimo-v2.5-pro、MiniMax-M2.7；稳定性待验证 |
| **zhenhaoji** | deepseek-v4-pro | 10 | auto | ⚠️ 有限 | 只有 deepseek-v4-pro 可靠；Claude/GPT/Gemini 都返回注入拦截 |
| **xiaomi-tp** | mimo-v2.5 | 5 | auto | ⚠️ 备选 | reasoning model；max_tokens≥4096；genm 验证过出货率；中文长文质量未验证 |
| **useful-codex** | gpt-5.4 | 7 | stream-only | ❌ 不适合 | 0:30-7:30 禁用；GPT 系中文创作质量不如 qwen/deepseek；适合跨族 jury |
| **jiujiu-jury** | qwen3.6-max-preview-thinking | 8 | auto | ⚠️ reviewer only | 与久久同源；thinking 模式适合评审；大包 504 |

## 按角色推荐

### prose_writer（正文生成，4000+ 字中文）

| 优先级 | 端点 | 模型 | 理由 |
|---|---|---|---|
| Primary | 久久 | qwen3.6-max-preview-nothinking | 当前验证最充分；nothinking 无推理痕迹 |
| Fallback 1 | ioll-mix | qwen3.6-max-preview | 同模型不同网关，避免久久单点故障 |
| Fallback 2 | windhub | deepseek-v3-2-251201 | DeepSeek 中文长文能力强；独立网关 |
| 备选 | ioll-mix | deepseek-v3.2 / kimi-k2.6 | 未在 Ginga 验证过，但模型能力足够 |

### reviewer（质量评审）

| 优先级 | 端点 | 模型 | 理由 |
|---|---|---|---|
| Primary | jiujiu-jury | qwen3.6-max-preview-thinking | thinking 模式适合分析；但大包 504 |
| Fallback 1 | ioll-grok | grok-4.20-auto | 分析能力强；stream-only |
| Fallback 2 | wzw | GLM-4.7-thinking | 有 thinking 变体 |
| 备选 | useful-codex | gpt-5.4 | 跨族视角；但有时间窗口限制 |

### repair（章节修复）

| 优先级 | 端点 | 模型 | 理由 |
|---|---|---|---|
| Primary | 久久 | qwen3.6-max-preview-nothinking | 与生成同模型，风格一致 |
| Fallback | ioll-mix | qwen3.6-max-preview | 同上 |

## 需要你决策的问题

1. **ioll-mix 的 qwen3.6-max-preview 是否可以作为久久的 fallback？** 它是同模型不同网关，理论上输出质量一致，但未在 Ginga 做过 4 章真实验证。

2. **windhub 的 deepseek-v3.2 是否值得纳入？** DeepSeek 中文能力公认强，但 Ginga 从未用它生成过正文，风格可能与 qwen 不同。

3. **wzw 要不要保留？** 64 个模型但默认 GLM-4.7，GLM 系在长篇中文创作上的表现不如 qwen/deepseek。如果只是做 fallback 的 fallback，可能不值得维护。

4. **useful-codex 要不要剔除？** 有时间窗口限制（0:30-7:30 禁用），GPT 系中文创作不是强项。但如果需要跨族 jury 视角可以保留。

5. **xiaomi-tp 的 mimo-v2.5 要不要试？** reasoning model，genm 验证过出货率，但中文长篇创作质量未知。

6. **zhenhaoji 要不要剔除？** 只有 deepseek-v4-pro 可用，其他模型都有注入拦截问题。如果 deepseek-v4-pro 质量好可以保留为 fallback。
