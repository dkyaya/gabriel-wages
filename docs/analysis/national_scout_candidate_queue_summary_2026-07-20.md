# National Scout Candidate Queue and Coverage Summary

Batch/output date: 2026-07-20

Last rebuilt: 2026-07-21

Stage: scout-output filtering, deferred-verification scheduling, and source-discovery coverage accounting only. No new source was independently opened, verified, downloaded, ingested, codified, canonicalized, or used as claim evidence during queue maintenance.

## Result

The durable national queue contains 540 URL-bearing candidate rows from PA, TX, MA, NJ, three Illinois state-scale runs, NY, CA25, and the serialized CA25.2/NJ25 recovery. Four hundred thirty-three are scheduled for later coordinated verification; 107 are preserved as context, duplicate, insufficient/rejected, or already-canonical holds. The IL25.3 handoff also preserves one parsed Rolling Meadows row without a source URL; it is not counted as a source-candidate queue row and no locator was inferred.

Successful scout coverage is 207 of the 35,589 authoritative municipal/township governments: PA 25, TX 3, MA 8, NJ 27, IL 74, NY 25, and CA 45. One hundred eighty-one produced candidates and 26 produced valid empty lists. Twenty-three failed attempts remain separately excluded: 16 MA connection-only requests later superseded by a successful rerun, Bloomington IL's failure-only timeout, five CA timeout-only rows including new Fairfield, and NJ Princeton. The serialized recovery added 48 covered municipalities and 89 candidate rows without counting either timeout as coverage.

## Queue totals

| State | Candidate rows | Queued later | Holds/rejections |
|---|---:|---:|---:|
| PA | 75 | 47 | 28 |
| TX | 6 | 2 | 4 |
| MA | 24 | 13 | 11 |
| NJ | 32 | 23 | 9 |
| IL | 217 | 182 | 35 |
| NY | 57 | 48 | 9 |
| CA | 129 | 118 | 11 |
| **Total** | **540** | **433** | **107** |

| Triage bucket | Rows |
|---|---:|
| `high_priority_later_verify` | 343 |
| `medium_priority_later_verify` | 59 |
| `low_priority_later_verify` | 31 |
| `context_only_hold` | 50 |
| `likely_duplicate_hold` | 13 |
| `insufficient_hold` | 34 |
| `rejected_from_calibration` | 2 |
| `already_canonical_hold` | 8 |

## Strongest apparent later-verification groups

These are metadata-only scheduling judgments, not source findings. CA25.2 adds apparent police/fire/civilian shapes for Glendale, Ontario, Oceanside, Corona, Roseville, Hayward, Pasadena, Santa Clara, Clovis, Richmond, San Luis Obispo, and Davis. NJ25 adds apparent three-unit shapes for Perth Amboy, Atlantic City, and Morristown, plus a Garfield police/civilian pair. CA25's San Diego, Fresno, Long Beach, Los Angeles, Chico, Anaheim, and Palo Alto groups remain visible, as do the strongest apparent IL/NY groups. Several new CA/NJ rows extend beyond or begin after 2024; deterministic triage lowers wholly post-window rows, and later verification must establish actual operative overlap. TX/MA findings retain only their explicitly labeled calibration status.

No CA25 URL exactly matched another URL in the run, the pre-run queue, or canonical contracts. Three CA rows self-label possible duplicate risk and remain holds. No IL25.3 URL exactly matched another URL in its run, prior queue, or canonical contracts. This local string deduplication is not source verification.

## Coverage

| State | Universe | Covered | With candidates | Empty | Failure-only | Not successfully covered | Queued rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PA | 2,557 | 25 | 23 | 2 | 0 | 2,532 | 47 |
| TX | 1,224 | 3 | 2 | 1 | 0 | 1,221 | 2 |
| MA | 351 | 8 | 8 | 0 | 0 | 343 | 13 |
| NJ | 564 | 27 | 15 | 12 | 1 | 537 | 23 |
| IL | 2,719 | 74 | 68 | 6 | 1 | 2,645 | 182 |
| NY | 1,523 | 25 | 21 | 4 | 0 | 1,498 | 48 |
| CA | 483 | 45 | 44 | 1 | 5 | 438 | 118 |
| **National** | **35,589** | **207** | **181** | **26** | **7** | **35,382** | **433** |

Thirteen covered municipalities overlap canonical corpus municipalities, while eight returned candidate URLs are already canonical or calibration-confirmed duplicates. Those are separate measures. IL25.3 adds no exact canonical candidate URL.

## Workflow

After each separately authorized live batch: require a fresh direct-SDK smoke; preserve raw and failure/usage artifacts; normalize every row as scout-stage; rebuild the queue; count parseable empty outputs as coverage while excluding connection-only failures; and defer coordinated verification until enough municipality-level bundles can be reviewed efficiently. Verification must establish employer, unit, official provenance, execution/completeness, operative dates, wage content, duplicates, and matched-cycle overlap before ingestion. Codification and claim use remain later stages.

Recommended next move: keep parallel preparation but retain one serialized smoke/live API lane. Do not treat this recovery as proof of parallel-live stability or move automatically to Stage 2. Do not retry Oakland, Stockton, Oxnard, Redding, Fairfield, or Princeton without separate authorization. A later task may select another untouched 25-row batch or a coordinated matched-set verification wave; verification and ingestion remain separate later stages.
