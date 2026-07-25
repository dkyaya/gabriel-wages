# PDF-Readiness Pilot 1 Dashboard Status Note

Date: 2026-07-24

The dashboard builder now emits:

`docs/dashboard/data/pdf_readiness_status_summary.json`

The status is:

- `pdf_readiness_phase = pilot1_collected_not_merged`;
- `latest_pdf_readiness_pilot_id =
  PDF-READINESS-PILOT1-150-2026-07-24`;
- `pilot_rows_collected = 150`;
- `pdf_readiness_merge_status = not_started`;
- `source_review_rows_available = 2150`;
- `retained_pdf_artifacts_available = 2124`;
- text layer present / partial / absent: 107 / 19 / 24;
- technical parseability high / medium / low: 107 / 19 / 24;
- page-count minimum / median / p90 / maximum: 1 / 37 / 98 / 463;
- parser, hash, and missing-artifact failures: 0 / 0 / 0; and
- next recommendation:
  `larger_local_text_layer_page_count_pass_before_wage_extraction`.

The Source Review dashboard area has a concise PDF Readiness card stating
that the pilot is collected but not durably merged. It explicitly retains
the technical boundary: no URL, download, OCR, extracted-text artifact, wage
extraction, ingestion, or codification occurred.

Ingestion, codification, wage extraction, and wage-gap analysis remain
`not_started`. Text-layer presence is not described as proof that wage data,
the intended employer/unit, or a substantively relevant CBA is present.
