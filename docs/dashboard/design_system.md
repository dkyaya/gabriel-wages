# Dashboard Design System

## Product direction

The dashboard should read like a concise research brief: restrained, legible, and honest about evidence stage. The main view is for a PI meeting, so it leads with substantive status questions and hides file paths, schema details, and build metadata inside expandable sections.

The visual system uses a warm paper background, dark evergreen headings, off-white cards, compact blue data marks, and generous whitespace. Avoid gradients, ornamental motion, dense application chrome, and dashboard conventions that make operational metrics look like empirical findings.

## Information hierarchy

The main view should answer, in order:

1. How much of the national universe has a parseable scout outcome?
2. Where are candidate and likely matched-set leads concentrated?
3. How large is the later-verification workload?
4. Which evidence stages are available, prior-context-only, or unavailable?
5. What limitations prevent wage or causal interpretation?

The state report is a pipeline-status appendix, not a substitute for a claim-centered PI memorandum.

## Color semantics

| Role | CSS direction | Meaning |
| --- | --- | --- |
| Primary | dark evergreen | headings, report rules, primary actions |
| Scout | blue | source-discovery output only |
| Calibration | amber | bounded prior calibration context |
| Verified | green | reserved for a dedicated verified-source input |
| Ingested | teal outline | reserved for canonical provenance-passed input |
| Future/unavailable | neutral gray | absent validated dashboard stage |
| Failure | muted red | connection or parse-failure accounting |
| Warning | amber rule | interpretation and stage-boundary caveat |

The choropleth uses a sequential **blue** scale. Green must not encode candidate volume, scout coverage, queue priority, or operational readiness because green is reserved for verified evidence. Wage outcomes have no color scale in the MVP.

## Typography

- Georgia or the system serif stack for page and section headings.
- System sans-serif for controls, data, tables, notes, and body copy.
- Short uppercase eyebrow labels for orientation.
- Tabular data should be large enough to scan without dominating interpretation notes.
- Minimum screen body size is roughly 15–16 px; print body is 10.5 pt.

## Layout

- Four national headline cards on wide screens, collapsing to two and one.
- National tile map on the left and a sticky selected-state panel on the right.
- Two-column funnel and queue sections below the map.
- Full-width readiness and limitation panels.
- Maximum main width of approximately 1,480 px.
- Horizontal scrolling is limited to the tile map and dense tables on narrow screens.

## Component behavior

### NationalMap

- Defaults to scout coverage rate.
- Supports only the five safe fields documented in the README.
- Uses a token-free US tile-grid until reviewed GeoJSON exists.
- Shows the selected state with an amber focus/selection outline.
- Provides exact labels, tooltips, keyboard buttons, and an expandable table equivalent.
- States that positions are schematic and scale is relative to the current maximum.

### StateDetailPanel

- Shows universe, scout count/rate, candidate-positive count, queue composition, likely sets, empty outcomes, and failures.
- Always shows verification and ingestion status independently of scout status.
- Links to the dedicated report route rather than printing the whole dashboard.

### CoverageFunnel

- Uses a stepped layout rather than a conventional proportional bar because national coverage is currently a very small share of the universe.
- Prints exact values and percentages so the decorative step widths cannot be mistaken for quantitative scale.
- Keeps failures outside the funnel and future stages under an expandable section.

### CandidateQueueCards

- Uses high/medium/low only as later-verification scheduling language.
- Keeps hold/rejected visible.
- Labels unit counts as scout metadata, not confirmed bargaining units.

### AnalysisReadinessPanel

- Shows discovery as current, prior codified context as bounded context only, and later stages as not integrated.
- Includes an explicit unavailable wage-gap panel with the promotion gate.
- Never renders an absent count as zero.

### PrintableStateReport

- Derives entirely from the same `state_summary.json` state object and candidate-state aggregate used by the dashboard.
- Includes every required coverage, candidate, priority, likely-set, failure, and limitation field.
- Uses the phrases “not yet verified” and “not yet ingested.”
- Removes controls in print, preserves table headers, and avoids splitting major blocks.

## Status vocabulary

Approved labels:

- `Scout stage`
- `Scout coverage recorded`
- `Scout — parseable empty`
- `Scout attempt — failed`
- `Calibration context`
- `Not yet verified`
- `Verified source`
- `Not yet ingested`
- `Ingested`
- `Codified evidence`
- `Analysis unavailable`
- `Exploratory result`
- `Pilot result`

Do not use “complete,” “proven,” “confirmed,” “best,” “worst,” or “claim-ready” for scout output.

## Maps and quantitative displays

- Every map/chart needs an exact text or table alternative.
- Map colors must use current operational fields, never inferred outcomes.
- A relative color scale must say that it is relative; exact labels remain primary.
- Do not use pie charts, 3D effects, or unlabeled area encodings.
- `null` renders as “Not yet available,” never zero.

## Technical disclosure

Main cards should not expose run IDs, parser terminology, file paths, or source URLs. Place schema version, generated timestamp, source paths, builder warnings, metric formula, and queue definitions in `<details>` elements.

## Accessibility

- Preserve semantic headings and landmarks.
- Use real buttons for state selection and table actions.
- Maintain visible keyboard focus and `aria-pressed` on state tiles.
- Do not encode status by color alone; pair every status with text.
- Keep a table equivalent for the map.
- Maintain high contrast across all blue map bands and status pills.
- Respect reduced-motion preferences.

## Print behavior

The dedicated `#/state/<CODE>/report` view is optimized for letter-size portrait output. Print CSS:

- removes navigation/actions;
- uses a white background and black/gray text;
- keeps state title, data vintage, status labels, headline metrics, narrative, queue table, coverage accounting, evidence stages, and limitations;
- repeats table headers where supported;
- avoids splitting key blocks and rows; and
- reserves the footer for the non-empirical status caveat.

The report should remain short enough to serve as a standardized state appendix rather than reproducing the national dashboard.
