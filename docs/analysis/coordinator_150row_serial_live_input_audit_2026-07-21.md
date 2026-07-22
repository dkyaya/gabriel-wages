# Coordinator 150-Row Serialized Live Input Audit

Date: 2026-07-21

Result: **PASS — the coordinator input is an exact, eligible CA50 → NJ50 → TX50 concatenation and is locked for the authorized gate sequence.**

## Repository and relay gate

- Starting commit: `264ebd56d2e95cc07ae8e3e030c9cb2ce00ac2a7` (`Fix scout prompt identity and 150-row safety`).
- Runner-fix ancestry: PASS; `HEAD` is exactly commit `264ebd5`.
- Tracked worktree at gate: clean.
- Unrelated untracked item: `package-lock.json`; it is pre-existing and was not read, changed, staged, or deleted.
- All three worker relay ZIPs exist, pass archive integrity testing, and match the SHA-256 values in `three_worker_50row_prep_relay_assessment_2026-07-21.md`.
- Each relay-carried locked CSV is byte-identical to its coordinator copy.
- Worker 1 CA50: prep PASS, 50-row dry run complete, no backend attempt.
- Worker 2 NJ50: original relay FAIL at 0/50 prompt-body municipality IDs; the required coordinator regeneration/rereview passes 50/50 after the committed fix. These two records together satisfy the prep gate.
- Worker 3 TX50: prep PASS, 50-row dry run complete, no backend attempt.

No worker smoke or live scout is being used as authority for this run. No remote operation occurred.

## Construction

The locked input is:

`docs/analysis/coordinator_150row_serial_live_input_2026-07-21.csv`

It preserves the complete 22-column header shared by the three source inputs and concatenates data rows without transformation in this exact order:

1. Worker 1 CA50 priority ranks 1–50;
2. Worker 2 NJ50 priority ranks 1–50; and
3. Worker 3 TX50 priority ranks 1–50.

The file parsed back successfully as 150 rows × 22 columns. Source input headers are identical, each source contains exactly 50 data rows, and each worker's priority ranks remain exactly 1 through 50.

## Locked-input assertions

| Assertion | Result |
| --- | ---: |
| Total data rows | 150 |
| CA rows | 50 |
| NJ rows | 50 |
| TX rows | 50 |
| `worker_1` rows | 50 |
| `worker_2` rows | 50 |
| `worker_3` rows | 50 |
| Distinct `future_live_queue_id` values | 1 |
| Required queue ID | `COORD-SERIAL150-2026-07-21` |
| Unique `municipality_id` values | 150 |
| Unique `census_gov_id` values | 150 |
| File-order preservation | PASS |
| Worker priority-rank preservation | PASS |

No forbidden timeout-only municipality is present: Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, and Princeton are all absent.

## Current eligibility reconciliation

Every row was reconciled by `municipality_id` against the current national municipality universe and municipality coverage output, and by municipality ID against the current candidate queue. A separate state/name comparison was made against canonical `data/contracts.csv` city rows.

All 150 rows satisfy:

- `active_status=Y` in the authoritative universe;
- `government_type=municipal` and `geography_type=place`;
- the locked Census government ID matches the universe;
- `already_in_corpus=no` in the universe;
- `scout_coverage_status=not_scouted`;
- `queue_status=not_scouted`;
- `canonical_overlap_status=not_already_ingested_canonical`;
- zero successful live scout count;
- zero current candidate rows;
- zero recorded failed connection attempts;
- no municipality-ID overlap with the 540-row national scout candidate queue; and
- no state/municipality overlap with canonical contract cities.

No row became covered, queued, canonical, failure-only, duplicated, or otherwise ineligible. No substitute row was introduced.

## Locked hash

SHA-256:

```text
e53db4698b5dba439ad4d31fca79be1242808960d1a8d6809d31b1b915de62fc
```

This hash is the controlling input identity for the dry run, smoke/live gate, live result review, and any later merge-eligibility decision. Any subsequent hash mismatch is a hard stop.
