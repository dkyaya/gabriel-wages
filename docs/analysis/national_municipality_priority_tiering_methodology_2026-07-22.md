# National Municipality Priority Tiering Methodology

Date: 2026-07-22

Version: `national_priority_v1_2026-07-22`

## Purpose and interpretation

The score ranks municipality-employer rows for future source-discovery scouting under the Gabriel Wages matched safety/non-safety research design. It is deterministic, local, and interpretable. It does **not** assert that a municipality has a union, police/fire department, ordinary civilian bargaining unit, online agreement, wage gap, or causal mechanism.

Every authoritative municipality receives an underlying score and tier. Current operational status is separate: successfully scout-covered and already-canonical municipalities remain scored but are excluded from the future scout queue; failure-only municipalities retain their underlying tier and enter a separate retry category.

## Baseline 0–100 score

| Component | Maximum | Rule |
|---|---:|---|
| Population / employer scale | 30 | 40% national population midrank percentile plus 60% `log1p(population)` normalized to the observed national maximum |
| Government type | 10 | Municipal/place = 10; township/county subdivision = 4 |
| Smoothed state source yield | 20 | 60% candidate-positive rate, 25% candidate rows per covered municipality capped at three, 15% transport reliability |
| Smoothed research-design signal | 20 | 30% any police/fire candidate rate, 30% non-safety candidate rate, 40% likely-triad rate among successfully scouted municipalities |
| Geographic / strategic value | 10 | 40% state sample-depth gap, 20% state unscouted share, 30% mean associated-county coverage gap, 10% multi-county value |
| Data completeness | 5 | Population 3, county context 1.5, valid government/geography pair 0.5 |
| Existing municipality evidence | 5 | Descriptive only: candidate-positive rows, candidate volume, likely-triad label, and later-verification share; failure-only receives one point; unscouted and parseable-empty rows receive zero |
| Retry adjustment | 0 | Failure does not lower the underlying score; retry is represented separately |

Component scores are rounded for output, while the total is calculated from unrounded components and rounded to three decimals. The minimum and maximum need not equal 0 and 100 in a particular national vintage; the scale is bounded to that range.

## Population

The population norm is:

```text
0.40 × national midrank percentile
+ 0.60 × log1p(population) / log1p(max observed population)
```

This rewards employer scale without letting a few very large cities determine the entire score. Equal population values receive the same percentile. A missing value remains missing, earns no population points, and reduces confidence; zero is retained as an observed zero.

## State-yield smoothing

State evidence is empirically Bayes-smoothed with a 25-successful-municipality national prior. For a rate:

```text
smoothed rate = (state successes + 25 × national pooled rate)
                / (state successful scouts + 25)
```

Candidate rows per covered municipality use the same 25-municipality prior with the pooled national row mean. Failure reliability uses failure-only municipalities divided by successful plus failure-only municipalities, also smoothed to the pooled failure rate.

The normalized state-yield component is:

```text
0.60 × smoothed candidate-positive rate
+ 0.25 × min(smoothed candidate rows per covered / 3, 1)
+ 0.15 × (1 − smoothed failure rate)
```

Thus an unscouted state receives a neutral pooled estimate with low confidence, not zero and not an extreme guess. States with small samples move only gradually away from the prior.

## Research-design relevance

Only explicit existing scout labels are used at the state level. Municipality-level safety/non-safety evidence is never imputed to an unscouted employer. Each state rate uses the same 25-municipality prior:

```text
0.30 × smoothed share with any police or fire candidate
+ 0.30 × smoothed share with a non-safety candidate
+ 0.40 × smoothed likely-triad share
```

The likely-triad label means only that current unverified scout rows include police, fire, and non-safety unit labels. It is a scheduling proxy, not verified same-employer, same-cycle, signed agreement evidence.

## Geographic value

The geographic norm combines:

- state sample-depth gap: `1 − min(successfully covered / 100, 1)`;
- state unscouted share;
- mean coverage gap across every associated county; and
- a small multi-county indicator.

This rewards learning and geographic diversity while limiting geography to ten points. It cannot outrank employer scale and the two evidence components by itself. County metrics count associations, and the municipality-level mean prevents multi-county rows from being counted as multiple employers.

## Existing evidence and stage separation

Existing evidence contributes at most five points and is applicable only where an actual scout attempt produced municipality-level evidence. It is intentionally descriptive:

- candidate-positive: base signal plus bounded candidate volume, triad, and later-verification share;
- failure-only: one point to reflect an attempted high-value row without treating it as covered;
- parseable empty: zero municipality-evidence points;
- unscouted: zero; no municipality-specific evidence is imputed.

This can help evaluate whether high-scoring covered municipalities actually yielded candidates. It cannot make a covered municipality eligible for another ordinary scout wave.

## Confidence

- **High:** population, government type, and county context are complete, and the state has at least 50 successful scout outcomes.
- **Medium:** those fields are complete, and the state has 15–49 successful outcomes.
- **Low:** the state has fewer than 15 successful outcomes, or any municipality population/type/county input is missing.

Current high confidence therefore reflects input completeness and state sample depth—not verified source quality or substantive certainty.

## Tier assignment

Tiers use national score rank with stable tie-breaking by score descending, population descending, and municipality ID. This hybrid rank safeguard prevents an operationally unusable oversized top tier while retaining the continuous 0–100 score:

- Tier 1: top 5% — 1,780 rows in the current universe;
- Tier 2: next 10% — 3,559 rows;
- Tier 3: next 20% — 7,118 rows;
- Tier 4: next 30% — 10,676 rows;
- Tier 5: remaining 35% — 12,456 rows.

Covered municipalities participate in the underlying national rank but are removed from future eligibility. Consequently the current future-eligible Tier 1 pool is smaller than 1,780 and remains within the target operational range.

## Operational eligibility and retries

`future_scout_eligible_flag=no` when a row is successfully scout-covered or already canonical. Duplicate IDs fail the build rather than receiving a tier. Prohibited employer/geography categories also fail the build; none exist in the current authoritative universe.

Failure-only municipalities remain eligible with `retry_flag=yes`:

- Tier 1–2: high retry priority in a separately authorized retry wave;
- Tier 3: medium, after the next 300–600 new scouts;
- Tier 4–5: low/deferred unless state coverage or selection-bias needs justify retry.

No hardcoded municipality-name exception controls retry status; current exact failure accounting does.

## Sensitivity settings

The primary score remains unchanged. Two alternative rankings test concentration:

- population-heavy: population 40, state yield 15, research design 15;
- state-yield-heavy: population 25, state yield 30, research design 20, geography 5.

Government type remains 10, completeness 5, and existing evidence 5. Top-500 overlap, rank changes, and state composition are reported. The tiers should be rebuilt after every 300–600 additional successful municipality scouts because the state evidence base is currently concentrated in seven states.
