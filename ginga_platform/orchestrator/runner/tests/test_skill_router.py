"""Unit tests for platform.orchestrator.router.skill_router.

覆盖：
    - registry + contract.yaml priority 段加载
    - ``topic in [玄幻黑暗, 暗黑奇幻]`` 匹配走 dark-fantasy
    - 无 topic / 不匹配 → fallback to ``default_writer``
    - 多 skill 同时启用 → 最高 score 胜出
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
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
_ROUTER_PATH = _REPO_ROOT / "ginga_platform" / "orchestrator" / "router" / "skill_router.py"
_STATE_IO_PATH = _REPO_ROOT / "ginga_platform" / "orchestrator" / "runner" / "state_io.py"


class _StubStep:
    """skill_router 不实际使用 Step 的字段，给个占位就够."""

    def __init__(self, sid: str) -> None:
        self.id = sid


class SkillRouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.router_mod = _load_module("_skill_router_under_test", _ROUTER_PATH)
        cls.state_mod = _load_module("_state_io_under_test_router", _STATE_IO_PATH)

    def _setup_fake_skills(self, tmpdir: Path) -> tuple[Path, Path]:
        skills_root = tmpdir / "skills"
        # 两个 skill：dark-fantasy 强绑定玄幻黑暗 + planning-with-files cross-cutting.
        for sid, contract_text in [
            (
                "dark-fantasy-ultimate-engine",
                textwrap.dedent(
                    """\
                    skill_id: dark-fantasy-ultimate-engine
                    priority:
                      - when: topic in [玄幻黑暗, 暗黑奇幻]
                        score: 100
                      - when: topic in [其他玄幻]
                        score: 30
                      - default: 0
                    """
                ),
            ),
            (
                "planning-with-files",
                textwrap.dedent(
                    """\
                    skill_id: planning-with-files
                    priority:
                      - default: 10
                    """
                ),
            ),
        ]:
            sdir = skills_root / sid
            sdir.mkdir(parents=True)
            (sdir / "contract.yaml").write_text(contract_text, encoding="utf-8")
        registry = skills_root / "registry.yaml"
        registry.write_text(
            textwrap.dedent(
                """\
                skills:
                  - skill_id: dark-fantasy-ultimate-engine
                    enabled: true
                  - skill_id: planning-with-files
                    enabled: true
                """
            ),
            encoding="utf-8",
        )
        return registry, skills_root

    def _make_state_io(self, root: Path, topic_val):
        sio = self.state_mod.StateIO("router-book", state_root=root)
        if topic_val is not None:
            sio.apply({"locked.GENRE_LOCKED.topic": topic_val}, source="test")
        return sio

    def test_route_dark_fantasy_when_topic_matches(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            registry, skills_root = self._setup_fake_skills(Path(d))
            sio = self._make_state_io(Path(d) / "state", ["玄幻黑暗"])
            router = self.router_mod.SkillRouter(
                registry_path=registry, skills_root=skills_root
            )
            decision = router.route(_StubStep("G"), {"state_io": sio})
            self.assertEqual(decision.skill_id, "dark-fantasy-ultimate-engine")
            self.assertEqual(decision.score, 100)

    def test_route_falls_back_to_default_writer_when_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            registry, skills_root = self._setup_fake_skills(Path(d))
            sio = self._make_state_io(Path(d) / "state", ["都市言情"])
            router = self.router_mod.SkillRouter(
                registry_path=registry, skills_root=skills_root
            )
            decision = router.route(_StubStep("G"), {"state_io": sio})
            # planning-with-files default=10 应胜出 (>0)，dark-fantasy=0 不参与.
            # 因为 default > 0 视为有效候选，winner 应为 planning-with-files.
            self.assertEqual(decision.skill_id, "planning-with-files")
            self.assertEqual(decision.score, 10)

    def test_route_uses_fallback_when_registry_missing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            sio = self._make_state_io(Path(d) / "state", None)
            router = self.router_mod.SkillRouter(
                registry_path=Path(d) / "nope.yaml",
                skills_root=Path(d) / "skills",
            )
            decision = router.route(_StubStep("G"), {"state_io": sio})
            self.assertEqual(decision.skill_id, "default_writer")
            self.assertEqual(decision.score, 0)

    def test_router_callable_returns_skill_id(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            registry, skills_root = self._setup_fake_skills(Path(d))
            sio = self._make_state_io(Path(d) / "state", ["暗黑奇幻"])
            router = self.router_mod.SkillRouter(
                registry_path=registry, skills_root=skills_root
            )
            chosen = router(_StubStep("G"), {"state_io": sio})
            self.assertEqual(chosen, "dark-fantasy-ultimate-engine")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
