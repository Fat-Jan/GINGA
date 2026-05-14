---
name: state-schema
purpose: state.json 统一结构定义，作为所有模块的单一事实源
version: "1.0"
---

<context>
此文件定义 state.json 的完整结构，所有涉及状态存储的模块必须引用此文件。
禁止在其他文件中重复定义或修改此结构。如需更新，请修改本文件。
</context>

<instructions>

## State.json 完整结构

```json
{
  "version": "5.0",
  "meta": {
    "title": "",
    "genre": "",
    "platform": "",
    "target_chapters": 0,
    "target_words": 0,
    "created_at": "",
    "updated_at": ""
  },
  "progress": {
    "current_chapter": 0,
    "total_words": 0,
    "last_write_chapter": 0,
    "last_write_time": null,
    "milestones": {}
  },
  "entities": {
    "characters": {
      "protagonist": {
        "name": "",
        "power": { "realm": "", "level": "", "layer": 0 },
        "location": { "current": "", "origin": "" },
        "inventory": [],
        "abilities": [],
        "status": [],
        "current_goals": [],
        "known_secrets": [],
        "recent_events": []
      },
      "active": []
    },
    "items": { "tracked": [], "protagonist_inventory": [] },
    "locations": { "current": "", "visited": [], "important": [] },
    "factions": { "active": [] }
  },
  "plot_threads": {
    "foreshadowing": { "active": [], "pending": [], "warning": [], "overdue": [], "resolved": [] },
    "suspense": { "active": [], "resolved": [] },
    "main_quest": { "target": "", "location": "", "secret": "", "progress": 0 },
    "side_quests": []
  },
  "knowledge_base": {
    "reader_knows": [],
    "protagonist_knows": [],
    "protagonist_doesnt_know": [],
    "key_revelations": []
  },
  "quality_metrics": {
    "recent_scores": [],
    "average_score": 0,
    "trend": "stable",
    "last_review_chapter": 0,
    "dimension_scores": {}
  },
  "auto_learn_config": {},
  "reading_power_state": {
    "active_hooks": [],
    "hook_history": [],
    "micro_fulfillment_log": [],
    "cool_point_log": []
  },
  "learned_patterns": {},
  "market_adjustments": {},
  "platform_config": {},
  "genre_profile": {
    "loaded": "shared/profiles/xuanhuan/profile.yaml"
  },
  "active_launch_grammar": "",
  "active_primary_pivot": "",
  "launch_stack_phase": "",
  "launch_stack_drift_signal": "none",
  "active_context": {
    "sidecar_file": ".mighty/active-context.json"
  },
  "chapter_meta": {},
  "chapter_snapshots": {},
  "summaries_index": {},
  "character_states": {},
  "setting_versions": {},
  "dungeons": {},
  "teammates": {},
  "constraints_loaded": {},
  "updated_at": ""
}
```

---

## 0.1 顶层运行时区块

除 `version` 外，当前运行态顶层区块至少包括：

- `meta`
- `progress`
- `entities`
- `plot_threads`
- `knowledge_base`
- `quality_metrics`
- `auto_learn_config`
- `learned_patterns`
- `market_adjustments`
- `platform_config`
- `genre_profile`
- `active_launch_grammar`
- `active_primary_pivot`
- `launch_stack_phase`
- `launch_stack_drift_signal`
- `active_context`
- `chapter_meta`
- `chapter_snapshots`
- `summaries_index`
- `character_states`
- `setting_versions`
- `dungeons`
- `teammates`
- `constraints_loaded`

约束：

- 这些顶层字段都应在 template / schema / docs 三处保持一致
- 如果某字段已经进入模板和运行态，不得继续只写在 template 而不更新说明文档

## 0.2 顶层元信息 (`meta`)

`meta` 负责项目级静态元信息，例如标题、题材、平台、目标规模和更新时间。

推荐字段：

