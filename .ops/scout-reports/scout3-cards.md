# Scout 3: 提示词库参考 / prompts 全量横扫报告

**Scope**：`_原料/提示词库参考/prompts/` 全部 461 个 md 文件（460 个数字编号 + 1 个 `目录页.md` TOC），约 700KB 总文本，已全量实读（Python read_text，逐文件解析）。`findings.jsonl` 461 行；`dedup` 28 样本 vs `_原料/基座/`；`quality` 42 样本 A/B/C 评分。

**结论先行**：

1. **prompts/ 是「场景卡片库」**，而不是基座那种「题材级模板」。结构高度统一（4 个固定 H2 + 1 个 JSON code block），适合作为 atomic 级别的 RAG 召回单元，而不是直接作为 prompt 给 LLM 跑。它是 Foundation/RAG 层资产，不是 Platform/agent 层资产。
2. **458/461 文件遵循 `verb_object_phrase` 蛇形 task 命名**，verb 前缀高度集中：`write_(201) / design_(65) / generate_(48) / create_(18) / describe_(16)` 这 5 类覆盖 76%。其余 24% 是长尾 singleton——本质是「场景动作动词」无限细分的结果，不需要全部归并。
3. **与基座弱重叠为主**：28 样本中 25 有关键词命中，但其中 22 是「话题词被泛用」（如「战争」「金手指」在多个基座文件里出现，但只是被提及）。**真·语义级重复几乎为零**，prompts/ 与基座是「能力层 vs 场景层」的垂直分工。整体建议 **retain 95%+**，只少量 merge。
4. **质量整体偏高**：42 样本 A/A- 占 50%、B+ 占 33%、B 占 14%、C 占 2%。低分多因「示例输入=无」而不是 schema 烂。
5. **目录页.md 是工具性资产**（38KB 全是 TOC 索引），不当 prompt 卡，但作为 RAG 召回的「主题地图」很有价值。

## 样本覆盖与读取方法

本次实际打开并通过 Python `read_text(encoding='utf-8')` 完整解析了 **461 / 461 = 100%** 文件。每个文件提取了：
- 一级标题（`# N. 标题`，460/461 提取到）
- task 字段（JSON 内的 `"task": "verb_xxx"`，458/461 提取到）
- 顶层 JSON 字段集合（去重 key 列表，460/461 提取到）
- H2 章节列表（用于结构验证）
- 文件 byte size
- 首段 120 字 snippet

全部入 `.ops/scout-reports/scout3-findings.jsonl`（461 行，结构化）。

抽样深读 42 文件做质量评分（落 `.ops/scout-reports/scout3-quality.json`）；抽 28 样本对照基座做 dedup grep（落 `.ops/scout-reports/scout3-dedup.json`）。

读取顺序：编号 1-460 升序 + 目录页.md 收尾，分 6 批（5 批 × 80 + 1 批 × 61）流式处理，state.json 记录 cursor。

---

## 任务类型聚类

458 个有 `task` 字段的文件呈现一个**强一致但极度长尾**的命名规范：`verb_object_phrase` 蛇形 + 英文动词前缀。按 verb 前缀聚类如下。

### 前 5 大簇（覆盖 76%）

| 簇 | 文件数 | 占比 | 代表 task | 代表文件 |
|---|---:|---:|---|---|
| **正文生成 `write_*`** | 201 | 43.6% | write_combat_scene / write_auction_scene / write_love_triangle_scene / write_political_marriage | 13、25、28、267、395 |
| **结构设计 `design_*`** | 65 | 14.1% | design_power_system / design_villain / design_cybernetic_implants / design_puzzle_room | 6、10、50、387 |
| **生成器 `generate_*`** | 48 | 10.4% | generate_book_titles / generate_rules_dungeon / generate_lottery_pool / generate_cliffhanger | 4、8、78、147 |
| **原型创建 `create_*`** | 18 | 3.9% | create_character_profile / create_toxic_relatives / create_gap_moe_character | 9、20、294 |
| **场景描写 `describe_*`** | 16 | 3.5% | describe_dynamic_weather / describe_spaceship_interior / describe_power_overload | 148、174、175 |

