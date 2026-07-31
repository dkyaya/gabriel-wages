# Position and Schedule-Location Matching Method

## Objective

The project compares occupations within a municipality and cycle; it does not assume that police, fire, clerical, public-works, code-enforcement, or administrative jobs perform identical work. A valid comparison aligns the location of each position in its own pay structure so the measured contrast is not mechanically produced by comparing an entry rate with a maximum, a line worker with a chief, or an actual rate with an authorized ceiling.

## Required matching fields

1. Municipality and state.
2. Effective start/end dates, contract year, fiscal year, or a documented overlapping cycle.
3. Pay basis: hourly, annual, or a document-supported conversion.
4. Base/non-base status and non-base component type.
5. Occupation class and safety category.
6. Position or role family.
7. Rank, step, grade, payband, or schedule-location label.
8. Full-time/part-time or other work-status field.
9. Actual rate, schedule rate, range minimum, range maximum, or authorized ceiling.
10. Bargaining-unit status and source type.

## Comparison strata

- **Entry-to-entry:** first scheduled police/fire rate versus the first scheduled non-safety rate.
- **Matched step/tenure:** like-numbered step, grade, or documented years-of-service location.
- **Maximum-to-maximum:** top scheduled or legally authorized rates, kept separate from actual pay.
- **Line-position base rates:** patrol officer/firefighter versus non-safety frontline roles, excluding chiefs and department heads.
- **Command/managerial strata:** chief, captain, director, superintendent, and comparable non-safety management roles.
- **Part-time strata:** part-time safety versus part-time non-safety positions.
- **Non-base component strata:** longevity-to-longevity, shift-to-shift, certification-to-certification, or otherwise explicitly like-for-like components.

## Status rules

- `position_schedule_comparable`: all required fields are explicit and candidate-level source validation passes.
- `near_comparable_specific_blocker`: values and cycle align, but a named field—usually schedule location, actual-versus-maximum status, FTE status, rank, or bargaining status—is missing.
- `mechanism_context_only`: the records illuminate wage-setting or direction but cannot support a value contrast.
- `exclude_misclassified_or_noncomparable`: exact span contradicts the safety/occupation label or mixes unlike values.

## Current application

The upstream pair layer contains 27 records that pass coded pay-basis, period, unit/rank/step, and base/non-base flags. Exact-span review demonstrates that these flags are necessary but insufficient: records labeled safety can contain code-enforcement, construction, zoning, elected-official, legal-services, or administrative values. Candidate-level validation is therefore the final promotion gate.

Shreve currently passes as a part-time-to-part-time hourly base-rate comparison. Cammack Village is maximum-to-maximum but needs enactment and actual-pay confirmation. Canastota is entry-to-unlabeled-position and remains conditional. Alburtis is command-to-administrative and outside-versus-inside bargaining status, so it is limits-only.

This method allows the project to make stronger comparisons by defining the estimand precisely. It does not require declaring unlike jobs identical; it requires holding city and cycle fixed while ensuring that schedule location, pay concept, and employment status are not the source of a spurious difference.
