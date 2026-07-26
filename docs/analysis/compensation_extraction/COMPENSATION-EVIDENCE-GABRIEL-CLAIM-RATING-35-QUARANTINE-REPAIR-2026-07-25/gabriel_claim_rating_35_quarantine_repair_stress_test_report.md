# GABRIEL quarantine-repair stress-test report

The 64-test focused suite covers repair scope, immutable 608-row preservation, exact-quote enforcement, weak controls, positive controls, final-claim rejection, 643-row reconciliation, preflight gating, raw-payload exclusion, dashboard fail-closure, exclusion-scoped summary review, future-prompt boundaries, idempotency, and partial-output masquerading. All 64 tests passed.

The repair clarified one orchestration contract: the documented `repaired_with_remaining_quarantine` decision permits summary review when remaining rows are explicit exclusions. Dashboard and prompt logic now express that limited scope while global analysis readiness stays false.
