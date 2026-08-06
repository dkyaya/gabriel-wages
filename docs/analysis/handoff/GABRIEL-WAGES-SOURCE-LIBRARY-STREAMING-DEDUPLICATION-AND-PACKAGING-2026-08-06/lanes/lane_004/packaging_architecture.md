# Packaging architecture

The source library is written directly from the current canonical files into independent Zstandard-compressed tar archives. No full uncompressed library tree is created. Every archive uses the common root `gabriel-wages-source-library-2026-08-06/`, contains a disjoint source set, and can be listed, verified, and extracted without any other archive part.

Volume assignments are frozen before archive writing. Sources are ordered deterministically by state, municipality, and source ID. A source and its linked extracted-text companion remain together. Normal volumes target 2 GiB of uncompressed input and may not exceed 2.5 GiB unless one individual source requires a documented oversize volume.

Only one coordinator writes large archives. Before each volume, the coordinator checks that the current free space minus the planned uncompressed input remains at or above the 8 GiB floor. This conservative check reserves enough room even if compression is ineffective. A completed archive is accepted only after Zstandard integrity validation, safe-member inspection, expected-member reconciliation, and source-member SHA-256 verification.

Accepted volumes are immutable. Resume state records their checksums, and a later run begins with the first incomplete assignment. Completed files may be moved off-machine by the user without changing source lineage; the transferred-volume ledger must be updated deliberately before the next run.
