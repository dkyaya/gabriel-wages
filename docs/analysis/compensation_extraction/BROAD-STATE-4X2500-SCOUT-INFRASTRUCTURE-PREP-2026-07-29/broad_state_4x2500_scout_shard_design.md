# Shard design

Four 2,500-row shards mix states, regions, source-family queries, and safety/non-safety opportunities. Each shard is locked, independently runnable, checkpointed after every target, independently resumable, and restricted to its own future output directory. Shards are geographic/source-family lanes, not mechanism lanes.
