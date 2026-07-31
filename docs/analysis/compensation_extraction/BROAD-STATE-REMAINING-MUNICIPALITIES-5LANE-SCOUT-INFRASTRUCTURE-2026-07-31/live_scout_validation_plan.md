# Live Scout Validation Plan

Before launch, verify the final decision, master and lane hashes, exact 18,702-row union, disjoint lane IDs, five target counts, all `live_status=not_run`, and one flagged already-canonical municipality. During execution, require atomic per-municipality terminal checkpoints, bounded retries, isolated lane writes, and fail-closed resume. After execution, only unique parseable terminal outcomes may increase scout coverage; planned, failed, duplicate, and incomplete rows stay off the map. Candidate review remains separate.
