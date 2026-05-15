# Genm Absorption Jury

日期：2026-05-16

## 结论

Genm 值得吸收的是工程治理机制，不是目录结构或题材正文。Ginga 已经有 `StateIO`、sidecar、BookView、review、market、Reference Sidecar RAG 和 longform gate，因此本轮建议只吸收能强化边界、证据和可观测性的能力。

## 证据来源

- Genm scout：低成本 explorer 扫描 `/Users/arm/Desktop/genm`，重点确认 `registry-as-reference`、workflow stage runner、model topology、accept/refill、gate rules、report-only post_check、jury/evidence pack。
- Ginga fit scout：低成本 explorer 扫描 `/Users/arm/Desktop/ginga`，重点确认 `StateIO`、workflow/skill/capability、Foundation assets、BookView、review、market、book_analysis、Reference Sidecar RAG 的落点边界。
- 主控抽查：`/Users/arm/Desktop/genm/AGENTS.md`、`ROADMAP.md`、`TASK_BOARD.md`、`JURY_TRACKER.md`、`docs/architecture-overview.md`、`docs/model-topology.md`、`docs/vNext-*.md`；以及 Ginga `STATUS.md`、`ARCHITECTURE.md`、`ROADMAP.md`、`ginga_platform/**`、`rag/reference_sidecar.py`、`scripts/**`。

## Jury 矩阵

| 候选能力 | 建议 | Ginga 落点 | 理由 | 红线 |
|---|---|---|---|---|
| Registry-as-reference / 零拷贝资产引用 | 应该吸收 | Foundation asset 元数据、methodology/promoted 资产、reference sidecar | 可以减少资产正文复制和污染，适合把外部方法论变成可追踪引用 | 不直接复制 Genm `基座/` 正文进 Ginga 真值或默认 RAG |
| Accept -> refill 候选到真值链 | 应该吸收为原则，谨慎实现 | `StateIO` 周边的候选/人工接受/patch 流程 | Ginga 已有 StateIO，缺的是更明确的 candidate-only 到 truth 的人工门禁语言 | 不绕过 StateIO，不让 LLM 自由文本直接写 `runtime_state` |
| Model topology + live probe | 应该吸收 | Platform provider/router 规划、真实 LLM smoke、future model routing | Ginga 已有真实 LLM 与 provider 质量报告，但还没有角色级 provider 拓扑和 probe 证据面 | 不把模型快照写死为长期事实；provider 切换不能改变 truth 写入边界 |
| Report-only post_check / style fingerprint | 应该吸收 | `ginga review`、longform quality gate、`.ops/reviews/**` | 与 Ginga warn-only review 边界高度一致，可补强风格/质量可观测性 | 不把低分自动升级为硬失败，不自动改正文 |
| Hard gate / boundary rules | 应该吸收 | `validate_architecture_contracts.py`、`verify_all.py`、架构边界文档 | 可把 `default_path_breach`、`truth_divergence`、`router_bypass` 这类风险改写成 Ginga 自己的可验证规则 | 不照抄 Genm 规则名；按 Ginga 的 StateIO/RAG/sidecar 边界重写 |
| Jury / evidence pack 工作流 | 可以吸收 | `.ops/jury/**`、`.ops/reports/**`、高风险设计评审 | Ginga 已在长篇 reviewer queue 中使用类似机制，适合架构争议和高风险能力 | 不把 jury 原文当 truth，不把 review 输出注入 prompt |
| Workflow stage runner 形态 | 可以吸收 | `workflow DSL + step_dispatch + capability_registry` | Ginga 已有主干，Genm 的 stage/check.sh 经验可作为可观测性参考 | 不重写现有 workflow runner，不引入第二套 runner 真值 |
| Migration / audit scripts | 可以吸收 | 一次性迁移脚本、报告生成器 | 对历史资产迁移、路径修复、坏链审计有用 | 不绑定 Genm 目录结构，不做批量重写式迁移 |
| Genm 题材包正文 | 暂不吸收 | 无默认落点；仅可作为人工参考或污染隔离输入 | 内容属于 Genm 题材资产，直接搬运会污染 Ginga 资产边界 | 不进默认 RAG、StateIO、prompt、raw_ideas |
| 强平台化写作规则 / 去 AI 化规则原文 | 暂不吸收 | 可拆成 review rubric 候选 | 规则风格偏平台化，直接套用会过拟合 | 不变成全局写作规则，不自动改正文 |

## 推荐顺序

1. **先做边界型吸收**：把 `registry-as-reference`、candidate-only/truth、report-only、jury evidence pack 的术语写成 Ginga 后续规划规则，不急着实现新代码。
2. **再做可验证型吸收**：若要落代码，优先补 provider/model topology 的只读报告与 probe 记录，再考虑 router 接线。
3. **最后考虑运行主干**：workflow step、skill adapter、capability provider 靠近 `StateIO`，只有明确验收和回归命令时再开。

## 当前不建议开工的项

- 不做 Genm 目录结构迁移。
- 不把 Genm `基座/` 或 `Example writing style/` 原文搬入 Ginga。
- 不新增第二套 truth/state 系统。
- 不让 review、jury、market、book_analysis 输出反向进入默认 RAG 或 prompt。

## 后续可开任务

- `v1.8-0 Model Topology Observation`：只读 provider role matrix + live probe report，不接管 runtime。
- `v1.8-1 Candidate Truth Gate Wording`：梳理 Ginga 的 candidate-only / report-only / truth 写入术语，并同步到 `STATUS.md` / `ARCHITECTURE.md`。
- `v1.8-2 Review Style Fingerprint`：在 `ginga review` 中增加 report-only 风格指纹，不自动改正文。
