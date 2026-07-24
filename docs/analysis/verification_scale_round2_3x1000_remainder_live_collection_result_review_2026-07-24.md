# Verification Scale Round 2 3×1000 Remainder — Live Collection Result Review

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`  
Stage: bounded URL-routing collection and lane audit only; durable merge deferred

## Outcome

All offline readiness, identity, planning, dry-run, and dry-audit gates passed.
Exactly three nonempty live lanes then ran with the bounded verifier. All 2,476
selected rows reached terminal routing outcomes, all three lanes are
`completed_merge_eligible`, and the combined auditor recommends
`merge_all_verification_lanes`.

That recommendation is an audit result only. This task did not create or
update a durable Round 2 verification ledger.

## Selection boundary

The canonical input was
`docs/analysis/national_scout_candidate_queue_2026-07-20.csv`. Exact identity
subtraction used the 2,250-row durable Round 1 ledger at
`docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv`.

- URL-bearing queue rows: 4,726
- Round 1 identities excluded: 2,250
- exact Round 2 remainder selected: 2,476
- scheduled rows selected first: 1,350
- lower-disposition remainder selected second: 1,126
- unselected URL-bearing remainder: 0
- Round 1 queue identities rerun: 0
- duplicate Round 2 verification IDs: 0

Original candidate dispositions were retained:

| Candidate disposition | Rows |
|---|---:|
| scheduled | 1,350 |
| context_only_hold | 523 |
| insufficient_hold | 302 |
| likely_duplicate_hold | 291 |
| already_canonical_hold | 8 |
| calibration_reject | 2 |
| **Total** | **2,476** |

The lower-disposition rows remain candidate-routing records. Their inclusion
does not promote them to verified, ingested, codified, or analysis-ready
evidence.

## Locked lanes and health

| Lane | Input rows | SHA-256 | Logical URL opens | Reused rows | Runtime | Rows/hour |
|---|---:|---|---:|---:|---:|---:|
| Lane 1 | 826 | `ec60e33b9a79ffa7ad0dbabb43b490e3c9b2c338205722a3068269b980826bff` | 805 | 21 | 143.756 s | 20,685.094 |
| Lane 2 | 825 | `1c1e39c09fafd13f1eb4e2f914fc82ba716c0e548dd22a33dec8307788a03a04` | 795 | 30 | 130.393 s | 22,777.341 |
| Lane 3 | 825 | `2beb6fdb5857a6d8bea9ccee6e03992f7411c257ca86187d56210be92a2bc8fd` | 786 | 39 | 113.560 s | 26,153.526 |

Each process established its checkpoint ledger and lane-local artifact
directory before the next process launched. Exactly three lanes ran; there was
no fourth lane, retry, or resume. The overlapping live wall interval was
260.016 seconds (4m20.016s), producing an effective 34,280.976 selected
rows/hour and 33,034.899 logical fetches/hour.

All lanes retained the Round 1 safeguards: concurrency eight per lane,
20/8/15-second total/connect/read limits, five redirects, 10 MiB maximum
response size, disabled content samples, no environment proxy/auth
inheritance, incremental terminal ledgers, and lane-local metadata only.

## Terminal routing outcomes

| Status | Rows |
|---|---:|
| reachable_pdf_or_document | 1,665 |
| reachable_html | 127 |
| reachable_http | 2 |
| duplicate_of_verified_source | 68 |
| duplicate_same_url_pending | 22 |
| blocked_or_forbidden | 202 |
| not_found | 133 |
| too_large | 197 |
| error | 27 |
| ssl_error | 14 |
| timeout | 12 |
| connection_error | 7 |
| **Total** | **2,476** |

Reachable or successfully reused rows are the three reachable statuses plus
`duplicate_of_verified_source`: 1,862 / 2,476, or 75.2019%. There were 2,386
logical URL opens/network calls and 90 identity-preserving duplicate reuse
rows.

By original disposition, reachable/reused versus other terminal outcomes were:

| Disposition | Reachable/reused | Other terminal |
|---|---:|---:|
| scheduled | 1,126 | 224 |
| context_only_hold | 363 | 160 |
| likely_duplicate_hold | 242 | 49 |
| insufficient_hold | 121 | 181 |
| already_canonical_hold | 8 | 0 |
| calibration_reject | 2 | 0 |

These are routing results, not content-quality judgments.

## Response metadata and artifacts

Content types across all terminal rows:

| Content type | Rows |
|---|---:|
| application/pdf | 1,921 |
| text/html | 457 |
| unknown | 82 |
| application/xml | 5 |
| application/vnd.openxmlformats-officedocument.wordprocessingml.document | 4 |
| text/plain | 2 |
| text/xml | 2 |
| application/json | 1 |
| application/octet-stream | 1 |
| image/jpeg | 1 |

Bytes-read distribution:

| Range | Rows |
|---|---:|
| 0 bytes | 674 |
| 1–64 KiB | 123 |
| 64 KiB–1 MiB | 935 |
| 1–10 MiB | 744 |

The lanes wrote 2,330 small metadata JSON files totaling 993,431 bytes; the
largest is 979 bytes. Every nonblank ledger artifact path is lane-local and
resolves. No HTML content sample or full PDF/document was saved.

## State outcomes

Reachable/reused and other-terminal counts by state:

| State | Reachable/reused | Other terminal |
|---|---:|---:|
| AK | 8 | 3 |
| AL | 7 | 7 |
| AR | 7 | 9 |
| AZ | 20 | 9 |
| CA | 180 | 86 |
| CO | 22 | 3 |
| CT | 14 | 8 |
| DE | 7 | 2 |
| FL | 183 | 58 |
| GA | 6 | 1 |
| IA | 25 | 8 |
| ID | 16 | 4 |
| IL | 44 | 36 |
| IN | 46 | 12 |
| KS | 27 | 5 |
| KY | 17 | 1 |
| LA | 19 | 3 |
| MA | 52 | 22 |
| MD | 41 | 16 |
| ME | 28 | 4 |
| MI | 37 | 14 |
| MN | 103 | 28 |
| MO | 42 | 14 |
| MS | 11 | 1 |
| MT | 11 | 12 |
| NC | 15 | 2 |
| ND | 5 | 7 |
| NE | 8 | 1 |
| NH | 16 | 2 |
| NJ | 81 | 13 |
| NM | 31 | 10 |
| NV | 6 | 4 |
| NY | 55 | 9 |
| OH | 145 | 29 |
| OK | 18 | 3 |
| OR | 47 | 36 |
| PA | 83 | 19 |
| RI | 10 | 4 |
| SC | 2 | 1 |
| SD | 11 | 5 |
| TN | 22 | 6 |
| TX | 89 | 24 |
| UT | 29 | 8 |
| VA | 21 | 6 |
| VT | 6 | 3 |
| WA | 88 | 26 |
| WI | 80 | 25 |
| WV | 9 | 1 |
| WY | 12 | 4 |

## Audit and accounting boundary

The live auditor reports:

- Lane 1: `completed_merge_eligible`
- Lane 2: `completed_merge_eligible`
- Lane 3: `completed_merge_eligible`
- planned/ledger/terminal rows: 2,476 / 2,476 / 2,476
- cross-lane duplicate verification IDs: 0
- accounting mutations: 0
- recommendation: `merge_all_verification_lanes`

No durable Round 2 verification-routing ledger merge occurred. No scout
queue/coverage builder ran, and no scout accounting changed. No scout,
API/model/hosted-search call, ingestion, `gabriel.codify`, wage extraction,
wage-gap calculation or claim, causal claim, or regression occurred. The only
network activity was the explicitly authorized bounded URL verification
collection described above.

The next task is a separately authorized serial verification-ledger merge,
beginning with a fresh lane audit and preserving every original disposition.
