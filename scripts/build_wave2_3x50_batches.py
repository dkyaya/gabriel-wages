#!/usr/bin/env python3
"""Build Wave 2 CA50, TX50, and IL50 offline worker-preparation inputs.

This deterministic local builder reads the committed municipality universe,
current scout coverage, current candidate queue, canonical city context, and
county crosswalk. It does not open URLs, call a model, run a scout, verify or
ingest sources, codify text, or modify national queue/coverage outputs.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "docs" / "analysis"
UNIVERSE_PATH = ANALYSIS / "national_municipality_universe.csv"
COVERAGE_PATH = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
QUEUE_PATH = ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv"
CROSSWALK_PATH = ANALYSIS / "national_municipality_county_crosswalk.csv"
CONTRACTS_PATH = ROOT / "data" / "contracts.csv"
CITY_COVERAGE_PATH = ROOT / "data" / "city_coverage.csv"

OUTPUT_FIELDS = [
    "worker_id",
    "future_live_queue_id",
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
]

FUTURE_LIVE_QUEUE_ID = "COORD-SERIAL150-WAVE2-2026-07-22"
PROHIBITED_TIMEOUT_NAMES = {
    "Bloomington",
    "Oakland",
    "Stockton",
    "Oxnard",
    "Redding",
    "Fairfield",
    "Princeton",
    "Moreno Valley",
}

BATCH_SPECS = {
    "CA": {
        "worker_id": "worker_1",
        "output": ANALYSIS / "wave2_worker_1_ca50_scout_input_2026-07-22.csv",
        "covered_before": 94,
        "claims": (
            "CLM-2026-07-12-03; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-07; H1; H3; H4; H7; H8"
        ),
    },
    "TX": {
        "worker_id": "worker_2",
        "output": ANALYSIS / "wave2_worker_2_tx50_scout_input_2026-07-22.csv",
        "covered_before": 53,
        "claims": (
            "CLM-2026-07-12-02; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-08; H1; H3; H4; H6"
        ),
    },
    "IL": {
        "worker_id": "worker_3",
        "output": ANALYSIS / "wave2_worker_3_il50_scout_input_2026-07-22.csv",
        "covered_before": 74,
        "claims": (
            "CLM-2026-07-12-01; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-06; "
            "CLM-2026-07-12-07; H1; H2; H3; H4; H5; H7"
        ),
    },
}

EXPECTED_NAMES = {
    "CA": [
        "Folsom", "Whittier", "Hawthorne", "Livermore", "Newport Beach",
        "Rancho Cordova", "Buena Park", "Mountain View", "Redwood City",
        "Perris", "Alhambra", "Upland", "Lakewood", "Tustin", "Napa",
        "Milpitas", "Chino Hills", "Pittsburg", "Alameda", "Bellflower",
        "Apple Valley", "Pleasanton", "Rocklin", "Lake Elsinore", "Redlands",
        "Turlock", "Tulare", "Eastvale", "Camarillo", "Walnut Creek",
        "Dublin", "Baldwin Park", "Yuba City", "Madera", "Redondo Beach",
        "Lodi", "Yorba Linda", "Union City", "Brentwood", "Lynwood",
        "South San Francisco", "Laguna Niguel", "Porterville", "San Clemente",
        "Santa Cruz", "Woodland", "La Habra", "Encinitas", "La Mesa",
        "Montebello",
    ],
    "TX": [
        "Cedar Park", "Missouri City", "San Marcos", "Harlingen",
        "North Richland Hills", "Rowlett", "Victoria", "Pflugerville", "Kyle",
        "Wylie", "Euless", "Little Elm", "Texas City", "DeSoto", "Port Arthur",
        "Burleson", "Galveston", "Rockwall", "Grapevine", "Huntsville",
        "Cedar Hill", "Bedford", "Sherman", "Waxahachie", "Keller",
        "The Colony", "Haltom City", "Celina", "Schertz", "Weslaco",
        "Fulshear", "Prosper", "Coppell", "Midlothian", "Rosenberg",
        "Friendswood", "Lancaster", "Hurst", "Duncanville", "Hutto",
        "Copperas Cove", "Socorro", "Weatherford", "La Porte", "Farmers Branch",
        "San Juan", "Cibolo", "Cleburne", "Seguin", "Texarkana",
    ],
    "IL": [
        "Cicero", "Bartlett", "Carol Stream", "Hanover Park", "Addison",
        "Woodridge", "Glendale Heights", "Gurnee", "Algonquin", "Niles",
        "Lake in the Hills", "Glen Ellyn", "Huntley", "McHenry", "Burbank",
        "New Lenox", "Lansing", "Wilmette", "Round Lake Beach", "Vernon Hills",
        "Lockport", "Oak Forest", "Chicago Heights", "Woodstock", "West Chicago",
        "Yorkville", "Homer Glen", "South Elgin", "Zion", "Morton Grove",
        "Westmont", "Collinsville", "Melrose Park", "Elmwood Park", "Lisle",
        "Maywood", "Machesney Park", "Roselle", "Bloomingdale", "Montgomery",
        "Villa Park", "Darien", "Blue Island", "Geneva", "Grayslake",
        "Frankfort", "Park Forest", "South Holland", "Dolton", "Libertyville",
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalized_place(state: str, name: str) -> tuple[str, str]:
    return state.strip().upper(), " ".join(name.strip().casefold().split())


def county_context(rows: list[dict[str, str]]) -> str:
    return " | ".join(
        (
            f'{row["county_name"]} [{row["county_geoid"]}; '
            f'{row["county_equivalent_type"]}; '
            f'government-units-primary={row["is_government_units_primary_county"]}; '
            f'basis={row["relationship_basis"]}]'
        )
        for row in sorted(rows, key=lambda item: item["county_geoid"])
    )


def selection_bucket(rank: int) -> str:
    if rank <= 10:
        return "largest_remaining_place_employer"
    if rank <= 25:
        return "high_population_place_expansion"
    if rank <= 40:
        return "regional_municipal_employer_expansion"
    return "smaller_place_employer_diversity"


def selection_reason(state: str, row: dict[str, str], rank: int, covered: int) -> str:
    population = f'{int(row["population"]):,}'
    label = {
        "CA": "high-yield California expansion",
        "TX": "Texas institutional and municipal-employer contrast",
        "IL": "high-yield Illinois municipal labor-relations expansion",
    }[state]
    return (
        f'Population-ranked eligible {row["political_description"].lower()} employer '
        f'({population}; batch rank {rank}) for {label}, after excluding {covered} '
        "successfully scout-covered municipalities, all current failure-only rows, "
        "queue/canonical overlap, and prohibited employer types."
    )


def expected_units(state: str) -> str:
    base = (
        "municipal police; municipal fire only when the exact target municipality is "
        "the employer; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library); public arbitration, "
        "factfinding, impasse, compensation-plan, or other authoritative wage-setting "
        "material when available; prioritize mutually overlapping 2014-2024 cycles"
    )
    if state == "TX":
        return (
            base
            + "; if no ordinary non-safety CBA exists, return no qualifying CBA rather "
            "than substituting an advisory, school, county, authority, or private source"
        )
    return base


def verification_note(row: dict[str, str], context: str) -> str:
    return (
        f'Scout-stage only. Target exactly {row["government_name"]} (Census government '
        f'ID {row["census_gov_id"]}; internal municipality ID '
        f'{row["municipality_id"]}). County context: {context}. Exclude counties, school '
        "districts, transit agencies, port/airport authorities, housing authorities, "
        "park districts, township governments, industrial districts, fire/water/utility "
        "and other special districts, regional bodies, universities, state/federal "
        "employers, and private providers. If safety service is supplied by another "
        "employer, do not attribute that unit to the municipality. A safety agreement "
        "cannot satisfy the non-safety request. Do not make or recommend a public-records "
        "request. Allow an empty candidate list. Apply exact employer, unit, cycle, and "
        "duplicate controls; do not invent or repeat a known source. No source URL was "
        "opened during selection. Later verification—not this scout—must confirm employer, "
        "unit, provenance, execution/completeness, visible 2014-2024 dates, wage content, "
        "duplicates, access, and mutual cycle overlap."
    )


def build() -> dict[str, list[dict[str, str]]]:
    universe = read_csv(UNIVERSE_PATH)
    coverage = {row["municipality_id"]: row for row in read_csv(COVERAGE_PATH)}
    queue_rows = read_csv(QUEUE_PATH)
    queue_ids = {row["municipality_id"] for row in queue_rows if row["municipality_id"]}
    queue_places = {
        normalized_place(row["state"], row["municipality"]) for row in queue_rows
    }
    canonical_places = {
        normalized_place(row["state"], row["city_name"])
        for row in read_csv(CONTRACTS_PATH)
    }
    canonical_places.update(
        normalized_place(row["state"], row["city_name"])
        for row in read_csv(CITY_COVERAGE_PATH)
        if row.get("have_contract") == "1"
    )
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK_PATH):
        crosswalk[row["municipality_id"]].append(row)

    assert len(universe) == 35_589
    assert len(coverage) == 35_589
    assert len(queue_rows) == 786
    assert set(coverage) == {row["municipality_id"] for row in universe}

    built: dict[str, list[dict[str, str]]] = {}
    all_selected_ids: set[str] = set()
    all_selected_census_ids: set[str] = set()
    for state, spec in BATCH_SPECS.items():
        eligible = []
        for row in universe:
            if row["state"] != state:
                continue
            status = coverage[row["municipality_id"]]
            place_key = normalized_place(state, row["municipality"])
            if not (
                row["government_type"] == "municipal"
                and row["geography_type"] == "place"
                and row["active_status"] == "Y"
                and row["already_in_corpus"] != "yes"
                and status["already_in_corpus"] != "yes"
                and status["scout_coverage_status"] == "not_scouted"
                and status["failed_connection_attempt_count"] == "0"
                and status["queue_status"] == "not_scouted"
                and status["canonical_overlap_status"]
                == "not_already_ingested_canonical"
                and row["municipality_id"] not in queue_ids
                and place_key not in queue_places
                and place_key not in canonical_places
                and row["municipality"] not in PROHIBITED_TIMEOUT_NAMES
            ):
                continue
            eligible.append(row)

        eligible.sort(
            key=lambda row: (
                -int(row["population"] or 0),
                row["municipality"],
                row["municipality_id"],
            )
        )
        selected = eligible[:50]
        assert [row["municipality"] for row in selected] == EXPECTED_NAMES[state]

        output_rows: list[dict[str, str]] = []
        for rank, row in enumerate(selected, start=1):
            municipality_id = row["municipality_id"]
            county_rows = crosswalk[municipality_id]
            assert county_rows
            assert len(county_rows) == int(row["county_relationship_count"])
            assert {item["census_gov_id"] for item in county_rows} == {
                row["census_gov_id"]
            }
            assert municipality_id not in all_selected_ids
            assert row["census_gov_id"] not in all_selected_census_ids
            context = county_context(county_rows)
            output_rows.append(
                {
                    "worker_id": spec["worker_id"],
                    "future_live_queue_id": FUTURE_LIVE_QUEUE_ID,
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
                    "county_context_summary": context,
                    "priority_rank": str(rank),
                    "selection_bucket": selection_bucket(rank),
                    "selection_reason": selection_reason(
                        state, row, rank, spec["covered_before"]
                    ),
                    "claim_or_source_need_connection": spec["claims"],
                    "expected_units_to_search": expected_units(state),
                    "verification_notes": verification_note(row, context),
                    "recommended_scout_status": (
                        "locked_for_wave2_worker_prep_dry_run_only"
                    ),
                    "already_scouted_status": "no",
                    "coverage_status_before_run": "not_scouted",
                }
            )
            all_selected_ids.add(municipality_id)
            all_selected_census_ids.add(row["census_gov_id"])

        assert len(output_rows) == 50
        assert len({row["municipality_id"] for row in output_rows}) == 50
        assert len({row["census_gov_id"] for row in output_rows}) == 50
        assert {row["worker_id"] for row in output_rows} == {spec["worker_id"]}
        assert {row["future_live_queue_id"] for row in output_rows} == {
            FUTURE_LIVE_QUEUE_ID
        }
        assert {row["coverage_status_before_run"] for row in output_rows} == {
            "not_scouted"
        }
        built[state] = output_rows

    assert len(all_selected_ids) == 150
    assert len(all_selected_census_ids) == 150
    return built


def write_outputs(built: dict[str, list[dict[str, str]]]) -> None:
    for state, rows in built.items():
        path = BATCH_SPECS[state]["output"]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        with path.open(newline="", encoding="utf-8") as handle:
            parsed = list(csv.DictReader(handle))
        assert list(parsed[0]) == OUTPUT_FIELDS
        assert parsed == rows
        print(f"Wrote {len(rows)} rows: {path.relative_to(ROOT)}")


def main() -> int:
    built = build()
    write_outputs(built)
    print(
        "PASS: Wave 2 has 150 unique eligible municipal/place employers across "
        "CA, TX, and IL"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
