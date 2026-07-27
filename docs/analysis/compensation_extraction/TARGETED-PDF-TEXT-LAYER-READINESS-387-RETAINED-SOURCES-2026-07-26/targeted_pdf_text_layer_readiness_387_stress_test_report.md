# Stress-test report

- Empty, truncated, malformed, encrypted, and metadata-unreadable PDFs fail into explicit review/defer lanes.
- Oversized files or PDFs above the bounded page limit defer without text probing.
- PDF text-layer probes are capped at three pages and discard stdout after numeric signal counting.
- Empty, redirect-shell, script-heavy, and weak-visible-text HTML artifacts do not enter the HTML-text-ready lane.
- Hash, size, path, queue count, content-type count, and prior-exclusion overlap failures stop the run.
- Readiness errors prevent the text-extraction-ready decision.
- Partial outputs fail completion validation; completed `--resume` is read-only.
