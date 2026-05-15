"""v1.4 BookView / read-only explorer contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml


class BookViewContractTest(unittest.TestCase):
    def _seed_book(self, root: Path, book_id: str = "view-book") -> None:
        from ginga_platform.orchestrator.runner.state_io import StateIO

        sio = StateIO(book_id, state_root=root)
        sio.apply(
            {
                "locked.STORY_DNA": {
                    "premise": "失忆刺客追索短刃来源",
                    "conflict_engine": "记忆空白 vs 微粒掠夺集团",
                },
                "locked.GENRE_LOCKED": {"topic": ["玄幻黑暗"]},
                "entity_runtime.CHARACTER_STATE": {
                    "protagonist": {
                        "name": "无明",
                        "events": [{"ch": 1, "type": "awakening", "impact": "短刃吞吐微粒"}],
                    }
                },
                "entity_runtime.FORESHADOW_STATE": {
                    "pool": [{"id": "fh-001", "status": "open", "summary": "短刃符文"}]
                },
                "entity_runtime.GLOBAL_SUMMARY": {"total_words": 4000},
                "workspace.progress": "chapter_1_done",
            },
            source="test.seed_book",
        )
        sio.write_artifact(
            "chapter_01.md",
            "# 第一章\n\n无明在雨夜醒来，短刃正在吞吐微粒。\n",
            source="test.seed_chapter",
            artifact_type="chapter_text",
            payload={"chapter_no": 1, "execution_mode": "mock_harness"},
        )

    def test_export_book_view_writes_projection_only_under_ops_book_views(self) -> None:
        from ginga_platform.orchestrator.book_view import export_book_view

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "book_views"
            self._seed_book(state_root)
            before_state_files = {
                path.relative_to(state_root).as_posix(): path.read_text(encoding="utf-8")
                for path in sorted(state_root.rglob("*"))
                if path.is_file()
            }

            result = export_book_view(
                "view-book",
                run_id="run-001",
                state_root=state_root,
                output_root=output_root,
            )

            out_dir = output_root / "view-book" / "run-001"
            self.assertEqual(Path(result["output_dir"]), out_dir)
            self.assertTrue((out_dir / "book_view.json").exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue((out_dir / "chapters" / "chapter_01.md").exists())
            self.assertEqual(
                {
                    path.relative_to(state_root).as_posix(): path.read_text(encoding="utf-8")
                    for path in sorted(state_root.rglob("*"))
                    if path.is_file()
                },
                before_state_files,
            )
            payload = json.loads((out_dir / "book_view.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["projection"]["truth_source"], "StateIO")
            self.assertFalse(payload["projection"]["is_state_truth"])
            self.assertIn(".ops/book_analysis/**", payload["data_sources"]["forbidden_default_sources"])
            self.assertNotIn(
                ".ops/book_analysis",
                json.dumps(payload["data_sources"]["chapter_artifacts"], ensure_ascii=False),
            )
            self.assertEqual(payload["chapters"][0]["title"], "第一章")

    def test_export_rejects_output_outside_book_views_root(self) -> None:
        from ginga_platform.orchestrator.book_view import BookViewError, export_book_view

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            self._seed_book(state_root)

            with self.assertRaisesRegex(BookViewError, "book_views"):
                export_book_view(
                    "view-book",
                    run_id="run-001",
                    state_root=state_root,
                    output_root=root / "bad_views",
                )

    def test_query_book_view_reads_clean_state_and_chapters(self) -> None:
        from ginga_platform.orchestrator.book_view import query_book_view

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            self._seed_book(state_root)
            polluted = root / ".ops" / "book_analysis" / "run-1"
            polluted.mkdir(parents=True)
            (polluted / "chapter_atoms.json").write_text('{"leak": "should_not_read"}', encoding="utf-8")

            result = query_book_view("view-book", "短刃", state_root=state_root)

            self.assertEqual(result["mode"], "read_only")
            self.assertGreaterEqual(result["match_count"], 1)
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertIn("fh-001", serialized)
            self.assertNotIn("should_not_read", serialized)

    def test_cli_inspect_and_query_are_read_only(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state_root = root / "runtime_state"
            output_root = root / ".ops" / "book_views"
            self._seed_book(state_root)

            inspect_code = main(
                [
                    "inspect",
                    "view-book",
                    "--run-id",
                    "cli-run",
                    "--state-root",
                    str(state_root),
                    "--output-root",
                    str(output_root),
                ]
            )
            query_code = main(["query", "view-book", "无明", "--state-root", str(state_root)])

            self.assertEqual(inspect_code, 0)
            self.assertEqual(query_code, 0)
            self.assertTrue((output_root / "view-book" / "cli-run" / "book_view.json").exists())
            self.assertFalse((state_root / "view-book" / ".ops").exists())
            self.assertTrue(yaml.safe_load((state_root / "view-book" / "locked.yaml").read_text(encoding="utf-8")))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
