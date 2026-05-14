"""ST-S2-S-MULTI-CHAPTER S-2：locked 域 patch CLI 测试.

覆盖：
    - apply_patch_to_book 写 patch yaml + 改 state + 写 audit + applied.yaml + R3 stub
    - field 越权（非 locked.*）拒绝
    - reason / new_value 必填
    - dry_run 只写 yaml 不动 state
    - approve 流程（cli_main）

cli_main 用 subprocess 隔离 + state_root override 避免污染真仓库 state.
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from ginga_platform.orchestrator.cli.locked_patch import (
    LockedPatchError,
    _gen_patch_id,
    _parse_new_value,
    _validate_field_in_locked,
    apply_patch_to_book,
    cli_main,
)
from ginga_platform.orchestrator.runner.state_io import StateIO


class ValidateFieldTest(unittest.TestCase):
    def test_valid_locked_path_accepted(self) -> None:
        _validate_field_in_locked("locked.WORLD.factions")
        _validate_field_in_locked("locked.STORY_DNA.premise")

    def test_non_locked_path_rejected(self) -> None:
        with self.assertRaises(LockedPatchError):
            _validate_field_in_locked("entity_runtime.CHARACTER_STATE.protagonist.events")
        with self.assertRaises(LockedPatchError):
            _validate_field_in_locked("workspace.task_plan")

    def test_bare_locked_rejected(self) -> None:
        with self.assertRaises(LockedPatchError):
            _validate_field_in_locked("locked")

    def test_empty_path_rejected(self) -> None:
        with self.assertRaises(LockedPatchError):
            _validate_field_in_locked("")


class ParseNewValueTest(unittest.TestCase):
    def test_json_parsed(self) -> None:
        self.assertEqual(_parse_new_value('{"a":1}'), {"a": 1})
        self.assertEqual(_parse_new_value('[1,2,3]'), [1, 2, 3])
        self.assertEqual(_parse_new_value('"hello"'), "hello")

    def test_yaml_fallback(self) -> None:
        self.assertEqual(_parse_new_value("a: 1\nb: 2"), {"a": 1, "b": 2})

    def test_empty_rejected(self) -> None:
        with self.assertRaises(LockedPatchError):
            _parse_new_value("")
        with self.assertRaises(LockedPatchError):
            _parse_new_value("   ")


class GenPatchIdTest(unittest.TestCase):
    def test_format(self) -> None:
        pid = _gen_patch_id("Add Faction Shadow")
        self.assertTrue(pid.startswith("P-"))
        # P-<6 hex>-<sanitized-tag>
        parts = pid.split("-", 2)
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "P")
        self.assertEqual(len(parts[1]), 6)  # 3 bytes hex
        self.assertIn("add", parts[2])

    def test_unique(self) -> None:
        ids = {_gen_patch_id("x") for _ in range(20)}
        self.assertEqual(len(ids), 20, "patch ids should be unique")


class ApplyPatchToBookTest(unittest.TestCase):
    """S-2 主测：apply_patch_to_book 写盘 + 改 state + audit + R3 stub."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._state_root = Path(self._tmp.name) / "state"
        self._patches_root = Path(self._tmp.name) / "patches"
        self.book_id = "patch-book"
        # seed minimum locked 域
        sio = StateIO(self.book_id, state_root=self._state_root)
        sio.apply(
            {
                "locked.STORY_DNA.premise": "原始 premise",
                "locked.WORLD.factions": [{"id": "F-old", "name": "旧势力"}],
            },
            source="test.seed",
        )

    def test_apply_writes_patch_yaml_and_state(self) -> None:
        new_value = [{"id": "F-001", "name": "血雾教廷", "alignment": "hostile"}]
        result = apply_patch_to_book(
            self.book_id,
            field="locked.WORLD.factions",
            reason="第 25 章扩出血雾教廷",
            new_value=new_value,
            affected_chapters="25-40",
            approval_required=False,
            author="test",
            short_tag="add-blood-mist",
            state_root=self._state_root,
            patches_root=self._patches_root,
        )
        # 返回结构
        self.assertTrue(result["applied"])
        self.assertTrue(result["patch_id"].startswith("P-"))
        # patch yaml 落盘
        patch_path = Path(result["patch_path"])
        self.assertTrue(patch_path.exists(), f"patch yaml missing: {patch_path}")
        doc = yaml.safe_load(patch_path.read_text(encoding="utf-8"))
        self.assertEqual(doc["scope"], ["locked.WORLD.factions"])
        self.assertEqual(doc["affected_chapters"], "25-40")
        self.assertIn("血雾教廷", json.dumps(doc["new_value"], ensure_ascii=False))
        # applied.yaml 落盘
        self.assertTrue(Path(result["applied_path"]).exists())

        # state 已更新
        sio = StateIO(self.book_id, state_root=self._state_root)
        factions = sio.read("locked.WORLD.factions")
        self.assertEqual(factions[0]["id"], "F-001")
        self.assertEqual(factions[0]["name"], "血雾教廷")

        # audit_log 含 patch 记录 + R3 stub
        audits = sio.audit_log
        sources = [e["source"] for e in audits]
        self.assertIn("cli.locked_patch", sources)
        self.assertIn("cli.locked_patch.r3_consistency_checker", sources)

    def test_apply_rejects_non_locked_field(self) -> None:
        with self.assertRaises(LockedPatchError):
            apply_patch_to_book(
                self.book_id,
                field="entity_runtime.CHARACTER_STATE",
                reason="不该走 patch",
                new_value={"x": 1},
                state_root=self._state_root,
                patches_root=self._patches_root,
            )

    def test_apply_rejects_empty_reason(self) -> None:
        with self.assertRaises(LockedPatchError):
            apply_patch_to_book(
                self.book_id,
                field="locked.WORLD.factions",
                reason="",
                new_value=[],
                state_root=self._state_root,
                patches_root=self._patches_root,
            )

    def test_dry_run_does_not_modify_state(self) -> None:
        original = StateIO(self.book_id, state_root=self._state_root).read("locked.WORLD.factions")
        result = apply_patch_to_book(
            self.book_id,
            field="locked.WORLD.factions",
            reason="dry run test",
            new_value=[{"id": "F-DRY"}],
            state_root=self._state_root,
            patches_root=self._patches_root,
            dry_run=True,
        )
        self.assertFalse(result["applied"])
        # state 未变
        after = StateIO(self.book_id, state_root=self._state_root).read("locked.WORLD.factions")
        self.assertEqual(after, original)
        # patch yaml 仍写盘（记录意图）
        self.assertTrue(Path(result["patch_path"]).exists())
        # applied.yaml 不应存在
        self.assertNotIn("applied_path", result)


