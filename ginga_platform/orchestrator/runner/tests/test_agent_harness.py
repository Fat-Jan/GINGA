"""Offline agent harness tests.

The harness must exercise the public CLI shape without calling ask-llm:
runtime mock paths, one failing path, and v2.2 report-only/read-only sidecars.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml


class AgentHarnessTest(unittest.TestCase):
    def test_multi_agent_harness_accepts_main_validated_write_task(self) -> None:
        from scripts.validate_multi_agent_harness import validate_board

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            board = root / "board.json"
            board.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-05-16T13:00:00+08:00",
                        "tasks": [
                            {
                                "task_id": "v2.4-worker",
                                "title": "Multi-agent harness validator",
                                "status": "done",
                                "owner": "main-agent validation after Codex subagent callback",
                                "mode": "write-capable",
                                "owned_files": ["scripts/validate_multi_agent_harness.py"],
                                "forbidden_files": ["STATUS.md", "scripts/run_real_llm_harness.py"],
                                "expected_output": ".ops/validation/multi_agent_harness.json",
                                "verification": "python3 scripts/validate_multi_agent_harness.py",
                                "created_at": "2026-05-16T12:00:00+08:00",
                                "updated_at": "2026-05-16T13:00:00+08:00",
                                "evidence": ["unit test PASS", "validator report written"],
                                "blockers": [],
                                "handoff_note": "main-agent validated evidence and marked done",
                                "model_contract": {
                                    "provider": "OpenAI Codex subagent runtime",
                                    "model_tier": "coding worker",
                                    "reason": "bounded validator implementation",
                                    "fallback": "return BLOCKED with exact fields",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = validate_board(board)

            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["errors"], [])
            self.assertTrue(all(check["status"] == "PASS" for check in result["checks"]), result)

    def test_multi_agent_harness_rejects_subagent_done_and_weak_contracts(self) -> None:
        from scripts.validate_multi_agent_harness import validate_board

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            board = root / "board.json"
            board.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-05-16T13:00:00+08:00",
                        "tasks": [
                            {
                                "task_id": "bad-status",
                                "title": "Bad status",
                                "status": "complete",
                                "owner": "worker",
                                "owned_files": ["*"],
                                "expected_output": ".ops/validation/out.json",
                                "verification": "python3 scripts/example.py",
                                "created_at": "2026-05-16T12:00:00+08:00",
                                "updated_at": "2026-05-16T13:00:00+08:00",
                                "evidence": [],
                                "blockers": [],
                            },
                            {
                                "task_id": "subagent-done",
                                "title": "Subagent sole done authority near real LLM",
                                "status": "done",
                                "owner": "Codex subagent runtime",
                                "mode": "write-capable",
                                "owned_files": ["scripts/run_real_llm_harness.py"],
                                "expected_output": ".ops/reports/out.md",
                                "verification": "python3 scripts/run_real_llm_harness.py",
                                "created_at": "2026-05-16T12:00:00+08:00",
                                "updated_at": "2026-05-16T13:00:00+08:00",
                                "evidence": [],
                                "blockers": [],
                                "model_contract": {
                                    "provider": "OpenAI Codex subagent runtime",
                                    "model": "inherited",
                                    "reason": "test",
                                },
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = validate_board(board)

            self.assertEqual(result["status"], "FAIL", result)
            errors = "\n".join(result["errors"])
            self.assertIn("bad-status: status 'complete' is not allowed", errors)
            self.assertIn("bad-status: write-capable-looking task is missing model_contract", errors)
            self.assertIn("bad-status: write-capable task owned_files may not use repo root wildcard", errors)
            self.assertIn("subagent-done: done requires non-empty evidence", errors)
            self.assertIn("subagent-done: done requires main-agent validation", errors)
            self.assertIn("subagent-done: model_contract missing fallback", errors)
            self.assertIn("subagent-done: forbidden_files required for harness/agent/real LLM boundary tasks", errors)

    def test_multi_agent_harness_summarizes_legacy_done_gaps_without_warning_noise(self) -> None:
        from scripts.validate_multi_agent_harness import validate_board

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            board = root / "board.json"
            board.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-05-16T13:00:00+08:00",
                        "tasks": [
                            {
                                "task_id": "legacy-done",
                                "title": "Legacy done before v2.4",
                                "status": "done",
                                "owner": "old worker",
                                "owned_files": ["scripts/old.py"],
                                "expected_output": ".ops/reports/old.md",
                                "verification": "old check",
                                "created_at": "2026-05-13T12:00:00+08:00",
                                "updated_at": "2026-05-13T13:00:00+08:00",
                                "evidence": [],
                                "blockers": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = validate_board(board)

            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["warnings"], [])
            self.assertEqual(len(result["legacy_warnings"]), 3)

    def test_offline_harness_covers_cli_paths_and_error_exit_codes(self) -> None:
        from scripts.run_agent_harness import run_harness

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            json_output = root / "agent_harness.json"
            report_output = root / "agent_harness.md"

            result = run_harness(
                state_root=state_root,
                json_output=json_output,
                report_output=report_output,
            )

            self.assertTrue(result["passed"], result)
            cases = {case["name"]: case for case in result["cases"]}
            self.assertEqual(
                set(cases),
                {
                    "init",
                    "single_run",
                    "multi_chapter",
                    "immersive",
                    "missing_state_error",
                    "inspect_book_view",
                    "query_book_view",
                    "review_sidecar",
                    "market_sidecar",
                    "observability_workflow_stages",
                    "observability_evidence_pack",
                    "observability_migration_audit",
                    "model_topology_observe",
                },
            )

            for name, case in cases.items():
                self.assertEqual(case["exit_code"], case["expected_exit_code"], name)
                self.assertTrue(case["passed"], case)
            self.assertEqual(cases["missing_state_error"]["exit_code"], 1)

            for name in ("single_run", "multi_chapter", "immersive"):
                self.assertEqual(cases[name]["execution_mode"], "mock_harness")
            for name in (
                "inspect_book_view",
                "query_book_view",
                "review_sidecar",
                "market_sidecar",
                "observability_workflow_stages",
                "observability_evidence_pack",
                "observability_migration_audit",
                "model_topology_observe",
            ):
                self.assertEqual(cases[name]["execution_mode"], "cli_report_only")

            init_state = state_root / "harness-init"
            for domain in ("locked", "entity_runtime", "workspace", "retrieved", "audit_log"):
                self.assertTrue((init_state / f"{domain}.yaml").exists(), domain)

            single_state = state_root / "harness-single"
            self.assertTrue((single_state / "chapter_01.md").exists())
            single_audit = yaml.safe_load((single_state / "audit_log.yaml").read_text(encoding="utf-8"))
            entries = single_audit.get("entries", [])
            self.assertTrue(
                any(entry.get("payload", {}).get("artifact_type") == "chapter_text" for entry in entries),
                entries,
            )

            multi_chapters = sorted((state_root / "harness-multi").glob("chapter_*.md"))
            self.assertEqual([path.name for path in multi_chapters], ["chapter_01.md", "chapter_02.md"])

            immersive_chapters = sorted((state_root / "harness-immersive").glob("chapter_*.md"))
            self.assertEqual([path.name for path in immersive_chapters], ["chapter_01.md", "chapter_02.md"])

            ops_root = root / ".ops"
            book_view = ops_root / "book_views" / "harness-sidecar" / "harness-inspect" / "book_view.json"
            review = ops_root / "reviews" / "harness-sidecar" / "harness-review" / "review_report.json"
            market = ops_root / "market_research" / "harness-market" / "harness-market" / "market_report.json"
            workflow = ops_root / "workflow_observability" / "harness-workflow" / "workflow_stage_report.json"
            evidence = ops_root / "jury" / "evidence_packs" / "harness-evidence" / "evidence_pack.json"
            migration = ops_root / "migration_audit" / "harness-migration" / "migration_audit.json"
            topology = ops_root / "model_topology" / "harness-topology" / "model_topology_report.json"

            for path in (book_view, review, market, workflow, evidence, migration, topology):
                self.assertTrue(path.exists(), path)

            self.assertFalse((state_root / "harness-sidecar" / ".ops").exists())
            book_view_payload = json.loads(book_view.read_text(encoding="utf-8"))
            self.assertEqual(book_view_payload["projection"]["truth_source"], "StateIO")
            self.assertFalse(book_view_payload["projection"]["is_state_truth"])

            query_stdout = cases["query_book_view"]["stdout_tail"]
            query_payload = json.loads(query_stdout)
            self.assertEqual(query_payload["mode"], "read_only")
            self.assertIn("match_count", query_payload)
            self.assertNotIn("BOOK_ANALYSIS_SENTINEL", query_stdout)

            review_payload = json.loads(review.read_text(encoding="utf-8"))
            self.assertEqual(review_payload["kind"], "ReviewDeslopReport")
            self.assertEqual(review_payload["mode"], "warn_only")
            self.assertFalse(review_payload["auto_edit"])
            self.assertFalse(review_payload["projection"]["writes_runtime_state"])

            market_payload = json.loads(market.read_text(encoding="utf-8"))
            self.assertEqual(market_payload["kind"], "MarketResearchSidecarReport")
            self.assertEqual(market_payload["collection_mode"], "offline_fixture")
            self.assertTrue(market_payload["authorization"]["explicit"])
            self.assertFalse(market_payload["projection"]["writes_runtime_state"])
            self.assertFalse(market_payload["rag_policy"]["default_rag_eligible"])
            self.assertNotIn("EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK", market.read_text(encoding="utf-8"))

            workflow_payload = json.loads(workflow.read_text(encoding="utf-8"))
            self.assertEqual(workflow_payload["mode"], "report_only")
            self.assertFalse(workflow_payload["runs_workflow"])
            self.assertFalse(workflow_payload["writes_runtime_state"])
            self.assertGreater(workflow_payload["stage_count"], 0)

            evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(evidence_payload["mode"], "report_only")
            self.assertEqual(evidence_payload["evidence_count"], 1)
            self.assertFalse(evidence_payload["writes_runtime_state"])
            self.assertNotIn("SENTINEL_FULL_TEXT_SHOULD_NOT_COPY", evidence.read_text(encoding="utf-8"))

            migration_payload = json.loads(migration.read_text(encoding="utf-8"))
            self.assertEqual(migration_payload["mode"], "report_only")
            self.assertFalse(migration_payload["auto_migrate"])
            self.assertFalse(migration_payload["writes_runtime_state"])
            self.assertIn(".ops/book_analysis/run-1/source.md", migration_payload["forbidden_source_hits"])

            topology_payload = json.loads(topology.read_text(encoding="utf-8"))
            self.assertEqual(topology_payload["mode"], "report_only")
            self.assertFalse(topology_payload["runtime_takeover"])
            self.assertFalse(topology_payload["probe_summary"]["live_probe_enabled"])
            self.assertTrue(topology_payload["role_matrix"])
            self.assertTrue(all(item["status"] == "not_run" for item in topology_payload["probe_results"]))

            self.assertTrue(json_output.exists())
            report_text = report_output.read_text(encoding="utf-8")
            self.assertIn("mock_harness", report_text)
            self.assertIn("v2.2", report_text)
            self.assertIn("does not prove production readiness", report_text)

    def test_cli_rejects_real_llm_batches_above_v17_3_upper_bound(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            init_code = cli_main(
                [
                    "init",
                    "policy-book",
                    "--topic",
                    "玄幻黑暗",
                    "--premise",
                    "policy test premise",
                    "--state-root",
                    str(state_root),
                ]
            )
            self.assertEqual(init_code, 0)

            run_code = cli_main(
                [
                    "run",
                    "policy-book",
                    "--chapters",
                    "6",
                    "--state-root",
                    str(state_root),
                ]
            )
            self.assertEqual(run_code, 1)
            self.assertEqual(list((state_root / "policy-book").glob("chapter_*.md")), [])

    def test_cli_immersive_defaults_to_recommended_four_chapter_batch(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            self.assertEqual(
                cli_main(
                    [
                        "init",
                        "default-immersive-book",
                        "--topic",
                        "玄幻黑暗",
                        "--premise",
                        "default batch policy premise",
                        "--state-root",
                        str(state_root),
                    ]
                ),
                0,
            )

            self.assertEqual(
                cli_main(
                    [
                        "run",
                        "default-immersive-book",
                        "--mock-llm",
                        "--immersive",
                        "--word-target",
                        "200",
                        "--state-root",
                        str(state_root),
                    ]
                ),
                0,
            )
            chapters = sorted((state_root / "default-immersive-book").glob("chapter_*.md"))
            self.assertEqual([path.name for path in chapters], [f"chapter_{idx:02d}.md" for idx in range(1, 5)])

    def test_cli_blocks_real_llm_when_existing_longform_hard_gate_fails(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main as cli_main
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            self.assertEqual(
                cli_main(
                    [
                        "init",
                        "hard-gate-book",
                        "--topic",
                        "玄幻黑暗",
                        "--premise",
                        "无明在末日天堑追索血脉繁衍契约",
                        "--state-root",
                        str(state_root),
                    ]
                ),
                0,
            )
            sio = StateIO("hard-gate-book", state_root=state_root, autoload=True)
            sio.apply(
                {
                    "locked.STORY_DNA": {
                        "premise": "无明在末日天堑追索血脉繁衍契约",
                        "conflict_engine": "血脉繁衍契约 vs 末日城邦",
                    },
                    "locked.GENRE_LOCKED": {
                        "topic": ["玄幻黑暗", "末日多子多福"],
                        "style_lock": {"anchor_phrases": ["血脉", "末日", "繁衍契约"]},
                    },
                },
                source="test.seed_hard_gate",
            )
            loop_opening = (
                "无明睁开眼，发现自己又在天堑边缘，体内微粒正在短刃旁蠕动。"
                "失忆像灰白雾气一样覆盖记忆。"
            )
            for chapter_no in (1, 2):
                sio.write_artifact(
                    f"chapter_{chapter_no:02d}.md",
                    f"# 第{chapter_no}章\n\n{loop_opening * 40}",
                    source=f"test.seed_loop.{chapter_no}",
                    artifact_type="chapter_text",
                    payload={"chapter_no": chapter_no},
                )

            run_code = cli_main(
                [
                    "run",
                    "hard-gate-book",
                    "--chapters",
                    "1",
                    "--state-root",
                    str(state_root),
                ]
            )

            self.assertEqual(run_code, 1)
            self.assertFalse((state_root / "hard-gate-book" / "chapter_03.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
