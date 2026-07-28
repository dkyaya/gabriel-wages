# Next task prompt — four-lane combined broad text extraction

## Scope

Run bounded local text extraction over exactly 4,051 readiness-approved retained sources from:

`docs/analysis/compensation_extraction/COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28/`

Build the locked extraction queue only from the union of:

- `combined_broad_pdf_text_layer_readiness_4961_parse_text_layer_later.csv` — 3,177;
- `combined_broad_pdf_text_layer_readiness_4961_html_text_later.csv` — 834;
- `combined_broad_pdf_text_layer_readiness_4961_other_document_text_later.csv` — 40.

The union must contain exactly 4,051 unique readiness IDs and must exclude OCR/defer, oversized, corrupt/unreadable, encrypted/locked, shell/navigation-only, unsupported, needs-review, and readiness-error rows.

## Local artifact resolution

Operational `retained_file_path` values remain resolvable under the original source-review run directory. Those payload paths are local-only and Git-ignored.

The independent local artifact copy is rooted at:

`artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/retained_sources/`

Resolve an artifact-copy path by preserving the relative suffix below the operational `retained_sources/` root. Validate size and SHA-256 before extraction. If neither operational nor artifact-copy path resolves and matches, fail closed; do not redownload.

## Parallel execution

Use exactly four isolated, checkpointed, resumable lanes with controlled overlap:

- extraction_lane_001: 1,013 rows, T+0;
- extraction_lane_002: 1,013 rows, T+8 minutes;
- extraction_lane_003: 1,013 rows, T+16 minutes;
- extraction_lane_004: 1,012 rows, T+24 minutes.

Workers write only to isolated lane-specific output and artifact-storage prefixes. The coordinator merges after lane completion and updates shared dashboard/status/docs once.

## Storage rule

Extracted full text is an artifact payload and must not enter normal Git history. Store text artifacts under an approved ignored/artifact-storage root. Git may track only extraction manifests, hashes, sizes, lineage, bounded exact-span pointers if separately authorized, summaries, errors, checkpoints, and storage pointers. Run the staged-file and ahead-history large-artifact gates before commit and push.

## Prohibitions

Do not OCR or render pages/images. Do not extract tables or evidence spans unless separately authorized. Do not rate evidence, call GABRIEL/API/model systems, ingest, codify, normalize or compare wages, calculate wage gaps, run regressions or treatment-effect models, estimate national/population prevalence, or make final causal claims.

Keep the dashboard map filtered only by cumulative total scout-covered municipalities. Keep global analysis readiness false. A successful local commit does not mean the public/dashboard state is updated; verify plain `git push` success before making that claim.

Before closing any future rating task, verify every downstream summary input exists. Deterministically reconstruct only fully derivable missing summary artifacts from committed valid/quarantine/results ledgers; missing non-derivable inputs fail closed.
