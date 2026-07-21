# Three-Worker 50-Row Prep Relay Assessment

Date: 2026-07-21

Disposition: **do not run a smoke or live scout yet**. The three locked inputs remain the intended CA50/NJ50/TX50 wave, but the original NJ50 relay failed its prompt contract. The coordinator has corrected the shared prompt builder and produced a separate 50/50 NJ rereview. Live execution still requires a newly combined and hashed 150-row input, a final corrected-code dry review, one separately authorized smoke, and explicit live authorization.

## Evidence reviewed

The coordinator inspected all requested input, review, validation, and metadata files in these worker prep relays. The copies now held under the main repository `tmp/` have these SHA-256 values:

| Worker | Relay | SHA-256 |
| --- | --- | --- |
| 1 | `worker_1_ca50_prep_relay_20260721_worker1_ca50_attempt1.zip` | `6133669f8c2c599047fb4ccb181ea577eb736576e470aacfa1517237efcdd86b` |
| 2 | `worker_2_nj50_prep_relay_20260721_worker2_nj50_attempt1.zip` | `e891505bd8436452b63aa0459c5d6ed9ec26c1f3615ecb7d290cb276a4891f70` |
| 3 | `worker_3_tx50_prep_relay_20260721_worker3_tx50_attempt1.zip` | `34b720da88ef7cbd4f5cd9580d82da80a4375a2f37582272af0f04fcc42d7388` |

All three archives passed ZIP integrity testing. Their locked CSVs match the main coordinator copies byte-for-byte.

## Worker outcomes

### Worker 1 — CA50

- Final worker commit: `e391ce04347b0496f40a9283eb92f747a3e97c76` (`Prepare Worker 1 CA50 dry-run review`).
- Dry run: **completed**, run `ca_2026-07-21_185703`, 50 prompts, `mode=dry_run`, `live_attempted=false`, `backend_call_returned=false`, and `execution_status=dry_run_completed`.
- Review: **PASS**. The worker reported 50/50 exact employer/Census identity and 50/50 for the prohibited-employer, unit/comparator, source-stage, access-state, visible-year, duplicate, overlap, empty-output, no-public-records, and unverified-stage controls.
- Candidate readiness: the locked CA50 input is ready for the future corrected-code coordinator dry review. This prep evidence does not establish source discovery coverage or authorize live use by itself.

### Worker 2 — NJ50

- Final worker commit: `0969e3923cdaf09ce5dd1bc659333f3a65ebb654` (`Document Worker 2 NJ50 dry-run review failure`).
- Dry run: **completed**, run `nj_2026-07-21_190147`, 50 prompts, `mode=dry_run`, `live_attempted=false`, `backend_call_returned=false`, and `execution_status=dry_run_completed`.
- Review: **FAIL**. Exact government name and Census government ID appeared in 50/50 prompts, but the locked internal `municipality_id` appeared in 0/50 prompt bodies. Westfield, for example, was missing `cog_2025_170248` from its row-aware instructions.
- Why this blocked live: government name and Census ID do not replace the auditable locked internal row key. Without the internal ID in each prompt body, the coordinator cannot consistently check row identity or diagnose same-name city/township/county/school/authority leakage. The original relay therefore cannot be called prep-complete.
- Corrective disposition: `scripts/gabriel_state_source_scout.py` now emits `Locked internal municipality ID: <municipality_id>` whenever the row supplies it. A coordinator-only NJ50 dry run and rereview subsequently passed 50/50; see `worker_2_nj50_prompt_contract_rereview_after_municipality_id_fix_2026-07-21.md`. That rereview, not the original failed review alone, is required for the future live gate.

### Worker 3 — TX50

- Final worker commit: `8a885ef07b8cd9a12dfecaedec77ced8a38a740a` (`Prepare TX50 dry-run review evidence`).
- Dry run: **completed**, run `tx_2026-07-21_190015`, 50 prompts, `mode=dry_run`, `live_attempted=false`, `backend_call_returned=false`, and `execution_status=dry_run_completed`.
- Review: **PASS**. The worker reported 50/50 exact employer/Census identity and 50/50 for municipality-row identity, county context, substitute-employer exclusions, ordinary civilian comparator scope, source-stage/access-state controls, visible years, duplicates, overlap, empty output, no-public-records, and unverified-stage quarantine.
- Candidate readiness: the locked TX50 input is ready for the future corrected-code coordinator dry review. It remains prep-only evidence, not live output or source verification.

## Shared runner blockers found in the prep evidence

Every worker metadata file reports `live_hard_cap=25`. Before this coordinator change, the runner used `min(max_prompts, LIVE_HARD_CAP)`, so `--max-prompts 150` would have silently executed at most 25 rows. It also filtered every CSV row against a single `--state`, so a CA/NJ/TX input could silently lose 100 rows.

The minimum coordinator-side fix now provides:

- `--state ALL --allow-mixed-states` as the only explicit mixed-state mode;
- rejection of an explicit multi-state CSV when mixed mode is absent, rather than silent single-state filtering;
- `--live-hard-cap <N>` as a separate explicit ceiling paired with `--max-prompts <N>`;
- an error instead of truncation when `--max-prompts` exceeds the explicit cap;
- exact row-count authorization for live mixed-state runs;
- live mixed-state restrictions to direct SDK, `n_parallels=1`, zero SDK retries, no `--limit`, and no retry-file mode; and
- metadata recording the input states, mixed-state flag, and effective explicit cap.

No live path was exercised in this task. The offline regression suite constructed a synthetic ordered CA50/NJ50/TX50 input, loaded all 150 rows once, and proved that the old 25-row ceiling and any mixed-input/max-prompt mismatch fail closed.

## Recommendation

Do not run live now. First create and hash the exact combined 150-row input, run a corrected-code no-network dry review over all 150 prompts, reconcile all row and state counts, and inspect the Worker 1/2/3 evidence together with the new NJ50 rereview. Only a separately authorized future coordinator task may run the one no-search smoke and then the one sequential direct-SDK queue. No worker should receive live authority.
