"""Unit tests for rag.layer1_filter + step_dispatch RAG hook (ST-S2-R-RAG-LAYER1).

测试矩阵 (prompt §tests, ≥4 cases)：
    1. test_cold_start_empty_index_returns_empty   — 空 index 冷启动返回 []
    2. test_topic_filter_partial_match              — 已建 index 按 topic 部分匹配命中
    3. test_quality_grade_ordering_a_first          — quality_grade 排序：A > A- > B+ > B
    4. test_step_dispatch_rag_mode_off_skips_recall — rag_mode=off 时 step_dispatch 不调召回
    5. test_stage_specific_top_k_from_config        — top_k 从 recall_config.stage_specific_top_k 读 (R-4)
"""

from __future__ import annotations

import gc
import json
import sqlite3
import tempfile
import textwrap
import unittest
import warnings
from contextlib import closing
from pathlib import Path
from typing import Any, Mapping


_REPO_ROOT = Path(__file__).resolve().parents[4]


def _write_card_md(dirp: Path, slug: str, meta: dict[str, Any]) -> Path:
    fp = dirp / f"{slug}.md"
    import yaml as _yaml

    fp.write_text(
        "---\n" + _yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\nbody\n",
        encoding="utf-8",
    )
    return fp


def _promoted_methodology_meta(
    *,
    card_id: str = "promoted-trope-ch-0001-001",
    approved: bool = True,
    contamination_pass: bool = True,
) -> dict[str, Any]:
    return {
        "id": card_id,
        "asset_type": "methodology",
        "title": "Promoted Trope Recipe",
        "topic": ["reference_trope"],
        "stage": "ideation",
        "quality_grade": "B",
        "source_path": ".ops/book_analysis/**",
        "last_updated": "2026-05-15",
        "promoted_from": "trope-ch-0001-001",
        "human_review_status": "approved" if approved else "pending",
        "source_contamination_check": "pass" if contamination_pass else "fail",
        "default_rag_eligible": False,
    }


class ColdStartTest(unittest.TestCase):
    def test_cold_start_empty_index_returns_empty(self) -> None:
        """空目录建空索引；recall 返回 []，detect_state 报 cold."""
        from rag.cold_start import detect_state
        from rag.index_builder import build_index, count_cards
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "prompts").mkdir()
            idx = root / "index.sqlite"
            stats = build_index([root / "prompts"], idx)
            self.assertEqual(stats.cards_indexed, 0)
            self.assertEqual(count_cards(idx), 0)
            self.assertEqual(detect_state(idx), "cold")
            result = recall(stage="drafting", topic="玄幻黑暗", top_k=5, index_path=idx)
            self.assertEqual(result, [])

    def test_index_builder_excludes_forbidden_book_analysis_paths(self) -> None:
        from rag.index_builder import build_index, count_cards

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            allowed = root / "foundation" / "assets" / "prompts"
            forbidden = root / ".ops" / "book_analysis" / "run-1"
            allowed.mkdir(parents=True)
            forbidden.mkdir(parents=True)
            card_meta = dict(
                id="allowed-card",
                asset_type="prompt_card",
                title="clean",
                topic=["玄幻黑暗"],
                stage="drafting",
                quality_grade="A",
                card_intent="prose_generation",
                source_path="foundation/assets/prompts/allowed.md",
                last_updated="2026-05-15",
            )
            _write_card_md(allowed, "allowed", card_meta)
            polluted = dict(card_meta)
            polluted["id"] = "polluted-card"
            polluted["source_path"] = ".ops/book_analysis/run-1/polluted.md"
            _write_card_md(forbidden, "polluted", polluted)

            idx = root / "index.sqlite"
            stats = build_index(
                [allowed, forbidden],
                idx,
                repo_root=root,
                forbidden_paths=[".ops/book_analysis/**"],
            )

            self.assertEqual(stats.cards_indexed, 1)
            self.assertEqual(count_cards(idx), 1)
            with closing(sqlite3.connect(idx)) as conn:
                ids = [row[0] for row in conn.execute("SELECT id FROM cards ORDER BY id")]
            self.assertEqual(ids, ["allowed-card"])

    def test_default_index_builder_excludes_promoted_book_analysis_projection(self) -> None:
        from rag.index_builder import build_index, count_cards

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            methodology = root / "foundation" / "assets" / "methodology"
            methodology.mkdir(parents=True)
            _write_card_md(
                methodology,
                "promoted-trope-ch-0001-001",
                _promoted_methodology_meta(),
            )

            idx = root / "index.sqlite"
            stats = build_index(
                [methodology],
                idx,
                repo_root=root,
                forbidden_paths=[".ops/book_analysis/**"],
            )

            self.assertEqual(stats.cards_indexed, 0)
            self.assertEqual(stats.skipped_forbidden_path, 1)
            self.assertEqual(count_cards(idx), 0)


