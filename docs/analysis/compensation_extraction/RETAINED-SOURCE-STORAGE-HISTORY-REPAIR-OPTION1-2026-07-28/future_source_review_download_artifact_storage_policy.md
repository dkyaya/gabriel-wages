# Future source-review/download artifact-storage policy

Every future source-review/download run must choose and validate its artifact store before live downloads begin.

## Preflight

- Declare the approved artifact storage scheme and root.
- Prove the payload root is ignored by Git.
- Define deterministic storage pointers and local-path mapping.
- Create a retained manifest schema with byte size, SHA-256, access scope, availability, and backup status.
- Install a staged-file guard that fails on retained PDFs, HTML snapshots, office documents, archives, images, or extracted full text.
- Record that no source-review, candidate-review, or verification rerun is implied by storage validation.

## Live run

- Workers write payloads only to isolated artifact-store lane prefixes.
- Workers write lightweight checkpoints and manifests separately.
- Each retained payload is hashed before it is marked retained.
- Coordinator summaries reconcile row count, byte total, content-type counts, and unique hashes.
- Git additions are explicit; blanket `git add .` is prohibited for source-review/download tasks.

## Closeout

- Run the staged-path and ahead-history source-binary audits.
- Run the individual and aggregate new-blob-size audits.
- Verify all lightweight manifests, queues, summaries, dashboard/status artifacts, scripts, and tests are tracked.
- Verify payload files remain available at their artifact pointers.
- Push with plain `git push` and confirm the branch is not ahead afterward.
- If push fails, stop the next research phase and create a push-only or storage repair. Never rerun the download stage to repair Git transport.

The dashboard may report retained counts and readiness state, but the map remains total scout coverage only. Artifact storage never changes global analysis readiness.
