# Post-PI Descriptive Analysis Roadmap

Date: 2026-07-23

## What “check if wage gaps exist” means

The first analysis is descriptive: determine whether verified, comparable safety and non-safety bargaining units within the same municipality and time window show different wage-growth percentages, and describe the magnitude and distribution of those differences.

It does not mean estimating a causal effect, asserting that a mechanism caused a gap, or treating unmatched contracts as comparable observations.

## Suggested wage-growth gap definition

For a validated matched municipality/time window:

> **Safety wage-growth gap percentage = safety wage growth percentage − non-safety wage growth percentage.**

The safety side should be police or fire. The comparison side should be a matched ordinary municipal occupation such as clerical/administrative, public works, sanitation, library, parks/recreation, or another defensible non-safety unit. Wage concepts, start/end dates, compounding conventions, bargaining-cycle overlap, and employer identity must be consistent or explicitly harmonized before calculating the difference.

Where both police and fire or multiple non-safety units are available, retain bargaining-unit-level observations and document the comparison rule. Do not collapse units or cycles into one row.

## Why verification and extraction come first

Scout candidates can be duplicates, context pages, expired links, wrong employers, wrong units, partial documents, or sources without usable wage schedules. A percentage gap is defensible only after:

1. exact employer and unit verification;
2. official provenance and document-type review;
3. date and cycle-overlap confirmation;
4. completeness and duplicate review;
5. extraction of comparable wage concepts and endpoints;
6. ingestion with source pointers and structured match identifiers; and
7. validation of the safety/non-safety pairing.

Until these gates pass, the dashboard and reports must say that wage gaps are not yet calculated.

## Mechanism tracking concept

For each analysis-ready matched set, retain verbatim mechanism text and later GABRIEL-derived measures. Descriptively document which mechanisms are correlated with higher or lower wage-growth gaps—for example, comparability language, arbitration or fact-finding features, parity language, retroactivity, pension or staffing provisions, and bargaining-cycle characteristics.

This is correlation documentation, not causal attribution. Report counterexamples, missingness, source quality, and alternative explanations alongside any pattern.

## Dashboard requirement

Once verified/extracted matched wage data exist, add:

- a state/municipality map layer for wage-growth gap percentage;
- filtering by gap percentage ranges;
- clear safety occupation, comparison occupation, time-window, wage-concept, and source-quality filters;
- sample-size and missing-data indicators;
- links from displayed gaps to the validated source/match record; and
- a conspicuous distinction between descriptive gaps and later regression results.

No gap layer should display synthetic zeros for unavailable observations. Missing or incomparable data must remain unavailable.

## Deferred work

Regressions are deferred until the project has broad verified source conversion, consistent extraction, adequate within-municipality safety/non-safety matches, documented measurement choices, and a stable descriptive data product. The first downstream cycle should improve those foundations and determine the efficient next collection strategy.
