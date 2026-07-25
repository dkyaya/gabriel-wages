# Full Text/Table Detection Dashboard Status Note

Date: 2026-07-25

The dashboard text/table status layer now records:

- phase: `full_parse_text_collected_not_merged`;
- latest round:
  `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`;
- collected rows: 1,828 / 1,828 durable parse-text candidates;
- four completed 457-row lanes;
- wage-table signals: 1,067 likely, 749 possible, 12 unlikely;
- contract-period signals: 1,672 likely, 103 possible, 53 unlikely;
- table-like structure: 1,717 likely, 107 possible, 4 unlikely;
- extraction-pilot priorities: 1,067 p1, 754 p2, 7 p3; and
- durable merge status: `not_started`.

The dashboard continues to state that the detection fields are deterministic,
heuristic, and preliminary. Candidate pages are hints, not wage observations.
Manual calibration is required before extraction.

The dashboard does not imply that a durable text/table merge, OCR, final wage
extraction, ingestion, codification, wage-gap analysis, or causal analysis
occurred. `scripts/build_dashboard_data.py` uses the committed full-run
collection summary as the source for this status, with Pilot 1 retained as a
fallback if the full-run summary is absent.
