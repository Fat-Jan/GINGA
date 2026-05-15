"""ginga CLI entrypoint — argparse based, dispatches to demo_pipeline.

Usage:
    python3 -m ginga_platform.orchestrator.cli init <book_id> --topic <topic>
    python3 -m ginga_platform.orchestrator.cli run <book_id>
    python3 -m ginga_platform.orchestrator.cli status <book_id>
    python3 -m ginga_platform.orchestrator.cli review <book_id>
    python3 -m ginga_platform.orchestrator.cli market <book_id> --fixture <path> --authorize
    python3 -m ginga_platform.orchestrator.cli model-topology observe
    python3 -m ginga_platform.orchestrator.cli observability workflow-stages
    python3 -m ginga_platform.orchestrator.cli idea add <title> [--body <text>] [--stdin]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ginga_platform.orchestrator.cli.demo_pipeline import (
    MOCK_HARNESS_MODE,
    init_book,
    _mock_chapter_text,
    run_workflow,
    show_status,
)
from ginga_platform.orchestrator.cli.idea import add_idea
from ginga_platform.orchestrator.cli.longform_policy import (
    DEFAULT_CHAPTER_BATCH_SIZE,
    MAX_REAL_LLM_CHAPTER_BATCH_SIZE,
    load_chapter_artifacts,
    validate_longform_hard_gate,
    validate_real_llm_batch_size,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


def _validate_real_llm_preflight(book_id: str, *, state_root: Path | None, mock_llm: bool) -> None:
    if mock_llm:
        return
    sio = StateIO(book_id, state_root=state_root, autoload=True)
    chapters = load_chapter_artifacts(sio.state_dir)
    validate_longform_hard_gate(state=sio.state, chapters=chapters, mock_llm=mock_llm)


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
    p_init.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )

    p_run = sub.add_parser("run", help="跑 workflow MVP（A-H 12 step，G 调 dark-fantasy 生成第一章）")
    p_run.add_argument("book_id")
    p_run.add_argument(
        "--llm-endpoint",
        default="久久",
        help="ask-llm 端点 alias（默认 久久）",
    )
    p_run.add_argument(
        "--word-target",
        type=int,
        default=4000,
        help="第一章字数目标（默认 4000）",
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
        default=None,
        help=(
            f"章节数：>=2 触发 multi_chapter runner；--immersive 未指定时默认 {DEFAULT_CHAPTER_BATCH_SIZE} 章；"
            f"真实 LLM 生产上限 {MAX_REAL_LLM_CHAPTER_BATCH_SIZE} 章"
        ),
    )
    p_run.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )
    p_run.add_argument(
        "--mock-llm",
        action="store_true",
        help="离线 harness 模式：不调用 ask-llm，只生成固定 mock 章节；不得用于声明真实 LLM demo 完成",
    )

    p_status = sub.add_parser("status", help="查看 book 当前 state 状态")
    p_status.add_argument("book_id")
    p_status.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )

    p_inspect = sub.add_parser("inspect", help="导出只读 BookView projection")
    p_inspect.add_argument("book_id")
    p_inspect.add_argument("--run-id", help="BookView run id；默认 UTC 时间戳")
    p_inspect.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )
    p_inspect.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/book_views"),
        help="BookView 输出根目录（默认 .ops/book_views）",
    )

    p_query = sub.add_parser("query", help="只读查询 StateIO / chapter artifacts")
    p_query.add_argument("book_id")
    p_query.add_argument("query")
    p_query.add_argument("--limit", type=int, default=10)
    p_query.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )

    p_review = sub.add_parser("review", help="导出 warn-only Review / deslop sidecar 报告")
    p_review.add_argument("book_id")
    p_review.add_argument("--run-id", help="Review run id；默认 UTC 时间戳")
    p_review.add_argument("--rubric-profile", default="platform_cn_webnovel_v1")
    p_review.add_argument(
        "--state-root",
        type=Path,
        help="runtime_state 根目录；测试/harness 可传临时目录，默认 foundation/runtime_state",
    )
    p_review.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/reviews"),
        help="Review 输出根目录（默认 .ops/reviews）",
    )

    p_market = sub.add_parser("market", help="导出显式授权的 Market Research sidecar 报告")
    p_market.add_argument("book_id")
    p_market.add_argument("--run-id", help="Market Research run id；默认 UTC 时间戳")
    p_market.add_argument("--fixture", type=Path, required=True, help="离线市场 fixture JSON")
    p_market.add_argument(
        "--authorize",
        action="store_true",
        help="显式授权本次市场 sidecar 读取离线 fixture；未传则拒绝执行",
    )
    p_market.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/market_research"),
        help="Market Research 输出根目录（默认 .ops/market_research）",
    )

    p_model_topology = sub.add_parser("model-topology", help="只读模型拓扑观察报告")
    model_topology_sub = p_model_topology.add_subparsers(dest="model_topology_cmd", required=True)
    p_model_topology_observe = model_topology_sub.add_parser(
        "observe",
        help="导出 role/stage/provider 观察报告；默认不跑 live probe",
    )
    p_model_topology_observe.add_argument("--run-id", help="model topology run id；默认 UTC 时间戳")
    p_model_topology_observe.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/model_topology"),
        help="Model topology 输出根目录（默认 .ops/model_topology）",
    )
    p_model_topology_observe.add_argument(
        "--probe-live",
        action="store_true",
        help="显式运行 ask-llm 最小探针；默认只写 not_run 观察报告",
    )

    p_observability = sub.add_parser("observability", help="report-only 证据与工作流可观测性")
    observability_sub = p_observability.add_subparsers(dest="observability_cmd", required=True)
    p_workflow_stages = observability_sub.add_parser("workflow-stages", help="导出只读 workflow stage 观察报告")
    p_workflow_stages.add_argument("--run-id", help="run id；默认 UTC 时间戳")
    p_workflow_stages.add_argument(
        "--workflow-path",
        type=Path,
        default=Path("ginga_platform/orchestrator/workflows/novel_pipeline_mvp.yaml"),
        help="Workflow YAML 路径",
    )
    p_workflow_stages.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/workflow_observability"),
        help="Workflow observability 输出根目录（默认 .ops/workflow_observability）",
    )
    p_evidence_pack = observability_sub.add_parser("evidence-pack", help="导出 citation-only jury evidence pack")
    p_evidence_pack.add_argument("--run-id", help="run id；默认 UTC 时间戳")
    p_evidence_pack.add_argument(
        "--evidence",
        type=Path,
        action="append",
        required=True,
        help="证据文件路径，可重复；只引用 sha256/大小，不复制全文",
    )
    p_evidence_pack.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/jury/evidence_packs"),
        help="Evidence pack 输出根目录（默认 .ops/jury/evidence_packs）",
    )
    p_migration_audit = observability_sub.add_parser("migration-audit", help="导出只读迁移/污染源审计报告")
    p_migration_audit.add_argument("--run-id", help="run id；默认 UTC 时间戳")
    p_migration_audit.add_argument(
        "--scan-root",
        type=Path,
        action="append",
        required=True,
        help="扫描根路径，可重复",
    )
    p_migration_audit.add_argument(
        "--output-root",
        type=Path,
        default=Path(".ops/migration_audit"),
        help="Migration audit 输出根目录（默认 .ops/migration_audit）",
    )

    p_idea = sub.add_parser("idea", help="raw idea 暂存区：只落盘，不进 state/RAG")
    idea_sub = p_idea.add_subparsers(dest="idea_cmd", required=True)
    p_idea_add = idea_sub.add_parser("add", help="写入一条 raw idea")
    p_idea_add.add_argument("title", help="灵感标题")
    p_idea_add.add_argument("--body", help="正文")
    p_idea_add.add_argument("--stdin", action="store_true", help="从标准输入读取正文")

    args = parser.parse_args(argv)

    if args.cmd == "init":
        init_book(
            args.book_id,
            topic=args.topic,
            premise=args.premise,
            word_target=args.word_target,
            state_root=args.state_root,
        )
        state_root = args.state_root or Path("foundation/runtime_state")
        print(f"✅ init done: {state_root / args.book_id}")
        return 0
    elif args.cmd == "run":
        requested_chapters = (
            args.chapters
            if args.chapters is not None
            else (DEFAULT_CHAPTER_BATCH_SIZE if getattr(args, "immersive", False) else 1)
        )
        try:
            validate_real_llm_batch_size(requested_chapters, mock_llm=args.mock_llm)
            _validate_real_llm_preflight(args.book_id, state_root=args.state_root, mock_llm=args.mock_llm)
        except ValueError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 1
        # immersive 分支：dispatch 到 ImmersiveRunner.run_block
        if getattr(args, "immersive", False):
            from ginga_platform.orchestrator.cli.immersive_runner import ImmersiveRunner
            llm_caller = None
            execution_mode = None
            if getattr(args, "mock_llm", False):
                execution_mode = MOCK_HARNESS_MODE

                def llm_caller(prompt: str, endpoint: str, **_kw: object) -> str:
                    chapter_no = len(getattr(llm_caller, "_calls", [])) + 1
                    getattr(llm_caller, "_calls", []).append(chapter_no)
                    return _mock_chapter_text(chapter_no, args.word_target)

                setattr(llm_caller, "_calls", [])
            runner = ImmersiveRunner(args.book_id, state_root=args.state_root, llm_caller=llm_caller)
            result = runner.run_block(
                chapters=requested_chapters,
                llm_endpoint=args.llm_endpoint,
                word_target=args.word_target,
                execution_mode=execution_mode,
            )
            if result.get("last_error"):
                print(f"❌ immersive run failed: {result['last_error']}", file=sys.stderr)
                return 1
            print(f"✅ immersive done: {result['chapter_count']} chapters, "
                  f"applied={result['applied_count']}, paths={result['chapter_paths']}")
            return 0
        # 非 immersive：--chapters >= 2 走 multi_chapter runner（S-3/S-4/S-5）
        if requested_chapters >= 2:
            from ginga_platform.orchestrator.cli.multi_chapter import run_multi_chapter
            result = run_multi_chapter(
                args.book_id,
                chapters=requested_chapters,
                llm_endpoint=args.llm_endpoint,
                word_target=args.word_target,
                state_root=args.state_root,
                mock_llm=args.mock_llm,
            )
            if not result["ok"]:
                print(
                    f"❌ multi_chapter failed: chapters_done={result['chapters_done']}, "
                    f"errors={result['errors']}, dod={result['dod_report']['fails']}",
                    file=sys.stderr,
                )
                return 1
            print(
                f"✅ multi_chapter done: {result['chapters_done']}/{requested_chapters} chapters, "
                f"DoD PASS, total_words={result['dod_report']['total_words']}, "
                f"foreshadow_pool={result['dod_report']['foreshadow_pool_size']}"
            )
            return 0
        chapter_path = run_workflow(
            args.book_id,
            llm_endpoint=args.llm_endpoint,
            word_target=args.word_target,
            state_root=args.state_root,
            mock_llm=args.mock_llm,
        )
        if chapter_path is None:
            print("❌ run failed", file=sys.stderr)
            return 1
        size = Path(chapter_path).stat().st_size
        print(f"✅ run done: {chapter_path} ({size} bytes)")
        return 0
    elif args.cmd == "status":
        show_status(args.book_id, state_root=args.state_root)
        return 0
    elif args.cmd == "inspect":
        from ginga_platform.orchestrator.book_view import export_book_view

        result = export_book_view(
            args.book_id,
            run_id=args.run_id,
            state_root=args.state_root,
            output_root=args.output_root,
        )
        print(f"✅ BookView exported: {result['output_dir']}")
        return 0
    elif args.cmd == "query":
        import json

        from ginga_platform.orchestrator.book_view import query_book_view

        result = query_book_view(
            args.book_id,
            args.query,
            state_root=args.state_root,
            limit=args.limit,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    elif args.cmd == "review":
        from ginga_platform.orchestrator.review import export_review_report

        result = export_review_report(
            args.book_id,
            run_id=args.run_id,
            state_root=args.state_root,
            output_root=args.output_root,
            rubric_profile=args.rubric_profile,
        )
        print(
            f"✅ Review report exported: {result['output_dir']} "
            f"(status={result['status']}, issues={result['issue_count']})"
        )
        return 0
    elif args.cmd == "market":
        from ginga_platform.orchestrator.market_research import export_market_research_report

        result = export_market_research_report(
            args.book_id,
            run_id=args.run_id,
            fixture_path=args.fixture,
            output_root=args.output_root,
            authorized=args.authorize,
        )
        print(
            f"✅ Market report exported: {result['output_dir']} "
            f"(signals={result['signal_count']})"
        )
        return 0
    elif args.cmd == "model-topology":
        if args.model_topology_cmd == "observe":
            from ginga_platform.orchestrator.model_topology import export_model_topology_observation

            result = export_model_topology_observation(
                run_id=args.run_id,
                output_root=args.output_root,
                probe_live=args.probe_live,
            )
            print(
                f"✅ Model topology observation exported: {result['output_dir']} "
                f"(live_probe={result['probe_summary']['live_probe_enabled']})"
            )
            return 0
    elif args.cmd == "observability":
        if args.observability_cmd == "workflow-stages":
            from ginga_platform.orchestrator.genm_observability import export_workflow_stage_observation

            result = export_workflow_stage_observation(
                run_id=args.run_id,
                workflow_path=args.workflow_path,
                output_root=args.output_root,
            )
            print(f"✅ Workflow stage observation exported: {result['output_dir']}")
            return 0
        if args.observability_cmd == "evidence-pack":
            from ginga_platform.orchestrator.genm_observability import export_jury_evidence_pack

            result = export_jury_evidence_pack(
                run_id=args.run_id,
                evidence_paths=args.evidence,
                output_root=args.output_root,
            )
            print(f"✅ Jury evidence pack exported: {result['output_dir']} (evidence={result['evidence_count']})")
            return 0
        if args.observability_cmd == "migration-audit":
            from ginga_platform.orchestrator.genm_observability import export_migration_audit

            result = export_migration_audit(
                run_id=args.run_id,
                scan_roots=args.scan_root,
                output_root=args.output_root,
                repo_root=Path.cwd(),
            )
            print(
                f"✅ Migration audit exported: {result['output_dir']} "
                f"(status={result['status']}, forbidden_hits={len(result['forbidden_source_hits'])})"
            )
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
