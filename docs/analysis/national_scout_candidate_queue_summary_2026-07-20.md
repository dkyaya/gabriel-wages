# National Scout Candidate Queue and Coverage Summary

Date: 2026-07-20

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new URL was opened, no PDF was downloaded, and no source was newly verified, ingested, codified, added to canonical coverage, or used as claim evidence.

## Plain-English result

The project now has one durable national candidate queue instead of separate state files that invite immediate source-by-source verification. It contains all 113 preserved candidate rows from the final Pennsylvania pilot/batch, Texas, the successful Massachusetts rerun, and New Jersey. Sixty-seven rows are queued for a later coordinated verification wave; 46 are held as context, likely duplicates, insufficient/rejected findings, or already canonical material.

Scout coverage is now calculated against the full 35,589-government municipality/township universe. Thirty-nine municipalities are source-discovery covered: 25 in Pennsylvania, 3 in Texas, 8 in Massachusetts, and 3 in New Jersey. Thirty-six produced candidates; Austin and two PA municipalities produced successful parseable empty results. Sixteen Massachusetts connection-only request attempts are recorded but excluded from discovery coverage; the later successful rerun supplies MA coverage.

Deep verification is being deferred because the immediate goal is national pattern discovery, not completing ingestion one document at a time. Texas and Massachusetts verification passes remain valuable calibration exercises: they identified wrong-unit context, document-state errors, cycle mistakes, context-only locators, and canonical duplicates. Their findings improve ranking, but they are explicitly labeled calibration findings rather than final project-wide verification.

## Queue totals

| State | Candidate rows | Queued for later verification | Other holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| **Total** | **113** | **67** | **46** |

Triage buckets:

| Bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 33 |
| `medium_priority_later_verify` | 15 |
| `low_priority_later_verify` | 19 |
| `context_only_hold` | 33 |
| `likely_duplicate_hold` | 2 |
| `insufficient_hold` | 1 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

The 33/15/19 priority labels schedule later work; they do not assert source truth. Pennsylvania's 75 legacy rows have no completed calibration and are still model output. New Jersey's eight rows remain unverified scout output. Only prior TX/MA ledger findings influence calibration columns.

## Highest-value later verification groups

The queue should be selected in matched groups rather than by opening the highest-scoring URL in isolation:

1. **Jersey City NJ:** police and fire successor leads are high priority; the ordinary-civilian Local 246 lead is held for duplicate review. Together they may form a 2021-2022 overlap, but no leg is newly verified here.
2. **Camden NJ:** Local 788 fire 2021-2024 and CWA Local 1014 civilian 2022-2025 form a promising apparent 2022-2024 pair. The Local 2578 consent award is a likely-duplicate/unit-identity hold, and no police leg was returned.
3. **Seekonk MA calibration set:** police and calibration-corrected fire material around 2019-2022 plus library 2020-2023 is the strongest previously calibrated matched set. Two 2022-2025 safety URLs are already canonical and are held.
4. **Houston TX calibration set:** the full City-hosted HOPE 2015-2018 agreement is the strongest ordinary-civilian lead; the HPOU 2015-2018 police agreement remains provenance-incomplete. The later HOPE cover and fire settlement memo are context only.
5. **Worcester/Boston MA calibration leads:** Worcester's police award/MOA and Boston's fire agreement/MOA are later-ingestion candidates from calibration, but they still need coordinated pre-ingestion matching decisions rather than immediate ingestion.
6. **PA matched-set clusters:** the legacy PA queue contains multiple high/medium city, union, CBA, and award leads. Because PA has not received a comparable verification calibration, later waves should select complete municipality-level police/fire/non-safety groups and first remove exact/likely duplicates and out-of-window cycles.

Newark's 2017-2023 fire Legistar record remains `context_only_hold`: it is a useful locator but not an inspected executed fire agreement. The queue does not treat it as canonical repair.

## What came from calibration

The TX/MA calibration ledgers cover 30 parsed scout rows in the queue: all 6 TX rows and all 24 MA rows.

- Eight rows carry prior `later_ingest_candidate` recommendations: Houston HOPE plus seven MA sources. They are labeled `verified_later_ingest_candidate` only as calibration-stage findings.
- Seven MA rows are calibration-confirmed duplicate/superseded canonical sources and are held.
- Five rows are verified context-only material: two TX and three MA.
- The San Antonio fire agreement returned under `non_safety` and the unsupported Municode interpretation are `rejected_from_calibration`.
- One Newton row remains calibration-unreachable/insufficient.
- Other verified or partially verified TX/MA rows stay queued according to match value, access, completeness, and the calibration next action.

No calibration finding was promoted to canonical source verification, ingestion, codification, or claim support during this task.

## National scout coverage

| State | Universe | Scout-covered | With candidates | Successful no-candidate | Remaining unscouted | Queued candidate rows |
|---|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 561 | 5 |
| **National** | **35,589** | **39** | **36** | **3** | **35,550** | **67** |

Thirteen scout-covered municipalities already have at least one canonical contract row: PA 1, TX 3, MA 8, and NJ 1. That municipality-level overlap does not mean every returned candidate is canonical. At candidate level, eight returned URLs are held as already canonical: one PA row and seven MA rows.

The prior calibration ledgers identify eight later-ingestion candidates—one TX and seven MA—but ingestion remains deferred. Massachusetts has 16 failed connection attempts recorded and excluded from coverage; all eight affected municipalities are counted only because the later rerun succeeded.

## Workflow going forward

After each separately authorized live batch:

1. Require a fresh synthetic no-search smoke preflight. For the HUIT proxy, prefer the direct-SDK backend because it bypasses the unreliable GABRIEL wrapper probe while preserving the scout parser/artifact pipeline.
2. Preserve raw outputs, prompt preview, run metadata, usage/cost, parsed candidates, and failure ledgers.
3. Add candidate rows to the durable queue without opening every URL.
4. Apply only scout metadata and existing calibration findings for light triage.
5. Update municipality/state/county scout coverage, including parseable empty results and excluding connection-only failures.
6. Continue national scouting through strategically chosen claim, regime, geography, and matched-repair slices.
7. Select later verification waves from high-value municipality-level sets, not one-off URLs.
8. Ingest only after verification establishes employer, unit, provenance, execution/completeness, dates, wage content, duplicates, and matched-cycle value.

Scout coverage answers "did a bounded discovery prompt complete?" Verification coverage answers "did the returned source prove what the row claims?" Ingestion coverage answers "is a provenance-complete document represented in the canonical corpus?" Codified coverage answers "has the ingested evidence been measured under the codification contract?" Claim coverage answers "does verified/codified evidence bear on a registered claim?" Treating those as one status would recreate the very leakage the queue is designed to prevent.

## Recommended next scout slice

Do not launch it without separate authorization. The next small national slice should be Illinois—Chicago, Aurora, and Rockford—the next three untouched `ready_for_scout` claim-register targets in the existing manifest. Prepare a full-context input with exact employer, known-source/cycle exclusions, and matched-unit objectives; run a fresh direct-SDK synthetic preflight; then use serial, zero-retry direct-SDK scouting if authorized. Queue and account for the output immediately, but defer deep verification until a coordinated wave can compare the strongest Illinois municipality-level sets against the existing queue.