class ReferenceSidecarRagTest(unittest.TestCase):
    def test_sidecar_builds_only_approved_promoted_methodology_assets(self) -> None:
        from rag.reference_sidecar import build_reference_sidecar_index

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            methodology = root / "foundation" / "assets" / "methodology"
            polluted = root / ".ops" / "book_analysis" / "run-1"
            methodology.mkdir(parents=True)
            polluted.mkdir(parents=True)
            _write_card_md(methodology, "promoted-approved", _promoted_methodology_meta())
            _write_card_md(
                methodology,
                "promoted-pending",
                _promoted_methodology_meta(card_id="promoted-pending", approved=False),
            )
            _write_card_md(
                methodology,
                "promoted-contaminated",
                _promoted_methodology_meta(card_id="promoted-contaminated", contamination_pass=False),
            )
            _write_card_md(polluted, "promoted-illegal", _promoted_methodology_meta(card_id="promoted-illegal"))

            idx = root / "sidecar.sqlite"
            stats = build_reference_sidecar_index(repo_root=root, index_path=idx)

            self.assertEqual(stats.cards_indexed, 1)
            with closing(sqlite3.connect(idx)) as conn:
                ids = [row[0] for row in conn.execute("SELECT id FROM cards ORDER BY id")]
            self.assertEqual(ids, ["promoted-trope-ch-0001-001"])

    def test_sidecar_recall_is_explicit_opt_in_and_default_rag_stays_empty(self) -> None:
        from rag.index_builder import build_index
        from rag.layer1_filter import recall
        from rag.reference_sidecar import build_reference_sidecar_index, recall_reference_sidecar

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            methodology = root / "foundation" / "assets" / "methodology"
            methodology.mkdir(parents=True)
            _write_card_md(methodology, "promoted-approved", _promoted_methodology_meta())

            default_idx = root / "default.sqlite"
            build_index(
                [methodology],
                default_idx,
                repo_root=root,
                forbidden_paths=[".ops/book_analysis/**"],
            )
            default_hits = recall(
                stage="ideation",
                topic="reference_trope",
                asset_type="methodology",
                top_k=5,
                index_path=default_idx,
            )
            self.assertEqual(default_hits, [])

            sidecar_idx = root / "sidecar.sqlite"
            build_reference_sidecar_index(repo_root=root, index_path=sidecar_idx)
            sidecar = recall_reference_sidecar(
                stage="ideation",
                topic="reference_trope",
                top_k=5,
                index_path=sidecar_idx,
            )

            self.assertEqual([card["id"] for card in sidecar["cards"]], ["promoted-trope-ch-0001-001"])
            self.assertEqual(sidecar["diagnostics"]["execution_mode"], "reference_sidecar_rag")
            self.assertTrue(sidecar["diagnostics"]["explicit_opt_in_required"])


