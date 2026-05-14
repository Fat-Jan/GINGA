"""ginga Sprint 1 + Sprint 2 demo pipeline.

这是 CLI real LLM demo path，保留简化 wire-up；不是完整 workflow DSL
production runner。

MVP 切片（Sprint 1）：
    - init_book: 用 StateIO 写初始 locked + entity_runtime 域
    - run_workflow: 加载 state → 构造 prompt → 调 ask-llm → 落 chapter_NN.md + state 更新 + audit
    - show_status: 打印 state 摘要

Sprint 2 扩展（ST-S2-S-MULTI-CHAPTER）：
    - run_workflow 支持 chapter_no 参数，按章节滚动更新 entity_runtime：
        - CHARACTER_STATE.protagonist.events 追加本章关键事件
        - FORESHADOW_STATE.pool 既有 hook 检查 expected_payoff 是否触发；新增 hook 由 LLM 输出抽取
        - RESOURCE_LEDGER.particles delta 累加（用 op_translator）
        - GLOBAL_SUMMARY.total_words delta 累加
        - GLOBAL_SUMMARY.arc_summaries 每 5 章追加一条 arc 总结
    - 抽出 apply_chapter_rollup helper，便于 multi_chapter.py 调用 + 测试覆盖
    - run_workflow 仍保留简化路径（不走 step_dispatch），方便单章 LLM 调用调试；
      完整 12 step + R1/R2/R3 + V1 由 multi_chapter.py 包装

简化说明：
    - 不跑完整 12 step（A-F 设定步骤的 mock 已在 init 内完成；G 真调 LLM；H/R/V 用 audit log 标记）
    - adapter.input_transform 的复杂数据组织由本模块直接做（S2 末完善 adapter wire-up）
    - LLM 默认走 windhub (deepseek-v3.2)，可 --llm-endpoint 切换
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.runner.op_translator import (
    adapter_ops_to_state_updates,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


# ---------- execution mode ---------------------------------------------------


MOCK_HARNESS_MODE = "mock_harness"
DETERMINISTIC_EVAL_MODE = "deterministic_eval"
REAL_LLM_DEMO_MODE = "real_llm_demo"


def _mock_chapter_text(chapter_no: int, word_target: int) -> str:
    """Deterministic offline chapter body used by the P2-5 harness."""
    table = (
        "| 写作自检 | 内容 |\n|---|---|\n"
        "| 当前锚定 | mock_harness / 微粒 / 天堑 |\n"
        f"| 当前微粒 | {chapter_no * 10} |\n"
        f"| 预计微粒变化 | {chapter_no * 10} |\n"
        "| 主要冲突 | 离线 harness 验证 CLI 与 StateIO 边界 |\n\n"
    )
    body_unit = (
        f"# 第{chapter_no}章 · 离线演练\n\n"
        "这是一段 mock harness 章节正文，只用于验证 CLI、StateIO、audit_log 和 artifact 边界。"
        "它不调用真实 LLM，也不代表真实创作质量或生产链路完成。"
    )
    repeated = body_unit * max(3, min(16, word_target // 80))
    hook = (
        f"\n\n<!-- foreshadow: id=fh-mock-{chapter_no:02d} planted_ch={chapter_no} "
        f"expected_payoff={chapter_no + 10} summary=mock harness chapter {chapter_no} hook -->\n"
    )
    return table + repeated + hook


def _call_llm_or_mock(
    prompt: str,
    endpoint: str,
    *,
    max_tokens: int = 4096,
    mock_llm: bool = False,
    chapter_no: int = 1,
    word_target: int = 3500,
) -> tuple[str, str]:
    if mock_llm:
        return _mock_chapter_text(chapter_no, word_target), MOCK_HARNESS_MODE
    return _call_llm(prompt, endpoint, max_tokens=max_tokens), REAL_LLM_DEMO_MODE


def _state_io_kwargs(state_root: Path | str | None) -> dict[str, Any]:
    return {"state_root": state_root} if state_root is not None else {}


# ---------- init_book --------------------------------------------------------


def init_book(
    book_id: str,
    topic: str,
    premise: str,
    word_target: int,
    *,
    state_root: Path | str | None = None,
) -> None:
    """初始化书：建空 state + 写入 locked + entity_runtime seed."""
    sio = StateIO(book_id, **_state_io_kwargs(state_root))

    # locked 域 seed（用户决策后锁定，禁止 patch 流程外修改）
    sio.apply(
        {
            "locked.STORY_DNA.premise": premise,
            "locked.STORY_DNA.conflict_engine": "失忆刺客 vs 微粒掠夺集团；个体存续 vs 跨天堑生态",
            "locked.STORY_DNA.payoff_promise": "主角逐步觉醒、回收伏笔、改写微粒规则",
            "locked.STORY_DNA.word_target": word_target,
            "locked.GENRE_LOCKED.topic": [topic],
            "locked.GENRE_LOCKED.style_lock": {
                "tone": ["暗黑", "压抑", "凶性显化"],
                "forbidden_styles": ["都市腔", "科幻腔", "游戏系统播报腔", "轻小说吐槽腔"],
                "anchor_phrases": ["微粒", "天堑", "内宇宙"],
            },
            "locked.WORLD.cosmology": "四重天堑 / 内宇宙四阶",
            "locked.WORLD.economy": "微粒为通货，总量硬上限 840000000",
            "locked.PLOT_ARCHITECTURE.acts": [
                {"name": "第一幕：觉醒", "chapters": "1-30"},
                {"name": "第二幕：争夺", "chapters": "31-150"},
                {"name": "第三幕：改写", "chapters": "151-300"},
            ],
            "locked.PLOT_ARCHITECTURE.pivot_points": [
                {"ch": 1, "type": "起", "beat": "失忆刺客醒来，发现被植入未知微粒"},
                {"ch": 30, "type": "转", "beat": "首次跨越天堑边界"},
            ],
        },
        source="cli.init.A-E_setup",
    )

    # entity_runtime seed
    sio.apply(
        {
            "entity_runtime.CHARACTER_STATE": {
                "protagonist": {
                    "name": "未命名刺客",
                    "inventory": [{"item": "刻有古老符文的短刃", "count": 1}],
                    "abilities": [{"skill": "影迹潜行", "level": 5, "cooldown": 0}],
                    "body": {"hp": 100, "mp": 80, "status": ["失忆", "微粒残留"]},
                    "psyche": {
                        "mood": "警觉",
                        "beliefs": ["不信任任何人"],
                        "traumas": ["记忆缺失带来的存在性恐惧"],
                    },
                    "relations": [],
                    "events": [],
                }
            },
            "entity_runtime.RESOURCE_LEDGER.particles": 0,
            "entity_runtime.RESOURCE_LEDGER.items": [],
            "entity_runtime.FORESHADOW_STATE.pool": [
                {
                    "id": "fh-001",
                    "planted_ch": 1,
                    "expected_payoff": 30,
                    "status": "open",
                    "summary": "短刃上的古老符文",
                }
            ],
            "entity_runtime.GLOBAL_SUMMARY.total_words": 0,
            "entity_runtime.GLOBAL_SUMMARY.arc_summaries": [],
        },
        source="cli.init.F_state_init",
    )

    # workspace seed（思路 3 三件套）
    sio.apply(
        {
            "workspace.task_plan": f"# Task Plan — {book_id}\n\n## 目标\n50 万字玄幻黑暗长篇 / Killer Use Case 验证\n",
            "workspace.findings": f"# Findings — {book_id}\n\n## 初始设定\n- 题材锁定: {topic}\n",
            "workspace.progress": f"# Progress — {book_id}\n\n## START {datetime.now().isoformat()}\n- init done\n",
        },
        source="cli.init.workspace_seed",
    )

    sio.audit(
        "cli.init",
        severity="info",
        msg=f"book initialized: id={book_id} topic={topic} target={word_target}",
        action="log",
        payload={"locked_premise": premise[:80]},
    )


# ---------- run_workflow -----------------------------------------------------


def _build_chapter_prompt(state: dict, word_target: int, chapter_no: int = 1) -> str:
    """根据 state 拼装某章节生成 prompt（最小化，不调 adapter.input_transform）.

    参数:
        state: state_io.state 的视图（含 locked / entity_runtime / workspace 等域）
        word_target: 目标字数（中文计算）
        chapter_no: 当前章节号（1-based，决定 prompt 里的章节标题与上下文摘要片段）
    """
    locked = state.get("locked", {})
    entity = state.get("entity_runtime", {})

    story_dna = locked.get("STORY_DNA", {})
    genre = locked.get("GENRE_LOCKED", {})
    world = locked.get("WORLD", {})
    plot = locked.get("PLOT_ARCHITECTURE", {})
    style = genre.get("style_lock", {})
    char = entity.get("CHARACTER_STATE", {}).get("protagonist", {})
    foreshadow = entity.get("FORESHADOW_STATE", {}).get("pool", [])
    global_summary = entity.get("GLOBAL_SUMMARY", {}) or {}
    arc_summaries = global_summary.get("arc_summaries", []) or []
    char_events = char.get("events", []) or []

    forbidden = "、".join(style.get("forbidden_styles", []))
    anchor = "、".join(style.get("anchor_phrases", []))
    tone = "、".join(style.get("tone", []))
    fh_items = "; ".join(
        f"{f.get('id', '<?>')}（第{f.get('planted_ch', '?')}章埋 / 第{f.get('expected_payoff', '?')}章回收, status={f.get('status', '?')}）: {f.get('summary', '')}"
        for f in foreshadow
    ) or "（暂无）"

    # 第一章 vs 后续章：定位提示不同
    if chapter_no == 1:
        chapter_label = "第一章 · <小标题>"
        chapter_beat = plot.get("pivot_points", [{}])[0].get("beat", "")
        history_block = "（首章，无前情）"
        embed_hint = "体现主角失忆 + 微粒残留 + 短刃符文伏笔"
    else:
        chapter_label = f"第{chapter_no}章 · <小标题>"
        # 在 pivot_points 里找最近的一个 ch <= chapter_no 作为定位
        matching = [p for p in plot.get("pivot_points", []) if isinstance(p, dict) and p.get("ch", 1) <= chapter_no]
        chapter_beat = (matching[-1].get("beat", "") if matching else "")
        # 最近 3 条 arc_summaries + 最近 5 条 events 作为前情摘要
        recent_arcs = arc_summaries[-3:] if arc_summaries else []
        recent_events = char_events[-5:] if char_events else []
        history_lines = []
        if recent_arcs:
            history_lines.append("### 已写 arc 摘要")
            for a in recent_arcs:
                history_lines.append(
                    f"- {a.get('arc', '?')}: {a.get('summary', '')[:120]}（words={a.get('words', '?')}）"
                )
        if recent_events:
            history_lines.append("### 主角近期关键事件")
            for e in recent_events:
                history_lines.append(
                    f"- 第{e.get('ch', '?')}章 [{e.get('type', '?')}]: {e.get('impact', '')[:120]}"
                )
        history_block = "\n".join(history_lines) if history_lines else "（暂无前情摘要）"
        embed_hint = (
            f"延续前情节奏 / 推进 STORY_DNA conflict_engine / 至少回应或新增 1 个伏笔（status open 的优先）"
        )

    total_words = global_summary.get("total_words", 0)
    particles = (entity.get("RESOURCE_LEDGER", {}) or {}).get("particles", 0)

    prompt = f"""你是「dark-fantasy-ultimate-engine」窄通道生产引擎，按下方设定写第{chapter_no}章。

