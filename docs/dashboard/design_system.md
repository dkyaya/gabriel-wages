# Dashboard Design System

## Design direction

The dashboard should feel like a restrained research brief: warm paper background, dark green headings, white content cards, compact typography, and generous whitespace. It should be credible in a PI meeting and clean when printed. Avoid startup-style gradients, decorative animations, and dashboard chrome that competes with the research status.

## Color semantics

| Role | Color direction | Meaning |
| --- | --- | --- |
| Primary | dark evergreen | headings, navigation, selected state |
| Scout | blue | source-discovery output only |
| Calibration | amber | bounded prior calibration context |
| Verified | green | dedicated verified-source input only |
| Future/unavailable | neutral gray | absent pipeline stages |
| Failure | muted red | connection/parse failure accounting |
| Warning | amber border | interpretation caveat |

Never use verified green for candidate-positive counts or readiness scores.

## Typography

- Georgia/system serif for page and section headings.
- System sans-serif for data, controls, table text, and notes.
- Short uppercase eyebrow labels orient the reader without adding technical jargon.
- Minimum body size 15–16 px on screen and 10.5–11 pt in print.

## Layout

- Four national headline cards on wide screens, collapsing to two and one.
- National map on the left and sticky/adjacent state panel on the right.
- Two-column analysis sections below the map.
- Maximum page width around 1,480 px.
- No horizontal scrolling except dense tables in narrow viewports.

## Cards and hierarchy

Each card has one question, one primary answer, and one interpretation line. Cards should not expose run IDs, source paths, or parser fields in their default state. Technical details belong in expandable sections.

## Maps and charts

- Use a token-free Leaflet state choropleth with committed geometry.
- Use operational readiness or scout coverage for color; never wage outcomes until those exist.
- Include a table/text equivalent.
- Use direct labels and restrained legends.
- Avoid pie charts and three-dimensional effects.

## Status language

Approved labels:

- `Scout — unverified lead`
- `Scout — parseable empty`
- `Scout attempt — failed`
- `Calibration context`
- `Verification pending`
- `Verified source`
- `Ingestion pending`
- `Ingested`
- `Codified evidence`
- `Analysis unavailable`
- `Exploratory result`
- `Pilot result`

Do not use “complete,” “proven,” “confirmed,” or “claim-ready” for scout output.

## Print behavior

The print view removes navigation, map controls, and queue explorer interactions. It keeps the state title, date/vintage, four headline metrics, narrative, queue/failure details, claim context, and limitations. Cards and table rows should avoid page breaks. Printed state reports should fit a short appendix format rather than reproducing the entire dashboard.

## Accessibility

- Preserve keyboard focus and visible focus rings.
- Do not encode status by color alone; every color has a text label.
- Maintain high contrast on state cells and status pills.
- Give maps an accessible table/grid fallback.
- Use semantic headings, lists, definition lists, and table headers.
- Respect reduced-motion preferences; the MVP uses no essential motion.
