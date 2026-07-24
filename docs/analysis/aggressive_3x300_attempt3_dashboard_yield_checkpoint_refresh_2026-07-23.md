# Aggressive 3×300 Attempt 3 — Dashboard, Yield, and Checkpoint Refresh

Date: 2026-07-23/24

## Refresh result

The coordinator refreshed:

```text
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

After the unchanged-methodology priority rebuild, the dashboard builder ran
again so all final JSON layers share the same current accounting and priority
vintage.

The yield report now contains 51 state/DC rows and seven reviewed coordinated
waves/rounds. Attempt 3 is the latest round:

- 900 attempted;
- 899 parseable;
- 591 candidate-positive;
- 308 parseable-empty;
- one failure-only;
- 1,389 parsed lead rows;
- 9,422.628 seconds parallel wall time;
- 343.853 attempted rows/hour; and
- 1.545 parsed leads per parseable municipality.

## Project-phase status

`project_phase_summary.json` now records:

- current phase: `Verification planning and source triage`;
- 2,436 scout-covered municipalities;
- checkpoint status: `reached_exceeded`;
- checkpoint margin: +436;
- zero ordinary waves remaining;
- 4,726 URL-bearing candidate rows;
- no additional broad round planned; and
- the active instruction to pause broad scouting.

`parallel_scout_status.json` records
`aggressive_3x300_completed_accounting_merged`, all three Attempt 3 lanes,
899 parseable outcomes, 1,379 URL-bearing queue additions, and serial
accounting after audit. The dashboard frontend and README were updated from
the obsolete “planned 3×300” language to the post-checkpoint verification
transition.

## State-yield learning

The top 15 states with at least ten successful scouts, ranked by current
candidate rows per covered municipality, are:

| Rank | State | Covered | Candidate density |
|---:|---|---:|---:|
| 1 | NV | 11 | 3.091 |
| 2 | NH | 13 | 2.846 |
| 3 | MA | 60 | 2.683 |
| 4 | WA | 90 | 2.633 |
| 5 | OR | 69 | 2.609 |
| 6 | CT | 24 | 2.583 |
| 7 | CA | 304 | 2.546 |
| 8 | MT | 21 | 2.524 |
| 9 | OH | 328 | 2.494 |
| 10 | IL | 123 | 2.423 |
| 11 | ME | 20 | 2.300 |
| 12 | MI | 73 | 2.274 |
| 13 | AK | 13 | 2.231 |
| 14 | IA | 36 | 2.083 |
| 15 | NE | 15 | 2.067 |

Nevada, New Hampshire, Montana, Maine, Alaska, and Nebraska enter the displayed
top 15 after the larger cross-state sample. Ohio remains high-yield but its
candidate density moderates as its covered base rises from 179 to 328.
These are operational discovery-yield patterns, not source-quality or wage
findings.

## Interpretation boundary

All candidate rows remain unverified. The dashboard's wage-growth-gap layer
remains planned and inactive; it contains no synthetic or calculated gaps.
The checkpoint is a workflow transition, not an evidentiary threshold.
Verification, extraction, ingestion, source rating, and matched descriptive
analysis must occur before any wage-gap result can be displayed.
