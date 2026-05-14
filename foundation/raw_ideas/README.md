# foundation/raw_ideas/ ：灵感暂存区

> 来源：ARCHITECTURE §3.6（jury-3 P0）。
> 定位：schema 不兼容的灵感先扔这里；系统只做松散索引，不强制解析。

## 用途

凌晨 3 点突然冒出来的好点子，碰巧又跟现有 5 类 schema（genre_profile / template / methodology / checker_or_schema_ref / prompt_card）都不太对得上——直接落到本目录，不要被 schema 卡掉。

后续可以由作家主动把某条 raw_idea 手动 promote 为正式资产（template / prompt_card / runtime_state patch）。

## 写入约定

### 文件命名

```
foundation/raw_ideas/<YYYY-MM-DD>-<short-slug>.md
```

举例：

```
foundation/raw_ideas/2026-05-13-tomb-time-loop.md
foundation/raw_ideas/2026-05-14-dark-fantasy-bone-currency.md
```

### 内容要求

- 自由文本，不强制 frontmatter
- 不强制结构
- 不强制语言（中英文混写都行）
- 建议带一句话主题 + 几行展开 + 时间戳

### 推荐最简模板

```markdown
# <一句话主题>

时间：YYYY-MM-DD HH:MM
触发：<什么时候在哪冒出来的，可选>

<具体内容，任意展开>

可能挂的 schema：<template / prompt_card / 都不沾，可选>
```

## CLI 入口（当前已实现）

```bash
ginga idea add "<标题>"
ginga idea add "<标题>" --body "<正文>"
cat note.md | ginga idea add "<标题>" --stdin
```

当前 CLI 只实现 `idea add`：写入 markdown 文件并打印相对路径。

## 系统行为

- workflow **不会**自动消费 raw_ideas/ 内容（避免污染 state）
- CLI **不会**写 runtime_state / audit_log，也不会维护 `_index.md`
- RAG 召回**不**召回 raw_ideas/（避免半成品被注入 prompt）
- guard / checker 都不审 raw_ideas/

## 不允许做的事

- 不要把 raw_ideas/ 当 prompt 库用——它是"写下来怕忘"暂存区，不是召回源
- 不要把 raw_ideas/ 里的内容直接拷进 runtime_state——必须先走 promote 流程
- 不要批量自动化解析——保留灵感原始形态是这个目录存在的全部意义

## 关联

- ARCHITECTURE §3.6 灵感逃逸通道
- ROADMAP Sprint 1 任务 F-9
- 来源 jury-3 P0 修订
