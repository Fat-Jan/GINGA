severity | field_path | issue | suggestion
---|---|---|---
高 | conclusion | 草案将拆书定位为“参考作品分析层”，但未明确其与核心创作流程的交互机制，可能导致分析结果与生成主链脱节，成为信息孤岛。 | 建议在结论中补充分析层如何向主链提供“已验证”的输入（如通过审核的技法模式），并明确一个从分析结果到创作提示（prompt example）的正式提升（promotion）流程，确保分析价值能被主链消费。
高 | architecture.RAG | 草案提出RAG使用“sidecar index”，但未定义其与默认RAG的隔离机制和调用策略，存在无意污染默认召回的风险。 | 建议明确sidecar index的物理存储路径（如`.sidecar_rag/`）、独立的召回配置，并仅在`book_analysis_pipeline`等特定workflow中显式启用该索引，避免在通用生成步骤中被默认调用。
中 | priority.P0 | 将“D1-D12 schema”列为P0，但其作为“手填拆书框架”，成熟度低。过早将其作为基础schema引入，可能因后续频繁变更而影响依赖它的其他P0/P1功能。 | 建议调整优先级：P0仅保留“章节拆分”和“文风指纹”等数据提取基础能力。将D1-D12 schema降为P1，作为分析产物的输出格式之一进行原型验证，待结构稳定后再考虑提升为Foundation资产。
中 | risk.copyright | 草案识别了“桥段搬运”风险，但未提出具体的技术防护措施，仅依赖“人工确认”。在自动化流程中，存在通过RAG或prompt example间接泄露的风险。 | 建议在架构中增加“来源标记与过滤”机制。所有来自参考作品的分析片段和派生模式必须携带强来源标记。在生成主链的RAG召回和prompt组装阶段，应具备基于配置过滤特定来源内容的能力。
中 | implementation.boundary | 草案强调“不写目标作品runtime_state”，但未禁止分析层写入自己的分析状态。若使用`StateIO(book_id="analysis-<source>")`，可能模糊“创作状态”与“分析状态”的边界，增加系统复杂性。 | 建议明确规定分析workflow不通过`StateIO`写入任何`runtime_state`域。所有分析产物仅作为`artifact`写入文件系统（如`.ops/book_analysis/`），并通过路径引用，彻底隔离状态管理。
中 | risk.robustness | 草案指出拆书脚本对“空章节、中文引号”等处理不健壮，但未将其列为实施前置条件。若直接基于现有逻辑构建provider，会引入基础质量风险。 | 建议在Phase 1“离线纯函数化”中，将“空输入测试”、“异常格式处理”、“依赖缺失降级”作为provider原型实现的强制验收标准，并编写对应的单元测试，否则不予集成。
低 | phase_plan.Phase4 | “长期skill化”的触发条件（独立contract、长期维护需求）描述模糊，可能导致未来架构决策摇摆。 | 建议明确量化或场景化的触发条件，例如：“当分析能力需要维护超过X个独立配置项”、“当需要与超过Y个其他capability进行复杂编排时”，再启动skill适配评估。
低 | priority.matrix | 将“展示脚本”和`fix_dialogue.py`列为“低价值或不建议”，但`fix_dialogue.py`可能包含有价值的校准逻辑。直接放弃可能遗漏可复用的算法。 | 建议在Phase 1中，将`fix_dialogue.py`的核心算法（如对话比例重算逻辑）抽象为独立的校准函数进行评估。如果算法有效，可将其作为“style lock校准建议”的一部分，而非直接迁移脚本。
低 | implementation.testing | 草案提到“tempdir测试”，但未涵盖对大型参考作品（如超长网络小说）的分析性能与资源消耗测试，可能存在运行时风险。 | 建议在Phase 2的可选workflow/CLI开发中，加入对大型输入文件的性能基准测试和内存使用监控，并设定合理的超时与中断机制，确保分析任务可控。
中 | architecture.Foundation | 草案提到分析结果经“人工确认”后可成为Foundation派生资产，但未定义“人工确认”的具体工作流和权限，流程存在模糊地带。 | 建议设计一个简单的“资产提升请求”（Promotion Request）流程，例如：在`.ops/book_analysis/`中生成`promotion_candidate.yaml`，需经指定角色（如项目负责人）批准后，由脚本自动迁移至Foundation相应目录。