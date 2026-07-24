# Future Coordinator Prompt — Content-Triage Round 1 Serial Merge

Use only after separately authorized content-triage lanes complete and the
lane auditor recommends `merge_all_content_triage_lanes`.

Work only in the main coordinator repository. Do not inspect remotes or push.
Do not open URLs, download documents, parse PDFs, run OCR, or perform live
review during the merge.

Round: `CONTENT-TRIAGE-ROUND1-1000-2026-07-24`

1. Require a clean tracked worktree and exact input hashes.
2. Re-run `scripts/audit_content_triage_lanes.py`.
3. Require both lanes `completed_merge_eligible`, 1,000/1,000 terminal rows,
   zero duplicate triage/queue IDs, preserved duplicate groups, and no
   protected/accounting mutations.
4. Merge exactly once into a round-specific durable `content_triage_ledger`
   and summary. Preserve all routing/candidate provenance and preliminary
   labels.
5. Do not overwrite prior cumulative triage history with only the newest
   round. Maintain explicit round-specific and cumulative/latest outputs.
6. Refresh dashboard content-triage status from the merged summary.
7. Validate, commit locally, and create a relay.

The merge must not update scout queue/coverage, contracts, city coverage,
corpus, or the durable URL-routing outcomes. It must not ingest, codify,
download/parse documents, extract wages, calculate wage gaps, make causal
claims, or run regressions.
