# GABRIEL Codify Massachusetts — Prompt Preview — 2026-07-09 (run date 2026-07-10)

## Selected rows (10, dry-run verified)

1. `ma_somerville_police_spsoa_2012` — MA, Somerville, police (arbitration_award)
2. `ma_wayland_fire_jlmc_2020` — MA, Wayland, fire (arbitration_award)
3. `ma_franklin_police_2022` — MA, Franklin, police
4. `ma_franklin_fire_2022` — MA, Franklin, fire
5. `ma_franklin_public_works_2022` — MA, Franklin, public_works
6. `ma_franklin_library_2022` — MA, Franklin, library
7. `ma_franklin_other_2022` — MA, Franklin, other (custodians)
8. `ma_boston_clerical_admin_2023` — MA, Boston, clerical_admin
9. `ma_georgetown_other_2020` — MA, Georgetown, other (custodians)
10. `ma_georgetown_police_2020` — MA, Georgetown, police

Full rationale in `docs/analysis/gabriel_codify_massachusetts_sample_selection_2026-07-09.md`. Windows source: `docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv`, built fresh this session directly from the underlying corpus PDFs (`pdftotext -layout`, no ingestion) — not reused from a prior extraction file, since no Massachusetts-specific deterministic excerpt CSV existed yet.

## Full codebook reference (unchanged from the pilot and the Texas/Ohio scale-up)

19 attributes, defined in `scripts/gabriel_codify_pilot.py`'s `CATEGORIES` dict, verbatim identical to `docs/analysis/gabriel_codify_full_codebook_pilot_design_2026-07-09.md` Section 4. No codebook changes this run. Binary semantics preserved: `evidence_status` is `present`, `not_found`, or `unclear`; no confidence/caveat scoring added.

## Output schema (per attribute, per row)

`evidence_status` (present/not_found/unclear), `excerpt` (verbatim, <40 words, blank if not_found), `excerpt_location` (if identifiable), `confidence` (fixed `not_applicable` — `gabriel.codify()` has no native confidence field), `caveat` (blank/one sentence).

## Representative window (excerpt) — `ma_somerville_police_spsoa_2012`

```
--- Excerpt 1 ---
1
Analysis and Issues
 Under the Collective Bargaining Laws of Massachusetts,
the Interest Arbitration process is utilized when "there is
an exhaustion of the process of collective bargaining which
constitutes a potential threat to public welfare". In
reaching the conclusions in the present award, the
Arbitration Panel has considered the criteria set forth in
the statute including the municipality's ability to pay,
wag[es and benefits of comparable towns...]

--- Excerpt 2 [Section 3] ---
e selected by mutual agreement of the parties; the parties may also
agree to submit the grievance to the State Board of Conciliation and Arbitration for arbitration in
accordance with its procedures. If the parties are unable to agree on an arbitrator or said State
Board, the Association, within thirty (30) days after said written notice to the Mayor, may request
the American Arbitration Association to provide a panel of arbitrators...

--- Excerpt 3 ---
dermen and the Mayor by virtue of statutes or ordinances not superseded by this Agreement, and
cannot be subject to any grievance or arbitration proceeding except as specifically provided for in
this Agreement.

[... 3 more excerpts: overtime compensation, holdover/detail pay, a UMass Collins Center
classification-and-compensation study reference -- 3,891 characters / ~641 words total, well
under the 1,500-word max_words_per_call cap]
```

This window is a strong, genuine test of the codebook's interest-vs-grievance-arbitration distinction: Excerpt 1 is real interest-arbitration analysis text (a JLMC arbitration panel's own opinion), while Excerpts 2-3 are ordinary grievance-arbitration procedure clauses from the underlying base CBA the award amends. **Note the separator format**: `--- Excerpt N [location] ---`, containing only a sequence number and (where found) a genuine `Section`/`Article` marker pulled from the source text itself — no mechanism name, codebook label, or analytical hint of any kind, directly repairing the Texas/Ohio scale-up's header-leakage defect.

## Exact dry-run command used

```
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 10 \
  --windows docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv
```

Matches this run's task instructions exactly (no CLI adjustment needed). Output: `tmp/gabriel_codify_pilots/2026-07-10_102543/` — `run_config.json` confirms `max_calls_allowed: 10`, `max_calls_requested: 10`, `use_harvard_proxy: true`, `n_attributes: 19`, `live_run_attempted: false`, all 10 `selected_contract_ids`. `dry_run_log.txt` confirms no network call and no credential read.

## Confirmation: source-window body headers are neutral

Every one of the 10 windows was built via `docs/analysis/gabriel_codify_massachusetts_evidence_windows_2026-07-09.csv`'s builder script, which runs a hard-fail contamination check (`check_contamination()`) against all 19 `CATEGORIES` keys plus `"Mechanism"`/`"Arbitration / impasse"` before writing the CSV, and again on round-trip parse — 0 hits across all 10 windows. `scripts/gabriel_codify_pilot.py`'s own independent read-time check (`_check_window_contamination()`, added this session) additionally re-verified this immediately before the dry run above ran successfully (a contamination hit would have caused the dry run to `sys.exit(1)` before reaching this point — verified separately via a deliberately re-contaminated copy of the same CSV, which did fail as expected).
