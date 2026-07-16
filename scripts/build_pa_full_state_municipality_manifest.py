#!/usr/bin/env python3
"""Build the full Pennsylvania municipality source-scout planning manifest.

This is an accounting and prioritization utility only. It does not run a live
scout, call a model/API, verify a source, ingest a document, or codify text.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "docs" / "analysis"
UNIVERSE_PATH = ANALYSIS / "national_municipality_universe.csv"
CROSSWALK_PATH = ANALYSIS / "national_municipality_county_crosswalk.csv"
SCOUT_COVERAGE_PATH = ANALYSIS / "gabriel_state_source_scout_municipality_coverage.csv"
CITY_COVERAGE_PATH = ROOT / "data" / "city_coverage.csv"
NATIONAL_MANIFEST_PATH = ANALYSIS / "next_wave_municipality_scout_manifest_2026-07-16.csv"
OUTPUT_PATH = ANALYSIS / "pa_full_state_municipality_scout_manifest_2026-07-16.csv"

PLANNING_BATCH_SIZE = 100
RUNNER_SHARD_SIZE = 25

FIELDS = [
    "pa_batch_id",
    "pa_runner_shard_id",
    "pa_priority_rank",
    "state",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "population_year",
    "county_relationship_count",
    "multi_county_flag",
    "county_context_summary",
    "batching_county_geoid",
    "batching_county_name",
    "already_scouted",
    "scout_positive_status",
    "already_in_corpus",
    "already_in_city_coverage",
    "government_website_available",
    "pa_priority_score",
    "pa_priority_tier",
    "selection_reason",
    "expected_units_to_search",
    "verification_notes",
    "recommended_scout_status",
]

POLITICAL_TYPE_POINTS = {
    "CITY": 15,
    "MUNICIPALITY": 12,
    "BOROUGH": 8,
    "TOWN": 8,
    "TOWNSHIP": 5,
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def population_points(population: str) -> int:
    value = int(float(population or 0))
    if value >= 50_000:
        return 50
    if value >= 25_000:
        return 40
    if value >= 10_000:
        return 30
    if value >= 5_000:
        return 20
    if value >= 2_000:
        return 10
    return 0


def population_band(population: str) -> str:
    value = int(float(population or 0))
    if value >= 50_000:
        return "50,000+"
    if value >= 25_000:
        return "25,000-49,999"
    if value >= 10_000:
        return "10,000-24,999"
    if value >= 5_000:
        return "5,000-9,999"
    if value >= 2_000:
        return "2,000-4,999"
    return "under 2,000"


def priority_tier(score: int) -> str:
    if score >= 60:
        return "tier_1_high_plausibility"
    if score >= 45:
        return "tier_2_medium_high_plausibility"
    if score >= 25:
        return "tier_3_systematic_mid_small"
    return "tier_4_small_low_information"


def primary_batching_county(relationships: list[dict[str, str]]) -> dict[str, str]:
    primary = [
        row for row in relationships if row["is_government_units_primary_county"] == "yes"
    ]
    if len(primary) != 1:
        raise ValueError(
            "Expected exactly one Government Units primary/headquarters county for "
            f"{relationships[0]['municipality_id']}; found {len(primary)}"
        )
    return primary[0]


def county_context(relationships: list[dict[str, str]]) -> str:
    return " | ".join(
        f"{row['county_name']} [{row['county_geoid']}; {row['county_equivalent_type']}; "
        f"government-units-primary={row['is_government_units_primary_county']}; "
        f"basis={row['relationship_basis']}]"
        for row in sorted(relationships, key=lambda item: item["county_geoid"])
    )


def priority_score(
    row: dict[str, str],
    relationships: list[dict[str, str]],
    scouted_counties: set[str],
    positive_counties: set[str],
    triad_counties: set[str],
) -> tuple[int, list[str]]:
    county_geoids = {item["county_geoid"] for item in relationships}
    score = population_points(row["population"])
    parts = [f"population band {population_band(row['population'])}"]

    political_points = POLITICAL_TYPE_POINTS.get(row["political_description"], 0)
    score += political_points
    parts.append(f"Census political type {row['political_description'].lower()}")

    if row["government_website"]:
        score += 15
        parts.append("Government Units record supplies an official website")
    else:
        parts.append("no official website is recorded in Government Units")

    if county_geoids & scouted_counties:
        score += 10
        parts.append("shares county context with a previously scouted municipality")
    if county_geoids & positive_counties:
        score += 5
        parts.append("shares county context with a scout-positive municipality")
    if county_geoids & triad_counties:
        score += 5
        parts.append("shares county context with a prior likely-triad scout result")
    if row["multi_county_flag"] == "yes":
        score += 3
        parts.append("multi-county geography adds cross-county coverage value")
    return score, parts


def diversified_tier_order(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Rank by tier, then cycle across primary counties within each tier.

    The primary county is used only as a deterministic batching stratum. Every
    relationship remains present in county_context_summary.
    """
    ordered: list[dict[str, object]] = []
    tier_order = (
        "tier_1_high_plausibility",
        "tier_2_medium_high_plausibility",
        "tier_3_systematic_mid_small",
        "tier_4_small_low_information",
    )
    for tier in tier_order:
        by_county: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            if row["_tier"] == tier:
                by_county[str(row["_batching_county_geoid"])].append(row)
        for county_rows in by_county.values():
            county_rows.sort(
                key=lambda item: (
                    -int(item["_score"]),
                    -int(float(str(item["population"]) or 0)),
                    str(item["municipality"]),
                    str(item["census_gov_id"]),
                )
            )
        while any(by_county.values()):
            cycle = [
                by_county[county_geoid].pop(0)
                for county_geoid in sorted(by_county)
                if by_county[county_geoid]
            ]
            cycle.sort(
                key=lambda item: (
                    -int(item["_score"]),
                    -int(float(str(item["population"]) or 0)),
                    str(item["municipality"]),
                    str(item["census_gov_id"]),
                )
            )
            ordered.extend(cycle)
    if len(ordered) != len(rows):
        raise ValueError("Diversified priority ordering lost or duplicated rows")
    return ordered