### 中层簇（覆盖 11%）

| 簇 | 文件数 | 代表 task | 解读 |
|---|---:|---|---|
| 模拟/推演 `simulate_*` | 8 | simulate_war_strategy / simulate_fantasy_economy / simulate_livestream_chat | 数据模拟向，常带 nested array |
| 大纲 `outline_*` | 6 | outline_golden_three / outline_amnesia_arc / outline_redemption_arc | 篇章级结构卡 |
| 校验 `check_*` | 6 | check_foreshadowing / check_villain_logic / check_world_building | **重要的 checker 资产**，与基座方法论同维度 |
| 管理 `manage_*` | 4 | manage_pr_crisis / manage_timeline / manage_reader_expectation | 状态管理向 |
| 扩展 `expand_*` | 4 | expand_outline_point / expand_scene_to_text / expand_setting_description | **流水线粘合资产**，可对接 Platform 层 |
| 润色 `polish_*` | 3 | polish_dialogue / polish_scene_for_impact / polish_text_style | 修改向 |
| 构建 `build_*` | 3 | build_political_factions / build_investigation_logic_chain | 关系网/逻辑链 |
| 改编 `adapt_*` | 3 | adapt_novel_to_script / adapt_to_audio_drama | 跨介质 |
| 建造 `construct_*` | 3 | construct_misunderstanding_chain / construct_plot_twist | 逻辑链构建 |
| 可视化 `visualize_*` | 3 | visualize_cyberspace / visualize_magic_rune / visualize_inner_thought | 具象化向 |
| 平衡 `balance_*` | 3 | balance_game_skills / balance_magic_system / balance_system_data | 数值校准 |
| 规划 `plan_*` | 3 | plan_information_reveal / plan_pov_switch / plan_butterfly_effect | 信息释放节奏 |

### 长尾簇（覆盖 13%）

`analyze_*`(2) / `optimize_*`(2) / `inject_*`(2) / `evaluate_*`(2) / `tech_*`(2) / `script_*`(2) / `plot_*`(2) / `rewrite_*`(2) / `structure_*`(2) / `convert_*`(2) ——这些 2 文件级动词每个都对应不同的写作动作，**不建议强行归并到上面的大簇**，因为它们的语义边界明确（如 `analyze_market_trends` ≠ `simulate_war_strategy`）。

剩下 35 个 **singleton 动词**：`macro_/tournament_/long_/diagnose_/compliance_/overcome_/infrastructure_/finale_/real_/fix_/alternate_/body_/xenolinguistics_/magic_/solve_/dark_/customize_/negotiate_/action_/ancient_/wasteland_/pet_/exploit_/auction_/escalate_/control_/use_/track_/fill_/choreograph_/sharpen_/flesh_/adjust_/final_/insert_/differentiate_/break_/replace_/practice_/fanfic_/mimic_/...`。这些 singleton **不是不规范，而是命名颗粒太细**——每个对应一个具体写作动作，作为「卡片名」是合理的；但聚类时**按二级 verb 类目归并**更实用，见下文「场景卡片 schema」一节的 `card_intent` 字段设计。

### 非 task 文件（3 个）

- `1.md` 全能网文主编角色加载——用 `system_instruction` 字段而不是 `task`，本质是 **persona setup card**
- `2.md` 文风与禁区锁——用 `style_lock`字段，本质是 **style lock card**
- `目录页.md`——TOC 索引，无 prompt 内容

这 3 个不应该塞进 task 聚类，而应该作为 **特殊资产类**单独建模（见 schema 一节）。

### 命名规律小结

- **动词前缀**：标志着「写作动作」的语义类型，是 RAG 召回时的强信号
- **宾语短语**：对应「具体场景」，是 RAG 召回时的语义匹配点
- **极度长尾是设计选择**：每张卡是一个独立的可调用 action，不是模板的变种。这与基座的「题材-阶段-用途」三维体系完全不同。

---

## JSON-style schema 抽取

