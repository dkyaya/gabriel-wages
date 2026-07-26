# GABRIEL claim-rating stress-test report

The 69-test focused suite exercises all registered adversarial modes, including input contamination, schema drift, quote paraphrase, weak-category overuse, strike-direction handling, forbidden final claims, preflight bypass, checkpoint corruption, reconciliation failure, raw-payload persistence, dashboard overpromotion, descendant-state compatibility, and partial-output masquerading. All 69 tests passed.

The live preflight surfaced two weak-diagnostic validator inconsistencies and the predecessor suites surfaced one dashboard descendant-state incompatibility. All three were fixed without relaxing exact-quote, input-scope, causal-boundary, or global-readiness guards, and regression coverage was added.
