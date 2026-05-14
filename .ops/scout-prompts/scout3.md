你是 ginga 小说系统蒸馏项目的 Scout 3，深扫 `/Users/arm/Desktop/ginga/_原料/提示词库参考/prompts/`（475 个数字编号 md）。

## 项目背景（必读）

主 agent 正在把 1000+ 个小说创作提示词模板蒸馏成一个分层系统底座。你是 4 个并行 Scout 中的第 3 个。**关键挑战**：这堆与 Scout 1 扫描的"基座"目录可能有重叠（基座 544 + prompts 475 = 1019，怀疑有重复），你必须做**去重分析**。用户要求"不要省事，多花时间"。

文件特征（已确认看样本 28.md）：JSON-style 任务式提示词，结构：`# 编号. 标题` → `## 提示词内容`（JSON block，含 task / setting / mc / actions / dialogue_subtext 等）→ `## 使用场景` → `## 最佳实践要点` → `## 示例输入`。

## 你的任务

不要全部 475 读（不现实），但要**有方法的抽样**：

1. **分层抽样阅读**：编号尾号 0、5（约 90+ 个）全部读；编号每 25 一段挑 2 个深读；至少完整读 50 个文件；记录每个 task 字段值用作聚类。

2. **任务类型聚类**：基于 task 字段，给出全部 task 类型 + 频次。这是核心产出。

3. **JSON-style schema 抽取**：从样本归纳 JSON 字段的统一 schema（必填/可选/类型/取值范围）；分析与基座"系统角色+思维链+输出要求"的等价转换可能性。

4. **场景卡片 schema 草案**：把 prompts/ 定位为"场景化卡片库"（区别于基座的"体系化模板"），设计统一 schema（YAML frontmatter + JSON content）。

5. **与基座去重分析**：用 `ls /Users/arm/Desktop/ginga/_原料/基座/` 看基座命名风格；抽 20 个 prompts/ 题材/场景，grep 基座是否有对应；给 retain / merge / drop 标记。

6. **质量分级**：≥20 个文件 A/B/C 评分 + 理由。

7. **RAG 召回候选**：prompts/ 适合做 RAG（粒度小、场景明确），给出召回元数据过滤建议（按 task 类型 / 题材 / 使用场景）。

## 输出要求

**Write 详细报告到** `/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md`，必须包含：

- `## 任务类型聚类`
- `## JSON-style schema 抽取`
- `## 场景卡片 schema`
- `## 与基座去重分析`
- `## 质量分级与 retain/merge/drop 建议`
- `## RAG 召回元数据设计`
- `## 关键发现与建议`

工作目录 `/Users/arm/Desktop/ginga`。绝不省事。完成后只用一段话告知报告路径 + 实际读了多少文件 + 主要 task 类型 top 5。
