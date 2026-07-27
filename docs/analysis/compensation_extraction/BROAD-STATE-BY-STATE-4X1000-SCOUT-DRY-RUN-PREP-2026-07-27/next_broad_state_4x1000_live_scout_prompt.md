# Next task: broad state 4x1000 live scout

Execute the four committed geographic shards separately and in order: `broad_shard_001`, `broad_shard_002`, `broad_shard_003`, and `broad_shard_004`. Do not collapse the queues. Before any live request, revalidate the master and shard SHA-256 locks, confirm the prior 1,205-candidate queue is unchanged, and run a separately authorized hosted-search/direct-SDK smoke preflight. Stop before live scouting if the gate fails.

Each shard must use a distinct result directory and checkpoint target identities. A completed shard must never be rerun. Resume an interrupted shard only from its committed queue and skip completed parseable identities. Use sanitized-artifact mode: save no raw prompts, raw responses, secrets, tokens, cookies, or auth headers. Use bounded retries and stop on repeated transport instability.

This is broad geographic and source-family-diverse discovery. Mechanism targeting is not the default. Capture candidate locator metadata and snippets only. Do not open URLs directly, verify with HEAD/GET, download, inspect documents, extract, rate, ingest, codify, calculate wage gaps, run regressions or treatment effects, or make national/population/final causal claims.

Do not begin candidate review after any shard or after all four shards. Candidate review remains deferred until a separately authorized combined review of the preserved 1,205 prior candidates and all review-eligible new-shard candidates.

Dashboard update requirement: after every completed shard, update status/docs with substantive live results, but add only committed parseable outcomes to actual total scout coverage. Keep planned and failed targets off the map. The map remains total scout coverage only and global analysis readiness remains false. Do not imply wage gaps, regressions, treatment effects, national/population prevalence, or final causal claims.

Future rating artifact-completeness requirement: any later rating task must verify all downstream summary inputs and deterministically reconstruct derivable missing summaries from committed valid/quarantine/results ledgers. Validate reconciliation, commit/push the repair, and continue. Missing non-derivable artifacts still fail closed.
