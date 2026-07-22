# Wave 2 Worker 1 CA50 Offline Preparation Prompt

Work only in:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1`

This is offline preparation and dry-run review only. Do not run a smoke, live scout, API/model request, hosted search, URL opening/download, source verification, public-records action, ingestion, `gabriel.codify`, queue/coverage rebuild, dashboard build, or protected canonical edit. Do not inspect or modify remotes; do not push, fetch, or pull.

## 0. Worktree setup and clean branch

Run locally:

```bash
cd /Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1

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

git switch -C wave2_worker_1_ca50_prep_20260722 main
test "$(git branch --show-current)" = "wave2_worker_1_ca50_prep_20260722"
git show --no-patch --oneline HEAD
git status --short

PYTHON=.venv/bin/python
test -x "$PYTHON" || PYTHON=python3
"$PYTHON" --version
```

Do not inspect a remote to update `main`; use the existing local `main` ref. Record the starting commit. Local excludes and a `.venv` symlink are untracked worktree configuration and must not be committed.

## 1. Required-file and locked-input gate

Require:

```bash
test -f AGENTS.md
test -f docs/analysis/wave2_worker_1_ca50_scout_input_2026-07-22.csv
test -f docs/analysis/wave2_worker_1_ca50_selection_methodology_2026-07-22.md
test -f docs/analysis/wave2_worker_1_ca50_prep_prompt_2026-07-22.md
test -f docs/analysis/wave2_3x50_batch_plan_2026-07-22.md
test -f docs/prompts/gabriel_parallel_worker_template.md
test -f scripts/gabriel_state_source_scout.py
test -f scripts/test_gabriel_state_source_scout_prompt.py
```

Read those files in that order. Use the shared worker template only for offline isolation, artifact, and validation discipline; its smoke/live gates are prohibited here.

Run this no-network structural audit:

```bash
"$PYTHON" - <<'PY'
import csv
from pathlib import Path

path = Path("docs/analysis/wave2_worker_1_ca50_scout_input_2026-07-22.csv")
rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
forbidden_names = {
    "Bloomington", "Oakland", "Stockton", "Oxnard", "Redding",
    "Fairfield", "Princeton", "Moreno Valley",
}
forbidden_employer_fragments = (
    "COUNTY OF", "SCHOOL DISTRICT", "TRANSIT AUTHORITY", "HOUSING AUTHORITY",
    "PORT AUTHORITY", "AIRPORT AUTHORITY", "PARK DISTRICT", "TOWNSHIP",
    "INDUSTRIAL DISTRICT", "UNIVERSITY", "UTILITY DISTRICT",
)
assert len(rows) == 50
assert {r["worker_id"] for r in rows} == {"worker_1"}
assert {r["future_live_queue_id"] for r in rows} == {
    "COORD-SERIAL150-WAVE2-2026-07-22"
}
assert {r["state"] for r in rows} == {"CA"}
assert len({r["municipality_id"] for r in rows}) == 50
assert len({r["census_gov_id"] for r in rows}) == 50
assert {r["government_type"] for r in rows} == {"municipal"}
assert {r["geography_type"] for r in rows} == {"place"}
assert {r["already_scouted_status"] for r in rows} == {"no"}
assert {r["coverage_status_before_run"] for r in rows} == {"not_scouted"}
assert not ({r["municipality"] for r in rows} & forbidden_names)
assert not any(
    fragment in r["government_name"].upper()
    for r in rows for fragment in forbidden_employer_fragments
)
assert [int(r["priority_rank"]) for r in rows] == list(range(1, 51))
print("PASS: Worker 1 CA50 locked-input contract")
PY
```

If any assertion fails, stop. Do not edit, replace, append, or reorder a row.

## 2. Protected-file baseline

Record hashes or a scoped diff baseline for `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, the national queue and municipality/state/county coverage files, their builders, `PROGRESS.md`, the main handoff, dashboard files, and workflows. At the end, require no difference from local `main` for those paths. Do not inspect `.env` or credential values.

## 3. Dry run only

Set a unique attempt label, verify the output path does not already exist, and run with the resolved interpreter:

```bash
"$PYTHON" scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state CA \
  --municipalities-csv docs/analysis/wave2_worker_1_ca50_scout_input_2026-07-22.csv \
  --output-dir tmp/wave2_worker_1_ca50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal \
  --sleep-between-prompts 5
```

Do not add `--live`. Do not run a smoke helper or test credential presence. Require `run_metadata.json` to report `mode=dry_run`, `execution_status=dry_run_completed`, `municipalities_requested=50`, `sleep_between_prompts=5.0`, `live_attempted=false`, and `backend_call_returned=false`. Require 50 rows in `row_timing.csv`, all `live_attempted=no`, `success_status=dry_run_planned`, and `parse_status=not_attempted`.

## 4. Review all 50 prompts

Inspect every prompt section in `prompt_preview.md`. Create:

`docs/analysis/wave2_worker_1_ca50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md`

Record deterministic 50/50 counts and representative excerpts for:

- municipality name and CA state;
- locked internal `municipality_id`;
- exact `government_name`;
- Census government ID;
- county context;
- expected units;
- verification notes;
- strict employer, unit, source, and ordinary non-safety controls;
- permission to return no candidates;
- blocked/unreadable versus dead/unreachable separation;
- duplicate and known-source controls;
- unverified-stage handling;
- public-records prohibition; and
- no invention of URLs.

Any result below 50/50 is a prep failure. Stop and preserve evidence; do not patch the runner or locked input in the worker task.

## 5. No-network validation

Run only:

```bash
"$PYTHON" -m py_compile scripts/gabriel_state_source_scout.py
"$PYTHON" -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
"$PYTHON" scripts/test_gabriel_state_source_scout_prompt.py
git diff --check
```

Then prove the protected paths are unchanged from local `main`. No queue/coverage or dashboard builder may run.

## 6. Worker commit and prep relay

Create one local worker commit containing only the new batch-specific dry-run review and intentionally tracked prep evidence. Do not commit `.venv`, local excludes, `.env`, raw credentials, or global outputs.

Create a sanitized relay under `tmp/`, for example:

`tmp/wave2_worker_1_ca50_prep_relay_<ATTEMPT_LABEL>_<commit>.zip`

Include the locked input, methodology, this prompt, complete dry-run directory (`prompt_preview.md`, `row_timing.csv`, `run_metadata.json`), 50/50 review, validation output, starting/latest commit, git status/log/diff/changed files, protected-file comparison, and `next_task.md`. The next-task note must say **prep-only; the main coordinator owns the one future smoke/live lane**. Do not push or perform any remote operation.
