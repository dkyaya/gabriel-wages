# Full-Universe Metadata-Only Content-Triage Serial Merge Validation

Date: 2026-07-24

## Result

**PASS.** The cumulative merge implementation, durable 4,726-row ledger,
latest pointers, dashboard status, and protected boundaries passed validation.

## Commands and checks

- Six requested Python modules compiled.
- `python scripts/test_content_triage_planning.py`: 18/18 tests passed.
  The suite includes multi-round merge preservation, deterministic summaries,
  lower-disposition preservation, zero-source-access enforcement, overwrite
  refusal, and failures for duplicate triage IDs, duplicate candidate IDs,
  nonterminal rows, non-merge-eligible audits, and routing-identity mismatch.
- Final Round 1 audit: two `completed_merge_eligible` lanes, 1,000/1,000
  terminal rows, zero source access, and
  `merge_all_content_triage_lanes`.
- Final remainder audit: four `completed_merge_eligible` lanes, 3,726/3,726
  terminal rows, zero source access, and
  `merge_all_content_triage_lanes`.
- Durable cumulative ledger: 4,726 rows, 4,726 unique triage IDs, 4,726
  unique candidate-queue IDs, and exact candidate identity equality with the
  cumulative routing ledger.
- Cumulative/latest ledger files are byte-identical. Cumulative/latest summary
  files are byte-identical.
- `python scripts/build_dashboard_data.py` completed for 51 states/DC, 35,589
  municipalities, 2,436 scout-covered municipalities, and 4,726 candidate
  rows.
- Dashboard JSON parsed and reports
  `metadata_only_full_universe_merged`, 4,726 merged rows, and merge status
  `merged`.
- The dashboard production build passed.
- `python scripts/validate.py` passed.
- `python ingest/test_pipeline.py`: 60/60 tests passed.
- `python ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact and 18 overlap), two exploratory adjacent matches,
  and six unmatched safety units.
- `git diff --check` passed.

Validation output is preserved under:

`tmp/content_triage_full_universe_metadata_serial_merge_validation_2026-07-24/`

## Immutable boundaries

Before/after SHA-256 checks are unchanged:

| Artifact | SHA-256 |
|---|---|
| `data/contracts.csv` | `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8` |
| `data/city_coverage.csv` | `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3` |
| canonical candidate queue | `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83` |
| cumulative routing ledger | `831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499` |
| cumulative routing summary | `f701b48f94e65e6b7a5f26a2d3d479f05f86530d1f9f33ed3bd8e59c35f1fca0` |
| aggregate `corpus/` hash | `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a` |

All row-level and summary source-access counters are zero. No URL was opened;
no network/API/model/hosted-search/scout call, download, document/PDF parse,
or OCR operation occurred.

The provenance-aware safety check confirms that `candidate_url`, `final_url`,
and `source_locator` are byte-identical to their committed routing inputs.
Thirty-six field references contain inherited public URL query parameters
whose names resemble access/signature parameters; no query value was printed
or newly introduced. No secret-like pattern exists in any non-URL ledger
field.

No scout queue/coverage accounting or durable URL-routing artifact changed.
No source rating, ingestion, codification, wage extraction, wage-gap
calculation or claim, causal claim, regression, remote inspection, fetch,
pull, or push occurred.