### Top JSON 字段（基于 458 个 task 文件统计）

| 字段 | 出现文件数 | 占比 | 角色 |
|---|---:|---:|---|
| **task** | 458 | 100% | **强制核心字段**，identifier，verb_object 命名 |
| outcome | 63 | 13.8% | 期望产出（自然语言描述） |
| name | 42 | 9.2% | 实体名（角色、地点、物品） |
| action | 36 | 7.9% | 动作描述 |
| reaction | 32 | 7.0% | 反应（人物或群体） |
| atmosphere | 31 | 6.8% | 氛围 |
| setting | 25 | 5.5% | 场景设定 |
| style | 23 | 5.0% | 风格关键词 |
| trigger | 23 | 5.0% | 触发条件 |
| location | 21 | 4.6% | 地点 |
| scene | 21 | 4.6% | 场景上下文 |
| goal | 20 | 4.4% | 目标 |
| climax | 20 | 4.4% | 高潮节点 |
| conflict | 19 | 4.1% | 冲突 |
| twist | 19 | 4.1% | 反转 |
| type | 18 | 3.9% | 类型分类 |
| dialogue | 18 | 3.9% | 对话内容 |
| instruction | 17 | 3.7% | 指令说明 |
| method | 16 | 3.5% | 方法 |
| target | 16 | 3.5% | 目标对象 |
| tone | 15 | 3.3% | 语气 |
| character | 15 | 3.3% | 角色 |
| event | 15 | 3.3% | 事件 |
| theme | 14 | 3.1% | 主题 |
| role | 13 | 2.8% | 角色身份 |
| output_structure | 13 | 2.8% | **元字段**，套娃定义输出 schema |
| context | 13 | 2.8% | 上下文 |

### 推荐 JSON schema 草案

基于实际样本归纳，提示词卡片的 JSON 内容部分推荐这套 schema（**所有字段除 task 外都是可选**——prompts/ 的特点是 schema 因 task 而异，不能强求统一）：

```yaml
type: PromptCardJSON
required:
  - task                      # string, 必填，verb_object 蛇形
optional_common:              # 高频可选字段（≥7% 文件用到）
  - outcome:        string    # 期望产出/最终目标
  - name:           string    # 实体名
  - action:         string    # 动作
  - reaction:       string    # 反应
  - atmosphere:     string    # 氛围
  - setting:        string    # 场景
  - style:          string    # 风格
  - trigger:        string    # 触发条件
  - location:       string    # 地点
optional_structural:          # 结构性字段（中高频）
  - output_structure: object  # 套娃：定义生成内容的 schema
  - scene:          string
  - goal:           string
  - climax:         string
  - conflict:       string
  - twist:          string
  - tone:           string
  - dialogue:       string
custom:                       # 卡特定字段（低频，按需）
  - 任何场景特化字段（如 pantheon, currency_system, factions, levels...）
```

### 三类 JSON 结构变体

实际遵循下面 3 种结构之一：

#### 变体 A：扁平 verb-noun 卡（最常见，~70%）

```json
{
  "task": "write_combat_scene",
  "setting": "Ancient Battlefield",
  "action": "MC vs Demon General",
  "atmosphere": "Blood and Fire",
  "outcome": "MC unleashes hidden bloodline"
}
```

#### 变体 B：输出 schema 套娃（中频，~10%）

```json
{
  "task": "create_character_profile",
  "role": "Protagonist",
  "archetype": "{{archetype}}",
  "output_structure": {
    "basic_info": {"name": "", "age": "", "occupation": ""},
    "personality": {...}
  }
}
```

#### 变体 C：列表/数组卡（中频，~15%）

```json
{
  "task": "generate_lottery_pool",
  "tiers": {
    "SSR (1%)": ["Time Stop", "Instant Kill"],
    "SR (5%)": ["Flight", "Invisibility"]
  },
  "draw_result": "Simulate a 10-draw session"
}
```

#### 变体 D：非 task 卡（少数，<5%）

