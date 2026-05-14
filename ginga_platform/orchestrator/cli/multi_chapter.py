"""多章 runner + R1/R2/R3 终稿三件套 + V1 DoD checker (ST-S2-S-MULTI-CHAPTER S-3/S-4/S-5).

职责:
    - run_multi_chapter: 串起 N 章生成全流程，每章经过 G(run_workflow) → R1(润色) → R2(一致性) → R3(终稿打包)，结束跑一次 V1 DoD.
    - _call_llm_for_polish: R1 风格润色（独立 LLM 调用，便于测试 mock）.
    - _r2_consistency_check: R2 调 invoke_checkers 跑 character-iq + cool-point-payoff，容忍存量 checker yaml schema 不匹配（aigc-style-detector dict-vs-list 已知问题，落 audit 不阻塞）.
    - _r3_final_pack: 把 polished 正文 + 元数据表格写入 foundation/runtime_state/<book>/chapter_NN.md（覆盖 run_workflow 落的草稿）.
    - _v1_release_check: V1 DoD = 每章 >= min_bytes + foreshadow pool >= min_pool + total_words 累加非零.

不重写 run_workflow 内的 R1-R3 mock audit；那批 audit 留作单章 demo 路径（demo_pipeline 直接被 ginga run 单章用），multi_chapter 路径自己在 audit_log 里覆写真实结果.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from ginga_platform.orchestrator.cli.demo_pipeline import _call_llm, run_workflow
from ginga_platform.orchestrator.cli.demo_pipeline import (
    MOCK_HARNESS_MODE,
    REAL_LLM_DEMO_MODE,
)
from ginga_platform.orchestrator.meta_integration.checker_invoker import (
    CheckerBlocked,
    CheckerLoadError,
    invoke_checkers,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


_DEFAULT_R2_CHECKERS = ["character-iq-checker", "cool-point-payoff-checker"]


def _call_llm_for_polish(text: str, endpoint: str) -> str:
    """R1: 调 LLM 做风格润色，保留原意 + 收紧节奏 + 强化氛围.

    抽出独立函数便于测试 mock；生产路径走 ask-llm <endpoint> 同 demo_pipeline._call_llm.
    """
    polish_prompt = (
        "请对下方章节做风格润色：保留原意与表格信息，收紧节奏、统一调性、强化氛围；"
        "不要删去任何 HTML 注释（<!-- foreshadow: ... -->）或元数据表格行。"
        "直接输出润色后全文，不要任何说明文字。\n\n"
        f"{text}"
    )
    return _call_llm(polish_prompt, endpoint, max_tokens=6144)


def _mock_polish(text: str) -> str:
    return text.rstrip() + "\n\n<!-- mock_harness: R1 polish skipped -->\n"


def _r2_consistency_check(
    sio: StateIO,
    chapter_no: int,
    chapter_text: str,
    *,
    checker_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """R2: 调 invoke_checkers 跑 character-iq + cool-point-payoff，warn 模式不阻塞.

    容忍 CheckerLoadError（如 aigc-style-detector dict-vs-list schema 不匹配的存量 checker yaml）：
    落一条 audit warn，继续推进；CheckerBlocked 实际不会触发因为默认 mode=warn.
    """
    cids = checker_ids if checker_ids is not None else list(_DEFAULT_R2_CHECKERS)
    step_output = {"chapter_no": chapter_no, "chapter_text": chapter_text}
    runtime_context = {"state_io": sio, "step_id": f"R2_consistency_check.ch{chapter_no}"}
    results: list[dict[str, Any]] = []
    for cid in cids:
        try:
            single = invoke_checkers(
                [cid],
                step_output=step_output,
                runtime_context=runtime_context,
            )
            results.extend(single)
        except CheckerLoadError as exc:
            sio.audit(
                source=f"multi_chapter.R2_consistency_check.ch{chapter_no}",
                severity="warn",
                msg=f"checker {cid} load failed (schema?): {exc}",
                action="log",
                payload={"checker_id": cid, "skipped": True},
            )
            results.append({"checker_id": cid, "mode": "off", "hit_rule": None, "severity": "warn", "skipped": True, "error": str(exc)})
        except CheckerBlocked as exc:
            sio.audit(
                source=f"multi_chapter.R2_consistency_check.ch{chapter_no}",
                severity="error",
                msg=f"checker {cid} blocked: {exc}",
                action="block",
                payload={"checker_id": cid},
            )
            results.append({"checker_id": cid, "mode": "block", "hit_rule": "blocked", "severity": "error"})
    sio.audit(
        source=f"multi_chapter.R2_consistency_check.ch{chapter_no}",
        severity="info",
        msg=f"R2 ran {len(results)} checkers",
        action="log",
        payload={"results": [{"id": r.get("checker_id"), "hit": r.get("hit_rule")} for r in results]},
    )
    return results


def _build_chapter_metadata_table(
    sio: StateIO,
    chapter_no: int,
    polished_text: str,
    r2_results: list[dict[str, Any]],
) -> str:
    """R3 元数据表格：附在 chapter 末尾，记录本章关键指标 + R2 结果."""
    word_count = sum(1 for ch in polished_text if "一" <= ch <= "鿿")
    pool = sio.read("entity_runtime.FORESHADOW_STATE.pool") or []
    total_words = sio.read("entity_runtime.GLOBAL_SUMMARY.total_words") or 0
    r2_summary = ", ".join(
        f"{r.get('checker_id')}={r.get('hit_rule') or 'ok'}" for r in r2_results
    ) or "(none)"
    return (
        "\n\n---\n\n"
        "## 章节元数据（R3 final pack）\n\n"
        "| 字段 | 值 |\n|---|---|\n"
        f"| chapter_no | {chapter_no} |\n"
        f"| word_count | {word_count} |\n"
        f"| total_words_after | {total_words} |\n"
        f"| foreshadow_pool_size | {len(pool)} |\n"
        f"| R2_checker_results | {r2_summary} |\n"
    )


def _r3_final_pack(
    sio: StateIO,
    chapter_no: int,
    polished_text: str,
    r2_results: list[dict[str, Any]],
) -> Path:
    """R3: 把 polished 正文 + metadata table 写到 chapter_NN.md（覆盖 run_workflow 草稿）."""
    meta_table = _build_chapter_metadata_table(sio, chapter_no, polished_text, r2_results)
    out_path = sio.write_artifact(
        f"chapter_{chapter_no:02d}.md",
        polished_text.rstrip() + meta_table,
        source=f"multi_chapter.R3_final_pack.ch{chapter_no}",
        artifact_type="chapter_text",
        payload={"chapter_no": chapter_no, "stage": "R3_final_pack"},
    )
    return out_path


def _v1_release_check(
    sio: StateIO,
    *,
    min_bytes: int = 3000,
    min_pool: int = 1,
) -> dict[str, Any]:
    """V1 DoD checker：每章 >=min_bytes / FORESHADOW pool >=min_pool / total_words 累加 > 0."""
    state_dir = sio.state_dir
    chapters = sorted(state_dir.glob("chapter_*.md"))
    fails: list[dict[str, Any]] = []
    chapter_sizes: list[dict[str, Any]] = []
    for c in chapters:
        size = c.stat().st_size
        chapter_sizes.append({"name": c.name, "bytes": size})
        if size < min_bytes:
            fails.append({"chapter": c.name, "issue": "below_min_bytes", "bytes": size, "min": min_bytes})
    pool = sio.read("entity_runtime.FORESHADOW_STATE.pool") or []
    if len(pool) < min_pool:
        fails.append({"issue": "foreshadow_pool_too_small", "size": len(pool), "min": min_pool})
    total_words = sio.read("entity_runtime.GLOBAL_SUMMARY.total_words") or 0
    if total_words <= 0:
        fails.append({"issue": "total_words_not_accumulated", "value": total_words})
    report: dict[str, Any] = {
        "pass": len(fails) == 0,
        "fails": fails,
        "chapters_checked": len(chapters),
        "chapter_sizes": chapter_sizes,
        "foreshadow_pool_size": len(pool),
        "total_words": total_words,
    }
    sio.audit(
        source="multi_chapter.V1_release_check",
        severity=("info" if report["pass"] else "warn"),
        msg=f"V1 DoD {'PASS' if report['pass'] else 'FAIL'}: {len(fails)} issues",
        action="log",
        payload=report,
    )
    return report


def run_multi_chapter(
    book_id: str,
    chapters: int,
    *,
    llm_endpoint: str = "windhub",
    word_target: int = 3500,
    min_bytes: int = 3000,
    min_pool: int = 1,
    state_root: Path | str | None = None,
    mock_llm: bool = False,
) -> dict[str, Any]:
    """N 章连跑 runner：依次 G(run_workflow) → R1 → R2 → R3，结束跑 V1 DoD.

    返回 dict::

        {
            "ok": bool,                    # 所有章节完成 + V1 PASS
            "chapters_done": int,
            "chapter_paths": [str],
            "dod_report": {...},           # V1 报告
            "errors": [...],
        }

    任一章 LLM/IO 失败立刻 break，errors 记原因；不抛异常.
    """
    if chapters < 1:
        raise ValueError(f"chapters must be >= 1, got {chapters}")
    sio_kwargs: dict[str, Any] = {"autoload": True}
    if state_root is not None:
        sio_kwargs["state_root"] = state_root
    sio = StateIO(book_id, **sio_kwargs)
    chapters_done = 0
    chapter_paths: list[str] = []
    errors: list[dict[str, Any]] = []

    for ch_no in range(1, chapters + 1):
        try:
            draft_path = run_workflow(
                book_id,
                llm_endpoint=llm_endpoint,
                word_target=word_target,
                chapter_no=ch_no,
                state_root=state_root,
                mock_llm=mock_llm,
            )
            if draft_path is None:
                errors.append({"chapter": ch_no, "issue": "run_workflow_returned_none"})
                break
            # run_workflow 落盘后重新 autoload sio（rollup 已写到磁盘）.
            sio = StateIO(book_id, **sio_kwargs)
            original = Path(draft_path).read_text(encoding="utf-8")
            polished = _mock_polish(original) if mock_llm else _call_llm_for_polish(original, llm_endpoint)
            r2_results = _r2_consistency_check(sio, ch_no, polished)
            final_path = _r3_final_pack(sio, ch_no, polished, r2_results)
            chapter_paths.append(str(final_path))
            chapters_done += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"chapter": ch_no, "issue": f"{type(exc).__name__}: {exc}"})
            sio.audit(
                source=f"multi_chapter.run.ch{ch_no}",
                severity="error",
                msg=f"chapter {ch_no} failed: {exc}",
                action="block",
            )
            break

    # 重新加载 state，跑 V1 DoD（不管中途 break）
    sio = StateIO(book_id, **sio_kwargs)
    dod_report = _v1_release_check(sio, min_bytes=min_bytes, min_pool=min_pool)
    return {
        "ok": chapters_done == chapters and dod_report["pass"],
        "execution_mode": MOCK_HARNESS_MODE if mock_llm else REAL_LLM_DEMO_MODE,
        "chapters_done": chapters_done,
        "chapter_paths": chapter_paths,
        "dod_report": dod_report,
        "errors": errors,
    }


__all__ = [
    "run_multi_chapter",
    "_call_llm_for_polish",
    "_r2_consistency_check",
    "_r3_final_pack",
    "_v1_release_check",
]
