# Limited exact-span qualitative promotion stress test

The promotion failure corpus registers 30 adversarial modes covering tier contamination, identity, span, provenance, active/QA, mixed joins, mechanism typing, cycle/occupation/matching eligibility, lane separation, conflicts, immutable inputs, dashboard readiness, checkpoint/resume, future prompt, relay, payload leakage, and count reconciliation. Final test totals are recorded in the validation report.

The new promotion suite passed 56/56 tests. Together with the three required predecessor suites, 178/178 focused tests passed; the repository's separate ingestion suite passed 60/60. No implementation bug was discovered in this promotion run, and no guardrail was weakened. The system rejected or quarantined every adversarial fixture as designed.
