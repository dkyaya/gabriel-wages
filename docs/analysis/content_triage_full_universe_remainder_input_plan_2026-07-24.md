# Full-Universe Metadata-Triage Remainder Input Plan

Date: 2026-07-24
Round: `CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24`

## Result

**PASS.** The planner selected every routed candidate identity not already in
the completed 1,000-row Round 1 metadata-only ledgers.

The exact command was:

```text
python scripts/prepare_content_triage_batches.py --routing-ledger-csv docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv --candidate-queue-csv docs/analysis/national_scout_candidate_queue_2026-07-20.csv --output-dir docs/analysis/content_triage_rounds/CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24 --round-id CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24 --exclude-triage-ledger-csv tmp/content_triage_rounds/CONTENT-TRIAGE-ROUND1-1000-2026-07-24/lane_1_metadata_only_attempt1/triage_ledger.csv --exclude-triage-ledger-csv tmp/content_triage_rounds/CONTENT-TRIAGE-ROUND1-1000-2026-07-24/lane_2_metadata_only_attempt1/triage_ledger.csv --priority-scope all_routed_remainder --include-nonreachable --include-too-large --include-lower-disposition --include-duplicates --metadata-only-all-statuses --batch-size 1000 --num-lanes 4 --balance-lanes --plan-only
```

## Identity and capacity audit

- Cumulative routed rows: 4,726
- Already metadata-triaged Round 1 rows: 1,000
- Exact selected remainder: 3,726
- Combined Round 1 plus remainder: 4,726
- Cross-round duplicate candidate-queue IDs: 0
- Combined unique candidate-queue IDs: 4,726
- Combined unique triage IDs: 4,726
- Remainder rows left unselected: 0
- Four-lane capacity: 4,000

| Lane | Rows | SHA-256 |
|---|---:|---|
| Lane 1 | 932 | `eb51159f098a759627d4e64acd403bfd0aaf262e008907dd4deef674a09fd7b1` |
| Lane 2 | 932 | `34b283beebb07c46b521c1e14410bafc052e45a399542448e216a0735235e5f1` |
| Lane 3 | 931 | `57982445180e636b21ccb6dfee2f60ad86fd6afb0fc655ca455964bc1e71d1ac` |
| Lane 4 | 931 | `17e31afe730b083f3b876357936cf404fbf8b6459cca675249bbb8ed3acf74e8` |

## Selected metadata distributions

### Routing status

| Status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 2,533 |
| `reachable_html` | 145 |
| `reachable_http` | 2 |
| `duplicate_of_verified_source` | 70 |
| `duplicate_same_url_pending` | 28 |
| `blocked_or_forbidden` | 339 |
| `not_found` | 264 |
| `too_large` | 261 |
| `error` | 45 |
| `ssl_error` | 17 |
| `timeout` | 14 |
| `connection_error` | 8 |

### Original candidate disposition

| Disposition | Rows |
|---|---:|
| `scheduled` | 2,600 |
| `context_hold` | 523 |
| `insufficient_hold` | 302 |
| `duplicate_hold` | 291 |
| `already_canonical` | 8 |
| `calibration_rejected` | 2 |

All lower dispositions remain unchanged in the lane CSVs.

### Candidate source type

| Source type | Rows |
|---|---:|
| `cba` | 2,000 |
| `wage_schedule_or_compensation_plan` | 803 |
| `memorandum_or_settlement` | 355 |
| `ordinance_or_policy` | 206 |
| `arbitration_award` | 151 |
| `factfinding` | 77 |
| `context_only` | 50 |
| `agenda_cover_sheet` | 28 |
| `unknown` | 21 |
| `meeting_minutes` | 11 |
| `index_page` | 10 |
| `blocked_or_unreadable` | 6 |
| `insufficient_source` | 5 |
| `pay_plan` | 3 |

### Routed content type

| Content type | Rows |
|---|---:|
| `application/pdf` | 2,855 |
| `text/html` | 728 |
| `unknown` | 127 |
| all other small routed types | 16 |

### State distribution

```text
AK 29; AL 14; AR 16; AZ 29; CA 568; CO 25; CT 32; DC 2; DE 17;
FL 241; GA 7; HI 1; IA 75; ID 20; IL 232; IN 58; KS 41; KY 18;
LA 22; MA 103; MD 57; ME 46; MI 166; MN 131; MO 56; MS 12;
MT 37; NC 17; ND 12; NE 31; NH 24; NJ 94; NM 41; NV 16;
NY 139; OH 364; OK 21; OR 126; PA 102; RI 14; SC 3; SD 37;
TN 28; TX 113; UT 37; VA 27; VT 15; WA 170; WI 214; WV 10;
WY 16.
```

## Expected deterministic triage categories

Applying the implemented metadata-only rules without writing outputs yields
the following planning expectation:

- `high_priority_content_review`: 760
- `medium_priority_content_review`: 1,232
- `low_priority_content_review`: 360
- `duplicate_defer_to_canonical`: 295
- `oversized_needs_separate_pass`: 261
- `blocked_or_unreachable_defer`: 603
- `needs_manual_review`: 205
- `already_canonical_context`: 8
- `excluded_from_content_review`: 2

These are preliminary metadata-only routing decisions. They do not confirm
source relevance, officialness, employer/unit match, content, wage tables, or
extractability.

No URL was opened; no source was downloaded or parsed; no PDF/OCR operation,
ingestion, codification, wage extraction, analysis, or durable triage merge
occurred.
