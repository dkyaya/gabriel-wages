# Future Coordinator Prompt Template — 2×2000 URL-Routing Collection

Use only with a future queue containing new or unrouted candidate URLs and
under separate explicit authorization to open those URLs.

## Placeholders

- Repository: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`
- Round ID: `<FUTURE_ROUND_ID>`
- Candidate queue: `<FUTURE_CANDIDATE_QUEUE_CSV>`
- Prior cumulative routing ledger:
  `<OPTIONAL_PRIOR_CUMULATIVE_LEDGER_CSV>`

## Authorization boundary

This prompt authorizes bounded URL-routing collection and lane audit only. It
does not authorize a durable ledger merge, scouting, ingestion, codification,
document extraction, wage extraction, wage-gap analysis, causal claims,
regressions, remote inspection, or push.

## Offline readiness

1. Require a clean tracked worktree and the committed `bulk_2x2000` planner,
   bounded verifier, two-lane auditor, and cumulative merge safeguards.
2. Read the future queue and any prior cumulative ledger locally.
3. Run:

```bash
python scripts/prepare_scaled_verification_batches.py \
  --candidate-queue-csv <FUTURE_CANDIDATE_QUEUE_CSV> \
  --output-dir docs/analysis/verification_rounds/<FUTURE_ROUND_ID> \
  --round-id <FUTURE_ROUND_ID> \
  --profile bulk_2x2000 \
  --exclude-verified-ledger-csv <OPTIONAL_PRIOR_CUMULATIVE_LEDGER_CSV> \
  --priority-scope future_unverified \
  --balance-lanes \
  --capacity-only-plan \
  --plan-only
```

If no prior ledger exists for the future queue, omit that argument and
document why. Never use `--allow-reroute-already-verified` without a separate
explicit reroute decision.

4. Stop if the plan is a zero-row sentinel. Do not manufacture work.
5. For a nonempty plan, require no more than two lanes, no more than 2,000
   rows per lane, unique candidate and verification identities, zero prior
   overlap, balanced rows, stable duplicate groups, and zero URL opens.
6. Run fresh dry runs for both nonempty lane inputs and audit them together.
   Require every row terminal as `dry_run_planned`, zero network calls, and
   no artifacts/downloads.

## Bounded live collection

Only after explicit live authorization, run the exact generated commands with:

- two lanes maximum;
- concurrency eight per lane;
- 20/8/15-second total/connect/read timeouts;
- five redirects;
- 10 MiB response ceiling;
- disabled content samples;
- lane-local metadata artifacts;
- incremental ledger/timing/summary checkpoints; and
- duplicate reuse within each lane.

Launch Lane 1, confirm checkpoint and artifact lifecycle health, then launch
Lane 2. Do not launch a third lane or increase concurrency. Preserve healthy
sibling work if one lane fails. Do not reuse or overwrite output directories.

## Audit and stop

After both lanes terminate, run `scripts/audit_verification_lanes.py`. Review
input hashes, terminal coverage, duplicate identities/groups, status and
content-type distributions, byte buckets, artifact integrity, and the merge
recommendation.

Create a collection review, validation record, one local commit, and relay.
Stop before the durable routing-ledger merge regardless of recommendation.
Do not ingest, codify, extract wages, calculate gaps, or turn routing outcomes
into evidence claims.
