# Stress-test report

- Non-extracted, deferred, excluded, Tier C/D, wrong-path, size-drift, or SHA-drift rows fail before search.
- Required-context rules keep generic budget, study, recruitment, arbitration, and mediation mentions out of positive spans.
- Force-majeure mentions of strikes/lockouts and descriptive pay amounts merely using the word `appropriated` are explicitly rejected from the positive lane.
- Exact substring, offset, and SHA checks cover every positive and ambiguous record.
- Positive records are bounded to five per source and 900 characters per span; context is bounded to 160 characters on each side.
- Ambiguous and no-span sources remain explicit exclusions from the rating manifest.
- PDF and HTML lanes remain separate; no network, OCR, rendering, or model dependency exists.
- Partial packages fail completion validation; completed `--resume` is read-only.
