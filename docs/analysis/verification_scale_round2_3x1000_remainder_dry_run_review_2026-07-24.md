# Verification Scale Round 2 3×1000 Remainder Dry-Run Review

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`

## Results

| Lane | Input rows | Dry ledger | Dry timing | Status |
|---|---:|---:|---:|---|
| Lane 1 | 826 | 826 | 826 | `dry_run_passed` |
| Lane 2 | 825 | 825 | 825 | `dry_run_passed` |
| Lane 3 | 825 | 825 | 825 | `dry_run_passed` |

All 2,476 rows have complete verification schema fields, syntactically valid
HTTP(S) locators, terminal `dry_run_planned` status, and a matching
`plan_timing.csv` row. Each dry summary records:

- total/connect/read timeout: 20/8/15 seconds;
- redirects: five maximum;
- response bytes: 10,485,760 maximum;
- concurrency: eight;
- content samples: disabled;
- robots/access note: enabled;
- live verification performed: false;
- URLs opened/network calls: 0/0.

The plan contains 74 exact duplicate URL groups and 90 follower rows eligible
for in-lane representative reuse; zero groups are split across lanes.

The combined dry auditor classifies all three lanes `dry_run_passed`, inspects
2,476/2,476 dry-terminal rows, and reports zero URL opens/network calls.
Its `do_not_merge_until_resume_or_review` recommendation is correct because
dry output must never be merged as live routing evidence.

**Gate: PASS.** The locked inputs and bounded live commands are ready for the
separately authorized live collection. Dry-run execution did not ingest,
codify, extract wages, calculate gaps, run scouts/models, or alter accounting.
