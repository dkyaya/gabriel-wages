# National Municipal Labor Evidence Dashboard Architecture Plan

Date: 2026-07-21  
Status: first architecture scaffold; source-discovery data only

## Purpose

The dashboard should give the PI and research team a fast, honest view of where the national municipal labor evidence project stands: which municipal governments are in scope, where source discovery has run successfully, which municipalities produced leads, how the later-verification queue is distributed, where likely police/fire/non-safety sets may exist, and which analytical steps are still blocked.

It complements formal PI reports rather than replacing them. A report should still make a bounded argument in prose, connect a claim to evidence and counterevidence, explain research-design choices, and state what would change the conclusion. The dashboard is the persistent status and exploration layer behind those reports. It is useful for selecting states, diagnosing source gaps, and producing standardized state appendices; it is not itself a final empirical paper or a substitute for judgment.

## Audience and default reading level

The primary audience is the PI and research team. The default view should therefore answer substantive questions without exposing file paths, run IDs, parser terminology, or build details. Technical provenance and field definitions remain available in expandable sections and the data documentation.

The first screen should answer five questions:

1. How much of the national municipal universe has been scouted?
2. Which states have candidate-positive and likely matched-set leads?
3. How large and how urgent is the later-verification queue?
4. Which claims have structured prior context, and what evidence stages remain missing?
5. Is the project ready for source-discovery analysis, pilot wage analysis, or full wage-gap analysis?

## Recommended stack

- React with Vite for a small static application.
- Static JSON generated locally from committed repository CSVs.
- Leaflet with a committed, simplified public-domain state GeoJSON for the eventual choropleth. The map should not require a basemap or token. The first scaffold does not download a boundary file; adding one requires a documented provenance review.
- CSS print styles and a hash-based state route such as `#/state/CA`, which works on GitHub Pages without server-side route rewriting.
- No backend, database, authentication layer, or secret API key.

Mapbox is not justified. A token-free state-boundary choropleth is enough for this project, avoids credential management, prints cleanly, and keeps the site reproducible. MapLibre would also be acceptable if the map later needs richer vector interactions, but Leaflet is the smaller MVP dependency.

## Static deployment strategy

The dashboard lives under `docs/dashboard/`. Vite builds a static `dist/` directory with relative asset paths (`base: "./"`). A later, separately authorized GitHub Pages workflow can build and publish that directory. This task creates no deployment workflow, inspects no remote, and performs no publication.

The site should bundle the generated JSON at build time. GitHub Pages then serves immutable HTML, JavaScript, CSS, and JSON assets; there is no runtime connection to the research repository, a model service, or a private data source.

## Data flow

```text
Committed analysis CSVs
  national municipality universe
  national municipality/state coverage
  national candidate queue
  optional claim / state-city / hypothesis tables
                |
                v
scripts/build_dashboard_data.py
  validates row identities and status boundaries
  aggregates only display-safe counts
  writes warnings and null placeholders
                |
                v
docs/dashboard/data/*.json
                |
                v
React/Vite static dashboard -> GitHub Pages build
```

The builder is intentionally one-way and non-destructive. It never writes to the source CSVs, canonical contracts, city coverage, or corpus. It does not open candidate URLs or decide whether a source is valid.

## Update procedure

After a coordinator has imported completed scout batches and rebuilt national queue/coverage once:

1. Confirm the queue and municipality/state coverage builders completed and their validation passed.
2. Run `python scripts/build_dashboard_data.py`.
3. Review the builder summary, warnings, source-file metadata, and the four JSON diffs.
4. Confirm the identity `candidate-positive + parseable-empty = scout-covered` and that connection-only failures remain outside coverage.
5. Review the dashboard locally after dependencies have been installed in a separately authorized frontend task.
6. Commit queue/coverage and dashboard JSON in the same coordinator update, or in a clearly linked dashboard-refresh commit.

Missing optional claim or extraction files must not stop the build. The builder writes empty arrays or null values and emits warnings. Missing required queue/coverage/universe inputs is a hard error because a partial build would be misleading.

## Page and component model

### National map

The map colors states by an operational `evidence_readiness_score`. This score summarizes discovery workflow readiness only: coverage presence, candidate-positive share, high-priority lead volume, likely matched-set lead volume, and prior claim-registry context. It is not evidence strength, a wage result, or a state ranking on substantive outcomes.

The map tooltip should show state name, universe, scout-covered count/rate, candidate-positive count, high-priority leads, likely matched-set leads, and a stage caveat. States with no discovery coverage remain visibly distinct from states with parseable empty results.

### State detail panel

Selecting a state opens a right-side panel with headline cards, a short plain-English narrative, queue composition, failure accounting, likely matched-set leads, and prior claim IDs where available. Status chips must use distinct labels for `Scout`, `Calibration context`, `Verification`, `Ingestion`, `Codified evidence`, and `Analysis`.

