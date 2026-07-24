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
candidate queue and an immutable round ID. Available three-lane profiles are
`conservative_250`, `standard_500`, `aggressive_750`, and `max_1000`.
The recommended first live round is `aggressive_750`: three lanes of 750
candidate rows, or 2,250 total.
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
- `dry_run_planned`, never a live verification status.

The live path is implemented but must never be exercised without separate
explicit authorization. Its tests use only injected `httpx.MockTransport`
responses and contact no network.

## Bounded live safeguards

Under separate explicit authorization:

- use eight concurrent logical requests per lane for the first 3×750 round;
- use isolated lane directories;
- apply a 20-second outer limit, 8-second connect timeout, 15-second read
  timeout, five-redirect maximum, and 10 MiB response cap;
- send only a descriptive user agent and accept header; do not inherit proxy,
  cookie, credential, or authentication configuration;
- record HTTP status, content type, final URL, redirects, bytes, timing,
  terminal classification, and sanitized errors;
- checkpoint the ledger after every completed URL group so an interruption
  preserves partial work;
- write response metadata inside the lane-local artifact directory;
- keep HTML content samples disabled by default; if separately enabled, cap
  them at 64 KiB and remove script/style blocks;
- never save a huge response or full document;
- respect applicable robots/access/terms constraints;
- do not scrape licensed/authenticated sources;
- never substitute a different URL silently;
- preserve partial lanes and do not overwrite them; and
- keep candidate, verification, ingestion, and evidence ledgers separate.

The verifier records conservative statuses:
`reachable_http`, `reachable_html`, `reachable_pdf_or_document`,
`blocked_or_forbidden`, `not_found`, `timeout`, `connection_error`,
`ssl_error`, `too_large`, `unsupported_scheme`, `invalid_url`, or `error`.
Header-level reachability never establishes officialness, employer match,
wage content, mechanism language, or downstream suitability; those fields
remain unknown or require content review.

## Duplicate URL behavior

Every candidate row remains in the lane input and ledger. The planner assigns
a deterministic exact-URL group and, with `--dedupe-fetch-plan`, keeps groups
in one lane where capacity permits. The live runner fetches one representative
per in-lane group. Reachable followers become
`duplicate_of_verified_source`; followers of an unsuccessful representative
become `duplicate_same_url_pending`. Both retain their own
`verification_id`, queue identity, and link to the representative artifact.

## Audit before any merge

Run `scripts/audit_verification_lanes.py` after all lanes terminate. The audit
checks input hashes, full row coverage, verification-ID uniqueness, duplicate
groups, terminal status counts, content types, bytes, summaries, and lane
classifications. A dry-run result recommends
`do_not_merge_until_resume_or_review`.

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

## Scaling decision

Use 3×750 first. It takes two nominal rounds to cover all 3,600 scheduled
rows and three to disposition all 4,726 URL-bearing candidates. Consider
3×1,000 only after the first live round demonstrates stable server behavior,
bounded artifact sizes, low interruption rates, and a clean lane audit. At
3×1,000, the full backlog fits in two nominal rounds, but the timeout-heavy
lane envelope grows to roughly 41.7 minutes.
