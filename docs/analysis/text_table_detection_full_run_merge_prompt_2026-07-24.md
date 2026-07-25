# Future Prompt — Serial Full-Run Text/Table Detection Merge

Do not run this prompt as part of the full local collection task.

Work in the main coordinator repository only:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Run a serial, offline durable text/table-detection merge for:

`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

Use exactly these four lane ledgers:

- `tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/lane_1_local_attempt1/text_table_detection_ledger.csv`
- `tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/lane_2_local_attempt1/text_table_detection_ledger.csv`
- `tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/lane_3_local_attempt1/text_table_detection_ledger.csv`
- `tmp/text_table_detection_pilots/TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24/lane_4_local_attempt1/text_table_detection_ledger.csv`

Use the committed manifest and rerun its lane audit. Require all four lanes
to be `completed_merge_eligible`, all 1,828 rows terminal, no duplicate
detection/PDF-readiness/source-review/candidate IDs, no missing or unexpected
rows, no hash failures, no missing artifacts, no parser errors, no invalid
page hints, no hint overruns, no heuristic-version mismatches, no full-text
artifacts, and all prohibited-activity counters equal to zero.

Verify that the full-run PDF-readiness-ID and source-review-ID sets exactly
equal the durable PDF-readiness subset where:

- `recommended_next_action = parse_text_layer_later`;
- `text_layer_status` is `present` or `partial`; and
- the retained artifact path and hash are nonblank.

Verify the artifact path/hash/size/content-type/page-count values against the
durable PDF-readiness authority.

Create a cumulative durable text/table-detection ledger and summary for all
1,828 parse-text candidates, with latest pointers and a merge audit. Preserve
the earlier `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24` lane outputs as
superseded diagnostic provenance: all 150 pilot identities are already
included in the full-run rerun and must not be concatenated a second time.

Refresh the dashboard to `full_parse_text_merged`, but retain the distinctions
between heuristic detection, extraction readiness, final wage extraction,
ingestion, codified evidence, and analysis-ready wage observations.

Do not open URLs, access the network, download/redownload documents, parse
PDFs during the merge, run OCR, save complete text, extract final wage
values, ingest or codify documents, alter scout accounting, mutate routing,
metadata-triage, source-review, or PDF-readiness ledgers, calculate wage gaps,
make causal claims, run regressions, inspect remotes, or push.

After a successful merge, the next task is a manually reviewed,
stratified calibration subset of likely, possible, and unlikely page hints.
Do not proceed directly to final wage extraction.