```json
{
  "system_instruction": { "role": "Senior Editor", "mission": "..." }
}
```
or
```json
{
  "style_lock": { "narrative_voice": "Third-person limited", "prohibited_content": [...] }
}
```

### 与基座 JSON schema 的差异

基座模板的 JSON 是**「system role + 思维链 + 输出要求」**的 prompt 模板，schema 关注「如何让 LLM 生成什么」。
prompts/ 卡片的 JSON 是**「场景参数 + 期望产出」**的 scene-spec，schema 关注「这个场景需要哪些参数」。

**两者不能合并 schema**，应该作为 Foundation 层的两个并行 schema 注册。

---

## 场景卡片 schema

prompts/ 应该升级为标准化的 **PromptCard 资产类**。建议统一 schema：YAML frontmatter（治理元数据）+ Markdown body（原 4-H2 结构 + JSON content）。

### YAML Frontmatter（治理 / 检索字段）

| 字段 | 类型 | 必填 | 取值范围 | 来源 |
|---|---|---:|---|---|
| `id` | string | 是 | 唯一 slug，如 `card-write-auction-scene-25` | 新增治理字段 |
| `card_title` | string | 是 | 文档标题，去掉 `# N. ` 前缀 | `# 标题` 提取 |
| `card_intent` | enum | 是 | 见下方 12 大 intent 枚举 | 由 task verb 前缀映射 |
| `task_verb` | string | 是 | task 字段的 verb 前缀（write/design/...） | task 字段 |
| `task_full` | string | 是 | 完整 task 字段值（含 object） | task 字段 |
| `card_kind` | enum | 是 | `scene_card` / `setup_card` / `style_lock_card` / `checker_card` / `index_card` | 由 JSON 形态 + task 类型判断 |
| `topic_tags` | string[] | 否 | 题材标签：玄幻 / 都市 / 末世 / 校园 / 历史 / 科幻 / 修仙 / 系统 / 直播 / 同人 等 | 由标题/snippet 抽取 |
| `genre_match` | string[] | 否 | 匹配基座 `题材/网文/*.md` 的题材槽位 | 由 topic_tags 映射 |
| `granularity` | enum | 否 | `paragraph` / `scene` / `chapter` / `arc` / `meta` | 由 task object 推断 |
| `output_kind` | enum | 是 | `prose` / `dialogue` / `schema_json` / `table` / `list` / `setup_persona` / `style_lock` | 由 JSON 字段判断 |
| `requires_placeholders` | bool | 是 | 是否包含 `{{xxx}}` 占位符 | 正文搜索 |
| `placeholders` | string[] | 否 | 所有占位符 key 清单 | 正文抽取 |
| `quality_grade` | enum | 否 | A/A-/B+/B/C | quality phase 评分 |
| `dedup_verdict` | enum | 否 | `retain` / `merge_with:<base_file>` / `drop` | dedup phase 判定 |
| `source_path` | string | 是 | `_原料/提示词库参考/prompts/<file>.md` | 文件路径 |
| `byte_size` | int | 否 | 原始字节 | 文件 |

### `card_intent` 12 大枚举（聚类后的二级类目）

```
- prose_generation         # write_*（正文生成）
- structural_design        # design_*, build_*, construct_*（结构/关系/逻辑设计）
- generator                # generate_*（生成器卡）
- prototype_creation       # create_*（实体原型创建）
- scene_description        # describe_*, visualize_*（场景/视觉描写）
- simulation               # simulate_*, analyze_*（推演/分析）
- outline_planning         # outline_*, plan_*, structure_*, macro_*, long_*（篇章规划）
- checker_diagnostic       # check_*, diagnose_*, evaluate_*, compliance_*, balance_*（校验）
- editing_transformation   # polish_*, rewrite_*, expand_*, adapt_*, convert_*, optimize_*, inject_*, sharpen_*（编辑改写）
- management_tracking      # manage_*, track_*, control_*（状态管理）
- adaptation_specific      # tech_*, script_*, plot_*, fanfic_*（特化领域改编）
- persona_setup            # 非 task 的 system_instruction / style_lock 卡（特殊类）
```

