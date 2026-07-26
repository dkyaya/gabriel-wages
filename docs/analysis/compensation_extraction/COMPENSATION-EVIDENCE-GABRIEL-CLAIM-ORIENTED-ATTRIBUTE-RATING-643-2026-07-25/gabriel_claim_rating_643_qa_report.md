# GABRIEL claim-oriented rating QA report

The bounded run rated 608 of 643 authorized exact-span rows; 35 rows are quarantined. Valid plus quarantined rows reconcile exactly to 643 with no duplicate evidence IDs. All valid rows contain the complete 14-attribute v1.1 contract. Every positive supporting quote passed exact-substring validation against its supplied span.

No raw prompt or raw response was persisted. No cross-row substantive statistics, wage effect, wage gap, regression, treatment effect, or final causal conclusion was computed. Global analysis readiness remains false.

Three in-scope guardrail defects were fixed: weak diagnostic rows now follow their published `not_claim_ready` semantics; the allowed weak strength/direction combinations match v1.1; and predecessor dashboard validators recognize the two bounded-rating descendant states without allowing global readiness.

Decision: `gabriel_claim_rating_643_completed_with_quarantine`.
