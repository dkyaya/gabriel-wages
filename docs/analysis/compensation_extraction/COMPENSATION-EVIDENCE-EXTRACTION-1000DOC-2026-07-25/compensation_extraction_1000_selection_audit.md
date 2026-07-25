# Frozen cumulative 1,000-document selection audit

- Exact unique identities: 1000
- Corrected 500-document seed reused without GABRIEL: 500
- New retained identities: 500
- Cumulative units: `{"fire": 237, "non_safety": 400, "police": 363}`
- New units: `{"fire": 117, "non_safety": 200, "police": 183}`
- States/DC represented: 40
- Source families: `{"arbitration_award": 5, "cba": 951, "factfinding": 1, "memorandum_or_settlement": 10, "ordinance_or_policy": 9, "wage_schedule_or_compensation_plan": 24}`
- Packet rows: 5767; maximum six pages per case.
- Text caps: 1,500 characters per page and 6,000 per case.
- Selection SHA-256: `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`

The additive quotas are 183 police, 117 fire, and 200 non-safety because the
retained local pool has only 117 new fire identities with an explicit selected
non-safety partner across the cumulative seed. This preserves matching rather
than forcing three unmatched fire cases. The cumulative totals are 363 police,
237 fire, and 400 non-safety.

The freeze made zero GABRIEL/API calls and saved no full document/page text,
full table, raw prompt/response, or encoded image copy.