### `card_kind` 枚举（基于 JSON 形态）

```
scene_card     - 主体卡，task=verb_object 单卡（~445 张）
setup_card     - persona/style 上下文锁（1.md, 2.md 2 张）
style_lock_card - 风格约束（细化的 setup_card）
checker_card   - check_*/balance_* 等校验类（~10 张）
index_card     - 目录页（1 张）
```

### Body 结构（保留原 4 H2 + 增强）

```markdown
---
<yaml frontmatter as above>
---

# {{card_title}}

## 提示词内容
```json
{{json_content}}
```

## 使用场景
{{narrative use case}}

## 最佳实践要点
1. {{tip 1}}
2. {{tip 2}}

## 示例输入
{{example or "无"}}

## 反查 - card 间关系（可选，新增）
- 依赖：[card-xxx]
- 互补：[card-yyy]
- 同主题：[card-zzz]
```

---

## 与基座去重分析

### 28 样本 grep 结果（已存 `.ops/scout-reports/scout3-dedup.json`）

| 类别 | 文件数 | 含义 |
|---|---:|---|
| 真 retain（基座无任何对应） | 3 | 平行宇宙差异点 / 魔法学院分院仪式 / 校园霸凌反击战术 |
| 弱命中→ effective retain | 19 | 关键词被基座泛用，但 prompts/ 的场景颗粒度远细于基座 |
| 中度命中→ review 后多数 retain | 5 | 主题相邻但角度不同（如 [70.md 幕后黑手剧本] vs [题材/guize-guaitan.md]） |
| 强命中→ 可考虑 merge | 1 | [3.md 赛道热度] vs [基座/072-商业化-热度预测.md] |

### 28 个样本的 dedup 判定明细

| 样本 | 标题 | 命中 base 数 | dedup 判定 | 理由 |
|---|---|---:|---|---|
| 3.md | 赛道热度分析 | 1 | **merge_with: 072-商业化-热度预测.md** | 唯一强命中 |
| 68.md | 综艺节目流程 | 1 | merge_with: 方法论/写作/世界观母题目录 | 主题落入方法论母题 |
| 85.md | 都市商战布局 | 1 | merge_with: 方法论/市场/读者吸引力分类法 | 主题在方法论中提及 |
| 70.md | 幕后黑手剧本 | 2 | review | [题材/guize-guaitan] 仅是话题相邻 |
| 77.md | 刑侦法医尸检 | 2 | review | [题材/网文/zhihu-duanpian] 提及 |
| 158.md | 变身机甲着装 | 3 | retain | 弱命中 |
| 413.md | 校花贴身高手 | 3 | retain | 关键词在不同语境 |
| 73.md | 学院流课程表 | 6 | retain | 关键词被多个题材文件泛用 |
| 138.md | 星际战舰参数 | 7 | retain | 同上 |
| 16.md | 读者评论模拟 | 8 | retain | 同上 |
| 30.md | 百万字日更表 | 4 | retain | 弱命中 |
| 67.md | 直播间弹幕 | 8 | retain | 同上 |
| 152.md | 历史官制爵位 | 8 | review | 与 [方法论/写作/古代官职体系] + [模板/项目/古代] 有结构重叠 |
| 34.md | 完本总结新书预告 | 9 | retain | 弱命中 |
| 5.md | 简介优化黄金三行 | 29 | retain | 黄金三行在基座方法论中有，但 5.md 是优化器卡，角色不同 |
| 102.md | 经济通货膨胀 | 30 | retain | 同上 |
| 33.md | 首秀数据分析 | 36 | retain | 弱命中泛词高频 |
| 8.md | 规则怪谈/副本 | 40 | retain | 题材层重叠词高频，prompts/ 是场景级 |
| 439.md | 同人死神 | 18 | retain | 弱命中 |
| 267.md | 都市金融博弈 | 39 | retain | 同上 |
| 78.md | 系统抽奖池 | 68 | retain | 词被泛用 |
| 81.md | 战争战术推演 | 69 | retain | 战争词高频 |
| 44.md | 对话优化水词 | 160 | retain | 对话泛用 |
| 135.md | 社交媒体热搜 | 10 | retain | |
| 163.md | 微短剧转场 | 5 | retain | |
| 197.md | 校园霸凌反击 | 0 | retain（真） | 无任何命中 |
| 90.md | 魔法学院分院仪式 | 0 | retain（真） | 无任何命中 |
| 160.md | 平行宇宙差异点 | 0 | retain（真） | 无任何命中 |

