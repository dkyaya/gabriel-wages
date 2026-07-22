# Coordinator 150-Row Serialized Live Dry-Run Review

Date: 2026-07-21

Result: **PASS — all 150 corrected mixed-state prompts satisfy the locked row-identity and source-scout filter contract. Smoke is permitted to proceed under the task's one-smoke authorization.**

## Command and input identity

The main coordinator ran exactly:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/coordinator_150row_serial_live_input_2026-07-21.csv \
  --output-dir tmp/coordinator_150row_serial_live_dry_run_2026-07-21 \
  --prompt-mode minimal \
  --live-hard-cap 150
```

The locked input SHA-256 remained:

```text
e53db4698b5dba439ad4d31fca79be1242808960d1a8d6809d31b1b915de62fc
```

Run ID: `all_2026-07-21_193255`.

## Metadata gate

| Field | Required | Observed | Result |
| --- | --- | --- | --- |
| `mode` | `dry_run` | `dry_run` | PASS |
| `municipalities_requested` | 150 | 150 | PASS |
| `input_states` | CA, NJ, TX | CA, NJ, TX | PASS |
| `allow_mixed_states` | `true` | `true` | PASS |
| `live_hard_cap` | 150 | 150 | PASS |
| `live_attempted` | `false` | `false` | PASS |
| `backend_call_returned` | `false` | `false` | PASS |
| `execution_status` | `dry_run_completed` | `dry_run_completed` | PASS |

The dry-run directory contains only `prompt_preview.md` and `run_metadata.json`. No live backend was selected or invoked, no credential was read by the dry path, and no API/model/hosted-search call occurred.

## All-prompt audit

The audit parsed the 150 prompt sections, zipped them to the locked CSV rows in file order, and required the identifier suffix to match each row's exact `municipality_id`.

| Required prompt element or control | Result |
| --- | ---: |
| Municipality name | 150/150 |
| Row state | 150/150 |
| Locked internal `municipality_id` | 150/150 |
| Exact `government_name` | 150/150 |
| Exact Census government ID | 150/150 |
| Complete county-context summary | 150/150 |
| Exact expected-units instruction | 150/150 |
| Complete row-specific verification notes | 150/150 |
| Strict employer/unit/source controls | 150/150 |
| Empty/no-candidate guidance | 150/150 |
| Blocked/unreadable versus dead/unreachable separation | 150/150 |
| Unverified scout-stage quarantine | 150/150 |
| Locked file order and identifier mapping | 150/150 |

The controls prohibit counties, township governments, schools, transit and regional authorities, special districts, and private providers from substituting for the locked municipal employer. They preserve ordinary civilian comparator scope, safety/non-safety separation, context/insufficient classifications, visible-year requirements, duplicate and overlap states, and permission to return an empty candidate list rather than invent a source.

## Disposition

The corrected-code mixed-state dry gate is complete. The 150 rows and prompts are in CA50 → NJ50 → TX50 order, no row was lost or truncated, and the prompt-contract omission identified by Worker 2 is corrected across all three batches. Proceed to exactly one direct-SDK no-search smoke. If any smoke condition fails, stop without live execution.
