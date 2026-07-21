# National Scout Candidate Queue and Coverage Summary

Batch/output date: 2026-07-20

Last rebuilt: 2026-07-21

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was independently opened, verified, downloaded, ingested, codified, canonicalized, or used as claim evidence during queue maintenance.

## Result

The durable national queue contains 451 URL-bearing candidate rows from PA, TX, MA, NJ, three Illinois state-scale runs, NY, and CA25. Three hundred fifty-five are scheduled for later coordinated verification; 96 are preserved as context, duplicate, insufficient/rejected, or already-canonical holds. The IL25.3 handoff also preserves one parsed Rolling Meadows row without a source URL; it is not counted as a source-candidate queue row and no locator was inferred.

Successful scout coverage is 159 of the 35,589 authoritative municipal/township governments: PA 25, TX 3, MA 8, NJ 3, IL 74, NY 25, and CA 21. One hundred forty-five produced candidates and 14 produced valid empty lists. Twenty-one failed attempts remain separately excluded: 16 MA connection-only requests later superseded by a successful rerun, Bloomington IL's failure-only timeout, and four CA25 failure-only timeouts.

## Queue totals

| State | Candidate rows | Queued later | Holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 8 | 5 | 3 |
| IL | 217 | 182 | 35 |
| NY | 57 | 48 | 9 |
| CA | 64 | 58 | 6 |
| **Total** | **451** | **355** | **96** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 279 |
| `medium_priority_later_verify` | 49 |
| `low_priority_later_verify` | 27 |
| `context_only_hold` | 47 |
| `likely_duplicate_hold` | 9 |
| `insufficient_hold` | 30 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

## Strongest apparent later-verification groups

These are metadata-only scheduling judgments, not source findings: CA25 adds apparent matched-cycle groups for San Diego, Fresno, Long Beach, Los Angeles, Chico, Anaheim, and Palo Alto, with Berkeley and Santa Barbara touching at the 2024 boundary. Sycamore IL appears to have two police/fire/civilian sets; Lombard IL has two-cycle material; Belvidere, Alton, East Moline, and Ottawa retain apparent overlapping groups; and Glenview, DeKalb, Rochester, Ithaca, Saratoga Springs, and Syracuse remain strong earlier groups. TX/MA findings retain only their explicitly labeled calibration status.

No CA25 URL exactly matched another URL in the run, the pre-run queue, or canonical contracts. Three CA rows self-label possible duplicate risk and remain holds. No IL25.3 URL exactly matched another URL in its run, prior queue, or canonical contracts. This local string deduplication is not source verification.

## Coverage

| State | Universe | Covered | With candidates | Empty | Failure-only | Not successfully covered | Queued rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 3 | 3 | 0 | 0 | 561 | 5 |
| IL | 2,719 | 74 | 68 | 6 | 1 | 2,645 | 182 |
| NY | 1,523 | 25 | 21 | 4 | 0 | 1,498 | 48 |
| CA | 483 | 21 | 20 | 1 | 4 | 462 | 58 |
| **National** | **35,589** | **159** | **145** | **14** | **5** | **35,430** | **355** |

Thirteen covered municipalities overlap canonical corpus municipalities, while eight returned candidate URLs are already canonical or calibration-confirmed duplicates. Those are separate measures. IL25.3 adds no exact canonical candidate URL.

## Workflow

After each separately authorized live batch: require a fresh direct-SDK smoke; preserve raw and failure/usage artifacts; normalize every row as scout-stage; rebuild the queue; count parseable empty outputs as coverage while excluding connection-only failures; and defer coordinated verification until enough municipality-level bundles can be reviewed efficiently. Verification must establish employer, unit, official provenance, execution/completeness, operative dates, wage content, duplicates, and matched-cycle overlap before ingestion. Codification and claim use remain later stages.

Recommended next move: do not retry Oakland, Stockton, Oxnard, or Redding without separate authorization. Prepare another untouched state-scale 25-row batch with the authoritative universe/current coverage and require a fresh direct-SDK smoke, or select a coordinated municipality-bundle verification wave from the strongest apparent CA/IL/NY groups. Verification and ingestion remain separate later stages.
