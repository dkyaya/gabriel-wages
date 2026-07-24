# Future Coordinator Prompt — Source-Review Pilot 1 Live

Use only under separate explicit authorization to open and download the 150
locked pilot sources. This prompt authorizes bounded source access and lane
audit only. It does not authorize a durable source-review merge, ingestion,
codification, wage extraction, wage-gap analysis, causal claims, or
regressions.

Work only in the main coordinator repository. Do not inspect remotes or push.

## Locked pilot and preflight

Pilot: `SOURCE-REVIEW-PILOT1-150-2026-07-24`.

Read the manifest, input audit, two lane inputs/audits, operating handoff,
source-rating schema, source-review operating procedure, and bounded-live-path
implementation summary. Require a clean tracked worktree and the bounded
runner implementation ancestry.

Recompute and require:

- lane 1: 75 rows,
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`;
- lane 2: 75 rows,
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`;
- 150 unique source-review and candidate-queue identities;
- zero cross-lane overlap; and
- unchanged p1, scheduled, CBA-candidate, reachable-PDF planning metadata.

Run fresh dry runs into new directories and audit them. Require 75/75 rows per
lane, two `dry_run_passed` classifications,
`dry_run_complete_no_live_source_review`, and zero URL, network, download,
parse, PDF, OCR, sample, and artifact counters.

## Bounded live collection

Refuse to reuse or overwrite either live directory. Create a separate
lane-command-log directory before launch, but let the runner create each live
output and its `candidate_artifacts` directory.

Run exactly two lanes. Each command must use:

```text
--review-mode source_rating_live
--download-mode bounded
--allow-live-content-access
--concurrency 4
--timeout 30
--connect-timeout 8
--read-timeout 20
--max-redirects 5
--max-bytes 26214400
--no-write-content-samples
```

Lane 1:

```bash
python scripts/source_review_sources.py \
  --input-csv docs/analysis/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_source_review_input.csv \
  --output-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_live_attempt1 \
  --candidate-artifact-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_live_attempt1/candidate_artifacts \
  --review-mode source_rating_live \
  --download-mode bounded \
  --allow-live-content-access \
  --concurrency 4 \
  --timeout 30 \
  --connect-timeout 8 \
  --read-timeout 20 \
  --max-redirects 5 \
  --max-bytes 26214400 \
  --no-write-content-samples
```

Lane 2 is identical except for `lane_2_source_review_input.csv`,
`lane_2_live_attempt1`, and its lane-local artifact directory. Preserve
console logs and exit codes outside the fresh live output directories. Start
the second lane only after confirming the first established its checkpointed
ledger and artifact directory. Do not launch a third lane, raise concurrency,
or retry into a new directory.

The runner must retain only bounded lane-local artifacts and metadata. It must
not write to `corpus/`, parse PDFs, run OCR, extract tables or wages, ingest,
or codify. Rating fields remain preliminary; wage and mechanism signals remain
unknown without inspected text.

## Audit, scaling decision, and stop

After both lanes terminate, run `scripts/audit_source_review_lanes.py`. Review
input hashes, identities, terminal statuses, access/download distributions,
artifact locality, exact hashes and sizes, observed content types, preliminary
ratings, errors, and the merge recommendation.

Create a live result review and validation record. Make the scaling decision
from quality and operations together:

- recommend 500 next only if all 150 rows are terminal, artifacts/hashes are
  clean, runtime is acceptable, manual-review burden is low, and preliminary
  ratings are useful;
- consider 750 or 1,000 only if runtime is exceptionally fast and artifact
  quality/rating usefulness remain strong;
- do not scale on speed alone; include artifact size, transport/parse errors,
  rating usefulness, and manual-review burden;
- keep OCR, heavy parsing, and intensive manual review in smaller lanes.

Commit and relay the collection, then stop before durable merge regardless of
the recommendation. A separate serial task must use the merge prompt.
