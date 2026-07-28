# Next task

After this storage/history repair is pushed successfully, run the four-lane bounded text extraction described in `next_combined_broad_text_extraction_prompt.md`.

The locked queue contains 4,051 readiness-approved sources: 3,177 parse-text-layer PDFs, 834 HTML files, and 40 other documents. Use lane sizes 1,013 / 1,013 / 1,013 / 1,012 with T+0 / T+8 / T+16 / T+24 starts.

Resolve original ignored operational paths first and use the deterministic local artifact-copy mapping as fallback. Validate SHA-256 before extraction. Do not redownload or rerun readiness. Extracted full text must use approved ignored/artifact storage and must never enter normal Git history.

All evidence rating, GABRIEL/API/model analysis, ingestion, codification, OCR, rendering, wage-gap/regression/treatment-effect work, prevalence claims, and causal claims remain outside scope. The map remains total scout coverage only, and global analysis readiness remains false.
