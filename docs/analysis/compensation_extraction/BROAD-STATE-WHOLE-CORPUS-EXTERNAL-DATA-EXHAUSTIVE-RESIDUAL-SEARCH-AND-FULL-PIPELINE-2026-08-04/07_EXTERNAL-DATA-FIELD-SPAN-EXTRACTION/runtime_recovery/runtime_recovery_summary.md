# Field/span runtime recovery summary

Classified state: **D — payload processing complete; coordinator interrupted**.

No original lane, replacement worker, merge coordinator, or validation coordinator is active. The two aligned full observations began 77.5 seconds apart and were identical: every lane remained at 2,832 accepted terminal outcomes, with no ledger-count, byte-size, mtime, checkpoint, error, or temporary-artifact change.

| 001 | 2,832 | 2,832 | 0 | 879,812 | 640,454 | 320,322 | 0 |
| 002 | 2,832 | 2,832 | 0 | 976,572 | 763,671 | 351,823 | 0 |
| 003 | 2,832 | 2,832 | 0 | 1,146,329 | 913,231 | 409,992 | 0 |
| 004 | 2,832 | 2,832 | 0 | 1,017,484 | 754,994 | 361,722 | 0 |
| 005 | 2,832 | 2,832 | 0 | 1,538,573 | 1,217,087 | 759,205 | 0 |

Global accepted payloads: **14,160**. Global remaining payloads: **0**. No lane overlap, duplicate accepted ID, foreign accepted ID, duplicate worker, open task file, missing artifact pointer, malformed final JSONL line, or new truncated gzip ledger was found. The prior interrupted gzip streams were already resealed and documented before the completed payload run; this recovery did not repair or truncate any ledger.

Free disk is 33.35 GiB, leaving 25.35 GiB above the required 8 GiB reserve.

Action: the original coordinator finalize/merge/validation completed during this recovery; no payload worker was launched. No hosted search, GABRIEL/API, OCR, cleanup, payload replay, worker termination, or append-only-ledger mutation occurred.
