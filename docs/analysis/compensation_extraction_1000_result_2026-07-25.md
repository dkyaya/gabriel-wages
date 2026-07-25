# Provisional 1,000-document compensation extraction: stopped at preflight

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-PROVISIONAL-SCALE-2026-07-25`

## Result

The cumulative selection and packet freeze succeeded, but the representative
GABRIEL preflight failed the strict semantic schema. The run therefore stopped
before live extraction, exactly as required by the fail-closed rule. The
corrected 500-document provisional layer remains authoritative; no incomplete
1,000-document lane output is being presented as extraction.

## Frozen cumulative design

- Exactly 1,000 unique retained document identities and content hashes.
- Prior corrected seed preserved: 500 identities, zero new API calls.
- New expansion: 500 identities.
- Units: 363 police, 237 fire, 400 non-safety.
- Matching: every safety identity retains an explicit selected non-safety
  comparison pointer.
- States/DC: 40.
- Source families: six—951 CBAs, 24 wage schedules/compensation plans, ten
  memoranda/settlements, nine ordinances/policies, five arbitration awards,
  and one factfinding document.
- Frozen selection SHA-256:
  `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`.
- Packet rows: 5,767, covering all 1,000 identities.
- Packet caps: six pages/case, 1,500 text characters/page, and 6,000 text
  characters/case; observed maxima were 6, 1,499, and 5,999.

The additive unit mix is 183 police, 117 fire, and 200 non-safety. This uses
all 117 available new fire identities with an explicit selected non-safety
partner and avoids forcing unmatched cases merely to reproduce the earlier
percentage split.

## Preflight

GABRIEL ran only for six new representative cases after the no-call freeze and
local packet validation. Backend was `huit_openai_responses_direct_sdk`; model
was `gpt-5.4-nano`. The bounded requests contained 29 page references, 28,526
text characters, and one existing rendered image totaling 34,138 bytes.

Five cases were schema-valid. The conflict-prone case returned a
`mixed_ready` disposition without both mandatory quantitative and qualitative
sub-record types. The deterministic semantic validator rejected it rather
than coercing or repairing the answer. Preflight validity was 5/6 (83.3333%),
below the required 100% for live start.

No raw prompt, raw response, image copy, full page/document text, full table,
credential, or authorization header was retained.

## Decision

Decision: `stopped_at_preflight_schema_invalid`.

- Live 500-new-document extraction: not started.
- Cumulative observation counts: not computed.
- 1,000-document QA: not run because there are no live lane outputs.
- Scaling beyond 1,000: blocked.
- Latest usable provisional extraction layer: the corrected 500-document
  targeted-QA shadow ledgers.

The next action is to repair or further constrain the relationship between
`case_disposition` and required sub-record arrays, add a focused regression
fixture for the exact mixed-disposition failure, and rerun the unchanged
six-path preflight. Live extraction remains prohibited until all six pass.