- `title`
- `genre`
- `platform`
- `target_chapters`
- `target_words`
- `created_at`
- `updated_at`

## 0.3 进度区块 (`progress`)

`progress` 负责当前创作进度与里程碑。

推荐字段：

- `current_chapter`
- `total_words`
- `last_write_chapter`
- `last_write_time`
- `milestones`

## 0.4 质量统计 (`quality_metrics`)

`quality_metrics` 负责项目级 review 汇总，而不是单章长评。

推荐字段：

- `recent_scores`
- `average_score`
- `trend`
- `last_review_chapter`
- `dimension_scores`

## 0.5 自动学习配置 (`auto_learn_config`)

`auto_learn_config` 负责自动学习与自动分析阈值，不应混入 chapter 级写回。

## 0.6 平台配置 (`platform_config`)

`platform_config` 负责平台级硬边界，例如章长、黄金三章、节奏阈值。

## 一、实体结构 (entities)

## 0.7 题材配置轻量投影 (`genre_profile`)

`genre_profile` 只保留从 shared profile contract 投影出来的最小运行态字段，不保留整份 raw profile。

推荐字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| loaded | string | 当前生效 profile 路径 |
| positioning_sidecar | string | 组合题材定位 sidecar 路径，默认 `.mighty/content-positioning.json` |
| 节奏 | object | 从 profile `pacing` 投影的轻量摘要 |
| 爽点密度 | number/string | 从 profile `cool_points.density` 或兼容字段投影 |
| strand权重 | object | 从 profile `strand_weights` 投影 |
| 特殊约束 | object[] | 从 profile `constraints` 投影 |
| bucket | string | 可选，当前内容桶 |
| positioning_initialized | boolean | 是否已显式初始化组合定位字段；为 `true` 时，空数组也视为有效 override |
| tagpacks | string[] | 可选，主桶上的玩法 overlay |
| strong_tags | string[] | 可选，平台表层强标签 |
| narrative_modes | string[] | 可选，结构模式 |
| tone_guardrails | string[] | 可选，风味与质量护栏 |

约束：

- `genre_profile` 是投影层，不是 raw profile dump
- 长文本方法论、对白模板、场景模板等不应直接复制进 `state.json`
- 真正的题材源仍在 `shared/profiles/*`

### 0.8 组合题材定位 sidecar (`content-positioning`)

当项目需要承载组合题材 / 多主题卖点 / 群像结构模式时：

- `state.genre_profile` 只保留轻量镜像
- 更完整的组合定位解释应写入 `.mighty/content-positioning.json`

建议 sidecar 至少保留：

- `primary_profile`
- `primary_bucket`
- `tagpacks`
- `strong_tags`
- `narrative_modes`
- `tone_guardrails`
- `compiler_output`

### 1.1 主角结构 (entities.characters.protagonist)

```json
{
  "name": "林轩",
  "power": {
    "realm": "炼气",
    "level": "三层",
    "layer": 3
  },
  "location": {
    "current": "青云宗内门",
    "origin": "青云宗外门"
  },
  "inventory": ["青云剑", "入门令牌"],
  "abilities": ["基础剑法", "青云诀一层"],
  "status": ["健康"],
  "current_goals": ["突破炼气四层", "参加宗门大比"],
  "known_secrets": [],
  "recent_events": ["突破炼气期", "结识李青云"]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 主角姓名 |
| power | object | 境界信息（结构化） |
| power.realm | string | 境界名称（如：炼气、筑基、金丹） |
| power.level | string | 境界等级（如：一层、三层） |
| power.layer | number | 层数（用于数值比较） |
| location | object/string | 当前推荐对象形态：`{current, origin}`；兼容旧字符串形态 |
| inventory | string[] | 持有物品列表 |
| abilities | string[] | 已掌握能力/功法 |
| status | string[] | 状态标签（健康、受伤等） |
| current_goals | string[] | 当前目标列表 |
| recent_events | string[] | 最近发生的重要事件 |

### 1.2 活跃角色结构 (entities.characters.active)

```json
[
  {
    "name": "李青云",
    "role": "supporting",
    "identity": "青云宗内门弟子",
    "relationship": "师兄",
    "power": {
      "realm": "筑基",
      "level": "三层",
      "layer": 3
    },
    "first_appearance": 15,
    "last_mention": 18,
    "status": "active"
  }
]
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 角色姓名 |
| role | string | 角色类型：protagonist/supporting/antagonist/minor |
| identity | string | 身份描述 |
| relationship | string | 当前推荐的与主角关系字段 |
| relation_to_protagonist | string | 历史兼容字段，旧项目可继续读 |
| power | object | 境界信息（结构化，同主角） |
| first_appearance | number | 首次出场章节 |
| last_mention | number | 最近提及章节 |
| status | string | 状态：active/archived/dead |

