#!/usr/bin/env python3
"""Build the locked 25-municipality California scout input.

This local-only builder reads the authoritative municipality universe, current
scout-coverage ledger, county crosswalk, national manifest, and national scout
queue. It does not open source URLs, call a model/API, verify sources, ingest
documents, submit public-records requests, or change canonical data.
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
OUTPUT = DOCS / "national_batch01_ca25_scout_input_2026-07-20.csv"

WAVE_ID = "CA25-2026-07-20"

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
        "Los Angeles",
        "claim_register_anchor",
        "Highest-priority California national-manifest anchor and the state's largest municipal employer; central large-city safety-versus-civilian wage-setting contrast.",
    ),
    (
        "Sacramento",
        "claim_register_anchor",
        "California capital and national-manifest anchor; adds state-administrative and large municipal-employer context without substituting state or county units.",
    ),
    (
        "San Diego",
        "claim_register_anchor",
        "National-manifest anchor and major southern California full-service city with strong police/fire/civilian comparison relevance.",
    ),
    (
        "San Francisco",
        "claim_register_anchor",
        "National-manifest anchor and California's consolidated city-and-county municipal structure; retained only for the exact City and County employer.",
    ),
    (
        "Fresno",
        "claim_register_anchor",
        "National-manifest anchor and Central Valley regional center selected for a large inland municipal labor-market contrast.",
    ),
    (
        "San Jose",
        "large_city_state_anchor",
        "Largest untouched Bay Area city and major technology-region municipal employer with high-value safety/non-safety comparability.",
    ),
    (
        "Long Beach",
        "large_city_state_anchor",
        "Large Los Angeles County city selected as an independent municipal employer; port and school employers are explicit exclusions.",
    ),
    (
        "Oakland",
        "large_city_state_anchor",
        "Large East Bay municipal employer selected for public-safety wage-setting and ordinary civilian comparison relevance.",
    ),
    (
        "Bakersfield",
        "large_city_state_anchor",
        "Large inland Kern County city selected for geographic, industry, and municipal labor-market contrast.",
    ),
    (
        "Anaheim",
        "large_city_state_anchor",
        "Large Orange County city with an exact city-employer target; county, school, tourism/private, and authority substitutes are excluded.",
    ),
    (
        "Riverside",
        "large_city_state_anchor",
        "Large Inland Empire city and county-seat setting selected for municipal-scale and regional wage-setting variation.",
    ),
    (
        "Stockton",
        "large_city_state_anchor",
        "Large San Joaquin Valley/Delta city selected for fiscal, safety-labor, and ordinary municipal comparator relevance.",
    ),
    (
        "Chula Vista",
        "mid_city_comparison_candidate",
        "Large secondary San Diego County city selected as an independent full-service municipal-employer comparison.",
    ),
    (
        "Fremont",
        "mid_city_comparison_candidate",
        "Large East Bay city selected for an independent municipal employer and high-income regional labor-market contrast.",
    ),
    (
        "Modesto",
        "mid_city_comparison_candidate",
        "Stanislaus County regional center selected for a Central Valley city-employer comparison distinct from county agencies.",
    ),
    (
        "Oxnard",
        "mid_city_comparison_candidate",
        "Ventura County coastal/industrial city selected for southern coastal regional diversity and municipal-unit comparability.",
    ),
    (
        "Santa Rosa",
        "mid_city_comparison_candidate",
        "North Bay regional center selected for geographic diversity and a distinct city police/fire/civilian wage-setting environment.",
    ),
    (
        "Salinas",
        "mid_city_comparison_candidate",
        "Monterey County regional center selected for agricultural-region labor-market contrast and exact municipal-employer discovery.",
    ),
    (
        "Vallejo",
        "mid_city_comparison_candidate",
        "Solano County city selected for Bay Area fiscal and public-safety labor-mechanism relevance at a medium employer scale.",
    ),
    (
        "Redding",
        "regional_diversity_candidate",
        "Far northern California regional center selected to prevent the batch from concentrating only on coastal metropolitan employers.",
    ),
    (
        "Chico",
        "regional_diversity_candidate",
        "Northern Sacramento Valley city selected for a medium municipal-employer and regional labor-market contrast.",
    ),
    (
        "Visalia",
        "regional_diversity_candidate",
        "Southern Central Valley regional center selected for inland geographic diversity and clean city-employer identity.",
    ),
    (
        "Santa Barbara",
        "regional_diversity_candidate",
        "Central Coast city selected for coastal regional diversity and a medium-scale municipal public-safety/civilian comparison.",
    ),
    (
        "Berkeley",
        "clean_municipal_employer_candidate",
        "Distinct East Bay city employer selected for likely organized police/fire/civilian bargaining material at a smaller scale than Oakland.",
    ),
    (
        "Palo Alto",
        "clean_municipal_employer_candidate",
        "Smaller Santa Clara County city selected for a clean municipal-employer and high-wage regional comparison distinct from San Jose.",
    ),
]

EXPECTED_BUCKETS = {
    "claim_register_anchor": 5,
    "large_city_state_anchor": 7,
    "mid_city_comparison_candidate": 7,
    "regional_diversity_candidate": 4,
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
    manifest_rows = [row for row in read_csv(MANIFEST) if row["state"] == "CA"]
    manifest_ids = {row["municipality_id"] for row in manifest_rows}
    queue_rows = read_csv(QUEUE)
    queue_ids = {row["municipality_id"] for row in queue_rows}
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK):
        crosswalk[row["municipality_id"]].append(row)

    universe_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        if row["state"] == "CA":
            universe_by_name[row["municipality"]].append(row)

    selected_names = {entry[0] for entry in SELECTION}
    selected_universe_rows = [
        row
        for row in universe
        if row["state"] == "CA" and row["municipality"] in selected_names
    ]
    selected_ids = {row["municipality_id"] for row in selected_universe_rows}
    current_statuses = Counter(
        coverage[municipality_id]["scout_coverage_status"]
        for municipality_id in selected_ids
    )
    pre_run_state = current_statuses == Counter({"not_scouted": 25})
    post_run_state = current_statuses == Counter(
        {
            "scouted_with_candidates": 20,
            "scouted_no_candidates": 1,
            "scout_attempt_failed_connection": 4,
        }
    )
    if not (pre_run_state or post_run_state):
        raise ValueError(f"Unexpected CA25 coverage state: {current_statuses}")

    expected_failed_names = {"Oakland", "Stockton", "Oxnard", "Redding"}
    if post_run_state:
        observed_failed_names = {
            row["municipality"]
            for row in selected_universe_rows
            if coverage[row["municipality_id"]]["scout_coverage_status"]
            == "scout_attempt_failed_connection"
        }
        if observed_failed_names != expected_failed_names:
            raise ValueError(
                f"Unexpected CA25 failure-only municipalities: {observed_failed_names}"
            )
        ca_queue_rows = [row for row in queue_rows if row["state"] == "CA"]
        if len(ca_queue_rows) != 64 or {
            row["scout_run_id"] for row in ca_queue_rows
        } != {"ca_2026-07-21_101012"}:
            raise ValueError("Post-run CA queue does not match the recorded CA25 live run")

    output: list[dict[str, str]] = []
    for rank, (name, bucket, reason) in enumerate(SELECTION, start=1):
        matches = [
            row
            for row in universe_by_name[name]
            if row["government_type"] == "municipal"
            and row["geography_type"] == "place"
            and row["government_name"].startswith(("CITY OF ", "CITY AND COUNTY OF "))
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one CA municipal place/city government for {name}; found {len(matches)}"
            )
        row = matches[0]
        municipality_id = row["municipality_id"]
        status = coverage[municipality_id]
        if pre_run_state and status["scout_coverage_status"] != "not_scouted":
            raise ValueError(
                f"Selected municipality is not untouched: {name}={status['scout_coverage_status']}"
            )
        if pre_run_state and status["failed_connection_attempt_count"] != "0":
            raise ValueError(f"Selected municipality has a recent failed attempt: {name}")
        if pre_run_state and municipality_id in queue_ids:
            raise ValueError(f"Selected municipality already has a queue row: {name}")
        if post_run_state:
            expected_failures = "1" if name in expected_failed_names else "0"
            if status["failed_connection_attempt_count"] != expected_failures:
                raise ValueError(
                    f"Unexpected post-run failure count for {name}: "
                    f"{status['failed_connection_attempt_count']}"
                )
        if status["already_in_corpus"] != "no":
            raise ValueError(f"Selected municipality already has canonical corpus context: {name}")

        county_rows = crosswalk[municipality_id]
        if len(county_rows) != int(row["county_relationship_count"]):
            raise ValueError(f"County relationship count mismatch for {name}")
        county_names = "/".join(item["county_name"] for item in county_rows)
        structure_note = (
            " The City and County of San Francisco is the authoritative California consolidated "
            "municipal employer in the universe; exclude every other county or special-district employer."
            if name == "San Francisco"
            else ""
        )
        output.append(
            {
                "wave_id": WAVE_ID,
                "priority_rank": str(rank),
                "state": "CA",
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
                    "California matched-cycle discovery for police/fire versus ordinary municipal "
                    "civilian wage-setting material; test safety/non-safety wage-gap mechanisms "
                    "across coastal/inland, northern/southern, and large/smaller city employers."
                ),
                "expected_units_to_search": (
                    "police CBA; fire CBA; one ordinary general-municipal non-safety CBA such as "
                    "clerical, public works, library, or citywide civilian; public arbitration, "
                    "factfinding, impasse, or other binding wage-setting mechanism material"
                ),
                "verification_notes": (
                    f"Later verification must confirm exact {row['government_name']} employer and Census ID "
                    f"{row['census_gov_id']}, official/union provenance, visible 2014-2024 operative dates, "
                    f"paid-unit identity, execution/completeness, and mutual cycle overlap. Do not substitute "
                    f"{county_names}, school districts, transit agencies, housing authorities, port or airport "
                    "authorities, park/recreation districts, fire/water/utility or other special districts, "
                    "regional bodies, universities, state/federal employers, or private providers. A police, "
                    "fire, EMS, corrections, dispatcher, or other safety agreement cannot serve as the ordinary "
                    "non-safety comparator. Search only public materials; do not make or recommend a CPRA/PRA "
                    "or other public-records request. Allow an empty candidate list if no qualifying city-unit "
                    f"source is found.{structure_note}"
                ),
                "recommended_scout_status": "ready_for_scout",
                "already_scouted_status": "no",
                # Preserve the locked pre-run snapshot even when the builder is
                # rerun after queue/coverage accounting has advanced.
                "coverage_status_before_run": "not_scouted",
                "scout_purpose": "matched_comparison_repair",
                "anchor_cycle": (
                    "No canonical anchor cycle is supplied. Seek visibly supported overlapping 2014-2024 "
                    "police/fire/ordinary-non-safety cycles; label non-overlap or unclear year evidence."
                ),
                "known_source_cycle_exclusions": (
                    f"None recorded: no {row['government_name']} canonical contract or national queue "
                    "candidate as of 2026-07-20."
                ),
                "known_source_notes": (
                    f"No canonical or queued {row['government_name']} source/cycle is known locally; "
                    "duplicate checks remain required against any sources returned within this run."
                ),
                "known_source_urls": "",
            }
        )

    output_ids = {row["municipality_id"] for row in output}
    if len(output) != 25 or len(output_ids) != 25:
        raise ValueError("CA25 output must contain 25 distinct municipality IDs")
    if len({row["census_gov_id"] for row in output}) != 25:
        raise ValueError("CA25 output must contain 25 distinct Census government IDs")
    if manifest_ids - output_ids:
        missing = sorted(manifest_ids - output_ids)
        raise ValueError(f"CA25 omitted California manifest anchors: {missing}")
    if Counter(row["selection_bucket"] for row in output) != Counter(EXPECTED_BUCKETS):
        raise ValueError("CA25 selection-bucket counts changed")
    if {row["government_type"] for row in output} != {"municipal"}:
        raise ValueError("CA25 unexpectedly includes a prohibited government type")
    if {row["geography_type"] for row in output} != {"place"}:
        raise ValueError("CA25 unexpectedly includes a non-place geography")
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
        raise ValueError("CA25 CSV failed parse-back schema/row validation")
    if [row["municipality"] for row in parsed] != [entry[0] for entry in SELECTION]:
        raise ValueError("CA25 CSV order changed on parse-back")
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
