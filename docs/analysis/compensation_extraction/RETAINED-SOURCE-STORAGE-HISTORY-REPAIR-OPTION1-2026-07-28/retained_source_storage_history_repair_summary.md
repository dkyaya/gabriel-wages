# Retained-source storage/history repair summary

Decision: `retained_source_storage_history_repair_completed_extraction_ready`.

Option 1 completed safely. All 4,961 retained source files remain in their original Git-ignored operational paths and in an independent project-local ignored artifact copy. Before repair, all 4,961 files matched the committed byte sizes and SHA-256 hashes. After preservation, all 4,961 original files and all 4,961 artifact-copy files matched again.

The three local-only commits that contained the 12,475,949,771-byte retained payload were reconstructed on the unchanged pushed base `845333f`. The pushed replacement commit is `52a9243df210ba0e40fea695062f48b9adf5817b`. Its ahead-history audit found:

- 298 new blobs;
- 98,725,389 aggregate new-blob bytes;
- largest blob 6,966,173 bytes;
- retained-source paths: 0;
- retained-source blobs: 0;
- blobs over 100 MiB: 0.

Plain `git push` succeeded on the first repaired attempt. No force push, fetch, pull, rebase, merge, or remote configuration change occurred. Already-pushed history was not rewritten.

All lightweight source-review/download, readiness, dashboard/status, script, test, manifest, hash, queue, lane, and validation artifacts remain tracked. The source-review decision remains `combined_broad_source_review_download_5589_completed_pdf_readiness_ready`. The readiness decision remains `combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready`, with 4,051 sources ready for the next bounded extraction stage.

Option 2 is now the mandatory future standard: retained/downloaded source binaries and extracted full text live in approved artifact storage, while Git tracks only manifests, hashes, lineage, summaries, checkpoints, validation records, and storage pointers. Staged-file and ahead-history gates fail closed on payload files.

The dashboard was rebuilt and validated. Only generated timestamps changed during this storage-only task; map data remains total scout coverage only and global analysis readiness remains false.
