#!/usr/bin/env python3
"""Build national scout coverage accounting from existing project files.

This is an accounting/setup script only. It does not run GABRIEL, verify
sources, ingest documents, or touch canonical corpus files.
"""

from __future__ import annotations

import csv
import io
import sys
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "analysis"
TMP = ROOT / "tmp"

COUNTY_ZIP_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2024_Gazetteer/2024_Gaz_counties_national.zip"
)
COUNTY_ZIP_CACHE = TMP / "2024_Gaz_counties_national.zip"
COUNTY_SOURCE = COUNTY_ZIP_URL
COUNTY_SOURCE_VINTAGE = "2024 Census Gazetteer counties national file"
COUNTY_UNIVERSE_NOTES = "Filtered to 50 states plus DC; territories excluded."
COUNTY_MAPPING_SOURCE = "curated mapping to 2024 Census county-equivalent universe"
INCOMPLETE_MUNI_NOTE = (
    "Known-municipality counts reflect the project's current placeholder municipality "
    "universe, not a full national municipality inventory."
)

COUNTY_UNIVERSE_FIELDS = [
    "state",
    "state_fips",
    "county_fips",
    "county_geoid",
    "county_name",
    "county_equivalent_type",
    "county_name_normalized",
    "source",
    "source_date_or_vintage",
    "notes",
]

COUNTY_STATE_SUMMARY_FIELDS = [
    "state",
    "state_fips",
    "county_equivalent_count",
    "source",
    "notes",
]

MUNICIPALITY_UNIVERSE_FIELDS = [
    "state",
    "municipality",
    "municipality_id",
    "county_geoid",
    "county_name",
    "source_for_county_mapping",
    "municipality_source",
    "population_rank_note",
    "already_scouted",
    "already_in_corpus",
    "notes",
]

NATIONAL_STATE_COVERAGE_FIELDS = [
    "state",
    "county_equivalent_count",
    "municipalities_known",
    "municipalities_scouted",
    "municipalities_scout_positive",
    "municipalities_with_police_candidate",
    "municipalities_with_fire_candidate",
    "municipalities_with_non_safety_candidate",
    "municipalities_with_likely_triad",
    "candidate_rows_total",
    "official_or_union_candidate_rows",
    "high_priority_candidate_rows",
    "scout_total_cost",
    "input_tokens_total",
    "reasoning_tokens_total",
    "output_tokens_total",
    "last_updated",
]

NATIONAL_COUNTY_COVERAGE_FIELDS = [
    "state",
    "county_geoid",
    "county_name",
    "municipalities_known",
    "municipalities_scouted",
    "municipalities_scout_positive",
    "candidate_rows_total",
    "likely_triad_municipalities",
    "notes",
]

