# Post-PI Scale-Up Wave 1 Coordinator Handoff After Worker Relays

Date: 2026-07-23

Disposition: **future coordinator procedure only; no preflight or live call is authorized by this handoff.**

Inspect exactly three `post_pi_wave1_worker_<N>_prep_relay_2026-07-23_<commit>.zip`
files copied into the main coordinator repo `tmp/`. For every relay, verify the
locked input hash and 50-row order, compact prompt review, five exact-ID search
hints, adaptive metadata, `row_timing.csv` with 50 planning rows, no-backend
lifecycle, validation, protected-file comparison, sanitized contents, and local
worker commit. Stop on missing or inconsistent evidence; do not substitute rows.

Combine Worker 1, Worker 2, then Worker 3 into one locked 150-row coordinator
input. Preserve ranks 1–150, wave ID `POST-PI-SCALEUP-WAVE1-2026-07-23`, queue ID `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23`, exact
identity order, and all prompt-control fields. Record the combined SHA-256 and
run a separate 150-prompt offline dry review.

A separately authorized coordinator live task must run
`scripts/run_scout_preflight_gate.py` first and stop unless the evidence gate and
executed preflight pass. Only then may one serialized direct-SDK process use:

- `--state ALL --allow-mixed-states`;
- `--prompt-mode compact`;
- `--search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv`;
- `--max-prompts 150 --live-hard-cap 150 --n-parallels 1`;
- `--sleep-between-prompts 5`;
- adaptive settings `3/5/15/10/25/2`;
- zero SDK retries, a fresh output directory, and the existing connection-collapse stop.

No concurrent live workers. Stop on connection collapse, repeated transport
failure, systematic parse/schema failure, artifact/lifecycle loss, protected
mutation, or secret exposure. Resume only from a terminal parent into a fresh
child after exact input-hash and completed-ID review.

Rebuild queue, coverage, yield learning, and dashboard data only if the complete
lineage is merge-eligible. Do not refresh priority tiers every wave; use the
documented 300–600-successful-scout threshold or a new strategy requirement.
After a successful merge, update progress toward the approximately
2,000-covered checkpoint. Keep failure-only retries separate.
Verification, extraction, ingestion, rating, descriptive wage-gap analysis,
mechanism-correlation documentation, and the future gap map/filter remain the
post-checkpoint phase; regressions remain deferred.
