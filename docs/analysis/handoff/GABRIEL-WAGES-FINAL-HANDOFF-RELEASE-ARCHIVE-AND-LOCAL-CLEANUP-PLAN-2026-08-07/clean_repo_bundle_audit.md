# Clean-repository bundle audit

The clean Git bundle is **5,110,249 bytes** with SHA-256 `e35c3441a0c2515b3402a6a1ad29f2fb07c8d7cde652062c0991e90d97e2e4cb`. `git bundle verify` passed. A separate clone resolved `main` and `handoff-release-2026-08-07` to `71154479e507a5079168bb7152848b10230c5239`, passed all 18 tests, and verified every release checksum.

The optional tracked-files snapshot ZIP is **5,652,686 bytes** with SHA-256 `35f0726c441ce4a8a4a1ccd34e9bff60cdc3d01407062043286f50c37e068fdb`. `unzip -t` passed. Neither artifact includes source-library volumes.
