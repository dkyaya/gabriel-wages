# Next PI Report and Regression Roadmap

Date: 2026-07-21  
Status: planning; no new source verification, extraction, or regression was performed

## Guiding principle

Do not wait for perfect data, but label early regressions as exploratory/pilot and keep source-stage limitations visible.

Aggressive iteration is useful when it exposes data gaps and tests the design. It becomes misleading when discovery metadata is treated as outcome data, unmatched units are pooled as though comparable, or pilot coefficients are presented as durable findings.

## Proposed next PI report

The next report should be claim-centered rather than a state-by-state mechanism inventory.

1. **Executive summary.** State what the project can currently say about source availability, matched-set prospects, and bounded prior mechanism evidence. Separate those statements from wage findings that remain unavailable.
2. **Research question and design.** Reiterate the within-city, within-bargaining-cycle police/fire/non-safety comparison and the one-row-per-unit-cycle rule.
3. **National source-discovery status.** Present universe, coverage, candidate yield, valid empty outcomes, failures, queue priority, and likely matched-set leads.
4. **Claim readiness.** For each leading claim, show scope, evidence, reasoning, counterevidence, limitations, what would change the team’s mind, and the next source need.
5. **Matched-set pipeline.** Show which municipalities have plausible police/fire/non-safety bundles and which exact verification/extraction steps block analysis.
6. **Early descriptive analyses.** Analyze the discovery process and selection into the candidate queue without interpreting it as a wage mechanism.
7. **Wage-analysis plan.** Define the pilot and full specifications, minimum data requirements, and reporting safeguards.
8. **Next decisions.** Ask the PI to choose among further discovery, coordinated verification, wage extraction, and report-focused evidence consolidation.
9. **Technical appendix.** Include definitions, data vintages, state tables, source-stage audit, failure accounting, and reproducibility commands.

## Dashboard relationship to the report

The dashboard supplies current counts, reproducible state briefs, and an interactive route into queue/readiness status. The report freezes a version of those data and makes an argument. Every report figure should cite the dashboard data vintage or the underlying committed table; no number should silently update after the memo is circulated.

The dashboard can persist between reports and answer “where are we now?” The report answers “what do these data mean, what do they not mean, and what should we do next?”

## Recommended visuals

### Available from current discovery data

1. **US coverage map.** State color is operational discovery readiness, with direct labels for scout coverage and likely matched-set leads. It must not be titled as wage or bargaining strength.
2. **State coverage bar chart.** Covered municipalities and candidate-positive municipalities by active state, with the municipal universe shown separately or as a rate.
3. **National source-discovery funnel.** Universe → scout covered → candidate positive → queued for later verification → likely matched-set leads. Connection failures appear outside the funnel.
4. **Candidate quality matrix.** State by unit type or triage bucket, displaying later-verification priority and hold counts.
5. **City matched-set table.** Initially “likely” scout groups with an unverified badge; later add verified employer/unit/cycle overlap columns.

### Available after verification/codification inputs are integrated

6. **Mechanism heatmap.** City-cycle by occupation and mechanism attribute, using only verified/codified evidence and explicitly marking missing/not searched versus not found.
7. **Claim evidence table.** Claim, support, counterevidence, limitations, and source needs.

### Available after wage extraction

8. **Matched-cycle wage trajectories.** Police, fire, and non-safety wage levels or growth within selected city-cycle sets.
9. **Regression tables and coefficient plots.** Pilot and full specifications with confidence intervals, matched-set counts, and sample sensitivity.

## Early source-discovery analyses available now

These analyses describe the research pipeline, not wage setting:

- candidate yield per parseable municipality by state;
- valid empty and transport-failure rates;
- police/fire/non-safety candidate composition;
- later-verification priority and hold composition;
- likelihood of a scout-labeled triad by state and municipality population band;
- concentration of candidate leads across municipalities/states;
- relationship between municipal population, government type, and candidate yield;
- sensitivity of coverage conclusions to excluding calibration or legacy-wrapper waves; and
- source-discovery throughput and parse rates by backend/run cohort, using run metadata rather than candidate content.

Any analysis of candidate yield must state that public posting practices, search visibility, prompt/model behavior, and parser behavior affect the outcome.

## Exploratory regressions before wage extraction

The following can be run once a tidy municipality/run-level discovery table is built. They study data availability, not wage gaps:

