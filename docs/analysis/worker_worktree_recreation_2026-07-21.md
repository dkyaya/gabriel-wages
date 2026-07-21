# Worker Worktree Recreation Report

Date: 2026-07-21

Disposition: **Worker 1, Worker 2, and Worker 3 were recreated cleanly from planning commit `1d68a0e`; the dashboard worktree and all research/data workflows were untouched.**

## Scope and starting state

- Main coordinator repository: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`
- Starting main commit: `1d68a0ef970391317c5511d88cc6cfa6fa24bb63`
- Planning commit used: `1d68a0e` — `Prepare CA NJ TX 50-row scout batches`
- Main tracked status before maintenance: clean.
- Ignored maintenance context: untracked `package-lock.json` remained in the main repository and was not changed, deleted, or committed.
- Existing dashboard worktree before and after maintenance: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-dashboard` at `87c568c` on `dashboard-scaffold`.

No Git remote was inspected, configured, created, validated, or modified. No fetch, pull, or push occurred.

## Old worker cleanup

- Worker 1 was not registered as a worktree when removal began; `git worktree remove --force` therefore reported that it was not a working tree.
- Worker 2 was registered at `12f7293` on `worker-2` and was removed.
- Worker 3 was registered at `2e8ea73` on `worker-3` and was removed.
- Stale worktree metadata was pruned.
- Maintenance timestamp: `20260721_184813`.
- No leftover `gabriel-worker-1`, `gabriel-worker-2`, or `gabriel-worker-3` directory remained after removal, so no directory was moved to a `_broken_20260721_184813` path.
- The pre-existing local `worker_1_ca50_prep_20260721` branch was deleted before recreation. The corresponding Worker 2 and Worker 3 prep branch names did not exist locally and required no deletion.
- The dashboard worktree was not removed, moved, pruned as stale, edited, or otherwise touched.

## Recreated worktrees

| Worker | Path | Branch | HEAD | Tracked status |
| --- | --- | --- | --- | --- |
| Worker 1 | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1` | `worker_1_ca50_prep_20260721` | `1d68a0e` | clean |
| Worker 2 | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2` | `worker_2_nj50_prep_20260721` | `1d68a0e` | clean |
| Worker 3 | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-3` | `worker_3_tx50_prep_20260721` | `1d68a0e` | clean |

All three worktrees were created with `git worktree add -b <branch> <path> 1d68a0e`. Final `git branch --show-current`, `git rev-parse HEAD`, `git show --no-patch --oneline HEAD`, and tracked-only porcelain checks matched the table.

## Local excludes and Python availability

The requested local exclude entries were configured through the repository-local Git exclude file:

- `.venv/`
- `.env`
- `.claude/`
- `__pycache__/`
- `.pytest_cache/`

Because `.venv` is a symlink rather than a directory, the additional local-only `.venv` pattern was added so the symlink itself remains excluded and cannot be accidentally committed.

The main environment existed at `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/.venv`, and `bin/python` was executable. Each worker now has an ignored local `.venv` symlink pointing to that existing environment. No virtual environment was created and no package installation ran.

## Required-file verification

All required files exist in each applicable worker:

- `AGENTS.md`
- the worker-specific 50-row scout input CSV
- the worker-specific selection methodology
- the worker-specific offline prep prompt
- `docs/analysis/three_worker_50row_batch_plan_2026-07-21.md`
- `docs/prompts/gabriel_parallel_worker_template.md`
- `scripts/gabriel_state_source_scout.py`
- `scripts/test_gabriel_state_source_scout_prompt.py`

The check covered 24 worker/file combinations and passed without a missing file. No worker batch input file was edited.

## No-network Python checks

Each worker used `.venv/bin/python` and passed:

```text
python -m py_compile scripts/gabriel_state_source_scout.py
python -m py_compile scripts/test_gabriel_state_source_scout_prompt.py
```

Result: six successful compile checks, two per worker. Only ignored `__pycache__` bytecode could be written. No direct-SDK test, API client request, smoke preflight, scout, dry run, model call, hosted search, or network action ran.

## Protected-state confirmation

This task did not run or modify any of the following:

- Gabriel scouts or dry runs;
- API/model calls or smoke preflights;
- source URLs, source verification, or downloads;
- ingestion or `gabriel.codify`;
- `data/contracts.csv`, `data/city_coverage.csv`, or corpus files;
- national candidate queue or municipality/state/county coverage outputs;
- dashboard files or dashboard builds;
- worker batch inputs;
- Git remotes, fetch, pull, or push; or
- environment variables, credential values, `.env` contents, or secrets.

## Next instructions

Rerun the Worker 1, Worker 2, and Worker 3 offline prep prompts in their respective persistent worktrees. Skip any branch-switching or worktree-creation step: the workers are already freshly created on the correct prep branches at `1d68a0e`. Each next worker task remains dry-run/prep only under its locked prompt; it does not inherit live, smoke, API/model, verification, ingestion, codification, or national accounting authority.
