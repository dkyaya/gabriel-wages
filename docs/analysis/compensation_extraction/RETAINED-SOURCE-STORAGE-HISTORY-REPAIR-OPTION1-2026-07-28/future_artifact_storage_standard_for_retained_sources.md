# Future artifact-storage standard for retained sources

Status: mandatory for future source-review/download and extraction stages.

## Storage boundary

Retained PDFs, HTML snapshots, office documents, images, OCR derivatives, extracted full-text artifacts, and other source payloads must never be committed to normal Git history. They belong in an approved large-file or artifact store. During local work, they may live under a Git-ignored artifact root.

Git tracks only lightweight control-plane artifacts:

- immutable source IDs and source lineage;
- canonical source locators and retrieval metadata;
- content type and byte size;
- SHA-256 content hashes;
- artifact storage scheme and storage pointer;
- local-relative operational path when available;
- availability/replication status;
- decisions, summaries, checkpoints, validation reports, queues, and tests.

## Required manifest pointer fields

Future retained-source manifests must carry or deterministically join to:

- `artifact_storage_scheme`;
- `artifact_storage_pointer`;
- `artifact_object_key_or_content_address` when applicable;
- `local_artifact_relative_path` when available;
- `retained_file_size_bytes`;
- `retained_file_sha256`;
- `artifact_availability_status`;
- `artifact_replication_or_backup_status`;
- `artifact_access_scope`;
- `source_review_download_id` and upstream lineage IDs.

Pointers may not embed credentials, tokens, cookies, authorization headers, or expiring signed URLs.

## Required gates

Before a source-review/download task can close:

1. Every retained payload has a size, SHA-256 hash, and resolvable approved storage pointer.
2. The retained payload directory is ignored by Git.
3. A staged-path gate proves no retained payload is staged.
4. An ahead-history audit proves no retained payload blob entered commits to be pushed.
5. A push preflight reports both the largest new blob and aggregate new-blob bytes.
6. The relay distinguishes local artifact preservation from remote Git/dashboard publication.
7. `git push` success is verified before public/dashboard state is declared updated.

Any failed gate stops the task before commit or push. A later deletion commit is not an adequate repair if the payload already entered an unpushed ancestor; the unpushed history must be reconstructed.

## Current local implementation

The 2026-07-28 combined broad retained sources are preserved at:

`artifacts/local_retained_sources/combined_broad_source_review_download_5589_2026-07-28/retained_sources/`

The original operational paths remain available and Git-ignored so committed manifests and readiness queues stay resolvable. This local arrangement is Option 1 preservation, not external publication. Migration to approved external artifact storage remains a future storage operation.

## Research boundaries

Artifact availability does not imply extraction, rating, ingestion, codification, causal status, or global analysis readiness. Storage operations may not change evidence or analysis status.
