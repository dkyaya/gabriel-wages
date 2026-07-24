# Future 2×2000 Verification Operating Procedure

Date: 2026-07-24

## Purpose

`bulk_2x2000` is a high-throughput **URL-routing-only** profile for a future
expanded candidate queue. It plans at most two lanes of 2,000 candidate rows,
for a 4,000-row round capacity. It records reachability, redirects, response
metadata, bounded byte counts, terminal transport statuses, and duplicate
reuse while preserving every candidate identity and original disposition.

It is not a profile for content review, document download, PDF parsing, OCR,
source-quality rating, ingestion, codification, wage extraction, or wage
analysis.

## When to use it

Use `bulk_2x2000` only when:

1. a canonical candidate queue contains a large set of genuinely new or
   unrouted URL-bearing identities;
2. a cumulative routing ledger is supplied when prior routing exists;
3. exact candidate and verification identities pass the exclusion audit;
4. a plan-only run produces nonempty, balanced, unique lanes;
5. both 2,000-row dry runs finish with zero URL opens/network calls;
6. live URL opening receives separate explicit authorization; and
7. the operator accepts the larger resume and audit unit.

Use 3×1000 when failure isolation matters more than maximum capacity. Use
smaller lanes for new code, uncertain server behavior, or any workflow that
stores/parses content or adds human classifications.

## Locked initial settings

- Lanes: 2
- Maximum rows per lane: 2,000
- Total capacity: 4,000
- Concurrency: 8 per lane initially
- Total timeout: 20 seconds
- Connect timeout: 8 seconds
- Read timeout: 15 seconds
- Redirect limit: 5
- Response ceiling: 10,485,760 bytes (10 MiB)
- Content samples: disabled
- Environment proxy/auth inheritance: disabled by verifier
- Artifacts: lane-local metadata only
- Duplicate handling: one logical fetch per in-lane exact-URL group where
  reusable

Concurrency 10–12 is a documented future option, not a default. It requires
operator approval and a separately validated run; do not increase it merely
because a queue is large.

## Planning gate

Use:

```bash
python scripts/prepare_scaled_verification_batches.py \
  --candidate-queue-csv <FUTURE_CANDIDATE_QUEUE.csv> \
  --output-dir docs/analysis/verification_rounds/<FUTURE_ROUND_ID> \
  --round-id <FUTURE_ROUND_ID> \
  --profile bulk_2x2000 \
  --exclude-verified-ledger-csv <OPTIONAL_PRIOR_CUMULATIVE_LEDGER.csv> \
  --priority-scope future_unverified \
  --balance-lanes \
  --capacity-only-plan \
  --plan-only
```

Omit the prior-ledger argument only when the future queue has no prior routing
history. For the current canonical queue, the planner automatically applies
the committed cumulative ledger unless
`--allow-reroute-already-verified` is explicitly supplied. Never use that
flag casually.

If no unrouted rows remain, the planner creates a no-work manifest, input
audit, no-command note, and no-merge handoff. It creates no lane input CSV.

## Dry-run gate

Run the generated two lane inputs with `--dry-run`. Require:

- exact manifest hashes and row counts;
- at most 2,000 planned rows per lane;
- unique verification and candidate queue IDs across lanes;
- terminal `dry_run_planned` status for every row;
- zero URL opens and zero network calls;
- zero candidate artifacts or downloaded bytes; and
- no protected or accounting changes.

Audit both dry outputs together. Dry-run status never authorizes live URL
opening.

## Future live gate

Only after separate explicit authorization:

1. create two fresh live output and artifact directories;
2. launch Lane 1;
3. confirm its checkpoint ledger, summary, timing, and artifact root exist;
4. launch Lane 2 after a brief health gate;
5. do not launch a third lane;
6. preserve a healthy sibling lane if one lane fails;
7. never overwrite an existing output directory; and
8. do not resume without an audited plan using the verifier’s
   `--resume-from-output-dir` and `--skip-completed-verification-ids`
   controls.

The verifier writes its ledger, timing, and summary atomically after each
duplicate group finishes. It retains only bounded row state in memory and
writes small, sanitized, deterministic lane-local metadata artifacts. Content
samples and full documents remain off.

## Runtime and artifact expectations

Prior observed per-lane routing throughput was approximately 20,600–28,100
rows/hour. A 2,000-row lane therefore projects to roughly 4.3–5.8 minutes of
active work under a similar URL mix. Plan for 6–10 minutes of total wall time
including lane establishment and health checks, with longer outcomes possible
under timeout-heavy or throttled servers.

The prior 4,726-row universe produced 4,551 unique small metadata artifacts
and a 4.85 MB cumulative CSV. A 4,000-row routing round should be budgeted for
roughly 3,700–4,000 small metadata JSON files plus several megabytes of CSV
and audit output. This estimate does not authorize saving source content.

## Audit and serial merge

After both live lanes terminate:

- rerun `scripts/audit_verification_lanes.py`;
- require exact input hashes and identity coverage;
- require every planned row to have a terminal routing status;
- require zero cross-lane duplicate verification IDs;
- require all nonblank artifact paths to exist inside their lane roots;
- review status/content-type/byte distributions and duplicate reuse;
- stop before merge.

A separate serial merge task may run
`scripts/merge_verification_lanes.py` exactly once only when the audit
recommends `merge_all_verification_lanes`. The merge must preserve
round-specific and project-wide cumulative/latest history and must reject
overlap with earlier durable identities.

## Dashboard wording

Use “URL-routing outcomes” or “routing coverage.” Never summarize a routing
round as content verification, source relevance, ingested evidence, extracted
wages, or wage-gap analysis. A reachable document has not yet passed
employer/unit/cycle or extractability review.
