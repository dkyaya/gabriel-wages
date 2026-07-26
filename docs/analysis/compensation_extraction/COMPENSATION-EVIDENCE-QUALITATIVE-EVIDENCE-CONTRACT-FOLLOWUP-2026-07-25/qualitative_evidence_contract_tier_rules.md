# Qualitative evidence-contract tier rules

| Tier | Required span status | Required span QA | Candidate eligible | Permitted use |
|---|---|---|---|---|
| `exact_span_coded_candidate` | `exact_verified` | `span_exact_unique_verified`; pass=`true` | true | Separate limited readiness review only |
| `ambiguous_exact_span_navigation` | `span_ambiguous_multiple_candidates` | navigation-only | false | Navigation, audit, future bounded repair |
| `unavailable_span_navigation` | `span_unavailable_or_unverified` | navigation-only | false | Navigation, audit, future bounded repair |

The tiers are exhaustive and mutually exclusive. Fuzzy, paraphrased, inferred, cross-page, OCR-derived, image-derived, URL-derived, model-derived, and full-page evidence are inadmissible. Exact candidate status does not change historical QA, analysis readiness, or causal interpretation.
