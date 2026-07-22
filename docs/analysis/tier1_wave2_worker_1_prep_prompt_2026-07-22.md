# Tier 1 Wave 2 Worker 1 Offline Preparation Prompt

Use Codex Routine / GPT-5.6 Terra Medium.

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1`. This is offline/dry-run preparation only. Do not run a smoke, hosted-search diagnostic, live scout, API/model/backend call, URL opening/download, source verification, public-records action, ingestion, `gabriel.codify`, queue/coverage/priority/dashboard rebuild, or protected canonical edit. Do not inspect/configure/validate/modify remotes; do not push, fetch, or pull.

## Worktree setup

```bash
cd /Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1
EXCLUDE_FILE="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$EXCLUDE_FILE")"
grep -qxF ".venv/" "$EXCLUDE_FILE" || echo ".venv/" >> "$EXCLUDE_FILE"
grep -qxF ".env" "$EXCLUDE_FILE" || echo ".env" >> "$EXCLUDE_FILE"
grep -qxF ".claude/" "$EXCLUDE_FILE" || echo ".claude/" >> "$EXCLUDE_FILE"
grep -qxF "__pycache__/" "$EXCLUDE_FILE" || echo "__pycache__/" >> "$EXCLUDE_FILE"
grep -qxF ".pytest_cache/" "$EXCLUDE_FILE" || echo ".pytest_cache/" >> "$EXCLUDE_FILE"
test -z "$(git status --porcelain --untracked-files=no)" || { echo "ERROR: tracked files are dirty"; git status --short; exit 1; }
git switch -C tier1_wave2_worker_1_prep_20260722 main
test "$(git branch --show-current)" = "tier1_wave2_worker_1_prep_20260722"
git status --short
PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python
"$PYTHON" --version
```

Use only local `main`; do not inspect a remote. Stop if tracked files are dirty.

## Locked-input gate

Require and read `AGENTS.md`, the assigned input/audit/prompt, the shared split audit and coordinator handoff, the scout runner, prompt test, and deterministic hints file.

- Assigned input: `docs/analysis/tier1_wave2_worker_1_scout_input_2026-07-22.csv`
- Expected rows: `50`
- Expected worker ID: `worker_1`
- Expected future queue ID: `COORD-TIER1-WAVE2-SERIAL150-2026-07-22`
- Expected state scope: `CROSS_STATE_TIER1_WAVE2`
- Expected wave rank range: `151–200`
- Expected prompt mode: `compact`
- Expected hints: `docs/analysis/municipality_search_hints_2026-07-22.csv`
- Expected input SHA-256: `f9cd191ca00e6e965cde83879a1383f23d1750b8e90d0a5812697c98aa19b20f`

Run a local Python structural audit before any dry run. Require exact rows/order/ranks, one expected worker/queue/scope, 50 unique nonblank municipality IDs and Census IDs, Tier 1, current ordinary eligibility, no retry/failure/canonical/covered rows, all five attached hints, only municipal/place or township/county-subdivision employers, and the expected SHA-256. Stop rather than edit or substitute any locked row.

```bash
"$PYTHON" - <<'PY'
import csv, hashlib
from pathlib import Path
path = Path("docs/analysis/tier1_wave2_worker_1_scout_input_2026-07-22.csv")
rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
allowed = {("municipal", "place"), ("township", "county_subdivision")}
assert len(rows) == 50
assert {r["worker_id"] for r in rows} == {"worker_1"}
assert {r["future_live_queue_id"] for r in rows} == {"COORD-TIER1-WAVE2-SERIAL150-2026-07-22"}
assert {r["worker_state_scope"] for r in rows} == {"CROSS_STATE_TIER1_WAVE2"}
assert [int(r["tier1_rank"]) for r in rows] == list(range(151, 201))
assert {r["priority_tier"] for r in rows} == {"Tier 1"}
assert {r["future_scout_eligible_flag"] for r in rows} == {"true"}
assert {r["retry_flag"] for r in rows} == {"false"}
assert {r["failure_only_flag"] for r in rows} == {"false"}
assert {r["already_canonical_flag"] for r in rows} == {"false"}
assert {r["scout_coverage_status"] for r in rows} == {"not_scouted"}
assert len({r["municipality_id"] for r in rows}) == 50
assert len({r["census_gov_id"] for r in rows}) == 50
assert all(r["municipality_id"] and r["census_gov_id"] for r in rows)
assert all(r["search_hints_available"] == "true" for r in rows)
assert all(all(r[f"search_hint_{i}"] for i in range(1, 6)) for r in rows)
assert all((r["government_type"], r["geography_type"]) in allowed for r in rows)
assert hashlib.sha256(path.read_bytes()).hexdigest() == "f9cd191ca00e6e965cde83879a1383f23d1750b8e90d0a5812697c98aa19b20f"
print("PASS: Tier 1 Wave 2 Worker 1 locked-input gate")
PY
```

Record a protected-file baseline for `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, national queue/coverage/priority outputs, dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect `.env` or credential values.

## Run exactly one offline dry run

Require `tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1` not to exist, then run exactly:

