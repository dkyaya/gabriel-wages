# Post-PI Scale-Up Wave 1 Worker 3 Offline Preparation Prompt

Use **Codex Routine / GPT-5.6 Terra Medium**.

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-3`. This task is offline/dry-run preparation only. Do not
run a smoke, preflight, hosted search, live scout, API/model/backend call, URL
opening/download, source verification, public-records action, ingestion,
`gabriel.codify`, queue/coverage/priority/dashboard rebuild, or protected
canonical edit. Do not inspect/configure/validate/modify remotes; do not push,
fetch, or pull.

## Worktree and branch

Require clean tracked files. Create or update the local worker branch from the
local `main` branch only:

```bash
cd /Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-3
git switch main
git switch -C post_pi_wave1_worker_3_prep_20260723 main
PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python
```

Do not inspect a remote. Read `AGENTS.md`, this prompt, the assigned input and
audit, the shared split audit, the coordinator handoff, the scout runner, the
prompt test, and the deterministic hints file.

Copy the assigned input CSV from the main coordinator checkout only if it is
absent in the worker checkout; otherwise compare it byte-for-byte with main.
Then read the assigned CSV before performing the structural audit. Do not edit
the locked CSV in the worker worktree.

## Locked input

- Assigned input: `docs/analysis/post_pi_wave1_worker_3_scout_input_2026-07-23.csv`
- Expected rows: `50`
- Expected worker ID: `worker_3`
- Expected queue ID: `COORD-POST-PI-WAVE1-SERIAL150-2026-07-23`
- Expected state scope: `CROSS_STATE_POST_PI_SCALEUP_WAVE1`
- Expected rank range: `101–150`
- Assignment: `rank_sliced_contiguous`
- Expected SHA-256: `574507500387ccbfb162504086b9463811b6906f765a2066d3a7d928ae17941d`

Before the dry run, audit exact order/ranks, 50 unique nonblank municipality and
Census IDs, Tier 1 status, ordinary future eligibility, no retry/failure-only/
covered/canonical rows, allowed municipal/place or township/county-subdivision
government categories, all five hints, and the expected hash. Stop rather than
edit or substitute a locked row.

Record a protected-file baseline for `data/contracts.csv`,
`data/city_coverage.csv`, `corpus/`, national queue/coverage/priority inputs,
dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect
`.env`, credential files, or environment values.

## Run exactly one 50-row offline dry run

Require the output directory to be absent, then run exactly:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/post_pi_wave1_worker_3_scout_input_2026-07-23.csv \
  --output-dir tmp/post_pi_wave1_worker_3_prep_dry_run_20260723_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 50 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```

Do not add `--live`. Confirm the run generated exactly 50 prompts and made no
live/API/model/backend calls. Dry-run pacing is metadata only.

## Review and validate

Create a dry-run review and inspect all 50 prompts plus `row_timing.csv` and
`run_metadata.json`. Confirm:

- all 50 prompt identities exactly match the locked input in order;
- compact prompt mode was used;
- deterministic search hints appeared in every prompt;
- adaptive settings `3/5/15/10/25/2` are present in metadata;
- `row_timing.csv` exists with exactly 50 dry-run planning rows;
- `live_attempted=false` and `backend_call_returned=false`;
- each prompt includes locked municipality/government/Census identity, county
  context, expected safety and ordinary non-safety units, exact-employer
  controls, excluded-employer controls, authoritative-source controls,
  valid-empty guidance, blocked/dead separation, duplicate suppression,
  public-records prohibition, and unverified-stage handling; and
- all 50 prompts preserve the exact output-schema requirements.

Create a worker validation report. Run only offline compile/prompt tests and
`git diff --check`; compare protected files to the baseline. Do not run the
direct-SDK suite if it would use anything other than its fully mocked no-network
paths.

## Local commit and sanitized relay

Commit only worker-created dry-run review and validation evidence locally with a
message such as `Prepare post-PI Wave 1 Worker 3 offline dry run`. Do not
commit dry-run `tmp/`, `.venv`, `.env`, credentials, caches, local excludes, or
unrelated files. Do not push.

Create a sanitized relay ZIP containing the locked input/audit/prompt, dry-run
review, worker validation report, prompt preview, `row_timing.csv`,
`run_metadata.json`, protected-file comparison, git status/log/diff/changed
files, and a `next_task.md` stating that the coordinator owns all preflight/live
work. Exclude `.env`, credential files, credentials, tokens, cookies, secrets,
raw auth headers, caches, and unrelated files.

Name the relay:

```text
tmp/post_pi_wave1_worker_3_prep_relay_2026-07-23_<commit>.zip
```

**Mandatory relay copy:** after creating and inspecting the final ZIP, copy it
into the main coordinator repo:

```bash
COORDINATOR_TMP="/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
mkdir -p "$COORDINATOR_TMP"
cp "tmp/post_pi_wave1_worker_3_prep_relay_2026-07-23_<commit>.zip" "$COORDINATOR_TMP/"
cmp "tmp/post_pi_wave1_worker_3_prep_relay_2026-07-23_<commit>.zip" "$COORDINATOR_TMP/post_pi_wave1_worker_3_prep_relay_2026-07-23_<commit>.zip"
```

Preserve the basename exactly. Inspect ZIP filenames and stop if any secret,
credential, environment, cache, or unrelated path appears.

## Final worker report

Report branch/commit, locked input hash, 50-row identity gate, state/tier/rank
profile, compact/hints/adaptive evidence, 50/50 prompt review, timing and
validation results, worker relay path, copied coordinator relay path/hash, and
confirmation that no live/API/model/preflight/hosted-search/URL/verification/
ingestion/codify/accounting/remote/push action occurred.