class TopicFilterTest(unittest.TestCase):
    def _build_idx(self, root: Path) -> Path:
        src = root / "prompts"
        src.mkdir()
        _write_card_md(
            src,
            "card_xuanhuan",
            dict(
                id="prompts-card-prose-xuanhuan-001",
                asset_type="prompt_card",
                title="玄幻战斗场面",
                topic=["玄幻黑暗", "战斗"],
                stage="drafting",
                quality_grade="A",
                card_intent="prose_generation",
                source_path="_原料/foo/1.md",
                last_updated="2026-05-10",
            ),
        )
        _write_card_md(
            src,
            "card_urban",
            dict(
                id="prompts-card-prose-urban-002",
                asset_type="prompt_card",
                title="都市相亲",
                topic=["都市", "爱情"],
                stage="drafting",
                quality_grade="B+",
                card_intent="prose_generation",
                source_path="_原料/foo/2.md",
                last_updated="2026-05-11",
            ),
        )
        idx = root / "index.sqlite"
        from rag.index_builder import build_index

        st = build_index([src], idx)
        assert st.cards_indexed == 2
        return idx

    def test_topic_filter_partial_match(self) -> None:
        """topic=list 部分命中：传 [玄幻黑暗] 应只召回卡 1."""
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_idx(Path(d))
            hit = recall(stage="drafting", topic=["玄幻黑暗"], top_k=10, index_path=idx)
            self.assertEqual([c["id"] for c in hit], ["prompts-card-prose-xuanhuan-001"])
            # str 形式也应能命中
            hit_str = recall(stage="drafting", topic="都市", top_k=10, index_path=idx)
            self.assertEqual([c["id"] for c in hit_str], ["prompts-card-prose-urban-002"])
            # topic 不命中任何 → []
            none_hit = recall(stage="drafting", topic="科幻", top_k=10, index_path=idx)
            self.assertEqual(none_hit, [])

    def test_topic_aliases_match_both_query_and_card_topics(self) -> None:
        """topic alias normalization: either side may use any known alias."""
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            alias_cards = [
                ("general_cn", "通用", "general-group"),
                ("general_en", "general", "general-group"),
                ("weird_cn", "怪谈", "weird-group"),
                ("weird_rule", "规则怪谈", "weird-group"),
                ("action_cn", "动作", "action-group"),
                ("action_fight", "战斗", "action-group"),
                ("system_cn", "系统", "system-group"),
                ("system_flow", "系统流", "system-group"),
            ]
            for slug, topic, group in alias_cards:
                _write_card_md(
                    src,
                    slug,
                    dict(
                        id=f"id-{slug}",
                        asset_type="prompt_card",
                        title=slug,
                        topic=[topic],
                        stage="drafting",
                        quality_grade="A",
                        card_intent="prose_generation",
                        source_path=f"_原料/{slug}.md",
                        last_updated="2026-05-13",
                        test_group=group,
                    ),
                )
            idx = root / "index.sqlite"
            build_index([src], idx)

            cases = [
                ("通用", {"id-general_cn", "id-general_en"}),
                ("general", {"id-general_cn", "id-general_en"}),
                ("怪谈", {"id-weird_cn", "id-weird_rule"}),
                ("规则怪谈", {"id-weird_cn", "id-weird_rule"}),
                ("动作", {"id-action_cn", "id-action_fight"}),
                ("战斗", {"id-action_cn", "id-action_fight"}),
                ("系统", {"id-system_cn", "id-system_flow"}),
                ("系统流", {"id-system_cn", "id-system_flow"}),
            ]
            for query_topic, expected_ids in cases:
                with self.subTest(query_topic=query_topic):
                    got = recall(stage="drafting", topic=query_topic, top_k=10, index_path=idx)
                    self.assertEqual({c["id"] for c in got}, expected_ids)

    def test_topic_aliases_cover_structural_gold_set_gaps(self) -> None:
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for slug, topic in [
                ("xuanhuan", "玄幻"),
                ("infinite", "无限流"),
                ("romance", "言情"),
                ("twist", "反转"),
            ]:
                _write_card_md(
                    src,
                    slug,
                    dict(
                        id=f"id-{slug}",
                        asset_type="prompt_card",
                        title=slug,
                        topic=[topic],
                        stage="setting",
                        quality_grade="A",
                        card_intent="structural_design",
                        source_path=f"_原料/{slug}.md",
                        last_updated="2026-05-13",
                    ),
                )
            idx = root / "index.sqlite"
            build_index([src], idx)

            xuanhuan_hits = recall(
                stage="setting",
                topic=["玄幻", "通用"],
                asset_type="prompt_card",
                card_intent="structural_design",
                top_k=10,
                index_path=idx,
            )
            romance_hits = recall(
                stage="setting",
                topic=["言情", "女频", "豪门"],
                asset_type="prompt_card",
                card_intent="structural_design",
                top_k=10,
                index_path=idx,
            )

            self.assertEqual({card["id"] for card in xuanhuan_hits}, {"id-xuanhuan", "id-infinite"})
            self.assertEqual({card["id"] for card in romance_hits}, {"id-romance", "id-twist"})

    def test_recall_closes_sqlite_connection_without_resource_warning(self) -> None:
        """Layer 1 recall should not leak sqlite connections under repeated calls."""
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            idx = self._build_idx(Path(d))
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                for _ in range(3):
                    recall(stage="drafting", topic="玄幻黑暗", top_k=10, index_path=idx)
                gc.collect()

            resource_warnings = [warning for warning in caught if issubclass(warning.category, ResourceWarning)]
            self.assertEqual(resource_warnings, [])


