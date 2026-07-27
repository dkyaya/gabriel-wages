# Resumability plan

Run shards in controlled order. Each shard writes to its own future output directory and retains its queue hash. Resume only within the same shard using `scout_target_id` and `municipality_id`; skip completed parseable identities. Never collapse the shards or rerun a completed shard. Candidate review remains prohibited until the scouting stop condition is explicit.
