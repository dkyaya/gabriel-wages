# Wave 2 Worker 2 TX50 Offline Preparation Prompt

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2`. This is offline preparation/dry review only. No remotes, push, fetch, pull, smoke, live scout, API/model call, hosted search, URL opening/download, verification, public-records action, ingestion, codify, queue/coverage rebuild, dashboard build, or protected canonical edit is permitted.

## 0. Worktree setup

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
  echo "ERROR: tracked worker files are dirty; stop"
  git status --short
  exit 1
}
git switch -C wave2_worker_2_tx50_prep_20260722 main
test "$(git branch --show-current)" = "wave2_worker_2_tx50_prep_20260722"
git show --no-patch --oneline HEAD
git status --short
PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python3
"$PYTHON" --version
```

Use local `main`; do not inspect a remote. Do not commit local excludes or `.venv` configuration.

## 1. Required files and input gate

Require and then read these files; use the shared template’s offline controls only:

```bash
test -f AGENTS.md
test -f docs/analysis/wave2_worker_2_tx50_scout_input_2026-07-22.csv
test -f docs/analysis/wave2_worker_2_tx50_selection_methodology_2026-07-22.md
test -f docs/analysis/wave2_worker_2_tx50_prep_prompt_2026-07-22.md
test -f docs/analysis/wave2_3x50_batch_plan_2026-07-22.md
test -f docs/prompts/gabriel_parallel_worker_template.md
test -f scripts/gabriel_state_source_scout.py
test -f scripts/test_gabriel_state_source_scout_prompt.py
```

Run:

```bash
"$PYTHON" - <<'PY'
import csv
from pathlib import Path
p = Path("docs/analysis/wave2_worker_2_tx50_scout_input_2026-07-22.csv")
rows = list(csv.DictReader(p.open(newline="", encoding="utf-8")))
forbidden = {"Bloomington", "Oakland", "Stockton", "Oxnard", "Redding", "Fairfield", "Princeton", "Moreno Valley"}
bad = ("COUNTY OF", "SCHOOL DISTRICT", "TRANSIT AUTHORITY", "HOUSING AUTHORITY", "PORT AUTHORITY", "AIRPORT AUTHORITY", "PARK DISTRICT", "TOWNSHIP", "INDUSTRIAL DISTRICT", "UNIVERSITY", "UTILITY DISTRICT")
assert len(rows) == 50
assert {r["worker_id"] for r in rows} == {"worker_2"}
assert {r["future_live_queue_id"] for r in rows} == {"COORD-SERIAL150-WAVE2-2026-07-22"}
assert {r["state"] for r in rows} == {"TX"}
assert len({r["municipality_id"] for r in rows}) == 50
assert len({r["census_gov_id"] for r in rows}) == 50
assert {(r["government_type"], r["geography_type"]) for r in rows} == {("municipal", "place")}
assert {r["already_scouted_status"] for r in rows} == {"no"}
assert {r["coverage_status_before_run"] for r in rows} == {"not_scouted"}
assert not ({r["municipality"] for r in rows} & forbidden)
assert not any(x in r["government_name"].upper() for r in rows for x in bad)
assert [int(r["priority_rank"]) for r in rows] == list(range(1, 51))
print("PASS: Worker 2 TX50 locked-input contract")
PY
```

Stop without substitution if it fails. Record protected-file baselines for canonical data/corpus, national queue/coverage/builders, PROGRESS/handoff, dashboard, and workflows.

## 2. Dry run and review

Resolve `$PYTHON`, choose a fresh attempt label/output path, and run only:

```bash
"$PYTHON" scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state TX \
  --municipalities-csv docs/analysis/wave2_worker_2_tx50_scout_input_2026-07-22.csv \
  --output-dir tmp/wave2_worker_2_tx50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal \
  --sleep-between-prompts 5
```

Require dry-run lifecycle, 50 requests, five-second metadata, no live/backend attempt, and 50 dry-planned `row_timing.csv` rows. Inspect every prompt and write `docs/analysis/wave2_worker_2_tx50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md` with 50/50 counts for municipality, TX, internal ID, government name, Census ID, county context, expected units, verification notes, employer/unit/source and ordinary-non-safety controls, empty-result guidance, blocked/dead separation, duplicate controls, unverified-stage handling, public-records prohibition, and no invented URLs. Anything below 50/50 stops prep.

## 3. Validation, commit, and relay

Run only:

```bash
"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py
"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py
git diff --check
```

Prove protected paths match local `main`. Create one local batch-prep commit. Create `tmp/wave2_worker_2_tx50_prep_relay_<ATTEMPT_LABEL>_<commit>.zip` containing the locked input/methodology/prompt, complete dry artifacts including timing and metadata, 50/50 review, validation, git status/log/diff/changed files, protected-file comparison, and `next_task.md`. The note must say prep-only and coordinator-owned smoke/live. Do not push.
