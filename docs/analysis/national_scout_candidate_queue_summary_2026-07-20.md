# National Scout Candidate Queue and Coverage Summary

Date: 2026-07-20

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was independently opened, verified, downloaded, ingested, codified, canonicalized, or used as claim evidence during queue maintenance.

## Result

The durable national queue contains 387 URL-bearing candidate rows from PA, TX, MA, NJ, three Illinois state-scale runs, and NY. Two hundred ninety-seven are scheduled for later coordinated verification; 90 are preserved as context, duplicate, insufficient/rejected, or already-canonical holds. The IL25.3 handoff also preserves one parsed Rolling Meadows row without a source URL; it is not counted as a source-candidate queue row and no locator was inferred.

Successful scout coverage is 138 of the 35,589 authoritative municipal/township governments: PA 25, TX 3, MA 8, NJ 3, IL 74, and NY 25. One hundred twenty-five produced candidates and 13 produced valid empty lists. Seventeen failed attempts remain separately excluded: 16 MA connection-only requests later superseded by a successful rerun and Bloomington IL's failure-only timeout.

## Queue totals

| State | Candidate rows | Queued later | Holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| IL | 217 | 182 | 35 |
| NY | 57 | 48 | 9 |
| **Total** | **387** | **297** | **90** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 226 |
| `medium_priority_later_verify` | 46 |
| `low_priority_later_verify` | 25 |
| `context_only_hold` | 44 |
| `likely_duplicate_hold` | 6 |
| `insufficient_hold` | 30 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

## Strongest apparent later-verification groups

These are metadata-only scheduling judgments, not source findings: Sycamore IL appears to have two police/fire/civilian sets (2015-2019 and 2023-2025); Lombard IL has two-cycle material with an apparent common 2019 boundary; Belvidere and Alton IL each appear to have 2022-2026 triads; East Moline and Ottawa IL have apparent overlapping sets; and Glenview, DeKalb, Rochester, Ithaca, Saratoga Springs, and Syracuse remain strong earlier groups. Downers Grove, Elmhurst, Mattoon, and Calumet City add apparent award/mechanism leads. TX/MA findings retain only their explicitly labeled calibration status.

No IL25.3 URL exactly matched another URL in the run, the pre-run queue, or canonical contracts. One St. Charles row self-labels possible duplicate risk and remains context-only. This local deduplication is not source verification.

## Coverage

| State | Universe | Covered | With candidates | Empty | Failure-only | Not successfully covered | Queued rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 0 | 561 | 5 |
| IL | 2,719 | 74 | 68 | 6 | 1 | 2,645 | 182 |
| NY | 1,523 | 25 | 21 | 4 | 0 | 1,498 | 48 |
| **National** | **35,589** | **138** | **125** | **13** | **1** | **35,451** | **297** |

Thirteen covered municipalities overlap canonical corpus municipalities, while eight returned candidate URLs are already canonical or calibration-confirmed duplicates. Those are separate measures. IL25.3 adds no exact canonical candidate URL.

## Workflow

After each separately authorized live batch: require a fresh direct-SDK smoke; preserve raw and failure/usage artifacts; normalize every row as scout-stage; rebuild the queue; count parseable empty outputs as coverage while excluding connection-only failures; and defer coordinated verification until enough municipality-level bundles can be reviewed efficiently. Verification must establish employer, unit, official provenance, execution/completeness, operative dates, wage content, duplicates, and matched-cycle overlap before ingestion. Codification and claim use remain later stages.

Recommended next move: prepare the next untouched state-scale 25-row batch—California remains a strong contrast candidate—using the authoritative universe and current coverage. Do not run it live without separate authorization and a new successful direct-SDK smoke.
