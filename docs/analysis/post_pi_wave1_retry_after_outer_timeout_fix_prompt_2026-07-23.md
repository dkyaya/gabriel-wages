# Future Coordinator Prompt — Retry Post-PI Wave 1 After Outer-Timeout Fix

Use this prompt only under a separately authorized live coordinator task. Do not treat this document as current live authorization.

---

Work in the main coordinator repo only:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Run one fresh Post-PI Wave 1 coordinator-controlled 150-row serialized direct-SDK live scout only after every gate below passes.

## Immutable lineage and exclusions

- Preserve the stopped `bd5e259` run as quarantined non-evidence:
  `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1`
- Do not resume from or write into that directory.
- Do not count its Lake Oswego in-flight request as an official attempt or failure.
- Use the unchanged locked input:
  `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`
- Required SHA-256:
  `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Reconcile all 150 IDs against then-current coverage, canonical, and failure-only exclusions. Stop without substitution if any row is no longer an ordinary eligible target.
- Confirm current code contains the tested outer `asyncio.wait_for` guard and `outer_timeout` terminal-row behavior.

Do not inspect remotes, push, fetch, pull, run concurrent live workers, verify or download sources independently, ingest, codify, calculate wage gaps, make causal claims, or run regressions.

## Evidence gates

1. Require a clean tracked worktree and record unrelated untracked files separately.
2. Recheck the exact locked input hash, 150 unique municipality IDs, 150 unique Census IDs, no retry/failure-only/covered/canonical rows, and 150/150 five-hint completeness.
3. Run all mocked direct-SDK and prompt tests. Confirm the never-returning fake call becomes `outer_timeout` near its configured small deadline, two such rows stop later requests, and the success fixture is unchanged.
4. Run the stronger preflight first in a fresh plan-only directory:

```bash
python scripts/run_scout_preflight_gate.py \
  --plan-only \
  --output-dir tmp/post_pi_wave1_outer_timeout_retry_preflight_plan_2026-07-23_attempt1 \
  --model gpt-5.4-nano \
  --timeout 30 \
  --search-context-size low \
  --max-calls 4
```

Confirm plan-only made zero external calls.

5. Create a fresh one-row diagnostic input from locked rank 1, then run exactly one authorized stronger live preflight in fresh directories:

```bash
python scripts/run_scout_preflight_gate.py \
  --output-dir tmp/post_pi_wave1_outer_timeout_retry_preflight_live_2026-07-23_attempt1 \
  --model gpt-5.4-nano \
  --timeout 30 \
  --search-context-size low \
  --max-calls 4 \
  --include-one-row-probe \
  --probe-input-csv tmp/post_pi_wave1_outer_timeout_retry_one_row_probe_input_2026-07-23_attempt1.csv \
  --probe-output-dir tmp/post_pi_wave1_outer_timeout_retry_one_row_probe_2026-07-23_attempt1
```

Stop unless the no-search control, both hosted-search controls, and the one-row production probe pass with response lifecycle and usage evidence. Quarantine the probe from all official accounting.

6. Run and audit a fresh offline 150-row dry run:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv \
  --output-dir tmp/post_pi_wave1_outer_timeout_retry_dry_run_2026-07-23_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 150 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```

Require 150 exact prompts, 150/150 hints, compact mode, complete identity and employer/unit/source controls, adaptive metadata, 150 dry timing rows, and no backend call.

## One authorized live process

Only after all gates pass, create a lineage note in this fresh output directory:

`tmp/post_pi_wave1_outer_timeout_retry_live_direct_sdk_2026-07-23_attempt1`

Then run exactly one process:

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv \
  --output-dir tmp/post_pi_wave1_outer_timeout_retry_live_direct_sdk_2026-07-23_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path tmp/post_pi_wave1_outer_timeout_retry_live_direct_sdk_2026-07-23_attempt1/batch_cost_log.csv
```

## Live review rules

- Verify every called row reaches a terminal parseable or failed timing state.
- If a call reaches the outer deadline, require:
  `failure_type=outer_timeout`, start/finish/elapsed evidence near 90 seconds, empty response ID/text/tokens, adaptive failure/backoff, and no pending timing state.
- Two consecutive no-evidence transport failures must stop later requests as `stopped_before_request`.
- If any rows are stopped before request, lifecycle/artifact integrity is lost, or outputs are incomplete, set `merge_eligible=false`; preserve artifacts and do not rebuild accounting.
- Do not rerun into the same directory.
- Use a fresh resume directory only when the parent is terminal, the locked hash matches, and completed-ID/failure selection is explicitly audited.

## Post-run boundary

Only if the complete lineage is merge-eligible:

1. rebuild candidate queue and coverage exactly once;
2. refresh yield learning;
3. refresh dashboard/checkpoint JSON;
4. update progress toward approximately 2,000 covered municipalities.

Keep the priority-layer refresh deferred unless the documented success cadence, deterministic threshold, or project strategy requires it. All candidates remain unverified. Verification, extraction, ingestion, rating, descriptive wage-gap analysis, and regressions remain outside this retry task.

---