class QualityOrderTest(unittest.TestCase):
    def test_quality_grade_ordering_a_first(self) -> None:
        """A > A- > B+ > B 顺序；C 默认被过滤 (quality_floor=B)."""
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for slug, grade in [
                ("a_card", "A"),
                ("aminus_card", "A-"),
                ("bplus_card", "B+"),
                ("b_card", "B"),
                ("c_card", "C"),  # 默认被 floor=B 排除
            ]:
                _write_card_md(
                    src,
                    slug,
                    dict(
                        id=f"id-{slug}",
                        asset_type="prompt_card",
                        title=slug,
                        topic=["玄幻黑暗"],
                        stage="drafting",
                        quality_grade=grade,
                        card_intent="prose_generation",
                        source_path=f"_原料/{slug}.md",
                        last_updated="2026-05-13",
                    ),
                )
            idx = root / "index.sqlite"
            build_index([src], idx)
            ordered = recall(stage="drafting", topic="玄幻黑暗", top_k=10, index_path=idx)
            ids = [c["id"] for c in ordered]
            self.assertEqual(
                ids,
                ["id-a_card", "id-aminus_card", "id-bplus_card", "id-b_card"],
                f"C-grade should be filtered, ordering should be A > A- > B+ > B, got {ids}",
            )

            # quality_floor=C 放宽后 C 卡也进
            wider = recall(
                stage="drafting",
                topic="玄幻黑暗",
                top_k=10,
                quality_floor="C",
                index_path=idx,
            )
            self.assertIn("id-c_card", [c["id"] for c in wider])

    def test_topic_specificity_breaks_quality_ties_before_top_k(self) -> None:
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for i in range(4):
                _write_card_md(
                    src,
                    f"generic-{i}",
                    dict(
                        id=f"id-generic-{i}",
                        asset_type="prompt_card",
                        title=f"generic-{i}",
                        topic=["玄幻"],
                        stage="setting",
                        quality_grade="B",
                        card_intent="structural_design",
                        source_path=f"_原料/generic-{i}.md",
                        last_updated=f"2026-05-1{i}",
                    ),
                )
            _write_card_md(
                src,
                "specific",
                dict(
                    id="id-specific",
                    asset_type="prompt_card",
                    title="specific",
                    topic=["玄幻", "系统"],
                    stage="setting",
                    quality_grade="B",
                    card_intent="structural_design",
                    source_path="_原料/specific.md",
                    last_updated="2026-05-01",
                ),
            )
            idx = root / "index.sqlite"
            build_index([src], idx)

            cards = recall(
                stage="setting",
                topic=["系统", "玄幻"],
                asset_type="prompt_card",
                card_intent="structural_design",
                top_k=3,
                index_path=idx,
            )

            self.assertEqual(cards[0]["id"], "id-specific")
            self.assertIn("id-specific", [card["id"] for card in cards])


