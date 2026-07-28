# Push diagnostics

## Ahead history

Local `main` is three commits ahead of the local `origin/main` tracking ref:

1. `1b46e0ded70c8ab30b7c1b8651906ef93d030aa1` — Run combined broad source review downloads
2. `a305a4dd18f47099f000c48aa8c5d11f6df7bc04` — Record source review push repair
3. `d17549fe065c243d753167e5df4c7edba4e89209` — Review broad retained source text readiness

## Object and path audit

- Added paths ahead of `origin/main`: 5,200.
- Added retained-source paths: 4,961.
- Tracked retained-source bytes: 12,475,949,771 (11.619 GiB).
- Tracked retained types: 3,980 PDF; 941 HTML; 5 DOC; 34 DOCX; 1 TXT.
- New blobs ahead of `origin/main`: 5,182 totaling 12,415,784,234 bytes (11.563 GiB).
- Newly introduced retained-source blobs: 4,898 totaling 12,325,687,089 bytes (11.479 GiB). The count is below 4,961 because some retained paths reuse blob objects already reachable from `origin/main`.
- Blobs over 100 MB: 0.
- Largest new blob: 65,319,205 bytes, a retained PDF.
- Added PDF paths: 3,980.
- Added HTML paths: 941.
- Added extracted-text or `corpus/` paths: 0.
- Added archive/image/database-style binary build artifact paths: 0 under the checked extensions.
- Added scripts: 4.
- Added `docs/analysis` paths: 5,196, dominated by the 4,961 retained source files.

## Push outcome

Both plain pushes failed with the same HTTP 500 and unexpected sideband disconnect. This repeated result, combined with the 11.5 GiB newly introduced object set, makes another unchanged push inappropriate. This is an evidence-based diagnosis of a material aggregate-history push blocker; it is not proof of the remote service's internal root cause.

Repair requires an explicitly authorized storage/history decision. A simple later commit deleting or ignoring the retained sources would not remove their blobs from the three unpushed ancestor commits. No history rewrite, Git LFS migration, external artifact upload, fetch, pull, rebase, merge, or remote change was attempted in this task.