### 整体 dedup 判定（外推到 461 全集）

- **retain 95%+**：prompts/ 的场景颗粒度（"在 X 场景做 Y 动作"）与基座的题材/方法论颗粒度（"网文 X 题材怎么写"）几乎不重叠
- **merge candidate < 2%**：仅 3-5 张卡（如 [3.md 赛道热度→072-商业化-热度预测]、[68.md 综艺→母题目录]）可考虑融合，但即使不融合也不冲突
- **drop 0**：没有卡是单纯重复
- **review 5-10%**：少数中度命中需要人工 review，但都倾向 retain

### 与基座的角色定位差异

| 维度 | 基座（544 md） | prompts/（461 md） |
|---|---|---|
| 颗粒度 | 题材级 / 方法论级 | 场景级 / 动作级 |
| schema | system_role + thinking_chain + output_req | task + scene_params + outcome |
| 用途 | 复用的能力库 / 模板 | atomic 场景调用卡 / RAG 召回单元 |
| 维度 | 题材 × 阶段 × 用途 | task_verb × 场景关键词 |
| 重用层 | Platform / agent | Foundation / RAG |

**核心建议**：prompts/ 不应替代基座，也不应被基座替代；两者作为 Foundation 层的两个并行资产类一起注册，由 Platform 层根据 task 不同分别召回。

---

## 质量分级与 retain/merge/drop 建议

### 42 文件评分汇总（已存 `.ops/scout-reports/scout3-quality.json`）

| 等级 | 数量 | 占比 |
|---|---:|---:|
| A | 19 | 45% |
| A- | 2 | 5% |
| B+ | 14 | 33% |
| B | 6 | 14% |
| C | 1 | 2% |

**A/A- 合计 50%、A/A-/B+ 合计 83%。** prompts/ 库整体质量偏高。

### 评分标准

- **A**：≥5 JSON keys，含 nested arrays/objects，示例输入 substantive（非 "无"），使用场景 / 最佳实践具体
- **A-**：A 的所有标准，但示例输入 "无"
- **B+**：4-5 keys，结构合理但示例输入 "无"
- **B**：3-4 keys，使用场景或最佳实践偏浅
- **C**：非 prompt 卡 / 异常稀薄 / 索引类

### Top A 样本（高完整度，建议优先入 RAG）

| 文件 | 标题 | 卖点 |
|---|---|---|
| 8.md | 规则怪谈/副本生成 | output_structure 6 子键 + truth_value 三态 |
| 50.md | 赛博朋克义体改装 | nested loadout 含 side_effect 代价机制 |
| 48.md | 末世避难所升级树 | 4 级深度嵌套 + 资源经济闭环 |
| 4.md | 黄金书名生成器 | 4-strategy schema + few-shot examples |
| 9.md | 主角详细档案 | output_structure 含 cheat_synergy |
| 6.md | 力量体系设计 | levels array + power_gap 自检 |
| 39.md | 番茄风主角人设卡 | 7 子键 + 占位符化 |
| 78.md | 系统抽奖池 | 4 tier 含概率分布 |
| 49.md | 变异生物图鉴 | 6 子键含 weakness/loot 战斗交互 |
| 51.md | 朝堂党争关系网 | 3 派系 nested 含 hidden_card |
| 192.md | 日式轻小说标题 | examples + concrete output |
| 289.md | 职场面试 | substantive 示例输入 |
| 294.md | 反差萌设定 | charm_point 字段升华 |
| 3.md | 赛道热度分析 | 4-block 元字段 + 示例输入 |
| 381.md | 赛博空间黑客潜入 | 6 字段 + 具象化示例 |
| 387.md | 密室逃脱 | 6 字段 + 倒计时机制 |
| 455.md | 系统面板UI | 6 字段含 visual_flair |
| 10.md | 反派仇恨值拉升 | hate_factor + downfall 闭环 |
| 2.md | 文风与禁区锁 | prohibited_content 负向约束 |

