# Tier 1 Worker 2 Offline Preparation Prompt

Use Codex Routine / GPT-5.6 Terra Medium.

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2`. This is offline preparation and prompt dry-run review only. Do not run a smoke, live scout, API/model request, hosted search, URL opening/download, source verification, public-records action, ingestion, `gabriel.codify`, queue/coverage rebuild, dashboard build, or protected canonical edit. Do not inspect/configure/validate/modify remotes; do not push, fetch, or pull.

## 1. Worktree setup and fresh local branch

Run:

```bash
cd /Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2

EXCLUDE_FILE="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$EXCLUDE_FILE")"
grep -qxF ".venv/" "$EXCLUDE_FILE" || echo ".venv/" >> "$EXCLUDE_FILE"
grep -qxF ".env" "$EXCLUDE_FILE" || echo ".env" >> "$EXCLUDE_FILE"
grep -qxF ".claude/" "$EXCLUDE_FILE" || echo ".claude/" >> "$EXCLUDE_FILE"
grep -qxF "__pycache__/" "$EXCLUDE_FILE" || echo "__pycache__/" >> "$EXCLUDE_FILE"
grep -qxF ".pytest_cache/" "$EXCLUDE_FILE" || echo ".pytest_cache/" >> "$EXCLUDE_FILE"

test -z "$(git status --porcelain --untracked-files=no)" || {
  echo "ERROR: tracked worker files are dirty; stop before switching"
  git status --short
  exit 1
}

git switch -C tier1_worker_2_prep_20260722 main
test "$(git branch --show-current)" = "tier1_worker_2_prep_20260722"
git show --no-patch --oneline HEAD
git status --short

PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python3
"$PYTHON" --version
```

Use only the existing local `main` ref. Do not inspect a remote. Stop if tracked state is dirty. Local excludes and any `.venv` symlink are worktree configuration and must not be committed.

## 2. Required files and locked-input gate

Require and read, in order:

```bash
test -f AGENTS.md
test -f docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv
test -f docs/analysis/tier1_worker_2_input_audit_2026-07-22.md
test -f docs/analysis/tier1_worker_2_prep_prompt_2026-07-22.md
test -f docs/analysis/tier1_post_tiering_top150_input_audit_2026-07-22.md
test -f docs/analysis/tier1_worker_batch_split_design_audit_2026-07-22.md
test -f scripts/gabriel_state_source_scout.py
test -f scripts/test_gabriel_state_source_scout_prompt.py
```

The assigned contract is:

- Input: `docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv`
- Expected rows: 50
- Expected worker ID: `worker_2`
- Expected queue ID: `COORD-TIER1-WAVE1-SERIAL150-2026-07-22`
- Expected state scope: `CROSS_STATE_TIER1`
- Expected rank span: `51–100`
- Expected input SHA-256: `02c3e5ea8529a079d3a8286dfba371a55a94041a050e5b49941b1297767ae62a`

Run this no-network structural audit:

```bash
"$PYTHON" - <<'PY'
import csv, hashlib
from pathlib import Path

