# Stress-test report

PASS. Deterministic validation checks reject duplicate municipalities, invalid shard IDs, shard counts other than 1,000, weak/duplicate/review target tiers, queue/union mismatch, lock-hash changes, actual-covered or prior-wave municipality admission, nonzero forbidden-action counters, and partial-package completion. The committed test suite also revalidates zero-write idempotence.
