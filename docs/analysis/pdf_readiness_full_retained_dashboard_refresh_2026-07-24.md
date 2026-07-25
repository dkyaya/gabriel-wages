# Full Retained PDF-Readiness Dashboard Refresh

Date: 2026-07-24

## Result

The dashboard now reads the durable cumulative PDF-readiness summary and
reports:

- `pdf_readiness_phase = full_retained_merged`;
- latest merge ID:
  `PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`;
- merge status: `merged`;
- retained PDFs available / readiness rows merged: 2,124 / 2,124;
- readiness coverage rate: 1.0;
- text layer present / partial / absent: 1,608 / 220 / 296;
- technical parseability high / medium / low: 1,608 / 220 / 296;
- parse-text-layer-later / OCR-later: 1,828 / 296;
- total pages represented: 108,028;
- median / maximum page count: 44 / 463;
- technical readiness: `complete_for_retained_pdfs`; and
- next recommendation: `text_layer_table_detection_pilot`.

The durable latest path displayed by the dashboard is:

`docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv`

The frontend PDF Readiness card now distinguishes the durable merged
technical-readiness layer from the earlier collected-not-merged state. It
shows full retained coverage, text-layer groups, total pages, and the next
bounded pilot.

The dashboard continues to show OCR, ingestion, codification, wage
extraction, and wage-gap analysis as `not_started`.

## Caveats

- PDF readiness records technical parseability only.
- Text-layer presence does not prove that wage data or a wage table exists.
- OCR has not run.
- Wage extraction has not started.
- No ingestion or codification has occurred.

The dashboard refresh opened no URL or retained PDF and made no
network/API/model call.
