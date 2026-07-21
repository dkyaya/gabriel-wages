# National Scout Candidate Queue and Coverage Summary

Date: 2026-07-20

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was independently opened, verified, downloaded, ingested, codified, canonicalized, or used as claim evidence during queue maintenance.

## Result

The durable national queue contains 318 candidate rows from PA, TX, MA, NJ, two Illinois state-scale runs, and NY. Two hundred thirty-nine are scheduled for later coordinated verification; 79 are preserved as context, duplicate, insufficient/rejected, or already-canonical holds.

Successful scout coverage is 113 of the 35,589 authoritative municipal/township governments: PA 25, TX 3, MA 8, NJ 3, IL 49, and NY 25. One hundred two produced candidates and 11 produced valid empty lists. Seventeen failed attempts remain separately excluded: 16 MA connection-only requests later superseded by a successful rerun and Bloomington IL's failure-only timeout.

## Queue totals

| State | Candidate rows | Queued later | Holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| IL | 148 | 124 | 24 |
| NY | 57 | 48 | 9 |
| **Total** | **318** | **239** | **79** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 173 |
| `medium_priority_later_verify` | 43 |
| `low_priority_later_verify` | 23 |
| `context_only_hold` | 43 |
| `likely_duplicate_hold` | 6 |
| `insufficient_hold` | 20 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

## Strongest apparent later-verification groups

These are metadata-only scheduling judgments, not source findings: Glenview IL appears to have a 2023-2026 police/fire/civilian overlap; DeKalb IL an apparent 2017-2019 overlap; Carpentersville IL a possible 2023-2024 overlap pending the supposed civilian unit's identity; Rock Island IL a possible 2025-2026 overlap; and Rochester, Ithaca, Saratoga Springs, and Syracuse NY remain strong earlier groups. Downers Grove and Elmhurst add apparent arbitration/mechanism leads. TX/MA findings retain only their explicitly labeled calibration status.

No IL25.2 exact URL matched another URL in the run, the pre-run queue, or canonical contracts. This local deduplication is not source verification.

## Coverage

| State | Universe | Covered | With candidates | Empty | Failure-only | Not successfully covered | Queued rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 0 | 561 | 5 |
| IL | 2,719 | 49 | 45 | 4 | 1 | 2,670 | 124 |
| NY | 1,523 | 25 | 21 | 4 | 0 | 1,498 | 48 |
| **National** | **35,589** | **113** | **102** | **11** | **1** | **35,476** | **239** |

Thirteen covered municipalities overlap canonical corpus municipalities, while eight returned candidate URLs are already canonical or calibration-confirmed duplicates. Those are separate measures. The second Illinois run adds no exact canonical candidate URL.

## Workflow

After each separately authorized live batch: require a fresh direct-SDK smoke; preserve raw and failure/usage artifacts; normalize every row as scout-stage; rebuild the queue; count parseable empty outputs as coverage while excluding connection-only failures; and defer coordinated verification until enough municipality-level bundles can be reviewed efficiently. Verification must establish employer, unit, official provenance, execution/completeness, operative dates, wage content, duplicates, and matched-cycle overlap before ingestion. Codification and claim use remain later stages.

Recommended next move: prepare the next untouched state-scale 25-row batch—California remains a strong contrast candidate—using the authoritative universe and current coverage. Do not run it live without separate authorization and a new successful direct-SDK smoke.