path = Path("docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv")
rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
known_failures = {
    ("CA", "Stockton"), ("CA", "Redding"), ("CA", "Oakland"),
    ("CA", "Moreno Valley"), ("CA", "Oxnard"), ("CA", "Fairfield"),
    ("IL", "Bloomington"), ("IL", "Huntley"), ("IL", "Roselle"),
    ("NJ", "Princeton"),
}
allowed = {("municipal", "place"), ("township", "county_subdivision")}
assert len(rows) == 50
assert {r["worker_id"] for r in rows} == {"worker_2"}
assert {r["future_live_queue_id"] for r in rows} == {"COORD-TIER1-WAVE1-SERIAL150-2026-07-22"}
assert {r["worker_state_scope"] for r in rows} == {"CROSS_STATE_TIER1"}
assert [int(r["tier1_rank"]) for r in rows] == list(range(51, 101))
assert {r["priority_tier"] for r in rows} == {"Tier 1"}
assert {r["future_scout_eligible_flag"] for r in rows} == {"true"}
assert {r["retry_flag"] for r in rows} == {"false"}
assert {r["failure_only_flag"] for r in rows} == {"false"}
assert {r["already_canonical_flag"] for r in rows} == {"false"}
assert {r["scout_coverage_status"] for r in rows} == {"not_scouted"}
assert len({r["municipality_id"] for r in rows}) == 50
assert all(r["municipality_id"] for r in rows)
assert len({r["census_gov_id"] for r in rows}) == 50
assert all(r["census_gov_id"] for r in rows)
assert not ({(r["state"], r["municipality"]) for r in rows} & known_failures)
assert all((r["government_type"], r["geography_type"]) in allowed for r in rows)
assert hashlib.sha256(path.read_bytes()).hexdigest() == "02c3e5ea8529a079d3a8286dfba371a55a94041a050e5b49941b1297767ae62a"
print("PASS: Tier 1 Worker 2 locked-input contract")
PY
```

If any check fails, stop. Do not edit, reorder, replace, or append a locked row. Consolidated municipal/place government labels remain exact authoritative employers; never substitute a standalone county or other prohibited entity.

## 3. Protected-file baseline

Before the dry run, record a scoped diff/hash baseline for `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, national queue/coverage files, all national priority outputs, dashboard files, `PROGRESS.md`, the main handoff, and workflows. Do not inspect `.env` or any credential value. At the end, require no changes from local `main` for these paths.

## 4. Run exactly one dry run

Require `tmp/tier1_worker_2_prep_dry_run_20260722_attempt1` not to exist. Then run exactly:

```bash
test ! -e tmp/tier1_worker_2_prep_dry_run_20260722_attempt1
"$PYTHON" scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_worker_2_prep_dry_run_20260722_attempt1 \
  --prompt-mode minimal \
  --live-hard-cap 50 \
  --sleep-between-prompts 5
```

Do not add `--live`. Do not run smoke or direct-SDK diagnostics. Dry-run sleep is configuration metadata only and must not invoke a backend wait or request.

## 5. Inspect all 50 prompts and timing metadata

Inspect `tmp/tier1_worker_2_prep_dry_run_20260722_attempt1/prompt_preview.md`, `tmp/tier1_worker_2_prep_dry_run_20260722_attempt1/row_timing.csv`, and `tmp/tier1_worker_2_prep_dry_run_20260722_attempt1/run_metadata.json`. Create `docs/analysis/tier1_worker_2_filter_contract_dry_run_review_20260722_attempt1.md`.

The review must record 50/50 prompt presence for municipality, state, locked internal municipality ID, exact government name, Census government ID, county context, expected units, verification cautions, strict employer/unit/source controls, no-candidate guidance, blocked/dead separation, duplicate controls, unverified-stage handling, and the public-records prohibition. It must also confirm:

- `input_states` equals the exact distinct states in the locked input;
- `allow_mixed_states=true`;
- `municipalities_requested=50`;
- `live_hard_cap=50`;
- `sleep_between_prompts=5.0`;
- `live_attempted=false`;
- `backend_call_returned=false`;
- lifecycle is `dry_run_completed`; and
- `row_timing.csv` has 50 rows in locked order with `success_status=dry_run_planned` and no token/response IDs.

Use exact row identity, not fuzzy name matching. A valid empty-source instruction is required; it is not a dry-run failure.

## 6. No-network validation only

Run only:

```bash
"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py
"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py
git diff --check
```

Create `docs/analysis/tier1_worker_2_no_network_validation_20260722_attempt1.md` with commands, exit codes, concise output, Python executable, and an explicit statement that no network/API/model/backend call occurred. Do not run a smoke preflight or any live/direct-SDK invocation.

Recheck protected files against local `main`. Only the worker review/validation/relay documentation may be new or changed. The locked CSV, its input audit, and this prep prompt must remain byte-identical.

## 7. Local worker commit

Stage only the worker-created review and validation/report files. Inspect the staged names, then commit locally:

