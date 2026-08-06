# Source-library tool specifications

## Streaming packager

The packager reads the canonical source-selection table in deterministic SHA-256 order and writes bounded compressed volumes directly from the existing source roots. It must not build a full uncompressed staging tree. After each volume closes, it writes the archive checksum, member inventory, validation result, and atomic resume checkpoint. It starts the next volume only after the prior volume passes validation.

## Volume validator

The validator checks archive size, SHA-256, readability, member count, member byte total, path safety, ordering, and optionally every member hash. A failed volume is quarantined. Validation failure must not advance the packaging checkpoint.

## Reconstruction tool

The reconstruction tool operates from a caller-supplied library root. It verifies volume checksums before extraction, rejects unsafe paths and symlink escapes, separates originals from extracted text, verifies reconstructed original hashes, and writes a compact reconstruction report. It supports full, family, and single-source reconstruction without relying on the original repository.
