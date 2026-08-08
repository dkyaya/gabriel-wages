# Source-library transfer final record

## Current status

**Transfer complete by user confirmation; remote byte verification pending.**

The private source-library release is linked to clean handoff tag `handoff-release-2026-08-07` and commit `71154479e507a5079168bb7152848b10230c5239`.

Library contents:

- 26,635 canonical originals
- 23,454 extracted-text companions
- 28 independent `.tar.zst` volumes
- 56,164,354,195 original-source bytes
- 48,027,944,647 compressed bytes
- 154 exact-duplicate groups consolidated
- 162 duplicate physical copies removed from packaging
- 409,679,973 duplicate bytes avoided
- 0 missing packaged sources
- 2 quarantined nonlibrary or invalid candidates

Integrity anchors:

- Source index SHA-256: `ffa31b609b914bb6bb2af37363931240d0b1b0e544849428e21e6b80a42d80b8`
- Volume manifest SHA-256: `a54509c5cf9f6bc19c91219f8117f9bfb651913d29657703a6626e809dccd4ee`
- READ-ME-FIRST SHA-256: `21946d9a40fea9a2d83780d0a9219a05b59f6b5eadd8f4dec94d4271099a5f6f`

The user reported all 28 volumes, the final READ-ME-FIRST package, and checksum files uploaded to the private user-managed `Safety_NonSafety_Source_Library` destination. This lane did not access Drive, list remote files, download remote bytes, or compute remote checksums.

Before transfer, each independent volume passed Zstandard integrity checks and 100 percent streaming source-member SHA-256 validation. That proves the local package was internally valid before upload. It does not prove that every remote byte matches.

## Remaining action

The receiving researcher or archive custodian must independently verify every remote or downloaded volume and final metadata file against the preserved checksum record. Record method, observed bytes, observed SHA-256, date, verifier, and pass/fail result.

## Cleanup status

Local source deletion is **not authorized**. User-confirmed upload is not a substitute for remote-byte verification. Even after checksum verification, deletion requires a separate path-specific cleanup plan and explicit user approval.
