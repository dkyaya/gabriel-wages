# No-tracked-binaries validation

Audit target: repaired commit `52a9243df210ba0e40fea695062f48b9adf5817b` relative to unchanged base `845333f19e9b0814d546696885a4e22adcbf0fb9`.

- `git ls-files` under the operational `retained_sources/` root: 0.
- `git ls-files` under the local artifact root: 0.
- retained-source blob paths in repaired ahead history: 0.
- blobs over 100 MiB in repaired ahead history: 0.
- total repaired ahead-history blobs: 298.
- aggregate repaired ahead-history blob bytes: 98,725,389.
- largest repaired blob: 6,966,173 bytes.
- staged retained/PDF/HTML/artifact payload paths before repair commit: 0.

The operational and artifact roots are both ignored by repository-root rules. All 4,961 local operational files and all 4,961 artifact-copy files remain present and hash-valid.

A local-only rollback branch, `local-backup/retained-source-heavy-history-20260728`, preserves the original unpushed commit graph for emergency recovery. It is not part of `main`, was not pushed, and must never be pushed. Its existence does not change the main/upstream audit; it does mean old blobs remain in the local object database until that rollback ref is explicitly retired in a separately authorized cleanup.
