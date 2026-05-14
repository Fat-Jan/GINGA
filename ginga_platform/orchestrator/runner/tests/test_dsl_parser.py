"""Unit tests for platform.orchestrator.runner.dsl_parser.

由于项目顶层包名 ``platform`` 与 stdlib ``platform`` 模块冲突 (技术债，记录上报)，
测试用 ``importlib.util.spec_from_file_location`` 直接按路径加载模块，
不走 ``import platform.orchestrator.*``.
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
import tempfile
import unittest
from pathlib import Path


def _load_module(name: str, fp: Path):
    spec = importlib.util.spec_from_file_location(name, fp)
    assert spec and spec.loader, f"failed to load spec for {fp}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_REPO_ROOT = Path(__file__).resolve().parents[4]
_DSL_PARSER_PATH = _REPO_ROOT / "ginga_platform" / "orchestrator" / "runner" / "dsl_parser.py"


class DslParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module("_dsl_parser_under_test", _DSL_PARSER_PATH)

    def test_parse_minimal_workflow(self) -> None:
        Workflow = self.mod.Workflow
        Step = self.mod.Step
        raw = {
            "name": "minimal",
            "version": "1.0",
            "steps": [
                {"id": "A", "uses_capability": "base-template-story-dna"},
                {
                    "id": "B",
                    "uses_skill": "skill-router",
                    "preconditions": ["guard:no-fake-read"],
                    "postconditions": ["checker:aigc-style-detector"],
                    "state_reads": ["locked.*"],
                    "state_writes": ["entity_runtime.CHARACTER_STATE"],
                    "description": "chapter draft",
                },
            ],
        }
        wf = self.mod.parse_workflow_dict(raw)
        self.assertIsInstance(wf, Workflow)
        self.assertEqual(wf.name, "minimal")
        self.assertEqual(wf.step_ids, ["A", "B"])
        step_b = wf.find("B")
        self.assertIsNotNone(step_b)
        assert step_b is not None  # narrow for type checker
        self.assertIsInstance(step_b, Step)
        self.assertEqual(step_b.guard_ids(), ["no-fake-read"])
        self.assertEqual(step_b.checker_ids(), ["aigc-style-detector"])
        self.assertTrue(step_b.is_skill_step)
        self.assertFalse(step_b.is_capability_step)

    def test_parse_rejects_duplicate_step_id(self) -> None:
        raw = {
            "name": "dup",
            "steps": [{"id": "X"}, {"id": "X"}],
        }
        with self.assertRaises(self.mod.DSLParseError):
            self.mod.parse_workflow_dict(raw)

    def test_parse_rejects_capability_and_skill_together(self) -> None:
        raw = {
            "name": "x",
            "steps": [{"id": "A", "uses_capability": "foo", "uses_skill": "bar"}],
        }
        with self.assertRaises(self.mod.DSLParseError):
            self.mod.parse_workflow_dict(raw)

    def test_parse_from_yaml_file(self) -> None:
        yaml_text = textwrap.dedent(
            """\
            name: novel_pipeline_mvp_stub
            version: "1.0"
            steps:
              - id: A_brainstorm
                uses_capability: base-methodology-creative-brainstorm
                preconditions: [guard:no-fake-read]
              - id: G_chapter_draft
                uses_skill: skill-router
                state_reads: [locked.*, entity_runtime.*]
                state_writes: [chapter_text]
                postconditions: [checker:character-iq-checker]
            """
        )
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(yaml_text)
            path = Path(f.name)
        try:
            wf = self.mod.parse_workflow(path)
            self.assertEqual(wf.step_ids, ["A_brainstorm", "G_chapter_draft"])
            self.assertEqual(wf.find("G_chapter_draft").guard_ids(), [])  # type: ignore[union-attr]
            self.assertEqual(wf.find("G_chapter_draft").checker_ids(), ["character-iq-checker"])  # type: ignore[union-attr]
        finally:
            path.unlink(missing_ok=True)

    def test_parse_missing_name_raises(self) -> None:
        with self.assertRaises(self.mod.DSLParseError):
            self.mod.parse_workflow_dict({"steps": []})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