### Printable state report

Each state has a hash route (`#/state/CA`) and a print action. Print CSS removes navigation and interactive controls, expands the state narrative and limitations, uses a white background, preserves table headers, and avoids splitting cards across pages. The printable page is a standardized evidence-status appendix, not a final PI memo.

### Candidate queue explorer

The MVP shows aggregate state, unit-type, confidence, and triage-bucket counts. A later municipality-level JSON can support filtering by state, municipality, unit type, owner type, cycle evidence, wrong-employer risk, blocked/unreadable status, and duplicate risk. Raw source URLs should remain hidden by default and should never imply verification.

### Coverage funnel

The current funnel is:

1. municipal universe;
2. parseable scout-covered municipalities;
3. candidate-positive municipalities;
4. municipalities queued for later verification; and
5. likely matched-set lead groups.

Future stages—project-wide verified sources, ingested contracts, wage observations, codified evidence, and claim-ready matched sets—remain null until dedicated inputs exist. Connection attempts appear alongside the funnel, not inside it.

### Claim/evidence panel

Claim cards should follow the project’s claim-centered reporting structure:

- claim text and scope;
- status and evidence-strength label from the claim register;
- supporting evidence and reasoning;
- counterevidence;
- key limitations;
- what would change the team’s mind; and
- additional source needs.

National scout candidates may appear only under “source needs / unverified leads.” They cannot appear as supporting evidence before verification and ingestion/codification where required.

### Analysis-readiness panel

This panel shows which inputs exist and which analyses they support. It should explicitly separate source-discovery summaries from structured wage analysis. A disabled regression area is preferable to an empty chart that could be mistaken for a null result.

### Later regression-results panel

This component remains unavailable in the MVP. When a validated wage table exists, it should show sample definition, outcome, unit of observation, fixed effects, standard-error choice, coefficient/interval, matched-set coverage, exclusions, and versioned specification notes. Results must link back to an immutable model table or artifact, not be calculated ad hoc in the browser.

## Current and future metrics

| Metric | Available now | Interpretation |
| --- | ---: | --- |
| Municipality universe count | Yes | Authoritative Census municipal/township-government universe used by the project |
| Scout-covered municipalities | Yes | Parseable candidate or valid empty model output; not verification |
| Candidate-positive municipalities | Yes | At least one parsed scout lead |
| No-candidate municipalities | Yes | Parseable empty list; not proof of absence |
| Failed scout municipalities/attempts | Yes | Infrastructure outcomes excluded from coverage |
| Candidate queue rows | Yes | Unverified source leads and calibration overlays |
| High/medium/low later-verification rows | Yes | Scheduling priority, not source quality proof |
| Likely matched-set groups | Yes | Unit-label scheduling lead, not verified cycle match |
| State evidence-readiness score | Yes | Operational discovery triage score only |
| Project-wide verified source count | No | Future dedicated verification input |
| Later-ingest candidate count | Not project-wide | Future dedicated, reconciled ingestion decision input |
| Extracted wage observations | No | Future validated wage table |
| Police/fire/non-safety wage gaps | No | Future matched-cycle analysis |
| Regression estimates | No | Future versioned analysis output |
| Confidence levels for claims | Not from national scouting | Future evidence synthesis, never inferred from candidate volume |

## Status semantics and visual safeguards

The UI must never collapse these stages:

| Stage | Meaning | Allowed display language |
| --- | --- | --- |
| Scout | A model returned parseable discovery metadata | “Unverified lead” |
| Calibration | A bounded prior review checked selected rows | “Calibration context”; not project-wide verification |
| Verification | Employer, unit, dates, completeness, access, wage content, and match are checked | “Verified source” only from a dedicated ledger |
| Ingestion | Source passed provenance gates and entered canonical processing | “Ingested” only from canonical pipeline output |
| Codified | Verbatim source text was measured/coded | “Codified evidence” |
| Claim | Evidence and counterevidence support a bounded statement | Claim status from the claim register |

Colors should reinforce this: scout is blue, calibration is amber, verified is green, future/unavailable is gray, and failures are red. Green must not be used for unverified candidate volume.

## What the dashboard must not show yet

The MVP must not show a national public-safety wage premium, city wage-gap ranking, causal mechanism coefficient, claim confidence interval, or “best/worst” state interpretation. The repository does not yet provide a dashboard-ready, verified, extracted wage panel that could sustain those results. Candidate counts describe the discovery process and public-source landscape; they are not wage observations and must not be treated as outcome data.

## MVP boundary and next frontend milestone

This task delivers the builder, four static datasets, documentation, and an uninstalled React/Vite draft. The next frontend milestone should add a provenance-documented simplified state GeoJSON, implement the Leaflet choropleth, add automated JSON-schema checks, render-test the print route, and establish a GitHub Pages build only after the deployment path is separately authorized.
