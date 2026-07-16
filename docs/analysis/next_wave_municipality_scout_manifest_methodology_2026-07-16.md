# Next-Wave Municipality Scout Manifest Methodology — 2026-07-16

## Outcome

`next_wave_municipality_scout_manifest_2026-07-16.csv` is a ranked, bounded source-scouting plan for **100 municipality governments in 19 states/DC**. It is divided into four 25-municipality execution batches (`NWMS-2026-07-16-01` through `NWMS-2026-07-16-04`). It is not a scout result, source-verification ledger, ingestion queue, or codification record.

The manifest contains:

- 100 unique `municipality_id` values and 100 unique Census government IDs;
- 94 municipal governments and 6 township governments;
- 18 multi-county municipalities, with all **52** of their municipality-county relationships retained in `county_context_summary`;
- 12 municipalities already represented in the corpus, included only for a named matched-comparison repair or repeat-cycle need;
- 0 already-scouted municipalities and therefore 0 PA re-scouts; and
- 0 blank required cells.

No GABRIEL scout call, model/API call, source verification, source ingestion, or codification was performed. All 100 rows remain `recommended_scout_status=ready_for_scout`; that status means only that the municipality is eligible for a future bounded scout run.

## Sources read before selection

The selection begins with claims and source needs, not with a population ranking. The controlling local sources were:

- `claim_testing_source_wave_methodology_2026-07-12.md`;
- `claim_register_2026-07-12.csv`;
- `claim_driven_source_needs_2026-07-12.csv`;
- `hypothesis_tracker_2026-07-12.csv`;
- `state_city_claim_map_2026-07-12.csv` and its summary;
- `pa_nj_candidate_sources_followup_2026-07-12.csv` and the PA/NJ claim notes;
- `national_source_targets_2026-07-12.csv`;
- `national_scout_coverage_methodology_2026-07-15.md` and setup note;
- `national_municipality_universe.csv`; and
- `national_municipality_county_crosswalk.csv`.

The latest relay bundle, `tmp/national_municipality_universe_crosswalk_2026-07-16_relay_4c2db6c.zip`, carried the national-universe, crosswalk, coverage, progress, handoff, and builder files. Every relay-carried substantive file matched the repository copy byte-for-byte. The relay did not contain `AGENTS.md` or the older claim/source-strategy files listed above, so those unchanged files were read from the repository. There was no substantive relay/repository disagreement.

## Why the wave size is 100

The authoritative universe has 35,589 active municipal/township governments. Scouting all of them would produce an unauditable verification backlog and would violate the claim-driven, bounded-wave method.

A 100-government wave is large enough to cover the project's named claim gaps and several institutional/geographic contrasts, but still divides cleanly into **four batches of 25**, the largest batch size already exercised by the project's scout workflow. The intended operating rule is sequential: scout one 25-row batch, parse and deduplicate it, verify the strongest safety/non-safety leads, update coverage, and only then release the next batch. The manifest does not authorize any future live call by itself.

## Prioritization rules

The manifest is a purposive claim-testing sample, not a representative probability sample. Ranking proceeds in this order:

1. **Repair named matched-comparison gaps.** Existing safety-only or incomplete city designs receive the highest ranks when a specific missing unit would convert dead weight into a usable safety/non-safety comparison. San Antonio, Somerville, Newton, Austin, Newark, Boston, Worcester, Arlington MA, Georgetown MA, and Jersey City make up this bucket.
2. **Add repeat cycles to current claim anchors.** Franklin, Seekonk, and Houston are already useful designs. Repeat-cycle sourcing is more valuable than another unrelated safety-only city because it adds time variation while preserving within-city occupational comparability.
3. **Carry forward explicit national source targets.** Twenty municipalities are already named in `national_source_targets_2026-07-12.csv`. Their existing claim IDs, hypothesis IDs, expected value, and expected verification burden are copied into the selection logic rather than re-invented.
4. **Add institutional-regime contrasts.** Texas, Florida, North Carolina, Tennessee, Wisconsin, and Nevada municipalities test source-availability hypotheses about specialized or uneven safety/non-safety pathways and formal-impasse/comparator evidence. These labels are planning hypotheses drawn from the existing claim/source-need files, not new legal findings. Current law and local bargaining authority must be checked before interpreting a scout result.
5. **Add within-state replications around flagships.** Additional NJ, IL, NY, CT, RI, MN, WA, OR, and CA governments prevent one large city from standing in for an entire state's source environment. The set deliberately includes midsize and small governments as well as the largest city.
6. **Retain administrative/geographic anchors.** Annapolis, Colorado Springs, and DC supply state-capital, consolidated/independent-government, and regional diversity not captured by a pure population sort.