FULL_STATE_TO_ABBR = {
    "Pennsylvania": "PA",
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

STATE_ABBR_TO_FIPS = {
    "AL": "01",
    "AK": "02",
    "AZ": "04",
    "AR": "05",
    "CA": "06",
    "CO": "08",
    "CT": "09",
    "DE": "10",
    "DC": "11",
    "FL": "12",
    "GA": "13",
    "HI": "15",
    "ID": "16",
    "IL": "17",
    "IN": "18",
    "IA": "19",
    "KS": "20",
    "KY": "21",
    "LA": "22",
    "ME": "23",
    "MD": "24",
    "MA": "25",
    "MI": "26",
    "MN": "27",
    "MS": "28",
    "MO": "29",
    "MT": "30",
    "NE": "31",
    "NV": "32",
    "NH": "33",
    "NJ": "34",
    "NM": "35",
    "NY": "36",
    "NC": "37",
    "ND": "38",
    "OH": "39",
    "OK": "40",
    "OR": "41",
    "PA": "42",
    "RI": "44",
    "SC": "45",
    "SD": "46",
    "TN": "47",
    "TX": "48",
    "UT": "49",
    "VT": "50",
    "VA": "51",
    "WA": "53",
    "WV": "54",
    "WI": "55",
    "WY": "56",
}


@dataclass(frozen=True)
class MunicipalityCountyMap:
    county_geoid: str
    note: str = ""


KNOWN_MUNICIPALITY_COUNTY_MAP: dict[tuple[str, str], MunicipalityCountyMap] = {
    ("CA", "Los Angeles"): MunicipalityCountyMap("06037"),
    ("CA", "Sacramento"): MunicipalityCountyMap("06067"),
    ("CO", "Denver"): MunicipalityCountyMap("08031", "County-equivalent consolidated city-county."),
    ("CT", "Hartford"): MunicipalityCountyMap("09110", "Uses Connecticut's current Census county-equivalent planning regions."),
    ("IL", "Aurora"): MunicipalityCountyMap("17089", "Primary county assignment only; municipality spans multiple counties."),
    ("IL", "Chicago"): MunicipalityCountyMap("17031"),
    ("IL", "Naperville"): MunicipalityCountyMap("17043", "Primary county assignment only; municipality spans multiple counties."),
    ("IL", "Rockford"): MunicipalityCountyMap("17201"),
    ("IL", "Springfield"): MunicipalityCountyMap("17167"),
    ("MA", "Arlington"): MunicipalityCountyMap("25017"),
    ("MA", "Boston"): MunicipalityCountyMap("25025"),
    ("MA", "Franklin"): MunicipalityCountyMap("25021"),
    ("MA", "Georgetown"): MunicipalityCountyMap("25009"),
    ("MA", "Newton"): MunicipalityCountyMap("25017"),
    ("MA", "Seekonk"): MunicipalityCountyMap("25005"),
    ("MA", "Somerville"): MunicipalityCountyMap("25017"),
    ("MA", "Wayland"): MunicipalityCountyMap("25017"),
    ("MA", "Worcester"): MunicipalityCountyMap("25027"),
    ("MD", "Baltimore"): MunicipalityCountyMap("24510", "County-equivalent independent city."),
    ("MN", "Minneapolis"): MunicipalityCountyMap("27053"),
    ("NJ", "Camden"): MunicipalityCountyMap("34007"),
    ("NJ", "Jersey City"): MunicipalityCountyMap("34017"),
    ("NJ", "Newark"): MunicipalityCountyMap("34013"),
    ("NJ", "Paterson"): MunicipalityCountyMap("34031"),
    ("NJ", "Trenton"): MunicipalityCountyMap("34021"),
    ("NY", "Albany"): MunicipalityCountyMap("36001"),
    ("NY", "Buffalo"): MunicipalityCountyMap("36029"),
    ("NY", "Rochester"): MunicipalityCountyMap("36055"),
    ("NY", "Syracuse"): MunicipalityCountyMap("36067"),
    ("NY", "Yonkers"): MunicipalityCountyMap("36119"),
    ("OH", "Cincinnati"): MunicipalityCountyMap("39061"),
    ("OH", "Cleveland"): MunicipalityCountyMap("39035"),
    ("OH", "Columbus"): MunicipalityCountyMap("39049", "Primary county assignment only; municipality spans multiple counties."),
    ("OH", "Toledo"): MunicipalityCountyMap("39095"),
    ("OR", "Portland"): MunicipalityCountyMap("41051", "Primary county assignment only; municipality spans multiple counties."),
    ("PA", "Allentown"): MunicipalityCountyMap("42077"),
    ("PA", "Altoona"): MunicipalityCountyMap("42013"),
    ("PA", "Bethlehem"): MunicipalityCountyMap("42077", "Primary county assignment only; municipality spans multiple counties."),
    ("PA", "Carlisle"): MunicipalityCountyMap("42041"),
    ("PA", "Chambersburg"): MunicipalityCountyMap("42055"),
    ("PA", "Chester"): MunicipalityCountyMap("42045"),
    ("PA", "Easton"): MunicipalityCountyMap("42095"),
    ("PA", "Erie"): MunicipalityCountyMap("42049"),
    ("PA", "Harrisburg"): MunicipalityCountyMap("42043"),
    ("PA", "Hazleton"): MunicipalityCountyMap("42079"),
    ("PA", "Johnstown"): MunicipalityCountyMap("42021"),
    ("PA", "Lancaster"): MunicipalityCountyMap("42071"),
    ("PA", "Lebanon"): MunicipalityCountyMap("42075"),
    ("PA", "McKeesport"): MunicipalityCountyMap("42003"),
    ("PA", "New Castle"): MunicipalityCountyMap("42073"),
    ("PA", "Norristown"): MunicipalityCountyMap("42091"),
    ("PA", "Philadelphia"): MunicipalityCountyMap("42101", "County-equivalent consolidated city-county for project accounting purposes."),
    ("PA", "Pittsburgh"): MunicipalityCountyMap("42003"),
    ("PA", "Pottstown"): MunicipalityCountyMap("42091"),
    ("PA", "Reading"): MunicipalityCountyMap("42011"),
    ("PA", "Scranton"): MunicipalityCountyMap("42069"),
    ("PA", "State College"): MunicipalityCountyMap("42027"),
    ("PA", "Wilkes-Barre"): MunicipalityCountyMap("42079"),
    ("PA", "Williamsport"): MunicipalityCountyMap("42081"),
    ("PA", "York"): MunicipalityCountyMap("42133"),
    ("TX", "Austin"): MunicipalityCountyMap("48453", "Primary county assignment only; municipality spans multiple counties."),
    ("TX", "Houston"): MunicipalityCountyMap("48201", "Primary county assignment only; municipality spans multiple counties."),
    ("TX", "San Antonio"): MunicipalityCountyMap("48029"),
    ("WA", "Seattle"): MunicipalityCountyMap("53033"),
    ("WI", "Madison"): MunicipalityCountyMap("55025"),
}


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    parse_back_validate(path, fields)


def parse_back_validate(path: Path, fields: list[str]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        if header != fields:
            raise ValueError(f"{path}: header mismatch")
        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(fields):
                raise ValueError(f"{path}: row {line_number} width {len(row)} != {len(fields)}")


def ensure_county_zip() -> Path:
    COUNTY_ZIP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if COUNTY_ZIP_CACHE.exists():
        return COUNTY_ZIP_CACHE
    with urllib.request.urlopen(COUNTY_ZIP_URL, timeout=60) as response:
        COUNTY_ZIP_CACHE.write_bytes(response.read())
    return COUNTY_ZIP_CACHE


def county_equivalent_type(state: str, county_name: str) -> str:
    if state == "DC":
        return "federal_district"
    if state == "CT":
        return "planning_region"
    if state == "LA":
        return "parish"
    if state == "AK":
        if county_name.startswith("City and Borough of ") or county_name.endswith(" City and Borough"):
            return "city_and_borough"
        if county_name.startswith("Municipality of ") or county_name.endswith(" Municipality"):
            return "municipality"
        if county_name.endswith(" Census Area"):
            return "census_area"
        return "borough"
    if county_name.endswith(" city"):
        return "independent_city"
    return "county"


def normalize_county_name(name: str) -> str:
    value = name.strip()
    if value.startswith("City and Borough of "):
        value = value.replace("City and Borough of ", "", 1)
    elif value.startswith("Municipality of "):
        value = value.replace("Municipality of ", "", 1)
    for suffix in (
        " County",
        " Parish",
        " Borough",
        " Census Area",
        " Planning Region",
        " Municipality",
        " city",
        " City and Borough",
    ):
        if value.endswith(suffix):
            value = value[: -len(suffix)]
            break
    value = value.lower().replace(".", "").replace("'", "")
    return "_".join(value.split())


def load_county_universe() -> list[dict]:
    zip_path = ensure_county_zip()
    with zipfile.ZipFile(zip_path) as archive:
        member = archive.namelist()[0]
        raw_text = archive.read(member).decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw_text), delimiter="\t")
    rows: list[dict] = []
    for row in reader:
        state = row["USPS"].strip()
        if state not in STATE_ABBR_TO_FIPS:
            continue
        county_geoid = row["GEOID"].strip()
        county_name = row["NAME"].strip()
        rows.append(
            {
                "state": state,
                "state_fips": county_geoid[:2],
                "county_fips": county_geoid[2:],
                "county_geoid": county_geoid,
                "county_name": county_name,
                "county_equivalent_type": county_equivalent_type(state, county_name),
                "county_name_normalized": normalize_county_name(county_name),
                "source": COUNTY_SOURCE,
                "source_date_or_vintage": COUNTY_SOURCE_VINTAGE,
                "notes": COUNTY_UNIVERSE_NOTES,
            }
        )
    return sorted(rows, key=lambda row: (row["state_fips"], row["county_geoid"]))


