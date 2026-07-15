# GABRIEL State Source Scout — Coverage Accounting Methodology (2026-07-15)

**Status:** durable project standard, like the schema/methodology doc it extends (`gabriel_state_source_scout_methodology_2026-07-14.md`). Update in place; do not fork a dated copy.

## Purpose

Every prior scout session (2026-07-14 pilot/retry, 2026-07-15 timeout/rate-limit/tuning sessions) answered "did this run work?" but nothing tracked, cumulatively, "how much of the state have we scouted, and what does it look like so far?" This adds two persistent, append/upsert CSVs under `docs/analysis/` that accumulate across every future scout run:

- `gabriel_state_source_scout_municipality_coverage.csv` — one row per municipality ever scouted, upserted (a municipality's row is replaced with its latest outcome each time it's re-scouted or retried, never duplicated).
- `gabriel_state_source_scout_state_coverage.csv` — one row per state, recomputed in full from all municipality-coverage rows for that state each time `--build-coverage` runs.

Both are built via `scripts/gabriel_state_source_scout.py --build-coverage` (see the script's own `--help` for flags), not hand-edited.

## Critical distinction: scout-positive vs. verified

**Every count in these two files describes unverified model output.** A municipality with `candidate_count > 0` has produced *leads* — plausible-looking source URLs a model found via web search — not confirmed, reachable, or ingested documents. Use this vocabulary when describing these files:

- **scout-positive**: a municipality with `candidate_count > 0` (at least one candidate lead was produced).
- **candidate lead / lead**: an individual row in a `parsed_candidates.csv`.
- **unverified**: the default and required state of every candidate row (`verification_status=unverified` per the original methodology doc) until a human or a future authorized session checks it.
- **needs verification**: `needs_verification=yes` in the municipality-coverage file — flags that this municipality has leads worth a future URL-reachability pass, not that it has been checked.

**Never** describe a scout-positive municipality as "collected," "verified," "ingested," or "confirmed" based on these files alone. That status change only happens through the existing promotion pipeline (`source_planning_csv_hygiene_standard_2026-07-08.md`'s `verification_status`/`promotion_status` vocabulary), which this accounting layer does not alter.

## Municipality coverage — field notes

- `scout_status` (`not_scouted | scouted_parseable | scouted_failed | retry_parseable | retry_failed`): reflects the *final* outcome after an immediate retry, if one was run. A municipality that failed the main run and then succeeded on retry shows `retry_parseable`, not `scouted_failed` — the coverage file always reflects current best-known status, not full attempt history (attempt history lives in each run's own `raw_outputs.csv`/`failed_parses.csv`, referenced via `raw_outputs_ref`/`failed_parses_ref`).
- `parse_status` (`parseable | failed`): the same final-outcome binary, redundant with `scout_status` by design — `parse_status` is for quick filtering, `scout_status` preserves whether a retry was needed.
- `likely_triad` (`yes`/`no`): `yes` only if candidates spanning all three of `police`, `fire`, `non_safety` were produced for that municipality in the same run. This is a scout-stage signal (the model found leads for all three categories), not a claim that the underlying documents exist or match cycles — matching-cycle triad verification remains a downstream, human-in-the-loop step per `AGENTS.md`'s cross-occupation design.
- `best_source_owner_type` / `best_candidate_priority`: the single highest-authority/highest-priority value across that municipality's candidates this run (priority order: `state_labor_board > city > union > third_party > school > news > unknown`; `high > medium > low`). A summary signal for triage, not a statement that the *specific* highest-priority candidate has been checked.
- `needs_retry` (`yes`/`no`): `yes` only if the municipality's current final status is a failure (`scouted_failed`/`retry_failed`) — i.e., still needs another attempt, if one is authorized.
- Cost/token/time fields are pulled directly from that municipality's own row in the relevant run's `raw_outputs.csv` (matched by the exact identifier `gabriel_state_source_scout_<run_id>_<municipality_id>`, not string-parsed) — no aggregation ambiguity.

## State coverage — field notes

- `total_municipalities_known`: the size of the municipality list used for the **most recent** `--build-coverage` call for that state — i.e., how many municipalities are in the working batch/gazetteer file, not a claim about the true total number of municipalities in the state. As batch lists grow (see `gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.md`'s note on population-rank sourcing), this number should be expected to grow too; it is explicitly **not** an authoritative state population-center count.
- All other fields aggregate across **every** municipality-coverage row on file for that state (not just the most recent batch) — so re-running `--build-coverage` after a second, disjoint batch correctly reflects cumulative state progress, not just the latest batch.
- `estimated_cost_per_100_municipalities` / `estimated_time_per_100_municipalities`: derived from this state's own observed average cost/time per scouted municipality (successful calls only for time; all attempts for cost), with a flat +15s/municipality added to the time estimate for the recommended `sleep_between_prompts` spacing under a fully sequential (`n_parallels=1`) batch. These will drift as more, more-varied municipalities are scouted — treat as a live-updating estimate, not a fixed number.

## What this does NOT do

- Does not verify any URL, fetch any document, or check `data/contracts.csv` for overlap. A "needs_verification=yes" row is a to-do item for a future, separately-scoped session (see `gabriel_state_source_scout_retry_summary_2026-07-14.md`'s Task 6 URL-check pattern for what that session should look like).
- Does not promote, ingest, or touch `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or any claim/evidence file.
- Does not replace the per-run `run_metadata.json`/`cost_summary.json`/`raw_outputs.csv` artifacts — those remain the authoritative per-run record; the coverage files are a cumulative index over them.