class TemplateExistsTest(unittest.TestCase):
    """S-2 验收：meta/patches/_template.patch.yaml 必须存在且字段齐."""

    def test_template_file_exists_and_has_required_fields(self) -> None:
        # 计算项目根的 meta/patches/_template.patch.yaml 绝对路径
        # 测试是从 cwd=ginga repo 跑的，相对路径 ok
        path = Path("meta/patches/_template.patch.yaml")
        # 兜底：若 cwd 不是 ginga 根，按本文件位置回溯
        if not path.exists():
            here = Path(__file__).resolve()
            # ginga_platform/orchestrator/runner/tests/test_locked_patch.py -> repo
            repo = here.parents[4]
            path = repo / "meta" / "patches" / "_template.patch.yaml"
        self.assertTrue(path.exists(), f"template missing: {path}")
        raw = path.read_text(encoding="utf-8")
        for key in ("patch_id", "ts", "scope", "reason", "affected_chapters", "approval_required", "new_value", "post_apply"):
            self.assertIn(key, raw, f"template missing field {key!r}")


class CliMainTest(unittest.TestCase):
    """cli_main 入口：approve flag / dry-run / 错误退码."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._state_root = Path(self._tmp.name) / "state"
        self._patches_root = Path(self._tmp.name) / "patches"
        self.book_id = "cli-book"
        sio = StateIO(self.book_id, state_root=self._state_root)
        sio.apply({"locked.STORY_DNA.premise": "seed"}, source="test.seed")

        # patch _default_state_root 让 cli_main 内部 StateIO(...) 走 tmp
        # （改成 lazy lookup 后 mock 模块级函数才生效，避免 Python 默认参数绑定陷阱）
        self._patch_state_root = patch(
            "ginga_platform.orchestrator.runner.state_io._default_state_root",
            return_value=self._state_root,
        )
        self._patch_state_root.start()
        self.addCleanup(self._patch_state_root.stop)

    def test_cli_requires_approve_when_approval_required_true(self) -> None:
        argv = [
            self.book_id,
            "--field", "locked.STORY_DNA.premise",
            "--reason", "更新 premise",
            "--new-value", '"新 premise 内容"',
            "--patches-root", str(self._patches_root),
            "--approval-required", "true",
        ]
        buf_err = io.StringIO()
        with redirect_stderr(buf_err):
            rc = cli_main(argv)
        self.assertEqual(rc, 3)
        self.assertIn("approval_required", buf_err.getvalue())

    def test_cli_applies_with_approve_flag(self) -> None:
        argv = [
            self.book_id,
            "--field", "locked.STORY_DNA.premise",
            "--reason", "更新 premise",
            "--new-value", '"新 premise 内容"',
            "--patches-root", str(self._patches_root),
            "--approval-required", "true",
            "--approve",
        ]
        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            rc = cli_main(argv)
        self.assertEqual(rc, 0)
        self.assertIn("applied=True", buf_out.getvalue())
        # state 已更新
        sio = StateIO(self.book_id, state_root=self._state_root)
        self.assertEqual(sio.read("locked.STORY_DNA.premise"), "新 premise 内容")

    def test_cli_dry_run_no_approve_needed(self) -> None:
        argv = [
            self.book_id,
            "--field", "locked.STORY_DNA.premise",
            "--reason", "更新 premise",
            "--new-value", '"dry only"',
            "--patches-root", str(self._patches_root),
            "--approval-required", "true",
            "--dry-run",
        ]
        rc = cli_main(argv)
        self.assertEqual(rc, 0)
        # state 未变
        sio = StateIO(self.book_id, state_root=self._state_root)
        self.assertEqual(sio.read("locked.STORY_DNA.premise"), "seed")

    def test_cli_rejects_invalid_field(self) -> None:
        argv = [
            self.book_id,
            "--field", "entity_runtime.X",
            "--reason", "越权",
            "--new-value", '"foo"',
            "--patches-root", str(self._patches_root),
            "--approval-required", "false",
        ]
        buf_err = io.StringIO()
        with redirect_stderr(buf_err):
            rc = cli_main(argv)
        self.assertEqual(rc, 4)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
