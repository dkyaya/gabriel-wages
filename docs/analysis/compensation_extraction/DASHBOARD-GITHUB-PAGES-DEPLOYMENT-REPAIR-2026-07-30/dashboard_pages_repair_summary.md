# Dashboard GitHub Pages deployment repair

The local dashboard data and rendered production build already contained the complete 2026-07-30 readiness status. The public site remained stale because Pages deployment run `30555371198` failed during dashboard JSON regeneration, before Node/Vite or artifact upload.

The failing gate required 4,961 historical retained binaries under a deliberately Git-ignored `retained_sources/` directory. A clean GitHub Actions checkout can never contain those files. The bounded repair validates the tracked manifest's confined paths, positive sizes, unique IDs, and unique SHA-256 hashes in clean checkouts, while continuing to verify physical file presence and size when local retained storage exists. The Pages workflow now executes a focused regression test before regeneration.

Local regeneration, a clean exported-checkout reproduction, both production builds, and the local rendered smoke passed. Repair commit `35933347c376cf99c988f893f4501366a1a98295` then completed Pages workflow `30558746863`: regeneration, Vite build, artifact upload, and Pages deployment all passed.

The cache-busted public Playwright smoke at `https://dkyaya.github.io/gabriel-wages/?dashboard_smoke=20260730_post_repair_1554` visibly confirmed every required July 30 value, the exact next task and readiness blockers, total-scout-coverage-only map semantics, the current readiness report link, and absence of the stale 6,919/candidate-review current state. The final public pass had zero console errors and warnings.
