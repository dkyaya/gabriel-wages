# Future 2×2000 Dashboard Status Note

Date: 2026-07-24

The dashboard’s current verification result is unchanged:

- verification phase: `full_url_routing_merged`;
- current URL-bearing queue routed: 4,726 / 4,726;
- cumulative reachable/reused: 3,750 / 4,726 (79.3483%);
- current unrouted URL-bearing rows: 0; and
- ingestion, codification, wage extraction, and wage-gap analysis:
  `not_started`.

The verification status JSON now additionally records:

- `future_bulk_verification_profile`: `bulk_2x2000`;
- `future_bulk_profile_status`:
  `available_for_future_unrouted_candidate_queues`;
- `current_queue_bulk_rerun_status`: `not_needed`; and
- `current_queue_unrouted_url_bearing_rows`: `0`.

The Verification Pipeline panel describes `bulk_2x2000` as reserved for
future queues with new unrouted identities. It does not show another current
verification round as planned or pending.

This is an operational capability note, not a new evidence stage. The next
substantive phase for the current queue remains content triage and
extraction-readiness planning.
