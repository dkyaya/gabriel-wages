# Independent adjudication PREP1 validation

Date: 2026-07-25
Packet: `TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`

## Result

**PASS.** The 150-case human packet is blinded, bounded, internally
consistent, and ready for future independent human review. Human adjudication
has not started, and no extraction is authorized.

## Commands and results

The required commands completed successfully:

```text
.venv/bin/python -m py_compile scripts/prepare_independent_text_table_adjudication_packet.py
.venv/bin/python -m py_compile scripts/test_independent_text_table_adjudication_packet.py
.venv/bin/python -m py_compile scripts/build_dashboard_data.py
.venv/bin/python scripts/test_independent_text_table_adjudication_packet.py
.venv/bin/python scripts/build_dashboard_data.py
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
git diff --check
npm run build  # from docs/dashboard
```

Results:

- Python compilation: pass.
- New synthetic/offline packet tests: 7/7 pass.
- Dashboard data build: pass.
- Repository schema validation: pass.
- Ingestion tests: 60/60 pass.
- Coverage audit: pass.
- Dashboard frontend production build: pass; only the existing Vite chunk-size
  advisory appeared.
- Diff whitespace check: pass.

## Packet integrity

- cases: 150;
- unique adjudication IDs: 150;
- unique preserved calibration/source-review/PDF-readiness/candidate
  identities: 150 each;
- human-facing REVIEW1/REVIEW2 label fields: zero;
- prior extraction-gate/action fields in human CSV: zero;
- human rows initialized `not_reviewed`: 150;
- render manifest rows: 785;
- rendered pages present: 785;
- maximum rendered pages per case: six;
- render failures: zero;
- manifest/image byte-size matches: 785/785;
- manifest/image SHA-256 matches: 785/785;
- rendered bytes: 106,889,932;
- PDFs or text files created inside the packet: zero;
- full text, complete tables, or structured wage values created: zero;
- dashboard JSON parses and reports the required adjudication status.

The images are bounded local review aids, not wage observations. Their roughly
102 MiB size makes them unsuitable for the lite relay; they remain in the
local packet while the manifest, hashes, case index, and instructions carry
the review plan.

## Immutability

Final hashes equal the pre-run baselines:

| Protected input or authority | SHA-256 |
|---|---|
| Original calibration input | `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` |
| REVIEW2 reviewed CSV | `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a` |
| REVIEW2 summary JSON | `02f751e78f2ef412444912bb6eda7087907b32da618cb9a9f69082d06366037a` |
| REVIEW2 decision JSON | `662b465f441df4359e3261b40c821e453dd672b5243e24c76634c5ec87b44b3c` |
| REVIEW1 directory file-hash inventory | `722d5b01c7a9aba3e653852aef5de60fa566e6168247b010e3bdde716a39b7b8` |
| Durable text/table-detection ledger | `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03` |
| Durable PDF-readiness ledger | `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953` |
| Durable source-review ledger | `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f` |
| `data/contracts.csv` | `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8` |
| `data/city_coverage.csv` | `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3` |
| Sorted corpus filename inventory | `32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322` |

No diff exists under the original calibration packet, REVIEW1, REVIEW2,
routing ledgers, metadata-triage ledgers, source-review ledgers,
PDF-readiness ledgers, text/table-detection ledgers, protected data CSVs, or
`corpus/`.

## Safety confirmations

- URLs opened: 0.
- Network/API/model/hosted-search calls: 0.
- Downloads or redownloads: 0.
- OCR runs: 0.
- Wage extraction runs: 0.
- 500-document extraction prompt runs: 0.
- Smaller extraction pilot runs: 0.
- Ingestion actions: 0.
- `gabriel.codify` actions: 0.
- Durable-ledger mutations: 0.
- Wage-gap calculations, causal claims, and regressions: 0.
- Remote inspections, fetches, pulls, pushes, or remote mutations: 0.
- High-risk secret signatures in new/changed packet artifacts: 0.

## Corpus snapshot

`ingest/audit_coverage.py` reports 64 contracts, 19 cities, 28 healthy
matched pairs (10 exact and 18 overlap), two exploratory adjacent matches,
and six unmatched safety units. This task did not modify corpus data or
coverage.
