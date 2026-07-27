# Next prompt: bounded Tier C exact-span rating

Use only the 159 positive exact records in `tier_c_evidence_span_rating_candidate_manifest.csv`. Revalidate each exact substring, offset, and SHA-256 against its task-local extracted text artifact. Rate only the supplied exact span and bounded context; preserve source, city, unit, cycle, region, lane, mechanism target, file, and text lineage. Exclude ambiguous, no-span, extraction-quality, readiness, and source-review exclusions.

Do not fetch/pull, open URLs, download, access retained source files or PDFs, run OCR/rendering, call GABRIEL/API/a model without separate authorization, use evidence outside supplied spans/context, ingest, codify, normalize/compare values, calculate wage gaps, run regressions/treatment effects, make national/prevalence/final-causal claims, or set global analysis readiness true.

Dashboard update requirement: After every task, update dashboard/status/docs with any new substantive information unless there are genuinely no updates to provide. If no dashboard update is needed, explicitly report that no update was needed and why. Dashboard updates must preserve global analysis readiness false unless separately authorized, and must not imply wage gaps, regressions, treatment effects, national prevalence, or final causal claims.

Future source discovery defaults to broad state-by-state geographic coverage and explicit source-family diversity; mechanism-targeted scouting is secondary gap filling.
