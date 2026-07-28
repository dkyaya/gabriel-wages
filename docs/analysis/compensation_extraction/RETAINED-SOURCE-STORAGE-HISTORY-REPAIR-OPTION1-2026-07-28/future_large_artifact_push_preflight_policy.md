# Future large-artifact push-preflight policy

Run this preflight before every commit and push that follows a live/local data stage.

## Fail conditions

Fail before commit if any staged path:

- is under a configured retained/downloaded/artifact payload root;
- is a source PDF, saved HTML page, office document, archive, image, OCR output, or extracted full-text payload produced by the run;
- lacks an explicit lightweight-artifact allowlist classification.

Fail before push if:

- any retained/downloaded payload path exists in commits ahead of the upstream base;
- any single new blob exceeds 100 MiB;
- aggregate new-blob bytes exceed 250 MiB without an explicit task-specific exception and documented remote capacity;
- the source manifest, SHA-256 manifest, or artifact pointer inventory does not reconcile;
- the branch/upstream base is ambiguous;
- the relay or dashboard status claims remote/public update before push success.

## Required report

Record:

- upstream base and ahead/behind counts;
- changed and added path counts;
- retained/artifact payload path count;
- new blob count and aggregate bytes;
- largest 20 new blobs;
- blobs over 100 MiB;
- artifact-pointer, size, and hash reconciliation;
- post-push ahead/behind status;
- local commit success separately from remote push success.

The preflight must inspect Git objects, not only the current index, because a later deletion does not remove payloads from an unpushed ancestor.
