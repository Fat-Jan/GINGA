# Methodology Assets Migration Report

Task: `ST-S3-M-METHODOLOGY-ASSETS`  
Date: 2026-05-14

## Counts

- Source markdown files discovered under `_原料/基座/方法论`: 14
- Scout-confirmed source files migrated: 13
- Methodology assets created: 12
- Checker/schema-ref assets created: 1
- Validator scripts created: 1

## File Map

| Source | Asset | Type |
|---|---|---|
| `_原料/基座/方法论/市场/2026网文市场趋势.md` | `foundation/assets/methodology/base-methodology-market-2026-webnovel-trends.md` | methodology |
| `_原料/基座/方法论/市场/state-schema.md` | `foundation/assets/checkers_or_schema_refs/base-schema-ref-runtime-state.md` | checker_or_schema_ref |
| `_原料/基座/方法论/市场/读者吸引力分类法.md` | `foundation/assets/methodology/base-methodology-market-reading-power-taxonomy.md` | methodology |
| `_原料/基座/方法论/写作/世界观母题目录.md` | `foundation/assets/methodology/base-methodology-writing-worldview-motif-catalog.md` | methodology |
| `_原料/基座/方法论/写作/反AI味.md` | `foundation/assets/methodology/base-methodology-writing-anti-ai-style.md` | methodology |
| `_原料/基座/方法论/写作/古代官职体系.md` | `foundation/assets/methodology/base-methodology-writing-ancient-official-system.md` | methodology |
| `_原料/基座/方法论/写作/古代家族亲缘.md` | `foundation/assets/methodology/base-methodology-writing-ancient-kinship.md` | methodology |
| `_原料/基座/方法论/写作/角色命名.md` | `foundation/assets/methodology/base-methodology-writing-character-naming.md` | methodology |
| `_原料/基座/方法论/创意/平台分析指南.md` | `foundation/assets/methodology/base-methodology-creative-platform-analysis.md` | methodology |
| `_原料/基座/方法论/创意/投稿指南.md` | `foundation/assets/methodology/base-methodology-creative-submission-guide.md` | methodology |
| `_原料/基座/方法论/创意/黄金三章.md` | `foundation/assets/methodology/base-methodology-creative-golden-three.md` | methodology |
| `_原料/基座/方法论/平台/跨平台写作规范.md` | `foundation/assets/methodology/base-methodology-platform-cross-platform-writing.md` | methodology |
| `_原料/基座/方法论/平台/题材跨平台适配矩阵.md` | `foundation/assets/methodology/base-methodology-platform-genre-adaptation-matrix.md` | methodology |

## Priority File Handling

- `黄金三章.md`: includes `hard_rule`, `soft_rule`, `checklist`, `example`, and `platform_variant`.
- `读者吸引力分类法.md`: includes `hard_rule`, `enumeration`, `checklist`, and `schema_ref`; kept as methodology with checker integration notes.
- `state-schema.md`: migrated as `checker_or_schema_ref` because the checker/schema schema supports `target_asset_type`, `output_schema`, and `check_mode`.
- `反AI味.md`: includes `hard_rule`, `soft_rule`, `checklist`, and `example`; notes checker integration.
- `角色命名.md`: includes `hard_rule`, `soft_rule`, `checklist`, and `example`.
- `跨平台写作规范.md`: includes `hard_rule`, `soft_rule`, `checklist`, `platform_variant`, and `example`.

## Deferred Ambiguities

- `_原料/基座/方法论/写作/平台审核.md` exists in the live tree but was not listed in `.ops/scout-reports/scout1-base.md` among the 13 methodology files. To preserve the requested count of 13, it was not migrated in this pass.
- Several source documents contain market or platform policy claims with time sensitivity. Assets preserve routing and operational guidance, but final execution should refresh live platform rules before production use.
- The validator currently checks required fields, enum values, ISO dates, topic list shape, `source_path` existence, and `sub_sections` shape. It does not validate nested object schemas beyond basic structure.
