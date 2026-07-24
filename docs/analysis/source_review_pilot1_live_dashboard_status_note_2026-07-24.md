# Source-Review Pilot 1 Dashboard Status Note

Date: 2026-07-24

The dashboard source-review layer now records:

- `source_review_phase = pilot1_live_collected_not_merged`;
- `source_review_live_status = pilot1_collected_not_merged`;
- latest pilot:
  `SOURCE-REVIEW-PILOT1-150-2026-07-24`;
- live rows collected: 150;
- terminal rows: 150;
- source-review merge status: `not_started`;
- content download status: `pilot1_collected_not_merged`;
- source rating status: `pilot1_collected_not_merged`;
- extraction readiness: `preliminary_pilot1_not_merged`;
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

The dashboard reports the actual terminal distribution—149 connection errors
and one forbidden response—and does not imply that a source body was retained,
that content was rated, or that a durable merge occurred. The scaling
recommendation is to diagnose the connection failures before any separately
authorized retry, not to enlarge the batch.
