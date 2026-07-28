# Source-review/download lightweight artifact validation

The source-review/download run remains substantively complete after separating its payload from Git:

- decision: `combined_broad_source_review_download_5589_completed_pdf_readiness_ready`;
- queue: 5,589;
- completed lanes: 4;
- retained sources: 4,961;
- retained PDFs/HTML/other: 3,980 / 941 / 40;
- excluded/deferred: 628;
- retained bytes: 12,475,949,771;
- unique retained SHA-256 hashes: 4,961.

There are 109 lightweight files in the run directory outside `retained_sources/`. They include the decision, summary, retained manifests, hash manifests, results, excluded/deferred records, lane checkpoints/results, coverage summaries, validation reports, dashboard sync reports, planning notes, and next-task prompt.

The retained payload is no longer Git content, but every committed manifest path remains locally resolvable and has a deterministic mapping to the ignored artifact copy. No source-review/download stage was rerun.
