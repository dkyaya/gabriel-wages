# Tier 1 full run after diagnostic: readiness audit

Date: 2026-07-22
Starting main-repository commit: `b74e82d151a19e6e612181bfbc21cc018f237c33` (`Diagnose hosted search transport failures`)
Decision: **PASS — eligible for one fresh coordinator-controlled 150-row run after a fresh dry-run and one immediate smoke preflight pass.**

## Repository and lineage gate

The tracked worktree was clean at the start of this task. The unrelated untracked root-level `package-lock.json` was reported and left untouched. The current commit is descended from all required local milestones: national tiering `bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714`, Tier 1 batch preparation `364fd9d`, stopped parent `c6b3664`, stopped retry `25445fe`, and transport diagnostic `b74e82d`.

No git remote was inspected or changed, and no fetch, pull, or push occurred.

## Locked input gate

Authoritative locked input: `docs/analysis/tier1_coordinator_150row_serial_live_input_2026-07-22.csv`

SHA-256: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`

Deterministic checks against the locked file and current coverage/queue outputs passed:

- 150 rows, 150 unique `municipality_id` values, and 150 unique Census government IDs.
- Tier 1: 150; `future_scout_eligible_flag=true`: 150; `retry_flag=false`: 150; `failure_only_flag=false`: 150.
- `scout_coverage_status=not_scouted`: 150; `already_canonical_flag=false`: 150; government type `municipal`: 150.
- Worker counts are exactly 50 each for `worker_1`, `worker_2`, and `worker_3`.
- Tier ranks are exactly 1–150 with no gaps.
- The sole queue label is `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`.
- All 150 IDs occur in the current municipality coverage output and all remain `not_scouted`; none is canonical and none appears in the current candidate queue.
- None of the ten isolated retry-only municipalities is present: Stockton, Redding, Oakland, Moreno Valley, Oxnard, Fairfield, Bloomington, Huntley, Roselle, or Princeton.
- State counts match the locked-input audit: AK 1, AL 6, AR 2, AZ 11, CO 9, CT 3, DC 1, FL 15, GA 7, HI 1, IA 4, ID 1, IN 2, KS 4, KY 2, LA 3, MA 9, MD 1, MI 4, MN 4, MO 5, MS 1, NC 8, NE 2, NM 2, NV 4, OH 2, OK 3, OR 3, RI 1, SC 3, SD 1, TN 7, UT 1, VA 7, WA 6, and WI 4.

## Stopped-attempt lineage

### Parent `c6b3664`

The parent output at `tmp/tier1_coordinator_150row_serial_live_direct_sdk_2026-07-22` used the same locked-input hash. It attempted only Oklahoma City, OK and Phoenix, AZ. Both ended as immediate `connection_error` outcomes with no response ID, response text, or token use. Its timing ledger has two attempted failures and 148 `stopped_before_request` rows. It produced zero parseable rows and zero candidate rows. It was not merge-eligible, and its outputs were not added to queue, coverage, dashboard, or priority accounting.

### Retry `25445fe`

The retry output at `tmp/tier1_coordinator_150row_serial_live_retry_direct_sdk_2026-07-22_attempt1` used the same locked-input hash and repeated the same bounded stop: Oklahoma City and Phoenix had immediate `connection_error` outcomes without IDs, text, or tokens, followed by 148 `stopped_before_request` rows. It produced zero parseable rows and zero candidate rows, was not merge-eligible, and did not trigger queue, coverage, dashboard, or priority rebuilds.

The two transport-only attempts are not municipality/source-discovery evidence. Oklahoma City and Phoenix therefore remain ordinary `not_scouted` rows for this official full run.

## Diagnostic readiness

Diagnostic commit `b74e82d` reached Recommendation A: the direct-SDK route was healthy. Its bounded suite passed the no-search control, the hosted-search trivial public query, and the hosted-search municipality-style query. The production scout runner then completed the one-row Oklahoma City probe with one parseable row and two candidate rows. The diagnostic and probe explicitly reported no queue/coverage/dashboard/corpus accounting changes.

The one-row probe remains quarantined under `tmp/`; it is not an official scout result and must not be merged or counted. Its purpose was limited to proving that the production runner could again complete a search-enabled municipality prompt.

## Authorization conclusion

A fresh full run is appropriate because the locked input remains unchanged and eligible, neither stopped attempt produced mergeable evidence, and the independent diagnostic plus actual one-row production probe established that both the route and scout call path were functioning again. The remaining gates are a new 150-row dry-run audit and exactly one immediate no-search direct-SDK smoke preflight.

Fresh directories reserved for this task:

- Dry-run: `tmp/tier1_coordinator_150row_serial_live_after_diag_dry_run_2026-07-22_attempt1`
- Smoke: `tmp/tier1_coordinator_150row_serial_live_after_diag_smoke_2026-07-22_attempt1`
- Live: `tmp/tier1_coordinator_150row_serial_live_after_diag_direct_sdk_2026-07-22_attempt1`

The live directory was confirmed absent before work. It will not reuse either failed directory. Diagnostic/probe artifacts and both stopped runs remain excluded from official accounting.
