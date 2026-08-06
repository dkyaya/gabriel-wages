# Next task

## Resume revised-atlas public deployment validation

Do not rerender or repeat accepted atlas work. After the GitHub Actions and Pages outage clears, inspect workflow run `31124212169` (or rerun the same commit if GitHub cancels it), require HTTP 200 for the revised landing page and PDF, download the served PDF, verify its SHA-256 equals `46608bb50eaf0dee046f85629c92210472b96777b5e8a048e49b8a52059fe247`, and mark deployment Gate Q complete.

Only after that validation should the project proceed to `GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-SPLIT-PACKAGING-2026-08-06`. That packaging task must stream directly from canonical source roots into bounded split compressed volumes, preserve aliases and provenance, checksum every volume, avoid any full uncompressed staging copy, assume no external storage device, and delete no original source.