def state_summary_rows(county_rows: list[dict]) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for row in county_rows:
        counts[row["state"]] += 1
    rows = []
    for state in sorted(counts, key=lambda abbr: (STATE_ABBR_TO_FIPS[abbr], abbr)):
        rows.append(
            {
                "state": state,
                "state_fips": STATE_ABBR_TO_FIPS[state],
                "county_equivalent_count": counts[state],
                "source": COUNTY_SOURCE,
                "notes": COUNTY_UNIVERSE_NOTES,
            }
        )
    return rows


def load_contract_city_ids() -> dict[tuple[str, str], str]:
    city_ids: dict[tuple[str, str], str] = {}
    with (ROOT / "data" / "contracts.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            city_ids[(row["state"], row["city_name"])] = row["city_id"]
    return city_ids


def slugify_city(text: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in text]
    value = "".join(chars)
    while "__" in value:
        value = value.replace("__", "_")
    return value.strip("_")


def load_known_municipalities() -> list[dict]:
    contract_city_ids = load_contract_city_ids()
    municipality_rows: dict[tuple[str, str], dict] = {}

    def upsert(state: str, municipality: str, source_label: str, municipality_id: str = "", population_rank_note: str = "", already_in_corpus: str = "") -> None:
        key = (state, municipality)
        row = municipality_rows.setdefault(
            key,
            {
                "state": state,
                "municipality": municipality,
                "municipality_id": municipality_id or contract_city_ids.get(key, f"{state.lower()}_{slugify_city(municipality)}"),
                "municipality_source_parts": [],
                "population_rank_note": "",
                "already_in_corpus": already_in_corpus or ("yes" if key in contract_city_ids else "no"),
            },
        )
        if source_label not in row["municipality_source_parts"]:
            row["municipality_source_parts"].append(source_label)
        if municipality_id:
            row["municipality_id"] = municipality_id
        if population_rank_note and not row["population_rank_note"]:
            row["population_rank_note"] = population_rank_note
        if already_in_corpus:
            row["already_in_corpus"] = already_in_corpus

    with (ROOT / "data" / "contracts.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            upsert(row["state"], row["city_name"], "data/contracts.csv", municipality_id=row["city_id"], already_in_corpus="yes")

    with (DOCS / "national_source_targets_2026-07-12.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            upsert(FULL_STATE_TO_ABBR[row["state"]], row["city"], "docs/analysis/national_source_targets_2026-07-12.csv")

    with (DOCS / "gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            upsert(
                row["state"],
                row["municipality"],
                "docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv",
                municipality_id=row["municipality_id"],
                population_rank_note=row["population_rank_note"],
                already_in_corpus=row["already_in_corpus"],
            )

    coverage_ids = load_scout_coverage_rows_by_muni_id()
    rows: list[dict] = []
    for key in sorted(municipality_rows):
        row = municipality_rows[key]
        mapping = KNOWN_MUNICIPALITY_COUNTY_MAP.get(key)
        if mapping is None:
            raise KeyError(f"Missing county mapping for municipality {key}")
        notes = mapping.note
        rows.append(
            {
                "state": row["state"],
                "municipality": row["municipality"],
                "municipality_id": row["municipality_id"],
                "county_geoid": mapping.county_geoid,
                "county_name": "",  # filled later
                "source_for_county_mapping": COUNTY_MAPPING_SOURCE,
                "municipality_source": "; ".join(row["municipality_source_parts"]),
                "population_rank_note": row["population_rank_note"],
                "already_scouted": "yes" if row["municipality_id"] in coverage_ids else "no",
                "already_in_corpus": row["already_in_corpus"],
                "notes": notes,
            }
        )
    return rows


def load_scout_coverage_rows_by_muni_id() -> dict[str, dict]:
    coverage_path = DOCS / "gabriel_state_source_scout_municipality_coverage.csv"
    rows: dict[str, dict] = {}
    with coverage_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[row["municipality_id"]] = row
    return rows


def attach_county_names(municipality_rows: list[dict], county_rows: list[dict]) -> list[dict]:
    county_lookup = {row["county_geoid"]: row["county_name"] for row in county_rows}
    output = []
    for row in municipality_rows:
        county_name = county_lookup.get(row["county_geoid"])
        if county_name is None:
            raise KeyError(f"Unknown county geoid {row['county_geoid']} for {row['municipality_id']}")
        updated = dict(row)
        updated["county_name"] = county_name
        output.append(updated)
    return sorted(output, key=lambda row: (row["state"], row["municipality"]))


def build_national_state_coverage(
    county_rows: list[dict], municipality_rows: list[dict], scout_rows: dict[str, dict], last_updated: str
) -> list[dict]:
    county_counts: dict[str, int] = defaultdict(int)
    for row in county_rows:
        county_counts[row["state"]] += 1

    known_by_state: dict[str, list[dict]] = defaultdict(list)
    for row in municipality_rows:
        known_by_state[row["state"]].append(row)

    scout_by_state: dict[str, list[dict]] = defaultdict(list)
    for row in scout_rows.values():
        scout_by_state[row["state"]].append(row)

    rows = []
    for state in sorted(county_counts, key=lambda abbr: (STATE_ABBR_TO_FIPS[abbr], abbr)):
        scout_rows_state = scout_by_state.get(state, [])
        rows.append(
            {
                "state": state,
                "county_equivalent_count": county_counts[state],
                "municipalities_known": len(known_by_state.get(state, [])),
                "municipalities_scouted": len(scout_rows_state),
                "municipalities_scout_positive": sum(1 for row in scout_rows_state if int(row["candidate_count"] or 0) > 0),
                "municipalities_with_police_candidate": sum(1 for row in scout_rows_state if int(row["police_candidate_count"] or 0) > 0),
                "municipalities_with_fire_candidate": sum(1 for row in scout_rows_state if int(row["fire_candidate_count"] or 0) > 0),
                "municipalities_with_non_safety_candidate": sum(1 for row in scout_rows_state if int(row["non_safety_candidate_count"] or 0) > 0),
                "municipalities_with_likely_triad": sum(1 for row in scout_rows_state if row["likely_triad"] == "yes"),
                "candidate_rows_total": sum(int(row["candidate_count"] or 0) for row in scout_rows_state),
                "official_or_union_candidate_rows": sum(
                    int(row["candidate_count"] or 0)
                    for row in scout_rows_state
                    if row["best_source_owner_type"] in {"city", "state_labor_board", "union"}
                ),
                "high_priority_candidate_rows": sum(
                    int(row["candidate_count"] or 0)
                    for row in scout_rows_state
                    if row["best_candidate_priority"] == "high"
                ),
                "scout_total_cost": round(sum(float(row["total_cost"] or 0.0) for row in scout_rows_state), 7),
                "input_tokens_total": sum(float(row["input_tokens_total"] or 0.0) for row in scout_rows_state),
                "reasoning_tokens_total": sum(float(row["reasoning_tokens_total"] or 0.0) for row in scout_rows_state),
                "output_tokens_total": sum(float(row["output_tokens_total"] or 0.0) for row in scout_rows_state),
                "last_updated": last_updated,
            }
        )
    return rows


def build_national_county_coverage(
    county_rows: list[dict], municipality_rows: list[dict], scout_rows: dict[str, dict]
) -> list[dict]:
    municipalities_by_county: dict[str, list[dict]] = defaultdict(list)
    for row in municipality_rows:
        municipalities_by_county[row["county_geoid"]].append(row)

    scout_by_muni_id = scout_rows
    rows = []
    for county_row in county_rows:
        county_geoid = county_row["county_geoid"]
        munis = municipalities_by_county.get(county_geoid, [])
        scouted = [m for m in munis if m["municipality_id"] in scout_by_muni_id]
        rows.append(
            {
                "state": county_row["state"],
                "county_geoid": county_geoid,
                "county_name": county_row["county_name"],
                "municipalities_known": len(munis),
                "municipalities_scouted": len(scouted),
                "municipalities_scout_positive": sum(
                    1 for muni in scouted if int(scout_by_muni_id[muni["municipality_id"]]["candidate_count"] or 0) > 0
                ),
                "candidate_rows_total": sum(
                    int(scout_by_muni_id[muni["municipality_id"]]["candidate_count"] or 0) for muni in scouted
                ),
                "likely_triad_municipalities": sum(
                    1 for muni in scouted if scout_by_muni_id[muni["municipality_id"]]["likely_triad"] == "yes"
                ),
                "notes": INCOMPLETE_MUNI_NOTE,
            }
        )
    return rows


def main() -> int:
    county_rows = load_county_universe()
    county_state_rows = state_summary_rows(county_rows)
    municipality_rows = attach_county_names(load_known_municipalities(), county_rows)
    scout_rows = load_scout_coverage_rows_by_muni_id()
    last_updated = datetime.now().replace(microsecond=0).isoformat()
    national_state_rows = build_national_state_coverage(county_rows, municipality_rows, scout_rows, last_updated)
    national_county_rows = build_national_county_coverage(county_rows, municipality_rows, scout_rows)

    write_csv(DOCS / "national_county_universe.csv", county_rows, COUNTY_UNIVERSE_FIELDS)
    write_csv(DOCS / "national_county_state_summary.csv", county_state_rows, COUNTY_STATE_SUMMARY_FIELDS)
    write_csv(DOCS / "national_municipality_universe.csv", municipality_rows, MUNICIPALITY_UNIVERSE_FIELDS)
    write_csv(DOCS / "national_scout_coverage_state.csv", national_state_rows, NATIONAL_STATE_COVERAGE_FIELDS)
    write_csv(DOCS / "national_scout_coverage_county.csv", national_county_rows, NATIONAL_COUNTY_COVERAGE_FIELDS)

    total_counties = len(county_rows)
    total_municipalities = len(municipality_rows)
    total_scouted = sum(1 for row in municipality_rows if row["already_scouted"] == "yes")
    print(f"county_equivalents={total_counties}")
    print(f"known_municipalities={total_municipalities}")
    print(f"scouted_municipalities={total_scouted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
