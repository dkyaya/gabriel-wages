# Verification Scale Round 2 3×1000 Remainder — Dashboard Refresh

Date: 2026-07-24

The dashboard builder now reads the project-wide cumulative/latest routing
summary rather than treating “latest” as a Round 2-only replacement.

Current verification status:

- `verification_phase`: `full_url_routing_merged`;
- latest merged round:
  `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`;
- latest merge:
  `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-MERGE-2026-07-24`;
- live verification status: `all_candidate_urls_routed`;
- Round 1 rows: 2,250;
- Round 2 rows: 2,476;
- cumulative routing rows: 4,726 / 4,726;
- routing coverage rate: 100%;
- Round 2 reachable/reused: 1,862 (75.2019%);
- cumulative reachable/reused: 3,750 (79.3483%);
- remaining scheduled rows: 0;
- remaining URL-bearing rows: 0; and
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

The Verification Pipeline panel now shows full URL-routing coverage, the
Round 1 and Round 2 row counts, and the cumulative reachable/reused rate. It
directs the next phase to content relevance and extraction-readiness triage,
not another broad routing round.

The dashboard retains the following caveats:

- complete URL routing is not complete content verification;
- a reachable PDF/document is not an extracted wage observation or confirmed
  employer/unit match;
- blocked, not-found, oversized, and transport results are routing outcomes;
- held, context, duplicate, canonical, and rejected rows retain their original
  lower dispositions; and
- no wage gap has been calculated.

Scout accounting remains unchanged at 4,726 URL-bearing queue rows and 2,436
scout-covered municipalities.