### 1.3 物品结构 (entities.items)

```json
{
  "tracked": [
    "青云剑",
    {
      "name": "入门令牌",
      "type": "凭证"
    }
  ],
  "protagonist_inventory": ["青云剑", "入门令牌"]
}
```

说明：

- `tracked` 当前兼容两种形态：
  - 字符串列表
  - 带 `name` 的对象列表
- 新 consumer 应优先按“可从对象取 `name`，否则回落字符串”的方式读取

### 1.4 地点结构 (entities.locations)

```json
{
  "current": "青云宗内门",
  "visited": ["青云宗外门", "后山", "青云宗内门", "藏经阁"],
  "important": ["藏经阁"]
}
```

### 1.5 势力结构 (entities.factions)

```json
{
  "active": [
    "剑阁",
    {
      "name": "青云宗",
      "type": "宗门势力",
      "stance": "neutral",
      "relationship": "中立",
      "first_appearance": 3,
      "key_members": ["李青云", "王长老"]
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 势力名称 |
| type | string | 势力类型：宗门势力/家族/联盟/组织 |
| stance | string | 立场：friendly/neutral/hostile |
| relationship | string | 当前推荐的与主角关系描述字段 |
| relation_to_protagonist | string | 历史兼容字段，旧项目可继续读 |
| first_appearance | number | 首次出现章节 |
| key_members | string[] | 关键成员列表 |

---

## 二、剧情线索结构 (plot_threads)

### 2.1 伏笔结构 (plot_threads.foreshadowing)

```json
{
  "active": [
    {
      "id": "FS-001",
      "name": "神秘身世",
      "description": "主角的身世之谜",
      "planted_chapter": 1,
      "expected_resolve": "15-25",
      "status": "pending",
      "importance": "high",
      "mentions": [1, 5, 10]
    }
  ],
  "resolved": [
    {
      "id": "FS-002",
      "name": "玉佩秘密",
      "planted_chapter": 5,
      "resolved_chapter": 15,
      "resolution": "玉佩是上古传承之物"
    }
  ]
}
```

**伏笔状态**:

| 状态 | 说明 |
|------|------|
| planted | 刚埋设，尚未提及 |
| pending | 待回收，已有提及 |
| warning | 超期警告，接近预期回收上限 |
| overdue | 已超期，需要尽快回收 |
| resolved | 已回收 |

---

## 三、知识库结构 (knowledge_base)

```json
{
  "reader_knows": [
    "主角有神秘身世",
    "玉佩是传承之物"
  ],
  "protagonist_knows": [
    "自己有神秘身世"
  ],
  "protagonist_doesnt_know": [
    "身世真相",
    "玉佩完整功能"
  ]
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| reader_knows | 读者已知但主角可能不知道的信息 |
| protagonist_knows | 主角已知的信息 |
| protagonist_doesnt_know | 主角尚不知道的重要信息（当前推荐字段） |
| protagonist_unknown | 历史兼容字段 |

---

## 四、追读力状态结构 (reading_power_state)

### 4.1 活跃钩子 (active_hooks)

```json
[
  {
    "id": "hook_001",
    "type": "mystery",
    "introduced_chapter": 15,
    "content": "神秘玉佩的来历",
    "strength": "strong",
    "status": "active"
  }
]
```

**钩子类型**:

| 类型 | 说明 |
|------|------|
| crisis | 危机钩 |
| mystery | 悬念钩 |
| desire | 渴望钩 |
| emotion | 情绪钩 |
| choice | 选择钩 |

**钩子状态**:

| 状态 | 说明 |
|------|------|
| active | 活跃中 |
| partially_fulfilled | 部分兑现 |
| fulfilled | 已兑现 |

### 4.2 钩子历史 (hook_history)

```json
[
  {
    "chapter": 16,
    "hook_type": "crisis",
    "strength": "strong",
    "fulfilled_in": 17
  }
]
```

### 4.3 微兑现日志 (micro_fulfillment_log)

```json
[
  {
    "chapter": 16,
    "types": ["MF-02", "MF-04"],
    "count": 2,
    "details": ["与女主关系进展", "获得灵石奖励"]
  }
]
```

**微兑现类型**:

| ID | 类型 |
|----|------|
| MF-01 | 信息兑现 |
| MF-02 | 关系兑现 |
| MF-03 | 能力兑现 |
| MF-04 | 资源兑现 |
| MF-05 | 认可兑现 |
| MF-06 | 情绪兑现 |
| MF-07 | 线索兑现 |

### 4.4 爽点日志 (cool_point_log)

```json
[
  {
    "chapter": 16,
    "pattern": "CP-01",
    "execution": "complete",
    "intensity": "high"
  }
]
```

**执行状态**:

| 状态 | 说明 |
|------|------|
| complete | 完整执行 |
| partial | 部分执行 |
| failed | 执行失败 |

---

## 五、章节快照结构 (chapter_snapshots)

```json
{
  "15": {
    "chapter": 15,
    "created_at": "2026-03-14T10:30:00Z",
    "word_count": 5200,

    "protagonist_state": {
      "name": "林轩",
      "power": {
        "realm": "炼气",
        "level": "三层",
        "layer": 3
      },
      "location": {
        "current": "青云宗内门",
        "previous": "青云宗外门"
      },
      "inventory": ["青云剑", "入门令牌", "神秘玉佩"],
      "abilities": ["基础剑法", "青云诀一层"],
      "status": ["健康"],
      "current_goals": ["突破炼气四层", "参加宗门大比"]
    },

    "active_characters": [
      {
        "name": "李青云",
        "role": "师兄",
        "relation": "友好",
        "last_interaction": 15
      }
    ],

    "active_foreshadowing": [
      {
        "id": "FS-001",
        "name": "神秘身世",
        "status": "pending",
        "planted_chapter": 1
      }
    ],

    "knowledge_state": {
      "reader_knows": ["主角有神秘身世", "玉佩是传承之物"],
      "protagonist_knows": ["自己有神秘身世"],
      "protagonist_doesnt_know": ["身世真相", "玉佩完整功能"]
    },

    "new_entities": [
      {"type": "character", "name": "王长老", "role": "minor"},
      {"type": "location", "name": "藏经阁三层"}
    ],

    "key_events": [
      "林轩进入藏经阁",
      "发现功法秘籍",
      "与王长老对话"
    ],

    "summary": "林轩在李青云的引荐下进入藏经阁，获得重要功法，同时埋下新的伏笔。",

    "quality_metrics": {
      "overall": 82,
      "dimensions": {
        "爽点": 85,
        "一致性": 80,
        "节奏": 78,
        "OOC": 90,
        "连续性": 85,
        "追读力": 75
      }
    }
  }
}
```

---

## 五、章节元数据扩展约定 (chapter_meta)

`chapter_meta` 保持可扩展，但扩展必须落在单章级，不得额外新造平行顶层状态中心。

推荐字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| review_score | number | 当前章节总评 |
| review_grade | string | 当前章节评级 |
| review_time | string | 最近 review 时间 |
| needs_fix | boolean | 当前章节是否仍需要局部修补 |
| dimension_scores | object | 评审维度分数 |
| issue_clusters | object[] | review 收敛出的可执行问题簇，供 close/fix/rewrite 消费 |
| recommended_next_action | string | `none/fix/polish/rewrite/write` 等路由建议 |
| chapter_structure | object | 可选结构摘要，记录本章冲突/主角弧线/对手模式/收获/代价/章末风格 |
| anti_flattening_flags | string[] | 反脸谱化风险标签，保持轻量 |
| anti_flattening_summary | object | 可选结构摘要，记录主角特权、关系、阵营、代价链等问题 |
| fanqie_bucket_flags | string[] | 命中番茄 bucket 时的轻量风险标签 |
| fanqie_bucket_summary | object | 可选 bucket 级摘要，记录当前主故障与红灯 |
| content_standard_flags | string[] | 当前章节明确命中的内容标准失格标签 |
| packaging_alignment_note | string | 当前章节与外层包装承诺的轻量对齐说明 |
| active_launch_grammar | string | 当前生效的起盘语法，详细结果见 `.mighty/launch-stack.json` |
| active_primary_pivot | string | 当前主要起盘支点，详细结果见 `.mighty/launch-stack.json` |
| launch_stack_phase | string | 当前起盘协议栈阶段，如 `draft/locked/reselected` |
| launch_stack_drift_signal | string | 当前起盘协议栈漂移信号，如 `none/watch/strong` |
| last_close_time | string | 最近一次 `novel-close` 执行时间 |
| last_close_route | string | 最近一次 `novel-close` 选择的主路由 |
| last_close_review_score_before | number | 最近一次 `novel-close` 首轮 review 分数 |
| last_close_review_score_after | number | 最近一次 `novel-close` 末轮 review 分数 |

### 反脸谱化轻量约定

- `issue_clusters` 不应长期表现为“高分 + 空数组 + 继续写”；若反复出现，应视为 review artifact 假阳性信号
- `recommended_next_action` 与 `needs_fix` 应同时存在；不要只给分数，不给路由结论
- `chapter_structure` 只保留轻量可枚举字段，不在 `state` 里复制整份章纲分析
- 当前推荐的 6 个结构键是：
  - `conflict_type`
  - `protagonist_arc`
  - `opponent_mode`
  - `gain_type`
  - `cost_visibility`
  - `chapter_end_style`
- `anti_flattening_flags` 只记录明显结构风险，不做大段分析存储
- `anti_flattening_summary` 只有在 review 明确识别到关键问题时才写
- 不为反脸谱化单独创建新的顶层 state 区块

### 番茄 bucket 轻量约定

- `fanqie_bucket_flags` 只在 bucket 级红灯清晰时写
- `fanqie_bucket_summary` 只保留主故障、红灯和 bucket 档位，不存长段评语
- 不为 bucket 专项检查单独创建新的顶层 state 区块

### 写作基本功压缩信号约定

- `learned_patterns.opening_strategy` 只保留当前项目可执行的开篇策略
- `learned_patterns.multi_line_guardrails` 只保留当前项目仍在生效的多线编排提醒
- `learned_patterns.content_standard_alerts` 只保留重复出现、值得下游消费的失格提醒
- `chapter_meta[N].content_standard_flags` 只在单章失格明确时写
- `chapter_meta[N].packaging_alignment_note` 只保留一句包装承诺对齐判断
- 这些字段都应保持轻量，不存课程长文

### `learned_patterns` / `market_adjustments` externalize 兼容约定

- 这两块当前允许两种合法形态：
  - inline 完整对象
  - externalized pointer summary
- 当项目已经旁路到 sidecar 后，`state.json` 中推荐只保留：
  - `externalized`
  - `sidecar_file`
  - `last_updated`
  - 少量可直接判断的摘要字段
- consumer 应遵循：
  - 优先 sidecar
  - sidecar 缺失时回落到 `state` inline 数据
  - 不要假定只存在单一形态

### 起盘协议栈轻量约定

- `active_launch_grammar` / `active_primary_pivot` 只记录当前生效结论
- `launch_stack_phase` / `launch_stack_drift_signal` 只记录阶段与漂移风险
- 详细 `launch_stack` 结果、候选与 compiler 输出，应保存在 `.mighty/launch-stack.json`
- 不为起盘协议栈新增顶层长分析区块

### active_context 侧栏约定

- `active_context` 只作为 sidecar 指针与轻量摘要存在
- 详细当前写作上下文应保存在 `.mighty/active-context.json`
- `active_context` 可以保留：
  - `sidecar_file`
  - `last_built`
  - `summary_window`
  - `hook_count`
  - `guardrail_count`
- `active_context` 不是新的 truth source，不应与 `state.json`、`state-archive`、`index` 竞争事实归属

### 运行时镜像与章节账本约定

以下顶层区块当前已进入模板与运行态，应视为正式 schema 范围：

- `auto_learn_config`
- `platform_config`
- `chapter_meta`
- `chapter_snapshots`
- `summaries_index`
- `character_states`
- `setting_versions`
- `dungeons`
- `teammates`
- `constraints_loaded`

约束：

- 这些区块允许阶段性扩展，但不得再依赖“模板里有、schema 里没有”的隐式兼容
- 若后续继续扩字段，应同步更新：
  - `shared/templates/state-schema-v5.json`
  - `shared/templates/state-v5-template.json`
  - 当前说明文档

### `dimension_scores` 附加键约定

除已有质量维度外，可追加：

- `开篇抓力`
- `层次清晰度`
- `推进有效性`
- `人物立体度`
- `关系张力`
- `阵营分歧`
- `代价感`

这些键是可选增强项，不要求每次 review 全量写入，但一旦写入应保持语义稳定

---

## 六、摘要索引结构 (summaries_index)

```json
{
  "1": "主角获得金手指",
  "2": "进入宗门，开始修炼",
  "3": "突破炼气一层"
}
```

---

## 七、字段命名规范

### 7.1 命名规则

- 统一使用 **camelCase** 驼峰命名
- 禁止使用 snake_case 或 kebab-case
- 布尔字段以 `is_`、`has_` 开头（如 `is_resolved`）

### 7.2 时间戳格式

- 使用 ISO 8601 格式：`2026-03-14T10:30:00Z`
- 存储于 `updated_at` 字段

### 7.3 ID 格式

- 伏笔：`FS-001`、`FS-002`（FS = Foreshadowing）
- 事件：`E-001`、`E-002`
- 钩子：`hook_001`、`hook_002`

---

## 八、版本兼容性

### 8.1 结构变更规则

1. 新增字段：向后兼容，可直接添加
2. 删除字段：需要迁移脚本，保留废弃字段一段时间
3. 重命名字段：需要迁移脚本，同时支持新旧字段名

### 8.2 迁移示例

从旧结构（level 为字符串）迁移到新结构（power 为对象）：

```javascript
// 迁移前
"protagonist": {
  "name": "林轩",
  "level": "炼气一层"
}

// 迁移后
"protagonist": {
  "name": "林轩",
  "power": {
    "realm": "炼气",
    "level": "一层",
    "layer": 1
  }
}
```

---

## 九、引用说明

所有涉及 state.json 结构的模块必须在文档开头引用本文件：

```markdown
> **结构定义**: 参考 [state-schema.md](./state-schema.md)
```

</instructions>
