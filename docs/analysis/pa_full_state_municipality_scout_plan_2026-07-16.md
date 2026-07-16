# Pennsylvania Full-State Municipality Scout Plan — 2026-07-16

## Outcome

`pa_full_state_municipality_scout_manifest_2026-07-16.csv` is a complete, ranked planning frame for all **2,557** active Pennsylvania municipal and township governments in the corrected national municipality universe.

- Municipal governments: **1,014**
- Township governments: **1,543**
- Already scouted: **25**
- Scout-positive: **23**
- Scouted with no candidate: **2**
- Unscouted and eligible for future scouting: **2,532**
- Already in the canonical corpus: **1** (Philadelphia)
- Already in `data/city_coverage.csv`: **1** (Philadelphia)
- Multi-county governments: **12**
- Municipality-county relationship rows: **2,569**

The 25 previously scouted municipalities remain in the CSV for auditability but have `pa_batch_id=not_assigned_already_scouted`, `pa_runner_shard_id=not_assigned_already_scouted`, and `recommended_scout_status=excluded_already_scouted`. No retest is justified by this plan. All 2,532 unscouted rows have `recommended_scout_status=ready_for_scout`, which means eligible for a future bounded scout—not verified, ingested, or codified.

No live GABRIEL scout, model/API, source verification, ingestion, or codification call was performed.

## Source-of-truth correction required for the PA frame

The relay-carried files matched the working tree byte-for-byte at starting commit `76ff94a`. During the required universe/crosswalk reconciliation, one clear national-builder bug appeared: Census government ID `191397`, `TOWNSHIP OF AUBURN`, was labeled `state=OR` in the universe even though its `FIPS_STATE=42`, `FIPS_COUNTY=115`, and crosswalk county are Susquehanna County, Pennsylvania.

The underlying 2025 Government Units workbook explains the discrepancy. Its `STATE` column belongs to the government contact's **mailing address**; Auburn Township's contact address is in Oregon. `FIPS_STATE` is the government's jurisdiction. Thirty-eight active municipal/township governments nationally have a mailing state different from their jurisdiction state.

`build_scout_coverage.py` was corrected to derive jurisdiction state from `FIPS_STATE`, enforce state/state-FIPS consistency, and rebuild the national universe, crosswalk, and state coverage. The national total remains 35,589, but 38 governments move to their correct states. Pennsylvania changes from 2,556 to **2,557** because Auburn Township is now correctly included. This is clear repository/source evidence that the relay's national state assignment was incomplete for the requested PA full-state task; all scout-result metrics remain unchanged.

## Why a full Pennsylvania scan is useful

The national 100-municipality manifest is optimized for claim testing: it repairs named safety/non-safety gaps, adds repeat cycles, and probes institutional contrasts across states. A full-state PA frame answers a different question: which municipality employers anywhere in one state produce plausible public police, fire, and ordinary non-safety source leads before the project spends verification or ingestion effort?

That state-by-state approach can:

- reveal source-rich small and midsize municipalities that a national large-city sample would miss;
- identify where Pennsylvania's Act 111 safety-side materials and ordinary municipal non-safety agreements appear together;
- distinguish legitimate no-unit/no-public-source outcomes from municipalities never queried;
- provide a complete denominator for PA scout coverage; and
- support later county/geographic stratification without confusing a county association with municipality completion.

The full manifest is a planning and accounting frame, not authorization to run 2,532 prompts without stops. At the prior PA batch's observed rate, a blind sweep could generate roughly three candidate rows per municipality—potentially about 7,600 unverified leads. Verification capacity, not prompt generation, is the binding constraint.

## Scout-runner input shape and batching

`scripts/gabriel_state_source_scout.py` requires only these municipality-input columns:

- `municipality_id`
- `municipality`
- `state`

It ignores additional columns, filters rows to the requested `--state`, preserves input order, and defaults to dry-run. Its live path enforces `LIVE_HARD_CAP=25`. Therefore this plan uses two compatible batching layers:

1. **Planning batches of 100** in `pa_batch_id`, as requested for state-scale accounting. There are **26** planning batches: 25 batches of 100 and one final batch of 32.
2. **Runner shards of at most 25** in `pa_runner_shard_id`. There are **102** shards: 101 shards of 25 and one final shard of 7. Every 100-row planning batch is four runner shards; the final 32-row planning batch is one 25-row shard plus one 7-row shard.

For any future dry run, first filter the full manifest to one `pa_runner_shard_id` and write a small CSV retaining at least the three required input fields. Do not pass the unfiltered 2,557-row manifest and assume the runner will select an arbitrary later shard: the runner supports a leading `--limit`, not an offset or `pa_batch_id` filter.

The safe command shape is:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state PA \
  --municipalities-csv <one-filtered-runner-shard.csv> \
  --prompt-mode minimal
