# Parallel Round 2 3×150 Dashboard, Yield, and Checkpoint Refresh

Date: 2026-07-23

## Disposition

**Complete.** After the successful serial queue/coverage rebuild, the
coordinator refreshed scout yield learning and all dashboard JSON:

```text
python scripts/build_scout_yield_learning_report.py
python scripts/build_dashboard_data.py
```

The dashboard builder was run again after the authorized priority refresh so
the priority and project-phase layers share the same current accounting
vintage.

## Current checkpoint

- Scout-covered municipalities: **1,537 / 2,000**
- Progress: **76.9%**
- Remaining: **463**
- Comparable 150-row waves remaining: **4** when counted serially
- Candidate queue rows: **3,347**
- Candidate-positive municipalities: **1,267**
- Failure-only municipalities: **27**

`project_phase_summary.json` and `parallel_scout_status.json` now report the
completed and serially merged three-lane Round 2. The operations layer
recommends a checkpoint-targeted custom three-lane collection rather than
automatically launching the prepared 3 × 300 feasibility round.

## Yield refresh

The yield report now contains six reviewed waves/parallel rounds. The latest
round records:

- 450 attempted and 446 parseable municipalities;
- 383 candidate-positive and 63 parseable-empty municipalities;
- four failure-only rows;
- 985 candidate lead rows;
- 5,615.561 seconds parallel wall time;
- 288.484 attempted rows/hour; and
- 2.209 candidate rows per parseable municipality.

Among states with at least ten successful scouts, the refreshed top ten by
candidate rows per covered municipality are OH, MD, MA, PA, CT, WA, OR, CA,
IL, and NM. Before this merge the top ten were OH, IA, WA, WI, CT, PA, OR,
MA, NM, and CA. These rankings are operational source-discovery yield signals;
they are not source-quality, wage, or causal findings.

## Dashboard status

All generated dashboard JSON files parse. The frontend operations note now
states that the 3 × 150 collection and its serial merge succeeded, that
candidate exports remained lane-local, and that 3 × 300 would likely
overshoot the approximately 2,000 checkpoint.

Candidate rows remain unverified leads. The planned wage-growth-gap percentage
map/filter remains inactive because verified and extracted wage observations
do not yet exist. The dashboard makes no claim that wage gaps exist and does
not report mechanism correlations or regressions.
