# Limited exact-span qualitative readiness review result

Decision: `limited_exact_span_qualitative_readiness_pass_with_blockers_documented`

The limited review verified all 759 exact-span candidates as unique, current-active, provenance-complete rows with valid literal-span hashes, offsets, page pointers, retained-content hashes, and separate historical/span QA fields. Zero ambiguous or unavailable rows entered the exact tier, and the three tiers still reconcile as 759 + 614 + 581 = 1,954.

This is a restricted pass, not global analysis readiness. Ninety-three exact-span rows remain `needs_review`; 226 lack an exact cycle; 239 lack a controlled occupation; 16 have historical mixed memberships; eight use `mechanism_type=other`; four lack structured mechanism detail beyond the label/span; and only 85 have exact matched-set support for the primary city-by-cycle design. A future limited promotion prompt may be run only with separate authorization and explicit row-level eligibility/quarantine fields.

The 614 ambiguous and 581 unavailable rows remain navigation-only. The 862 quantitative candidates, 1,045 quantitative exceptions, 4,733 non-base companion rows, 345 reference/control rows, and two unresolved groups/five observations remain separate and unchanged. No data promotion or analysis occurred, and analysis readiness remains false.