```bash
git add docs/analysis/tier1_worker_2_filter_contract_dry_run_review_20260722_attempt1.md docs/analysis/tier1_worker_2_no_network_validation_20260722_attempt1.md
git diff --cached --name-only
git commit -m "Prepare Tier 1 Worker 2 offline dry run"
git status --short
```

Do not commit `.venv`, local excludes, dry-run `tmp/` contents, `.env`, credentials, or unrelated files. Do not push.

## 8. Sanitized relay and mandatory copy to coordinator tmp

Create a fresh staging directory. The relay must contain the locked input/audit/prompt, dry-run artifacts including `prompt_preview.md`, `row_timing.csv`, and `run_metadata.json`, review, validation, protected-file comparison, git status/log/diff/changed-file evidence, and `next_task.md` saying prep-only and coordinator owns smoke/live. Exclude `.env`, `.venv`, credentials, caches, and secrets.

Use the exact naming and copy pattern:

```bash
COMMIT="$(git rev-parse --short HEAD)"
RELAY="tmp/tier1_worker_2_prep_relay_2026-07-22_${COMMIT}.zip"
STAGE="tmp/tier1_worker_2_prep_relay_2026-07-22_${COMMIT}"
test ! -e "$STAGE"
test ! -e "$RELAY"
mkdir -p "$STAGE/docs/analysis" "$STAGE/dry_run" "$STAGE/evidence"
cp docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv docs/analysis/tier1_worker_2_input_audit_2026-07-22.md docs/analysis/tier1_worker_2_prep_prompt_2026-07-22.md "$STAGE/docs/analysis/"
cp docs/analysis/tier1_worker_2_filter_contract_dry_run_review_20260722_attempt1.md docs/analysis/tier1_worker_2_no_network_validation_20260722_attempt1.md "$STAGE/docs/analysis/"
cp -R tmp/tier1_worker_2_prep_dry_run_20260722_attempt1/. "$STAGE/dry_run/"
git status --short > "$STAGE/evidence/git_status_post_commit.txt"
git log -1 --oneline > "$STAGE/evidence/git_log_latest.txt"
git diff main...HEAD --stat > "$STAGE/evidence/patch_diff_summary.txt"
git diff main...HEAD --name-only > "$STAGE/evidence/changed_files.txt"
git diff --exit-code main -- data/contracts.csv data/city_coverage.csv corpus docs/analysis/national_scout_candidate_queue_2026-07-20.csv docs/analysis/national_scout_coverage_municipality_2026-07-20.csv docs/analysis/national_municipality_priority_tiers_2026-07-22.csv docs/analysis/national_priority_tier_top_targets_2026-07-22.csv docs/dashboard .github/workflows > "$STAGE/evidence/protected_file_comparison.txt"
printf "%s\n" "Worker 2 prep only is complete. Coordinator must inspect this relay and owns any later dry merge, smoke, or live scout." > "$STAGE/next_task.md"
zip -qr "$RELAY" "$STAGE"
unzip -Z1 "$RELAY" > "$STAGE/evidence/relay_contents.txt"
COORDINATOR_TMP="/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/tmp"
mkdir -p "$COORDINATOR_TMP"
cp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
cmp "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
shasum -a 256 "$RELAY" "$COORDINATOR_TMP/$(basename "$RELAY")"
```

The final relay basename must remain `tier1_worker_2_prep_relay_2026-07-22_<commit>.zip` in the coordinator repo's `tmp/`. This copy is mandatory. Before copying, inspect ZIP filenames (not credential contents) and stop if `.env`, credential, token, cookie, secret, `.venv`, or cache files appear.

## Final response

Report: branch/commit; input hash; 50-row gate; state/rank distribution; dry-run metadata; 50/50 prompt-contract result; timing-row result; validation result; protected-file result; worker relay path; copied coordinator relay path/hash; and confirmation that no smoke/live/API/model/URL/verification/ingestion/codify/queue/coverage/remote/push action occurred.
