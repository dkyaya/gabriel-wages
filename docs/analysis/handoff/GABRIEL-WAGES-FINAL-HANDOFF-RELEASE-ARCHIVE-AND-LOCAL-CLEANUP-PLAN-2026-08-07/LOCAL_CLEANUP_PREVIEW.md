# Local cleanup preview

This is a path review, not an executable deletion script. No path listed here was deleted.

| Path | Current logical size | Proposed class | Reason / prerequisite |
|---|---:|---|---|
| `.` | 120.85 GiB | KEEP_UNTIL_APPROVAL | historical project root; only Strategy B Wave 5 |
| `artifacts` | 64.52 GiB | REVIEW_MANUALLY | resolve path-level contents before deletion |
| `artifacts/local_retained_sources` | 50.77 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `docs` | 31.71 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `docs/analysis` | 31.46 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `docs/analysis/compensation_extraction` | 30.93 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04` | 30.00 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/pdf` | 27.85 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `.git` | 14.03 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | historical bundle transfer and explicit approval |
| `.git/objects` | 14.02 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | historical bundle transfer and explicit approval |
| `.git/objects/pack` | 13.72 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | historical bundle transfer and explicit approval |
| `artifacts/local_structured_external_data` | 12.37 GiB | DELETE_RECONSTRUCTIBLE | Wave 3 after reproducibility and approval |
| `artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04` | 12.23 GiB | DELETE_RECONSTRUCTIBLE | Wave 3 after reproducibility and approval |
| `docs/analysis/compensation_extraction/COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28` | 11.66 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28` | 11.62 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/retained_sources` | 11.62 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `docs/analysis/compensation_extraction/COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28/retained_sources` | 11.62 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04` | 9.42 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `tmp` | 9.21 GiB | DELETE_LOW_RISK | Wave 1 after frozen path check and approval |
| `artifacts/local_retained_sources/broad_state_4x2500_source_review_download_2026-07-30` | 6.11 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |
| `artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/reconciled_external_layers` | 4.41 GiB | DELETE_RECONSTRUCTIBLE | Wave 3 after reproducibility and approval |
| `tmp/source_review_pilots` | 4.21 GiB | DELETE_LOW_RISK | Wave 1 after frozen path check and approval |
| `artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04/ingested_external_layers` | 3.44 GiB | DELETE_RECONSTRUCTIBLE | Wave 3 after reproducibility and approval |
| `docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04/02_MERGED-EXTERNAL-CANDIDATE-REVIEW` | 3.39 GiB | KEEP_UNTIL_REMOTE_ARCHIVE_CONFIRMED | mixed tracked history; retire under Wave 5 |
| `artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/retained_sources/source_review_lane_003` | 3.23 GiB | DELETE_ORIGINAL_SOURCE_LOCAL_COPY_AFTER_LIBRARY_CONFIRMED | Wave 4 after source-library verification and approval |

The later destructive task must regenerate this list, compare it to the frozen manifest, stop on any unexpected path, and request explicit approval before acting.
