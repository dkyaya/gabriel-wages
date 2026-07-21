# Worker 3 TX50 Selection Methodology

Date: 2026-07-21

Status: locked offline-preparation input for a future coordinator-controlled serialized live queue. No live scout, API/model call, source opening, verification, ingestion, codification, or national queue/coverage rebuild occurred.

## Result and state choice

Texas remains the third state. The source-of-truth files give no reason to replace it: only three of 1,224 Texas municipalities are scout-covered, while five untouched very large Texas employers are explicit manifest priorities. Texas therefore offers both the strongest remaining manifest block and a large set of high-value municipal employers for the institutional-regime contrast. No alternative state has a clearer source-of-truth advantage that outweighs this combination.

`worker_3_tx50_scout_input_2026-07-21.csv` contains exactly 50 unique Texas municipal/place governments. The ordered batch is: Dallas; Fort Worth; El Paso; Arlington; Corpus Christi; Plano; Lubbock; Laredo; Irving; Garland; Frisco; McKinney; Amarillo; Grand Prairie; Brownsville; Killeen; Denton; Mesquite; Pasadena; McAllen; Waco; Midland; Lewisville; Carrollton; Round Rock; Abilene; Pearland; College Station; Richardson; League City; Odessa; Beaumont; Allen; New Braunfels; Tyler; Sugar Land; Conroe; Edinburg; Wichita Falls; San Angelo; Georgetown; Temple; Bryan; Mission; Baytown; Longview; Pharr; Leander; Flower Mound; and Mansfield.

## Authoritative inputs and strategic connection

The selection uses the task-named authoritative universe, current municipality coverage, candidate queue, next-wave manifest, and county crosswalk, with the serialized recovery relay governing current operating constraints.

The first five rows—Dallas, Fort Worth, El Paso, Arlington, and Corpus Christi—preserve manifest priorities 34–38. The already-covered manifest rows San Antonio, Austin, and Houston are excluded. The other 45 rows extend the same source-planning hypothesis to the largest untouched municipal employers in Texas.

Texas scouting is particularly useful for testing whether safety and ordinary civilian wages travel through different institutional pathways. That is a planning hypothesis, not a legal or empirical finding. If an ordinary non-safety CBA is unavailable, the future scout may identify an authoritative civilian wage-setting pathway, but only for the exact municipality and only as an unverified lead.

## Deterministic selection rule

Rows must be active Census `municipal` / `place` governments, `not_scouted`, have zero failed connection attempts, have no candidate-queue row, have no canonical overlap, and not be any prohibited timeout municipality. Eligible rows are sorted by descending 2023 population and municipality name; the first 50 are locked.

Manifest rows are `manifest_institutional_regime_contrast`; other ranks 6–20 are `large_municipal_employer_anchor`; ranks 21–50 are `high_value_regional_employer`. Population, not unverified web availability, drives the extension, so no source URL needed to be opened or inferred.

## County and employer controls

Texas includes many multi-county cities. Every municipality-county relationship is retained, sorted by county GEOID, and reconciled to the universe relationship count and Census government ID. Dallas and Fort Worth each preserve five county relationships; Corpus Christi preserves four; every other multi-county target likewise retains all relationships rather than a primary-county shortcut.

The exact-employer note excludes counties, schools, transit and port/airport authorities, housing and park authorities, township and special-district governments, regional bodies, universities, and private providers. The future scout must not attribute a contracted or neighboring safety unit to the city.

The builder asserts 50 unique municipality and Census IDs, no overlap with Workers 1 or 2, no current queue/canonical/coverage overlap, no failed-attempt row, and the exact locked order. All rows remain `locked_for_worker_prep_dry_run_only`; dry-run output does not confer discovery coverage.
