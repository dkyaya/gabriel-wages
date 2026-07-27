# Candidate deduplication and prior-seen report

- Upstream live-run locator duplicates already excluded: 80.
- Review-level stricter canonical-locator groups: 3 groups / 6 rows.
- Review-only duplicate exclusions: 3.
- Possible same-city normalized-title similarities: 9 groups / 20 rows. These were retained unless their canonical locator also duplicated another row.
- Deduped metadata-review rows: 4,225.
- Prior-seen counts: `{'known_safety_row_counterpart_target_not_satisfied': 16, 'municipality_and_non_safety_lead_seen_mechanism_target_is_new': 428, 'municipality_seen_safety_lead_target_unit_not_seen': 558, 'not_seen_in_consolidated_prior_scout_or_candidate_ledgers': 3226}`.

This review did not open locators or merge any row into a durable ledger.
