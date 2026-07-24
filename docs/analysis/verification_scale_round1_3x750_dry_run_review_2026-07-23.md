# Verification Scale Round 1 3×750 Dry-Run Review

Date: 2026-07-23/24
Round: `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`
Disposition: **PASS — ready for separately authorized live verification**

## Locked inputs

| Lane | Rows | SHA-256 |
|---|---:|---|
| 1 | 750 | `c03701be02afaa6c64cb63a8bb46cf9cae59f8665c3b2969e693b41a31cbfa65` |
| 2 | 750 | `ac9ee0b048f331df295ead483305d72c587ce8962b89426f84b5f42d96d048ca` |
| 3 | 750 | `a9192b47724dcc39eb09ac2760325a9fccd98fadc0b16452518fe4538ec9994a` |

The combined plan contains 2,250 unique verification IDs and 2,250 unique
candidate queue identities, all from the scheduled high-priority pool. It has
six exact-URL groups covering fourteen rows, so eight rows can reuse an
in-lane representative fetch. Duplicate-aware assignment keeps every such
group within one lane; zero exact-URL groups are split across lanes.

## Dry-run evidence

Each lane wrote 750 `dry_run_planned` ledger rows, a complete timing file, and
a parseable JSON summary. All identity and URL-syntax checks passed. Combined:

- planned and ledger rows: 2,250 / 2,250;
- lane classifications: three `dry_run_passed`;
- URLs opened: 0;
- network calls: 0; and
- audit recommendation: `do_not_merge_until_resume_or_review`.

That recommendation is correct: dry-run rows are not verified sources and
cannot be merged into a live verification ledger.

The bounded implementation was also exercised with `httpx.MockTransport`.
Synthetic responses covered reachable HTML, reachable PDF, redirect, timeout,
content-length over the 10 MiB cap, and exact duplicate reuse. Only fake
transport was used; no real locator was contacted.

At eight concurrent requests per lane, a transparent two-to-eight-second
average-response assumption gives roughly 3.1–12.5 minutes per lane. If every
logical fetch consumes the full 20-second limit, the rough upper bound is
31.3 minutes, excluding launch and audit overhead.

The round is ready for a separate, explicitly authorized live task using
fresh lane-local directories. It must stop before ledger merge, ingestion,
codification, extraction, or analysis.
