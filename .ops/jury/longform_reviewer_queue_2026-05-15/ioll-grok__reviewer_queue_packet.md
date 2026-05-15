**## 总体判定**

- **是否确认存在批量生成漂移**：是。queue 中 08-30 章（除少数例外）普遍出现高度同构的“骨髓痛觉→睁眼灰白视野→无天空/大地→悬浮尘埃/微粒→失忆+短刃+体内植入+天堑边缘”模板，连续多章开头几乎仅改 1-2 个形容词，属于典型的续写被误判为重开篇的批量漂移。

- **5 章推荐 / 7 章上限是否仍成立**：不成立。当前 reviewer_queue_count=21 已远超上限，漂移从 chapter_08 开始持续至 chapter_30，表明 5 章批量策略已失效，7 章上限需调整为更保守的 3-4 章（或触发更早的 state anchor 重置）。

- **是否需要人工终审**：是，必须。存在 P0 级问题（短章、禁词、伏笔标记缺失）及系统性 continuity 破坏，需人工决定重写范围与后续 prompt/state 干预。

**## 章节裁决表**

| chapter     | severity     | verdict                          | human_action                          | evidence |
|-------------|--------------|----------------------------------|---------------------------------------|----------|
| chapter_19.md | P0          | 必须重写或丢弃                  | 人工重写或删除，检查后续章节衔接    | short_chapter (2325 字 < 2400 阈值) + opening_loop_risk + missing_low_frequency_anchor |
| chapter_24.md | P0          | 必须重写                        | 人工修订 + 补伏笔标记                | opening_loop_risk + missing_foreshadow_marker (无 <!-- foreshadow: marker) |
| chapter_25.md | P0          | 必须重写                        | 人工修订 + 移除禁词                  | opening_loop_risk + forbidden_style_hit (叮=1) + missing_low_frequency_anchor |
| chapter_08.md | P1          | 保留骨架但需修订                | 人工或外部模型二次细审开头          | opening_loop_risk (典型“痛觉从骨髓炸开…无明睁开眼…灰白视野…天堑边缘…短刃…微粒”模板) |
| chapter_09.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_10.md | P1          | 保留骨架但需修订                | 人工修订开头模板                     | opening_loop_risk (类似模板) |
| chapter_11.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_13.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_14.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_15.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_16.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_17.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_18.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_20.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_21.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_22.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_23.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_26.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_27.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk |
| chapter_29.md | P1          | 保留骨架但需修订                | 人工修订 + 补低频锚点                | opening_loop_risk + missing_low_frequency_anchor |
| chapter_30.md | P1          | 保留骨架但需修订                | 人工修订                             | opening_loop_risk（模板延续） |

**## 跨章共性问题**

1. **P0 级：批量生成漂移与 continuity 崩坏**（chapter_08~30 普遍）——几乎每章均以近乎相同的“痛觉从骨髓深处炸开/渗出→无明睁开眼→灰白浑浊视野→无天空/大地→悬浮尘埃/微粒→失忆+短刃+体内植入+天堑边缘”句式开头，属于典型的续写被 gate 误判为重开篇，已形成系统性循环。

2. **P0 级：低频题材锚点丢失**（chapter_09,11,13,15,18,20,23,25,29 等）——血脉、多子多福、繁衍契约、末日在多数章节中完全缺失或仅弱化提及，导致 jiujiu-combo-smoke 核心组合题材被玄幻黑暗主轴稀释。

3. **P1 级：短章与质量下滑**（chapter_19）——2325 字远低于 gate 阈值，疑似批量后段疲软。

4. **P1 级：伏笔标记缺失**（chapter_24）——无 foreshadow_marker，后续状态快照与回收难以追踪。

5. **P1 级：禁词命中**（chapter_25）——forbidden_style_hit（叮=1），破坏风格锁。

6. **P2 级：模板化描写泛滥**——多章出现重复的“黑色斑块/鼓包/丝线/晶体”“短刃符文亮起”“影迹潜行”等段落，缺乏章节间递进与差异化冲突推进。

**## 给人工终审的优先顺序**

1. **chapter_19.md**（P0：短章+漂移+锚点缺失，最严重质量问题）
2. **chapter_25.md**（P0：禁词+漂移+锚点缺失，风格污染）
3. **chapter_24.md**（P0：漂移+伏笔标记缺失，影响后续连贯）
4. **chapter_08~11.md**（P1 批量起始段，确认漂移起点）
5. **chapter_13~18.md**（P1 集中区，检查是否可通过 state anchor 挽救）
6. **chapter_20~23.md、26~30.md**（P1 后续，评估整体重置必要性）

建议人工终审重点验证：是否需全局回滚至 chapter_07 后重新注入低频锚点与差异化 opening prompt，并将批量上限严格收紧。