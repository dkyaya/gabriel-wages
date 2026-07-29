# Resumability plan

Each worker owns one immutable shard and isolated output directory. After every target it writes an atomic checkpoint containing the last completed shard sequence, cumulative parse statuses, candidate count, errors, and queue hash. Resume must verify the same queue hash and continue at the next sequence without rerunning completed rows.
