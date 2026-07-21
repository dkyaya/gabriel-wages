#!/usr/bin/env python3
"""Build the two locked Stage 1 parallel-scout worker inputs.

This local-only builder reads the authoritative municipality universe, current
scout coverage, county crosswalk, national manifest, and scout queue. It does
not call a model/API, run a scout, open source URLs, verify sources, ingest,
codify, or alter queue/coverage/canonical data.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "analysis"
UNIVERSE = DOCS / "national_municipality_universe.csv"
COVERAGE = DOCS / "national_scout_coverage_municipality_2026-07-20.csv"
CROSSWALK = DOCS / "national_municipality_county_crosswalk.csv"
MANIFEST = DOCS / "next_wave_municipality_scout_manifest_2026-07-16.csv"
QUEUE = DOCS / "national_scout_candidate_queue_2026-07-20.csv"

PARALLEL_STAGE = "stage_1_two_parallel_25"
PROHIBITED_FAILURE_NAMES = {"Bloomington", "Oakland", "Stockton", "Oxnard", "Redding"}

FIELDS = [
    "wave_id",
    "state",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "county_relationship_count",
    "multi_county_flag",
    "county_context_summary",
    "priority_rank",
    "selection_bucket",
    "selection_reason",
    "claim_or_source_need_connection",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
    "already_scouted_status",
    "coverage_status_before_run",
    "worker_id",
    "parallel_stage",
    "scout_purpose",
    "anchor_cycle",
    "known_source_cycle_exclusions",
    "known_source_notes",
    "known_source_urls",
]


CA_SELECTION = [
    ("Irvine", "large_city_state_anchor", "Largest untouched CA municipal/place employer; adds an Orange County police/civilian comparison while requiring exact city-unit identity."),
    ("Santa Ana", "large_city_state_anchor", "Large Orange County seat and independent city employer with high safety-versus-civilian wage-setting relevance."),
    ("Huntington Beach", "large_city_state_anchor", "Large coastal Orange County city selected for an exact municipal public-safety and ordinary-civilian comparison."),
    ("Glendale", "large_city_state_anchor", "Large Los Angeles County city employer selected as a clean contrast to the already-scouted City of Los Angeles."),
    ("Ontario", "large_city_state_anchor", "Large Inland Empire city selected for inland labor-market and municipal-employer diversity."),
    ("Elk Grove", "large_city_state_anchor", "Large Sacramento-region city selected for a newer suburban municipal-employer contrast; non-city districts must be excluded."),
    ("Oceanside", "large_city_state_anchor", "Large northern San Diego County city selected for a coastal full-service municipal comparison."),
    ("Garden Grove", "large_city_state_anchor", "Large Orange County city selected for municipal police/civilian material and exact-employer screening of any fire material."),
    ("Corona", "mid_city_comparison_candidate", "Riverside County city selected for an Inland Empire comparison distinct from already-scouted Riverside."),
    ("Roseville", "mid_city_comparison_candidate", "Placer County regional center selected for northern Sacramento-metro and municipal labor-market diversity."),
    ("Hayward", "mid_city_comparison_candidate", "East Bay city selected as a medium-scale comparison distinct from covered Oakland, Fremont, and Berkeley."),
    ("Sunnyvale", "mid_city_comparison_candidate", "Santa Clara County city selected for a high-wage regional municipal-employer contrast."),
    ("Escondido", "mid_city_comparison_candidate", "Inland San Diego County city selected to balance coastal and inland southern California employers."),
    ("Pomona", "mid_city_comparison_candidate", "Eastern Los Angeles County city selected for an independent city-employer and inland regional contrast."),
    ("Fullerton", "mid_city_comparison_candidate", "North Orange County city selected for a medium-scale municipal police/fire/civilian discovery target."),
    ("Torrance", "mid_city_comparison_candidate", "South Bay city selected for an industrial/coastal municipal labor-market contrast."),
    ("Pasadena", "mid_city_comparison_candidate", "Independent Los Angeles County city selected for an established municipal-employer comparison."),
    ("Santa Clara", "mid_city_comparison_candidate", "Santa Clara County city selected for an exact city-employer contrast with San Jose and Sunnyvale."),
    ("Clovis", "regional_diversity_candidate", "Central Valley city selected as a comparison to covered Fresno while keeping the employer municipal."),
    ("Concord", "regional_diversity_candidate", "Contra Costa County city selected for an inland East Bay municipal-employer contrast."),
    ("Fairfield", "regional_diversity_candidate", "Solano County regional center selected for geographic and fiscal-environment diversity."),
    ("Richmond", "regional_diversity_candidate", "Contra Costa waterfront/industrial city selected for labor-market and fiscal-mechanism diversity."),
    ("San Luis Obispo", "regional_diversity_candidate", "Central Coast county-seat city selected for geographic and administrative diversity while excluding county and university employers."),
    ("Davis", "clean_municipal_employer_candidate", "Smaller Yolo County city selected for a clean municipal identity and university-employer exclusion test."),
    ("Eureka", "clean_municipal_employer_candidate", "Far-northern Humboldt County city selected to prevent Stage 1 from concentrating only on major coastal metros."),
]


NJ_SELECTION = [
    ("Paterson", "large_city_state_anchor", "Largest untouched NJ municipal/place employer and a high-value northern urban safety/civilian comparison."),
    ("Elizabeth", "large_city_state_anchor", "Large Union County city and port-region labor-market contrast; port/authority employers remain excluded."),
    ("Princeton", "regional_diversity_candidate", "Mercer County municipality selected for geographic and administrative diversity while explicitly excluding university and school employers."),
    ("Clifton", "large_city_state_anchor", "Large Passaic County city selected as an independent municipal-employer comparison."),
    ("Bayonne", "large_city_state_anchor", "Hudson County city selected for dense urban municipal labor and exact port/authority exclusion."),
    ("East Orange", "large_city_state_anchor", "Essex County city selected as a contrast to covered Newark without reusing Newark sources."),
    ("Passaic", "large_city_state_anchor", "Passaic County city selected for a dense medium-large municipal workforce comparison."),
    ("Union City", "large_city_state_anchor", "Hudson County city selected for a dense municipal-employer comparison distinct from Jersey City."),
    ("Vineland", "mid_city_comparison_candidate", "South Jersey Cumberland County city selected for geographic and regional labor-market diversity."),
    ("Hoboken", "national_manifest_anchor", "Untouched national-manifest anchor retained as an exact city employer; transit/port/authority substitutes are excluded."),
    ("New Brunswick", "mid_city_comparison_candidate", "Middlesex County city and regional administrative center selected with university and county employers excluded."),
    ("Perth Amboy", "mid_city_comparison_candidate", "Middlesex County city selected for an industrial/waterfront municipal comparison."),
    ("Plainfield", "mid_city_comparison_candidate", "Union County city selected for an independent municipal-employer and fiscal contrast."),
    ("West New York", "mid_city_comparison_candidate", "Authoritative Town of West New York municipal/place employer selected for Hudson County diversity."),
    ("Hackensack", "mid_city_comparison_candidate", "Bergen County seat selected for an administrative municipal comparison; county employers are excluded."),
    ("Sayreville", "mid_city_comparison_candidate", "Authoritative borough/place employer selected for a Middlesex County municipal comparison."),
    ("Linden", "mid_city_comparison_candidate", "Union County industrial city selected for municipal safety/civilian wage-setting relevance."),
    ("Fort Lee", "regional_diversity_candidate", "Bergen County borough selected for a dense suburban municipal-employer comparison."),
    ("Kearny", "regional_diversity_candidate", "Authoritative Town of Kearny municipal/place employer selected for a Hudson County industrial contrast."),
    ("Atlantic City", "national_manifest_anchor", "Untouched national-manifest anchor selected for a South Jersey fiscal/tourism contrast while excluding casino/private and authority employers."),
    ("Fair Lawn", "clean_municipal_employer_candidate", "Bergen County borough selected as a clean medium municipal-employer candidate."),
    ("Long Branch", "regional_diversity_candidate", "Monmouth County coastal city selected to diversify the batch beyond northern New Jersey."),
    ("Garfield", "clean_municipal_employer_candidate", "Bergen County city selected as a clean smaller municipal-employer candidate."),
    ("Rahway", "regional_diversity_candidate", "Union County city selected for a medium municipal comparison and transportation-employer exclusion test."),
    ("Morristown", "regional_diversity_candidate", "Morris County seat and town/place employer selected for western-northern geographic diversity; county employers are excluded."),
]


BATCHES = [
    {
        "worker_id": "parallel_worker_01",
        "state": "CA",
        "wave_id": "PARALLEL-STAGE1-W01-CA25.2-2026-07-21",
        "selection": CA_SELECTION,
        "output": DOCS / "parallel_worker_01_ca25_scout_input_2026-07-21.csv",
        "minimum_counties": 15,
        "expected_buckets": {
            "large_city_state_anchor": 8,
            "mid_city_comparison_candidate": 10,
            "regional_diversity_candidate": 5,
            "clean_municipal_employer_candidate": 2,
        },
    },
    {
        "worker_id": "parallel_worker_02",
        "state": "NJ",
        "wave_id": "PARALLEL-STAGE1-W02-NJ25-2026-07-21",
        "selection": NJ_SELECTION,
        "output": DOCS / "parallel_worker_02_nj25_scout_input_2026-07-21.csv",
        "minimum_counties": 11,
        "expected_buckets": {
            "national_manifest_anchor": 2,
            "large_city_state_anchor": 7,
            "mid_city_comparison_candidate": 8,
            "regional_diversity_candidate": 6,
            "clean_municipal_employer_candidate": 2,
        },
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def county_summary(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in sorted(rows, key=lambda value: value["county_geoid"]):
        rendered.append(
            f"{row['county_name']} [{row['county_geoid']}; "
            f"{row['county_equivalent_type']}; government-units-primary="
            f"{row['is_government_units_primary_county']}; "
            f"basis={row['relationship_basis']}]"
        )
    return " | ".join(rendered)


def build_batch(
    spec: dict[str, object],
    universe_by_state_name: dict[tuple[str, str], list[dict[str, str]]],
    coverage: dict[str, dict[str, str]],
    crosswalk: dict[str, list[dict[str, str]]],
    queue_ids: set[str],
) -> list[dict[str, str]]:
    state = str(spec["state"])
    worker_id = str(spec["worker_id"])
    selection = list(spec["selection"])
    output: list[dict[str, str]] = []
    county_geoids: set[str] = set()

    for rank, (name, bucket, reason) in enumerate(selection, start=1):
        matches = [
            row
            for row in universe_by_state_name[(state, name)]
            if row["government_type"] == "municipal"
            and row["geography_type"] == "place"
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one municipal/place government for {state} {name}; "
                f"found {len(matches)}"
            )
        row = matches[0]
        municipality_id = row["municipality_id"]
        status = coverage[municipality_id]
        if status["scout_coverage_status"] != "not_scouted":
            raise ValueError(
                f"Selected municipality is not untouched: {state} {name}="
                f"{status['scout_coverage_status']}"
            )
        if status["failed_connection_attempt_count"] != "0":
            raise ValueError(f"Selected municipality has a prior failed attempt: {state} {name}")
        if municipality_id in queue_ids:
            raise ValueError(f"Selected municipality already appears in queue: {state} {name}")
        if status["already_in_corpus"] != "no":
            raise ValueError(f"Selected municipality has canonical corpus context: {state} {name}")
        if name in PROHIBITED_FAILURE_NAMES:
            raise ValueError(f"Prohibited recent failure-only municipality selected: {state} {name}")

        county_rows = crosswalk[municipality_id]
        if len(county_rows) != int(row["county_relationship_count"]):
            raise ValueError(f"County relationship mismatch: {state} {name}")
        county_geoids.update(item["county_geoid"] for item in county_rows)
        county_names = "/".join(item["county_name"] for item in county_rows)

        output.append(
            {
                "wave_id": str(spec["wave_id"]),
                "state": state,
                "municipality": row["municipality"],
                "municipality_id": municipality_id,
                "census_gov_id": row["census_gov_id"],
                "government_name": row["government_name"],
                "government_type": row["government_type"],
                "geography_type": row["geography_type"],
                "population": row["population"],
                "county_relationship_count": row["county_relationship_count"],
                "multi_county_flag": row["multi_county_flag"],
                "county_context_summary": county_summary(county_rows),
                "priority_rank": str(rank),
                "selection_bucket": bucket,
                "selection_reason": reason,
                "claim_or_source_need_connection": (
                    f"Stage 1 parallel national discovery in {state}: seek a within-municipality, "
                    "mutually overlapping 2014-2024 safety/ordinary-civilian source set and "
                    "preserve mechanism leads without treating scout metadata as evidence."
                ),
                "expected_units_to_search": (
                    "municipal police CBA; municipal fire CBA only when the exact target city/town/"
                    "borough is the employer; one ordinary general-municipal non-safety CBA such "
                    "as clerical, public works, library, sanitation, or citywide civilian; public "
                    "arbitration, factfinding, impasse, or other binding wage-setting material"
                ),
                "verification_notes": (
                    f"Scout-stage only. Target exactly {row['government_name']} (Census government "
                    f"ID {row['census_gov_id']}). Exclude {county_names}, school districts, transit "
                    "agencies, port/airport authorities, housing authorities, park districts, "
                    "township governments, fire/water/utility or other special districts, regional "
                    "bodies, universities, state/federal employers, and private providers. If fire "
                    "or police service is supplied by another employer, do not attribute that unit "
                    "to the municipality; an exact municipal safety unit plus an ordinary municipal "
                    "civilian unit can still be useful. A safety agreement cannot satisfy the "
                    "non-safety request. Do not make or recommend a public-records request. Allow an "
                    "empty candidate list. Later verification—not this scout—must confirm employer, "
                    "unit, provenance, execution/completeness, dates, wages, duplicates, access, and "
                    "mutual cycle overlap."
                ),
                "recommended_scout_status": "locked_for_stage1_worker",
                "already_scouted_status": "no",
                "coverage_status_before_run": "not_scouted",
                "worker_id": worker_id,
                "parallel_stage": PARALLEL_STAGE,
                "scout_purpose": "matched_comparison_repair",
                "anchor_cycle": (
                    "No canonical anchor cycle is supplied. Seek visibly supported overlapping "
                    "2014-2024 municipal safety and ordinary-non-safety cycles; label non-overlap "
                    "or unclear year evidence instead of inferring dates."
                ),
                "known_source_cycle_exclusions": (
                    f"None recorded: no current national queue row or successful scout coverage "
                    f"for {row['government_name']} as of the locked 2026-07-21 pre-run snapshot."
                ),
                "known_source_notes": (
                    "No source URL was opened during selection. Duplicate checks remain required "
                    "against returned rows and the coordinator's pre-merge national queue."
                ),
                "known_source_urls": "",
            }
        )

    if len(output) != 25:
        raise ValueError(f"{worker_id} must contain exactly 25 rows")
    if len({row["municipality_id"] for row in output}) != 25:
        raise ValueError(f"{worker_id} municipality IDs are not unique")
    if len({row["census_gov_id"] for row in output}) != 25:
        raise ValueError(f"{worker_id} Census government IDs are not unique")
    if {row["government_type"] for row in output} != {"municipal"}:
        raise ValueError(f"{worker_id} includes a prohibited government type")
    if {row["geography_type"] for row in output} != {"place"}:
        raise ValueError(f"{worker_id} includes a non-place geography")
    observed_buckets = Counter(row["selection_bucket"] for row in output)
    if observed_buckets != Counter(spec["expected_buckets"]):
        raise ValueError(f"{worker_id} bucket counts changed: {observed_buckets}")
    if len(county_geoids) < int(spec["minimum_counties"]):
        raise ValueError(
            f"{worker_id} county diversity too low: {len(county_geoids)} < "
            f"{spec['minimum_counties']}"
        )
    return output


def main() -> int:
    universe = read_csv(UNIVERSE)
    coverage_rows = read_csv(COVERAGE)
    crosswalk_rows = read_csv(CROSSWALK)
    manifest_rows = read_csv(MANIFEST)
    queue_rows = read_csv(QUEUE)

    if len(universe) != 35_589 or len(coverage_rows) != 35_589:
        raise ValueError("Authoritative universe/coverage row counts changed")
    coverage = {row["municipality_id"]: row for row in coverage_rows}
    if len(coverage) != 35_589:
        raise ValueError("Coverage municipality IDs are not unique")
    queue_ids = {row["municipality_id"] for row in queue_rows}
    universe_by_state_name: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        universe_by_state_name[(row["state"], row["municipality"])].append(row)
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in crosswalk_rows:
        crosswalk[row["municipality_id"]].append(row)

    outputs: list[list[dict[str, str]]] = []
    for spec in BATCHES:
        rows = build_batch(spec, universe_by_state_name, coverage, crosswalk, queue_ids)
        output_path = Path(spec["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        parsed = read_csv(output_path)
        if len(parsed) != 25 or list(parsed[0]) != FIELDS:
            raise ValueError(f"Parse-back schema/row failure: {output_path}")
        if [row["municipality"] for row in parsed] != [
            entry[0] for entry in spec["selection"]
        ]:
            raise ValueError(f"Parse-back order changed: {output_path}")
        outputs.append(parsed)

    all_ids = [row["municipality_id"] for rows in outputs for row in rows]
    if len(all_ids) != 50 or len(set(all_ids)) != 50:
        raise ValueError("Stage 1 worker batches are not disjoint")

    manifest_by_state = defaultdict(dict)
    for row in manifest_rows:
        manifest_by_state[row["state"]][row["municipality_id"]] = row
    ca_selected = {row["municipality_id"] for row in outputs[0]}
    ca_manifest_uncovered = {
        municipality_id
        for municipality_id in manifest_by_state["CA"]
        if coverage[municipality_id]["scout_coverage_status"] == "not_scouted"
    }
    if ca_manifest_uncovered - ca_selected:
        raise ValueError("CA worker omitted an eligible untouched CA manifest anchor")
    nj_selected = {row["municipality_id"] for row in outputs[1]}
    required_nj_manifest = {
        municipality_id
        for municipality_id, row in manifest_by_state["NJ"].items()
        if coverage[municipality_id]["scout_coverage_status"] == "not_scouted"
        and next(
            value
            for value in universe
            if value["municipality_id"] == municipality_id
        )["government_type"]
        == "municipal"
    }
    # Edison, Woodbridge, and Lakewood are township governments and therefore
    # prohibited here; Hoboken and Atlantic City are the eligible untouched
    # municipal/place NJ manifest anchors.
    if required_nj_manifest - nj_selected:
        raise ValueError(
            "NJ worker omitted eligible municipal/place NJ manifest anchors: "
            f"{sorted(required_nj_manifest - nj_selected)}"
        )

    for spec, rows in zip(BATCHES, outputs):
        print(f"worker={spec['worker_id']} state={spec['state']} rows={len(rows)}")
        print("municipalities=" + ", ".join(row["municipality"] for row in rows))
        print(f"output={Path(spec['output']).relative_to(ROOT)}")
    print("stage1_total_rows=50 stage1_distinct_municipality_ids=50")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
