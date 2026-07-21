#!/usr/bin/env python3
"""Build the locked third 25-municipality Illinois scout input.

This local-only builder reads the authoritative municipality universe, current
scout-coverage ledger, county crosswalk, national manifest, both prior Illinois
inputs, and scout queue. It does not open source URLs, call a model/API, verify
sources, ingest documents, or change canonical data.
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
PRIOR_IL25 = DOCS / "national_batch01_il25_scout_input_2026-07-20.csv"
PRIOR_IL25_2 = DOCS / "national_batch01_il25_2_scout_input_2026-07-20.csv"
OUTPUT = DOCS / "national_batch01_il25_3_scout_input_2026-07-20.csv"

WAVE_ID = "IL25.3-2026-07-20"

FIELDS = [
    "wave_id",
    "priority_rank",
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
    "selection_bucket",
    "selection_reason",
    "claim_or_source_need_connection",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
    "already_scouted_status",
    "coverage_status_before_run",
    "scout_purpose",
    "anchor_cycle",
    "known_source_cycle_exclusions",
    "known_source_notes",
    "known_source_urls",
]


SELECTION = [
    (
        "Lombard",
        "large_city_state_anchor",
        "Largest untouched Illinois city/village municipal employer after IL25 and IL25.2; adds a third-tier DuPage comparison.",
    ),
    (
        "Buffalo Grove",
        "large_city_state_anchor",
        "Large Cook/Lake village selected for a multi-county municipal-employer and suburban labor-market contrast.",
    ),
    (
        "Park Ridge",
        "large_city_state_anchor",
        "Large Cook County city selected as an independent municipal employer near Chicago and the airport employment corridor.",
    ),
    (
        "Streamwood",
        "large_city_state_anchor",
        "Large northwest Cook County village selected to extend suburban scale and employer variation beyond IL25.2.",
    ),
    (
        "Wheeling",
        "large_city_state_anchor",
        "Large Cook/Lake village selected for multi-county context and police/fire/civilian discovery potential.",
    ),
    (
        "Calumet City",
        "mid_city_comparison_candidate",
        "Medium-large south Cook County city selected for an industrial-border municipal labor-market comparison.",
    ),
    (
        "Northbrook",
        "mid_city_comparison_candidate",
        "Medium-large north Cook County village selected as a clean independent municipal-employer comparison.",
    ),
    (
        "St. Charles",
        "mid_city_comparison_candidate",
        "Medium Fox River city spanning Kane and DuPage context, selected as a distinct employer from Aurora, Elgin, and Batavia.",
    ),
    (
        "Mundelein",
        "mid_city_comparison_candidate",
        "Medium Lake County village selected to broaden the state's northern municipal-labor comparison tier.",
    ),
    (
        "Elk Grove Village",
        "mid_city_comparison_candidate",
        "Medium Cook/DuPage village selected for a multi-county municipal and major employment-center contrast.",
    ),
    (
        "North Chicago",
        "mid_city_comparison_candidate",
        "Medium Lake County city selected for a distinct municipal employer in a federal-installation labor-market setting without substituting the federal employer.",
    ),
    (
        "Highland Park",
        "mid_city_comparison_candidate",
        "Medium Lake County city selected for north-shore municipal-employer and wage-setting contrast.",
    ),
    (
        "Batavia",
        "regional_diversity_candidate",
        "Kane/DuPage city selected to extend Fox River coverage while preserving a separate municipal employer.",
    ),
    (
        "Edwardsville",
        "regional_diversity_candidate",
        "Madison County city and county-seat setting selected for Metro East administrative and labor-market variation.",
    ),
    (
        "Belvidere",
        "regional_diversity_candidate",
        "Boone County city selected for northwest Illinois industrial and county-seat comparison value.",
    ),
    (
        "Kankakee",
        "regional_diversity_candidate",
        "Kankakee County city and regional center selected outside the core Chicago suburban employer tier.",
    ),
    (
        "Ottawa",
        "regional_diversity_candidate",
        "LaSalle County city and regional administrative center selected for north-central Illinois diversity.",
    ),
    (
        "Jacksonville",
        "regional_diversity_candidate",
        "Morgan County city selected for a smaller west-central regional-center and municipal-employer comparison.",
    ),
    (
        "Marion",
        "regional_diversity_candidate",
        "Williamson County city selected to add southern Illinois coverage and geographic contrast.",
    ),
    (
        "East Peoria",
        "continuity_with_il25_candidate",
        "Independent Tazewell County city selected alongside IL25 Peoria without transferring any source or verification status.",
    ),
    (
        "East Moline",
        "continuity_with_il25_candidate",
        "Independent Rock Island County city selected to extend the IL25 Moline and IL25.2 Rock Island comparison.",
    ),
    (
        "Sycamore",
        "continuity_with_il25_2_candidate",
        "Independent DeKalb County city selected alongside IL25.2 DeKalb for regional continuity without source-status transfer.",
    ),
    (
        "Alton",
        "continuity_with_il25_2_candidate",
        "Independent Madison County city selected alongside IL25.2 Granite City and the broader Metro East comparison.",
    ),
    (
        "Rolling Meadows",
        "clean_municipal_employer_candidate",
        "Smaller Cook County city selected as a clean municipal-employer and scale contrast within the northwest suburbs.",
    ),
    (
        "Mattoon",
        "clean_municipal_employer_candidate",
        "Smaller Coles County city selected for an east-central municipal-employer and scale contrast.",
    ),
]

EXPECTED_BUCKETS = {
    "large_city_state_anchor": 5,
    "mid_city_comparison_candidate": 7,
    "regional_diversity_candidate": 7,
    "continuity_with_il25_candidate": 2,
    "continuity_with_il25_2_candidate": 2,
    "clean_municipal_employer_candidate": 2,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def county_summary(rows: list[dict[str, str]]) -> str:
    rendered = []
    for row in sorted(rows, key=lambda value: value["county_geoid"]):
        primary = "yes" if row["is_government_units_primary_county"] == "yes" else "no"
        rendered.append(
            f"{row['county_name']} [{row['county_geoid']}; "
            f"{row['county_equivalent_type']}; government-units-primary={primary}; "
            f"basis={row['relationship_basis']}]"
        )
    return " | ".join(rendered)


def build_rows() -> list[dict[str, str]]:
    universe = read_csv(UNIVERSE)
    coverage = {row["municipality_id"]: row for row in read_csv(COVERAGE)}
    manifest_rows = [row for row in read_csv(MANIFEST) if row["state"] == "IL"]
    queue_ids = {row["municipality_id"] for row in read_csv(QUEUE)}
    prior_il25 = read_csv(PRIOR_IL25)
    prior_il25_2 = read_csv(PRIOR_IL25_2)
    prior_il25_ids = {row["municipality_id"] for row in prior_il25}
    prior_il25_2_ids = {row["municipality_id"] for row in prior_il25_2}
    all_prior_ids = prior_il25_ids | prior_il25_2_ids
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK):
        crosswalk[row["municipality_id"]].append(row)

    if len(prior_il25_ids) != 25 or len(prior_il25_2_ids) != 25:
        raise ValueError("Both prior Illinois inputs must contain 25 distinct municipality IDs")
    if prior_il25_ids & prior_il25_2_ids:
        raise ValueError("IL25 and IL25.2 inputs unexpectedly overlap")
    il25_statuses = Counter(coverage[value]["scout_coverage_status"] for value in prior_il25_ids)
    if il25_statuses != Counter(
        {
            "scouted_with_candidates": 23,
            "scouted_no_candidates": 1,
            "scout_attempt_failed_connection": 1,
        }
    ):
        raise ValueError(f"Unexpected IL25 coverage statuses: {il25_statuses}")
    il25_2_statuses = Counter(
        coverage[value]["scout_coverage_status"] for value in prior_il25_2_ids
    )
    if il25_2_statuses != Counter(
        {"scouted_with_candidates": 22, "scouted_no_candidates": 3}
    ):
        raise ValueError(f"Unexpected IL25.2 coverage statuses: {il25_2_statuses}")
    bloomington = [row for row in prior_il25 if row["municipality"] == "Bloomington"]
    if (
        len(bloomington) != 1
        or coverage[bloomington[0]["municipality_id"]]["scout_coverage_status"]
        != "scout_attempt_failed_connection"
    ):
        raise ValueError("Bloomington is not preserved as the expected failure-only IL25 row")
    if {row["municipality_id"] for row in manifest_rows} - prior_il25_ids:
        raise ValueError("An Illinois manifest row unexpectedly remains outside IL25")

    universe_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        if row["state"] == "IL":
            universe_by_name[row["municipality"]].append(row)

    output: list[dict[str, str]] = []
    for rank, (name, bucket, reason) in enumerate(SELECTION, start=1):
        matches = [
            row
            for row in universe_by_name[name]
            if row["government_type"] == "municipal"
            and row["geography_type"] == "place"
            and row["government_name"].startswith(("CITY OF ", "VILLAGE OF "))
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one IL city/village municipal place for {name}; found {len(matches)}"
            )
        row = matches[0]
        municipality_id = row["municipality_id"]
        status = coverage[municipality_id]
        if municipality_id in prior_il25_ids:
            raise ValueError(f"Selected municipality was already in IL25: {name}")
        if municipality_id in prior_il25_2_ids:
            raise ValueError(f"Selected municipality was already in IL25.2: {name}")
        if status["scout_coverage_status"] != "not_scouted":
            raise ValueError(
                f"Selected municipality is not untouched: {name}={status['scout_coverage_status']}"
            )
        if status["failed_connection_attempt_count"] != "0":
            raise ValueError(f"Selected municipality has a recent failed attempt: {name}")
        if municipality_id in queue_ids:
            raise ValueError(f"Selected municipality already has a queue row: {name}")
        if status["already_in_corpus"] != "no":
            raise ValueError(f"Selected municipality already has canonical corpus context: {name}")

        county_rows = crosswalk[municipality_id]
        if len(county_rows) != int(row["county_relationship_count"]):
            raise ValueError(f"County relationship count mismatch for {name}")
        county_names = "/".join(item["county_name"] for item in county_rows)
        output.append(
            {
                "wave_id": WAVE_ID,
                "priority_rank": str(rank),
                "state": "IL",
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
                "selection_bucket": bucket,
                "selection_reason": reason,
                "claim_or_source_need_connection": (
                    "Illinois third-wave matched-cycle discovery for police/fire versus ordinary "
                    "municipal civilian wage-setting material; extend employer-scale and geographic "
                    "variation after IL25 and IL25.2."
                ),
                "expected_units_to_search": (
                    "police CBA; fire CBA; one ordinary general-municipal non-safety CBA; "
                    "public arbitration/factfinding/impasse or wage-setting mechanism material"
                ),
                "verification_notes": (
                    f"Later verification must confirm exact {row['government_name']} employer and Census ID "
                    f"{row['census_gov_id']}, official/union provenance, visible 2014-2024 operative dates, "
                    f"paid-unit identity, and mutual cycle overlap. Do not substitute {county_names}, school "
                    "districts, transit agencies, housing authorities, park districts, town/township governments, "
                    "fire/water/other special districts, regional bodies, universities, federal installations, "
                    "or private providers. Allow an empty candidate list if no qualifying city-unit source is found."
                ),
                "recommended_scout_status": "ready_for_scout",
                "already_scouted_status": "no",
                "coverage_status_before_run": status["scout_coverage_status"],
                "scout_purpose": "matched_comparison_repair",
                "anchor_cycle": (
                    "No canonical anchor cycle is supplied. Seek visibly supported overlapping 2014-2024 "
                    "police/fire/ordinary-non-safety cycles; label non-overlap or unclear evidence."
                ),
                "known_source_cycle_exclusions": (
                    f"None recorded: no {row['government_name']} canonical contract or national queue candidate "
                    "as of 2026-07-20."
                ),
                "known_source_notes": (
                    f"No canonical or queued {row['government_name']} source/cycle is known locally; "
                    "this is unverified scout-stage matched-set discovery only."
                ),
                "known_source_urls": "",
            }
        )

    if len(output) != 25 or len({row["municipality_id"] for row in output}) != 25:
        raise ValueError("IL25.3 output must contain 25 distinct municipality IDs")
    if {row["municipality_id"] for row in output} & all_prior_ids:
        raise ValueError("IL25.3 unexpectedly overlaps a prior Illinois input")
    if Counter(row["selection_bucket"] for row in output) != Counter(EXPECTED_BUCKETS):
        raise ValueError("IL25.3 selection-bucket counts changed")
    if {row["government_name"].split()[0] for row in output} - {"CITY", "VILLAGE"}:
        raise ValueError("IL25.3 unexpectedly includes a non-city/village employer")
    return output


def main() -> int:
    rows = build_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    parsed = read_csv(OUTPUT)
    if len(parsed) != 25 or list(parsed[0]) != FIELDS:
        raise ValueError("IL25.3 CSV failed parse-back schema/row validation")
    if [row["municipality"] for row in parsed] != [entry[0] for entry in SELECTION]:
        raise ValueError("IL25.3 CSV order changed on parse-back")
    print(f"rows={len(parsed)}")
    print("municipalities=" + ", ".join(row["municipality"] for row in parsed))
    print(
        "selection_buckets="
        + ", ".join(
            f"{bucket}:{count}"
            for bucket, count in sorted(
                Counter(row["selection_bucket"] for row in parsed).items()
            )
        )
    )
    print(f"output={OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
