# Stress-test report

- Non-ready, non-retained, Tier C/D, and prior-excluded rows fail before extraction.
- Retained path, size, or SHA-256 drift fails before extraction.
- PDF extraction is local `pdftotext` only; timeout, nonzero exit, excessive output, empty text, low density, and bad-character signals remain explicit outcomes.
- HTML extraction reads local bounded bytes only and excludes scripts, styles, SVG, and network resources.
- Key-like secret patterns prevent artifact retention.
- PDF and HTML artifact directories remain separate and task-local.
- Partial outputs fail completion validation; completed `--resume` is read-only.