def expected_units(row: dict[str, str]) -> str:
    if row["already_scouted"] == "yes":
        return "No default re-scout; verify the existing unverified police/fire/non-safety leads instead."
    return (
        "police; fire; at least one ordinary general-municipal non-safety unit "
        "(clerical_admin/public_works/sanitation/library); public Act 111 award, "
        "factfinding, or impasse material when available"
    )


def verification_notes(row: dict[str, str], relationships: list[dict[str, str]]) -> str:
    if row["already_scouted"] == "yes":
        return (
            "Excluded from default live-scout batches. Review existing scout-stage leads for exact "
            "employer, reachable official/union provenance, 2014-2024 dates, and overlapping "
            "safety/non-safety cycles; do not infer verification from scout positivity."
        )
    notes = [
        "After scouting, verify exact employer, reachable official/union provenance, 2014-2024 dates, and overlapping safety/non-safety cycles before promotion; scout output remains unverified."
    ]
    if row["government_type"] == "township":
        notes.append(
            "Confirm the township government—not a same-name borough/city, county, school district, or statistical place—is the employer."
        )
    if row["multi_county_flag"] == "yes":
        notes.append(
            "Retain all county relationships in county_context_summary; the batching county is only a scheduling stratum."
        )
    if not row["government_website"]:
        notes.append(
            "No official website is recorded in Government Units, so expect lower source-discovery and verification yield."
        )
    if int(float(row["population"] or 0)) < 5_000:
        notes.append(
            "Small-government inclusion does not prove paid police/fire bargaining units; document a legitimate no-unit result rather than inventing a source."
        )
    return " ".join(notes)


