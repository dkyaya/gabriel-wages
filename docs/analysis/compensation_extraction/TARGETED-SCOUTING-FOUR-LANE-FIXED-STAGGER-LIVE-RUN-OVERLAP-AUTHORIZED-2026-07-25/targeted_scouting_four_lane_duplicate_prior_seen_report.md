# Duplicate and prior-seen accounting

The immutable queues carried 2000 targets into live scouting. Parsed candidate locators were deterministically canonicalized across lanes. 80 duplicate candidate lead(s) were excluded from the combined candidate-only registry; no prior durable candidate/source ledger was mutated or merged.

- Candidate sources retained: 4228
- Duplicate candidate locators excluded: 80
- Explicit target skips: 549
- Prior-seen status counts: `{'known_safety_row_counterpart_target_not_satisfied': 7, 'municipality_and_non_safety_lead_seen_mechanism_target_is_new': 172, 'municipality_seen_safety_lead_target_unit_not_seen': 321, 'not_seen_in_consolidated_prior_scout_or_candidate_ledgers': 1500}`
- Queue duplicate-risk counts: `{'low': 1828, 'medium': 172}`
