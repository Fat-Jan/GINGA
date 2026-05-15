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
    - 默认 ``llm_caller`` 走 ``ginga_platform.orchestrator.cli.demo_pipeline._call_llm``（subprocess 调 ask-llm）。
    - 单元测试可注入 mock_callable(prompt, endpoint) -> str 替代真实 LLM。
    - chapter_text 落盘：每章一份 ``chapter_<NN>.md`` 到 ``foundation/runtime_state/<book_id>/``。
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Callable, Dict, Optional

from ginga_platform.skills.dark_fantasy_ultimate_engine.adapter import DarkFantasyAdapter
from ginga_platform.orchestrator.runner.state_io import StateIO
from ginga_platform.orchestrator.cli.demo_pipeline import MOCK_HARNESS_MODE, REAL_LLM_DEMO_MODE
from ginga_platform.orchestrator.cli.longform_policy import DEFAULT_CHAPTER_BATCH_SIZE


# 默认 LLM 调用器（subprocess ask-llm）——延迟 import 避免 demo_pipeline 依赖闭环
def _default_llm_caller(prompt: str, endpoint: str, max_tokens: int = 4096) -> str:
    from ginga_platform.orchestrator.cli.demo_pipeline import _call_llm
    return _call_llm(prompt, endpoint, max_tokens=max_tokens)


def _default_prompt_builder(state: dict, word_target: int, chapter_no: int) -> str:
    """每章 prompt 构造器：复用 demo_pipeline._build_chapter_prompt 主体，
    并在末尾追加 "现在写第 N 章" 提示."""
    from ginga_platform.orchestrator.cli.demo_pipeline import _build_chapter_prompt
    base = _build_chapter_prompt(state, word_target, chapter_no=chapter_no)
    return base + f"\n\n## 当前章节号\n第 {chapter_no} 章（共本沉浸块）\n"


def _chapter_label_number(chapter_no: int) -> str:
    return "一" if chapter_no == 1 else str(chapter_no)


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
        try:
            # Step 2-3: 顺序跑 N 章
            for i in range(chapters):
                ch_no = start_chapter_no + i
                state_view = self.state_io.state  # dict-of-dict 视图

                prompt = self.prompt_builder(state_view, word_target, ch_no)
                chapter_text = self.llm_caller(prompt, llm_endpoint)
                chapter_text = _normalize_chapter_heading(chapter_text, ch_no)

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
        finally:
            # Step 4-5: chapter_block_end 自动触发 → exit
            summary = self.adapter.exit_immersive_mode()

        return {
            "chapter_count": chapters,
            "chapter_paths": chapter_paths,
            "applied_count": summary.get("applied_count", 0),
            "failed_count": summary.get("failed_count", 0),
            "last_error": summary.get("last_error"),
            "batch_chapter_count": summary.get("chapter_count", 0),
        }


__all__ = ["ImmersiveRunner"]
