# Remaining readable parse-text selection audit

- Durable remaining rows outside the frozen 1,000 hashes: 827
- Frozen unique remaining content hashes: 826
- Corrected 1,000-document seed retained without GABRIEL: 1,000
- New GABRIEL-required cases: 826
- Units: `{"fire": 202, "non_safety": 207, "police": 417}`
- States/DC represented: 48
- Priorities: `{"p1": 430, "p2": 391, "p3": 5}`
- Source families: `{"arbitration_award": 5, "cba": 766, "factfinding": 1, "memorandum_or_settlement": 10, "ordinance_or_policy": 10, "wage_schedule_or_compensation_plan": 34}`
- Matched non-safety opportunities retained: 270
- Packet page rows: 4610
- Maximum pages per case: 6
- Maximum text characters per page/case: 1499 / 5999
- Selection SHA-256: `43b768fba4e3d122727d2cbf9614885922a55be5f2bd1afd37d36f47a4695d81`

The 827-row / 826-hash discrepancy is one exact retained-content duplicate in
North Miami, Florida. Both durable rows point to the same SHA-256
`8848b83eb035d9cfba1345c940ce69662fdc3e092bc52f60ea7599820389289c`. The selected representative is
`ttd_a930d5e423fad93db8dcaac1`; the excluded duplicate
detection identity is `ttd_ecb0448e2ddaf335f23eced8`.
The deterministic rule selects the highest evidence score and then the lexical
detection ID. The duplicate hash is sent once, not twice, and both identities
remain documented here and in the selection summary.

The freeze made no GABRIEL/API calls and saved no full document/page text,
full table, raw prompt/response, or encoded image copy. OCR-later documents and
all hashes in the frozen 1,000-document selection are excluded.
