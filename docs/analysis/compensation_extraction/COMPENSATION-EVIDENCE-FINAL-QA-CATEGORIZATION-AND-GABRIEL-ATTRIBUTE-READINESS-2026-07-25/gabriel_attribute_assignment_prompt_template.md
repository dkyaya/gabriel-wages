# GABRIEL attribute assignment template

Classify only the supplied `evidence_id` and exact `evidence_span_or_summary_pointer`. Return JSON conforming to `gabriel_attribute_schema_contract.json`. Assign every taxonomy boolean. Use only literal support in the supplied span; never infer from government, occupation, filename, source family, or outside knowledge. Copy a short exact supporting substring into `evidence_quote`.

If evidence is insufficient, set `not_useful_for_attribute_analysis=true`, set unsupported attributes false, and provide a specific reason code. Do not use `null` or `no_good`. Do not estimate wage effects, compare groups, calculate statistics, make causal claims, or alter provenance. GABRIEL measurement is not causal proof.
