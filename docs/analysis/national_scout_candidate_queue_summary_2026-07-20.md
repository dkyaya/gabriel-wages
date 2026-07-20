# National Scout Candidate Queue and Coverage Summary

Date: 2026-07-20

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was opened, downloaded, verified, ingested, codified, added to canonical coverage, or used as claim evidence during queue maintenance.

## Plain-English result

The durable national queue now contains all 189 preserved candidate rows from Pennsylvania, Texas, Massachusetts, New Jersey, and the Illinois IL25 run. One hundred thirty-five rows are scheduled for later coordinated verification; 54 are retained as context, duplicate, insufficient/rejected, or already-canonical holds.

Scout coverage is calculated against the full 35,589-government municipality/township universe. Sixty-three municipalities are successfully source-discovery covered: 25 PA, 3 TX, 8 MA, 3 NJ, and 24 IL. Fifty-nine produced candidates; Austin, two PA municipalities, and Champaign IL produced valid parseable empty outputs. Seventeen failed request attempts are separately recorded and excluded: 16 MA connection-only rows later superseded by a successful rerun, plus Bloomington IL's failure-only timeout.

Deep verification remains deferred. TX and MA verification were calibration exercises that improved triage; no IL, NJ, or PA output was newly verified. Scout, calibration, verification, ingestion, canonical, codified, and claim statuses remain distinct.

## Queue totals

| State | Candidate rows | Queued for later verification | Other holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| IL | 76 | 68 | 8 |
| **Total** | **189** | **135** | **54** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 91 |
| `medium_priority_later_verify` | 25 |
| `low_priority_later_verify` | 19 |
| `context_only_hold` | 35 |
| `likely_duplicate_hold` | 2 |
| `insufficient_hold` | 7 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

The 91/25/19 priority labels schedule later work; they do not establish source truth. All 76 IL rows and all 8 NJ rows remain unverified model output. Only the prior TX/MA ledgers influence calibration fields.

## Highest-value later verification groups

Verification waves should select matched municipality groups, not the highest-scoring URL in isolation:

1. **Rockford IL:** apparent 2023-2025 police, 2022-2026 fire, and 2022-2025 AFSCME material form a strong model-described 2023-2025 overlap.
2. **Springfield IL:** apparent police 2022-2026, fire 2021-2025, and IUOE/CWLP 2020-2025 material form a potential 2022-2025 set, with an additional police-award mechanism lead.
3. **Joliet and Bolingbrook IL:** apparent matched groups cover roughly 2020-2024 and 2020-2023, respectively. Joliet needs explicit within-run locator deduplication; Bolingbrook's six rows need unit and document reconciliation.
4. **Decatur IL:** apparent police/fire/civilian overlap in 2023-2024 plus a later fire-award mechanism lead.
5. **Jersey City NJ:** police/fire successor and ordinary-civilian leads may overlap in 2021-2022; the Local 246 row needs duplicate review.
6. **Camden NJ:** apparent fire 2021-2024 and civilian 2022-2025 material form a promising pair. No police leg was returned; Local 2578 versus Local 788 requires unit reconciliation.
7. **Seekonk MA calibration set:** police and calibration-corrected fire material around 2019-2022 plus library 2020-2023 remains the strongest already-calibrated group. Two newer safety URLs are already canonical and held.
8. **Houston TX calibration set:** the City-hosted HOPE 2015-2018 agreement is the strongest ordinary-civilian lead; HPOU police provenance remains incomplete.
9. **Worcester/Boston MA and PA clusters:** the calibrated MA mechanism leads and uncalibrated PA municipality groups remain candidates for coordinated rather than piecemeal review.

Chicago's apparent 2012-2017 triad is a blocked legacy locator set, not a verified current-cycle match. Aurora returned fire plus police-management context but no ordinary-civilian leg. Those limitations keep the claim anchors from being overstated.

## Calibration carried forward

The existing TX/MA calibration ledgers cover 30 queue rows: all 6 TX and all 24 MA rows.

- Eight rows retain prior `later_ingest_candidate` recommendations: one TX and seven MA. This is a calibration-stage scheduling status, not ingestion.
- Seven MA duplicate/superseded rows plus one exact PA URL are held as already canonical.
- Five rows are prior verified context-only material: two TX and three MA.
- The San Antonio safety-as-non-safety row and unsupported Municode interpretation remain rejected.
- One Newton row remains calibration-unreachable/insufficient.

No calibration finding was promoted during the Illinois run or queue rebuild. Illinois contributes no calibration-verified or later-ingestion-approved row.

## National scout coverage

| State | Universe | Scout-covered | With candidates | Successful no-candidate | Failure-only municipalities | Not successfully covered | Queued candidate rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 0 | 561 | 5 |
| IL | 2,719 | 24 | 23 | 1 | 1 | 2,695 | 68 |
| **National** | **35,589** | **63** | **59** | **4** | **1** | **35,526** | **135** |

`Not successfully covered` includes untouched municipalities and any failure-only municipality. Thus Illinois has 2,694 `not_scouted` rows plus Bloomington's one failed-only row. The national municipality CSV preserves those two states separately.

Thirteen covered municipalities already have at least one canonical contract row: PA 1, TX 3, MA 8, NJ 1, and IL 0. At candidate level, eight returned URLs are already canonical/confirmed duplicates: PA 1 and MA 7. Municipality overlap and candidate duplication are different measures.

MA's 16 connection-error request rows do not add coverage, although the later successful rerun covers all eight affected municipalities. Bloomington's zero-response timeout is recorded once and excluded. Champaign's valid empty response does count as discovery coverage but does not prove no source exists.

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

Do not launch another scout without separate authorization and a fresh direct-SDK smoke preflight. The next state-scale slice should come from the untouched high-priority national manifest, using the IL25 operating pattern: full-context locked municipal rows, serial zero-retry execution, immediate queue/coverage rebuild, and deferred verification. Select a state with a useful mix of claim anchors and municipal labor-source availability; do not retry Bloomington as an unannounced extra call.
