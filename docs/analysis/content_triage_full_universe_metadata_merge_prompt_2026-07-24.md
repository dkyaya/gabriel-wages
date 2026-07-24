# Future Coordinator Prompt — Full-Universe Metadata-Only Content-Triage Merge

Use only under separate explicit authorization. This prompt performs an
offline serial merge of already collected metadata-only triage outcomes. It
does not authorize source access, downloading, parsing, OCR, source rating,
extraction, ingestion, codification, wage analysis, or scout-accounting
changes.

Work only in the main coordinator repository:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Do not inspect remotes or push.

## Inputs

Merge both collected rounds:

1. `CONTENT-TRIAGE-ROUND1-1000-2026-07-24`
   - Lane 1 metadata-only attempt 1: 500 rows
   - Lane 2 metadata-only attempt 1: 500 rows
2. `CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24`
   - Lane 1 metadata-only attempt 1: 932 rows
   - Lane 2 metadata-only attempt 1: 932 rows
   - Lane 3 metadata-only attempt 1: 931 rows
   - Lane 4 metadata-only attempt 1: 931 rows

Read the committed manifests, input audits, result reviews, no-merge notes,
lane summaries, and audit artifacts for both rounds.

## Readiness gates

Require a clean tracked worktree and the collection commit ancestry. Re-run
`scripts/audit_content_triage_lanes.py` separately for both manifests.
Require:

- Round 1: two `completed_merge_eligible` lanes and
  `merge_all_content_triage_lanes`;
- remainder: four `completed_merge_eligible` lanes and
  `merge_all_content_triage_lanes`;
- 1,000 Round 1 plus 3,726 remainder rows;
- 4,726 unique `triage_id` values;
- 4,726 unique `candidate_queue_row_id` values;
- exact identity equality with the cumulative URL-routing ledger;
- zero cross-round candidate or triage identity overlap;
- terminal metadata-only status for every row;
- zero URL/network/download/parse/PDF/OCR/content-artifact counters; and
- original candidate dispositions and routing statuses preserved.

Stop if any gate fails.

## Exactly-once serial merge

Create or use a fail-closed offline content-triage merge script. It must refuse
an existing merge output directory and must not open URLs or mutate upstream
artifacts.

Write:

- a Round 1-specific durable metadata-triage ledger;
- a remainder-round-specific durable metadata-triage ledger;
- `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`;
- `docs/analysis/content_triage_ledgers/content_triage_metadata_summary_cumulative.json`;
- latest pointer/copy outputs that represent all 4,726 rows, not only the
  newest round; and
- a merge audit documenting identities, distributions, source-access zeros,
  and stage boundaries.

Every merged row must remain explicitly
`metadata_only_triaged_not_content_reviewed`. Preserve all preliminary fields,
duplicate and oversized handling, original disposition, routing status, and
recommended next action. Do not reinterpret deferred or rejected rows.

## Dashboard and validation

Only after a successful merge, update dashboard status to
`metadata_only_full_universe_merged`, with 4,726 durable metadata-only rows.
Keep content download, final source rating, extraction, ingestion, codify,
wage extraction, and wage-gap analysis not started.

Run compiles, content-triage tests, both fresh lane audits, dashboard build,
`scripts/validate.py`, ingestion tests, coverage audit, protected/upstream
hash checks, identity equality, artifact confinement, secret checks, and
`git diff --check`.

Create a result review, validation record, one local commit, and relay. Do not
push or inspect remotes.
