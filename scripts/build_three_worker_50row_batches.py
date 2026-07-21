#!/usr/bin/env python3
"""Build the locked CA50, NJ50, and TX50 offline worker-preparation inputs.

This builder is local and deterministic. It reads only the committed municipality
universe, scout coverage, candidate queue, strategic manifest, and county
crosswalk. It does not open source URLs, run a scout/model, verify sources, or
modify national queue/coverage outputs.
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
MANIFEST_PATH = ANALYSIS / "next_wave_municipality_scout_manifest_2026-07-16.csv"
CROSSWALK_PATH = ANALYSIS / "national_municipality_county_crosswalk.csv"

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

FUTURE_LIVE_QUEUE_ID = "COORD-SERIAL150-2026-07-21"
PROHIBITED_TIMEOUT_NAMES = {
    "Bloomington",
    "Oakland",
    "Stockton",
    "Oxnard",
    "Redding",
    "Fairfield",
    "Princeton",
}

BATCH_SPECS = {
    "CA": {
        "worker_id": "worker_1",
        "output": ANALYSIS / "worker_1_ca50_scout_input_2026-07-21.csv",
        "claims": (
            "CLM-2026-07-12-03; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-07; H1; H3; H4; H7; H8"
        ),
    },
    "NJ": {
        "worker_id": "worker_2",
        "output": ANALYSIS / "worker_2_nj50_scout_input_2026-07-21.csv",
        "claims": (
            "CLM-2026-07-12-01; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-06; "
            "CLM-2026-07-12-07; H1; H2; H3; H4; H5; H7"
        ),
    },
    "TX": {
        "worker_id": "worker_3",
        "output": ANALYSIS / "worker_3_tx50_scout_input_2026-07-21.csv",
        "claims": (
            "CLM-2026-07-12-02; CLM-2026-07-12-04; "
            "CLM-2026-07-12-05; CLM-2026-07-12-08; H1; H3; H4; H6"
        ),
    },
}

EXPECTED_NAMES = {
    "CA": [
        "Santa Clarita", "San Bernardino", "Fontana", "Moreno Valley",
        "Rancho Cucamonga", "Lancaster", "Palmdale", "Victorville", "Orange",
        "Simi Valley", "Thousand Oaks", "Antioch", "Carlsbad", "Menifee",
        "Murrieta", "Temecula", "Santa Maria", "San Buenaventura (Ventura)",
        "Downey", "Costa Mesa", "Jurupa Valley", "West Covina", "El Monte",
        "Rialto", "El Cajon", "Inglewood", "Burbank", "Vacaville", "San Mateo",
        "Hesperia", "Daly City", "Vista", "Norwalk", "Tracy", "San Marcos",
        "Merced", "Chino", "Indio", "Hemet", "Carson", "Manteca", "Compton",
        "Mission Viejo", "South Gate", "Santa Monica", "Westminster",
        "Citrus Heights", "Lake Forest", "San Leandro", "San Ramon",
    ],
    "NJ": [
        "Westfield", "Englewood", "Bergenfield", "Millville", "Bridgeton",
        "Paramus", "Ridgewood", "Lodi", "Cliffside Park", "Carteret",
        "South Plainfield", "Glassboro", "North Plainfield", "Summit", "Roselle",
        "Lindenwold", "Elmwood Park", "Secaucus", "Pleasantville", "Harrison",
        "Palisades Park", "Hawthorne", "Point Pleasant", "Tinton Falls",
        "Rutherford", "Dover", "Dumont", "New Milford", "Madison",
        "North Arlington", "South River", "Asbury Park", "Phillipsburg", "Tenafly",
        "Metuchen", "Highland Park", "Fairview", "Hammonton", "Ramsey", "Edgewater",
        "Hopatcong", "Middlesex", "Collingswood", "Somerville", "Florham Park",
        "Roselle Park", "Eatontown", "New Providence", "Woodland Park",
        "Ridgefield Park",
    ],
    "TX": [
        "Dallas", "Fort Worth", "El Paso", "Arlington", "Corpus Christi", "Plano",
        "Lubbock", "Laredo", "Irving", "Garland", "Frisco", "McKinney", "Amarillo",
        "Grand Prairie", "Brownsville", "Killeen", "Denton", "Mesquite", "Pasadena",
        "McAllen", "Waco", "Midland", "Lewisville", "Carrollton", "Round Rock",
        "Abilene", "Pearland", "College Station", "Richardson", "League City",
        "Odessa", "Beaumont", "Allen", "New Braunfels", "Tyler", "Sugar Land",
        "Conroe", "Edinburg", "Wichita Falls", "San Angelo", "Georgetown", "Temple",
        "Bryan", "Mission", "Baytown", "Longview", "Pharr", "Leander",
        "Flower Mound", "Mansfield",
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def selection_bucket(state: str, rank: int, manifest_rank: str) -> str:
    if state == "TX" and manifest_rank:
        return "manifest_institutional_regime_contrast"
    if state == "TX":
        return "large_municipal_employer_anchor" if rank <= 20 else "high_value_regional_employer"
    if state == "CA":
        if rank <= 10:
            return "largest_uncovered_city_anchor"
        if rank <= 30:
            return "high_population_city_expansion"
        return "regional_city_employer_expansion"
    if rank <= 15:
        return "largest_uncovered_place_employer"
    if rank <= 35:
        return "mid_size_borough_city_expansion"
    return "regional_place_employer_expansion"


def selection_reason(state: str, row: dict[str, str], rank: int, manifest_rank: str) -> str:
    population = f'{int(row["population"]):,}'
    if state == "TX" and manifest_rank:
        return (
            f'Manifest priority {manifest_rank} and population-ranked high-value Texas '
            f'municipal employer ({population}; batch rank {rank}); selected for the '
            "institutional safety-versus-ordinary-civilian wage-setting contrast."
        )
    if state == "TX":
        return (
            f'Population-ranked high-value Texas municipal employer ({population}; '
            f'batch rank {rank}) extending the five untouched manifest anchors into a '
            "broad large-employer contrast set."
        )
    if state == "NJ":
        return (
            f'Population-ranked untouched New Jersey place government ({population}; '
            f'batch rank {rank}) selected after excluding covered/canonical rows and '
            "township governments."
        )
    return (
        f'Population-ranked untouched California city government ({population}; '
        f'batch rank {rank}) extending coverage beyond the 45 successfully scouted '
        "municipalities while excluding all failure-only rows."
    )


def expected_units(state: str) -> str:
    base = (
        "municipal police; municipal fire only when the exact target municipality is "
        "the employer; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library); public arbitration, "
        "factfinding, impasse, compensation-plan, or other authoritative wage-setting "
        "material when available"
    )
    if state == "TX":
        return base + "; if no ordinary non-safety CBA exists, identify the authoritative civilian wage-setting pathway"
    return base


def verification_note(row: dict[str, str], context: str) -> str:
    return (
        f'Scout-stage only. Target exactly {row["government_name"]} (Census government '
        f'ID {row["census_gov_id"]}). County context: {context}. Exclude counties, school '
        "districts, transit agencies, port/airport authorities, housing authorities, "
        "park districts, township governments, fire/water/utility and other special "
        "districts, regional bodies, universities, state/federal employers, and private "
        "providers. If safety service is supplied by another employer, do not attribute "
        "that unit to the municipality. A safety agreement cannot satisfy the non-safety "
        "request. Do not make or recommend a public-records request. Allow an empty "
        "candidate list. No source URL was opened during selection. Later verification—not "
        "this scout—must confirm employer, unit, provenance, execution/completeness, visible "
        "2014-2024 dates, wage content, duplicates, access, and mutual cycle overlap."
    )


def build() -> dict[str, list[dict[str, str]]]:
    universe = read_csv(UNIVERSE_PATH)
    coverage = {row["municipality_id"]: row for row in read_csv(COVERAGE_PATH)}
    queue_ids = {row["municipality_id"] for row in read_csv(QUEUE_PATH)}
    manifest = {row["municipality_id"]: row for row in read_csv(MANIFEST_PATH)}
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK_PATH):
        crosswalk[row["municipality_id"]].append(row)

    assert len(universe) == 35_589
    assert set(coverage) == {row["municipality_id"] for row in universe}

    built: dict[str, list[dict[str, str]]] = {}
    all_selected_ids: set[str] = set()
    for state, spec in BATCH_SPECS.items():
        eligible = [
            row
            for row in universe
            if row["state"] == state
            and row["government_type"] == "municipal"
            and row["geography_type"] == "place"
            and row["active_status"] == "Y"
            and row["already_in_corpus"] != "yes"
            and coverage[row["municipality_id"]]["scout_coverage_status"] == "not_scouted"
            and row["municipality_id"] not in queue_ids
            and row["municipality"] not in PROHIBITED_TIMEOUT_NAMES
        ]
        eligible.sort(key=lambda row: (-int(row["population"] or 0), row["municipality"]))
        selected = eligible[:50]
        assert [row["municipality"] for row in selected] == EXPECTED_NAMES[state]

        output_rows: list[dict[str, str]] = []
        for rank, row in enumerate(selected, start=1):
            municipality_id = row["municipality_id"]
            county_rows = crosswalk[municipality_id]
            assert county_rows
            assert len(county_rows) == int(row["county_relationship_count"])
            assert {item["census_gov_id"] for item in county_rows} == {row["census_gov_id"]}
            assert municipality_id not in all_selected_ids
            assert coverage[municipality_id]["failed_connection_attempt_count"] == "0"
            assert coverage[municipality_id]["canonical_overlap_status"] == "not_already_ingested_canonical"
            assert coverage[municipality_id]["queue_status"] == "not_scouted"

            manifest_rank = manifest.get(municipality_id, {}).get("priority_rank", "")
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
                    "selection_bucket": selection_bucket(state, rank, manifest_rank),
                    "selection_reason": selection_reason(state, row, rank, manifest_rank),
                    "claim_or_source_need_connection": spec["claims"],
                    "expected_units_to_search": expected_units(state),
                    "verification_notes": verification_note(row, context),
                    "recommended_scout_status": "locked_for_worker_prep_dry_run_only",
                    "already_scouted_status": "no",
                    "coverage_status_before_run": "not_scouted",
                }
            )
            all_selected_ids.add(municipality_id)

        assert len(output_rows) == 50
        assert len({row["municipality_id"] for row in output_rows}) == 50
        assert len({row["census_gov_id"] for row in output_rows}) == 50
        assert {row["worker_id"] for row in output_rows} == {spec["worker_id"]}
        assert {row["future_live_queue_id"] for row in output_rows} == {FUTURE_LIVE_QUEUE_ID}
        built[state] = output_rows

    assert len(all_selected_ids) == 150
    return built


def write_outputs(built: dict[str, list[dict[str, str]]]) -> None:
    for state, rows in built.items():
        path = BATCH_SPECS[state]["output"]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
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
    print("PASS: 150 unique, eligible municipal/place employers across three locked batches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
