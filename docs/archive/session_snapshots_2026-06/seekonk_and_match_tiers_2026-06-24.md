# 2026-06-24 - Seekonk ingestion and match-tier update snapshot

## Summary

This session closed out two linked workstreams:

1. Seekonk official contract archive ingestion added six clean public CBA rows from the official archive.
2. Coverage-audit logic now distinguishes exact-cycle, overlap-cycle, adjacent-cycle, and unmatched safety rows, with tests and methodology notes updated to match.

No GABRIEL run was performed. No new downloads, PRRs, or additional ingestion work were done for this final snapshot task.

## Files known to have been created or edited in this line of work

- `ingest/audit_coverage.py`
- `ingest/test_pipeline.py`
- `docs/hypotheses.md`
- `docs/hypotheses_public_source_strategy_2026-06-24.md`
- `inbox/manifest.csv`
- `data/contracts.csv`
- `data/city_coverage.csv`
- `corpus/ma_seekonk/`
- `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md`
- `docs/acquisition/ma_school_committee_meeting_materials_recon_2026-06-24.md`

## Seekonk rows ingested

- `ma_seekonk_police_2022`
- `ma_seekonk_fire_2022`
- `ma_seekonk_clerical_admin_2021`
- `ma_seekonk_teacher_2021`
- `ma_seekonk_public_works_2023`
- `ma_seekonk_library_2023`

## Corpus snapshot

- contracts: 20
- cities: 7
- healthy matched pairs: 6
- exact-cycle: 3
- overlap-cycle: 3
- exploratory adjacent matches: 0
- unmatched safety units: 3

## Test, validation, and audit results

```text
python ingest/test_pipeline.py
40 passed, 0 failed

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3 | cities: 7
healthy matched pairs: 6
  exact-cycle: 3
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

Unmatched safety units at snapshot time:

- `ma_somerville_police_spsoa_2012`
- `ma_somerville_police_spea_2012`
- `ma_newton_police_2015`

## Current methodological state

- Exact-cycle and overlap-cycle matches count as healthy.
- Adjacent-cycle matches remain exploratory and are not counted as healthy.
- Silence in CBAs or MOAs on comparability may reflect document opacity or institutionalized bargaining conventions, not necessarily true absence of comparability logic.
- v9 GABRIEL remains premature.

## Recommended next work

- Do one more public-source expansion pass.
- Target official portals that expose safety plus clean non-safety contracts.
- Keep Newton, Somerville, and Boston mechanism-evidence routes alive.
- Do not open PRR work unless the PI changes preference.
- Do not run v9 yet.

## Git and repo status

This directory is initialized as a Git repo, so a local Git snapshot remains possible.

For this audit task, `git status --short` showed an already-dirty working tree with tracked modifications and untracked files, including the Seekonk corpus/materials and coverage-audit work. No commit or reset action was taken.
