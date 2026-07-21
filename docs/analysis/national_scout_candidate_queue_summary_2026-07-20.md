# National Scout Candidate Queue and Coverage Summary

Date: 2026-07-20

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was opened, downloaded, verified, ingested, codified, added to canonical coverage, or used as claim evidence during queue maintenance.

## Plain-English result

The durable national queue now contains all 246 preserved candidate rows from Pennsylvania, Texas, Massachusetts, New Jersey, Illinois, and New York. One hundred eighty-three rows are scheduled for later coordinated verification; 63 are retained as context, duplicate, insufficient/rejected, or already-canonical holds.

Scout coverage is calculated against the full 35,589-government municipality/township universe. Eighty-eight municipalities are successfully source-discovery covered: 25 PA, 3 TX, 8 MA, 3 NJ, 24 IL, and 25 NY. Eighty produced candidates; eight produced valid parseable empty outputs. Seventeen failed request attempts remain separately recorded and excluded: 16 MA connection-only rows later superseded by a successful rerun, plus Bloomington IL's failure-only timeout.

Deep verification remains deferred. TX and MA verification were calibration exercises that improved triage; no NY, IL, NJ, or PA output was newly verified. Scout, calibration, verification, ingestion, canonical, codified, and claim statuses remain distinct.

## Queue totals

| State | Candidate rows | Queued for later verification | Other holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| IL | 76 | 68 | 8 |
| NY | 57 | 48 | 9 |
| **Total** | **246** | **183** | **63** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 124 |
| `medium_priority_later_verify` | 36 |
| `low_priority_later_verify` | 23 |
| `context_only_hold` | 40 |
| `likely_duplicate_hold` | 3 |
| `insufficient_hold` | 10 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

The 124/36/23 priority labels schedule later work; they do not establish source truth. All 57 NY, 76 IL, and 8 NJ rows remain unverified model output. Only the prior TX/MA ledgers influence calibration fields.

## Highest-value later verification groups

Verification waves should select matched municipality groups, not the highest-scoring URL in isolation:

1. **Rochester NY:** apparent police 2019-2024, fire 2021-2026, and AFSCME 2022-2027 agreements suggest mutual overlap in 2022-2024, plus a possible successor police agreement.
2. **Ithaca NY:** apparent police, fire, and civilian agreements suggest a 2021-2024 overlap and a police successor mechanism through 2026.
3. **Saratoga Springs NY:** apparent police, fire, DPW, and City Hall material suggests a 2019-2021 matched period.
4. **Syracuse NY:** police award/MOA material plus apparent full fire and CSEA agreements suggest a mechanism-focused 2018-2019 group, although a police base agreement is not yet established.
5. **Rockford IL:** apparent 2023-2025 police, 2022-2026 fire, and 2022-2025 AFSCME material form a strong model-described 2023-2025 overlap.
6. **Springfield, Joliet, Bolingbrook, and Decatur IL:** these remain the strongest apparent Illinois groups, subject to Joliet locator deduplication and exact unit/document review.
7. **Jersey City and Camden NJ:** Jersey City's possible 2021-2022 three-unit group and Camden's fire/civilian pair remain high-value gap-filling leads.
8. **Seekonk MA and Houston TX calibration groups:** retain their existing calibration-stage value without treating those findings as final verification or ingestion approval.

New York City is a narrow legacy-overlap locator group rather than a current matched set. Poughkeepsie needs blocked-access resolution; Auburn's safety and civilian rows are adjacent, not mutually overlapping; Kingston's civilian row is a multi-union premium MOA. Those limitations keep high raw triage scores from being mistaken for verified matched sets.

## Calibration carried forward

The existing TX/MA calibration ledgers cover 30 queue rows: all 6 TX and all 24 MA rows.

- Eight rows retain prior `later_ingest_candidate` recommendations: one TX and seven MA. This is a calibration-stage scheduling status, not ingestion.
- Seven MA duplicate/superseded rows plus one exact PA URL are held as already canonical.
- Five rows are prior verified context-only material: two TX and three MA.
- The San Antonio safety-as-non-safety row and unsupported Municode interpretation remain rejected.
- One Newton row remains calibration-unreachable/insufficient.

No calibration finding was promoted during the NY run or queue rebuild. New York contributes no calibration-verified or later-ingestion-approved row.

## National scout coverage

| State | Universe | Scout-covered | With candidates | Successful no-candidate | Failure-only municipalities | Not successfully covered | Queued candidate rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 0 | 561 | 5 |
| IL | 2,719 | 24 | 23 | 1 | 1 | 2,695 | 68 |
| NY | 1,523 | 25 | 21 | 4 | 0 | 1,498 | 48 |
| **National** | **35,589** | **88** | **80** | **8** | **1** | **35,501** | **183** |

`Not successfully covered` includes untouched municipalities and any failure-only municipality. Thus Illinois still includes Bloomington's failed-only row. The national municipality CSV preserves that status separately from `not_scouted`.

Thirteen covered municipalities already have at least one canonical contract row: PA 1, TX 3, MA 8, NJ 1, IL 0, and NY 0. At candidate level, eight returned URLs are already canonical/confirmed duplicates: PA 1 and MA 7. Municipality overlap and candidate duplication are different measures. The NY run adds no exact canonical or pre-existing queue URL overlap.

MA's 16 connection-error request rows do not add coverage, although the later successful rerun covers all eight affected municipalities. Bloomington's zero-response timeout remains excluded. The four NY parseable empty responses count as discovery coverage but do not prove that sources do not exist.

## Workflow going forward

After each separately authorized live batch:

1. Require a fresh synthetic no-search direct-SDK smoke preflight for HUIT.
2. Preserve prompt, metadata, raw output, parsed/failed rows, failure ledger, and usage/cost artifacts.
3. Add candidate rows to the durable queue without opening every URL.
4. Apply only scout metadata and completed calibration notes for light triage.
5. Update municipality/state/county coverage, counting parseable empty results and excluding failure-only attempts.
6. Continue strategic state-scale scouting before scheduling coordinated verification waves.
7. Verify complete municipality-level matched sets and mechanism bundles rather than isolated links.
8. Ingest only after employer, unit, provenance, execution/completeness, dates, wage content, duplicate, and match checks pass.

Scout coverage answers whether a bounded discovery prompt completed. Verification coverage asks whether the returned source proves its modeled description. Ingestion coverage asks whether a provenance-complete document is represented canonically. Codified and claim coverage are still later stages. Keeping these separate prevents discovery output from becoming evidence by accident.

## Recommended next scout slice

Do not launch another scout without separate authorization and a fresh direct-SDK smoke preflight. The next preparation task should consider a locked California 25-city dry-run batch: Los Angeles and Sacramento are the next untouched manifest anchors, and California provides strong institutional and geographic contrast after Illinois and New York. Selection must still use the authoritative universe and current coverage, exclude non-municipal employers, and undergo dry-run prompt review before any live authorization.
