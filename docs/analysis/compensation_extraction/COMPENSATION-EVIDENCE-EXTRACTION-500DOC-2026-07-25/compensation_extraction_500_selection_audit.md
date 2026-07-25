# Frozen 500-document selection audit

- Exact unique document identities: 500
- Unit counts: `{"fire": 120, "non_safety": 200, "police": 180}`
- Source counts: `{"arbitration_award": 5, "cba": 452, "factfinding": 1, "memorandum_or_settlement": 10, "ordinance_or_policy": 9, "wage_schedule_or_compensation_plan": 23}`
- States/DC represented: 40
- Planned lanes: `{"mixed": 447, "qualitative": 1, "quantitative": 47, "reference_and_exclusion": 5}`
- Safety rows with a selected same-municipality non-safety opportunity: all.
- Packet pages: 2843; maximum six per case.
- Text caps: 1,500 per page and 6,000 per case.
- Selection SHA-256: `2341e68426e5e62bdf406817fed17c703ee116d7c31af81f9e73b8b96ad583fb`

The freeze made zero GABRIEL/API calls. It used only local retained, hash-
verified, PDF-signature-valid, OCR-free artifacts. No full text/table or page
snippet was saved in the manifests.
