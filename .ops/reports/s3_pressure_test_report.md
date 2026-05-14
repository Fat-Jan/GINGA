# Sprint 3 Pressure Test Report

Generated: `2026-05-14T13:30:07.598560+00:00`

## Overall

- Pass rate: **100.0%** (7/7)
- Mean dimension score: **100.0%**
- Target: **80%**
- Result: **PASS**
- Runtime policy: local artifact reads only; no LLM calls; no runtime_state mutation.

## Dimensions

| Dimension | Status | Score | Key evidence |
|---|---:|---:|---|
| multi-chapter continuity | PASS | 100.0% | headings=[1, 2, 3, 4, 5]; anchors={'微粒': 100, '天堑': 7, '内宇宙': 13, '短刃': 43} |
| immersive continuity | PASS | 100.0% | headings=[1, 2, 3, 4, 5]; anchors={'微粒': 102, '天堑': 14, '内宇宙': 8, '短刃': 65} |
| prompt schema readiness | PASS | 100.0% | violations=0; min coverage=100% |
| weak-example debt | PASS | 100.0% | 0/461 weak candidates |
| methodology asset readiness | PASS | 100.0% | methodology_asset_count=12, checker_asset_count=1 |
| dedup evidence readiness | PASS | 100.0% | status=ok, sample_count=25 |
| RAG test status | PASS | 100.0% | Ran 13 tests OK |

## Failing Dimensions

- None.

## Notes

- weak-example debt: Failing until weak_example_candidate_count reaches 0.
- RAG test status: Handoff also records full ginga_platform discovery: Ran 112 tests OK.
