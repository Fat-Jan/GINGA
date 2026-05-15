好的，作为 Ginga 项目的第三方架构评审，我将基于您提供的“拆书逻辑蒸馏融合规划”进行独立审查。

**审查总结：** 该规划在战略方向和边界意识上表现出色，其核心理念——“蒸馏能力而非搬运脚本”——与 Ginga 架构哲学高度一致。规划清晰地设立了“禁区”（如不写 runtime_state，不进默认 RAG），这是成功的关键。主要风险集中在**实现的复杂性与核心边界技术落地的清晰度**之间，以及对**“侧载”新架构元素（如 sidecar RAG）** 的细节把控不足。需要补充关键的架构对接细节和风险控制的具体实现方案。

**结构化审查意见：**

| severity | field_path | issue | suggestion |
| :--- | :--- | :--- | :--- |
| **高** | `Phase 6: Sidecar RAG` | **架构边界模糊，引入新复杂度**。规划提出“物理索引和默认 RAG 分离”，但未定义如何与 Ginga 现有的 RAG 层（如果已存在或规划中）集成。这引入了新的、未说明的 RAG 变体（`reference_sidecar.py`），可能成为架构混乱点。`reference_sidecar_recall.yaml` 配置与现有 RAG 配置的关系未说明。 | 1. **明确技术选型**：在 `rag/reference_sidecar.py` 中，明确它是完全独立的索引+检索实现，还是对现有 RAG 组件的一种配置模式。 2. **定义查询接口**：明确 `reference_sidecar` 的查询入口、返回格式，以及如何被 workflow DSL 调用（是否通过新的 capability？）。 3. **优先级重估**：考虑到这是新架构元素，建议将此阶段从“最小可执行路线”中移除，推迟到 Phase 5 (Promotion Flow) 稳定运行后，作为独立的增强项再设计实施。 |
| **高** | `Phase 3: D1-D12 Candidate` | **任务拆分粒度与自动化风险**。将 `deconstruction_report.py` 蒸馏为“D1-D12 候选结构”是核心，但“半自动候选”的表述过于模糊。完全依赖正则或关键词抽取 D1-D12 结构极易失败（原计划也承认要避免“脆弱正则”）。若自动化质量低，会制造大量无价值的 `candidate`，增加人工审计负担。 | 1. **明确自动化边界**：在 Phase 3 中，将“自动生成”降级为“辅助标注”。工具应主要负责：a) 按章节切分文本块；b) 提供可能相关的原文摘录（证据）；c) 生成一个**空的、结构完整的** D1-D12 模板供人工填写。 2. **引入置信度/证据**：要求每个非空维度必须附带 `evidence_refs`，且 validator 需检查摘录长度是否符合安全规则。 |
| **中** | `数据流完整性 / Phase 5` | **Promotion 路径缺乏闭环验证**。`promote.py` 将候选资产写入 `foundation/assets/`，但验收标准仅说“promote 后 Foundation validator 通过”。未说明如何触发和验证 Foundation 层的现有 validator，以及如何确保新资产（如 `reference_patterns/`）不干扰现有 Foundation 资产的加载和使用。 | 1. **在 Phase 5 的验收中增加**：“调用 `foundation` 现有校验器（如 `validate_foundation.py`，假设存在）对目标目录运行，结果为 PASS”。 2. **定义资产加载协议**：明确 `reference_patterns` 资产在 Foundation 层如何被识别和加载（例如，通过命名空间、类型标签），确保与现有的 `methodology`/`prompts` 并存且不冲突。 |
| **中** | `风险控制 / Phase 2` | **证据片段的版权与使用风险控制不足**。`Evidence Snippet` 中明确包含 `raw_excerpt_path`（原文摘录）。虽然声明了 `allowed_use: “analysis_only”`，但缺乏技术手段强制执行。摘录文件存在于磁盘，可能被其他流程误读或泄露。 | 1. **修改设计**：将 `raw_excerpt_path` 改为 **`excerpt_hash`**，仅存储哈希值。原文摘录应临时生成，或存储在一个访问受严格控制的、非默认的临时目录中，并在审计完成后自动清理。 2. **在 `promote.py` 或单独的审计脚本中增加检查**：确保被 promote 的 `reference_pattern` 不依赖于长期存储的 `raw_excerpt_path` 文件。 |
| **中** | `架构边界 / Meta checker` | **Meta checker 结果的应用不明确**。规划禁止将 checker/audit 结果“注入 prompt”，这是正确的。但未说明这些 audit 结果（如污染检查、相似度分数）在 `promotion_candidate.yaml`