## 题材与风格锁
- 题材：{', '.join(genre.get('topic', []))}
- 语气基调：{tone}
- 禁止文风：{forbidden}（一旦出现就毁全章）
- 核心锚词：{anchor}

## 核心冲突公式（STORY_DNA，不可改）
- premise：{story_dna.get('premise', '')}
- conflict_engine：{story_dna.get('conflict_engine', '')}
- payoff_promise：{story_dna.get('payoff_promise', '')}

## 世界观（不可越界）
- 宇宙观：{world.get('cosmology', '')}
- 经济规则：{world.get('economy', '')}

## 三幕结构 + 当前章节定位
- 三幕：{json.dumps(plot.get('acts', []), ensure_ascii=False)}
- 本章 beat：{chapter_beat}
- 当前累计字数：{total_words}
- 当前微粒余额：{particles}

## 主角状态卡（runtime_state.CHARACTER_STATE）
- 姓名：{char.get('name', '')}
- 持有：{json.dumps(char.get('inventory', []), ensure_ascii=False)}
- 能力：{json.dumps(char.get('abilities', []), ensure_ascii=False)}
- 身体：{json.dumps(char.get('body', {}), ensure_ascii=False)}
- 心理：{json.dumps(char.get('psyche', {}), ensure_ascii=False)}