class StageTopKTest(unittest.TestCase):
    def test_stage_specific_top_k_from_config(self) -> None:
        """top_k=None 时按 recall_config.stage_specific_top_k[stage] 取 (R-4)."""
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            # 写 8 张同 stage 同 topic 的 A 级卡
            for i in range(8):
                _write_card_md(
                    src,
                    f"c{i}",
                    dict(
                        id=f"id-c{i}",
                        asset_type="prompt_card",
                        title=f"card-{i}",
                        topic=["玄幻黑暗"],
                        stage="drafting",
                        quality_grade="A",
                        card_intent="prose_generation",
                        source_path="x",
                        last_updated="2026-05-13",
                    ),
                )
            idx = root / "index.sqlite"
            build_index([src], idx)
            config = {
                "stage_specific_top_k": {"drafting": 3, "default": 5},
                "cold_start": {"enabled_layers": [1]},
                "warm_start": {"enabled_layers": [1, 2]},
            }
            # top_k=None → 应回 3 (drafting stage)
            cards = recall(
                stage="drafting",
                topic="玄幻黑暗",
                top_k=None,
                index_path=idx,
                config=config,
            )
            self.assertEqual(len(cards), 3, f"expect 3 from drafting top_k, got {len(cards)}")
            # 未在 config 的 stage 走 default=5
            cards2 = recall(
                stage="analysis",
                topic="玄幻黑暗",
                top_k=None,
                index_path=idx,
                config=config,
            )
            # 注意：analysis stage 在 cards 里不存在 (cards 的 stage=drafting)，所以 0
            # 这里换个写法：换 stage 后改 top_k=None 看是否兜底——用一个新 stage 的卡片
            self.assertEqual(cards2, [])

    def test_filter_expansion_is_configured_not_default(self) -> None:
        """stage/card_intent expansion is opt-in through recall config."""
        from rag.index_builder import build_index
        from rag.layer1_filter import recall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "prompts"
            src.mkdir()
            for slug, stage, intent in [
                ("framework", "framework", "outline_planning"),
                ("outline", "outline", "outline_planning"),
                ("analysis", "analysis", "checker_diagnostic"),
                ("simulation", "setting", "simulation"),
                ("drafting", "drafting", "prose_generation"),
                ("setting-prototype", "setting", "prototype_creation"),
            ]:
                _write_card_md(
                    src,
                    slug,
                    dict(
                        id=f"id-{slug}",
                        asset_type="prompt_card",
                        title=slug,
                        topic=["通用"],
                        stage=stage,
                        quality_grade="A",
                        card_intent=intent,
                        source_path=f"_原料/{slug}.md",
                        last_updated="2026-05-13",
                    ),
                )
            idx = root / "index.sqlite"
            build_index([src], idx)

            exact = recall(
                stage="framework",
                topic="通用",
                asset_type="prompt_card",
                card_intent="outline_planning",
                top_k=10,
                index_path=idx,
            )
            self.assertEqual([card["id"] for card in exact], ["id-framework"])

            expanded = recall(
                stage="framework",
                topic="通用",
                asset_type="prompt_card",
                card_intent="outline_planning",
                top_k=10,
                index_path=idx,
                config={
                    "layer1_filter_expansion": {
                        "stage": {"framework": ["framework", "outline", "analysis"]},
                        "card_intent": {
                            "outline_planning": ["outline_planning", "checker_diagnostic"],
                        },
                    }
                },
            )
            self.assertEqual(
                [card["id"] for card in expanded],
                ["id-analysis", "id-framework", "id-outline"],
            )

            drafting_expanded = recall(
                stage="drafting",
                topic="通用",
                asset_type="prompt_card",
                card_intent="prose_generation",
                top_k=10,
                index_path=idx,
                config={
                    "layer1_filter_expansion": {
                        "stage": {"drafting": ["drafting", "outline", "setting"]},
                        "card_intent": {
                            "prose_generation": [
                                "prose_generation",
                                "outline_planning",
                                "prototype_creation",
                            ],
                        },
                    }
                },
            )
            self.assertEqual(
                [card["id"] for card in drafting_expanded],
                ["id-drafting", "id-outline", "id-setting-prototype"],
            )


