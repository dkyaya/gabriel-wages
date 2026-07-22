# Wave 2 Coordinator 150-Row Locked Input Audit

Date: 2026-07-22

Disposition: **PASS — the exact CA50→TX50→IL50 concatenation is locked and currently eligible for the coordinator dry gate.**

## Locked file

- Path: `docs/analysis/wave2_coordinator_150row_serial_live_input_2026-07-22.csv`
- SHA-256: `1227234e23635f6bae0d700d95ae7ac0890098c4906c106fffe3ef446b554bbf`
- Rows: 150 data rows plus one header
- Future queue ID: `COORD-SERIAL150-WAVE2-2026-07-22`

## Structure and order

The file was assembled without substitution in this exact order:

1. Worker 1 CA rows 1–50;
2. Worker 2 TX rows 1–50; and
3. Worker 3 IL rows 1–50.

Counts are CA=50, TX=50, IL=50 and `worker_1`=50, `worker_2`=50, `worker_3`=50. The 150 municipality IDs are unique; the 150 Census government IDs are unique. Row identity, order, and all columns reconcile exactly to the three prep-passed worker inputs.

## Current eligibility reconciliation

The audit used the current 35,589-row municipality coverage output, 786-row candidate queue, `data/contracts.csv`, `data/city_coverage.csv`, and exact state/name plus ID comparisons. Every locked row remains:

- `scout_coverage_status=not_scouted`;
- `queue_status=not_scouted` with no queue ID or exact state/name overlap;
- `canonical_overlap_status=not_already_ingested_canonical` with no exact contract/city-coverage overlap;
- absent from corpus context;
- free of prior failed-connection attempts; and
- an active municipal/place government rather than a prohibited school, county, authority, township, district, university, private, or other non-municipal employer.

No row became ineligible and no ad hoc replacement was made.

## Forbidden failure-name gate

There is no selected municipality named Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, Princeton, or Moreno Valley. The overlap count is zero.

## Pre-run accounting baseline

- Candidate queue rows: 786
- Successful scout-covered municipalities: 356
- Candidate-positive municipalities: 293
- Failure-only municipalities: 8
- CA covered / candidate rows: 94 / 234
- TX covered / candidate rows: 53 / 85
- IL covered / candidate rows: 74 / 217

This audit creates no discovery outcome. The input is authorized only for the subsequent dry, smoke, and conditional coordinator-live gates; it verifies no source and changes no national accounting.
