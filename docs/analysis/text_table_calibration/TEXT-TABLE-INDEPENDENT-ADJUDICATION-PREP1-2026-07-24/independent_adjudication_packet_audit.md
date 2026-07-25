# Independent adjudication packet audit

Packet: `TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`
Generated at: `2026-07-25T15:32:34Z`

## Result

**PASS.** Prepared 150 blinded cases. The human-facing CSV has
exactly 28 fields: 15 identity/page
fields and 13 human-review fields.

- REVIEW2 identity check: `exact_set_match_read_only`
- REVIEW1/REVIEW2 label fields in human CSV: `0`
- Prior extraction-gate/recommended-action fields in human CSV: `0`
- Render manifest rows: `785`
- Rendered pages: `785`
- Render failures: `0`
- Rendered bytes: `106889932`
- Maximum planned pages for any case: `6`
- Candidate-page window: `±1`
- Navigation-page budget: `4`
- Maximum rendered pages per case: `6`

## Immutability and safety

- Calibration input SHA-256 before/after: `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` / `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`
- REVIEW2 SHA-256 before/after: `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a` / `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a`
- Full document or page text saved: `no`
- Full tables saved: `no`
- Structured wage values saved: `no`
- URLs opened: `0`
- Network/API/model calls: `0`
- OCR runs: `0`
- Wage extraction runs: `0`
- Ingestion actions: `0`
- Codify actions: `0`

Rendering, when requested, uses only local PDF pages named in the bounded render
manifest. Images are review aids and are not wage observations.
