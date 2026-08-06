# Lane 003: extracted-text companion reconciliation

Status: **complete**

This lane reconciled existing extracted-text companions against the Phase 0 canonical source inventory. It did not run extraction or OCR, and it did not copy, move, delete, package, stage, or commit any source or companion file.

## Results

- Canonical source universe: **26,637**
- Current text companions selected by exact source SHA-256: **23,454**
- Selected current companion bytes: **1,201,303,562** (1.12 GiB)
- Sources without a selected text companion: **3,183**
- Proposed companion-path collisions: **0**

## Status distribution

- `current_text_companion_available`: 23,454
- `no_text_companion_extraction_repair_required`: 97
- `no_text_companion_no_extraction_manifest`: 2,623
- `no_text_companion_ocr_deferred`: 118
- `no_text_companion_readiness_excluded`: 328
- `structured_only_no_text_companion`: 17

## Selection provenance

- `broad_state_4x2500_text`: 2,625
- `combined_broad_text_4051`: 3,761
- `remaining_municipalities_text`: 2,292
- `targeted_text_layer_321`: 289
- `tier_c_text_layer_378`: 344
- `whole_corpus_external_non_ocr_extraction`: 14,143


## Linkage policy

All selected links use the original source file's SHA-256. The current whole-corpus non-OCR extraction layer has first priority, followed by earlier complete extraction manifests in chronological order. Filename-only inference is never used. When several exact-hash-linked text variants remain, the chosen current companion is recorded alongside the multiplicity and uncertainty flag.

CSV structured rows are not mislabeled as extracted text. OCR-later, extraction-repair, readiness-excluded, and no-manifest sources remain explicit non-companion statuses.

## Packaging boundary

The `proposed_companion_archive_path` field is only a future path plan. This lane created no archive and copied no data.
