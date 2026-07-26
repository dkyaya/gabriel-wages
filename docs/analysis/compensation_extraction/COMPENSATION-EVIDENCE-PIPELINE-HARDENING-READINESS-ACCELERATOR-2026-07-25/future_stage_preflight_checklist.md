# Future stage preflight checklist

1. Confirm clean tracked worktree and expected ancestor commit.
2. Verify every required path and recorded SHA-256.
3. Confirm the prior decision authorizes only the requested next phase.
4. Run a no-write dry run and schema/count reconciliation.
5. Freeze exact IDs, page/input bounds, and output directory.
6. Verify credentials without printing them only when that phase authorizes API use.
7. Reject OCR-later, non-target, missing-path, wrong-hash, and one-to-many inputs.
8. Confirm raw values/provenance/history remain immutable and exceptions explicit.
9. Prove dashboard cannot overstate readiness.
10. Prove checkpoint/relay schemas and idempotent resume before live work.
