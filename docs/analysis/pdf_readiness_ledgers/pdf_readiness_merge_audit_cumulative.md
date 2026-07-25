# Cumulative PDF-Readiness Merge Audit

- merge ID: `PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`
- merged at: `2026-07-25T12:25:23Z`
- stage: `technical_readiness_checked_not_extracted`
- rounds: `{'PDF-READINESS-PILOT1-150-2026-07-24': 150, 'PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24': 1974}`
- source-review / retained PDF / readiness rows: 2150 / 2124 / 2124
- exact retained source-review and candidate identity equality: yes
- authority path/hash/size/content-type and inherited-field equality: yes
- readiness statuses: `{'readiness_checked': 2124}`
- text-layer statuses: `{'absent': 296, 'partial': 220, 'present': 1608}`
- technical parseability: `{'high': 1608, 'low': 296, 'medium': 220}`
- recommended next actions: `{'ocr_later': 296, 'parse_text_layer_later': 1828}`
- page count summary: `{'count': 2124, 'minimum': 1, 'median': 44, 'mean': 50.86064, 'p90': 84, 'maximum': 463, 'total_pages': 108028, 'buckets': {'11_to_25': 215, '1_to_10': 86, '26_to_50': 990, '51_to_100': 701, 'over_100': 132}}`
- duplicate PDF-readiness/source-review/candidate identities: 0 / 0 / 0
- missing/hash/signature/parser failures: 0 / 0 / 0 / 0
- URLs/network/downloads/OCR/full-text/wage extraction: 0 / 0 / 0 / 0 / 0 / 0
- ingestion/codify/scout/routing/triage/source-review mutations: 0 / 0 / 0 / 0 / 0 / 0

The merged layer records technical page-count and bounded sampled text-layer readiness only. It does not establish wage-table presence, wage values, source relevance, employer or unit match, ingested evidence, codified evidence, or analysis-ready observations.
