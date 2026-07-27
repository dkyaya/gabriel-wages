# Stress-test report

- Count drift: fail closed unless the completed source-review queue is 556 and retained files are 463.
- Missing retained file: fail closed unless all 463 local retained paths exist.
- Stale current-facing UI phrase: fail closed for the prior PI-report label, first-verification-round next step, or discovery-phase headings.
- Mixed current/historical display: discovery coverage, tiers, operations, queue, yield, and state reports must be labeled historical.
- Report-link regression: fail closed unless exactly one current report exists and it is the bounded memo.
- Analysis overclaim: fail closed if global readiness becomes true or a wage-gap/causal result is presented.
- Unsafe source work: this runner never opens retained files, downloads sources, parses pages, extracts text, renders, OCRs, rates, ingests, or codifies.
