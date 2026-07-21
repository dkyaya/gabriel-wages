#!/usr/bin/env python3
"""Build the locked second 25-municipality Illinois scout input.

This local-only builder reads the authoritative municipality universe, current
scout-coverage ledger, county crosswalk, national manifest, prior IL25 input,
and scout queue. It does not open source URLs, call a model/API, verify sources,
ingest documents, or change canonical data.
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
OUTPUT = DOCS / "national_batch01_il25_2_scout_input_2026-07-20.csv"

WAVE_ID = "IL25.2-2026-07-20"

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

# IL25 already covered the state's largest municipal anchors. This second batch
# deliberately mixes the next tier of municipal employers with regional and
# continuity comparisons while excluding every prior IL25 ID, including the
# failure-only Bloomington row.
SELECTION = [
    (
        "Arlington Heights",
        "large_city_state_anchor",
        "Largest eligible Illinois village after IL25; a substantial Cook County municipal employer for the second state-scale tier.",
    ),
    (
        "Oak Lawn",
        "large_city_state_anchor",
        "Large southwest Cook County village selected for municipal public-safety and ordinary-civilian comparison outside Chicago.",
    ),
    (
        "Berwyn",
        "large_city_state_anchor",
        "Large inner-ring Cook County city adding a dense municipal-employer contrast to the first Illinois batch.",
    ),
    (
        "Mount Prospect",
        "large_city_state_anchor",
        "Large northwest Cook County village selected as a clean municipal employer with likely cross-unit bargaining relevance.",
    ),
    (
        "Wheaton",
        "large_city_state_anchor",
        "Large DuPage County city and county-seat setting selected for administrative importance and suburban labor-market contrast.",
    ),
    (
        "Oak Park",
        "mid_city_comparison_candidate",
        "Medium-large inner-ring village selected to compare an independent municipal employer with nearby Chicago and Berwyn.",
    ),
    (
        "Hoffman Estates",
        "mid_city_comparison_candidate",
        "Medium-large northwest suburban village selected for a multi-county municipal context and cross-unit comparison potential.",
    ),
    (
        "Downers Grove",
        "mid_city_comparison_candidate",
        "Medium-large DuPage village selected as a distinct municipal employer after Naperville and Wheaton.",
    ),
    (
        "Plainfield",
        "mid_city_comparison_candidate",
        "Fast-growing Will/Kendall municipal employer selected to complement Joliet and test suburban matched-cycle availability.",
    ),
    (
        "Glenview",
        "mid_city_comparison_candidate",
        "Medium-large north Cook County village selected for a clean municipal boundary and likely police/fire/civilian comparison value.",
    ),
    (
        "Elmhurst",
        "mid_city_comparison_candidate",
        "DuPage County city selected for a municipal employer comparison between the larger and smaller Illinois tiers.",
    ),
    (
        "Romeoville",
        "mid_city_comparison_candidate",
        "Will County village selected as a separate municipal labor-market comparison near Joliet and Bolingbrook.",
    ),
    (
        "Crystal Lake",
        "regional_diversity_candidate",
        "McHenry County city selected to extend coverage into the outer northwest metropolitan region.",
    ),
    (
        "DeKalb",
        "regional_diversity_candidate",
        "DeKalb County city selected as a regional administrative and university-market setting while excluding university employers.",
    ),
    (
        "Carpentersville",
        "regional_diversity_candidate",
        "Kane County village selected for Fox River corridor diversity and a separate municipal employer from Elgin.",
    ),
    (
        "Oswego",
        "regional_diversity_candidate",
        "Kendall County village selected for outer-suburban growth and a clean municipal-government comparison.",
    ),
    (
        "Pekin",
        "regional_diversity_candidate",
        "Tazewell County city selected for central-Illinois industrial and municipal-administration contrast with Peoria.",
    ),
    (
        "Danville",
        "regional_diversity_candidate",
        "Vermilion County city selected as an eastern-Illinois regional center outside the Chicago metropolitan labor market.",
    ),
    (
        "Granite City",
        "regional_diversity_candidate",
        "Madison County industrial city selected for Metro East geographic and bargaining-institution contrast.",
    ),
    (
        "Urbana",
        "continuity_with_il25_candidate",
        "Municipal counterpart to IL25 Champaign, whose successful scout returned no candidates; selected without treating Champaign's empty result as verification.",
    ),
    (
        "Rock Island",
        "continuity_with_il25_candidate",
        "Independent Rock Island County city selected to extend the IL25 Moline comparison across Quad Cities municipal employers.",
    ),
    (
        "O'Fallon",
        "continuity_with_il25_candidate",
        "St. Clair County city selected to extend the IL25 Belleville comparison within the Metro East municipal labor market.",
    ),
    (
        "Loves Park",
        "continuity_with_il25_candidate",
        "Winnebago County city selected to extend the IL25 Rockford comparison while preserving a separate municipal employer.",
    ),
    (
        "Galesburg",
        "clean_municipal_employer_candidate",
        "Knox County city selected as a smaller western-Illinois municipal employer and scale contrast.",
    ),
    (
        "Freeport",
        "clean_municipal_employer_candidate",
        "Stephenson County city selected as a smaller northwest-Illinois municipal employer beyond the Rockford area.",
    ),
]

EXPECTED_BUCKETS = {
    "large_city_state_anchor": 5,
    "mid_city_comparison_candidate": 7,
    "regional_diversity_candidate": 7,
    "continuity_with_il25_candidate": 4,
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
    prior_rows = read_csv(PRIOR_IL25)
    prior_ids = {row["municipality_id"] for row in prior_rows}
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK):
        crosswalk[row["municipality_id"]].append(row)

    if len(prior_ids) != 25:
        raise ValueError("Prior IL25 input must contain 25 distinct municipality IDs")
    prior_statuses = Counter(coverage[value]["scout_coverage_status"] for value in prior_ids)
    if prior_statuses != Counter(
        {"scouted_with_candidates": 23, "scouted_no_candidates": 1, "scout_attempt_failed_connection": 1}
    ):
        raise ValueError(f"Unexpected prior IL25 coverage statuses: {prior_statuses}")
    bloomington = [row for row in prior_rows if row["municipality"] == "Bloomington"]
    if len(bloomington) != 1 or coverage[bloomington[0]["municipality_id"]]["scout_coverage_status"] != "scout_attempt_failed_connection":
        raise ValueError("Bloomington is not preserved as the expected failure-only IL25 row")
    if {row["municipality_id"] for row in manifest_rows} - prior_ids:
        raise ValueError("An Illinois manifest row unexpectedly remains outside the prior IL25 input")

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
            raise ValueError(f"Expected one IL city/village municipal place for {name}; found {len(matches)}")
        row = matches[0]
        municipality_id = row["municipality_id"]
        status = coverage[municipality_id]
        if municipality_id in prior_ids:
            raise ValueError(f"Selected municipality was already in IL25: {name}")
        if status["scout_coverage_status"] != "not_scouted":
            raise ValueError(f"Selected municipality is not untouched: {name}={status['scout_coverage_status']}")
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
                    "Illinois second-wave matched-cycle discovery for police/fire versus ordinary municipal "
                    "civilian wage-setting material; expand geographic and employer-scale variation after IL25."
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
                    "fire/water/other special districts, regional bodies, universities, or private providers. "
                    "Allow an empty candidate list if no qualifying city-unit source is found."
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
        raise ValueError("IL25.2 output must contain 25 distinct municipality IDs")
    if Counter(row["selection_bucket"] for row in output) != Counter(EXPECTED_BUCKETS):
        raise ValueError("IL25.2 selection-bucket counts changed")
    if {row["government_name"].split()[0] for row in output} - {"CITY", "VILLAGE"}:
        raise ValueError("IL25.2 unexpectedly includes a non-city/village employer")
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
        raise ValueError("IL25.2 CSV failed parse-back schema/row validation")
    if [row["municipality"] for row in parsed] != [entry[0] for entry in SELECTION]:
        raise ValueError("IL25.2 CSV order changed on parse-back")
    print(f"rows={len(parsed)}")
    print("municipalities=" + ", ".join(row["municipality"] for row in parsed))
    print(
        "selection_buckets="
        + ", ".join(
            f"{bucket}:{count}"
            for bucket, count in sorted(Counter(row["selection_bucket"] for row in parsed).items())
        )
    )
    print(f"output={OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
