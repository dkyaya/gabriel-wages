# Deterministic external-data ingestion methodology

The ingestion input was 1,876,183 validated compact administrative observations, not the recall-heavy raw field or span hits. Raw extraction hits, boilerplate, labels, headers, structural repetitions, duplicate-only records, classification errors, superseded outputs, and failed-gate outputs were excluded.

Five independent local lanes ingested each compact observation once. Raw values, exact source coordinates, source hashes, record lineage, event lineage, and claim-linkage provenance were preserved. Source-specific observations remained physically independent. Cross-source corroboration was linked rather than merged. Conflicts and ambiguity flags remained explicit and unresolved. Canonical vocabularies standardized routing labels without changing substantive values.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.

These external observations were not scored using GABRIEL. Deterministic classification is not equivalent to GABRIEL rating, and mechanical QA was not independent human semantic gold coding. Claim-critical records were queued for later bounded semantic cross-examination.

No side, period, pay-basis, or compensation-basis reconciliation occurred. No normalization, safety/non-safety matching, wage-gap or growth calculation, aggregation, regression, treatment-effect analysis, claim adjudication, or visual production occurred. Implementation-event deduplication was not rerun.

The 12,844 unsearched targets and 7,895 verified sources held by storage capacity limit completeness. The corpus retains 1,029,482 unique native PDF pages, counted separately from text-page equivalents.
