# Full Text/Table Detection Dashboard Refresh

The dashboard now reports the durable merge of
`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`.

## Status

- phase: `full_parse_text_merged`
- merge:
  `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-MERGE-2026-07-24`
- merge status: `merged`
- durable rows / parse-text authority rows: 1,828 / 1,828
- OCR-later rows outside this detection scope: 296
- durable latest ledger:
  `docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv`
- next recommendation:
  `manual_calibration_subset_before_extraction`

## Displayed detection statistics

- wage-table signal: likely 1,067; possible 749; unlikely 12
- contract-period signal: likely 1,672; possible 103; unlikely 53
- table-like structure: likely 1,717; possible 107; unlikely 4
- extraction priority: p1 1,067; p2 754; p3 7
- recommended actions:
  wage-table extraction pilot 1,067; larger detection pass 747;
  contract-period extraction pilot 7; manual review 7
- pages scanned / with text: 17,861 / 17,369
- candidate wage-page hints: 7,649

## Files refreshed

- `docs/dashboard/data/text_table_detection_status_summary.json`
- dashboard JSON outputs rebuilt by `scripts/build_dashboard_data.py`
- `docs/dashboard/src/components/ProjectHubSections.jsx`
- `scripts/build_dashboard_data.py`

The builder now validates the durable summary, durable ledger row count,
identity coverage, frozen heuristic, duplicate/failure counters, and forbidden
activity counters before emitting the merged status. The UI labels candidate
pages as hints rather than wage observations and sends the workflow to manual
calibration.

No dashboard field implies OCR, final wage extraction, ingestion,
codification, wage-gap analysis, regression, or causal analysis. Those stages
remain `not_started`.
