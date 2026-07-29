# Next task: bounded exact-span rating in four parallel lanes

Rate only the 17,259 exact rows in `combined_broad_span_extraction_3815_rating_candidate_manifest.csv`.
Do not rerun source review, readiness, text extraction, or span extraction. Do not normalize or
compare wage values, ingest, codify, calculate gaps, estimate effects, or make population/causal
claims. Preserve verbatim spans, offsets, hashes, provenance, the total-scout-only dashboard map,
and `global_analysis_readiness = false`. Use four independently checkpointed lanes with standard
T+0/T+8/T+16/T+24 starts and controlled overlap. Rating needs explicit authorization.

## Post-rating artifact completeness rule

Before closing the rating task, verify that every downstream summary input exists. If a required
summary artifact is fully derivable from committed valid/quarantine/results ledgers, reconstruct it
deterministically, validate complete reconciliation, commit and push the repair, and continue.
Missing non-derivable artifacts fail closed. Do not report dashboard/public state updated unless
plain `git push` succeeds. Full text and retained binaries remain ignored and untracked.
