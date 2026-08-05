# Exhaustive external-data resume preflight failure

**Decision:** `broad_state_whole_corpus_external_data_exhaustive_pipeline_preflight_failed_backend_unstable`

The locked checkpoint passed every integrity test, but live hosted search remains Category B. All seven external-data families returned zero-source responses on both bounded attempts. The parser remained healthy, which isolates the failure to transport/source availability rather than the queue or schema.

- Preserved completed targets: **5,845**
- Locked remaining targets: **12,844**
- Resumed production targets completed: **0**
- Fresh hosted-search smoke calls: **14**
- Production probe calls: **0**
- Production lane calls: **0**
- New candidates: **0**

The exact locked queue and five deterministic lane files remain ready for another preflight. No preserved target may be rerun.