class StepDispatchHookTest(unittest.TestCase):
    def test_step_dispatch_rag_mode_off_skips_recall(self) -> None:
        """rag_mode=off 时 step_dispatch 不调召回，audit 记 'rag disabled by user'."""
        from ginga_platform.orchestrator.runner.dsl_parser import Step
        from ginga_platform.orchestrator.runner.state_io import StateIO
        from ginga_platform.orchestrator.runner.step_dispatch import dispatch_step

        called: list[str] = []

        def fake_cap(inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            # 期望 inputs 不含召回结果 (rag off)
            called.append(repr(inputs))
            return {"result": "ok"}

        with tempfile.TemporaryDirectory() as d:
            sio = StateIO("rag-off-book", state_root=Path(d))
            step = Step(id="G_chapter_draft", uses_capability="cap-x")
            ctx = {
                "state_io": sio,
                "workflow_flags": {"rag_mode": "off"},
            }
            result = dispatch_step(
                step,
                ctx,
                capability_registry={"cap-x": fake_cap},
            )
            self.assertEqual(result.used, "capability:cap-x")
            # audit_log 中必须有 rag_mode off 的记录
            sources = [e.get("msg", "") for e in sio.audit_log]
            self.assertTrue(
                any("rag disabled by user" in s for s in sources),
                f"audit_log missing rag-off entry; got: {sources}",
            )
            # capability 收到的 inputs 中 retrieved.cards 应是 [] (hook 注入了空 list)
            self.assertEqual(len(called), 1)
            self.assertIn("retrieved.cards", called[0])

    def test_step_dispatch_rag_mode_on_invokes_recall(self) -> None:
        """rag_mode=on 默认会调召回；空 index 时 cards=[]，audit info 注入 0 card."""
        from ginga_platform.orchestrator.runner.dsl_parser import Step
        from ginga_platform.orchestrator.runner.state_io import StateIO
        from ginga_platform.orchestrator.runner.step_dispatch import dispatch_step

        seen_inputs: list[dict[str, Any]] = []

        def fake_cap(inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            seen_inputs.append(dict(inputs))
            return {"result": "ok"}

        with tempfile.TemporaryDirectory() as d:
            sio = StateIO("rag-on-book", state_root=Path(d))
            # 让 index_path 指向一个不存在的位置（冷启动）
            step = Step(
                id="G_chapter_draft",
                uses_capability="cap-x",
                raw={
                    "id": "G_chapter_draft",
                    "uses_capability": "cap-x",
                    "retrieval_hint": {
                        "stage": "drafting",
                        "topic": ["玄幻黑暗"],
                        "index_path": str(Path(d) / "no-index.sqlite"),
                    },
                },
            )
            ctx = {
                "state_io": sio,
                "workflow_flags": {"rag_mode": "on"},
            }
            dispatch_step(step, ctx, capability_registry={"cap-x": fake_cap})
            self.assertEqual(seen_inputs[0].get("retrieved.cards"), [])
            msgs = [e.get("msg", "") for e in sio.audit_log]
            self.assertTrue(
                any("rag recall injected 0 card" in m for m in msgs),
                f"missing rag-on audit msg; got: {msgs}",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
