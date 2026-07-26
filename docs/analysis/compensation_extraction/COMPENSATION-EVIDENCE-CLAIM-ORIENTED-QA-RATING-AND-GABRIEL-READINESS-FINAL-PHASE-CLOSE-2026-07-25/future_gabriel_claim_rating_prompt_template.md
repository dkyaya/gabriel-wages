# Future GABRIEL claim-rating template

Rate only the supplied evidence ID and exact evidence span under codebook v1. Return schema-valid JSON with all 13 attributes. Do not use outside knowledge. For each present attribute, copy a short exact supporting quote and state a one-sentence claim boundary. If support is weak, use `weak_or_no_claim_support` with a specific reason code. Never use null/no_good.

Direction and causal-candidate fields are provisional evidence ratings, not causal conclusions. GABRIEL rating is not causal proof. Do not compute cross-row statistics, wage gaps, regressions, or effects.
