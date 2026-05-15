"""v1.5 Review / deslop warn-only sidecar contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class ReviewDeslopContractTest(unittest.TestCase):
    def _seed_book(self, root: Path, book_id: str = "review-book") -> None:
        from ginga_platform.orchestrator.runner.state_io import StateIO

        sio = StateIO(book_id, state_root=root)
        sio.apply(
            {
                "locked.STORY_DNA": {
                    "premise": "失忆刺客追索短刃来源",
                    "conflict_engine": "记忆空白 vs 微粒掠夺集团",
                },
                "locked.GENRE_LOCKED": {
                    "topic": ["玄幻黑暗"],
                    "style_lock": {
                        "forbidden_styles": ["游戏系统播报腔", "轻小说吐槽腔"],
                        "anchor_phrases": ["微粒", "天堑"],
                    },
                },
                "entity_runtime.GLOBAL_SUMMARY": {"total_words": 4000},
            },
            source="test.seed_review_book",
        )
        sio.write_artifact(
            "chapter_01.md",
            (
                "# 第一章\n\n"
                "无明在雨夜醒来，突然感到一种说不出的感觉。"
                "系统提示：叮，恭喜获得短刃。"
                "他仿佛听见命运的齿轮开始转动。\n"
            ),
            source="test.seed_review_chapter",
            artifact_type="chapter_text",
            payload={"chapter_no": 1, "execution_mode": "mock_harness"},
        )

    def _snapshot_files(self, root: Path) -> dict[str, str]:
        return {
            path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_review_writes_warn_only_sidecar_and_never_edits_state_or_chapters(self) -> None:
        from ginga_platform.orchestrator.review import export_review_report

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "reviews"
            self._seed_book(state_root)
            before_state = self._snapshot_files(state_root)

            result = export_review_report(
                "review-book",
                run_id="run-001",
                state_root=state_root,
                output_root=output_root,
            )

            out_dir = output_root / "review-book" / "run-001"
            report_path = out_dir / "review_report.json"
            self.assertEqual(Path(result["output_dir"]), out_dir)
            self.assertEqual(result["status"], "warn")
            self.assertTrue(report_path.exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertEqual(self._snapshot_files(state_root), before_state)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["kind"], "ReviewDeslopReport")
            self.assertEqual(report["mode"], "warn_only")
            self.assertFalse(report["auto_edit"])
            self.assertFalse(report["passed"])
            self.assertEqual(report["rubric"]["scope"], "report_only")
            self.assertFalse(report["projection"]["writes_runtime_state"])
            self.assertGreaterEqual(report["summary"]["issue_count"], 1)

    def test_review_default_sources_exclude_book_analysis_and_do_not_leak_pollution(self) -> None:
        from ginga_platform.orchestrator.review import export_review_report

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "reviews"
            self._seed_book(state_root)
            polluted = root / ".ops" / "book_analysis" / "run-1"
            polluted.mkdir(parents=True)
            (polluted / "leak.json").write_text('{"leak": "BOOK_ANALYSIS_SENTINEL"}', encoding="utf-8")

            export_review_report(
                "review-book",
                run_id="run-001",
                state_root=state_root,
                output_root=output_root,
            )

            report_text = (output_root / "review-book" / "run-001" / "review_report.json").read_text(
                encoding="utf-8"
            )
            readme_text = (output_root / "review-book" / "run-001" / "README.md").read_text(encoding="utf-8")
            report = json.loads(report_text)
            self.assertIn(".ops/book_analysis/**", report["data_sources"]["forbidden_default_sources"])
            self.assertNotIn("BOOK_ANALYSIS_SENTINEL", report_text)
            self.assertNotIn("BOOK_ANALYSIS_SENTINEL", readme_text)

    def test_cli_review_warn_only_exit_zero(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "reviews"
            self._seed_book(state_root)

            code = main(
                [
                    "review",
                    "review-book",
                    "--run-id",
                    "cli-run",
                    "--state-root",
                    str(state_root),
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue((output_root / "review-book" / "cli-run" / "review_report.json").exists())

    def test_review_rubric_is_not_in_creation_prompt(self) -> None:
        from ginga_platform.orchestrator.cli.demo_pipeline import _build_chapter_prompt
        from ginga_platform.orchestrator.runner.state_io import StateIO

        with tempfile.TemporaryDirectory() as d:
            state_root = Path(d) / "runtime_state"
            self._seed_book(state_root)
            state = StateIO("review-book", state_root=state_root, autoload=True).state

            prompt = _build_chapter_prompt(state, word_target=4000, chapter_no=1)

            self.assertNotIn("platform_cn_webnovel_v1", prompt)
            self.assertNotIn("ReviewDeslopReport", prompt)
            self.assertNotIn("AI 味", prompt)
            self.assertNotIn("rubric", prompt.lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
