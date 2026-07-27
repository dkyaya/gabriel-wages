# Next task: targeted Tier C PDF/text-layer readiness review over 463 retained sources

Use only the completed retained-source outputs from `DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27` and this readiness-preparation package. Expected retained scope: exactly 463 local files (397 PDF content-type files, 65 HTML files, and 1 octet-stream file), all already downloaded and hashed.

## Objective

Build and lock a 463-file readiness queue; verify every local path, recorded size, and SHA-256; preserve source/candidate/city/unit/cycle/mechanism/region lineage; keep PDF, HTML, and unsupported/ambiguous lanes separate; and classify whether each retained file can enter a later bounded local text-layer extraction pass.

Use controlled outcomes such as `text_layer_ready`, `html_text_ready`, `empty_or_too_short`, `low_text_density`, `suspected_bad_text_layer`, `html_noisy_or_shell`, `oversized_for_text_pass`, `ocr_later`, `corrupt_or_unreadable`, `unsupported_content_type`, and `needs_review`. Preserve all exclusions and duplicate relationships.

## Hard boundaries

- Do not fetch, pull, or inspect/configure remotes.
- Do not open URLs or redownload any source.
- Do not access or render PDF pages as images.
- Do not run OCR.
- Do not extract evidence spans, rate evidence, call GABRIEL/API/models, ingest, or codify.
- Do not normalize or compare quantitative values.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make national/population/final causal claims.
- Do not mutate predecessor inputs or durable ledgers.
- Keep every file not extracted, not rated, not ingested, not codified, non-causal, and globally not analysis-ready.
- Global analysis readiness remains false.
- Keep all new outputs under `docs/analysis`.

Fail closed if the retained queue is not exactly 463, a local path/hash mismatch occurs, any predecessor input is mutated, or a forbidden action would be required. The next decision should state whether a later bounded text-layer extraction pass is ready and identify all deferred/OCR-later/unsafe files explicitly.
