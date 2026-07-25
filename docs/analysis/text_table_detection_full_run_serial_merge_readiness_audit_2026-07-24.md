# Full Text/Table Detection Serial-Merge Readiness Audit

## Decision

`ready_to_merge_full_run_only`

The serial offline merge is authorized to use only the four completed local
lane ledgers for
`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`. The earlier
`TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24` outputs remain preserved as
superseded diagnostic provenance and must not be concatenated into the durable
result.

## Repository and scope gate

- pre-work HEAD:
  `827917bb201fb59bcfe1ce77dfd1fe3e29651ee6`
- tracked worktree at start: clean
- unrelated untracked item preserved and excluded: `package-lock.json`
- required ancestor commits confirmed:
  `827917b`, `4a9c2c7`, `11e689a`, `b45876e`, `74a843a`,
  `985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`,
  and `e028432`
- durable text/table-detection output directory before merge:
  absent

No git remotes were inspected or modified. No fetch, pull, or push was run.

## Fresh lane audit

The lane auditor was re-run with:

```text
.venv/bin/python scripts/audit_text_table_detection_lanes.py \
  --manifest docs/analysis/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/text_table_detection_pilot_manifest.json \
  --output-dir tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/serial_merge_lane_audit_2026-07-24
```

The fresh audit returned:

- Lane 1: `completed_merge_eligible`
- Lane 2: `completed_merge_eligible`
- Lane 3: `completed_merge_eligible`
- Lane 4: `completed_merge_eligible`
- planned / ledger / terminal rows: 1,828 / 1,828 / 1,828
- lane rows: 457 / 457 / 457 / 457
- duplicate text-table / PDF-readiness / source-review / candidate IDs:
  0 / 0 / 0 / 0
- detection status: `detection_checked` 1,828
- parser errors / hash failures / missing artifacts: 0 / 0 / 0
- invalid candidate-page hints / bounded hint overruns: 0 / 0
- frozen-heuristic mismatches: 0
- full-text artifacts: 0
- merge recommendation: `merge_all_text_table_detection_lanes`

## Exact authority equality

The authority is the subset of
`docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`
whose `recommended_next_action` is `parse_text_layer_later`.

An independent pre-merge validator confirmed:

- authority rows: 1,828
- full-run rows: 1,828
- exact `pdf_readiness_id` set equality: yes
- exact `source_review_id` correspondence: yes
- exact `candidate_queue_row_id` correspondence: yes
- artifact path, SHA-256 hash, byte size, content type, page count, and
  text-layer status match the authority row by row
- all 150 earlier pilot PDF-readiness identities are present in the full run
- the rerun results for those 150 identities match the frozen pilot heuristic;
  mismatches: 0

The full-run rerun is therefore the uniform operative result. Adding the pilot
rows would duplicate identities and is prohibited.

## Full-run signal summary

- wage-table signal: likely 1,067; possible 749; unlikely 12
- wage-table confidence: high 1,067; medium 749; low 12
- contract-period signal: likely 1,672; possible 103; unlikely 53
- contract-period confidence: high 1,672; medium 103; low 53
- table-like structure: likely 1,717; possible 107; unlikely 4
- extraction-pilot priority: p1 1,067; p2 754; p3 7
- recommended next action:
  - `wage_table_extraction_pilot`: 1,067
  - `larger_text_detection_pass`: 747
  - `contract_period_extraction_pilot`: 7
  - `manual_review`: 7
- candidate wage-page hints: 7,649
- pages scanned / pages with text: 17,861 / 17,369
- bounded characters inspected in memory: 21,232,318
- parser / frozen heuristic: pypdf 6.13.2 /
  `bounded_keyword_numeric_structure_v1`

These are preliminary deterministic detection signals and bounded page hints.
They are not wage observations, source-coded evidence, wage-gap findings, or
causal findings. The very high likely-or-possible rate requires manual
calibration before wage extraction.

## Forbidden-activity gate

Fresh audit and independent checks record:

- URLs opened: 0
- network/API/model calls: 0
- downloads/redownloads: 0 / 0
- OCR runs: 0
- full-text artifacts written: 0
- final wage values extracted: 0
- ingestion actions: 0
- codify actions: 0
- durable text/table-detection merges before this task: 0
- scout accounting mutations: 0
- durable URL-routing, metadata-triage, source-review, and PDF-readiness
  ledger mutations: 0

Baseline hashes were recorded for protected files and upstream authority
ledgers before the merge. The only durable data layer this merge may create or
update is the text/table-detection ledger/status layer.

## Merge recommendation

`merge_all_text_table_detection_lanes`

Proceed with one fail-closed serial merge of the four full-run ledgers. After a
clean merge, the next substantive task is a manually reviewed calibration
subset before any wage-table extraction pilot.
