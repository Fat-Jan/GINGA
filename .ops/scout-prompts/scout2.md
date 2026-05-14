你是 ginga 小说系统蒸馏项目的 Scout 2，深扫 `/Users/arm/Desktop/ginga/_原料/思路/`（3 个文件）。

## 项目背景（必读）

主 agent 正在把 1000+ 个小说创作提示词模板蒸馏成一个分层系统底座（Meta → Foundation → Platform → RAG 四层）。你是 4 个并行 Scout 中的第 2 个，负责"思路"目录——这是**最高优先级**目录，承载用户的创作哲学，要落到顶层 Meta（创作宪法）。用户要求"不要省事，多花时间"。

思路目录的关键判断（主 agent 已初步识别）：
- `待整理思路1` — 10 条 AI 专家级 SOP（搜索/答题/排版/语气）
- `待整理思路 2` — 用户**已写好的完整 Claude skill**：`dark-fantasy-ultimate-engine`（玄幻全栈引擎）
- `待整理思路 3` — 用户**已写好的另一个完整 Claude skill**：`planning-with-files v9.2.0-repo-grounded`

**用户已在自己真实小说项目里跑这两个 skill。蒸馏不能重新发明，必须做差异分析。**

## 你的任务

3 个文件每个**完整读完**（思路 2/3 可能很长，必须分段读完整），深度心智解码：

1. **思路 1 - 10 条 SOP 提炼**：列出全部规则，提炼为可注入的"元规则"，分必须做/必须不做。

2. **思路 2 - dark-fantasy-ultimate-engine skill 完整画像**：名称、定位、目标语气、任务判定逻辑（正文/设定/审查/账本）、信息源优先级、核心设定关键词、锁定/禁止风格、所有 sub-skill 名、好/雷判定标准。

3. **思路 3 - planning-with-files skill 完整画像**：版本号、定位、文件化工作流原则、具体目录约定（character_relationships.md / task_plan.md / findings.md / progress.md / 小说资料 / 57小说 等）、allowed-tools、hooks、隐式自检规则。

4. **跨文件归纳 - 用户创作宪法**：核心审美（去 AI 味/凶性/压迫感/高反馈/强因果）、核心红线（不丢上下文/不伪造已读/不滥用联网/不暴露思维链）、工作流哲学、角色定位。

5. **与基座/提示词库的关系**：思路 2/3 的 sub-skill 名在基座目录里能否找到对应？已有体系覆盖哪些原料？蒸馏边界（必须新增/只能增强/不能替代）。

## 输出要求

**Write 详细报告到** `/Users/arm/Desktop/ginga/.ops/scout-reports/scout2-doctrine.md`，必须包含：

- `## 思路 1 - 10 条 SOP`
- `## 思路 2 - dark-fantasy-ultimate-engine 画像`
- `## 思路 3 - planning-with-files 画像`
- `## 用户创作宪法`（≥10 条核心原则）
- `## 已有 skill 画像`
- `## 与原料其他部分的关系`
- `## 关键发现与建议`

工作目录 `/Users/arm/Desktop/ginga`。绝不省事——"自利偏差会导致标准滑坡"。完成后只用一段话告知报告路径 + 是否完整读完 3 个文件。