```

This task did not run even a dry-run preview because the requested deliverable is the planning manifest and comparison, not prompt generation.

## Priority score and tiers

The manifest uses transparent source-availability and comparability **proxies**, not a claim that a municipality has a police union, paid fire department, ordinary non-safety CBA, or public portal.

The score is additive:

### Population/administrative scale

- Population 50,000+: +50
- 25,000-49,999: +40
- 10,000-24,999: +30
- 5,000-9,999: +20
- 2,000-4,999: +10
- Under 2,000: +0

### Government form

- Census political description `CITY`: +15
- `MUNICIPALITY`: +12
- `BOROUGH` or `TOWN`: +8
- `TOWNSHIP`: +5

Government form is a modest administrative proxy only. It does not automatically rank a small city above a large township.

### Source-discovery and geographic signals

- Government Units record contains an official website: +15
- Shares any county context with an already-scouted municipality: +10
- Shares county context with a scout-positive municipality: +5
- Shares county context with a prior likely-triad scout result: +5
- Multi-county government: +3

The county-adjacency bonuses describe prior **scout-stage** experience only. They do not turn a neighboring municipality's lead into verification for another employer.

The tiers are:

| Priority tier | Score | Unscouted count | Interpretation |
|---|---:|---:|---|
| `tier_1_high_plausibility` | 60+ | 222 | Strongest population/administrative/source-discovery proxy combination. |
| `tier_2_medium_high_plausibility` | 45-59 | 337 | Meaningful scale or website/administrative signals, but fewer combined advantages. |
| `tier_3_systematic_mid_small` | 25-44 | 699 | Midsize/small governments retained for systematic coverage and possible clean comparisons. |
| `tier_4_small_low_information` | Under 25 | 1,274 | Mostly small or low-information governments; legitimate no-unit outcomes are likely. |
| `carry_forward_already_scouted` | Not scored | 25 | Audit-only rows excluded from default live-scout batches. |

Within each tier, governments are cycled across the Government Units primary/headquarters county and then ordered by score, population, name, and Census ID. The primary county is used only as a deterministic scheduling stratum. Every county relationship remains in `county_context_summary`, so multi-county governments are not analytically collapsed.

This design intentionally allows high-value small and midsize governments—such as Nanticoke, Dunmore, Waynesboro, and Hermitage—to appear beside larger townships. That supports the project's need for potentially cleaner matched municipal comparisons rather than only accumulating the largest employers.

## Batch 01 characteristics

Planning batch 01 contains 100 unscouted municipalities:

- 63 township and 37 municipal governments;
- 28 batching counties;
- 99 with a Government Units website and 1 without;
- population range 5,050 to 84,893; median 16,514.5;
- 8 at 50,000+, 29 at 25,000-49,999, 49 at 10,000-24,999, and 14 at 5,000-9,999;
- 100 in `tier_1_high_plausibility`;
- 0 already in the corpus; and
- 0 already scouted.

The first runner shard—ranks 1-25—contains 25 different batching counties. This makes the initial PA test geographically broad without sacrificing tier-1 status.

## Multi-county municipalities

Pennsylvania has 12 multi-county municipal/township governments in the corrected universe. Each has one manifest row and multiple segments in `county_context_summary`, with:

- county name;
- county GEOID;
- county-equivalent type;
- Government Units primary/headquarters flag; and
- relationship basis.

`batching_county_geoid` and `batching_county_name` are scheduling fields only. They never replace the complete relationship summary, and county coverage does not imply municipality completion.

## Existing verified/corpus and coverage context

Philadelphia is the only PA municipality currently represented in both the canonical corpus and `data/city_coverage.csv`. It is already scouted and is excluded from new live-scout batches. No unscouted PA municipality shares Philadelphia County because Philadelphia County has only that in-scope municipality government. Thus “near an existing verified city” was considered but cannot produce a same-county rank bonus under the available crosswalk.

The broader county bonuses use already-scouted, scout-positive, and likely-triad municipalities as weak source-environment proxies. They remain explicitly separate from verified, ingested, or codified status.

## PA carry-forward

The 25 previously scouted PA municipalities remain unchanged:

- 25 scouted;
- 23 scout-positive;
- 20 with a police candidate;
- 16 with a fire candidate;
- 14 with a non-safety candidate;
- 10 with likely-triad scout output;
- 75 candidate rows;
- 65 official-or-union candidate rows;
- 3 high-priority candidate rows; and
- $0.2687877 total scout cost.

Bethlehem and Carlisle returned no candidates but remain valid completed scout outcomes rather than failures. All 25 are excluded from the default new batches because another model pass would add less value than verifying the existing backlog. A retest should require a municipality-specific justification—such as a known prompt bug, a material portal change, or an unresolved failed parse—not merely `scout_positive_status=no`.

## Comparison with the national manifest

The two manifests serve complementary strategies:

| Dimension | National batch 01 | PA planning batch 01 |
|---|---:|---:|
| Municipalities | 25 | 100 |
| States | 6 | 1 |
| Already in corpus | 12 | 0 |
| Multi-county municipalities | 7 | 1 |
| Main design | Claim-driven repair, repeat cycles, and named institutional contrasts | Full-state discovery and complete PA coverage denominator |
| Priority composition | 10 matched-comparison repairs; 3 repeat-cycle anchors; 12 named targets | 100 tier-1 structural/source-availability proxies |
| Verification burden | Bounded and tied to named claims | Potentially large; four runner shards and likely many new unverified leads |

National batch 01 contains 8 MA, 5 IL, 5 NY, 3 TX, 3 NJ, and 1 CA municipality. The runner filters by a single `--state`, so national batch 01 cannot be executed as one 25-prompt call. It must be split into six state-specific inputs. That is an execution detail, not a reason to merge the strategies.

The national batch directly attacks existing design gaps—San Antonio, Somerville, Newton, Austin, Newark, Boston, Worcester, Arlington, Georgetown, and Jersey City—and adds repeat cycles for Franklin, Seekonk, and Houston. PA batch 01 instead broadens discovery within a state where 75 unverified candidate leads already await verification.

## Recommended next live scout path

**Recommendation: national batch 01, not PA batch 01 and not a hybrid.** Execute it as state-specific slices, beginning with the three-row Texas slice (San Antonio, Austin, Houston) because it contains the national manifest's rank 1 urgent non-safety gap, rank 4 ordinary-comparator gap, and rank 13 repeat-cycle anchor. Dry-run and review each state slice before any separately authorized live call.

Reasons:

1. National batch 01 has immediate claim and matched-design value; PA batch 01 is primarily discovery.
2. Twelve national rows already have corpus context, making verification and design impact easier to assess.
3. Pennsylvania already has 75 unverified leads from 25 municipalities. Adding up to 300 more leads from a 100-row PA planning batch before resolving that backlog would worsen the verification bottleneck.
4. A hybrid would split verification attention across two objectives and still require separate state-filtered runner calls. It offers no clear efficiency advantage.
5. The full PA plan remains valuable as the next state-scale pathway once verification capacity is available; it is not discarded by sequencing national batch 01 first.

The recommendation would change if:

- the existing PA candidate backlog is verified or triaged to a documented stopping point;
- the PI explicitly prioritizes a complete Pennsylvania source-availability denominator over current claim repairs;
- staff or tooling can verify a 100-municipality PA batch without allowing scout output to become de facto verified data;
- a current PA legal/source audit identifies a uniquely urgent statewide claim test;
- national batch 01's named gaps are resolved through non-scout methods; or
- a small dry-run/authorized PA shard shows substantially higher clean-triad yield than the earlier 25-municipality batch.

## Rebuild and validation

Run:

```bash
python scripts/build_pa_full_state_municipality_manifest.py
```

The builder requires:

- exact equality between the manifest municipality-ID set and the corrected PA universe;
- unique municipality and Census government IDs;
- state `PA` and state FIPS `42` consistency;
- exact copying of authoritative identity, population, geography, and status fields;
- every county GEOID present in the full relationship summary;
- exactly 25 already-scouted rows excluded from live batches;
- 2,532 unscouted rows marked ready;
- 26 planning batches: 25x100 + 1x32; and
- 102 runner shards: 101x25 + 1x7.

## Known limitations

- The score measures source-discovery plausibility, not actual bargaining-unit existence, contract availability, or match quality.
- Government Units website presence is not live URL verification; some URLs may be obsolete, misspelled, redirected, or inaccessible.
- Population values come from the Government Units source and may not share one uniform reference year.
- County adjacency is not distance. Except for the impossible Philadelphia same-county case, the available crosswalk cannot determine which municipality is physically closest to a verified city.
- Fire service is frequently regional, volunteer, or otherwise not a municipal bargaining unit in Pennsylvania; the municipality universe does not encode that institutional fact.
- School districts and county employers are outside this municipality-employer manifest even when they are locally important non-safety or public-safety employers.
- A 100-row planning batch still means four separately bounded live invocations under the current runner. Retries must remain limited and separately recorded.
- Using the prior batch's approximate $1.08/100 and 73 minutes/100 rates, 2,532 unscouted municipalities would imply roughly $27 and 31 sequential hours before retries, plus a far larger human-verification burden. These are planning estimates, not a commitment or authorization.
- Scout-positive, verified, ingested, and codified statuses remain separate. No field in this manifest promotes a lead downstream.
