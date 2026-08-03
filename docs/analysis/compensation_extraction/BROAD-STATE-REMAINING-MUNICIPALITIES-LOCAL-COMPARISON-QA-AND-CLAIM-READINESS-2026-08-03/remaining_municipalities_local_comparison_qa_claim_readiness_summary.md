# Remaining-municipality local comparison QA and claim readiness

Decision: `broad_state_remaining_municipalities_local_comparison_qa_claim_readiness_completed_repo_cleanup_ready`.

- Deduplicated local comparison QA pool: 17
- Local QA statuses: {"conditional_example_ready": 4, "local_supporting_example_ready": 13}
- Same-side QA statuses: {"same_side_claim_ready": 266, "same_side_context_only": 97, "same_side_needs_repair": 864, "same_side_supporting_example_ready": 1341, "same_side_write_off": 526}
- Quant–qual mechanism QA statuses: {"blocked_mechanism_link": 32, "moderate_mechanism_link_supporting": 359, "not_linkable_write_off": 208, "strong_mechanism_link_claim_ready": 636, "weak_mechanism_link_review": 15}
- Side-independent mechanism QA statuses: {"side_independent_mechanism_claim_ready": 15, "side_independent_mechanism_context": 20, "side_independent_mechanism_supporting": 57}
- National-readiness QA statuses: {"national_growth_readiness_ready": 346, "national_insufficient_structure": 470, "national_mechanism_readiness_ready": 745, "national_needs_pay_basis_repair": 463, "national_needs_period_repair": 161, "national_needs_side_balance": 3694, "national_readiness_stratum_partial": 2044, "national_readiness_stratum_ready": 299, "national_write_off": 493}
- Gates: {"growth_evidence_gate": "partial", "local_comparison_gate": "partial", "mechanism_evidence_gate": "pass", "national_readiness_gate": "partial", "non_base_compensation_evidence_gate": "partial", "same_side_evidence_gate": "partial"}

Every requested evidence group was processed. Raw evidence is preserved through the canonical source pointers, hashes, and copied provenance fields. No polished deliverable, final wage-gap, national, prevalence, policy-effect, or causal claim was created. Global analysis, wage-gap, and causal readiness remain false.
