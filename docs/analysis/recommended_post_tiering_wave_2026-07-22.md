# Recommended Post-Tiering Scout Wave

Date: 2026-07-22

Disposition: **recommend three cross-state 50-row offline-preparation batches drawn from Tier 1; do not create or run them in this task.**

## Why cross-state

The baseline top 500 spans 48 states/DC, and the leading unscouted municipalities are large employers in states with little or no current scout evidence. A cross-state design simultaneously targets high expected research value and learns whether the national-prior yield assumptions hold outside CA/IL/NJ/NY/PA/TX/MA. Three more state-specific batches would provide less information about selection and geographic generalization.

Failure-only rows must be excluded from these ordinary discovery batches and held for their separate retry protocol. Construct the future 150-row input by taking the first 150 `retry_flag=no` rows from `national_priority_tier_top_targets_2026-07-22.csv`, preserving rank order and exact IDs. This corresponds to global ranks 1–156 because six high-priority CA failures occur within that span.

## Proposed Worker 1 — national priority ranks 1–51 after excluding retries

- Rows: first 50 new-discovery targets
- States represented: 31
- Source-rank range: 1–51
- Top ten: Oklahoma City OK; Phoenix AZ; Portland OR; Milwaukee WI; Atlanta GA; Kansas City MO; Raleigh NC; Honolulu HI; Jacksonville FL; Tulsa OK
- Rationale: largest remaining municipal employers with exceptional geographic breadth; all are Tier 1, but most have low state-score confidence and therefore create high learning value.

## Proposed Worker 2 — next 50 eligible new-discovery targets

- Rows: new-discovery positions 51–100
- States represented: 29
- Source-rank range: 52–105
- Top ten: Dayton OH; St. Paul MN; Greensboro NC; Lincoln NE; Anchorage AK; North Las Vegas NV; St. Louis MO; Springfield MA; Madison WI; Chandler AZ
- Rationale: continues the largest-employer pool while introducing Massachusetts and additional medium/large cities across regions.

## Proposed Worker 3 — next 50 eligible new-discovery targets

- Rows: new-discovery positions 101–150
- States represented: 20
- Source-rank range: 106–156
- Top ten: Springdale AR; Providence RI; Tempe AZ; Akron OH; Sioux City IA; Chattanooga TN; Brockton MA; Warner Robins GA; Cambridge MA; Fort Lauderdale FL
- Rationale: completes a nationally diverse 150-row learning wave and increases Massachusetts, Florida, Arizona, Connecticut, and upper-Midwest representation without admitting township governments or failure retries.

The final future batches must be regenerated from the committed tier CSV, exact-audited against current coverage/canonical status immediately before preparation, and assigned a new queue ID. Do not use these prose lists as locked inputs.

## State lenses

The largest current Tier 1 eligible pools are Florida 121, California 110, Ohio 93, Georgia 65, Minnesota 63, Washington 59, North Carolina 57, Michigan 55, Pennsylvania 54, and Massachusetts 50.

Those counts have different evidentiary meanings:

- California has high state-score confidence and the strongest smoothed yield, but its largest municipalities are already covered and the remaining pool is smaller-employer expansion.
- Pennsylvania has medium confidence and strong observed yield; it is a good state-specific fallback after national learning.
- Florida, Ohio, Georgia, Minnesota, Washington, North Carolina, and Michigan have large high-value pools but low state-score confidence because no successful state sample currently exists.
- Massachusetts has only eight successful outcomes, so its strong observed yield remains prior-shrunk and low confidence.

## Expected yield and risks

The pooled current result is 391 candidate-positive municipalities out of 504 successful scouts (77.6%) and 2.002 candidate rows per covered municipality. The next cross-state wave consists of unusually large municipalities but mostly low-confidence states. Use a broad planning range of 90–120 candidate-positive municipalities and 200–330 URL-bearing candidate rows, not a point guarantee.

Risks include consolidated governments, contracted public-safety services, special-district substitutions, state-specific non-bargaining systems, and large-city portals that return many context-only or duplicate rows. Exact employer/unit/source controls remain mandatory. A valid empty exact-employer result is preferable to substituting county, school, authority, special-district, university, or private-provider material.

## Top 20 future targets

| Rank | Municipality | State | Population | Score | Confidence |
|---:|---|---|---:|---:|---|
| 1 | Oklahoma City | OK | 702,767 | 78.002 | low |
| 2 | Phoenix | AZ | 1,650,070 | 77.973 | low |
| 3 | Portland | OR | 630,498 | 77.877 | low |
| 4 | Milwaukee | WI | 561,385 | 77.745 | low |
| 5 | Atlanta | GA | 510,823 | 77.636 | low |
| 6 | Kansas City | MO | 510,704 | 77.636 | low |
| 7 | Raleigh | NC | 482,295 | 77.570 | low |
| 8 | Honolulu | HI | 989,408 | 77.393 | low |
| 9 | Jacksonville | FL | 985,843 | 77.389 | low |
| 10 | Tulsa | OK | 411,894 | 77.389 | low |
| 11 | Aurora | CO | 395,052 | 77.340 | low |
| 12 | Charlotte | NC | 911,311 | 77.298 | low |
| 13 | Indianapolis city (balance) | IN | 879,293 | 77.257 | low |
| 14 | Metro Government Of Louisville-Jefferson County | KY | 772,144 | 77.109 | low |
| 15 | Seattle | WA | 755,078 | 77.084 | low |
| 16 | Denver | CO | 716,577 | 77.024 | low |
| 17 | Durham | NC | 296,186 | 77.008 | low |
| 18 | Nashville-Davidson County | TN | 687,788 | 76.977 | low |
| 19 | Washington | DC | 678,972 | 76.962 | low |
| 20 | Las Vegas | NV | 660,929 | 76.931 | low |

These ranks are operational priorities, not verified source findings. Consolidated government labels remain within the authoritative municipal/place universe and must receive exact-employer controls during future prompt preparation.
