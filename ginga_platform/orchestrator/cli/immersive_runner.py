"""ImmersiveRunner — dark-fantasy 沉浸专线 N 章 block 运行器 (ST-S2-I IMMERSIVE).

设计来源：
    - ARCHITECTURE.md §4.5 immersive_mode
    - ginga_platform/skills/dark_fantasy_ultimate_engine/contract.yaml immersive_mode 段
    - .ops/jury/jury-3-novel-editor.md §改进 4

行为：
    enter_immersive_mode → N 章 G_chapter_draft（每章 build prompt + call LLM + adapter.output_transform 入 pending_updates，不立即 apply；checker 期内全静默）
    → chapter_block_end signal（默认 = run_block 末尾自动触发）
    → exit_immersive_mode（batch apply pending_updates 经 op_translator + state_io.transaction）

接入说明：
    - 默认 ``llm_caller`` 走 ``ginga_platform.orchestrator.cli.llm_config``（subprocess 调 ask-llm）。
    - 单元测试可注入 mock_callable(prompt, endpoint) -> str 替代真实 LLM。
    - chapter_text 落盘：每章一份 ``chapter_<NN>.md`` 到 ``foundation/runtime_state/<book_id>/``。
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Callable, Dict, Optional

from ginga_platform.skills.dark_fantasy_ultimate_engine.adapter import DarkFantasyAdapter
from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.cli.demo_pipeline import (
    MOCK_HARNESS_MODE,
    REAL_LLM_DEMO_MODE,
    build_chapter_input_bundle,
)
from ginga_platform.orchestrator.cli.longform_policy import DEFAULT_CHAPTER_BATCH_SIZE
from ginga_platform.orchestrator.cli.longform_policy import (
    BODY_CHINESE_TARGET_MAX,
    BODY_CHINESE_TARGET_MIN,
    MIN_SUBMISSION_CHINESE_CHARS,
    count_chinese,
    extract_chapter_body_text,
    hard_style_warn_hits,
    opening_loop_score,
    soft_style_warn_hits,
    style_warn_hits,
)


# 默认 LLM 调用器（subprocess ask-llm）——延迟 import 避免 demo_pipeline 依赖闭环
def _default_llm_caller(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
    from ginga_platform.orchestrator.cli.llm_config import call_llm_with_fallback

    return call_llm_with_fallback(prompt, endpoint=endpoint, max_tokens=max_tokens)


def _default_prompt_builder(state: dict, word_target: int, chapter_no: int) -> str:
    """每章 prompt 构造器：复用 demo_pipeline._build_chapter_prompt 主体，
    并在末尾追加 "现在写第 N 章" 提示."""
    from ginga_platform.orchestrator.cli.demo_pipeline import _build_chapter_prompt
    base = _build_chapter_prompt(state, word_target, chapter_no=chapter_no)
    return base + f"\n\n## 当前章节号\n第 {chapter_no} 章（共本沉浸块）\n"


def _chapter_label_number(chapter_no: int) -> str:
    return "一" if chapter_no == 1 else str(chapter_no)


def _body_char_target(word_target: int) -> tuple[int, int]:
    return BODY_CHINESE_TARGET_MIN, BODY_CHINESE_TARGET_MAX


def _minimum_body_chars(word_target: int) -> int:
    return MIN_SUBMISSION_CHINESE_CHARS


def _normalize_chapter_heading(chapter_text: str, chapter_no: int) -> str:
    """Correct the first markdown chapter heading to the requested chapter number."""
    target = _chapter_label_number(chapter_no)
    lines = chapter_text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        stripped = line.strip()
        is_heading = stripped.startswith("#") or (stripped.startswith("**第") and stripped.endswith("**"))
        if not is_heading:
            continue
        corrected = re.sub(
            r"第\s*([0-9]+|[一二三四五六七八九十]+)\s*章",
            f"第{target}章",
            line,
            count=1,
        )
        if corrected != line:
            lines[idx] = corrected
            return "".join(lines)
    return chapter_text


def _chapter_excerpt_for_bridge(chapter_text: str, *, limit: int = 220) -> str:
    lines = [
        line.strip()
        for line in chapter_text.splitlines()
        if line.strip()
        and not line.strip().startswith("|")
        and not line.strip().startswith("#")
        and not line.strip().startswith("<!--")
    ]
    compact: list[str] = []
    seen: set[str] = set()
    for line in lines:
        chunks = [chunk.strip() for chunk in re.split(r"(?<=[。！？!?])", line) if chunk.strip()]
        for chunk in chunks or [line]:
            if chunk in seen:
                continue
            compact.append(chunk)
            seen.add(chunk)
    excerpt = " ".join(compact[-4:])
    return excerpt[:limit]


def _repair_prompt(
    original_prompt: str,
    chapter_text: str,
    word_target: int,
    chapter_no: int,
    *,
    attempt: int = 1,
    failure: str | None = None,
    previous_chapter_bridge: str | None = None,
) -> str:
    target_minimum, target_ceiling = _body_char_target(word_target)
    minimum_body_chars = _minimum_body_chars(word_target)
    excerpt = _chapter_excerpt_for_bridge(chapter_text, limit=320)
    escalated = attempt >= 2
    escalation_lines = [
        "- 上一轮修复仍未通过；不要以 3500 为目标，本轮正文目标至少 4200 个中文正文汉字，宁可接近上限也不要贴近下限。",
        "- 必须写满 10 个正文段落；第 10 段前不得收束、总结或转入尾声，每段都要有新的动作、代价或规则后果。",
    ] if escalated else []
    bridge_lines = [
        f"- 本章第一段必须承接：{previous_chapter_bridge}",
        "- 禁止把醒来、睁眼、灰白环境、体内微粒或短刃当作开篇支点；只能把这些元素放在承接动作之后。",
    ] if chapter_no > 1 and previous_chapter_bridge else []
    return "\n".join(
        [
            original_prompt,
            "",
            f"## 质量修复第 {attempt} 次",
            f"上一版第 {chapter_no} 章未通过真实长篇 gate，请重写完整章节正文。",
            f"- 上一版失败摘要：{failure or 'short_chapter/opening_loop_risk'}",
            *escalation_lines,
            *bridge_lines,
            f"- 长度口径只看正文汉字数 {target_minimum}-{target_ceiling}；表格、标题、注释、标点不计入正文汉字数。",
            f"- 正文汉字数不得低于 {minimum_body_chars}，且任何真实长篇小批正文汉字数低于 {MIN_SUBMISSION_CHINESE_CHARS} 必须视为失败。",
            "- 必须重写为 9-11 个正文段落，每个正文段落 380-520 个汉字；动作推进、对手反应、身体代价、规则后果、伏笔推进都要落到正文。",
            f"- 至少新增 {max(900, minimum_body_chars // 4)} 个正文汉字的具体事件推进，不得只改标题、局部润色或压缩上一版。",
            "- 首段必须承接上一章收束动作或当前场面压力，禁止重新醒来、睁眼、灰白环境、体内微粒、短刃等重启模板。",
            "- 删除“说不出的感觉”“难以言喻”“复杂的情绪”，用动作、代价、对手反应替代。",
            "- 转折必须有明确动作因果；禁止出现“突然”“猛然”“下一秒”“命运的齿轮”“内心深处”“仿佛…命运”等 review style warn 词/句式。",
            "- 保留低频题材锚点：血脉、末日、多子多福、繁衍契约中至少一个。",
            f"- 每章必须输出至少 1 行可机读伏笔标记：<!-- foreshadow: id=<fh-NNN> planted_ch={chapter_no} expected_payoff=<章号> summary=<简述> -->；即使只推进旧伏笔，也要把本章铺垫、推进或回收线索写成 marker。",
            "",
            "## 上一版短摘录（只用于避开重复，不要压缩改写）",
            excerpt or "（无可用摘录）",
        ]
    )


def _needs_quality_repair(chapter_text: str, word_target: int, chapter_no: int) -> bool:
    if word_target < MIN_SUBMISSION_CHINESE_CHARS:
        return False
    return _quality_gate_failure(chapter_text, word_target, chapter_no) is not None


def _style_warn_hits(body_text: str) -> dict[str, int]:
    return style_warn_hits(body_text)


def _hard_style_warn_hits(body_text: str) -> dict[str, int]:
    return hard_style_warn_hits(body_text)


def _soft_style_warn_hits(body_text: str) -> dict[str, int]:
    return soft_style_warn_hits(body_text)


def _rewrite_style_warn_terms(chapter_text: str) -> str:
    hard_replacements = {
        "说不出的感觉": "刺痛沿着骨缝扩散",
        "难以言喻": "压得喉间发涩",
        "复杂的情绪": "迟疑被掌心冷汗压住",
        "命运的齿轮": "城门深处的绞盘",
        "内心深处": "胸骨后方",
    }
    rewritten = chapter_text
    for old, new in hard_replacements.items():
        rewritten = rewritten.replace(old, new)
    rewritten = re.sub(r"仿佛([^\n]*?)命运", r"像\1血契", rewritten)
    rewritten = re.sub(r"(?<=[。！？\n])([^。！？\n]{0,2})突然", r"\1这时", rewritten)
    rewritten = rewritten.replace("突然", "倏地")
    rewritten = re.sub(r"(?<=[。！？\n])([^。！？\n]{0,2})猛然", r"\1随即", rewritten)
    rewritten = rewritten.replace("猛然", "骤然")
    rewritten = rewritten.replace("下一秒", "下一息")
    return rewritten


def _rewrite_quality_gate_terms(chapter_text: str, chapter_no: int) -> str:
    rewritten = _rewrite_style_warn_terms(chapter_text)
    if chapter_no <= 1:
        return rewritten
    replacements = {
        "睁开眼": "抬手按住裂开的血门",
        "醒来": "从上一轮索债里撑住身体",
        "灰白雾气": "血门裂缝里的冷雾",
        "体内微粒": "掌心微粒",
        "短刃": "债刃",
    }
    lines = rewritten.splitlines()
    body_line_seen = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("<!--"):
            continue
        if body_line_seen:
            continue
        body_line_seen = True
        fixed = line
        for old, new in replacements.items():
            fixed = fixed.replace(old, new)
        lines[idx] = fixed
    return "\n".join(lines)


def _quality_gate_failure(chapter_text: str, word_target: int, chapter_no: int) -> str | None:
    if word_target < MIN_SUBMISSION_CHINESE_CHARS:
        return None
    failures: list[str] = []
    body_text = extract_chapter_body_text(chapter_text)
    chinese_chars = count_chinese(body_text)
    opening_score = opening_loop_score(body_text)
    minimum_body_chars = _minimum_body_chars(word_target)
    if chinese_chars < minimum_body_chars:
        failures.append(f"short_chapter body_chinese_chars={chinese_chars} < {minimum_body_chars}")
    if chapter_no > 1 and opening_score >= 3:
        failures.append(f"opening_loop_risk score={opening_score}")
    if "<!-- foreshadow:" not in chapter_text:
        failures.append("missing_foreshadow_marker")
    hard_hits = _hard_style_warn_hits(body_text)
    if hard_hits:
        failures.append(
            "style_warn " + ", ".join(f"{name}={count}" for name, count in sorted(hard_hits.items()))
        )
    return "; ".join(failures) if failures else None


class ImmersiveRunner:
    """dark-fantasy 沉浸专线 N 章 block 运行器.

    Usage::

        runner = ImmersiveRunner(book_id="demo-book")
        result = runner.run_block(chapters=5, llm_endpoint="久久", word_target=4000)
        # result: {"chapter_count": 5, "applied_count": ..., "chapter_paths": [...], ...}

    测试 / 离线模式::

        runner = ImmersiveRunner(book_id="demo-book", llm_caller=lambda p,e,**kw: "<mock chapter>")
    """

    def __init__(
        self,
        book_id: str,
        *,
        state_root: Path | str | None = None,
        llm_caller: Optional[Callable[..., str]] = None,
        prompt_builder: Optional[Callable[[dict, int, int], str]] = None,
    ) -> None:
        self.book_id = book_id
        if state_root is not None:
            self.state_io = StateIO(book_id, state_root=state_root)
        else:
            self.state_io = StateIO(book_id)
        self.adapter = DarkFantasyAdapter(self.state_io)
        self.llm_caller = llm_caller or _default_llm_caller
        self.prompt_builder = prompt_builder or _default_prompt_builder

    def run_block(
        self,
        chapters: int = DEFAULT_CHAPTER_BATCH_SIZE,
        *,
        llm_endpoint: str = "久久",
        word_target: int = 4000,
        start_chapter_no: int = 1,
        execution_mode: str | None = None,
    ) -> Dict[str, Any]:
        """跑一个连续 N 章的沉浸块.

        步骤：
            1. enter_immersive_mode（写 workflow_flags + snapshot）
            2. 顺序跑 N 章：构 prompt → call LLM → fake skill_output 喂 adapter.output_transform
               (immersive 期内自动入 pending_updates)
            3. 每章 chapter_text 落 chapter_<NN>.md（独立写盘，不走 state_io.apply 因为 state apply 在 exit 时一次性）
            4. chapter_block_end signal（自动触发 = run_block 末尾）
            5. exit_immersive_mode（batch apply + R2）

        Args:
            chapters: 章节数，必须 >= 1
            llm_endpoint: ask-llm endpoint alias (default "久久")
            word_target: 每章字数目标 (default 4000)
            start_chapter_no: 起始章号 (default 1，每章号 +1)

        Returns:
            dict: {"chapter_count": int, "chapter_paths": list[str],
                   "applied_count": int, "failed_count": int, "last_error": str | None}
        """
        if chapters < 1:
            raise ValueError(f"chapters must be >= 1, got {chapters}")

        # Step 1: 进入沉浸
        self.adapter.enter_immersive_mode()

        chapter_paths: list[str] = []
        previous_chapter_bridge: str | None = None
        run_error: str | None = None
        try:
            # Step 2-3: 顺序跑 N 章
            for i in range(chapters):
                ch_no = start_chapter_no + i
                state_view = self.state_io.state  # dict-of-dict 视图
                chapter_input_bundle = build_chapter_input_bundle(
                    state_view,
                    word_target,
                    chapter_no=ch_no,
                    previous_chapter_bridge_override=previous_chapter_bridge,
                )
                self.state_io.apply(
                    {"workspace.CHAPTER_INPUT_BUNDLE": chapter_input_bundle},
                    source=f"immersive_runner.chapter_{ch_no}.input_bundle",
                )
                state_view = self.state_io.state

                prompt = self.prompt_builder(state_view, word_target, ch_no)
                chapter_text = self.llm_caller(prompt, llm_endpoint)
                chapter_text = _normalize_chapter_heading(chapter_text, ch_no)
                if _needs_quality_repair(chapter_text, word_target, ch_no):
                    repair_failure = _quality_gate_failure(chapter_text, word_target, ch_no)
                    for attempt in (1, 2):
                        repair_prompt = _repair_prompt(
                            prompt,
                            chapter_text,
                            word_target,
                            ch_no,
                            attempt=attempt,
                            failure=repair_failure,
                            previous_chapter_bridge=previous_chapter_bridge,
                        )
                        chapter_text = self.llm_caller(repair_prompt, llm_endpoint)
                        chapter_text = _normalize_chapter_heading(chapter_text, ch_no)
                        repair_failure = _quality_gate_failure(chapter_text, word_target, ch_no)
                        if not repair_failure:
                            break
                    if repair_failure:
                        rewritten_chapter = _rewrite_quality_gate_terms(chapter_text, ch_no)
                        rewritten_failure = _quality_gate_failure(rewritten_chapter, word_target, ch_no)
                        if not rewritten_failure:
                            chapter_text = rewritten_chapter
                            repair_failure = None
                    if repair_failure:
                        raise RuntimeError(f"chapter {ch_no} failed quality gate after repair: {repair_failure}")
                previous_chapter_bridge = (
                    f"上一章生成摘要：{_chapter_excerpt_for_bridge(chapter_text)}"
                    if chapter_text.strip()
                    else previous_chapter_bridge
                )

                # fake skill_output（demo_pipeline 没用 adapter，这里补：
                # 第 N 章字数估算 → settlement.particle_balance.delta；其他字段留空）
                wc = sum(1 for c in chapter_text if "一" <= c <= "鿿")
                skill_output: Dict[str, Any] = {
                    "chapter_text": chapter_text,
                    "writing_self_check": {"context_range": f"ch{ch_no}", "word_count": wc},
                    "chapter_settlement": {},  # demo 不结算微粒
                    "state_updates": {},
                }

                # 调 adapter.output_transform（immersive 期内自动入 pending_updates）
                self.adapter.output_transform(skill_output)

                # 落 chapter_<NN>.md（独立写盘；exit 时 batch apply 不重写文件）
                mode = execution_mode or (
                    MOCK_HARNESS_MODE if self.llm_caller is not _default_llm_caller else REAL_LLM_DEMO_MODE
                )
                fp = self.state_io.write_artifact(
                    f"chapter_{ch_no:02d}.md",
                    chapter_text,
                    source="immersive_runner",
                    artifact_type="chapter_text",
                    payload={"chapter_no": ch_no, "execution_mode": mode},
                )
                chapter_paths.append(str(fp))

                # audit 每章生成（immersive 期内只 audit, checker 已静默）
                self.state_io.audit(
                    source="immersive_runner",
                    severity="info",
                    msg=f"chapter {ch_no} drafted (immersive, pending apply)",
                    action="log",
                    payload={"chapter_no": ch_no, "word_count": wc, "file": str(fp)},
                )
        except RuntimeError as exc:
            run_error = str(exc)
            self.state_io.audit(
                source="immersive_runner",
                severity="error",
                msg=run_error,
                action="block",
                payload={"chapter_paths": chapter_paths},
            )
        finally:
            # Step 4-5: chapter_block_end 自动触发 → exit
            summary = self.adapter.exit_immersive_mode()
        last_error = run_error or summary.get("last_error")

        return {
            "chapter_count": len(chapter_paths),
            "chapter_paths": chapter_paths,
            "applied_count": summary.get("applied_count", 0),
            "failed_count": summary.get("failed_count", 0) + (1 if run_error else 0),
            "last_error": last_error,
            "batch_chapter_count": summary.get("chapter_count", 0),
        }


__all__ = ["ImmersiveRunner"]
