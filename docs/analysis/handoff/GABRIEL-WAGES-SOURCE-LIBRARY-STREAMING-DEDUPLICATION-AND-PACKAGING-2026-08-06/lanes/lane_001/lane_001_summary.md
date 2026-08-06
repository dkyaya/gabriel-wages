# Lane 001 canonical source reconciliation

Lane 001 reconciled the Phase 0 source-selection manifests against the current filesystem without copying, moving, deleting, or packaging any source.

## Result

- Physical source candidates: **26,799 files** (52.69 GiB).
- Canonical SHA-256 identities: **26,637 sources** (52.31 GiB).
- Files found at their recorded paths: **26,799 of 26,799**.
- Size mismatches: **0**.
- Exact-duplicate groups: **154**, containing **162** redundant physical copies and **390.70 MiB** of duplicate bytes.
- Metadata inconsistencies among canonical IDs, aliases, or duplicate groups: **0**.
- Deterministic trusted-hash sample: **50 of 50 matched**.
- Additional duplicate-group backstop: **10 groups** rehashed; all selected files matched.
- Files larger than 1 GiB: **0**.
- Eligible canonical sources after reconciliation: **26,636** (52.31 GiB).
- Quarantine candidates: **1**. The sole candidate is the zero-byte `retained_quota.lock` control file, not a research source.
- Missing-source blockers: **0**.

## Important boundary

The lane did not create archive volumes or a staging copy. It did not copy, delete, rename, or alter source files. Full accounting relies on the trusted Phase 0 hashes, with a bounded 50-file validation sample and a ten-largest-duplicate-group backstop. Every canonical source remains subject to redistribution review before transfer.