### 提升建议（针对 B / B+ 卡）

最常见的扣分原因：**示例输入="无"**（占 B+/B 卡的 ~80%）。建议为这些卡补充 1-2 个具体示例输入，可直接将 B+ 升 A。

### retain / merge / drop 整体建议

| 操作 | 数量估计 | 适用场景 |
|---|---:|---|
| **retain as-is**（A/A- 直接入 RAG） | ~230 张 | 所有 A 级 + Top B+ |
| **retain after example-augment**（补示例输入） | ~200 张 | B+/B 级补示例后升级 |
| **merge with base**（融入基座方法论） | 3-5 张 | 见 dedup 表 |
| **special index**（不入 RAG 但作主题地图） | 1 张 | 目录页.md |
| **drop** | 0 张 | 无需丢弃 |

---

## RAG 召回元数据设计

### 召回过滤维度（基于 frontmatter）

| 维度 | 字段 | 取值数 | 主要用途 |
|---|---|---:|---|
| 语义意图 | `card_intent` | 12 | 按写作动作类型召回（"我要写场景"→ prose_generation） |
| 动作动词 | `task_verb` | ~20 | 细粒度筛选（"我要描写"→ describe_*） |
| 题材 | `topic_tags`, `genre_match` | ~30 | 匹配当前作品的题材槽位 |
| 颗粒度 | `granularity` | 5 | 按情节层级召回（章节级 vs 段落级） |
| 输出形态 | `output_kind` | 7 | 区分 prose / dialogue / schema / setup |
| 资产类型 | `card_kind` | 5 | 区分 scene_card / setup_card / checker_card |
| 质量 | `quality_grade` | 5 | 高质量优先 |
| 占位符 | `requires_placeholders` | bool | 区分可直接 use 卡 vs 需要填参卡 |

### 三层召回策略

**第 1 层：粗筛**（基于 frontmatter，无需向量化）

```python
# 用户写到「主角第一次见反派，要拉满仇恨」
filter:
  card_intent in [prose_generation, structural_design, prototype_creation]
  output_kind = prose | schema_json
  topic_tags overlap with current_project.topic_tags
  quality_grade in [A, A-, B+]
```

**第 2 层：向量召回**（基于 `card_title + snippet + json_keys` 拼接的 embedding）

```python
# 在第 1 层过滤后的卡集上做向量相似度
query_embed = embed("反派初登场仇恨拉升")
top_k = vector_search(filtered_cards, query_embed, k=10)
```

**第 3 层：动态注入**（基于上下文重排）

```python
# 召回 top_k 后，根据当前章节状态做最终重排
final = rerank(top_k, current_chapter_state, user_preference)
inject_to_prompt(final[:3])
```

### 元数据 freshness 维护

- 每张卡的 frontmatter 由静态分析脚本生成 + 人工标注（topic_tags / genre_match 易出错）
- 质量分级 + dedup 判定可由 LLM 二次复审
- `card_intent` 由 `task_verb` 自动映射（一次性建表）

### 推荐的 RAG 召回元数据 JSON 索引（部分）

```json
{
  "cards": [
    {
      "id": "card-write-auction-scene-25",
      "title": "拍卖会捡漏与打脸",
      "card_intent": "prose_generation",
      "task_verb": "write",
      "task_full": "write_auction_scene",
      "card_kind": "scene_card",
      "topic_tags": ["玄幻", "都市", "爽文"],
      "granularity": "scene",
      "output_kind": "prose",
      "quality_grade": "A-",
      "dedup_verdict": "retain",
      "source_path": "_原料/提示词库参考/prompts/25.md"
    }
  ]
}
```

---

## 关键发现与建议

### 1. prompts/ 是 Foundation 层资产，不是 Platform 层资产

