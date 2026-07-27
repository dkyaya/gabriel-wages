# Tier C span-extraction limits and boundaries

- Deterministic local rules only; no model or API calls.
- Only `extracted_ok` task-local text artifacts entered the span queue.
- At most 5 positive spans per source.
- Each span is at most 900 characters with 160 exact context characters on each side.
- Every positive and ambiguous record passed exact-substring, offset, and SHA-256 checks.
- PDF and HTML-derived text lineage remains explicit.
- Span extraction is not evidence rating, causal proof, national evidence, or wage analysis.
