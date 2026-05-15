"""Contract tests for v1.3-1 Reference Corpus P0 MVP.

These tests intentionally describe the first implementation surface for
``ginga_platform.book_analysis``.  If the package is not present yet, the
failures should point the implementation worker at the API names to provide.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping


UNIQUE_SOURCE_SENTENCE = "银烛城的鹤骨钟在午夜倒转三次。"

EXPECTED_API = {
    "ginga_platform.book_analysis.corpus": [
        "scan_source",
        "split_chapters",
        "build_source_manifest",
        "build_reference_corpus",
        "build_chapter_atoms",
        "build_trope_recipes",
        "promote_trope_recipes",
    ],
    "ginga_platform.book_analysis.promote": [
        "promote_trope_recipes",
    ],
    "ginga_platform.book_analysis.chapter_atoms": [
        "extract_chapter_atoms",
        "write_chapter_atoms_run",
    ],
    "ginga_platform.book_analysis.trope_recipes": [
        "extract_trope_recipe_candidates",
        "write_trope_recipe_run",
    ],
    "ginga_platform.book_analysis.report": ["render_scan_report"],
    "ginga_platform.book_analysis.validation": [
        "validate_manifest_dict",
        "validate_reference_corpus",
        "validate_chapter_atoms_run",
        "validate_trope_recipe_run",
        "validate_promoted_trope_assets",
    ],
}


def _load(name: str) -> Any:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:  # pragma: no cover - red-light contract
        raise AssertionError(
            f"Missing module {name!r}; expected v1.3-1 API: {EXPECTED_API}"
        ) from exc


def _require(module_name: str, attr: str) -> Any:
    module = _load(module_name)
    try:
        return getattr(module, attr)
    except AttributeError as exc:  # pragma: no cover - red-light contract
        raise AssertionError(
            f"Missing {module_name}.{attr}; expected v1.3-1 API: {EXPECTED_API}"
        ) from exc


def _write_source(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.write_text(text, encoding=encoding)


def _chaptered_text() -> str:
    return "\n".join(
        [
            "第1章 雾桥来信",
            UNIQUE_SOURCE_SENTENCE,
            "桥下只有潮声，没有任何人回答。",
            "",
            "第2章 旧塔灯火",
            "旧塔的灯火一盏盏熄灭。",
            "",
            "第三章 归潮",
            "潮水把无人认领的信送回岸边。",
        ]
    )


def _chapter_list(split_result: Any) -> list[Mapping[str, Any]]:
    if isinstance(split_result, Mapping):
        chapters = split_result.get("chapters", [])
    else:
        chapters = split_result
    assert isinstance(chapters, list), f"chapters should be a list, got {type(chapters)!r}"
    return chapters


def _issue_codes(items: Any) -> set[str]:
    if not items:
        return set()
    return {str(item.get("code")) for item in items if isinstance(item, Mapping)}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class ReferenceCorpusP0ContractTest(unittest.TestCase):
    def test_scan_source_records_metadata_hash_size_title_encoding_and_no_excerpt(self) -> None:
        scan_source = _require("ginga_platform.book_analysis.corpus", "scan_source")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample-reference.txt"
            _write_source(source, _chaptered_text())

            meta = scan_source(source)

        expected_hash = hashlib.sha256(_chaptered_text().encode("utf-8")).hexdigest()
        self.assertEqual(meta["sha256"], expected_hash)
        self.assertEqual(meta["input_size_bytes"], len(_chaptered_text().encode("utf-8")))
        self.assertEqual(meta["title"], "sample-reference")
        self.assertEqual(meta["encoding"].lower().replace("_", "-"), "utf-8")
        for forbidden in ("excerpt", "text", "content", "body", "raw_text", "source_text"):
            self.assertNotIn(forbidden, meta, f"scan metadata must not persist source excerpts: {forbidden}")

    def test_split_chapters_finds_chinese_headings_with_continuous_indexes_and_hashes_only(self) -> None:
        split_chapters = _require("ginga_platform.book_analysis.corpus", "split_chapters")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reference.txt"
            _write_source(source, _chaptered_text())

            result = split_chapters(source, encoding="utf-8")

        chapters = _chapter_list(result)
        self.assertEqual([chapter["index"] for chapter in chapters], [1, 2, 3])
        self.assertEqual([chapter["title"] for chapter in chapters], ["雾桥来信", "旧塔灯火", "归潮"])
        self.assertTrue(all(len(chapter["sha256"]) == 64 for chapter in chapters), chapters)
        self.assertTrue(all("start_offset" in chapter and "end_offset" in chapter for chapter in chapters))
        for chapter in chapters:
            for forbidden in ("excerpt", "text", "content", "body", "raw_text", "source_text"):
                self.assertNotIn(forbidden, chapter, f"chapter index must not persist source excerpts: {forbidden}")

    def test_split_chapters_returns_error_for_missing_headings_without_fake_chapters(self) -> None:
        split_chapters = _require("ginga_platform.book_analysis.corpus", "split_chapters")

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "plain.txt"
            _write_source(source, "这里只是一段没有章节标题的参考文本。\n" + UNIQUE_SOURCE_SENTENCE)

            result = split_chapters(source, encoding="utf-8")

        chapters = _chapter_list(result)
        self.assertEqual(chapters, [])
        self.assertIn(result.get("status"), {"error", "failed", "completed_with_errors"})
        self.assertIn("no_chapter_heading", _issue_codes(result.get("anomalies")))

    def test_split_chapters_reports_duplicate_missing_out_of_order_and_long_titles(self) -> None:
        split_chapters = _require("ginga_platform.book_analysis.corpus", "split_chapters")
        long_title = "过长标题" * 50
        source_text = "\n".join(
            [
                "第1章 重复之门",
                "第一段。",
                "第1章 重复之门",
                "第二段。",
                "第3章 跳号之雾",
                "第三段。",
                "第2章 倒序之潮",
                "第四段。",
                f"第4章 {long_title}",
                "第五段。",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "anomalies.txt"
            _write_source(source, source_text)

            result = split_chapters(
                source,
                encoding="utf-8",
                limits={"max_chapter_title_chars": 120},
            )

        codes = _issue_codes(result.get("anomalies")) | _issue_codes(result.get("warnings"))
        self.assertIn("duplicate_title", codes)
        self.assertIn("missing_number", codes)
        self.assertIn("out_of_order", codes)
        self.assertIn("long_title", codes)

    def test_manifest_contains_required_p0_fields_pollution_limits_and_zero_private_resources(self) -> None:
        build_source_manifest = _require("ginga_platform.book_analysis.corpus", "build_source_manifest")

        source_meta = {
            "path": "/tmp/reference.txt",
            "sha256": "a" * 64,
            "encoding": "utf-8",
            "title": "reference",
            "input_size_bytes": 123,
        }
        split_result = {
            "status": "ok",
            "chapters": [{"index": 1, "title": "开端", "sha256": "b" * 64}],
            "anomalies": [],
            "warnings": [],
        }

        manifest = build_source_manifest(
            run_id="book-analysis-test",
            source=source_meta,
            split_result=split_result,
            output_root=".ops/book_analysis/book-analysis-test",
            elapsed_seconds=0.01,
        )

        for key in (
            "run_id",
            "schema_version",
            "created_at",
            "source",
            "output",
            "chapters",
            "resources",
            "keyword_sources",
            "pollution",
            "validation",
            "limits",
        ):
            self.assertIn(key, manifest)
        self.assertTrue(manifest["pollution"]["pollution_source"])
        self.assertEqual(manifest["pollution"]["source_marker"], "[SOURCE_TROPE]")
        self.assertTrue(manifest["pollution"]["default_rag_excluded"])
        self.assertFalse(manifest["keyword_sources"]["active"])
        self.assertEqual(manifest["resources"]["excerpt_chars_saved"], 0)
        self.assertEqual(manifest["resources"]["private_cache_bytes"], 0)
        self.assertEqual(manifest["limits"]["defaults"]["max_excerpt_chars"], 0)
        self.assertEqual(manifest["limits"]["configured"]["max_excerpt_chars"], 0)
        self.assertFalse(manifest["limits"]["configured"]["private_cache_enabled"])

    def test_report_starts_with_source_marker_and_excludes_unique_source_sentences(self) -> None:
        render_scan_report = _require("ginga_platform.book_analysis.report", "render_scan_report")

        manifest = {
            "run_id": "book-analysis-test",
            "source": {"title": "reference", "input_size_bytes": 123, "sha256": "a" * 64},
            "chapters": {
                "count": 2,
                "numbering_ok": True,
                "anomalies": [],
            },
            "validation": {"status": "passed", "errors": [], "warnings": []},
            "pollution": {"source_marker": "[SOURCE_TROPE]"},
        }
        report = render_scan_report(
            manifest,
            split_result={
                "chapters": [{"index": 1, "title": "雾桥来信", "sha256": "b" * 64}],
                "source_preview": UNIQUE_SOURCE_SENTENCE,
            },
        )

        self.assertTrue(report.startswith("[SOURCE_TROPE]"), report[:80])
        self.assertIn("结构", report)
        self.assertNotIn(UNIQUE_SOURCE_SENTENCE, report)
        self.assertNotIn("桥下只有潮声", report)

    def test_validator_finds_pollution_path_chapter_count_and_rag_exclusion_errors(self) -> None:
        validate_manifest_dict = _require(
            "ginga_platform.book_analysis.validation",
            "validate_manifest_dict",
        )

        manifest = {
            "run_id": "book-analysis-test",
            "schema_version": "0.1.0",
            "created_at": "2026-05-15T15:00:00+08:00",
            "source": {
                "path": "/tmp/reference.txt",
                "sha256": "a" * 64,
                "encoding": "utf-8",
                "title": "reference",
                "input_size_bytes": 123,
            },
            "output": {
                "root": ".ops/book_analysis/book-analysis-test",
                "manifest_path": ".ops/book_analysis/book-analysis-test/source_manifest.json",
                "chapter_index_path": "/tmp/outside/chapter_index.json",
                "report_path": ".ops/book_analysis/book-analysis-test/scan_report.md",
            },
            "chapters": {
                "count": 2,
                "numbering_ok": True,
                "anomalies": [],
                "chapter_index_path": ".ops/book_analysis/book-analysis-test/chapter_index.json",
            },
            "resources": {
                "input_size_bytes": 123,
                "chapter_count": 2,
                "elapsed_seconds": 0.01,
                "excerpt_chars_saved": 0,
                "private_cache_bytes": 0,
            },
            "keyword_sources": {"active": False, "allowed_source_types": [], "entries": []},
            "pollution": {
                "pollution_source": False,
                "source_marker": "[SOURCE_TROPE]",
                "default_rag_excluded": False,
            },
            "validation": {"validator": "tests", "status": "not_run", "errors": [], "warnings": []},
            "limits": {
                "defaults": {
                    "max_input_size_bytes": 10485760,
                    "max_chapters": 500,
                    "max_elapsed_seconds": 120,
                    "max_chapter_title_chars": 120,
                    "max_excerpt_chars": 0,
                    "private_cache_enabled": False,
                    "max_private_cache_bytes": 0,
                },
                "configured": {
                    "max_input_size_bytes": 10485760,
                    "max_chapters": 500,
                    "max_elapsed_seconds": 120,
                    "max_chapter_title_chars": 120,
                    "max_excerpt_chars": 0,
                    "private_cache_enabled": False,
                    "max_private_cache_bytes": 0,
                },
            },
        }
        chapter_index = [{"index": 1, "title": "开端", "sha256": "b" * 64}]
        recall_config = {"recall_forbidden_paths": [], "recall_sources": [{"path": ".ops/book_analysis/"}]}

        report = validate_manifest_dict(
            manifest,
            chapter_index=chapter_index,
            run_root=Path(".ops/book_analysis/book-analysis-test"),
            recall_config=recall_config,
        )

        codes = _issue_codes(report.get("errors"))
        self.assertIn("missing_pollution_source", codes)
        self.assertIn("output_path_outside_run_root", codes)
        self.assertIn("chapter_count_mismatch", codes)
        self.assertIn("default_rag_not_excluded", codes)

    def test_build_reference_corpus_writes_run_outputs_and_validator_passes(self) -> None:
        build_reference_corpus = _require("ginga_platform.book_analysis.corpus", "build_reference_corpus")
        validate_reference_corpus = _require(
            "ginga_platform.book_analysis.validation",
            "validate_reference_corpus",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            source = repo_root / "incoming" / "reference.txt"
            source.parent.mkdir()
            _write_source(source, _chaptered_text())

            run_root = build_reference_corpus(
                source_path=source,
                run_id="book-analysis-test",
                output_base=repo_root / ".ops" / "book_analysis",
            )
            run_root = Path(run_root)

            self.assertEqual(run_root, repo_root / ".ops" / "book_analysis" / "book-analysis-test")
            manifest_path = run_root / "source_manifest.json"
            chapter_index_path = run_root / "chapter_index.json"
            report_path = run_root / "scan_report.md"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(chapter_index_path.exists())
            self.assertTrue(report_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            chapters = json.loads(chapter_index_path.read_text(encoding="utf-8"))
            report_md = report_path.read_text(encoding="utf-8")

            self.assertEqual(manifest["chapters"]["count"], 3)
            self.assertEqual(len(chapters), 3)
            self.assertTrue(manifest["pollution"]["default_rag_excluded"])
            self.assertEqual(manifest["resources"]["excerpt_chars_saved"], 0)
            self.assertTrue(report_md.startswith("[SOURCE_TROPE]"))
            self.assertNotIn(UNIQUE_SOURCE_SENTENCE, report_md)

            validation = validate_reference_corpus(run_root, repo_root=repo_root)
            self.assertEqual(validation["status"], "passed", validation)

            for unexpected in (
                repo_root / "foundation" / "runtime_state",
                repo_root / "foundation" / "raw_ideas",
                run_root / ".private_evidence",
            ):
                self.assertFalse(unexpected.exists(), f"P0 corpus build must not create {unexpected}")


class ChapterAtomV132ContractTest(unittest.TestCase):
    def _build_p0_run(self, repo_root: Path) -> Path:
        build_reference_corpus = _require("ginga_platform.book_analysis.corpus", "build_reference_corpus")
        source = repo_root / "incoming" / "reference.txt"
        source.parent.mkdir(parents=True, exist_ok=True)
        _write_source(source, _chaptered_text())
        return Path(
            build_reference_corpus(
                source_path=source,
                run_id="v1-3-2-source",
                output_base=repo_root / ".ops" / "book_analysis",
            )
        )

    def test_extract_chapter_atoms_returns_structure_only_events_without_source_excerpts(self) -> None:
        extract_chapter_atoms = _require(
            "ginga_platform.book_analysis.chapter_atoms",
            "extract_chapter_atoms",
        )

        chapters = [
            {
                "chapter_id": "ch-0001",
                "chapter_no": 1,
                "title": "雾桥来信",
                "start_offset": 0,
                "end_offset": 120,
                "char_count": 120,
                "sha256": "b" * 64,
                "anomalies": [],
            }
        ]
        result = extract_chapter_atoms(chapters)

        self.assertEqual(result["schema_version"], "0.2.0")
        self.assertEqual(result["quality_gates"]["status"], "passed")
        self.assertEqual(len(result["chapter_atoms"]), 1)
        atom = result["chapter_atoms"][0]
        self.assertEqual(atom["atom_id"], "atom-ch-0001-001")
        self.assertEqual(atom["source_chapter_id"], "ch-0001")
        self.assertEqual(atom["atom_type"], "chapter_boundary")
        self.assertEqual(atom["title_fingerprint"], hashlib.sha256("雾桥来信".encode("utf-8")).hexdigest())
        self.assertNotIn("title", atom)
        for forbidden in ("excerpt", "text", "content", "body", "raw_text", "source_text"):
            self.assertNotIn(forbidden, atom, f"chapter atom must not persist source excerpts: {forbidden}")

    def test_build_chapter_atoms_writes_sidecar_outputs_and_validator_passes(self) -> None:
        build_chapter_atoms = _require("ginga_platform.book_analysis.corpus", "build_chapter_atoms")
        validate_chapter_atoms_run = _require(
            "ginga_platform.book_analysis.validation",
            "validate_chapter_atoms_run",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            source_run_root = self._build_p0_run(repo_root)

            atom_run_root = Path(
                build_chapter_atoms(
                    source_run_root=source_run_root,
                    run_id="v1-3-2-atoms",
                    output_base=repo_root / ".ops" / "book_analysis",
                )
            )

            self.assertEqual(atom_run_root, repo_root / ".ops" / "book_analysis" / "v1-3-2-atoms")
            atoms_path = atom_run_root / "chapter_atoms.json"
            gates_path = atom_run_root / "quality_gates.json"
            report_path = atom_run_root / "chapter_atom_report.md"
            run_config_path = atom_run_root / "run_config.json"
            for path in (atoms_path, gates_path, report_path, run_config_path):
                self.assertTrue(path.exists(), f"missing v1.3-2 output: {path}")

            atoms_payload = json.loads(atoms_path.read_text(encoding="utf-8"))
            gates_payload = json.loads(gates_path.read_text(encoding="utf-8"))
            report_md = report_path.read_text(encoding="utf-8")
            self.assertEqual(len(atoms_payload["chapter_atoms"]), 3)
            self.assertEqual(gates_payload["status"], "passed")
            self.assertTrue(report_md.startswith("[SOURCE_TROPE]"))
            self.assertIn("Chapter Atom", report_md)
            self.assertNotIn(UNIQUE_SOURCE_SENTENCE, report_md)
            self.assertNotIn("桥下只有潮声", report_md)

            validation = validate_chapter_atoms_run(atom_run_root, repo_root=repo_root)
            self.assertEqual(validation["status"], "passed", validation)

            for unexpected in (
                repo_root / "foundation" / "runtime_state",
                repo_root / "foundation" / "raw_ideas",
                atom_run_root / ".private_evidence",
            ):
                self.assertFalse(unexpected.exists(), f"v1.3-2 atom build must not create {unexpected}")

    def test_chapter_atom_validator_rejects_excerpts_bad_boundaries_and_failed_gates(self) -> None:
        validate_chapter_atoms_run = _require(
            "ginga_platform.book_analysis.validation",
            "validate_chapter_atoms_run",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            run_root = repo_root / ".ops" / "book_analysis" / "bad-atoms"
            run_root.mkdir(parents=True)
            _write_json(
                run_root / "chapter_atoms.json",
                {
                    "schema_version": "0.2.0",
                    "run_id": "bad-atoms",
                    "pollution": {
                        "pollution_source": True,
                        "source_marker": "[SOURCE_TROPE]",
                        "default_rag_excluded": True,
                    },
                    "chapter_atoms": [
                        {
                            "atom_id": "atom-ch-0001-001",
                            "source_chapter_id": "ch-0001",
                            "atom_type": "chapter_boundary",
                            "title_fingerprint": "c" * 64,
                            "excerpt": UNIQUE_SOURCE_SENTENCE,
                        }
                    ],
                    "quality_gates": {"status": "failed", "errors": [{"code": "manual_failure"}], "warnings": []},
                },
            )
            _write_json(run_root / "quality_gates.json", {"status": "failed", "errors": [{"code": "manual_failure"}], "warnings": []})
            (run_root / "chapter_atom_report.md").write_text("[SOURCE_TROPE]\n# Bad Atom Report\n", encoding="utf-8")

            validation = validate_chapter_atoms_run(run_root, repo_root=repo_root)

        codes = _issue_codes(validation.get("errors"))
        self.assertIn("atom_excerpt_saved", codes)
        self.assertIn("quality_gate_failed", codes)


class TropeRecipeV133ContractTest(unittest.TestCase):
    def _build_atom_run(self, repo_root: Path) -> Path:
        build_reference_corpus = _require("ginga_platform.book_analysis.corpus", "build_reference_corpus")
        build_chapter_atoms = _require("ginga_platform.book_analysis.corpus", "build_chapter_atoms")
        source = repo_root / "incoming" / "reference.txt"
        source.parent.mkdir(parents=True, exist_ok=True)
        _write_source(source, _chaptered_text())
        source_run_root = Path(
            build_reference_corpus(
                source_path=source,
                run_id="v1-3-3-source",
                output_base=repo_root / ".ops" / "book_analysis",
            )
        )
        return Path(
            build_chapter_atoms(
                source_run_root=source_run_root,
                run_id="v1-3-3-atoms",
                output_base=repo_root / ".ops" / "book_analysis",
            )
        )

    def test_extract_trope_recipe_candidates_returns_de_sourced_candidates(self) -> None:
        extract_trope_recipe_candidates = _require(
            "ginga_platform.book_analysis.trope_recipes",
            "extract_trope_recipe_candidates",
        )
        atoms_payload = {
            "run_id": "v1-3-3-atoms",
            "chapter_atoms": [
                {
                    "atom_id": "atom-ch-0001-001",
                    "source_chapter_id": "ch-0001",
                    "chapter_sha256": "b" * 64,
                    "title_fingerprint": "c" * 64,
                }
            ],
        }

        result = extract_trope_recipe_candidates(atoms_payload)

        self.assertEqual(result["schema_version"], "0.3.0")
        self.assertEqual(result["quality_gates"]["status"], "passed")
        self.assertEqual(result["promotion"]["status"], "not_promoted")
        self.assertEqual(len(result["candidates"]), 1)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["candidate_type"], "trope_recipe_candidate")
        self.assertTrue(candidate["pollution_source"])
        self.assertEqual(candidate["target"]["promote_to"], "none")
        self.assertGreaterEqual(len(candidate["variation_axes"]), 2)
        self.assertGreaterEqual(len(candidate["forbidden_copy_elements"]), 1)
        self.assertEqual(candidate["safety"]["source_contamination_check"], "pending")
        self.assertEqual(candidate["safety"]["human_review_status"], "pending")
        self.assertNotIn(UNIQUE_SOURCE_SENTENCE, json.dumps(candidate, ensure_ascii=False))
        self.assertNotIn("雾桥来信", json.dumps(candidate, ensure_ascii=False))
        for forbidden in ("excerpt", "text", "content", "body", "raw_text", "source_text", "title"):
            self.assertNotIn(forbidden, candidate, f"trope recipe must not persist source material: {forbidden}")

    def test_build_trope_recipes_writes_sidecar_outputs_and_validator_passes(self) -> None:
        build_trope_recipes = _require("ginga_platform.book_analysis.corpus", "build_trope_recipes")
        validate_trope_recipe_run = _require(
            "ginga_platform.book_analysis.validation",
            "validate_trope_recipe_run",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            atom_run_root = self._build_atom_run(repo_root)

            recipe_run_root = Path(
                build_trope_recipes(
                    source_atom_run_root=atom_run_root,
                    run_id="v1-3-3-recipes",
                    output_base=repo_root / ".ops" / "book_analysis",
                )
            )

            self.assertEqual(recipe_run_root, repo_root / ".ops" / "book_analysis" / "v1-3-3-recipes")
            recipes_path = recipe_run_root / "trope_recipes.json"
            gates_path = recipe_run_root / "quality_gates.json"
            report_path = recipe_run_root / "trope_recipe_report.md"
            run_config_path = recipe_run_root / "run_config.json"
            for path in (recipes_path, gates_path, report_path, run_config_path):
                self.assertTrue(path.exists(), f"missing v1.3-3 output: {path}")

            recipes_payload = json.loads(recipes_path.read_text(encoding="utf-8"))
            gates_payload = json.loads(gates_path.read_text(encoding="utf-8"))
            report_md = report_path.read_text(encoding="utf-8")
            self.assertEqual(len(recipes_payload["candidates"]), 3)
            self.assertEqual(gates_payload["status"], "passed")
            self.assertTrue(report_md.startswith("[SOURCE_TROPE]"))
            self.assertIn("Trope Recipe Candidate", report_md)
            self.assertNotIn(UNIQUE_SOURCE_SENTENCE, report_md)
            self.assertNotIn("桥下只有潮声", report_md)

            validation = validate_trope_recipe_run(recipe_run_root, repo_root=repo_root)
            self.assertEqual(validation["status"], "passed", validation)

            for unexpected in (
                repo_root / "foundation" / "runtime_state",
                repo_root / "foundation" / "raw_ideas",
                repo_root / "foundation" / "assets",
                repo_root / "foundation" / "schema",
                recipe_run_root / ".private_evidence",
            ):
                self.assertFalse(unexpected.exists(), f"v1.3-3 recipe build must not create {unexpected}")

    def test_trope_recipe_validator_rejects_pollution_promotion_and_missing_safety(self) -> None:
        validate_trope_recipe_run = _require(
            "ginga_platform.book_analysis.validation",
            "validate_trope_recipe_run",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            run_root = repo_root / ".ops" / "book_analysis" / "bad-recipes"
            run_root.mkdir(parents=True)
            _write_json(
                run_root / "trope_recipes.json",
                {
                    "schema_version": "0.3.0",
                    "run_id": "bad-recipes",
                    "pollution": {
                        "pollution_source": True,
                        "source_marker": "[SOURCE_TROPE]",
                        "default_rag_excluded": True,
                        "runtime_state_write_allowed": True,
                    },
                    "promotion": {"status": "promoted", "promote_to": "foundation"},
                    "candidates": [
                        {
                            "candidate_id": "trope-bad-001",
                            "candidate_type": "trope_recipe_candidate",
                            "pollution_source": True,
                            "source_refs": [{"evidence_id": "atom-bad", "source_hash": "b" * 64}],
                            "trope_core": "把雾桥来信的桥下潮声事件链改名复用。",
                            "reader_payoff": "复刻原作反转。",
                            "trigger_conditions": [],
                            "variation_axes": ["genre_swap"],
                            "forbidden_copy_elements": [],
                            "safety": {
                                "source_contamination_check": "fail",
                                "similarity_score": 0.9,
                                "human_review_status": "pending",
                            },
                            "target": {"promote_to": "foundation"},
                            "excerpt": UNIQUE_SOURCE_SENTENCE,
                        }
                    ],
                    "quality_gates": {"status": "failed", "errors": [{"code": "manual_failure"}], "warnings": []},
                },
            )
            _write_json(run_root / "quality_gates.json", {"status": "failed", "errors": [{"code": "manual_failure"}], "warnings": []})
            (run_root / "trope_recipe_report.md").write_text("[SOURCE_TROPE]\n# Bad Recipe Report\n", encoding="utf-8")

            validation = validate_trope_recipe_run(run_root, repo_root=repo_root)

        codes = _issue_codes(validation.get("errors"))
        self.assertIn("boundary_flag_not_false", codes)
        self.assertIn("promotion_not_allowed", codes)
        self.assertIn("missing_source_ref_field", codes)
        self.assertIn("insufficient_variation_axes", codes)
        self.assertIn("missing_forbidden_copy_elements", codes)
        self.assertIn("invalid_source_contamination_check", codes)
        self.assertIn("similarity_score_failed", codes)
        self.assertIn("recipe_forbidden_field_saved", codes)
        self.assertIn("quality_gate_failed", codes)


class TropeRecipePromoteFlowV134ContractTest(unittest.TestCase):
    def _candidate(self, *, approved: bool = True, contamination: str = "pass") -> dict[str, Any]:
        return {
            "candidate_id": "trope-ch-0001-001",
            "candidate_type": "trope_recipe_candidate",
            "pollution_source": True,
            "recipe_type": "underestimated_reversal",
            "source_refs": [
                {
                    "evidence_id": "atom-ch-0001-001",
                    "source_hash": "b" * 64,
                    "chapter_hash": "b" * 64,
                    "excerpt_hash": "c" * 64,
                    "chapter_locator": {"source_chapter_id": "ch-0001"},
                }
            ],
            "trope_core": "弱势角色被低估后，通过公开验证场景证明隐藏能力，使地位判断发生反转。",
            "reader_payoff": "读者获得压抑后的反转释放。",
            "trigger_conditions": ["角色被公开低估"],
            "variation_axes": ["genre_swap", "identity_swap"],
            "forbidden_copy_elements": ["source proper nouns", "source dialogue"],
            "safety": {
                "source_contamination_check": contamination,
                "similarity_score": 0.12,
                "human_review_status": "approved" if approved else "pending",
            },
            "target": {"promote_to": "none"},
        }

    def _recipe_payload(self, candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "0.3.0",
            "run_id": "v1-3-3-recipes",
            "pollution": {
                "pollution_source": True,
                "source_marker": "[SOURCE_TROPE]",
                "default_rag_excluded": True,
                "runtime_state_write_allowed": False,
                "raw_ideas_write_allowed": False,
                "prompt_injection_allowed": False,
                "default_input_whitelist_allowed": False,
            },
            "promotion": {
                "status": "not_promoted",
                "promote_to": "none",
                "requires_human_review": True,
            },
            "candidates": [candidate],
            "quality_gates": {"status": "passed", "errors": [], "warnings": []},
        }

    def test_promote_flow_requires_human_review_and_contamination_pass(self) -> None:
        promote_trope_recipes = _require("ginga_platform.book_analysis.promote", "promote_trope_recipes")

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "human_review_status"):
                promote_trope_recipes(
                    self._recipe_payload(self._candidate(approved=False)),
                    repo_root=repo_root,
                    approved_candidate_ids=["trope-ch-0001-001"],
                    target_kind="methodology",
                )
            with self.assertRaisesRegex(ValueError, "source_contamination_check"):
                promote_trope_recipes(
                    self._recipe_payload(self._candidate(contamination="pending")),
                    repo_root=repo_root,
                    approved_candidate_ids=["trope-ch-0001-001"],
                    target_kind="methodology",
                )

    def test_promote_flow_writes_only_whitelisted_foundation_asset(self) -> None:
        promote_trope_recipes = _require("ginga_platform.book_analysis.promote", "promote_trope_recipes")
        validate_promoted_trope_assets = _require(
            "ginga_platform.book_analysis.validation",
            "validate_promoted_trope_assets",
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            report = promote_trope_recipes(
                self._recipe_payload(self._candidate()),
                repo_root=repo_root,
                approved_candidate_ids=["trope-ch-0001-001"],
                target_kind="methodology",
            )

            self.assertEqual(report["status"], "promoted")
            output_path = repo_root / report["promoted_assets"][0]["path"]
            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.is_relative_to(repo_root / "foundation" / "assets" / "methodology"))
            text = output_path.read_text(encoding="utf-8")
            self.assertIn("asset_type: methodology", text)
            self.assertIn("promoted_from: trope-ch-0001-001", text)
            self.assertIn("source_contamination_check: pass", text)
            self.assertFalse((repo_root / "foundation" / "runtime_state").exists())
            self.assertFalse((repo_root / "foundation" / "raw_ideas").exists())
            self.assertFalse((repo_root / "foundation" / "assets" / "prompts").exists())

            validation = validate_promoted_trope_assets(
                repo_root / "foundation" / "assets" / "methodology",
                repo_root=repo_root,
            )
            self.assertEqual(validation["status"], "passed", validation)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
