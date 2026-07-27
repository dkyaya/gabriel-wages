# Next prompt: bounded exact-span rating review

Use only `targeted_evidence_span_extraction_321_rating_candidate_manifest.csv` rows with `span_status=span_extracted`. Verify each supplied span remains an exact substring at the recorded offsets and hash before any rating. Rate only the supplied exact span plus its bounded exact context; preserve PDF/HTML, retained-source, candidate, city, unit, cycle, mechanism-target, source-file, and extracted-text lineage.

Do not fetch or pull repository state, inspect/configure remotes, open URLs, download documents, include ambiguous/no-span/error/excluded rows, access PDFs/pages, run OCR or rendering, use evidence outside the supplied span/context, ingest, codify, calculate wage gaps, run regressions or treatment effects, make final causal claims, or mark global analysis readiness true. GABRIEL/API/model use requires separate explicit authorization. Rating is not causal proof.
