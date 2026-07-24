# Verification Scale Round 1 3×750 Live Collection Result Review

Date: 2026-07-24
Round: `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`
Disposition: **all three lanes completed; offline audit recommends `merge_all_verification_lanes`**

## Gates and launch

- Starting commit: `ee7041a47a047d40bbc83469e3aaea0cb1cb8000`.
- All three locked 750-row input hashes passed.
- Combined identities: 2,250 unique verification IDs and 2,250 unique queue
  IDs; zero cross-lane duplicates and zero exact-URL groups split across
  lanes.
- Three fresh dry runs passed 750/750 with zero URL opens/network calls.
- Known licensed/authenticated research-service hostname matches: zero.
- Exactly three live lanes launched; no fourth lane and no resume ran.

The coordinator confirmed a checkpoint ledger and lane-local artifact
directory before each next launch. At the Lane 1 gate, 45 rows were terminal
and 45 metadata artifacts existed. At the Lane 2 gate, 46 rows were terminal
and 46 metadata artifacts existed.

Filesystem creation and terminal-summary timestamps provide the most precise
persisted launch/runtime evidence:

| Lane | Output created UTC | Completed UTC | Runtime | Candidate rows/hour |
|---|---|---|---:|---:|
| 1 | 15:29:44.218 | 15:31:55 | 130.782 s | 20,645.059 |
| 2 | 15:31:56.052 | 15:33:44 | 107.948 s | 25,011.945 |
| 3 | 15:32:28.895 | 15:34:05 | 96.105 s | 28,094.183 |

Lane 1-to-2 creation spacing was 131.833 seconds; Lane 2-to-3 spacing was
32.843 seconds. The combined live wall interval was 260.782 seconds
(4m20.782s), for 31,060.438 candidate rows/hour or 30,950.001 logical
representative fetches/hour. These rates describe lightweight bounded
reachability/metadata checks, not document parsing or wage extraction.

## Per-lane results

| Status | Lane 1 | Lane 2 | Lane 3 | Combined |
|---|---:|---:|---:|---:|
| Candidate/terminal rows | 750 | 750 | 750 | 2,250 |
| Logical URL opens | 744 | 749 | 749 | 2,242 |
| Reachable PDF/document | 620 | 626 | 622 | 1,868 |
| Reachable HTML | 8 | 5 | 5 | 18 |
| Duplicate of reachable source | 2 | 0 | 0 | 2 |
| Duplicate same URL pending | 4 | 1 | 1 | 6 |
| Blocked/forbidden | 43 | 41 | 53 | 137 |
| Not found | 44 | 51 | 36 | 131 |
| Too large | 21 | 18 | 25 | 64 |
| Generic HTTP/client error | 6 | 5 | 7 | 18 |
| SSL error | 1 | 2 | 0 | 3 |
| Timeout | 0 | 1 | 1 | 2 |
| Connection error | 1 | 0 | 0 | 1 |

Reachable or successfully reused candidate rows total **1,888/2,250
(83.911%)**. The other 362 rows have explicit terminal routing statuses; they
are not silently dropped and do not become source or municipality failures in
scout accounting.

There were 257 redirecting rows. Content types recorded by the auditor are
1,934 `application/pdf`, 271 `text/html`, and 45 unknown. Content-type totals
include blocked, oversized, and otherwise non-reachable terminal outcomes and
therefore should not be equated with reachable-source counts.

Bytes-read buckets are:

- zero bytes: 359 rows;
- 1–64 KiB: 32;
- 64 KiB–1 MiB: 781; and
- 1–10 MiB: 1,078.

The lane-local artifact directories contain 2,221 JSON metadata files totaling
952,655 bytes. Maximum artifact size is 627 bytes. No HTML content sample or
full candidate document was saved.

## State routing summary

Reachable/reused versus other terminal rows:

`AK 12/6, CA 371/137, CT 33/7, DC 5/0, DE 8/0, HI 3/0, IA 34/8,
IL 197/21, KS 9/0, MA 80/7, ME 12/2, MI 103/12, MT 22/8, NE 18/4,
NH 15/4, NV 21/3, NY 58/17, OH 603/41, OR 62/35, RI 13/0, SD 15/6,
VT 6/0, WA 94/29, WI 94/15`.

These are verification routing outcomes, not measures of source quality,
contract availability, wages, mechanisms, or state performance.

## Audit and boundary

The offline auditor reports:

- three `completed_merge_eligible` lanes;
- 2,250/2,250 ledger and terminal rows;
- zero cross-lane duplicate verification IDs;
- eight duplicate-reuse rows;
- 2,242 URL opens/network calls;
- zero accounting mutations; and
- recommendation `merge_all_verification_lanes`.

That recommendation does not perform or authorize the durable ledger merge.
No scout queue, municipality/state/county coverage, dashboard, contract,
city-coverage, corpus, ingestion, codification, extraction, or analysis layer
was updated.

Next action: use
`verification_scale_round1_3x750_merge_prompt_2026-07-23.md` only under a
separate serial merge authorization.
