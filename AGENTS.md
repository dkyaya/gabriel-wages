# CLAUDE.md — Project Instructions

This file is read automatically by Claude Code as standing instructions for this repository. Follow it on every task.

## What this project is

Research project (HBS, PI: Prof. Andrei Shleifer) measuring **why public-safety wages (police, fire) rise faster than other municipal occupations**, using the GABRIEL text-measurement toolkit.

The design is a **cross-occupation comparison within cities**: we hold city × time fixed and let occupation vary. The empirical claim ("safety wages rise more than any other position") is only measurable if every safety unit has at least one matched non-safety unit in the same city and bargaining cycle. Maintaining that matching is the single most important data-collection discipline in this repo.

## Unit of observation

**One row = one bargaining unit's contract, for one negotiation cycle, in one city.**

Example: "Cambridge MA Police 2019–2022" is one row. "Cambridge MA Clerical 2019–2022" is a separate row. Never collapse multiple units or multiple cycles into a single row.

## The two-corpus rule (do not merge)

There are two analytically distinct text types. They live in **separate tables** and must never be merged into one:

1. **Causal corpus** (`contracts.csv`) — text that *causes* wages: collective bargaining agreements, interest-arbitration awards, fact-finding reports. Institutional mechanism.
2. **Discourse corpus** (`discourse.csv`) — text that *explains* wages: news articles, op-eds, budget narratives, academic commentary. Attributed explanation.

Discourse text does not map one-to-one onto contracts, so it is keyed independently (city + date + occupation_class) and joined to contracts only at analysis time. Forcing discourse into the contract schema is the most common way this kind of corpus becomes unusable. Do not do it.

## Capture verbatim — never pre-code

When populating mechanism fields (arbitration clauses, comparability clauses, etc.):

- **DO** capture the exact verbatim text span from the source document into the `*_text` field.
- **DO NOT** judge, paraphrase, or classify what the clause "really means" while populating. Whether a clause is "really" a parity clause is GABRIEL's job, made later, from the raw span. RA discretion at collection time contaminates the measurement the toolkit exists to make objective.

The flags (`*_flag`) record only that *some* relevant clause was found and its text captured — not a judgment about its strength or effect.

## Controlled vocabularies (enforced by validate.py)

`occupation_class` (the analytical spine — exact lowercase strings only):
`police`, `fire`, `teacher`, `sanitation`, `clerical_admin`, `public_works`, `transit`, `parks_rec`, `library`, `nurse_health`, `other`

`safety_flag` is **derived**: 1 if `occupation_class` is `police` or `fire`, else 0. The validator rejects any row where this is inconsistent.

`source_type`: `cba`, `arbitration_award`, `factfinding`, `budget_narrative`, `news`, `pension_report`
`source_corpus`: `causal`, `discourse`
`retrieval_method`: `public_download`, `foia`, `westlaw`, `lexis`, `bloomberg`, `factiva`, `newsbank`, `other`
`text_quality`: `clean`, `ocr_messy`, `partial`

## Provenance is non-negotiable

Every row in every table must have: `source_type`, `source_corpus`, `source_url_or_cite`, `retrieval_date` (ISO YYYY-MM-DD), `retrieval_method`, and `full_text_path` (a pointer into `corpus/`, not pasted full text). Rows missing any of these fail validation.

## Full document text goes in corpus/, not in CSVs

CSVs hold structured fields and short verbatim spans only. Full contracts/awards/articles are stored as files under `corpus/` and referenced by `full_text_path`. Never paste a full document into a cell.

## How to add rows

1. Read `docs/schema.md` for the authoritative field list, types, and required fields before writing any row.
2. Append rows — do not rewrite existing rows or reorder columns.
3. After any change to a CSV, run `python scripts/validate.py` and fix every error before considering the task done.
4. Update `data/city_coverage.csv` whenever you add a contract, so the matched-comparison holes stay visible.

## Coverage discipline

`data/city_coverage.csv` tracks city × occupation_class × cycle = have-it / don't. A city with a safety contract but no matched non-safety contract in the same cycle window is **dead weight for this design** — flag it, don't leave it silent. When asked to assess corpus health, report cities missing comparison units first.

## Definition of done for any data task

- New/changed CSV rows conform to `docs/schema.md`.
- `python scripts/validate.py` exits 0.
- `city_coverage.csv` reflects any new contracts.
- Full-text files are in `corpus/` and correctly pointed to.
- Changes are git-committed with a message describing what was added (which city/occupation/source batch).

## Session logging (PROGRESS.md)

At the end of a working session, offer to append an entry to `PROGRESS.md` (newest on top). Record **decisions, surprises, and next steps** — not keystroke-level changes, which git already captures. Each entry: what we did, decisions made and why, surprises/breakage, a corpus snapshot from `python ingest/audit_coverage.py`, and next steps. Run the coverage audit to fill the snapshot line accurately rather than estimating. Keep entries concise; the log is for reconstructing intent months later, not a transcript.

## Ingestion layer (ingest/)

Documents are turned into rows by the pipeline in `ingest/`, not hand-typed. Read `ingest/README.md` before touching it. Key rules:

- **Two intake paths.** Open public portals go through `ingest/fetchers/` (programmatic). Licensed sources (Westlaw/Lexis/Bloomberg) and FOIA material are NEVER scraped — they enter via `inbox/` + `inbox/manifest.csv` + `python ingest/process_inbox.py`. Do not write scrapers for licensed/authenticated sources; it violates their terms.
- **Verbatim is enforced in code.** Span extraction returns exact source text. The optional LLM fallback is gated by an anti-paraphrase check that discards any span not literally present in the source. Never relax this guard.
- **Provenance gate.** `pipeline.py` quarantines any row missing required metadata to `data/needs_metadata.csv`. Never bypass the quarantine to force a row into `contracts.csv`.
- **Before a real fetch run**, confirm each fetcher's `parse_listing()` selectors against the live page; they raise `NotImplementedError` until you do. Always `--dry-run` first.
- After any ingestion batch, run `python ingest/audit_coverage.py` and report safety units lacking a matched comparison unit first.
- Tests: `python ingest/test_pipeline.py` must stay green after pipeline changes.

## CBA source verification standard

Before a city's contracts are collected, its CBA sources must be "verified." A city is **verified** when all three hold, each recorded in the inventory:
1. **Findable source** — a locatable CBA source (ideally a central index/portal; otherwise union-local sites or a public-records/FOIA route). Record the URL or the route.
2. **Safety contract present** — the police and/or fire CBA is actually obtainable there, in the 2014–2024 window.
3. **Matched non-safety present** — at least one non-safety CBA (teacher/clerical/public-works) from the same city, overlapping the same cycle window.

Record per city in the inventory: `safety_cba_status` (verified_portal / union_site / foia_needed / not_found), the non-safety target unit, the source URL/route, and a note on quirks (e.g. multiple hosting domains, settled-vs-awarded). A city failing (3) — safety but no matched comparison in-window — is flagged dead weight, not collected. Observation window: 2014–2024. Do not download yet; verification only confirms sources exist.
