# Future GABRIEL claim-rating prompt template v1.1

Rate exactly one supplied literal evidence span. Use only that span. Return the strict v1.1 JSON object with all 14 attributes. Each positive attribute needs its own exact-substring supporting quote and a short reason code. False attributes use an empty quote, `not_supported`, `not_claim_ready`, and `not_applicable`.

Do not infer from city, occupation, source identity, or outside knowledge. Do not calculate statistics, wage effects, wage gaps, treatment effects, or regressions. Do not state final causal claims. A provisional causal-candidate label means only that the supplied text states a plausible mechanism to investigate.

For strike/no-strike language, do not assume direction. No-strike provisions and arbitration/factfinding substitutes may have offsetting implications; use `neutral_or_unclear` unless the supplied span itself states direction.

The runtime supplies only `evidence_id`, `EXACT_EVIDENCE_SPAN`, and the stable codebook. Raw prompts and raw responses must not be persisted.