Within those tiers, the tie-breakers are: urgent source need; ability to repair an existing corpus design; explicit appearance in the national target file; expected ability to locate police, fire, and an ordinary non-safety unit; population/administrative importance; state quota; and anticipated verification burden. A municipality repeatedly documented as a poor verification use—such as Elizabeth NJ after two unsuccessful rounds—was not included merely because it is large.

## Selection buckets and counts

| Selection bucket | Count | Purpose |
|---|---:|---|
| `matched_comparison_repair` | 10 | Fill a named missing comparison/safety leg or current-cycle successor gap. |
| `repeat_cycle_claim_anchor` | 3 | Add temporal depth to an existing matched claim anchor. |
| `claim_register_named_target` | 20 | Carry forward an explicit national source target and its claim/hypothesis links. |
| `institutional_regime_contrast` | 29 | Test source-availability and bargaining-pathway contrasts without treating them as established legal facts. |
| `within_state_replication` | 35 | Add non-flagship governments so state patterns are not inferred from one city. |
| `population_admin_anchor` | 3 | Preserve administrative and geographic diversity not captured elsewhere. |

## State and legal-regime diversity

| State | Count | Main role in wave |
|---|---:|---|
| CA | 5 | Named West Coast targets plus within-state replication. |
| CO | 2 | Named consolidated-government target plus Front Range replication. |
| CT | 5 | New England/formal-impasse and comparator-source need; includes statewide urban variation. |
| DC | 1 | Unique municipal/federal-district administrative anchor. |
| FL | 6 | Safety/non-safety pathway contrast requested by CLM-02/CLM-08 and H6. |
| IL | 10 | High-priority shared-framework matched-triad expansion plus midsize replications. |
| MA | 8 | Specific comparison repairs and repeat-cycle anchors; not generic expansion. |
| MD | 2 | Independent-city and state-capital administrative contrast. |
| MN | 5 | Dense cross-occupation replication requested by CLM-03/H8. |
| NC | 6 | Safety/non-safety source-availability contrast requested by CLM-02/CLM-08 and H6. |
| NJ | 8 | Centralized PERC verification route, current-cycle/triad gaps, and municipal/township replication. |
| NV | 3 | Formal-impasse/arbitration distinction and comparator-source contrast. |
| NY | 10 | High-priority arbitration/comparator and clean-triad target state plus city-size variation. |
| OR | 4 | Dense cross-occupation and West Coast institutional replication. |
| RI | 3 | Small-state/New England replication around multiple municipal employers. |
| TN | 5 | Safety/non-safety source-availability contrast requested by H6. |
| TX | 8 | Urgent non-safety repairs, repeat-cycle Houston, and within-regime replication. |
| WA | 4 | Dense cross-occupation replication and Western diversity. |
| WI | 5 | Named target plus the H6 safety/non-safety pathway contrast. |

This is deliberately not a comprehensive state-law taxonomy. The local claim files identify needed **types** of institutional contrast and suggested states, but they do not constitute a current 50-state legal survey. Before interpreting a source absence as a bargaining prohibition—or a source presence as an arbitration entitlement—the verification stage must check current state and local law using authoritative legal sources.

## How population was used without letting it dominate

Population is copied unchanged from the Census Government Units Listing and is used as a tie-breaker and a review-burden signal. Large governments matter because they are administratively consequential and more likely to have multiple bargaining units; very large cities also receive a warning to cap review to their strongest official/union leads because their source environments can be sprawling.

Population does not determine the sample by itself:

- the top 13 ranks are claim/design repairs or repeat-cycle anchors, including small Georgetown and Seekonk;
- the manifest includes state capitals and midsize/small within-state replications;
- repeated low-yield targets are omitted despite size; and
- state quotas prevent CA, NY, TX, or other large-state cities from crowding out New England, Midwest, Southeast, and Pacific Northwest comparisons.

## Municipality IDs, government types, and county context

Every row copies `municipality_id`, `census_gov_id`, `government_name`, `government_type`, `geography_type`, population, and workflow status directly from `national_municipality_universe.csv`. Same-name city/township governments are disambiguated by both Census government ID and government type. For example, the manifest selects municipal—not township—Aurora, Rockford, Springfield, Naperville, Elgin, Joliet, Champaign, Decatur, Green Bay, Duluth, and Rochester where both types exist.

The six selected township governments are Arlington MA, Georgetown MA, Seekonk MA, Edison NJ, Woodbridge NJ, and Lakewood NJ. They remain township employers because that is their Census government classification; they are not relabeled as incorporated places.

`county_context_summary` is built from `national_municipality_county_crosswalk.csv`, with one segment for every relationship:

```text
County Name [county GEOID; county-equivalent type; government-units-primary=yes/no; relationship basis]
```

