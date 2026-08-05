# Lane checkpoint reconciliation

Overall result: **PASS**.

| Lane | Queue | Accepted | Incomplete | Field records | Evidence spans | Ambiguities | Conflicts |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 001 | 2,832 | 2,832 | 0 | 879,812 | 640,454 | 320,322 | 0 |
| 002 | 2,832 | 2,832 | 0 | 976,572 | 763,671 | 351,823 | 0 |
| 003 | 2,832 | 2,832 | 0 | 1,146,329 | 913,231 | 409,992 | 0 |
| 004 | 2,832 | 2,832 | 0 | 1,017,484 | 754,994 | 361,722 | 0 |
| 005 | 2,832 | 2,832 | 0 | 1,538,573 | 1,217,087 | 759,205 | 0 |

The five immutable queues are disjoint and their union is exactly the locked 14,160-payload universe. The accepted outcome ledgers contain exactly one terminal record for every payload. Each checkpoint is complete, every gzip ledger reads to EOF, and each ledger's physical row count equals the sum declared by its lane's accepted outcomes. No foreign IDs, duplicate accepted IDs, missing artifact pointers, temporary partial outputs, or malformed final JSONL lines were found.

The earlier operational incident resealed interrupted gzip streams before the successful resume; this recovery found no new truncation and performed no ledger repair.