```bash
test ! -e tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1
"$PYTHON" scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_wave2_worker_1_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1 \
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

Do not add `--live`. Dry-run pacing is metadata/planning only and must make no backend call or sleep between backend requests.

## Review all 50 prompts

Inspect `tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1/prompt_preview.md`, `row_timing.csv`, and `run_metadata.json`; create `docs/analysis/tier1_wave2_worker_1_filter_contract_dry_run_review_20260722_attempt1.md`. Confirm 50/50 exact row identities, compact mode, all five deterministic query hints, municipality/state/locked municipality ID/government name/Census ID/county context/expected units/verification notes, strict employer/unit/source controls, valid-empty guidance, blocked/dead separation, duplicate controls, unverified-stage handling, public-records prohibition, and unchanged output schema requirements.

Also confirm mixed-state mode, 50 requested prompts, cap 50, `sleep_between_prompts=5.0`, adaptive mode and values 3/5/15/10/25/2 in metadata, `live_attempted=false`, `backend_call_returned=false`, dry-run-completed lifecycle, and exactly 50 `dry_run_planned` timing rows with no response IDs or tokens.

## No-network validation

Run only:

```bash
"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py
"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py
git diff --check
```

Create `docs/analysis/tier1_wave2_worker_1_no_network_validation_20260722_attempt1.md` with commands, exit codes, concise output, Python executable, protected-file comparison, and explicit no-network/no-backend confirmation. The locked input/audit/prompt must remain byte-identical.

## Commit and sanitized relay

Stage only worker-created review/validation evidence and commit locally as `Prepare Tier 1 Wave 2 Worker 1 offline dry run`. Do not commit dry-run `tmp/`, `.venv`, `.env`, local excludes, credentials, or unrelated files. Do not push.

Create a fresh sanitized relay containing the locked input/audit/prompt, review, validation, prompt preview, `row_timing.csv`, `run_metadata.json`, dry-run artifacts, protected comparison, git status/log/diff/changed files, and `next_task.md` saying prep-only and coordinator owns any preflight/live run. Exclude `.env`, `.venv`, credentials, tokens, cookies, secrets, caches, and unrelated files.
Copy the finished ZIP into the main coordinator directory `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp/` and preserve its basename exactly.

Use this exact naming/copy sequence:

```bash
COMMIT="$(git rev-parse --short HEAD)"
RELAY="tmp/tier1_wave2_worker_1_prep_relay_2026-07-22_${COMMIT}.zip"
STAGE="tmp/tier1_wave2_worker_1_prep_relay_2026-07-22_${COMMIT}"
test ! -e "$STAGE"
test ! -e "$RELAY"
mkdir -p "$STAGE/docs/analysis" "$STAGE/dry_run" "$STAGE/evidence"
cp docs/analysis/tier1_wave2_worker_1_scout_input_2026-07-22.csv docs/analysis/tier1_wave2_worker_1_input_audit_2026-07-22.md docs/analysis/tier1_wave2_worker_1_prep_prompt_2026-07-22.md "$STAGE/docs/analysis/"
cp docs/analysis/tier1_wave2_worker_1_filter_contract_dry_run_review_20260722_attempt1.md docs/analysis/tier1_wave2_worker_1_no_network_validation_20260722_attempt1.md "$STAGE/docs/analysis/"
cp -R tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1/. "$STAGE/dry_run/"
git status --short > "$STAGE/evidence/git_status_post_commit.txt"
git log -1 --oneline > "$STAGE/evidence/git_log_latest.txt"
git diff main...HEAD --stat > "$STAGE/evidence/patch_diff_summary.txt"
git diff main...HEAD --name-only > "$STAGE/evidence/changed_files.txt"
git diff --exit-code main -- data/contracts.csv data/city_coverage.csv corpus docs/analysis/national_scout_candidate_queue_2026-07-20.csv docs/analysis/national_scout_coverage_municipality_2026-07-20.csv docs/analysis/national_municipality_priority_tiers_2026-07-22.csv docs/analysis/national_priority_tier_top_targets_2026-07-22.csv docs/analysis/municipality_search_hints_2026-07-22.csv docs/dashboard .github/workflows > "$STAGE/evidence/protected_file_comparison.txt"
printf "%s\n" "Prep only complete; coordinator owns preflight/live and must inspect this relay." > "$STAGE/next_task.md"
zip -qr "$RELAY" "$STAGE"
COORDINATOR_TMP="/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
mkdir -p "$COORDINATOR_TMP"
cp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
cmp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
shasum -a 256 "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
```

The copied basename must remain `tier1_wave2_worker_1_prep_relay_2026-07-22_<commit>.zip`. Inspect ZIP filenames and stop if any secret/credential/environment/cache path appears.

## Final response

Report branch/commit, locked hash and 50-row gate, rank/state profile, compact/hints/adaptive metadata, 50/50 review, timing result, validation/protected-file result, worker relay path, copied coordinator relay path/hash, and confirmation that no live/API/model/smoke/diagnostic/URL/verification/ingestion/codify/queue/coverage/remote/push action occurred.
