# Broad-state 4×2500 text extraction summary

Decision: `broad_state_4x2500_text_extraction_completed_span_extraction_ready`

The bounded non-OCR pass processed all **2,940** readiness-approved retained sources across four independent 735-row lanes. It produced **2,940** local extracted-text artifacts totaling **182,067,064 bytes**. The extraction statuses reconcile exactly to the input queue.

| Status | Count |
|---|---:|
| `extracted_ok` | 2,795 |
| `extracted_empty` | 14 |
| `extracted_low_density` | 3 |
| `extracted_suspected_bad_text` | 32 |
| `html_noisy_or_boilerplate` | 96 |
| `source_file_missing` | 0 |
| `hash_mismatch` | 0 |
| `extraction_error` | 0 |
| `unsupported_despite_readiness` | 0 |

The span-extraction-ready queue contains **2,795** `extracted_ok` rows. Consistent with the existing project convention, low-density and noisy HTML outputs remain outside the next queue for explicit repair/review.

Full text exists only in `artifacts/local_extracted_text/broad_state_4x2500_text_extraction_2026-07-30`. No OCR, span extraction, rating, ingestion, codification, wage-gap analysis, regression, or causal analysis occurred. Global readiness remains partial diagnostic only; wage-gap readiness remains blocked pending normalization and causal readiness remains blocked pending matched structure.