def write_and_validate(
    output_rows: list[dict[str, str]],
    pa_universe: list[dict[str, str]],
    crosswalk_by_id: dict[str, list[dict[str, str]]],
) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    parsed = load_csv(OUTPUT_PATH)
    universe_by_id = {row["municipality_id"]: row for row in pa_universe}
    if len(parsed) != len(pa_universe):
        raise ValueError("PA manifest row count does not match PA universe")
    if {row["municipality_id"] for row in parsed} != set(universe_by_id):
        raise ValueError("PA manifest municipality IDs do not exactly match the PA universe")
    if len({row["census_gov_id"] for row in parsed}) != len(parsed):
        raise ValueError("PA manifest Census government IDs are not unique")
    if any(row["state"] != "PA" for row in parsed):
        raise ValueError("PA manifest contains a non-PA row")
    if [int(row["pa_priority_rank"]) for row in parsed] != list(range(1, len(parsed) + 1)):
        raise ValueError("PA priority ranks are not consecutive")

    copied_fields = (
        "state",
        "municipality",
        "census_gov_id",
        "government_name",
        "government_type",
        "geography_type",
        "population",
        "population_year",
        "county_relationship_count",
        "multi_county_flag",
        "already_scouted",
        "scout_positive_status",
        "already_in_corpus",
    )
    for row in parsed:
        source = universe_by_id[row["municipality_id"]]
        for field in copied_fields:
            if row[field] != source[field]:
                raise ValueError(f"Authoritative field drift for {row['municipality_id']} {field}")
        relationships = crosswalk_by_id[row["municipality_id"]]
        if len(relationships) != int(row["county_relationship_count"]):
            raise ValueError(f"Crosswalk count mismatch for {row['municipality_id']}")
        for relationship in relationships:
            if relationship["county_geoid"] not in row["county_context_summary"]:
                raise ValueError(f"Missing county context for {row['municipality_id']}")

    unscouted = [row for row in parsed if row["already_scouted"] == "no"]
    scouted = [row for row in parsed if row["already_scouted"] == "yes"]
    if len(scouted) != 25:
        raise ValueError(f"Expected 25 PA carry-forward scout rows, found {len(scouted)}")
    if any(row["recommended_scout_status"] != "ready_for_scout" for row in unscouted):
        raise ValueError("An unscouted PA row is not ready_for_scout")
    if any(row["recommended_scout_status"] != "excluded_already_scouted" for row in scouted):
        raise ValueError("A scouted PA row is not excluded_already_scouted")
    if any(
        row["pa_batch_id"] != "not_assigned_already_scouted"
        or row["pa_runner_shard_id"] != "not_assigned_already_scouted"
        for row in scouted
    ):
        raise ValueError("An already-scouted PA row was assigned a live-scout batch")

    batch_counts = Counter(row["pa_batch_id"] for row in unscouted)
    shard_counts = Counter(row["pa_runner_shard_id"] for row in unscouted)
    if len(batch_counts) != 26 or sorted(batch_counts.values()) != [32] + [100] * 25:
        raise ValueError(f"Unexpected PA planning batch structure: {batch_counts}")
    if len(shard_counts) != 102 or sorted(shard_counts.values()) != [7] + [25] * 101:
        raise ValueError(f"Unexpected PA runner-shard structure: {shard_counts}")


