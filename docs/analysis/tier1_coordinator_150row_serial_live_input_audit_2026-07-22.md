# Tier 1 Coordinator 150-Row Locked Input Audit

Date: 2026-07-22

Disposition: **PASS — locked input is eligible for a coordinator dry run.**

## Identity and ordering

- File: `docs/analysis/tier1_coordinator_150row_serial_live_input_2026-07-22.csv`
- SHA-256: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`
- Rows: 150.
- Worker order: Worker 1 ranks 1–50, Worker 2 ranks 51–100, Worker 3 ranks 101–150.
- Worker counts: `worker_1=50`, `worker_2=50`, `worker_3=50`.
- Rank range: exactly 1–150, unique and gap-free, in ascending file order.
- Queue identity: exactly one value, `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`.
- Identity uniqueness: 150 municipality IDs and 150 Census government IDs, with no blanks or duplicates.
- The file was constructed by retaining the Worker 1 header and rows, followed by Worker 2 rows and Worker 3 rows, without sorting or substitution.

## Eligibility

All 150 rows are `Tier 1`, future-scout eligible, non-retry, non-failure-only, `not_scouted`, noncanonical, and municipal/place governments. The locked input has no current national candidate-queue overlap. Current municipality coverage was re-read after worker preparation and still reports all 150 IDs as `not_scouted` and `not_already_ingested_canonical`.

The following failure-only retry municipalities are absent: Stockton CA, Redding CA, Oakland CA, Moreno Valley CA, Oxnard CA, Fairfield CA, Bloomington IL, Huntley IL, Roselle IL, and Princeton NJ.

No row was substituted after the priority-tier selection.

## State distribution

| State | Rows | State | Rows | State | Rows |
|---|---:|---|---:|---|---:|
| AK | 1 | AL | 6 | AR | 2 |
| AZ | 11 | CO | 9 | CT | 3 |
| DC | 1 | FL | 15 | GA | 7 |
| HI | 1 | IA | 4 | ID | 1 |
| IN | 2 | KS | 4 | KY | 2 |
| LA | 3 | MA | 9 | MD | 1 |
| MI | 4 | MN | 4 | MO | 5 |
| MS | 1 | NC | 8 | NE | 2 |
| NM | 2 | NV | 4 | OH | 2 |
| OK | 3 | OR | 3 | RI | 1 |
| SC | 3 | SD | 1 | TN | 7 |
| UT | 1 | VA | 7 | WA | 6 |
| WI | 4 | **Total** | **150** |  |  |

This exactly matches the planned distribution.

## Descriptive range

- Priority score: minimum 75.071; median 75.801; maximum 78.002.
- Population: minimum 70,542; median 196,626; maximum 1,650,070.
- Priority confidence: 150 low. This is expected because the transparent tiering model deliberately lowered confidence where state scout samples remained sparse; it does not invalidate Tier 1 operational ordering.

This audit used only local coordinator CSVs. It did not run a scout, backend, API, source verification, ingestion, or codification step.