1. **Candidate-positive model.** Binary candidate-positive outcome on log population, state fixed effects where estimable, government geography type, run cohort, and backend. Report average marginal effects descriptively.
2. **Likely matched-set lead model.** Binary scout-labeled triad on population and state/run controls among parseable outcomes. Interpret as verification scheduling, not true matched-set prevalence.
3. **Candidate count model.** Poisson or negative-binomial candidate rows per municipality with an exposure/offset for prompts if runs differ. Check overdispersion and zero inflation.
4. **Failure model.** Connection/timeout outcome on run cohort, state, prompt order, and elapsed-time position to diagnose infrastructure stability.
5. **Priority model.** High-priority queue share by state/unit type, explicitly recognizing that triage rules mechanically determine part of the result.

Use robust uncertainty, display raw denominators, and prefer simple descriptive models when cells are sparse. These models cannot test whether safety wages rise faster.

## Pilot wage regressions

Pilot wage analysis begins only after a partial set of sources is verified, ingested, and extracted into a table that preserves one bargaining unit × one negotiation cycle × one city per row. Minimum fields include municipality ID, unit ID/name, occupation class, safety flag, cycle start/end, wage concept, base/effective dates, provenance, full-text reference, and a matched-set ID.

Recommended pilot sequence:

1. Start with the densest verified city-cycle sets, not all available contracts.
2. Construct transparent wage outcomes: log wage level at common dates, cumulative negotiated increase, annualized increase, and contract duration.
3. Estimate within-city-cycle comparisons with city × cycle fixed effects and occupation indicators. The safety coefficient is identified from occupation variation inside matched sets.
4. Separate police and fire before pooling them as safety; use ordinary municipal civilian units as the primary comparison.
5. Run leave-one-city-out and alternative-cycle-overlap checks.
6. Label all estimates “pilot” and show exact matched-set and observation counts next to every coefficient.

Pilot models should not include scout confidence, candidate priority, or model-generated mechanism labels as though they were verified regressors.

## Full wage-gap regression program

Once the structured panel has enough repeated city-cycle sets:

- estimate wage growth or log wage levels with city × bargaining-cycle fixed effects;
- compare police and fire separately with non-safety occupation classes;
- include unit and repeated-cycle structure where the data support it;
- test whether verified/codified institutional mechanisms mediate or moderate safety/non-safety differences;
- report specifications with and without teachers or safety-adjacent units;
- distinguish base wages from overtime/premium channels;
- cluster uncertainty at the city level when the number of cities is adequate and provide small-cluster alternatives when it is not;
- report balance, attrition, missingness, and selection into verified/extracted samples; and
- freeze input hashes and specification IDs for every published table.

The core estimand must remain interpretable as an occupation difference within the same city and cycle. State-level or national averages that ignore matching are descriptive only.

## Caution language for early results

Suggested report language:

> These estimates are exploratory and use the currently verified subset. They test whether the planned within-city-cycle design is operational; they are not final national effect estimates. Source availability, incomplete cycle matching, and selective extraction may change both magnitude and sign.

For discovery regressions:

> The outcome is public-source discovery, not wages or bargaining power. Associations may reflect posting practices, search visibility, run conditions, and triage rules.

For mechanism analyses:

> Mechanism results use verified verbatim/codified evidence only. Absence from a curated window is not necessarily full-document absence, and mechanism presence does not by itself establish a wage effect.

## Readiness gates

### Gate to a discovery-status PI report

- queue/coverage reconciled after current worker waves;
- dashboard JSON refreshed and validated;
- current/future status language reviewed; and
- claim cards use only existing claim-register evidence.

### Gate to pilot wage analysis

- at least several exact or defensible overlapping city-cycle matched sets;
- verified employer/unit/document identity and wage content;
- extraction schema and provenance validation;
- predeclared outcome construction; and
- explicit sample-selection appendix.

### Gate to full wage-gap claims

- adequate state/city/cycle diversity;
- repeated matched sets and stable extraction;
- sensitivity to comparator definitions and influential cities;
- versioned regressions with appropriate uncertainty; and
- claim register updated with evidence, counterevidence, limitations, and decision rules.

## Recommended next move

Complete the separately planned Stage 1 parallel scout test and one coordinator queue/coverage merge, then refresh the dashboard data. In parallel at the project-planning level—not by opening scout URLs in this task—define the minimum verified wage-extraction table and select a small, coherent matched-city pilot. That keeps national discovery moving while creating the shortest honest path to the first exploratory within-city-cycle wage specification.
