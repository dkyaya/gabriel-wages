# Future summary-stage reconstruction fallback

A summary stage may recover a missing required input only when the artifact can be regenerated exactly from committed, immutable valid/quarantine/results ledgers. The recovery sequence is:

1. Confirm the locked predecessor decision and input hashes.
2. Confirm committed valid, quarantine, results, and candidate ledgers are complete.
3. Reconcile input = valid + quarantine and verify identity disjointness.
4. Derive the missing aggregate with controlled categories and deterministic ordering.
5. Validate the aggregate against every available predecessor count.
6. Write only the missing derivative artifact; do not change source ledgers.
7. Commit and push the repair separately with a precise message.
8. Continue the authorized summary task.

Fail closed when reconstruction is not exact, source ledgers are missing, hashes drift, or new rating judgment would be required.
