# Stress-test report

The builder fails closed on missing inputs, coverage drift, fewer than 10,000 defensible targets, duplicate municipality IDs, shard overflow, disallowed tiers, wrong shard union, or readiness/map-boundary changes. An idempotent temporary rebuild must reproduce queue and lock hashes.
