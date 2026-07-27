# Shard design

The four shards are geographic discovery shards, not mechanism lanes. Each contains exactly 1,000 unique municipalities, a mix of regions and states, and 125 targets from each of eight broad source-family query bundles. Each shard has its own queue hash, lock, result path, and resume identity. A later live task may finish one shard and stop without touching completed shards.
