# Text/Table Detection Pilot 1 Dashboard Status Note

Date: 2026-07-24

Pilot: `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24`

## Status represented

The dashboard now records the bounded local text/table-detection pilot as
`pilot1_collected_not_merged`. The status is deliberately separate from the
durably merged PDF-readiness layer and does not imply a durable
text/table-detection merge.

The new dashboard data file is:

- `docs/dashboard/data/text_table_detection_status_summary.json`

The dashboard data builder now emits that file from:

- `docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24/text_table_detection_collection_summary.json`

The Source Review project section displays a compact local detection
callout. No dashboard redesign was performed.

## Pilot facts shown

- collected and terminal rows: 150 / 150;
- lane rows: 50 / 50 / 50;
- durable merge status: `not_started`;
- parse-text candidates available: 1,828;
- OCR-later rows: 296;
- wage-table signals: 94 likely, 55 possible, one unlikely;
- contract-period signals: 112 likely, 20 possible, 18 unlikely;
- table-like structure: 135 likely, 14 possible, one unlikely;
- extraction-pilot priority: 94 p1, 54 p2, two p3;
- recommended actions: 94 wage-table extraction pilot, 54 larger detection
  pass, two manual review;
- pages scanned: 1,295;
- pages returning bounded text: 1,203;
- candidate wage-page hints: 599; and
- parser, hash, and missing-artifact failures: zero.

The next recommendation shown is
`prepare_full_text_table_detection_run`.

## Interpretation and caveats

The signal categories are deterministic, preliminary scheduling signals.
Candidate wage pages are page-number hints, not tables or wage
observations. The 149/150 likely-or-possible wage signal rate means the
sensitive heuristic should be manually calibrated before it is used to
authorize final wage-table extraction.

No URL was opened, no document was downloaded or redownloaded, and no OCR,
final wage extraction, ingestion, codification, wage-gap analysis, or
regression occurred. No full page or document text was saved. The durable
routing, content-triage, source-review, and PDF-readiness ledgers were not
mutated.
