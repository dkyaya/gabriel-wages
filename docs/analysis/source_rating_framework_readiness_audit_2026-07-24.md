# Source-Rating Framework Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The repository was ready for an offline source-rating and bounded
content-review pilot framework.

- Starting commit: `79df80c94b2676d3a5e05f50b0a2075bdfc0563b`
- Tracked worktree at start: clean
- Unrelated untracked item: `package-lock.json` (left untouched and excluded)
- Required ancestry: all requested commits are ancestors of `HEAD`

No source-rating ledger, source download, content review, extraction, ingestion,
codification, wage calculation, or regression output existed at the start.

## Canonical inputs used

- Durable metadata-triage ledger:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`
- Durable metadata-triage summary:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_summary_cumulative.json`
- Cumulative routing ledger:
  `docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`
- Candidate queue:
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`

The metadata-triage ledger contains 4,726 rows, 4,726 unique triage IDs, and
4,726 unique candidate-queue identities. Its merge audit records exact
candidate identity equality with the cumulative routing ledger.

Baseline SHA-256 values:

- metadata-triage ledger:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`
- routing ledger:
  `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`

## Full metadata-triage workload

Content-review priority:

| Preliminary scheduling priority | Rows |
|---|---:|
| `p1` | 1,760 |
| `p2` | 1,232 |
| `p3` | 360 |
| `defer` | 1,372 |
| `exclude` | 2 |

Recommended action:

| Metadata-only action | Rows |
|---|---:|
| `content_review_download_allowed_later` | 2,923 |
| `metadata_review_only` | 437 |
| `duplicate_group_review` | 295 |
| `oversized_strategy_later` | 261 |
| `blocked_status_review_later` | 603 |
| `manual_review` | 205 |
| `exclude_for_now` | 2 |

These are preliminary scheduling fields. In particular,
`content_review_download_allowed_later` is not evidence that a source is
official, relevant, correctly matched, extractable, or wage-bearing.

## p1 pilot pool

The p1/download-allowed pool contains 1,760 rows across 44 states and 889
municipalities. Its inherited metadata is deliberately homogeneous at the
main gates:

- original disposition: 1,760 `scheduled`;
- candidate priority: 1,760 `high`;
- candidate source type: 1,760 `cba`;
- routing status: 1,760 `reachable_pdf_or_document`; and
- routed content type: 1,760 `application/pdf`.

Other committed signals:

- source owner type: city 1,171; state labor board 514; union 47;
  third party 22; unknown/legacy placeholder 6;
- unit type scouted: police 773; fire 428; non-safety 559;
- likely-official domain signal: 1,736; unknown: 24;
- matched-set potential: yes 1,555; no 205; and
- duplicate groups with more than one row: 13 rows.

Largest p1 state pools are OH 517, CA 230, IL 177, FL 104, MI 94, WA 70,
MA 61, OR 55, WI 50, and MN 40. These values describe workload metadata,
not source-content findings.

## Deferred and special-handling pools

- Duplicate-deferred: 295
- Oversized: 261
- Blocked/not-found routing defer: 603
- Manual review: 205
- Final metadata exclusions: 2

The pilot excludes these pools. Duplicate decisions require canonical-group
review; oversized documents need separate byte and concurrency controls; and
blocked, missing, and error routing outcomes are not proof that a municipality
lacks a useful source.

## Why rating precedes ingestion and extraction

URL routing proves only that a locator produced a bounded response or reuse
outcome. Metadata triage schedules attention but never inspects source
content. A content-based rating layer is therefore necessary to establish,
before ingestion or extraction:

1. whether the source is official or otherwise reliable;
2. whether it concerns the intended municipality, employer, and bargaining
   unit;
3. which document type and period it actually covers;
4. whether a usable text layer or table structure exists; and
5. which downstream extraction mode is appropriate.

Skipping these gates would turn candidate labels into unsupported evidence
claims and would waste extraction effort on wrong-employer, duplicate,
context-only, or technically unsuitable sources.

## Why the first pilot is 150 rows

A 150-row pilot is large enough to span the 44-state p1 pool, several source
owners, safety and non-safety units, and likely matched sets. It is small
enough to audit downloads, hashes, page/text-layer metadata, reviewer
consistency, false-positive source labels, and artifact handling before
scaling to all 1,760 p1 rows or all 2,923 download-allowed-later rows.

The pilot framework itself remains offline. This audit, planning work, and
subsequent dry runs opened zero URLs, made zero network/API/model calls,
downloaded and parsed zero documents, ran zero OCR jobs, and performed no
scouting, source rating, ingestion, codification, wage extraction, wage-gap
analysis, causal analysis, or regression.
