# Verification Scale — Next Round Plan

Date: 2026-07-24

## Current position

Round 1 (`VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`) is merged into the
durable verification-routing ledger. It preserves 2,250 scheduled queue
identities and 2,250 terminal routing outcomes.

Against the canonical planning totals, approximately **1,350 scheduled rows**
remain (3,600 minus 2,250) and **2,476 full-pool URL-bearing rows** remain
(4,726 minus 2,250). A Round 2 planner must exclude the durable ledger's queue
and verification IDs before locking inputs; it must not assume subtraction
alone is a sufficient identity audit.

## Recommended next round

Prepare and, only under separate live URL authorization, run:

`VERIFICATION-SCALE-ROUND2-3X750-2026-07-24`

Keep:

- up to three lanes and 750-row lane capacity;
- concurrency eight per lane;
- 20-second total timeout;
- five redirects maximum;
- 10 MiB maximum response bytes;
- content samples disabled;
- lane-local metadata and incremental terminal ledgers;
- a combined lane audit followed by a later serial merge.

Only about 1,350 scheduled rows remain, so Round 2 cannot fill three
750-row lanes from scheduled candidates. The deterministic planner should
fill available capacity without substitution or duplication and record the
actual lane allocation. A balanced three-lane plan would be roughly 450 rows
per lane; a capacity-first allocation could use 750 and 600 rows with the
third lane empty/not launched. The planner and input audit should select and
document one approach before live execution.

## Oversized documents

Round 1 classified 64 rows as `too_large` under the 10 MiB ceiling. Do not
increase the global response limit for ordinary routing: full document
retention and parsing are not needed to record that a large document exists.
If downstream extraction requires these records, create a separate
oversized-document handling plan with explicit storage, security, and
extraction limits.

## Sequencing

Run Round 2 routing before starting broad ingestion/codification, so the
scheduled pool is substantially routed and its exception workload is known.
This is not authority to open URLs, ingest or codify documents, extract wages,
calculate wage gaps, or make claims. Each action retains its own later
authorization and audit boundary.
