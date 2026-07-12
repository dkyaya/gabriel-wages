# National Corpus Expansion Preflight - 2026-07-12

## Repository State

- Working directory: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
- Git status at preflight: `?? .claude/
?? tmp/`.
- Latest commit at preflight: `3bb9ebf Consolidate claim-centered evidence register`.

## Current Data Counts

- `data/contracts.csv`: 53 rows.
- `data/city_coverage.csv`: 53 rows.
- Contract states: {'MA': 32, 'OH': 13, 'TX': 8}.
- Contract cities: 16 distinct city-state pairs.
- Occupation classes: {'fire': 13, 'clerical_admin': 3, 'public_works': 7, 'police': 17, 'other': 8, 'teacher': 1, 'library': 3, 'nurse_health': 1}.
- Safety split: {'safety': 30, 'non_safety': 23}.
- Source types: {'cba': 49, 'arbitration_award': 4}.
- Text quality: {'ocr_messy': 12, 'clean': 39, 'partial': 2}.

## Current Evidence-Layer Counts

- `docs/analysis/gabriel_codify_evidence_layer.csv`: 781 rows.
- Evidence status: {'not_found': 488, 'present': 293}.
- Viewer verification: {'0': 497, '1': 284}.
- Verified-present rows available for claim support: 284.
- Evidence-layer states: {'MA': 338, 'OH': 270, 'TX': 173}.
- Evidence-layer cities: {'Houston': 65, 'Austin': 67, 'Columbus': 66, 'Cleveland': 67, 'Somerville': 22, 'Wayland': 40, 'Franklin': 110, 'Boston': 22, 'Georgetown': 41, 'Seekonk': 103, 'San Antonio': 41, 'Cincinnati': 76, 'Toledo': 61}.
- Codified sources in report source inventory: 37.

## Current States and Cities Covered

- States: MA, OH, TX.
- Cities: Arlington, MA, Boston, MA, Franklin, MA, Georgetown, MA, Newton, MA, Seekonk, MA, Somerville, MA, Wayland, MA, Worcester, MA, Cincinnati, OH, Cleveland, OH, Columbus, OH, Toledo, OH, Austin, TX, Houston, TX, San Antonio, TX.

## Current Claim-Register Summary

- `CLM-2026-07-12-01` (Ohio matched triads) - supported_provisional, moderate, report_ready=yes: In the currently coded Ohio matched triads, safety rows more often show formal impasse or interest-arbitration backstop language, while matched non-safety rows are better evidenced through classification, wage-grade, or grievance-administration channels.
- `CLM-2026-07-12-02` (Texas institutional unevenness) - supported_provisional, moderate, report_ready=yes: Texas evidence is consistent with institutionally uneven safety wage-setting, but the current Texas comparison is not a clean statewide safety-versus-non-safety design outside Houston.
- `CLM-2026-07-12-03` (Massachusetts cross-occupation base) - supported_provisional, moderate, report_ready=maybe: Massachusetts is the current corpus’s densest cross-occupation comparison base, supporting bounded safety/non-safety mechanism comparison in Franklin and Seekonk while still falling short of a uniform state grid.
- `CLM-2026-07-12-04` (Safety pressure conversion channels) - supported_provisional, moderate, report_ready=maybe: The strongest current safety mechanism pattern is not generic occupational hardship alone, but occupational pressure paired with channels that convert pressure into compensation language: overtime, callback, premium pay, minimum staffing, and formal impasse backstops.
- `CLM-2026-07-12-05` (Non-safety classification/admin channel) - supported_provisional, moderate, report_ready=maybe: In the currently coded non-safety evidence, the clearest wage-setting channel is classification, grade, step, or administrative adjustment language rather than safety-specific hazard or minimum-staffing language.
- `CLM-2026-07-12-06` (Arbitration distinction) - supported_provisional, strong, report_ready=yes: The current evidence supports a report-ready methodological distinction between interest/formal impasse arbitration and grievance or contract-interpretation arbitration; the San Antonio police contract is the clearest within-document test.
- `CLM-2026-07-12-07` (Comparator wage evidence gap) - needs_more_evidence, low, report_ready=no: Peer/comparator wage evidence should currently be stated only as a narrow and underdeveloped claim: codify verifies one Somerville comparator-style row, while San Antonio shows a documented false negative.
- `CLM-2026-07-12-08` (Texas non-safety outside Houston gap) - needs_more_evidence, low, report_ready=no: A substantive Texas non-safety comparison outside Houston is not report-ready: the current evidence has one genuine Houston non-safety source, one Austin safety-adjacent EMS source, and no San Antonio non-safety comparator.

## Why the Next Two Weeks Should Prioritize Expansion, Not Report Writing

The current claim register is useful but still narrow. It rests on three states, 37 codified sources, and a small number of high-value institutional contrasts. The strongest claims are bounded to Ohio, Texas, or a methods distinction; the weakest claims need new source types, especially comparator, factfinding, and non-safety material. A new report now would mostly restate the July mechanism report and the July 12 claim consolidation. The higher-return work is national source expansion that deliberately tests the eight leading hypotheses, especially whether Ohio-style matched triads and Texas-style institutional unevenness travel to other states.

## Explicit Run Constraints

- No git push.
- No remote inspection, validation, creation, or configuration.
- No GABRIEL/codify calls, model calls, API calls, or Harvard Proxy calls.
- No new source collection, downloads, source ingestion, FOIA, or PRR in this planning run.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, `docs/schema.md`, or final report DOCX/PDF artifacts.
- No new report draft prepared in this planning run.
