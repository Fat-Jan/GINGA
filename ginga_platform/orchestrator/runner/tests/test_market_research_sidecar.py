"""v1.6 Market Research Sidecar contract tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class MarketResearchSidecarContractTest(unittest.TestCase):
    def _fixture_path(self, root: Path) -> Path:
        fixture = {
            "fixture_id": "offline-cn-webnovel-sample",
            "collected_at": "2026-05-15T12:00:00Z",
            "sources": [
                {
                    "source_id": "榜单A",
                    "platform": "示例平台",
                    "url": "https://example.invalid/rank",
                    "collected_at": "2026-05-15T12:00:00Z",
                    "data_quality": "offline_fixture",
                    "items": [
                        {
                            "rank": 1,
                            "title": "黑暗微粒纪元",
                            "genre": "玄幻黑暗",
                            "signals": ["高收藏", "强冲突", "世界观压迫"],
                            "summary": "主角在天堑边缘争夺微粒资源。",
                            "raw_text": "EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK",
                        },
                        {
                            "rank": 2,
                            "title": "长夜血契",
                            "genre": "玄幻黑暗",
                            "signals": ["复仇", "血脉代价"],
                            "summary": "以代价换力量的复仇线。",
                        },
                    ],
                }
            ],
        }
        path = root / "fixtures" / "market.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_market_report_requires_explicit_authorization(self) -> None:
        from ginga_platform.orchestrator.market_research import MarketResearchError, export_market_research_report

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = self._fixture_path(root)

            with self.assertRaisesRegex(MarketResearchError, "authorization"):
                export_market_research_report(
                    "market-book",
                    run_id="run-001",
                    fixture_path=fixture,
                    output_root=root / ".ops" / "market_research",
                    authorized=False,
                )

    def test_market_report_writes_offline_sidecar_without_raw_text_or_state_writes(self) -> None:
        from ginga_platform.orchestrator.market_research import export_market_research_report

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = self._fixture_path(root)
            output_root = root / ".ops" / "market_research"

            result = export_market_research_report(
                "market-book",
                run_id="run-001",
                fixture_path=fixture,
                output_root=output_root,
                authorized=True,
            )

            out_dir = output_root / "market-book" / "run-001"
            report_path = out_dir / "market_report.json"
            self.assertEqual(Path(result["output_dir"]), out_dir)
            self.assertTrue(report_path.exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertFalse((root / "foundation" / "runtime_state").exists())

            report_text = report_path.read_text(encoding="utf-8")
            readme_text = (out_dir / "README.md").read_text(encoding="utf-8")
            self.assertNotIn("EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK", report_text)
            self.assertNotIn("EXTERNAL_RAW_SENTINEL_SHOULD_NOT_LEAK", readme_text)
            report = json.loads(report_text)
            self.assertEqual(report["kind"], "MarketResearchSidecarReport")
            self.assertEqual(report["collection_mode"], "offline_fixture")
            self.assertTrue(report["authorization"]["explicit"])
            self.assertEqual(report["projection"]["output_boundary"], ".ops/market_research/<book_id>/<run_id>/")
            self.assertFalse(report["projection"]["writes_runtime_state"])
            self.assertFalse(report["rag_policy"]["default_rag_eligible"])
            self.assertIn(".ops/market_research/**", report["rag_policy"]["forbidden_default_sources"])
            self.assertEqual(report["sources"][0]["collected_at"], "2026-05-15T12:00:00Z")
            self.assertEqual(report["sources"][0]["data_quality"], "offline_fixture")
            self.assertGreaterEqual(len(report["market_signals"]), 2)

    def test_market_cli_fixture_export(self) -> None:
        from ginga_platform.orchestrator.cli.__main__ import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = self._fixture_path(root)
            output_root = root / ".ops" / "market_research"

            code = main(
                [
                    "market",
                    "market-book",
                    "--run-id",
                    "cli-run",
                    "--fixture",
                    str(fixture),
                    "--authorize",
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(code, 0)
            self.assertTrue((output_root / "market-book" / "cli-run" / "market_report.json").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
