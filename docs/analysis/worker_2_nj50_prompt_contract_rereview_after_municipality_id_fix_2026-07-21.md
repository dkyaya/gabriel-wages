# Worker 2 NJ50 Prompt-Contract Rereview After Municipality-ID Fix

Date: 2026-07-21

Result: **PASS — 50/50 regenerated prompt blocks satisfy the corrected row-identity and filter contract.**

## Scope and command

The main coordinator regenerated the locked NJ50 input with the patched local runner in dry-run mode only:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state NJ \
  --municipalities-csv docs/analysis/worker_2_nj50_scout_input_2026-07-21.csv \
  --output-dir tmp/coordinator_regenerated_worker_2_nj50_dry_run_after_municipality_id_fix_2026-07-21 \
  --prompt-mode minimal
```

The output contains only `prompt_preview.md` and `run_metadata.json`. Metadata identifies run `nj_2026-07-21_191043`, 50 requested municipalities, `mode=dry_run`, `execution_status=dry_run_completed`, `live_attempted=false`, `backend_call_returned=false`, and `model_response_succeeded=false`. No live backend was selected or invoked, and no API/model/hosted-search call occurred.

## Exact 50-row audit

The rereview parsed all 50 prompt blocks in locked CSV order and compared each block to its corresponding input row.

| Required control | Result |
| --- | --- |
| Prompt count and locked input count | 50/50 |
| `Locked internal municipality ID: <municipality_id>` | 50/50 |
| Exact `government_name` | 50/50 |
| Exact Census government ID | 50/50 |
| Complete `county_context_summary` | 50/50 |
| Exact expected-unit search instruction | 50/50 |
| Row-specific verification cautions | 50/50 |
| Exact-employer and prohibited-substitute controls | 50/50 |
| Police/fire versus ordinary civilian unit controls | 50/50 |
| Context-only/insufficient and blocked/dead separation | 50/50 |
| Visible-year, duplicate, overlap, and no-candidate guidance | 50/50 |
| Unverified scout-stage quarantine | 50/50 |

Westfield now visibly includes all three identity components in the prompt body: `TOWN OF WESTFIELD`, Census government ID `170248`, and locked internal municipality ID `cog_2025_170248`. The same exact-row check passed for the other 49 rows.

## Disposition

The municipality-ID omission that caused the Worker 2 relay review to fail is corrected. NJ50 is now prep-complete only when the original Worker 2 relay is read together with this coordinator regeneration and rereview. This pass does not authorize a smoke or live scout and creates no discovery coverage. No URL was opened, no source was verified, no candidate was promoted, and no queue, coverage, canonical, ingestion, corpus, codified, or claim file changed.
