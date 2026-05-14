"""Unit tests for platform.orchestrator.runner.state_io.

测试覆盖：
    - read/apply/transaction/audit_log 四要素
    - rollback 恢复 snapshot
    - audit_log 不允许通过 apply 改 (jury-1 P0 强约束体现)
    - atomic write + reload 一致
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module(name: str, fp: Path):
    spec = importlib.util.spec_from_file_location(name, fp)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_REPO_ROOT = Path(__file__).resolve().parents[4]
_STATE_IO_PATH = _REPO_ROOT / "ginga_platform" / "orchestrator" / "runner" / "state_io.py"


class StateIOTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module("_state_io_under_test", _STATE_IO_PATH)

    def _new(self, root: Path):
        return self.mod.StateIO("demo-book", state_root=root)

    def test_apply_and_read_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            sio.apply(
                {
                    "locked.STORY_DNA.premise": "失忆刺客",
                    "entity_runtime.RESOURCE_LEDGER.particles": 42,
                },
                source="unit",
            )
            self.assertEqual(sio.read("locked.STORY_DNA.premise"), "失忆刺客")
            self.assertEqual(sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 42)
            self.assertEqual(sio.read("locked.MISSING", default="X"), "X")
            self.assertGreaterEqual(len(sio.audit_log), 1)

    def test_transaction_commit_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            with sio.transaction() as tx:
                tx.apply({"entity_runtime.RESOURCE_LEDGER.particles": 10})
            self.assertEqual(sio.read("entity_runtime.RESOURCE_LEDGER.particles"), 10)
            try:
                with sio.transaction() as tx:
                    tx.apply({"entity_runtime.RESOURCE_LEDGER.particles": 999})
                    raise RuntimeError("boom")
            except RuntimeError:
                pass
            self.assertEqual(
                sio.read("entity_runtime.RESOURCE_LEDGER.particles"),
                10,
                "rollback must restore prior value",
            )

    def test_audit_log_is_append_only_via_apply(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            with self.assertRaises(self.mod.StateIOError):
                sio.apply({"audit_log.entries": []})

    def test_disk_reload(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            sio.apply({"locked.STORY_DNA.premise": "v1"})
            sio.audit("checker:x", severity="warn", msg="trial")
            # new instance, same path → 必须读到同样真值.
            sio2 = self.mod.StateIO("demo-book", state_root=Path(d))
            self.assertEqual(sio2.read("locked.STORY_DNA.premise"), "v1")
            self.assertTrue(any(e.get("source") == "checker:x" for e in sio2.audit_log))

    def test_unknown_domain_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            with self.assertRaises(self.mod.StateIOError):
                sio.apply({"forbidden.something": 1})

    def test_write_artifact_marks_chapter_boundary_without_yaml_domain_write(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            path = sio.write_artifact(
                "chapter_01.md",
                "# 第一章\n\nmock",
                source="unit.artifact",
                artifact_type="chapter_text",
                payload={"execution_mode": "mock_harness"},
            )
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "chapter_01.md")
            self.assertTrue(
                any(
                    entry.get("payload", {}).get("artifact_type") == "chapter_text"
                    and entry.get("payload", {}).get("execution_mode") == "mock_harness"
                    for entry in sio.audit_log
                )
            )

    def test_write_artifact_rejects_yaml_state_domain_shortcut(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._new(Path(d))
            with self.assertRaises(self.mod.StateIOError):
                sio.write_artifact(
                    "locked.yaml",
                    "STORY_DNA: {}",
                    source="unit.bad",
                    artifact_type="state_domain",
                )
            with self.assertRaises(self.mod.StateIOError):
                sio.write_artifact(
                    "../escape.md",
                    "bad",
                    source="unit.bad",
                    artifact_type="chapter_text",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