## 前情摘要
{history_block}

## 待回收伏笔池（FORESHADOW_STATE）
- {fh_items}

## 输出要求
1. 必须先输出一个 markdown 表格《写作自检》（4 行：当前锚定 / 当前微粒 / 预计微粒变化 / 主要冲突）
2. 然后输出章节正文，目标字数 {word_target} 字（中文计算），章节标题用「{chapter_label}」
3. 章节正文要求：
   - 暗黑、压抑、凶性显化、暴力美学
   - {embed_hint}
   - 禁止出现：都市腔 / 科幻腔 / 游戏系统播报腔 / 轻小说吐槽 / 散文抒情
   - 不准写"系统提示""叮""恭喜获得"等游戏腔表达
4. 章节正文末尾如果发生微粒结算，输出《章节结算》表格（可选）
5. 如果埋下新伏笔，在结尾追加一行： `<!-- foreshadow: id=<fh-NNN> planted_ch={chapter_no} expected_payoff=<章号> summary=<简述> -->`（注释会被 demo_pipeline 抽取）

## 红线
- 不暴露思维链（不要写"我先想..."）
- 不机械重复设定（一笔带过即可）
- 不脱离 STORY_DNA / 风格锁

开始写第{chapter_no}章。
"""
    return prompt


def _call_llm(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
    """调用 ask-llm 子进程，返回 LLM 输出。失败 raise."""
    cmd = [
        "ask-llm",
        endpoint,
        "--max-tokens",
        str(max_tokens),
        "-s",  # stream
    ]
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ask-llm {endpoint} failed (exit={proc.returncode}): {proc.stderr[:500]}"
        )
    if not proc.stdout.strip():
        raise RuntimeError(f"ask-llm {endpoint} returned empty output")
    return proc.stdout


# ---------- foreshadow / chapter rollup helpers ------------------------------


# `<!-- foreshadow: id=fh-002 planted_ch=2 expected_payoff=20 summary=未知-->`
_FORESHADOW_HOOK_RE = re.compile(
    r"<!--\s*foreshadow:\s*id=([\w\-]+)\s+planted_ch=(\d+)\s+expected_payoff=(\d+)\s+summary=(.+?)\s*-->",
    re.IGNORECASE,
)

# 备选：`【伏笔】id=fh-002 ...` 的中文行式（兼容 LLM 不按注释输出的情况）
_FORESHADOW_CN_LINE_RE = re.compile(
    r"【伏笔】\s*id=([\w\-]+)\s+planted_ch=(\d+)\s+expected_payoff=(\d+)\s+summary=(.+)",
)


def _extract_foreshadow_hooks(chapter_text: str, chapter_no: int) -> list[dict]:
    """从章节文本里抽取 LLM 标注的新伏笔 hook.

    支持两种格式（提示词里要求 HTML 注释；中文行式作 fallback）:
        <!-- foreshadow: id=fh-002 planted_ch=2 expected_payoff=20 summary=xxx -->
        【伏笔】id=fh-002 planted_ch=2 expected_payoff=20 summary=xxx

    若 planted_ch 与传入 chapter_no 不一致，以 LLM 标注为准但记 warn。
    """
    hooks: list[dict] = []
    seen_ids: set[str] = set()
    for pattern in (_FORESHADOW_HOOK_RE, _FORESHADOW_CN_LINE_RE):
        for m in pattern.finditer(chapter_text or ""):
            fid, planted_raw, expected_raw, summary = m.groups()
            fid = fid.strip()
            if not fid or fid in seen_ids:
                continue
            seen_ids.add(fid)
            try:
                planted = int(planted_raw)
                expected = int(expected_raw)
            except ValueError:
                continue
            hooks.append(
                {
                    "id": fid,
                    "planted_ch": planted,
                    "expected_payoff": expected,
                    "status": "open",
                    "summary": summary.strip(),
                }
            )
    return hooks


def _check_foreshadow_payoff(pool: list[dict], chapter_no: int) -> list[dict]:
    """检查既有 foreshadow pool 在本章是否触发 expected_payoff.

    返回（potentially mutated）pool 副本：到期且仍 open 的 hook 状态切换为 tickled
    （表示"到达预期回收章节"，但不强行判定已回收，留给 R2 一致性 checker 复核）。
    """
    out: list[dict] = []
    for entry in pool:
        if not isinstance(entry, dict):
            out.append(entry)
            continue
        new_entry = dict(entry)
        expected = entry.get("expected_payoff")
        status = entry.get("status", "open")
        if (
            isinstance(expected, int)
            and chapter_no >= expected
            and status == "open"
        ):
            new_entry["status"] = "tickled"
            new_entry["tickled_at_ch"] = chapter_no
        out.append(new_entry)
    return out


def _extract_particle_delta(chapter_text: str) -> int:
    """简易解析章节结算里的微粒 delta（找 `delta=NNN` 或《章节结算》表格里的微粒变化）.

    不可靠则返回 0；用作 demo 演示，真正结算靠 dark-fantasy adapter.output_transform.
    """
    if not chapter_text:
        return 0
    # 优先：显式 delta=N 标注
    m = re.search(r"微粒\s*(?:delta|结算|变化)\s*[:=]\s*([+-]?\d+)", chapter_text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    # 备选：表格里 `预计微粒变化 | +N`
    m = re.search(r"预计微粒变化\s*\|\s*([+-]?\d+)", chapter_text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    return 0


def apply_chapter_rollup(
    sio: StateIO,
    *,
    chapter_no: int,
    chapter_text: str,
    word_count: int,
    arc_window: int = 5,
) -> dict[str, Any]:
    """把单章产出滚动写回 entity_runtime（多章 wire-up 核心入口）.

    步骤：
        1. 抽取 foreshadow hooks（LLM 标注），与既有 pool 合并去重；既有 hook 检查 expected_payoff
        2. 通过 op_translator 计算 particles delta（dict / numeric 合并语义统一）
        3. 累加 GLOBAL_SUMMARY.total_words
        4. 给 protagonist.events 追加本章关键事件（最小化记录: 章号 / type=draft / impact 摘要）
        5. 每 arc_window 章追加一条 arc_summaries

    返回 ops 列表（便于测试断言），同时 state_io 已落盘.
    """
    pool_now = sio.read("entity_runtime.FORESHADOW_STATE.pool") or []
    new_hooks = _extract_foreshadow_hooks(chapter_text, chapter_no)
    rolled_pool = _check_foreshadow_payoff(pool_now, chapter_no)
    existing_ids = {p.get("id") for p in rolled_pool if isinstance(p, dict)}
    for h in new_hooks:
        if h["id"] not in existing_ids:
            rolled_pool.append(h)
            existing_ids.add(h["id"])

    particle_delta = _extract_particle_delta(chapter_text)

    # 构造 op list 喂 op_translator
    ops: list[dict[str, Any]] = [
        {
            "op": "write",
            "path": "entity_runtime.FORESHADOW_STATE.pool",
            "value": rolled_pool,
        },
        {
            "op": "delta",
            "path": "entity_runtime.GLOBAL_SUMMARY.total_words",
            "value": word_count,
        },
        {
            "op": "append",
            "path": "entity_runtime.CHARACTER_STATE.protagonist.events",
            "value": {
                "ch": chapter_no,
                "type": "draft",
                "impact": f"第{chapter_no}章草稿生成（{word_count}字，新增{len(new_hooks)}个伏笔）",
            },
        },
    ]
    if particle_delta:
        ops.append(
            {
                "op": "delta",
                "path": "entity_runtime.RESOURCE_LEDGER.particles",
                "value": particle_delta,
            }
        )

    # 每 arc_window 章一条 arc 总结
    if chapter_no > 0 and chapter_no % arc_window == 0:
        ops.append(
            {
                "op": "append",
                "path": "entity_runtime.GLOBAL_SUMMARY.arc_summaries",
                "value": {
                    "arc": f"chapter_{chapter_no - arc_window + 1}-{chapter_no}",
                    "summary": f"第 {chapter_no - arc_window + 1}-{chapter_no} 章已生成",
                    "words": word_count,
                    "anchor_ch": chapter_no,
                },
            }
        )

    flat_updates = adapter_ops_to_state_updates(ops, sio)
    sio.apply(flat_updates, source=f"demo_pipeline.apply_chapter_rollup.ch{chapter_no}")
    sio.audit(
        f"cli.run.chapter_{chapter_no}.rollup",
        severity="info",
        msg=(
            f"chapter {chapter_no} rolled up: words+={word_count} "
            f"new_hooks={len(new_hooks)} particle_delta={particle_delta}"
        ),
        action="log",
        payload={"new_hook_ids": [h["id"] for h in new_hooks]},
    )
    return {
        "ops": ops,
        "flat_updates": flat_updates,
        "new_hooks": new_hooks,
        "particle_delta": particle_delta,
    }


def run_workflow(
    book_id: str,
    llm_endpoint: str = "windhub",
    word_target: int = 3500,
    chapter_no: int = 1,
    *,
    state_root: Path | str | None = None,
    mock_llm: bool = False,
) -> str | None:
    """跑简化版 workflow MVP：G_chapter_draft 真调 LLM 生成指定章节.

    Sprint 2 扩展：
        - 接受 chapter_no（默认 1，兼容 Sprint 1 单章 demo）
        - 完成后通过 apply_chapter_rollup 滚动 entity_runtime
        - 落盘到 chapter_NN.md（NN = 两位补零）

    Returns: chapter_NN.md 的绝对路径；失败返回 None.
    """
    sio = StateIO(book_id, autoload=True, **_state_io_kwargs(state_root))
    state = sio.state  # 直接拿 dict-of-dict 视图，不要走 snapshot（snapshot 嵌套到 .state 子键）

    if not state.get("locked", {}).get("STORY_DNA"):
        print(f"❌ state seed not found for book={book_id}; run `ginga init` first", file=sys.stderr)
        return None

    if chapter_no < 1:
        print(f"❌ chapter_no must be >= 1, got {chapter_no}", file=sys.stderr)
        return None

    sio.audit("cli.run.A_through_F", severity="info", msg="setup steps skipped (seeded by init)")

    # G_chapter_draft：真实 demo 调 LLM；mock harness 只走固定离线章节。
    if mock_llm:
        print(
            f"📝 mock_harness 生成第 {chapter_no} 章 (目标 {word_target} 字，不调用 ask-llm)...",
            file=sys.stderr,
        )
    else:
        print(
            f"📝 调用 ask-llm {llm_endpoint} 生成第 {chapter_no} 章 (目标 {word_target} 字)...",
            file=sys.stderr,
        )
    prompt = _build_chapter_prompt(state, word_target, chapter_no=chapter_no)
    try:
        chapter_text, execution_mode = _call_llm_or_mock(
            prompt,
            llm_endpoint,
            mock_llm=mock_llm,
            chapter_no=chapter_no,
            word_target=word_target,
        )
    except Exception as exc:
        sio.audit(
            f"cli.run.G_chapter_draft.ch{chapter_no}",
            severity="error",
            msg=f"LLM call failed: {exc}",
            action="block",
        )
        print(f"❌ LLM call failed: {exc}", file=sys.stderr)
        return None

    word_count = sum(1 for ch in chapter_text if "一" <= ch <= "鿿")
    print(f"✓ LLM 返回 {len(chapter_text)} 字符 / {word_count} 个汉字", file=sys.stderr)

    # 落 chapter_NN.md（两位补零）
    chapter_path = sio.write_artifact(
        f"chapter_{chapter_no:02d}.md",
        chapter_text,
        source=f"cli.run.G_chapter_draft.ch{chapter_no}",
        artifact_type="chapter_text",
        payload={"chapter_no": chapter_no, "execution_mode": execution_mode},
    )

    # H_chapter_settle：滚动更新 entity_runtime（多章 wire-up）
    apply_chapter_rollup(
        sio,
        chapter_no=chapter_no,
        chapter_text=chapter_text,
        word_count=word_count,
    )

    # R1-R3 + V1 audit log（mock；真实现由 multi_chapter.py 包装）
    for step in ("R1_style_polish", "R2_consistency_check", "R3_final_pack", "V1_release_check"):
        sio.audit(
            f"cli.run.{step}.ch{chapter_no}",
            severity="info",
            msg=f"{step} stub (multi_chapter.py implements full)",
        )

    return str(chapter_path)


# ---------- show_status ------------------------------------------------------


def show_status(book_id: str, *, state_root: Path | str | None = None) -> None:
    """打印 book 当前 state 摘要."""
    sio = StateIO(book_id, autoload=True, **_state_io_kwargs(state_root))
    state = sio.state
    print(f"=== book_id: {book_id} ===")
    print(f"state_dir: {sio.state_dir}")
    print(f"locked.STORY_DNA.premise: {state.get('locked', {}).get('STORY_DNA', {}).get('premise', '<unset>')[:80]}")
    print(f"locked.GENRE_LOCKED.topic: {state.get('locked', {}).get('GENRE_LOCKED', {}).get('topic', [])}")
    print(f"entity_runtime.GLOBAL_SUMMARY.total_words: {state.get('entity_runtime', {}).get('GLOBAL_SUMMARY', {}).get('total_words', 0)}")
    print(f"foreshadow pool size: {len(state.get('entity_runtime', {}).get('FORESHADOW_STATE', {}).get('pool', []))}")
    print(f"audit_log entries: {len(sio.audit_log)}")
    chapters = list(sio.state_dir.glob("chapter_*.md"))
    print(f"chapters on disk: {len(chapters)}")
    for c in chapters:
        print(f"  - {c.name}: {c.stat().st_size} bytes")
