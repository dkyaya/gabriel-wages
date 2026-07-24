# Scaled Candidate-Source Verification Operating Procedure

Date: 2026-07-23/24

## What this phase does

Scouting produced possible locators. Verification checks whether those leads
are reachable, relevant, correctly attributed to the municipality/employer
and unit, and promising for later extraction. It does not download a corpus,
ingest a contract, run GABRIEL, extract wage observations, or calculate a
wage-growth gap.

## Prepare deterministic batches

Use `scripts/prepare_scaled_verification_batches.py` with the committed
candidate queue, an immutable round ID, three lanes, and 250 rows per lane.
The default scheduled scope orders:

1. high-priority later-verification rows;
2. medium-priority rows;
3. low-priority rows;
4. higher observed state discovery yield;
5. larger municipality population; and
6. stable queue identity.

The planner enriches each queue row with authoritative municipality/Census
identity, assigns a stable `verification_id`, and assigns exact-URL and
near-candidate grouping keys without opening the URL.

Held/context rows remain out of ordinary rounds by default. The full-backlog
plan includes them explicitly because the user wants eventual disposition for
every URL-bearing candidate. Exact duplicate rows are preserved; later review
may open one representative and link the remainder to the same verified
artifact, while retaining every original queue ID.

## Dry-run every lane

Run `scripts/verify_candidate_sources.py --dry-run` once per locked input.
Require:

- exact input row count;
- unique verification and queue IDs;
- complete municipality/Census identity;
- syntactically valid HTTP(S) fields;
- `verification_ledger.csv`, `verification_summary.json`, and
  `plan_timing.csv`;
- zero URLs opened and zero network calls; and
- `planned_not_verified`, never a live verification status.

The current live path deliberately fails closed. Implement and test safe
fetching under a separate task before using the generated future commands.

## Future live lanes

Under separate explicit authorization:

- start with conservative concurrency (three URL requests per lane or lower);
- use isolated lane directories;
- apply bounded timeout and redirect limits;
- record status, content type, final URL, and evidence artifacts;
- avoid huge downloads unless explicitly configured;
- respect applicable robots/access/terms constraints;
- do not scrape licensed/authenticated sources;
- never substitute a different URL silently;
- preserve partial lanes and do not overwrite them; and
- keep candidate, verification, ingestion, and evidence ledgers separate.

## Audit before any merge

Run `scripts/audit_verification_lanes.py` after all lanes terminate. The audit
checks input hashes, full row coverage, verification-ID uniqueness, duplicate
groups, summaries, and lane classifications. A dry-run result can only
recommend `dry_run_complete_do_not_merge_live_ledger`.

A future live merge must be one coordinator-controlled serial operation. It
may update a durable verified-source ledger only after all approved lanes are
merge-eligible. It must not update scout coverage, `contracts.csv`,
`city_coverage.csv`, corpus files, codified evidence, or analysis-ready wage
tables.

## Downstream handoff

Verified candidate sources feed a later selection and extraction stage:

1. select verified sources with exact employer/unit and source provenance;
2. identify safety/non-safety same-city cycle potential;
3. extract exact wage concepts/tables and dates with provenance;
4. ingest through the project pipeline;
5. rate text quality and extractability;
6. calculate descriptive gaps only from validated matched observations; and
7. codify mechanism text separately, preserving verbatim spans.

Verification reports conversion and routing rates. It does not report wage
effects, mechanism effects, or causal findings.