def main() -> int:
    universe = load_csv(UNIVERSE_PATH)
    crosswalk = load_csv(CROSSWALK_PATH)
    scout_coverage = load_csv(SCOUT_COVERAGE_PATH)
    city_coverage = load_csv(CITY_COVERAGE_PATH)
    national_manifest = load_csv(NATIONAL_MANIFEST_PATH)

    pa_universe = [row for row in universe if row["state"] == "PA"]
    if any(row["state_fips"] != "42" for row in pa_universe):
        raise ValueError("PA universe contains a state-FIPS mismatch")
    crosswalk_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in crosswalk:
        if row["state"] == "PA":
            crosswalk_by_id[row["municipality_id"]].append(row)
    if set(crosswalk_by_id) != {row["municipality_id"] for row in pa_universe}:
        raise ValueError("PA universe and PA crosswalk municipality sets differ")

    scouted_counties: set[str] = set()
    positive_counties: set[str] = set()
    triad_counties: set[str] = set()
    scout_coverage_by_id = {row["municipality_id"]: row for row in scout_coverage}
    for row in pa_universe:
        county_geoids = {
            item["county_geoid"] for item in crosswalk_by_id[row["municipality_id"]]
        }
        if row["already_scouted"] == "yes":
            scouted_counties.update(county_geoids)
        if row["scout_positive_status"] == "yes":
            positive_counties.update(county_geoids)
        coverage = scout_coverage_by_id.get(row["municipality_id"], {})
        if coverage.get("likely_triad") == "yes":
            triad_counties.update(county_geoids)

    city_coverage_ids = {
        row["city_id"]
        for row in city_coverage
        if row["state"] == "PA" and row["have_contract"] == "1"
    }
    missing_coverage_ids = city_coverage_ids - {row["municipality_id"] for row in pa_universe}
    if missing_coverage_ids:
        raise ValueError(f"PA city-coverage IDs missing from universe: {missing_coverage_ids}")

    working: list[dict[str, object]] = []
    carry_forward: list[dict[str, object]] = []
    for source in pa_universe:
        row: dict[str, object] = dict(source)
        relationships = crosswalk_by_id[source["municipality_id"]]
        primary = primary_batching_county(relationships)
        row["_relationships"] = relationships
        row["_batching_county_geoid"] = primary["county_geoid"]
        row["_batching_county_name"] = primary["county_name"]
        row["_already_in_city_coverage"] = (
            "yes" if source["municipality_id"] in city_coverage_ids else "no"
        )
        if source["already_scouted"] == "yes":
            row["_score"] = -1
            row["_tier"] = "carry_forward_already_scouted"
            carry_forward.append(row)
        else:
            score, reason_parts = priority_score(
                source,
                relationships,
                scouted_counties,
                positive_counties,
                triad_counties,
            )
            row["_score"] = score
            row["_tier"] = priority_tier(score)
            row["_reason_parts"] = reason_parts
            working.append(row)

    ordered_unscouted = diversified_tier_order(working)
    carry_forward.sort(
        key=lambda item: (
            -int(float(str(item["population"]) or 0)),
            str(item["municipality"]),
            str(item["census_gov_id"]),
        )
    )
    ordered = ordered_unscouted + carry_forward

    output_rows: list[dict[str, str]] = []
    for rank, item in enumerate(ordered, start=1):
        source = {key: str(value) for key, value in item.items() if not key.startswith("_")}
        relationships = item["_relationships"]
        assert isinstance(relationships, list)
        already_scouted = source["already_scouted"] == "yes"
        if already_scouted:
            batch_id = "not_assigned_already_scouted"
            shard_id = "not_assigned_already_scouted"
            status = "excluded_already_scouted"
            reason = (
                "PA scout carry-forward row; excluded from default live-scout-ready batches because "
                f"already_scouted=yes and scout_positive_status={source['scout_positive_status']}. "
                "No municipality-specific retest is justified in this plan; verify existing leads first."
            )
        else:
            operational_rank = rank
            batch_id = f"PA-FULL-2026-07-16-B{((operational_rank - 1) // PLANNING_BATCH_SIZE) + 1:03d}"
            shard_id = f"PA-FULL-2026-07-16-RUN-{((operational_rank - 1) // RUNNER_SHARD_SIZE) + 1:03d}"
            status = "ready_for_scout"
            reason_parts = item["_reason_parts"]
            assert isinstance(reason_parts, list)
            reason = (
                f"{item['_tier']} (score={item['_score']}): "
                + "; ".join(str(part) for part in reason_parts)
                + ". Ranked through county-cycling within tier to preserve geographic diversity. "
                "These are source-availability/comparability proxies, not evidence that bargaining units or CBAs exist."
            )
        output_rows.append(
            {
                "pa_batch_id": batch_id,
                "pa_runner_shard_id": shard_id,
                "pa_priority_rank": str(rank),
                "state": source["state"],
                "municipality": source["municipality"],
                "municipality_id": source["municipality_id"],
                "census_gov_id": source["census_gov_id"],
                "government_name": source["government_name"],
                "government_type": source["government_type"],
                "geography_type": source["geography_type"],
                "population": source["population"],
                "population_year": source["population_year"],
                "county_relationship_count": source["county_relationship_count"],
                "multi_county_flag": source["multi_county_flag"],
                "county_context_summary": county_context(relationships),
                "batching_county_geoid": str(item["_batching_county_geoid"]),
                "batching_county_name": str(item["_batching_county_name"]),
                "already_scouted": source["already_scouted"],
                "scout_positive_status": source["scout_positive_status"],
                "already_in_corpus": source["already_in_corpus"],
                "already_in_city_coverage": str(item["_already_in_city_coverage"]),
                "government_website_available": "yes" if source["government_website"] else "no",
                "pa_priority_score": str(item["_score"]),
                "pa_priority_tier": str(item["_tier"]),
                "selection_reason": reason,
                "expected_units_to_search": expected_units(source),
                "verification_notes": verification_notes(source, relationships),
                "recommended_scout_status": status,
            }
        )

    write_and_validate(output_rows, pa_universe, crosswalk_by_id)
    first_batch = [row for row in output_rows if row["pa_batch_id"].endswith("B001")]
    print(f"pa_universe={len(pa_universe)}")
    print(f"already_scouted={len(carry_forward)}")
    print(f"unscouted={len(ordered_unscouted)}")
    print("planning_batch_size=100")
    print("planning_batches=26 (25x100 + 1x32)")
    print("runner_shards=102 (101x25 + 1x7)")
    print(f"pa_batch_01={len(first_batch)}")
    print(f"pa_batch_01_counties={len({row['batching_county_geoid'] for row in first_batch})}")
    print(f"national_manifest_rows={len(national_manifest)}")
    print(f"national_manifest_pa_rows={sum(row['state'] == 'PA' for row in national_manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
