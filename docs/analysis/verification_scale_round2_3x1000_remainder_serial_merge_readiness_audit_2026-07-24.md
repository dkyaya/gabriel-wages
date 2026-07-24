# Verification Scale Round 2 3×1000 Remainder — Serial Merge Readiness Audit

Date: 2026-07-24
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`
Starting commit: `e86abf760d40a037713dcf53db2a1becdede09c9`

## Repository and lineage

- The tracked worktree was clean before work.
- The unrelated untracked root `package-lock.json` was reported and left
  untouched.
- Current `HEAD` descends from `e86abf7`, `2bab4b0`, `642dbda`, `ee7041a`,
  `3616bae`, and `98ad608`.
- No Round 2 durable ledger directory or cumulative project-wide ledger
  existed before this task.

## Locked inputs and fresh audit

| Lane | Rows | SHA-256 | Classification |
|---|---:|---|---|
| Lane 1 | 826 | `ec60e33b9a79ffa7ad0dbabb43b490e3c9b2c338205722a3068269b980826bff` | `completed_merge_eligible` |
| Lane 2 | 825 | `1c1e39c09fafd13f1eb4e2f914fc82ba716c0e548dd22a33dec8307788a03a04` | `completed_merge_eligible` |
| Lane 3 | 825 | `2beb6fdb5857a6d8bea9ccee6e03992f7411c257ca86187d56210be92a2bc8fd` | `completed_merge_eligible` |

The fresh offline audit command was:

```bash
python scripts/audit_verification_lanes.py \
  --manifest docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verification_round_manifest.json \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/serial_merge_lane_audit_2026-07-24
```

It reports:

- planned / ledger / terminal rows: 2,476 / 2,476 / 2,476;
- cross-lane duplicate verification IDs: 0;
- accounting mutations: 0;
- URL opens and network calls from the completed live round: 2,386 / 2,386;
- duplicate reuse/link rows: 90; and
- recommendation: `merge_all_verification_lanes`.

Combined status counts are:

| Routing status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 1,665 |
| `reachable_html` | 127 |
| `reachable_http` | 2 |
| `duplicate_of_verified_source` | 68 |
| `duplicate_same_url_pending` | 22 |
| `blocked_or_forbidden` | 202 |
| `not_found` | 133 |
| `too_large` | 197 |
| `error` | 27 |
| `ssl_error` | 14 |
| `timeout` | 12 |
| `connection_error` | 7 |

## Identity and disposition boundary

The canonical URL-bearing queue contains 4,726 unique `queue_id` values.
Round 1 durably routes 2,250 unique queue identities. Round 2 contains 2,476
unique queue identities and verification IDs:

- Round 1 / Round 2 queue-ID overlap: 0;
- Round 1 plus Round 2 identity union: 4,726;
- canonical URL-bearing identities outside that union: 0; and
- Round 2 verification-ID duplicates: 0.

Round 2 preserves the original dispositions exactly:

| Original disposition | Rows |
|---|---:|
| `scheduled` | 1,350 |
| `context_hold` | 523 |
| `insufficient_hold` | 302 |
| `duplicate_hold` | 291 |
| `already_canonical` | 8 |
| `calibration_rejected` | 2 |

These labels remain routing provenance. The serial merge will not upgrade
held, context, duplicate, canonical, or calibration-rejected candidates into
high-quality, ingested, codified, or analysis-ready evidence.

## Artifacts and stage boundary

- nonblank artifact references: 2,416;
- unique lane-local metadata files: 2,330;
- missing or out-of-lane artifact paths: 0;
- content samples: 0;
- full documents added: 0; and
- secret/credential-shaped metadata findings: 0.

The pre-merge test suite now verifies cumulative pointer behavior: the
round-specific Round 2 ledger remains 2,476 rows, while cumulative and latest
outputs retain prior Round 1 rows and add Round 2 without identity overlap.
All ten offline/mock verification tests pass with zero external calls.

No scout queue, coverage, or dashboard/accounting builder has consumed the
Round 2 live outputs as scout evidence. No ingestion, codification, wage
extraction, wage-gap, causal, or regression output was created from this
round.

## Decision

**PASS.** The serial merge may proceed exactly once. It is authorized to
create the Round 2 durable routing ledger, a 4,726-row cumulative routing
ledger, cumulative/latest summaries, and verification-only dashboard status.
It will not open URLs, make a network/API/model call, change scout accounting,
ingest or codify a source, extract wages, calculate a wage gap, or create claim
evidence.
