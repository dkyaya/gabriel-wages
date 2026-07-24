# Content-Triage Round 1 — 1,000-Row Input Plan

Date: 2026-07-24
Round: `CONTENT-TRIAGE-ROUND1-1000-2026-07-24`

## Selection result

- Reachable or successfully reused pool: **3,750**
- Routing-eligible pool including 28 duplicate-pending rows: **3,778**
- Scheduled, high-priority, reachable rows before duplicate policy: **2,391**
- Eligible canonical representatives after duplicate policy: **2,382**
- Selected rows: **1,000**
- Unselected in-scope representatives: **1,382**
- URLs opened: **0**

The planner prioritized scheduled high-priority candidates, direct reachable
documents, CBA/source-rich metadata, official-looking ownership/domain
signals, likely matched safety/non-safety municipality potential, state yield,
and stable candidate identity. No content was inspected.

## Locked lanes

| Lane | Rows | SHA-256 |
|---|---:|---|
| Lane 1 | 500 | `1ae2aef43cec1756c0169b1395f00d8a772ddd12fd98a6a70c5b2937b784bc2b` |
| Lane 2 | 500 | `118f3ca494782d46e504bfb2ebded6c8afe9e22a7a81661808987ea78ae64688` |

The 1,000 triage IDs and 1,000 candidate queue IDs are unique, with no
cross-lane identity overlap.

## Selected mix

All 1,000 selected rows currently have:

- original disposition: `scheduled`;
- candidate priority: high;
- routing status: `reachable_pdf_or_document`;
- canonical response content type: `application/pdf`;
- candidate source type: `cba`; and
- planned content-review priority: `p1`.

This concentration is the deterministic result of applying the stated
CBA-first selection rule to a pool with more than 1,000 high-priority,
reachable CBA/PDF candidates. It is a metadata label, not confirmation that
all 1,000 files are CBAs.

State distribution:

| State | Rows |
|---|---:|
| OH | 454 |
| CA | 206 |
| WA | 67 |
| IL | 66 |
| MA | 58 |
| OR | 54 |
| CT | 30 |
| NV | 18 |
| MT | 16 |
| NH | 13 |
| RI | 13 |
| DC | 3 |
| HI | 2 |

The distribution intentionally follows the committed workload and state-yield
signals rather than imposing an artificial state quota. Later content-triage
rounds can add diversity after the highest-priority CBA/PDF block.

## Duplicate, lower-disposition, and exception handling

- Routing-eligible duplicate groups: **78**
- Linked rows beyond deterministic representatives: **93**
- Selected linked duplicate rows: **0**
- Lower-disposition routing-eligible rows: **756**
- Lower-disposition rows selected: **0**
- `too_large` rows deferred: **261**
- Blocked/not-found/error/SSL/timeout/connection rows deferred: **687**

Duplicate identities remain in the cumulative routing ledger and group
summary. Excluding linked duplicates from this first batch does not delete or
upgrade them. Lower-disposition rows remain context/insufficient/duplicate/
canonical/rejected candidates even when their URLs were reachable.

No URL was opened, no document was downloaded or parsed, and no source was
promoted into content-verified, extraction-ready, ingested, codified, or
analysis-ready evidence.
