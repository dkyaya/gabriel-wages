# Local retained-source artifact root

Local artifact root:

`artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/`

Preserved payload root:

`artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/retained_sources/`

Operational manifest root:

`docs/analysis/compensation_extraction/COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28/retained_sources/`

The artifact root contains a full project-local copy of all 4,961 retained files. The operational root remains present, resolvable, and Git-ignored so all committed source-review and readiness manifests continue to work without rewriting 4,961-row lineage artifacts. The deterministic mapping is the suffix below `retained_sources/`: each operational relative suffix maps to the same suffix below the artifact payload root.

Both roots were validated independently against the committed hash manifest after preservation:

- files: 4,961;
- total expected bytes: 12,475,949,771;
- unique SHA-256 hashes: 4,961;
- operational hash matches: 4,961;
- artifact-copy hash matches: 4,961.

Both roots are local-only and ignored by Git. The artifact root is not an external backup or public storage location. Future migration to approved external artifact storage must retain the same source IDs, sizes, hashes, and deterministic pointers.
