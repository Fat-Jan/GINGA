"""Tests for the thin `ginga idea add` raw-idea capture CLI."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from ginga_platform.orchestrator.cli.__main__ import main
from ginga_platform.orchestrator.cli.idea import add_idea, build_parser


FIXED_NOW = datetime(2026, 5, 14, 3, 4, 5)


class IdeaAddHelperTest(unittest.TestCase):
    def test_add_idea_writes_body_to_raw_ideas(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo_root = Path(d)
            rel_path = add_idea(
                "Bone Currency",
                body="死者遗骨可铸成通行货币。",
                root=repo_root,
                now=FIXED_NOW,
            )

            self.assertEqual(rel_path, Path("foundation/raw_ideas/2026-05-14-bone-currency.md"))
            output = repo_root / rel_path
            self.assertTrue(output.exists())
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "# Bone Currency\n\n"
                "时间：2026-05-14 03:04:05\n"
                "来源：ginga idea add\n\n"
                "死者遗骨可铸成通行货币。\n",
            )

    def test_add_idea_accepts_stdin_body(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo_root = Path(d)
            rel_path = add_idea(
                "night market",
                stdin_text="第一行\n第二行\n",
                root=repo_root,
                now=FIXED_NOW,
            )

            content = (repo_root / rel_path).read_text(encoding="utf-8")
            self.assertTrue(content.endswith("第一行\n第二行\n"))

    def test_duplicate_title_gets_numeric_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo_root = Path(d)
            first = add_idea("Bone Currency", root=repo_root, now=FIXED_NOW)
            second = add_idea("Bone Currency", root=repo_root, now=FIXED_NOW)
            third = add_idea("Bone Currency", root=repo_root, now=FIXED_NOW)

            self.assertEqual(first.name, "2026-05-14-bone-currency.md")
            self.assertEqual(second.name, "2026-05-14-bone-currency-2.md")
            self.assertEqual(third.name, "2026-05-14-bone-currency-3.md")

    def test_chinese_title_falls_back_to_time_slug(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            rel_path = add_idea("骨币经济", root=Path(d), now=FIXED_NOW)

            self.assertEqual(rel_path.name, "2026-05-14-idea-030405.md")

    def test_does_not_create_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            repo_root = Path(d)
            add_idea("Bone Currency", root=repo_root, now=FIXED_NOW)

            self.assertFalse((repo_root / "foundation/runtime_state").exists())


class IdeaCliParserTest(unittest.TestCase):
    def test_idea_add_dispatch_prints_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            with patch("ginga_platform.orchestrator.cli.__main__.Path.cwd", return_value=Path(d)):
                with patch("ginga_platform.orchestrator.cli.idea._current_time", return_value=FIXED_NOW):
                    with redirect_stdout(out):
                        code = main(["idea", "add", "Bone Currency", "--body", "bones"])

            self.assertEqual(code, 0)
            self.assertEqual(out.getvalue().strip(), "foundation/raw_ideas/2026-05-14-bone-currency.md")

    def test_idea_add_help_does_not_crash(self) -> None:
        parser = build_parser()
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                parser.parse_args(["add", "--help"])

        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
