# Verification Scale Round 2 3×1000 Remainder Input Plan

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`

## Exact command

```bash
python scripts/prepare_scaled_verification_batches.py \
  --candidate-queue-csv docs/analysis/national_scout_candidate_queue_2026-07-20.csv \
  --output-dir docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24 \
  --round-id VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24 \
  --profile max_1000 \
  --priority-scope remainder_all \
  --exclude-verified-ledger-csv docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv \
  --fill-with-held-after-scheduled \
  --balance-lanes \
  --concurrency-per-lane 8 \
  --verification-timeout 20 \
  --max-bytes 10485760 \
  --plan-only
```

The planner opened no URL and made no network call.

## Selection and lanes

- Canonical URL-bearing rows: 4,726.
- Round 1 durable identities excluded: 2,250 queue IDs and 2,250
  verification IDs.
- Exact remainder selected: **2,476 / 2,476**.
- 3×1,000 capacity: 3,000; unused capacity: 524.
- URL-bearing remainder left unselected: **0**.
- Round 1 queue-ID overlap: **0**.
- Round 1 verification-ID overlap: **0**.
- Round 2 unique queue IDs / verification IDs: **2,476 / 2,476**.

| Lane | Rows | Scheduled | Non-scheduled | SHA-256 |
|---|---:|---:|---:|---|
| Lane 1 | 826 | 451 | 375 | `ec60e33b9a79ffa7ad0dbabb43b490e3c9b2c338205722a3068269b980826bff` |
| Lane 2 | 825 | 450 | 375 | `1c1e39c09fafd13f1eb4e2f914fc82ba716c0e548dd22a33dec8307788a03a04` |
| Lane 3 | 825 | 449 | 376 | `2beb6fdb5857a6d8bea9ccee6e03992f7411c257ca86187d56210be92a2bc8fd` |

## Original dispositions

| Disposition preserved in input | Rows |
|---|---:|
| `scheduled` | 1,350 |
| `context_hold` | 523 |
| `insufficient_hold` | 302 |
| `duplicate_hold` | 291 |
| `already_canonical` | 8 |
| `calibration_rejected` | 2 |

The non-scheduled rows retain these values and `candidate_priority = held`;
their inclusion for complete routing does not promote them into verified,
ingested, codified, or analysis-ready evidence.

## Duplicate and source-type plan

- Exact duplicate groups in the remaining pool/selected round: 74.
- Duplicate rows eligible for an in-lane representative fetch: 90.
- Duplicate groups split across lanes: 0.

Source types are: 1,248 `cba`, 597
`wage_schedule_or_compensation_plan`, 192 `memorandum_or_settlement`, 181
`ordinance_or_policy`, 105 `arbitration_award`, 50 `context_only`, 28
`agenda_cover_sheet`, 22 `factfinding`, 18 `unknown`, 11 `meeting_minutes`,
10 `index_page`, six `blocked_or_unreadable`, five `insufficient_source`, and
three `pay_plan`.

## State distribution

`AK 11, AL 14, AR 16, AZ 29, CA 266, CO 25, CT 22, DE 9, FL 241, GA 7,
IA 33, ID 20, IL 80, IN 58, KS 32, KY 18, LA 22, MA 74, MD 57, ME 32,
MI 51, MN 131, MO 56, MS 12, MT 23, NC 17, ND 12, NE 9, NH 18, NJ 94,
NM 41, NV 10, NY 64, OH 174, OK 21, OR 83, PA 102, RI 14, SC 3, SD 16,
TN 28, TX 113, UT 37, VA 27, VT 9, WA 114, WI 105, WV 10, WY 16`.

## Gate

**PASS.** Every remaining URL-bearing queue identity is selected exactly once;
every selected row has complete municipality/Census identity, a syntactically
valid HTTP(S) URL, its original disposition, and a unique Round 2 verification
ID. No Round 1 identity was substituted or repeated, and no URL was opened.
