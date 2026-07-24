# Verification Scale Round 1 3×750 Dashboard Refresh

Date: 2026-07-24

The dashboard builder now reads the latest durable verification-routing
summary and emits `verification_phase = round1_3x750_merged`.

Current verification status:

- latest merged round:
  `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`;
- merge ID:
  `VERIFICATION-SCALE-ROUND1-3X750-MERGE-2026-07-24`;
- routing rows: 2,250;
- URL opens from the completed live round: 2,242;
- reachable/reused: 1,888 (83.911%);
- scheduled rows remaining estimate: 1,350;
- full URL-bearing backlog remaining estimate: 2,476;
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

The Verification Pipeline panel now shows the Round 1 merged routing count and
rate. It does not label those rows as ingested or analysis-ready.

All dashboard JSON files were rebuilt from committed scout accounting plus
the durable routing summary. Scout accounting itself did not change: the
dashboard still reports 2,436 scout-covered municipalities and 4,726
URL-bearing candidate rows.

Caveats remain explicit: verification routing is not ingestion; a reachable
document is not evidence of employer/unit match or extracted wages;
blocked/not-found/oversized/transport outcomes are not municipality
source-absence findings; and no wage gap has been calculated.