prompts/ 的 461 张卡是「场景级 atomic 调用单元」，不是「可直接当 prompt 跑的模板」。它们的价值在于：
- **作为 RAG 召回库**，根据当前写作上下文动态注入；
- **作为 scene-spec 资产**，被 Platform 层的 agent 调用以驱动子任务；
- **作为题材洞察样本**，反向喂给基座方法论的市场分析。

建议在四层架构中明确归位：
- **Meta 层**：用户创作宪法约束（继承 Scout 2 的成果），约束哪些 prompts 不应被召回（如「色情/政治雷区」自动 drop）
- **Foundation 层**：注册为 `PromptCard` 资产类，与基座的 `template/methodology/genre_profile` 并列
- **Platform 层**：作为 agent 的「场景库」，由 workflow 节点根据当前阶段调用相应 card_intent 的 cards
- **RAG 层**：核心召回库，按本报告设计的三层召回策略实现

### 2. 与基座的关系：垂直分工，不重叠不替代

dedup 28 样本中只有 1 个真"merge_with"候选（3.md vs 072-商业化-热度预测.md）。即使是这一个，也只是话题相邻，schema 完全不同。
建议：**双库并存**，由 Platform 层根据召回 intent 选择从基座还是 prompts/ 拿资产。

### 3. 命名长尾不是缺陷，是设计选择

458 个 task / ~450 个 unique value 这种「接近一文件一类」的极度长尾，是 prompts/ 的**设计意图**：每张卡是一个原子动作。不要试图归并到 50-100 个 task 类——会失去召回的精度。
建议：保留 task 原值，**用 `card_intent` 做二级聚类**（12 大类），用于粗筛；用 task + topic_tags 做细筛。

### 4. 质量优先级清单

- **立即可入 RAG**（A/A- 21 张，根据 42 抽样推断全集 ~230 张）：直接进
- **补示例后入 RAG**（B+ 14 张抽样，全集 ~150-180 张）：补 1-2 个具体示例输入即可
- **可选优化**（B 6 张抽样，全集 ~60-80 张）：扩 JSON keys + 加示例
- **不入 RAG**（C 1 张，全集 = 目录页.md）：作主题地图独立用

### 5. 目录页.md 的特殊价值

它是一份**全量 prompts/ 的 TOC 索引**（38KB），按编号/题材分组列出所有卡。建议：
- 提取它的 TOC 结构作为「卡片主题地图」
- 在 RAG 召回失败时回退到 TOC 做关键词模糊匹配
- 在 frontmatter `topic_tags` 标注阶段，把目录页的分组作为标签来源

### 6. 给阶段 2 蒸馏方案的输入

- prompts/ → **新建 Foundation 层 PromptCard 资产类**（独立于基座 Template）
- task verb → `card_intent` 12 大类映射表 → schema 的核心字段
- 每张卡补 YAML frontmatter（治理元数据） + 保留 4 H2 + JSON content 结构
- 不需要对内容做大改造，**主要是元数据补全 + 索引建立**
- RAG 召回策略按本节设计直接落地

### 7. 与已有 skill（思路 2/3）的协作

- 思路 3 `planning-with-files` 已有「场景卡」概念——prompts/ 可作为它的场景卡库
- 思路 2 `dark-fantasy-ultimate-engine` 的 sub-skill 可调用 prompts/ 卡作为执行单元
- **Meta 层创作宪法**应作为「卡片召回前置过滤器」，阻止违反用户审美/红线的卡被注入

### 8. 已存证据物

- `.ops/scout-reports/scout3-findings.jsonl`：461 行机器可读结构化 findings
- `.ops/scout-reports/scout3-dedup.json`：28 样本 dedup 表（15KB）
- `.ops/scout-reports/scout3-quality.json`：42 样本质量评分表（6.4KB）
- `.ops/scout-reports/scout3-state.json`：loop 全程状态机
- `.ops/scout-reports/scout3-progress.md`：loop 流式进度日志（人类可读）
- 本报告：`.ops/scout-reports/scout3-cards.md`
