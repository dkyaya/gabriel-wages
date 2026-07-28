# PDF/text readiness push-only repair summary

Decision: `push_only_repair_pdf_text_readiness_4961_push_failed`

The completed readiness commit `d17549fe065c243d753167e5df4c7edba4e89209` exists locally on `main`, and its decision remains `combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready`. The readiness results reconcile to 4,961 reviewed retained sources and 4,051 extraction-ready sources. Global analysis readiness remains false.

Two authorized plain `git push` attempts were made. Both failed with HTTP 500 and `send-pack: unexpected disconnect while reading sideband packet`. No third attempt was made.

The push preflight found 4,961 tracked retained-source paths totaling 12,475,949,771 bytes (11.619 GiB) in the unpushed history. Of the 12,415,784,234 bytes (11.563 GiB) of new Git blobs ahead of `origin/main`, 12,325,687,089 bytes (11.479 GiB) are newly introduced retained-source blobs. There are no individual blobs over 100 MB; the largest is 65,319,205 bytes. The aggregate object set, rather than a single over-limit file, is the material push risk.

No readiness, source-review/download, candidate-review, or verification stage was rerun. No document was redownloaded or modified. No text/table/span extraction, OCR, rendering, rating/model/API work, ingestion, codification, or statistical/causal analysis occurred.

The dashboard/readiness state remains committed locally but was not delivered to `origin/main`. A separate, explicitly authorized repository-storage/history repair is required before the four-lane text extraction phase starts.
