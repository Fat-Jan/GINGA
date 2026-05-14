"""ginga CLI entrypoint — argparse based, dispatches to demo_pipeline.

Usage:
    python3 -m ginga_platform.orchestrator.cli init <book_id> --topic <topic>
    python3 -m ginga_platform.orchestrator.cli run <book_id>
    python3 -m ginga_platform.orchestrator.cli status <book_id>
    python3 -m ginga_platform.orchestrator.cli idea add <title> [--body <text>] [--stdin]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ginga_platform.orchestrator.cli.demo_pipeline import (
    init_book,
    run_workflow,
    show_status,
)
from ginga_platform.orchestrator.cli.idea import add_idea


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ginga",
        description="Ginga Sprint 1 MVP — 输入创意 → 输出第一章",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="初始化新书（建空 state + 写入初始 locked 域）")
    p_init.add_argument("book_id", help="书 id（用作 foundation/runtime_state/<book_id>/ 目录名）")
    p_init.add_argument("--topic", required=True, help="题材（如 玄幻黑暗）")
    p_init.add_argument(
        "--premise",
        default="主角是一个失忆的刺客，醒来发现自己被卷入了一场跨越四重天堑的微粒争夺战",
        help="一句话核心冲突（默认 demo premise）",
    )
    p_init.add_argument(
        "--word-target",
        type=int,
        default=500000,
        help="字数目标（默认 500000）",
    )

    p_run = sub.add_parser("run", help="跑 workflow MVP（A-H 12 step，G 调 dark-fantasy 生成第一章）")
    p_run.add_argument("book_id")
    p_run.add_argument(
        "--llm-endpoint",
        default="windhub",
        help="ask-llm 端点 alias（默认 windhub）",
    )
    p_run.add_argument(
        "--word-target",
        type=int,
        default=3500,
        help="第一章字数目标（默认 3500）",
    )
    # immersive_mode（dark-fantasy 独有，ST-S2-I IMMERSIVE）
    p_run.add_argument(
        "--immersive",
        action="store_true",
        help="进入沉浸专线：连续多章 batch；checker 期内静默；exit 时批量 apply + R2 一致性",
    )
    p_run.add_argument(
        "--chapters",
        type=int,
        default=1,
        help="章节数：>=2 触发 multi_chapter runner（S-3/S-4/S-5 R1-R3 + V1 DoD）；仅 --immersive 时走沉浸专线",
    )

    p_status = sub.add_parser("status", help="查看 book 当前 state 状态")
    p_status.add_argument("book_id")

    p_idea = sub.add_parser("idea", help="raw idea 暂存区：只落盘，不进 state/RAG")
    idea_sub = p_idea.add_subparsers(dest="idea_cmd", required=True)
    p_idea_add = idea_sub.add_parser("add", help="写入一条 raw idea")
    p_idea_add.add_argument("title", help="灵感标题")
    p_idea_add.add_argument("--body", help="正文")
    p_idea_add.add_argument("--stdin", action="store_true", help="从标准输入读取正文")

    args = parser.parse_args(argv)

    if args.cmd == "init":
        init_book(args.book_id, topic=args.topic, premise=args.premise, word_target=args.word_target)
        print(f"✅ init done: foundation/runtime_state/{args.book_id}/")
        return 0
    elif args.cmd == "run":
        # immersive 分支：dispatch 到 ImmersiveRunner.run_block
        if getattr(args, "immersive", False):
            from ginga_platform.orchestrator.cli.immersive_runner import ImmersiveRunner
            runner = ImmersiveRunner(args.book_id)
            result = runner.run_block(
                chapters=args.chapters,
                llm_endpoint=args.llm_endpoint,
                word_target=args.word_target,
            )
            if result.get("last_error"):
                print(f"❌ immersive run failed: {result['last_error']}", file=sys.stderr)
                return 1
            print(f"✅ immersive done: {result['chapter_count']} chapters, "
                  f"applied={result['applied_count']}, paths={result['chapter_paths']}")
            return 0
        # 非 immersive：--chapters >= 2 走 multi_chapter runner（S-3/S-4/S-5）
        if getattr(args, "chapters", 1) >= 2:
            from ginga_platform.orchestrator.cli.multi_chapter import run_multi_chapter
            result = run_multi_chapter(
                args.book_id,
                chapters=args.chapters,
                llm_endpoint=args.llm_endpoint,
                word_target=args.word_target,
            )
            if not result["ok"]:
                print(
                    f"❌ multi_chapter failed: chapters_done={result['chapters_done']}, "
                    f"errors={result['errors']}, dod={result['dod_report']['fails']}",
                    file=sys.stderr,
                )
                return 1
            print(
                f"✅ multi_chapter done: {result['chapters_done']}/{args.chapters} chapters, "
                f"DoD PASS, total_words={result['dod_report']['total_words']}, "
                f"foreshadow_pool={result['dod_report']['foreshadow_pool_size']}"
            )
            return 0
        chapter_path = run_workflow(args.book_id, llm_endpoint=args.llm_endpoint, word_target=args.word_target)
        if chapter_path is None:
            print("❌ run failed", file=sys.stderr)
            return 1
        size = Path(chapter_path).stat().st_size
        print(f"✅ run done: {chapter_path} ({size} bytes)")
        return 0
    elif args.cmd == "status":
        show_status(args.book_id)
        return 0
    elif args.cmd == "idea":
        if args.idea_cmd == "add":
            stdin_text = sys.stdin.read() if args.stdin else None
            rel_path = add_idea(args.title, body=args.body, stdin_text=stdin_text, root=Path.cwd())
            print(rel_path.as_posix())
            return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
