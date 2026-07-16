#!/usr/bin/env python3
"""Build the bounded 2026-07-16 next-wave municipality scout manifest.

This script is selection/accounting only. It reads the authoritative national
municipality universe and full municipality-county crosswalk. It does not run a
scout, verify a source, ingest a document, or change any workflow status.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "docs" / "analysis"
UNIVERSE_PATH = ANALYSIS / "national_municipality_universe.csv"
CROSSWALK_PATH = ANALYSIS / "national_municipality_county_crosswalk.csv"
SOURCE_TARGETS_PATH = ANALYSIS / "national_source_targets_2026-07-12.csv"
OUTPUT_PATH = ANALYSIS / "next_wave_municipality_scout_manifest_2026-07-16.csv"

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
    "already_scouted",
    "scout_positive_status",
    "already_in_corpus",
    "selection_bucket",
    "selection_reason",
    "claim_or_source_need_connection",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
]

# Ordered deliberately. Each tuple is (state, municipality label in the
# authoritative universe, expected government type, selection bucket).
TARGETS = [
    ("TX", "San Antonio", "municipal", "matched_comparison_repair"),
    ("MA", "Somerville", "municipal", "matched_comparison_repair"),
    ("MA", "Newton", "municipal", "matched_comparison_repair"),
    ("TX", "Austin", "municipal", "matched_comparison_repair"),
    ("NJ", "Newark", "municipal", "matched_comparison_repair"),
    ("MA", "Boston", "municipal", "matched_comparison_repair"),
    ("MA", "Worcester", "municipal", "matched_comparison_repair"),
    ("MA", "Arlington", "township", "matched_comparison_repair"),
    ("MA", "Georgetown", "township", "matched_comparison_repair"),
    ("NJ", "Jersey City", "municipal", "matched_comparison_repair"),
    ("MA", "Franklin", "municipal", "repeat_cycle_claim_anchor"),
    ("MA", "Seekonk", "township", "repeat_cycle_claim_anchor"),
    ("TX", "Houston", "municipal", "repeat_cycle_claim_anchor"),
    ("IL", "Chicago", "municipal", "claim_register_named_target"),
    ("IL", "Aurora", "municipal", "claim_register_named_target"),
    ("IL", "Rockford", "municipal", "claim_register_named_target"),
    ("IL", "Springfield", "municipal", "claim_register_named_target"),
    ("IL", "Naperville", "municipal", "claim_register_named_target"),
    ("NY", "Buffalo", "municipal", "claim_register_named_target"),
    ("NY", "Rochester", "municipal", "claim_register_named_target"),
    ("NY", "Syracuse", "municipal", "claim_register_named_target"),
    ("NY", "Yonkers", "municipal", "claim_register_named_target"),
    ("NY", "Albany", "municipal", "claim_register_named_target"),
    ("NJ", "Camden", "municipal", "claim_register_named_target"),
    ("CA", "Los Angeles", "municipal", "claim_register_named_target"),
    ("CA", "Sacramento", "municipal", "claim_register_named_target"),
    ("WA", "Seattle", "municipal", "claim_register_named_target"),
    ("OR", "Portland", "municipal", "claim_register_named_target"),
    ("CT", "Hartford", "municipal", "claim_register_named_target"),
    ("MN", "Minneapolis", "municipal", "claim_register_named_target"),
    ("WI", "Madison", "municipal", "claim_register_named_target"),
    ("MD", "Baltimore", "municipal", "claim_register_named_target"),
    ("CO", "Denver", "municipal", "claim_register_named_target"),
    ("TX", "Dallas", "municipal", "institutional_regime_contrast"),
    ("TX", "Fort Worth", "municipal", "institutional_regime_contrast"),
    ("TX", "El Paso", "municipal", "institutional_regime_contrast"),
    ("TX", "Arlington", "municipal", "institutional_regime_contrast"),
    ("TX", "Corpus Christi", "municipal", "institutional_regime_contrast"),
    ("FL", "Jacksonville", "municipal", "institutional_regime_contrast"),
    ("FL", "Miami", "municipal", "institutional_regime_contrast"),
    ("FL", "Tampa", "municipal", "institutional_regime_contrast"),
    ("FL", "Orlando", "municipal", "institutional_regime_contrast"),
    ("FL", "Tallahassee", "municipal", "institutional_regime_contrast"),
    ("FL", "St. Petersburg", "municipal", "institutional_regime_contrast"),
    ("NC", "Charlotte", "municipal", "institutional_regime_contrast"),
    ("NC", "Raleigh", "municipal", "institutional_regime_contrast"),
    ("NC", "Greensboro", "municipal", "institutional_regime_contrast"),
    ("NC", "Durham", "municipal", "institutional_regime_contrast"),
    ("NC", "Winston-Salem", "municipal", "institutional_regime_contrast"),
    ("NC", "Asheville", "municipal", "institutional_regime_contrast"),
    ("TN", "Nashville-Davidson County", "municipal", "institutional_regime_contrast"),
    ("TN", "Memphis", "municipal", "institutional_regime_contrast"),
    ("TN", "Knoxville", "municipal", "institutional_regime_contrast"),
    ("TN", "Chattanooga", "municipal", "institutional_regime_contrast"),
    ("TN", "Clarksville", "municipal", "institutional_regime_contrast"),
    ("WI", "Milwaukee", "municipal", "institutional_regime_contrast"),
    ("WI", "Green Bay", "municipal", "institutional_regime_contrast"),
    ("WI", "Racine", "municipal", "institutional_regime_contrast"),
    ("WI", "Kenosha", "municipal", "institutional_regime_contrast"),
    ("NV", "Las Vegas", "municipal", "institutional_regime_contrast"),
    ("NV", "Reno", "municipal", "institutional_regime_contrast"),
    ("NV", "Carson", "municipal", "institutional_regime_contrast"),
    ("NJ", "Edison", "township", "within_state_replication"),
    ("NJ", "Woodbridge", "township", "within_state_replication"),
    ("NJ", "Lakewood", "township", "within_state_replication"),
    ("NJ", "Hoboken", "municipal", "within_state_replication"),
    ("NJ", "Atlantic City", "municipal", "within_state_replication"),
    ("IL", "Peoria", "municipal", "within_state_replication"),
    ("IL", "Elgin", "municipal", "within_state_replication"),
    ("IL", "Joliet", "municipal", "within_state_replication"),
    ("IL", "Champaign", "municipal", "within_state_replication"),
    ("IL", "Decatur", "municipal", "within_state_replication"),
    ("NY", "New York", "municipal", "within_state_replication"),
    ("NY", "Utica", "municipal", "within_state_replication"),
    ("NY", "Schenectady", "municipal", "within_state_replication"),
    ("NY", "White Plains", "municipal", "within_state_replication"),
    ("NY", "New Rochelle", "municipal", "within_state_replication"),
    ("CT", "New Haven", "municipal", "within_state_replication"),
    ("CT", "Bridgeport", "municipal", "within_state_replication"),
    ("CT", "Stamford", "municipal", "within_state_replication"),
    ("CT", "Waterbury", "municipal", "within_state_replication"),
    ("RI", "Providence", "municipal", "within_state_replication"),
    ("RI", "Warwick", "municipal", "within_state_replication"),
    ("RI", "Cranston", "municipal", "within_state_replication"),
    ("MN", "St. Paul", "municipal", "within_state_replication"),
    ("MN", "Duluth", "municipal", "within_state_replication"),
    ("MN", "Rochester", "municipal", "within_state_replication"),
    ("MN", "Bloomington", "municipal", "within_state_replication"),
    ("WA", "Tacoma", "municipal", "within_state_replication"),
    ("WA", "Spokane", "municipal", "within_state_replication"),
    ("WA", "Olympia", "municipal", "within_state_replication"),
    ("OR", "Eugene", "municipal", "within_state_replication"),
    ("OR", "Salem", "municipal", "within_state_replication"),
    ("OR", "Bend", "municipal", "within_state_replication"),
    ("CA", "San Diego", "municipal", "within_state_replication"),
    ("CA", "San Francisco", "municipal", "within_state_replication"),
    ("CA", "Fresno", "municipal", "within_state_replication"),
    ("MD", "Annapolis", "municipal", "population_admin_anchor"),
    ("CO", "Colorado Springs", "municipal", "population_admin_anchor"),
    ("DC", "Washington", "municipal", "population_admin_anchor"),
]

REPAIR_DETAILS = {
    ("TX", "San Antonio"): (
        "Urgent named gap: find an ordinary civilian comparison pathway or document its institutional non-availability; do not spend the wave rediscovering the existing safety contracts.",
        "CLM-2026-07-12-02; CLM-2026-07-12-06; CLM-2026-07-12-07; CLM-2026-07-12-08; H5; H6",
        "ordinary general-municipal non-safety unit or authoritative civilian wage-setting pathway (clerical_admin/public_works/sanitation); comparator or wage-study material",
    ),
    ("MA", "Somerville"): (
        "Repair a safety-only corpus city by locating an overlapping ordinary non-safety agreement; this is also the corpus's strongest current comparator-evidence anchor.",
        "CLM-2026-07-12-03; CLM-2026-07-12-06; CLM-2026-07-12-07; H5; H8",
        "ordinary non-safety unit in an overlapping cycle (clerical_admin/public_works/library); comparator or impasse material",
    ),
    ("MA", "Newton"): (
        "Repair a safety-only corpus city by locating an overlapping ordinary non-safety agreement.",
        "CLM-2026-07-12-03; CLM-2026-07-12-06; H8",
        "ordinary non-safety unit in an overlapping cycle (clerical_admin/public_works/library)",
    ),
    ("TX", "Austin"): (
        "Replace the current safety-adjacent EMS comparison with an ordinary general-municipal comparator.",
        "CLM-2026-07-12-02; CLM-2026-07-12-04; CLM-2026-07-12-08; H1; H3; H4; H6",
        "ordinary general-municipal non-safety unit distinct from EMS (clerical_admin/public_works/sanitation)",
    ),
    ("NJ", "Newark"): (
        "Find a current fire leg overlapping Newark's existing police/non-safety cycle so the design becomes a genuine triad.",
        "CLM-2026-07-12-01; CLM-2026-07-12-04; CLM-2026-07-12-05; CLM-2026-07-12-06; CLM-2026-07-12-07; H1; H2; H3; H4; H5; H7",
        "current fire CBA or award first; then repeat-cycle police and ordinary non-safety sources",
    ),
    ("MA", "Boston"): (
        "Complete the existing matched pair with a fire source, a high-value large-department mechanism test.",
        "CLM-2026-07-12-03; CLM-2026-07-12-04; H4; H8",
        "fire CBA or impasse/arbitration source overlapping the existing pair",
    ),
    ("MA", "Worcester"): (
        "Complete the existing fire/non-safety pair with a police leg; favor a base CBA over another amendment-only document.",
        "CLM-2026-07-12-03; H1; H7; H8",
        "police base CBA in an overlapping cycle; full non-safety base CBA if available",
    ),
    ("MA", "Arlington"): (
        "Complete the exact-cycle fire/public-works pair with police and test the city's currently symmetric impasse pattern.",
        "CLM-2026-07-12-03; CLM-2026-07-12-06; H1; H2; H7; H8",
        "police CBA or formal impasse source overlapping the existing exact-cycle pair",
    ),
    ("MA", "Georgetown"): (
        "Complete the existing matched pair with a fire leg, if a paid or call department has a written agreement.",
        "CLM-2026-07-12-03; H8",
        "fire agreement or authoritative evidence that no municipal fire bargaining agreement exists",
    ),
    ("NJ", "Jersey City"): (
        "Resolve the documented vintage problem by finding current-cycle successors for the known police, fire, and non-safety agreement set.",
        "CLM-2026-07-12-01; CLM-2026-07-12-04; CLM-2026-07-12-05; CLM-2026-07-12-06; CLM-2026-07-12-07; H1; H2; H3; H4; H5; H7",
        "current-cycle police; fire; ordinary non-safety successors; public award/factfinding material",
    ),
}

REPEAT_DETAILS = {
    ("MA", "Franklin"): "CLM-2026-07-12-03; CLM-2026-07-12-04; CLM-2026-07-12-05; H1; H3; H4; H8",
    ("MA", "Seekonk"): "CLM-2026-07-12-03; CLM-2026-07-12-04; CLM-2026-07-12-05; H1; H3; H4; H8",
    ("TX", "Houston"): "CLM-2026-07-12-02; CLM-2026-07-12-04; CLM-2026-07-12-05; CLM-2026-07-12-08; H1; H3; H4; H6",
}

FULL_STATE_TO_ABBR = {
    "New Jersey": "NJ",
    "Illinois": "IL",
    "New York": "NY",
    "California": "CA",
    "Washington": "WA",
    "Oregon": "OR",
    "Connecticut": "CT",
    "Minnesota": "MN",
    "Wisconsin": "WI",
    "Maryland": "MD",
    "Colorado": "CO",
}


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def population_band(value: str) -> str:
    population = int(float(value or 0))
    if population >= 1_000_000:
        return "very-large"
    if population >= 250_000:
        return "large"
    if population >= 75_000:
        return "mid-sized"
    return "small"


def county_context(relationships: list[dict[str, str]]) -> str:
    return " | ".join(
        f"{row['county_name']} [{row['county_geoid']}; {row['county_equivalent_type']}; "
        f"government-units-primary={row['is_government_units_primary_county']}; "
        f"basis={row['relationship_basis']}]"
        for row in sorted(relationships, key=lambda item: item["county_geoid"])
    )


def general_units() -> str:
    return (
        "police; fire; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library); public impasse/arbitration/factfinding "
        "material when available"
    )


def verification_note(universe_row: dict[str, str], state: str) -> str:
    notes = [
        "After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified.",
    ]
    if state == "NJ":
        notes.append("Use the PERC employer index as a verification route, but do not treat an index entry or decision synopsis as the CBA itself.")
    if universe_row["government_type"] == "township":
        notes.append("Confirm the township government—not a same-name city, county, school district, or statistical place—is the employer.")
    if universe_row["multi_county_flag"] == "yes":
        notes.append("Retain every county relationship shown in county_context_summary; do not use a primary-county shortcut.")
    if int(float(universe_row["population"] or 0)) >= 1_000_000:
        notes.append("High-burden large-city review: cap verification to the strongest official/union triad leads before expanding.")
    if int(float(universe_row["population"] or 0)) < 75_000:
        notes.append("Confirm that the government actually has paid public-safety bargaining units; universe inclusion alone does not prove unit availability.")
    return " ".join(notes)


def bucket_fields(
    state: str,
    municipality: str,
    bucket: str,
    source_targets: dict[tuple[str, str], dict[str, str]],
    population: str,
) -> tuple[str, str, str]:
    key = (state, municipality)
    if bucket == "matched_comparison_repair":
        return REPAIR_DETAILS[key]
    if bucket == "repeat_cycle_claim_anchor":
        return (
            f"Add a repeat cycle for the existing {municipality} matched-design anchor instead of accumulating a new safety-only city.",
            REPEAT_DETAILS[key],
            general_units() + "; prioritize a repeat cycle for the already represented units",
        )
    if bucket == "claim_register_named_target":
        target = source_targets[key]
        connection = "; ".join(
            value for value in (target["claim_ids_served"], target["hypotheses_served"]) if value
        )
        return (
            f"Carry forward {target['target_id']}, an explicit {target['target_priority']}-priority national source target; expected value={target['expected_value']} and verification burden={target['expected_burden']}.",
            connection,
            target["desired_source_set"],
        )
    if bucket == "institutional_regime_contrast":
        if state == "NV":
            connection = "CLM-2026-07-12-06; CLM-2026-07-12-07; H2; H5"
            regime_text = "formal-impasse/arbitration distinction and comparator-source contrast"
        else:
            connection = (
                "CLM-2026-07-12-02; CLM-2026-07-12-04; CLM-2026-07-12-05; "
                "CLM-2026-07-12-08; H1; H3; H4; H6"
            )
            regime_text = "specialized or uneven safety-versus-non-safety bargaining-pathway contrast"
        return (
            f"Selected as a {population_band(population)} government for {regime_text}; the classification is a source-planning hypothesis to verify, not a legal finding.",
            connection,
            general_units() + "; if no ordinary non-safety CBA exists, locate the authoritative wage-setting pathway",
        )
    if bucket == "within_state_replication":
        if state in {"NJ", "IL", "NY"}:
            connection = (
                "CLM-2026-07-12-01; CLM-2026-07-12-04; CLM-2026-07-12-05; "
                "CLM-2026-07-12-06; CLM-2026-07-12-07; H1; H2; H3; H4; H5; H7"
            )
        elif state == "CT":
            connection = "CLM-2026-07-12-03; CLM-2026-07-12-06; CLM-2026-07-12-07; H2; H5; H8"
        else:
            connection = (
                "CLM-2026-07-12-03; CLM-2026-07-12-04; CLM-2026-07-12-05; "
                "CLM-2026-07-12-07; H1; H3; H4; H7; H8"
            )
        return (
            f"Add a {population_band(population)} within-state replication around a named claim target so a single flagship city does not stand in for the state's source environment.",
            connection,
            general_units(),
        )
    if bucket == "population_admin_anchor":
        return (
            f"Administrative or geographic anchor selected to preserve institutional diversity; population band={population_band(population)}, but size alone did not determine inclusion.",
            "CLM-2026-07-12-03; CLM-2026-07-12-04; CLM-2026-07-12-05; CLM-2026-07-12-07; H1; H3; H4; H7; H8",
            general_units(),
        )
    raise ValueError(f"Unknown selection bucket: {bucket}")


def write_and_validate(rows: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    parsed = load_csv(OUTPUT_PATH)
    if len(parsed) != 100 or [int(row["priority_rank"]) for row in parsed] != list(range(1, 101)):
        raise ValueError("Manifest must contain ranks 1 through 100 exactly once")
    if len({row["municipality_id"] for row in parsed}) != 100:
        raise ValueError("Manifest municipality_id values are not unique")
    if len({row["census_gov_id"] for row in parsed}) != 100:
        raise ValueError("Manifest census_gov_id values are not unique")
    if any(row["state"] == "PA" for row in parsed):
        raise ValueError("PA carry-forward municipalities must not be re-scouted in this wave")
    if any(row["already_scouted"] != "no" for row in parsed):
        raise ValueError("This manifest intentionally contains new-scout municipalities only")
    if any(row["recommended_scout_status"] != "ready_for_scout" for row in parsed):
        raise ValueError("Unexpected recommended_scout_status")


def main() -> int:
    universe = load_csv(UNIVERSE_PATH)
    crosswalk = load_csv(CROSSWALK_PATH)
    source_target_rows = load_csv(SOURCE_TARGETS_PATH)

    universe_lookup: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in universe:
        universe_lookup[(row["state"], normalize(row["municipality"]), row["government_type"])].append(row)
    crosswalk_by_municipality: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in crosswalk:
        crosswalk_by_municipality[row["municipality_id"]].append(row)
    source_targets = {
        (FULL_STATE_TO_ABBR[row["state"]], row["city"]): row
        for row in source_target_rows
        if row["state"] in FULL_STATE_TO_ABBR
    }

    if len(TARGETS) != 100:
        raise ValueError(f"Expected exactly 100 target specifications, found {len(TARGETS)}")
    rows: list[dict[str, str]] = []
    for rank, (state, municipality, government_type, bucket) in enumerate(TARGETS, start=1):
        matches = universe_lookup[(state, normalize(municipality), government_type)]
        if len(matches) != 1:
            raise ValueError(
                f"Target must match one authoritative government: {state} {municipality} "
                f"{government_type}; matches={len(matches)}"
            )
        source = matches[0]
        relationships = crosswalk_by_municipality[source["municipality_id"]]
        if len(relationships) != int(source["county_relationship_count"]):
            raise ValueError(f"Crosswalk count mismatch for {source['municipality_id']}")
        if {row["census_gov_id"] for row in relationships} != {source["census_gov_id"]}:
            raise ValueError(f"Crosswalk Census ID mismatch for {source['municipality_id']}")
        reason, connection, units = bucket_fields(
            state, source["municipality"], bucket, source_targets, source["population"]
        )
        rows.append(
            {
                "wave_id": f"NWMS-2026-07-16-{((rank - 1) // 25) + 1:02d}",
                "priority_rank": str(rank),
                "state": source["state"],
                "municipality": source["municipality"],
                "municipality_id": source["municipality_id"],
                "census_gov_id": source["census_gov_id"],
                "government_name": source["government_name"],
                "government_type": source["government_type"],
                "geography_type": source["geography_type"],
                "population": source["population"],
                "county_relationship_count": source["county_relationship_count"],
                "multi_county_flag": source["multi_county_flag"],
                "county_context_summary": county_context(relationships),
                "already_scouted": source["already_scouted"],
                "scout_positive_status": source["scout_positive_status"],
                "already_in_corpus": source["already_in_corpus"],
                "selection_bucket": bucket,
                "selection_reason": reason,
                "claim_or_source_need_connection": connection,
                "expected_units_to_search": units,
                "verification_notes": verification_note(source, state),
                "recommended_scout_status": "ready_for_scout",
            }
        )
    write_and_validate(rows)
    print(f"manifest_rows={len(rows)}")
    print(f"states={len({row['state'] for row in rows})}")
    print(f"already_scouted={sum(row['already_scouted'] == 'yes' for row in rows)}")
    print(f"already_in_corpus={sum(row['already_in_corpus'] == 'yes' for row in rows)}")
    print(f"multi_county={sum(row['multi_county_flag'] == 'yes' for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
