# ST-S2-L-ANNOTATION：461 prompts 标注 + 双库去重 + RAG 索引（main agent /loop dynamic）

## 给主 agent 的 loop 任务规约

**这不是 P7 prompt，是主 agent 自己 /loop dynamic 跑的任务清单**。loop 协议：每轮处理 1 batch（20 张卡），失败 endpoint failover，进度落 jsonl checkpoint，DoD 满足前持续迭代。

## 任务目标

把 `_原料/提示词库参考/prompts/` 461 个 JSON-style md 蒸馏为 `foundation/assets/prompts/<id>.md`（带统一 frontmatter，schema = `foundation/schema/prompt_card.yaml`），写入 `rag/prompt_card_index.json`。**这是 Sprint 2 真正的"全量蒸馏"动作**。

## 必读输入

- `/Users/arm/Desktop/ginga/foundation/schema/prompt_card.yaml`（frontmatter schema）
- `/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-cards.md`（已分类的 12 大 card_intent + quality 草稿）
- `/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-quality.json`（42 张已评 quality 起点）
- `/Users/arm/Desktop/ginga/.ops/scout-reports/scout3-dedup.json`（28 样本 vs 基座对比起点）

## 任务清单

### L-1 半自动化标注工具
写一个 Python 脚本 `scripts/annotate_prompt_card.py`：
- 输入：原始 `_原料/提示词库参考/prompts/<file>.md`
- 步骤：(a) 读 JSON-style 内容 → (b) 调 ask-llm windhub 抽 frontmatter（按 prompt_card schema 字段）→ (c) 落 `foundation/assets/prompts/<id>.md`（frontmatter + 原内容）
- LLM prompt 模板：固定 system 段（schema 字段 + 抽取规则）+ user 段（卡片原文）
- max-tokens=1024 / batch 内串行调用（避免并发把端点打挂）

### L-2 优先级队列
按 `scout3-quality.json` 已评级 + scout3-cards.md 推论：A/A- 卡（约 230 张）优先；B+/B（约 200）次之；C/D（约 30）最后。建一个 `.ops/sprint-2/annotation-queue.json` 文件作为 batch 拉取队列。

### L-3 batch ≤20 张/轮 + endpoint failover
每 loop 轮：
1. 从队列拉 20 张未标
2. 顺序调 LLM 抽 frontmatter（windhub 默认）
3. 失败超 3 次自动切下一个 endpoint（**failover 矩阵**：windhub → ioll-grok（-s flag） → xiaomi-tp（非流式，no -s）→ 主 agent 接管手工标）
4. 落盘 `foundation/assets/prompts/<id>.md`
5. 追加进度到 `.ops/sprint-2/annotation-progress.jsonl`（每行一条 {ts, card_id, endpoint, status, latency}）
6. 心跳追加到 `.ops/p7-handoff/ST-S2-L-ANNOTATION.md`（每 batch 一条 entry）

### L-4 双库去重三段判定
在 frontmatter 标注完后跑：
- Step 1 粗筛：asset_type / template_family / card_intent / topic 是否高度重合（与基座 544 模板比对）
- Step 2 字段相似度：fields_required / output_contract Jaccard ≥0.3 进 Step 3
- Step 3 优先级裁决：基座 > prompts; genre_specific > universal; quality 高者优
输出 `.ops/sprint-2/dedup-verdicts.json`（每卡：verdict=retain/merge/drop + dedup_against=[基座 id 列表]）

### L-5 rag/prompt_card_index.json 构建
扫 `foundation/assets/prompts/*.md` 抽 frontmatter → 建索引 `rag/prompt_card_index.json`：
```json
{
  "count": 230,
  "by_stage": {"drafting": [...], "refinement": [...]},
  "by_card_intent": {...},
  "by_quality": {"A": [...], "A-": [...]}
}
```

## Loop 退出条件（DoD）

```bash
[ $(find foundation/assets/prompts -name '*.md' 2>/dev/null | wc -l) -ge 230 ] && \
  test -f rag/prompt_card_index.json && \
  python3 -c "import json; idx = json.load(open('rag/prompt_card_index.json')); assert idx['count'] >= 230; print(f\"index count: {idx['count']}\")" && \
  test -f .ops/sprint-2/dedup-verdicts.json && \
  echo PASS
```

## Loop 协议（主 agent 自驱）

- 每 wakeup 间隔 ≥ 1200s（避开 cache miss 窗口；batch 标注耗时 ~10-15min/轮）
- 每 batch 完成立即落 jsonl checkpoint
- 心跳文件 5 分钟无 entry → 怀疑卡死，主 agent 主动检查 endpoint 状态
- max_attempts 限制：单卡 LLM 失败 5 次跨 3 endpoint 仍失败 → 标 `status=manual` 留给主 agent 后处理
- 总轮数预算：230 张 A/A- ÷ 20 = 12 轮 batch；按 1 轮 15 min = 3 小时 wall（保守估）
- 通过 DoD 即结束 loop；主 agent 验收后看板推 done

## 红线

- 不批量 sed/awk 改卡片内容；只 prepend frontmatter
- 不动 `_原料/` 原料（只读）
- 不动其他 P7 Track 写范围
- 标错的卡（frontmatter 不通过 schema lint）必须人工 review，不许 auto-accept

## 启动条件

- ST-S2-PHASE0 不阻塞 L Track（独立）
- ST-S2-R-RAG-LAYER1 完成后 L-5 索引构建能复用其 index_builder（若提前就绪）
