# Next task: retained-source Git storage and push repair

Do not begin four-lane text extraction yet. First authorize a bounded repository-storage/history repair for the three commits currently ahead of `origin/main`.

The repair must preserve the 4,961 retained local source files and all readiness/source-review outputs while preventing the 12.48 GB retained-source payload from remaining in the Git objects that must be pushed. Because those blobs are reachable from the unpushed commit `1b46e0d`, a new deletion or `.gitignore` commit alone is insufficient.

The next prompt should explicitly authorize one selected strategy, with a rollback artifact and validation before mutation:

1. Reconstruct the three unpushed commits on top of the current `origin/main` tracking ref while excluding retained-source binaries from Git, preserving them locally under an ignored path; or
2. Migrate retained-source binaries to an explicitly approved large-file/artifact storage system and rewrite the three unpushed commits to reference that storage.

The repair must not fetch, pull, rebase, merge, configure remotes, rewrite already-pushed history, delete local retained sources, rerun research, or begin extraction unless separately authorized. After repair, it must validate all manifests and hashes, add the durable push-hardening policy, push with plain `git push`, confirm `main` is no longer ahead, and only then restore the next research step: four-lane bounded text extraction over the 4,051 readiness-approved sources.
