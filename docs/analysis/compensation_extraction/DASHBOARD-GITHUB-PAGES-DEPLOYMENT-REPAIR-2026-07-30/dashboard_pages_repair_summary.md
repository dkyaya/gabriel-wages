# Dashboard GitHub Pages deployment repair

The local dashboard data and rendered production build already contained the complete 2026-07-30 readiness status. The public site remained stale because Pages deployment run `30555371198` failed during dashboard JSON regeneration, before Node/Vite or artifact upload.

The failing gate required 4,961 historical retained binaries under a deliberately Git-ignored `retained_sources/` directory. A clean GitHub Actions checkout can never contain those files. The bounded repair validates the tracked manifest's confined paths, positive sizes, unique IDs, and unique SHA-256 hashes in clean checkouts, while continuing to verify physical file presence and size when local retained storage exists. The Pages workflow now executes a focused regression test before regeneration.

Local regeneration, a clean exported-checkout reproduction, both production builds, and the local rendered smoke passed. Public deployment and the cache-busted public visual smoke remain to be recorded after the repair commit is pushed.
