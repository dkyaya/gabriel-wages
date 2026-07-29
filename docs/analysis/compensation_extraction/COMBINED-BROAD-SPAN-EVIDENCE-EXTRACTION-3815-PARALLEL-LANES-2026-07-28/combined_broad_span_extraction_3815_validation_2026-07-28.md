# Span-extraction validation

Coordinator invariants passed for 3,815 sources and 18,174 positive/ambiguous span records (17,259 positive plus 915 ambiguous). The following commands passed:

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_combined_broad_span_extraction_3815.py scripts/span_extraction_3815_coordinator.py scripts/test_combined_broad_span_extraction_3815.py`
- `.venv/bin/python scripts/test_combined_broad_span_extraction_3815.py`
- `.venv/bin/python scripts/test_combined_broad_text_extraction_4051.py`
- `.venv/bin/python scripts/test_retained_source_storage_history_repair.py`
- `.venv/bin/python scripts/test_combined_broad_pdf_text_layer_readiness_4961.py`
- `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py`
- `.venv/bin/python scripts/build_dashboard_data.py`
- `npm --prefix docs/dashboard run build`
- `.venv/bin/python scripts/validate.py`
- `.venv/bin/python ingest/test_pipeline.py` (60 passed, 0 failed)
- `git diff --check`

Artifact checks found zero tracked files under `artifacts/local_extracted_text` and `artifacts/local_retained_sources`. The bounded output package is 194 MB before Git compression. The staged scope has 193 paths, 183 unique blobs, 154,754,950 unique uncompressed blob bytes, no blob over 50 MB, and a largest individual blob of 42,429,291 bytes—well below the 100 MB Git-hosting limit. The staged forbidden-artifact count is zero. Full text, retained binaries, unrelated rendered pages, and the unrelated root `package-lock.json` are excluded. The dashboard phase/overview sync passed, the map remains total scout coverage only, and global analysis readiness is false.