The 18 multi-county municipalities retain all 52 relationship segments. The manifest never turns the Government Units primary/headquarters county into a one-county analytical assignment. Crosswalk context is geography and verification assistance; county coverage remains distinct from municipality completion.

Special structures remain explicit:

- Baltimore is a municipal employer associated with its independent-city county equivalent.
- Carson (government name `CITY OF CARSON CITY`) is a municipal employer associated with the Carson City independent-city equivalent.
- Denver and Nashville-Davidson retain their exact consolidated/composite government names from Census.
- New England towns retain their township-government classifications.
- DC is the `CITY OF WASHINGTON DC` municipal government and the `11001` federal-district county equivalent.

## Why county-government employers remain out of scope

The source universe is municipal/township employers. Ordinary counties may be important police, corrections, sheriff, fire, public-works, or administrative employers, but mixing them into this file would change the employer type and the meaning of a within-city matched comparison. A future county-employer universe should be built separately from active Census county governments, define which county public-safety occupations are analytically comparable to municipal police/fire, and carry its own county-employer IDs, source needs, and coverage statuses. It should be linkable to this manifest by county GEOID but never appended as if a county were a municipality.

## Status separation and PA carry-forward

The manifest copies three status fields without inference:

- `already_scouted` — whether a GABRIEL source-scout query has already been run;
- `scout_positive_status` — whether that scout returned any unverified candidate leads; and
- `already_in_corpus` — whether the municipality is independently represented in the canonical contract corpus.

No field treats a scout-positive lead as verified, ingested, or codified. The 12 in-corpus rows are present because they have a named design repair or repeat-cycle purpose, not because ingestion implies scouting or verification.

PA carry-forward is: 2,557 municipality employers after correcting one out-of-state mailing-address assignment; 25 scouted; 23 scout-positive; 20 with police candidates; 16 with fire candidates; 14 with non-safety candidates; 10 likely triads; 75 candidate rows; 65 official-or-union candidate rows; 3 high-priority candidate rows; and $0.2687877 scout cost. The one-row universe correction does not change any scout-result metric. No PA municipality appears in this manifest. The PA bottleneck is verification of the existing unverified lead backlog, so another PA scout pass is not justified by the current criteria.

## Rebuild and validation procedure

Run:

```bash
python scripts/build_next_wave_municipality_manifest.py
```

The builder:

1. resolves every selected government against the authoritative universe by state, normalized municipality label, and expected government type;
2. requires exactly one match;
3. copies authoritative IDs, population, geography type, and workflow statuses;
4. joins every county relationship and requires the crosswalk count to match `county_relationship_count`;
5. assigns rank and a 25-row `wave_id`;
6. writes with `csv.DictWriter` and parses the result back;
7. requires 100 unique municipality IDs, 100 unique Census government IDs, ranks 1-100, no PA row, no already-scouted row, and `ready_for_scout` on every row.

The national coverage builder does not need to run for a manifest-only rebuild because this workflow does not alter the national universe, crosswalk, or coverage files.

## Known limitations and what would make the manifest change

- This is a purposive source-discovery design, not a representative national municipality sample. It cannot support population-weighted or national prevalence estimates.
- State-regime labels are claim-planning hypotheses based on the current source-need files, not a newly verified legal database. A current authoritative state-law audit could move states or municipalities between buckets.
- Population is the Government Units source value and may not share one uniform reference date across every row.
- Universe inclusion does not prove a paid police/fire unit, collective bargaining, an in-window agreement, or a public portal. Small governments are especially likely to produce legitimate no-source results.
- The place/county crosswalk combines 2020 place relationships, 2024 county/county-subdivision geography, and 2025 Government Units supplements. It is sufficient for preserved relationship context but is not a post-2020 boundary-history database.
- The claim/source files have evolved through later handoff entries. Where an older state-city map still labels Philadelphia or Trenton uncodified, the newer handoff documents their later codification; neither is added here for redundant scouting.
- Very large cities may yield too many weak candidates. Verification should stop after the strongest official/union police, fire, and ordinary non-safety routes are resolved.
- A material new corpus ingestion, verified-source ledger, state-law audit, scout-coverage update, or Census universe rebuild should trigger a manifest rebuild before live execution.

## Recommended next execution step

Do not launch all 100 rows. Extract only `wave_id=NWMS-2026-07-16-01` (ranks 1-25) into the scout runner's input shape. Because `gabriel_state_source_scout.py` filters one `--state` per invocation, split batch 01 into six state-specific inputs and dry-run/review each slice; the three-row Texas slice is the recommended first slice. If a live scout is later authorized, use the established one-request-at-a-time/minimal-prompt configuration with one bounded retry pass. Keep every return at scout stage, then verify the strongest official/union safety plus ordinary non-safety routes—starting with ranks 1-10—before releasing batch 02.
