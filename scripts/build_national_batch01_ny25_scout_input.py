#!/usr/bin/env python3
"""Build the locked 25-city New York state-scale scout input.

This local-only builder reads the authoritative municipality universe, current
scout-coverage ledger, county crosswalk, national manifest, and scout queue. It
does not open source URLs, call a model/API, verify sources, ingest documents,
or change canonical data.
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
OUTPUT = DOCS / "national_batch01_ny25_scout_input_2026-07-20.csv"

WAVE_ID = "NY25-2026-07-20"

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

# Ordered deliberately: the first five are the next untouched high-priority
# manifest targets; rows 6-10 preserve the manifest's additional NY replication
# cities; rows 11-25 broaden the scan without selecting towns/townships.
SELECTION = [
    (
        "Buffalo",
        "claim_register_anchor",
        "Manifest priority 19 / NST-2026-07-12-016: next untouched high-priority national claim target and a major western-New York municipal employer.",
    ),
    (
        "Rochester",
        "claim_register_anchor",
        "Manifest priority 20 / NST-2026-07-12-017: next untouched high-priority national claim target and a large Finger Lakes municipal employer.",
    ),
    (
        "Syracuse",
        "claim_register_anchor",
        "Manifest priority 21 / NST-2026-07-12-018: next untouched high-priority national claim target and a central-New York municipal anchor.",
    ),
    (
        "Yonkers",
        "claim_register_anchor",
        "Manifest priority 22 / NST-2026-07-12-019: next untouched high-priority national claim target and the largest selected Westchester municipal employer.",
    ),
    (
        "Albany",
        "claim_register_anchor",
        "Manifest priority 23 / NST-2026-07-12-020: next untouched high-priority national claim target and the state-capital municipal employer.",
    ),
    (
        "New York",
        "large_city_state_anchor",
        "Manifest priority 73: the nation's largest municipal employer and a five-borough administrative anchor for within-state replication.",
    ),
    (
        "Utica",
        "mid_city_comparison_candidate",
        "Manifest priority 74: Mohawk Valley city selected as a smaller within-state replication around the five claim anchors.",
    ),
    (
        "Schenectady",
        "mid_city_comparison_candidate",
        "Manifest priority 75: Capital Region industrial city adding an employer distinct from Albany and Troy.",
    ),
    (
        "White Plains",
        "mid_city_comparison_candidate",
        "Manifest priority 76: Westchester administrative center selected for suburban municipal-employer comparison.",
    ),
    (
        "New Rochelle",
        "large_city_state_anchor",
        "Manifest priority 77: large Westchester city providing a second downstate municipal comparison outside New York City.",
    ),
    (
        "Mount Vernon",
        "large_city_state_anchor",
        "Large unscouted Westchester city selected to deepen downstate safety/non-safety comparison without using a town or special district.",
    ),
    (
        "Troy",
        "mid_city_comparison_candidate",
        "Capital Region city selected to compare an independent municipal employer with nearby Albany and Schenectady.",
    ),
    (
        "Niagara Falls",
        "mid_city_comparison_candidate",
        "Western-New York city selected for regional and municipal labor-market contrast with Buffalo.",
    ),
    (
        "Binghamton",
        "mid_city_comparison_candidate",
        "Southern Tier city selected as a medium-scale municipal employer and regional administrative anchor.",
    ),
    (
        "Poughkeepsie",
        "regional_diversity_candidate",
        "Hudson Valley city selected for a smaller single-county municipal-employer comparison.",
    ),
    (
        "Newburgh",
        "regional_diversity_candidate",
        "Hudson Valley city selected for an independent Orange County municipal labor-market setting.",
    ),
    (
        "Middletown",
        "regional_diversity_candidate",
        "Orange County city paired regionally with Newburgh while preserving a separate municipal employer.",
    ),
    (
        "Ithaca",
        "regional_diversity_candidate",
        "Finger Lakes university-region city selected while explicitly excluding university and county substitutes.",
    ),
    (
        "Saratoga Springs",
        "regional_diversity_candidate",
        "Capital District/northern Hudson city selected for a distinct tourism and municipal-administration setting.",
    ),
    (
        "Watertown",
        "regional_diversity_candidate",
        "North Country city selected to extend the batch beyond the major downstate and Thruway labor markets.",
    ),
    (
        "Kingston",
        "regional_diversity_candidate",
        "Mid-Hudson city selected as a smaller independent municipal employer and county-seat comparison.",
    ),
    (
        "Jamestown",
        "clean_municipal_employer_candidate",
        "Smaller western-New York city selected for scale contrast and a potentially clean city-employer boundary.",
    ),
    (
        "Elmira",
        "clean_municipal_employer_candidate",
        "Smaller Southern Tier city selected for scale and geographic contrast with Binghamton.",
    ),
    (
        "Rome",
        "clean_municipal_employer_candidate",
        "Smaller Mohawk Valley city selected as an independent city employer complementing Utica.",
    ),
    (
        "Auburn",
        "clean_municipal_employer_candidate",
        "Smaller central-New York city selected for geographic diversity and a potentially clean city-employer boundary.",
    ),
]

EXPECTED_BUCKETS = {
    "claim_register_anchor": 5,
    "large_city_state_anchor": 3,
    "mid_city_comparison_candidate": 6,
    "regional_diversity_candidate": 7,
    "clean_municipal_employer_candidate": 4,
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
    manifest = {row["municipality_id"]: row for row in read_csv(MANIFEST)}
    queue_ids = {row["municipality_id"] for row in read_csv(QUEUE)}
    crosswalk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CROSSWALK):
        crosswalk[row["municipality_id"]].append(row)

    universe_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        if row["state"] == "NY":
            universe_by_name[row["municipality"]].append(row)

    output: list[dict[str, str]] = []
    for rank, (name, bucket, reason) in enumerate(SELECTION, start=1):
        matches = [
            row
            for row in universe_by_name[name]
            if row["government_type"] == "municipal"
            and row["geography_type"] == "place"
            and row["government_name"].startswith("CITY OF ")
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one NY municipal place city for {name}; found {len(matches)}")
        row = matches[0]
        municipality_id = row["municipality_id"]
        status = coverage[municipality_id]
        if status["scout_coverage_status"] != "not_scouted":
            raise ValueError(f"Selected municipality is not untouched: {name}={status['scout_coverage_status']}")
        if status["failed_connection_attempt_count"] != "0":
            raise ValueError(f"Selected municipality has a recent failure-only attempt: {name}")
        if municipality_id in queue_ids:
            raise ValueError(f"Selected municipality already has a queue row: {name}")
        if status["already_in_corpus"] != "no":
            raise ValueError(f"Selected municipality already has canonical corpus context: {name}")

        county_rows = crosswalk[municipality_id]
        if len(county_rows) != int(row["county_relationship_count"]):
            raise ValueError(f"County relationship count mismatch for {name}")

        manifest_row = manifest.get(municipality_id)
        if rank <= 10 and manifest_row is None:
            raise ValueError(f"Expected manifest context for selected row {rank}: {name}")
        claim_connection = (
            manifest_row["claim_or_source_need_connection"]
            if manifest_row
            else "State-scale NY safety/non-safety matched-cycle discovery; regional replication for wage-gap and bargaining-mechanism hypotheses."
        )

        county_names = "/".join(item["county_name"] for item in county_rows)
        empty_note = (
            " Allow an empty candidate list if no qualifying city-unit source is found."
            if rank >= 15
            else ""
        )
        output.append(
            {
                "wave_id": WAVE_ID,
                "priority_rank": str(rank),
                "state": "NY",
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
                "claim_or_source_need_connection": claim_connection,
                "expected_units_to_search": (
                    "police CBA; fire CBA; one ordinary general-municipal non-safety CBA; "
                    "public arbitration/factfinding/impasse or wage-setting mechanism material"
                ),
                "verification_notes": (
                    f"Later verification must confirm exact {row['government_name']} employer and Census ID "
                    f"{row['census_gov_id']}, official/union provenance, visible 2014-2024 operative dates, "
                    f"paid-unit identity, and mutual cycle overlap. Do not substitute {county_names}, the "
                    "State of New York, school districts, MTA/transit agencies, housing authorities, park "
                    "districts, town/township governments, fire/water/other special districts, universities, "
                    f"regional bodies, or private providers.{empty_note}"
                ),
                "recommended_scout_status": "ready_for_scout",
                "already_scouted_status": "no",
                "coverage_status_before_run": "not_scouted",
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
        raise ValueError("NY25 output must contain 25 distinct municipality IDs")
    if Counter(row["selection_bucket"] for row in output) != Counter(EXPECTED_BUCKETS):
        raise ValueError("NY25 selection-bucket counts changed")
    if {row["government_name"].split()[0] for row in output} != {"CITY"}:
        raise ValueError("NY25 unexpectedly includes a non-city employer")
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
        raise ValueError("NY25 CSV failed parse-back schema/row validation")
    if [row["municipality"] for row in parsed] != [entry[0] for entry in SELECTION]:
        raise ValueError("NY25 CSV order changed on parse-back")
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
