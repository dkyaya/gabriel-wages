# Wave 2 Worker 3 IL50 Offline Preparation Prompt

Work only in `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-3`. This is offline preparation/dry review only. Do not inspect/modify remotes; do not push/fetch/pull; and do not run a smoke, live scout, API/model call, hosted search, URL opening/download, verification, public-records action, ingestion, codify, queue/coverage rebuild, dashboard build, or protected canonical edit.

## 0. Worktree setup

```bash
cd /Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-3
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
git switch -C wave2_worker_3_il50_prep_20260722 main
test "$(git branch --show-current)" = "wave2_worker_3_il50_prep_20260722"
git show --no-patch --oneline HEAD
git status --short
PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python3
"$PYTHON" --version
```

Use only local `main`; local excludes and `.venv` are not commit content.

## 1. Required files and input gate

Require and read the following; use no smoke/live portion of the shared template:

```bash
test -f AGENTS.md
test -f docs/analysis/wave2_worker_3_il50_scout_input_2026-07-22.csv
test -f docs/analysis/wave2_worker_3_il50_selection_methodology_2026-07-22.md
test -f docs/analysis/wave2_worker_3_il50_prep_prompt_2026-07-22.md
test -f docs/analysis/wave2_3x50_batch_plan_2026-07-22.md
test -f docs/prompts/gabriel_parallel_worker_template.md
test -f scripts/gabriel_state_source_scout.py
test -f scripts/test_gabriel_state_source_scout_prompt.py
```

```bash
"$PYTHON" - <<'PY'
import csv
from pathlib import Path
p = Path("docs/analysis/wave2_worker_3_il50_scout_input_2026-07-22.csv")
rows = list(csv.DictReader(p.open(newline="", encoding="utf-8")))
forbidden = {"Bloomington", "Oakland", "Stockton", "Oxnard", "Redding", "Fairfield", "Princeton", "Moreno Valley"}
bad = ("COUNTY OF", "SCHOOL DISTRICT", "TRANSIT AUTHORITY", "HOUSING AUTHORITY", "PORT AUTHORITY", "AIRPORT AUTHORITY", "PARK DISTRICT", "TOWNSHIP", "INDUSTRIAL DISTRICT", "UNIVERSITY", "UTILITY DISTRICT")
assert len(rows) == 50
assert {r["worker_id"] for r in rows} == {"worker_3"}
assert {r["future_live_queue_id"] for r in rows} == {"COORD-SERIAL150-WAVE2-2026-07-22"}
assert {r["state"] for r in rows} == {"IL"}
assert len({r["municipality_id"] for r in rows}) == 50
assert len({r["census_gov_id"] for r in rows}) == 50
assert {(r["government_type"], r["geography_type"]) for r in rows} == {("municipal", "place")}
assert {r["already_scouted_status"] for r in rows} == {"no"}
assert {r["coverage_status_before_run"] for r in rows} == {"not_scouted"}
assert not ({r["municipality"] for r in rows} & forbidden)
assert not any(x in r["government_name"].upper() for r in rows for x in bad)
assert [int(r["priority_rank"]) for r in rows] == list(range(1, 51))
print("PASS: Worker 3 IL50 locked-input contract")
PY
```

`TOWN OF CICERO` is an allowed authoritative `municipal/place` incorporated employer, not a township row. Stop if any assertion fails; never substitute. Record protected canonical/global/dashboard/workflow baselines.

## 2. Dry run and 50/50 review

Resolve `$PYTHON`, use a unique fresh attempt path, and run only:

```bash
"$PYTHON" scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state IL \
  --municipalities-csv docs/analysis/wave2_worker_3_il50_scout_input_2026-07-22.csv \
  --output-dir tmp/wave2_worker_3_il50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal \
  --sleep-between-prompts 5
```

Require `dry_run_completed`, 50 prompts, sleep 5.0, no backend/live attempt, and 50 dry-planned timing rows. Inspect every prompt and write `docs/analysis/wave2_worker_3_il50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md`, proving 50/50 municipality, IL, internal ID, exact government, Census ID, county context, expected units, verification notes, strict employer/unit/source/ordinary-non-safety rules, empty-candidate guidance, blocked/dead separation, duplicate controls, unverified-stage handling, public-records prohibition, and no URL invention. Any shortfall stops prep.

## 3. Validation, commit, and relay

Run only:

```bash
"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py
"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py
git diff --check
```

Prove protected paths match local `main`. Create one local prep commit and `tmp/wave2_worker_3_il50_prep_relay_<ATTEMPT_LABEL>_<commit>.zip` with locked planning files, all dry artifacts including `row_timing.csv` and `run_metadata.json`, review, validation, git evidence, protected comparison, and a prep-only `next_task.md` assigning smoke/live exclusively to the main coordinator. Do not push.
