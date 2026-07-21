# Combined Gabriel State Scout Template

Use this template for one state batch handled end-to-end in one repository. It is reusable: replace all `{{PLACEHOLDER}}` values and retain the gates and prohibitions unchanged.

## Mission and authority

Prepare and, only with explicit authorization, scout the locked `{{STATE}}` batch. This is discovery only. Candidates must remain `unverified_scout_candidate`; no returned source is opened, downloaded, verified, ingested, codified, or used as evidence.

Use Heavy / GPT-5.6 Sol for selection, methodology, debugging, architecture, or prompt/filter-contract changes. Use Routine / GPT-5.6 Terra for the locked run and its accounting. Use Low / GPT-5.4 only for tiny documentation cleanup.

Before acting, read `AGENTS.md`, the newest `PROGRESS.md` and handoff entries, the current scout workflow, relevant selection/build scripts, and the locked batch input. Record the starting local commit. Do not inspect or modify remotes and do not push.

## Parameters

| Parameter | Value |
| --- | --- |
| State | `{{STATE}}` |
| Batch label | `{{BATCH_LABEL}}` |
| Date | `{{DATE}}` |
| Locked input | `{{INPUT_CSV}}` |
| Batch size | `{{BATCH_SIZE}}` (normally 25) |
| Output directory | `{{OUTPUT_DIR}}` |
| Cost-log path | `{{COST_LOG_PATH}}` |

## Gate 0 — select or prepare a locked 25-row batch, if needed

If a suitable locked input does not already exist, build one before any dry or live run. Select exactly 25 eligible municipal/place employers in one state; require distinct municipality and Census identifiers, the target state, no overlap with successfully scouted or failure-only rows unless separately authorized, no queue/canonical conflict, and no prohibited government type. Document the deterministic selection logic and parse-back assertions. Do not verify sources while selecting.

If an input already exists, validate that it still contains the exact locked rows. Never silently substitute, add, reorder, or retry municipalities.

## Gate 1 — dry-run prompt preview and checklist

Run the scout in dry-run mode only. Use the project command shape below, filling placeholders:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state {{STATE}} \
  --municipalities-csv {{INPUT_CSV}} \
  --output-dir {{DRY_RUN_OUTPUT_DIR}} \
  --prompt-mode minimal
```

Inspect every rendered prompt and write a dated filter-contract review. For every row, confirm: exact employer and Census ID; wrong-employer exclusions; ordinary municipal non-safety comparator definition; safety is not non-safety; context is distinct from a candidate; blocked is distinct from dead; visible years; duplicate handling; matched-cycle purpose; permitted empty candidate lists; public-records prohibition; and unverified scout-stage status.

Stop if the input or any checklist item fails. Correct the planning artifact, rerun dry review, and do not smoke or scout until the review passes.

## Gate 2 — direct-SDK smoke preflight

Only after Gate 1 passes and live API use is explicitly authorized, run one synthetic preflight:

```bash
.venv/bin/python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir {{SMOKE_OUTPUT_DIR}}
```

The preflight must send exactly `Reply with OK.`, use the configured direct SDK and HUIT `/v2` endpoint, use no search/tools, make one request, use a timeout no higher than 30 seconds, and use zero retries. Require nonempty `OK`/`OK.`, a response ID when exposed, positive output tokens, success metadata, and no connection error.

If it fails, stop. Preserve a sanitized stop note and relay; do not make a live scout request.

## Gate 3 — exact live scout

Only after smoke success and separate explicit authorization for the live batch, run the exact locked input:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state {{STATE}} \
  --municipalities-csv {{INPUT_CSV}} \
  --output-dir {{OUTPUT_DIR}} \
  --prompt-mode minimal \
  --max-prompts {{BATCH_SIZE}} \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0 \
  --cost-log-path {{COST_LOG_PATH}}
```

Stop on repeated connection failures without response IDs or output tokens, a systematic parser/schema defect, or an unexpected scope/canonical mutation. Preserve partial artifacts and stopped-before-request rows. Do not retry timeout-only rows or substitute another municipality.

## Post-run accounting

Create normalized batch candidates and a review with municipality/unit counts, parseable empty outcomes, connection/parser failures, leakage, token usage, estimate-only cost, and boundaries. Keep every candidate unverified.

Update the national queue and scout coverage only after a successful single-batch run, preserving every prior row and separately accounting for candidate-positive, parseable-empty, failure-only, and stopped-before-request outcomes. Rebuild each national accounting output once, validate, and record the result in the handoff/session log.

Run the required local validation suite, including:

```bash
python scripts/validate.py
python ingest/test_pipeline.py
python ingest/audit_coverage.py
```

Commit one intentional local batch/accounting change and create a sanitized relay with changed files, dry/smoke/live artifacts as applicable, validation outputs, git summaries, and a next-task note. Do not push.

## Absolute prohibitions

No source verification, URL opening/downloading, ingestion, `gabriel.codify`, changes to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`; no public-records requests; no automatic retries; no remote action; and no secrets in logs or relays.
