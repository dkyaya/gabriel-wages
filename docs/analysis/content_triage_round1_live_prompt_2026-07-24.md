# Future Coordinator Prompt — Content-Triage Round 1 Live

Use only under separate explicit authorization after a bounded metadata/content
review implementation has been added and offline-tested.

Work only in the main coordinator repository. Do not inspect remotes or push.

Round: `CONTENT-TRIAGE-ROUND1-1000-2026-07-24`

Read the round manifest, combined audit, both 500-row inputs/audits, operating
handoff, and the project content-triage schema/procedure. Recompute and require:

- Lane 1: 500 rows,
  `1ae2aef43cec1756c0169b1395f00d8a772ddd12fd98a6a70c5b2937b784bc2b`;
- Lane 2: 500 rows,
  `118f3ca494782d46e504bfb2ebded6c8afe9e22a7a81661808987ea78ae64688`;
- 1,000 unique triage IDs and candidate queue IDs;
- cumulative routing provenance and terminal eligible status for every row;
- zero cross-lane identity overlap; and
- exact duplicate-group provenance.

Run fresh dry runs first. Require 500/500 terminal `triage_planned` rows per
lane, zero URL opens, zero network calls, zero downloads, zero parsing/OCR,
and no protected/accounting changes.

Do not run live work until the implementation and explicit authorization state
whether review is committed-metadata-only or permits bounded URL/content
access. If bounded downloading is authorized later, require fresh lane-local
directories, conservative concurrency, per-file/batch byte ceilings,
content-type controls, checksums, checkpoint ledgers, no overwrite, and an
artifact audit. Never scrape licensed/authenticated sources.

Do not ingest, codify, extract wage values, calculate wage gaps, make causal
claims, or run regressions. Preserve preliminary field labels. After both
lanes terminate, audit them together, create review/validation artifacts,
commit locally, create a relay, and stop before durable triage-ledger merge.
