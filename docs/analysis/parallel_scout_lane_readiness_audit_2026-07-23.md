# Parallel Scout Lane Readiness Audit

Date: 2026-07-23

Disposition: **READY FOR OFFLINE FRAMEWORK IMPLEMENTATION; no parallel live run is authorized or represented as completed.**

## Repository and lineage gate

- Latest local commit before work: `3a7d762141af31baf3b5331883ea6ff21a18114f`.
- Branch: `main`.
- Required ancestry: `3a7d762`, `bd5e259`, `6db14f0`, and `bef5077` are all ancestors of the starting `HEAD`.
- Tracked worktree at start: clean.
- Unrelated untracked item: root `package-lock.json`; preserved and excluded.
- Current successful scout coverage: 794 of the approximately 2,000-municipality workflow checkpoint.
- Remaining to checkpoint: approximately 1,206, or roughly 8–9 successful 150-row waves if scheduled serially.

## Current serial runner behavior

The production runner accepts a locked municipality CSV, builds prompts in input order, and requires explicit mixed-state and hard-cap authorization. A direct-SDK live process is internally serialized with `--n-parallels 1`; a value greater than one fails closed. This framework does not change that invariant. Parallelism is process-level: multiple isolated lanes may eventually run at the same time, while each lane remains sequential internally.

Every lane command retains:

- direct-SDK backend;
- compact prompt mode;
- exact municipality/government/Census identity;
- five deterministic search hints;
- adaptive sleep/backoff `3/5/15/10` with stability/failure windows `25/2`;
- 90-second SDK/httpx timeout plus the runner-level outer timeout;
- zero direct-SDK retries;
- the existing two-consecutive no-evidence transport-collapse stop;
- terminal row timing and fresh-directory resume lineage.

## Outer-timeout readiness

Commit `3a7d762` retains the SDK/httpx timeout and wraps every per-row `client.responses.create(...)` awaitable in `asyncio.wait_for(..., timeout=timeout)`. A runner-expired call becomes a terminal `outer_timeout` row with empty response evidence, measured timing, adaptive failure/backoff, and participation in the existing collapse rule. Fully mocked tests prove a never-returning coroutine cannot stall a lane indefinitely.

The stopped `bd5e259` output remains immutable, nonterminal, non-mergeable, and excluded from evidence. Its locked Post-PI Wave 1 input is reusable only as a fresh lane input after current eligibility and hash checks.

## Current accounting workflow

Live scout outputs are only candidate-stage artifacts. National state changes occur later through a coordinator-controlled sequence:

1. audit the complete live lineage;
2. determine merge eligibility;
3. rebuild the national candidate queue once;
4. rebuild municipality/state scout coverage once;
5. refresh yield learning;
6. refresh dashboard and project-phase JSON;
7. review the combined diff and commit once.

The queue and coverage builders read repository-wide scout artifacts and write shared national outputs. Running them concurrently from lane processes would create order-dependent reads, overlapping writes, ambiguous provenance, and potentially different final counts depending on which process finished last. Dashboard and project documents would have the same collision problem. Parallel collection is therefore feasible; parallel accounting is not.

## Why isolated live collection is feasible

The live runner already supports an exact locked CSV, a caller-specified fresh output directory, a lane-specific cost log, terminal metadata, and no implicit accounting rebuild. Two operating-system processes can therefore collect disjoint municipalities without sharing mutable lane artifacts when:

- inputs are proven disjoint before launch;
- output and cost paths are unique;
- each process remains internally serialized;
- neither process edits shared documentation or accounting;
- capacity is gated immediately before launch;
- both outputs are audited together before any merge.

This is an architectural readiness finding, not evidence that the hosted-search route can sustain two lanes. The first two-lane execution remains a separately authorized capacity experiment with a staggered start and a fail-closed policy.

## Required isolation rules

- One immutable CSV, unique `lane_id`, output directory, cost log, lineage note, and review per lane.
- Zero municipality-ID or nonblank Census-ID overlap across all lane inputs.
- No shared output directory and no reuse of the stopped `bd5e259` directory.
- No lane commit, branch mutation, queue/coverage build, yield/dashboard refresh, or final project-log edit during collection.
- No source verification, ingestion, codification, canonical promotion, wage-gap calculation, causal analysis, or regression inside a lane.
- One coordinator audit consumes all lane artifacts after processes terminate.
- One separately authorized serial accounting merge follows only the resulting recommendation.

## Risk register

### Hosted-search capacity

Two simultaneous hosted-search lifecycles may increase throttling, latency, proxy instability, or no-evidence transport failures. Run one stronger preflight immediately beforehand, stagger Lane 2 by 2–5 minutes, retain per-lane adaptive pacing and outer timeouts, and stop all lanes if a widespread transport pattern appears.

### Accounting collisions

Concurrent builders can overwrite or double-observe shared queue and coverage outputs. Lane commands prohibit builders. One coordinator merge owns all shared files after audit.

### Duplicate municipality selection

Overlapping municipality or Census IDs could double-count attempts and complicate coverage. Planning fails before writing an accepted plan if any cross-lane duplicate exists. Lane 2 selection excludes every Lane 1 ID.

### Partial-lane failures

A completed lane and a partial lane cannot be treated as one completed round. The auditor classifies each separately. Parseable partial outputs are preserved but withheld until resume or explicit disposition.

### Resume lineage complexity

Every lane has its own parent hash and terminal-state requirements. Resume must use a new lane-specific directory and can never cross lane boundaries. The round manifest remains the authority for which input belongs to which lineage.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `docs/analysis/direct_sdk_outer_timeout_failure_audit_2026-07-23.md`
- `docs/analysis/direct_sdk_timeout_implementation_notes_2026-07-23.md`
- `docs/analysis/direct_sdk_outer_timeout_fix_summary_2026-07-23.md`
- `docs/analysis/post_pi_wave1_retry_after_outer_timeout_fix_prompt_2026-07-23.md`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_result_review_2026-07-23.md`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_audit_2026-07-23.md`
- `docs/analysis/post_pi_2000_municipality_strategy_2026-07-23.md`
- `docs/analysis/post_pi_descriptive_analysis_roadmap_2026-07-23.md`
- `docs/dashboard/data/project_phase_summary.json`
- `scripts/gabriel_state_source_scout.py`
- `scripts/run_scout_preflight_gate.py`
- `scripts/diagnose_direct_sdk_hosted_search_transport.py`
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`
- `scripts/test_gabriel_state_source_scout_prompt.py`
- `docs/analysis/scout_speed_stability_implementation_summary_2026-07-22.md`
- `docs/analysis/scout_speed_stability_next_wave_template_2026-07-22.md`
- `docs/analysis/municipality_search_hints_2026-07-22.csv`
- `scripts/build_national_scout_candidate_queue.py`
- `scripts/build_national_scout_coverage_status.py`
- `scripts/build_scout_coverage.py`
- `scripts/build_scout_yield_learning_report.py`
- `scripts/build_dashboard_data.py`
- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv`
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv`
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv`
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`
- `docs/dashboard/data/priority_summary.json`
- `docs/dashboard/data/top_priority_targets.json`

No required path differed from the requested canonical path. No live scout, API/model/hosted-search call, diagnostic, smoke preflight, URL access, source verification, ingestion, `gabriel.codify`, accounting mutation, priority-methodology change, remote operation, or push occurred.
