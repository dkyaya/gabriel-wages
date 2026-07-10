# GABRIEL Codify Texas/Ohio Scale-Up — Prompt Preview — 2026-07-09

## Selected rows (8, one live call each, dry-run verified 2026-07-09)

1. `tx_houston_police_2024` — TX, Houston, police
2. `tx_austin_police_2024` — TX, Austin, police
3. `tx_austin_fire_2023` — TX, Austin, fire
4. `oh_columbus_police_2023` — OH, Columbus, police
5. `oh_columbus_other_2024` — OH, Columbus, other
6. `oh_cleveland_police_2025` — OH, Cleveland, police
7. `oh_cleveland_fire_2025` — OH, Cleveland, fire
8. `oh_cleveland_other_2022` — OH, Cleveland, other

Windows source: `docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv`, assembled entirely from already-verified verbatim excerpts in this project's prior deterministic hand-extraction (`texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`, `texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`). No new corpus text opened this session.

## Full codebook reference (unchanged from the 4-row pilot)

19 attributes, defined in `scripts/gabriel_codify_pilot.py`'s `CATEGORIES` dict (verbatim identical to `docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md` Section 4). No codebook changes this run beyond the label/typo corrections already reflected in the viewer (`scripts/build_codify_evidence_viewer.py`'s `ATTRIBUTE_INFO`).

Binary semantics preserved: `evidence_status` is `present`, `not_found`, or `unclear` (`unclear` used sparingly for suggestive-but-insufficient text; downstream evidence layer treats anything outside `{present, not_found, unclear}` as `not_found`, never invented).

## Output schema (per attribute, per row — unchanged from the pilot)

`evidence_status` (present/not_found/unclear), `excerpt` (verbatim, <40 words, blank if not_found), `excerpt_location` (if identifiable), `confidence` (high/medium/low/not_applicable), `caveat` (one sentence if uncertain/partial, else blank).

## Representative window (full text) — `oh_cleveland_police_2025`

```
--- Arbitration / impasse backstop (legacy code -- may be interest OR grievance arbitration; distinguish from text) [page 6] ---
nd services of the City of Cleveland will be conducted efficiently and effectively. WITNESS ETH The parties acknowledge that during the negotiations and/or interest arbitration which resulted in this Contract each had the unlimited right and opportunity to make demands and proposals with respect to any subject or matter not removed by law or regulation from the area of collective bargaining and that the understanding and agreements arrived at by ...

--- Staffing shortage / recruitment / retention [page 68] ---
tion of 12-hour shifts and the application of Contract terms as set forth herein. Accordingly, the City and the CPP A agree to amend the Contract as follows: I. Deployment to Enhance Service and Staffing: On or about January 1, 2024, the City implemented 12-hour tours of duty for Police Officers assigned to Basic Patrol duties. ...

[... 7 more labeled excerpt blocks: overtime/callback, classification/wage schedule, training/certification,
premium pay, subcontracting/outsourcing, total compensation/benefits, hazard/risk/management-rights context,
and other -- 5,603 characters / ~723 words total, well under the 1,500-word max_words_per_call cap]
```

This window is a strong test case for the codebook's most important distinction: the `interest_arbitration_or_formal_impasse_backstop` vs. `grievance_or_contract_interpretation_arbitration` split. The "WITNESSETH" clause explicitly names "negotiations and/or interest arbitration which resulted in this Contract" — an interest-arbitration signal, not a grievance-arbitration one.

## Exact dry-run command used

```
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 8 \
  --windows docs/analysis/gabriel_codify_texas_ohio_scaleup_evidence_windows_2026-07-09.csv
```

This matches the command form given in this run's task instructions exactly (no CLI adjustment needed). Output: `tmp/gabriel_codify_pilots/2026-07-09_205718/` — `run_config.json` confirms `max_calls_allowed: 8`, `max_calls_requested: 8`, `use_harvard_proxy: true`, `n_attributes: 19`, `live_run_attempted: false`, and all 8 `selected_contract_ids`. No network call, no credential read (per `dry_run_log.txt`).

## Code change required to run this (documented, not silent)

`scripts/gabriel_codify_pilot.py`'s `HARD_MAX_CALLS` was raised from `4` to `8` as a deliberate, in-code, documented change for this approved scale-up (8 remaining rows, one call each) — see `docs/analysis/gabriel_codify_texas_ohio_scaleup_preflight_2026-07-09.md`. `--max-calls` above 8 is still refused.
