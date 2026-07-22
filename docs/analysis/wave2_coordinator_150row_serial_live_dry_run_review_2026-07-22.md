# Wave 2 Coordinator 150-Row Dry-Run Review

Date: 2026-07-22

Disposition: **PASS — all 150 corrected row-aware prompts passed the coordinator contract with no backend call.**

## Command and artifacts

The coordinator ran the exact requested dry command against `docs/analysis/wave2_coordinator_150row_serial_live_input_2026-07-22.csv`, SHA-256 `1227234e23635f6bae0d700d95ae7ac0890098c4906c106fffe3ef446b554bbf`, into the fresh directory `tmp/wave2_coordinator_150row_serial_live_dry_run_2026-07-22`.

Artifacts are `prompt_preview.md`, `row_timing.csv`, and `run_metadata.json`. Run ID is `all_2026-07-22_114311`.

## Metadata and timing gate

- Prompts / locked input rows: 150 / 150
- `input_states`: CA, IL, TX
- `allow_mixed_states`: true
- `live_hard_cap`: 150
- `sleep_between_prompts`: 5.0
- `execution_status`: `dry_run_completed`
- `live_attempted`: false
- `backend_call_returned`: false
- Timing rows: 150
- Timing status: 150 `dry_run_planned`; backend `dry-run`; live attempted `no`

The timing rows preserve exact CA→TX→IL file order even though the metadata state set is serialized alphabetically.

## Complete 150/150 prompt audit

Every prompt was ordinally paired with its locked CSV row and checked by exact literal comparison. All 150/150 include:

- municipality and state;
- locked internal municipality ID;
- exact `government_name` and Census government ID;
- complete county context, context-only rather than an alternate employer;
- complete expected-units string;
- complete verification notes;
- strict employer, bargaining-unit, ordinary non-safety, cycle, and document/source controls;
- explicit permission to return an empty candidate list;
- blocked/unreadable versus dead/unreachable separation;
- known/exact-source duplicate controls;
- unverified scout-stage handling and context/insufficient-stage separation; and
- the prohibition on making or recommending public-records requests.

All 150 also retain `Do not invent URLs.` and the rule that a safety document cannot satisfy the ordinary non-safety request.

## Decision

The dry gate passes. This review establishes prompt integrity only; it verifies no source, creates no scout coverage, and authorizes no accounting update. The next gate is exactly one direct-SDK, one-request, no-search smoke. A failed smoke remains a hard stop before live scouting.
