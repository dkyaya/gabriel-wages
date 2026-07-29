# Future span-extraction parallel-lane standard

Use four independently runnable, checkpointed workers starting at T+0/T+8/T+16/T+24 with controlled overlap. Workers write lane-local outputs only. The coordinator validates offsets, hashes, bounded context, lane union, and storage controls before shared summaries.
