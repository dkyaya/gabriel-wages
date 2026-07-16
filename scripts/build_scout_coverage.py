#!/usr/bin/env python3
"""Build national municipality/county universes and scout coverage accounting.

This is an accounting/setup script only. It downloads public Census source
files when their tmp/ caches are absent. It does not run GABRIEL, verify scout
leads, ingest documents, codify text, or touch canonical corpus files.
"""

from __future__ import annotations

import csv
import io
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "analysis"
TMP = ROOT / "tmp"

COUNTY_ZIP_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2024_Gazetteer/2024_Gaz_counties_national.zip"
)
COUNTY_ZIP_CACHE = TMP / "2024_Gaz_counties_national.zip"
COUNTY_SOURCE_VINTAGE = "2024 Census Gazetteer counties national file"
COUNTY_UNIVERSE_NOTES = "Filtered to 50 states plus DC; territories excluded."

GOVERNMENT_UNITS_ZIP_URL = (
    "https://www2.census.gov/programs-surveys/gus/datasets/2025/gov_units_2025.zip"
)
GOVERNMENT_UNITS_ZIP_CACHE = TMP / "gov_units_2025.zip"
GOVERNMENT_UNITS_MEMBER = "Govt_Units_2025_Final.xlsx"
GOVERNMENT_UNITS_SOURCE_VINTAGE = (
    "2025 Government Units Listing; GMAF snapshot active as of fiscal year ending 2025-06-30"
)

COUSUB_ZIP_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
    "2024_Gazetteer/2024_Gaz_cousubs_national.zip"
)
COUSUB_ZIP_CACHE = TMP / "2024_Gaz_cousubs_national.zip"
COUSUB_SOURCE_VINTAGE = "2024 Census Gazetteer county subdivisions national file"

PLACE_COUNTY_URL = (
    "https://www2.census.gov/geo/docs/reference/codes2020/"
    "national_place_by_county2020.txt"
)
PLACE_COUNTY_CACHE = TMP / "national_place_by_county2020.txt"
PLACE_COUNTY_SOURCE_VINTAGE = "2020 Census national place-by-county code table"

MUNICIPALITY_SCOPE_NOTE = (
    "Scope is functionally active Census municipal and township governments; "
    "ordinary counties, CDPs, school districts, and special districts are excluded."
)
COUNTY_COVERAGE_NOTE = (
    "County rows count municipality-county associations from the full crosswalk. "
    "Multi-county municipalities appear in every associated county, so county rows "
    "are not additive and do not imply municipality or county completion."
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
    "state_fips",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_name",
    "government_type",
    "geography_type",
    "political_description",
    "local_geography_fips",
    "population",
    "population_year",
    "active_status",
    "government_units_primary_county_geoid",
    "county_relationship_count",
    "multi_county_flag",
    "project_known_before_national_build",
    "already_scouted",
    "scout_positive_status",
    "verified_status",
    "ingested_status",
    "codified_status",
    "already_in_corpus",
    "government_website",
    "municipality_source",
    "population_rank_note",
    "notes",
]

MUNICIPALITY_COUNTY_CROSSWALK_FIELDS = [
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "government_type",
    "geography_type",
    "state_fips",
    "local_geography_fips",
    "county_geoid",
    "county_name",
    "county_equivalent_type",
    "is_government_units_primary_county",
    "relationship_source",
    "relationship_vintage",
    "relationship_basis",
    "notes",
]

NATIONAL_STATE_COVERAGE_FIELDS = [
    "state",
    "county_equivalent_count",
    "municipalities_in_universe",
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
    "notes",
]

NATIONAL_COUNTY_COVERAGE_FIELDS = [
    "state",
    "county_geoid",
    "county_name",
    "municipality_associations_in_universe",
    "municipality_associations_scouted",
    "municipality_associations_scout_positive",
    "candidate_rows_total",
    "likely_triad_municipality_associations",
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

XLSX_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


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


def ensure_download(url: str, cache_path: Path) -> Path:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        return cache_path
    with urllib.request.urlopen(url, timeout=120) as response:
        cache_path.write_bytes(response.read())
    return cache_path


def county_equivalent_type(state: str, county_name: str) -> str:
    if state == "DC":
        return "federal_district"
    if state == "CT":
        return "planning_region"
    if state == "LA":
        return "parish"
    if state == "NV" and county_name == "Carson City":
        return "independent_city"
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
    zip_path = ensure_download(COUNTY_ZIP_URL, COUNTY_ZIP_CACHE)
    with zipfile.ZipFile(zip_path) as archive:
        raw_text = archive.read(archive.namelist()[0]).decode("utf-8")
    rows: list[dict] = []
    for row in csv.DictReader(io.StringIO(raw_text), delimiter="\t"):
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
                "source": COUNTY_ZIP_URL,
                "source_date_or_vintage": COUNTY_SOURCE_VINTAGE,
                "notes": COUNTY_UNIVERSE_NOTES,
            }
        )
    return sorted(rows, key=lambda row: (row["state_fips"], row["county_geoid"]))


def state_summary_rows(county_rows: list[dict]) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for row in county_rows:
        counts[row["state"]] += 1
    return [
        {
            "state": state,
            "state_fips": STATE_ABBR_TO_FIPS[state],
            "county_equivalent_count": counts[state],
            "source": COUNTY_ZIP_URL,
            "notes": COUNTY_UNIVERSE_NOTES,
        }
        for state in sorted(counts, key=lambda abbr: (STATE_ABBR_TO_FIPS[abbr], abbr))
    ]


def xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.itertext()) for node in root.findall("m:si", XLSX_NS)]


def load_xlsx_sheet_records(xlsx_bytes: bytes, sheet_member: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as archive:
        shared = xlsx_shared_strings(archive)
        root = ET.fromstring(archive.read(sheet_member))
    raw_rows: list[dict[str, str]] = []
    for row_node in root.findall(".//m:sheetData/m:row", XLSX_NS):
        values: dict[str, str] = {}
        for cell in row_node.findall("m:c", XLSX_NS):
            reference = cell.get("r", "")
            match = re.match(r"[A-Z]+", reference)
            if not match:
                continue
            column = match.group(0)
            value_node = cell.find("m:v", XLSX_NS)
            value = "" if value_node is None else value_node.text or ""
            if cell.get("t") == "s" and value:
                value = shared[int(value)]
            elif cell.get("t") == "inlineStr":
                value = "".join(cell.itertext())
            values[column] = value.strip()
        raw_rows.append(values)
    if not raw_rows:
        raise ValueError("Government Units workbook General Purpose sheet is empty")
    field_by_column = raw_rows[0]
    return [
        {field: row.get(column, "") for column, field in field_by_column.items()}
        for row in raw_rows[1:]
    ]


def load_government_units() -> list[dict[str, str]]:
    zip_path = ensure_download(GOVERNMENT_UNITS_ZIP_URL, GOVERNMENT_UNITS_ZIP_CACHE)
    with zipfile.ZipFile(zip_path) as archive:
        xlsx_bytes = archive.read(GOVERNMENT_UNITS_MEMBER)
    records = load_xlsx_sheet_records(xlsx_bytes, "xl/worksheets/sheet1.xml")
    required = {
        "CENSUS_ID_PID6",
        "UNIT_NAME",
        "UNIT_TYPE",
        "STATE",
        "FIPS_STATE",
        "FIPS_COUNTY",
        "FIPS_PLACE",
        "ACTIVE",
    }
    if records and not required.issubset(records[0]):
        raise ValueError("Government Units workbook layout changed; required columns are missing")
    rows = [
        row
        for row in records
        if row["STATE"] in STATE_ABBR_TO_FIPS
        and row["UNIT_TYPE"] in {"2 - MUNICIPAL", "3 - TOWNSHIP"}
        and row["ACTIVE"] == "Y"
    ]
    ids = [row["CENSUS_ID_PID6"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Government Units source contains duplicate Census government IDs in scope")
    return rows


def load_place_county_rows() -> dict[tuple[str, str], list[dict[str, str]]]:
    path = ensure_download(PLACE_COUNTY_URL, PLACE_COUNTY_CACHE)
    output: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="|"):
            if row["STATE"] not in STATE_ABBR_TO_FIPS:
                continue
            if row["TYPE"].upper() != "INCORPORATED PLACE":
                continue
            output[(row["STATEFP"], row["PLACEFP"])].append(row)
    return output


def load_cousub_rows() -> dict[tuple[str, str, str], dict[str, str]]:
    zip_path = ensure_download(COUSUB_ZIP_URL, COUSUB_ZIP_CACHE)
    with zipfile.ZipFile(zip_path) as archive:
        raw_text = archive.read(archive.namelist()[0]).decode("utf-8")
    output: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in csv.DictReader(io.StringIO(raw_text), delimiter="\t"):
        state = row["USPS"].strip()
        geoid = row["GEOID"].strip()
        if state not in STATE_ABBR_TO_FIPS:
            continue
        output[(geoid[:2], geoid[2:5], geoid[5:])] = row
    return output


def strip_legal_area_description(name: str) -> str:
    value = " ".join(name.strip().split())
    suffixes = (
        " city and borough",
        " consolidated government",
        " metropolitan government",
        " unified government",
        " urban county",
        " municipality",
        " township",
        " plantation",
        " borough",
        " village",
        " town",
        " city",
    )
    lowered = value.lower()
    for suffix in suffixes:
        if lowered.endswith(suffix):
            return value[: -len(suffix)].strip()
    return value


def fallback_government_label(unit_name: str) -> str:
    value = " ".join(unit_name.strip().split())
    prefixes = (
        "CONSOLIDATED GOVERNMENT OF ",
        "METROPOLITAN GOVERNMENT OF ",
        "UNIFIED GOVERNMENT OF ",
        "CITY AND BOROUGH OF ",
        "CITY AND COUNTY OF ",
        "MUNICIPALITY OF ",
        "CHARTER TOWNSHIP OF ",
        "TOWNSHIP OF ",
        "BOROUGH OF ",
        "VILLAGE OF ",
        "TOWN OF ",
        "CITY OF ",
    )
    upper = value.upper()
    for prefix in prefixes:
        if upper.startswith(prefix):
            value = value[len(prefix) :]
            break
    return value.title()


def normalize_municipality_lookup(name: str) -> str:
    value = strip_legal_area_description(name)
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return " ".join(value.split())


def load_project_known_municipalities() -> dict[tuple[str, str], dict]:
    rows: dict[tuple[str, str], dict] = {}

    def upsert(
        state: str,
        municipality: str,
        source_label: str,
        municipality_id: str = "",
        population_rank_note: str = "",
        already_in_corpus: str = "",
    ) -> None:
        key = (state, normalize_municipality_lookup(municipality))
        record = rows.setdefault(
            key,
            {
                "state": state,
                "municipality": municipality,
                "municipality_id": municipality_id,
                "source_parts": [],
                "population_rank_note": "",
                "already_in_corpus": "no",
            },
        )
        if source_label not in record["source_parts"]:
            record["source_parts"].append(source_label)
        if municipality_id:
            record["municipality_id"] = municipality_id
        if population_rank_note and not record["population_rank_note"]:
            record["population_rank_note"] = population_rank_note
        if already_in_corpus:
            record["already_in_corpus"] = already_in_corpus

    with (ROOT / "data" / "contracts.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            upsert(
                row["state"],
                row["city_name"],
                "data/contracts.csv",
                municipality_id=row["city_id"],
                already_in_corpus="yes",
            )
    with (DOCS / "national_source_targets_2026-07-12.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            upsert(
                FULL_STATE_TO_ABBR[row["state"]],
                row["city"],
                "docs/analysis/national_source_targets_2026-07-12.csv",
            )
    with (DOCS / "gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        for row in csv.DictReader(handle):
            upsert(
                row["state"],
                row["municipality"],
                "docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv",
                municipality_id=row["municipality_id"],
                population_rank_note=row["population_rank_note"],
                already_in_corpus=row["already_in_corpus"],
            )
    missing_ids = [key for key, row in rows.items() if not row["municipality_id"]]
    for key in missing_ids:
        state, normalized = key
        rows[key]["municipality_id"] = f"{state.lower()}_{normalized.replace(' ', '_')}"
    return rows


def load_scout_coverage_rows_by_muni_id() -> dict[str, dict]:
    coverage_path = DOCS / "gabriel_state_source_scout_municipality_coverage.csv"
    rows: dict[str, dict] = {}
    with coverage_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[row["municipality_id"]] = row
    return rows


def geographic_label_and_type(
    government: dict[str, str],
    place_rows: dict[tuple[str, str], list[dict[str, str]]],
    cousub_rows: dict[tuple[str, str, str], dict[str, str]],
) -> tuple[str, str]:
    if government["UNIT_TYPE"] == "2 - MUNICIPAL":
        matches = place_rows.get((government["FIPS_STATE"], government["FIPS_PLACE"]), [])
        if matches:
            return strip_legal_area_description(matches[0]["PLACENAME"]), "place"
        return fallback_government_label(government["UNIT_NAME"]), "place"
    key = (government["FIPS_STATE"], government["FIPS_COUNTY"], government["FIPS_PLACE"])
    match = cousub_rows.get(key)
    if match:
        return strip_legal_area_description(match["NAME"]), "county_subdivision"
    return fallback_government_label(government["UNIT_NAME"]), "county_subdivision"


def build_municipality_rows_and_crosswalk(
    county_rows: list[dict],
    government_rows: list[dict[str, str]],
    place_rows: dict[tuple[str, str], list[dict[str, str]]],
    cousub_rows: dict[tuple[str, str, str], dict[str, str]],
    project_known: dict[tuple[str, str], dict],
    scout_rows: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    county_lookup = {row["county_geoid"]: row for row in county_rows}
    provisional: list[dict] = []
    source_keys: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for government in government_rows:
        municipality, geography_type = geographic_label_and_type(government, place_rows, cousub_rows)
        record = {
            "government": government,
            "municipality": municipality,
            "geography_type": geography_type,
        }
        provisional.append(record)
        source_keys[(government["STATE"], normalize_municipality_lookup(municipality))].append(record)

    project_by_census_id: dict[str, dict] = {}
    unresolved_project_keys: dict[tuple[str, str], int] = {}
    for key, project in project_known.items():
        candidates = source_keys.get(key, [])
        if len(candidates) == 1:
            selected = candidates[0]
        else:
            municipal_candidates = [
                candidate
                for candidate in candidates
                if candidate["government"]["UNIT_TYPE"] == "2 - MUNICIPAL"
            ]
            if len(municipal_candidates) != 1:
                unresolved_project_keys[key] = len(candidates)
                continue
            selected = municipal_candidates[0]
        project_by_census_id[selected["government"]["CENSUS_ID_PID6"]] = project
    if unresolved_project_keys:
        raise ValueError(
            "Project-known municipality matching is incomplete or ambiguous: "
            f"{unresolved_project_keys}"
        )

    matched_project_keys: set[tuple[str, str]] = set()
    universe_rows: list[dict] = []
    crosswalk_rows: list[dict] = []
    for item in provisional:
        government = item["government"]
        state = government["STATE"]
        source_key = (state, normalize_municipality_lookup(item["municipality"]))
        project = project_by_census_id.get(government["CENSUS_ID_PID6"])
        if project:
            matched_project_keys.add(source_key)
            municipality = project["municipality"]
            municipality_id = project["municipality_id"]
            project_sources = project["source_parts"]
            population_rank_note = project["population_rank_note"]
            in_corpus = project["already_in_corpus"]
        else:
            municipality = item["municipality"]
            municipality_id = f"cog_2025_{government['CENSUS_ID_PID6']}"
            project_sources = []
            population_rank_note = ""
            in_corpus = "no"

        primary_county_geoid = government["FIPS_STATE"] + government["FIPS_COUNTY"]
        relationship_candidates: dict[str, dict[str, str]] = {}
        if item["geography_type"] == "place":
            for place_row in place_rows.get((government["FIPS_STATE"], government["FIPS_PLACE"]), []):
                county_geoid = place_row["STATEFP"] + place_row["COUNTYFP"]
                if county_geoid in county_lookup:
                    relationship_candidates[county_geoid] = {
                        "source": PLACE_COUNTY_URL,
                        "vintage": PLACE_COUNTY_SOURCE_VINTAGE,
                        "basis": "2020_place_by_county",
                        "notes": "",
                    }
        else:
            cousub_key = (
                government["FIPS_STATE"],
                government["FIPS_COUNTY"],
                government["FIPS_PLACE"],
            )
            if cousub_key in cousub_rows and primary_county_geoid in county_lookup:
                relationship_candidates[primary_county_geoid] = {
                    "source": COUSUB_ZIP_URL,
                    "vintage": COUSUB_SOURCE_VINTAGE,
                    "basis": "2024_county_subdivision_geoid",
                    "notes": "",
                }

        if primary_county_geoid in county_lookup and primary_county_geoid not in relationship_candidates:
            fallback_note = (
                "Current primary/headquarters county from the 2025 Government Units Listing; "
                "the older place-by-county table did not supply a current county-equivalent match."
            )
            relationship_candidates[primary_county_geoid] = {
                "source": GOVERNMENT_UNITS_ZIP_URL,
                "vintage": GOVERNMENT_UNITS_SOURCE_VINTAGE,
                "basis": "2025_government_units_primary_county_supplement",
                "notes": fallback_note,
            }
        if not relationship_candidates:
            raise ValueError(
                f"No current county relationship for Census government {government['CENSUS_ID_PID6']}"
            )

        relationship_count = len(relationship_candidates)
        for county_geoid, relationship in sorted(relationship_candidates.items()):
            county = county_lookup[county_geoid]
            notes = relationship["notes"]
            if county["county_equivalent_type"] == "independent_city":
                notes = (notes + " Independent city represented as its own county-equivalent.").strip()
            if state == "DC":
                notes = (notes + " DC represented as one municipal government and one county-equivalent.").strip()
            crosswalk_rows.append(
                {
                    "municipality_id": municipality_id,
                    "census_gov_id": government["CENSUS_ID_PID6"],
                    "state": state,
                    "municipality": municipality,
                    "government_name": government["UNIT_NAME"],
                    "government_type": "municipal" if government["UNIT_TYPE"] == "2 - MUNICIPAL" else "township",
                    "geography_type": item["geography_type"],
                    "state_fips": government["FIPS_STATE"],
                    "local_geography_fips": government["FIPS_PLACE"],
                    "county_geoid": county_geoid,
                    "county_name": county["county_name"],
                    "county_equivalent_type": county["county_equivalent_type"],
                    "is_government_units_primary_county": "yes" if county_geoid == primary_county_geoid else "no",
                    "relationship_source": relationship["source"],
                    "relationship_vintage": relationship["vintage"],
                    "relationship_basis": relationship["basis"],
                    "notes": notes,
                }
            )

        scout = scout_rows.get(municipality_id)
        scout_positive_status = (
            "not_scouted"
            if scout is None
            else ("yes" if int(scout["candidate_count"] or 0) > 0 else "no")
        )
        notes = MUNICIPALITY_SCOPE_NOTE
        if relationship_count > 1:
            notes += " Multi-county government; all county relationships are in the crosswalk."
        if state == "DC":
            notes += " District of Columbia is represented explicitly as a municipal government."
        universe_rows.append(
            {
                "state": state,
                "state_fips": government["FIPS_STATE"],
                "municipality": municipality,
                "municipality_id": municipality_id,
                "census_gov_id": government["CENSUS_ID_PID6"],
                "government_name": government["UNIT_NAME"],
                "government_type": "municipal" if government["UNIT_TYPE"] == "2 - MUNICIPAL" else "township",
                "geography_type": item["geography_type"],
                "political_description": government.get("POLITICAL_CODE_DESCRIPTION", ""),
                "local_geography_fips": government["FIPS_PLACE"],
                "population": government.get("POPULATION", ""),
                "population_year": government.get("POPULATION_SOURCE_YEAR", ""),
                "active_status": government["ACTIVE"],
                "government_units_primary_county_geoid": primary_county_geoid,
                "county_relationship_count": relationship_count,
                "multi_county_flag": "yes" if relationship_count > 1 else "no",
                "project_known_before_national_build": "yes" if project else "no",
                "already_scouted": "yes" if scout else "no",
                "scout_positive_status": scout_positive_status,
                "verified_status": "not_accounted",
                "ingested_status": in_corpus,
                "codified_status": "not_accounted",
                "already_in_corpus": in_corpus,
                "government_website": government.get("WEB_ADDRESS", ""),
                "municipality_source": "; ".join([GOVERNMENT_UNITS_ZIP_URL, *project_sources]),
                "population_rank_note": population_rank_note,
                "notes": notes,
            }
        )

    if matched_project_keys != set(project_known):
        raise ValueError("Not every project-known municipality was preserved in the national universe")
    universe_ids = {row["municipality_id"] for row in universe_rows}
    unmatched_scout_ids = sorted(set(scout_rows) - universe_ids)
    if unmatched_scout_ids:
        raise ValueError(f"Scouted municipalities missing from national universe: {unmatched_scout_ids}")
    if len(universe_ids) != len(universe_rows):
        raise ValueError("Municipality IDs are not unique")
    crosswalk_keys = [(row["municipality_id"], row["county_geoid"]) for row in crosswalk_rows]
    if len(crosswalk_keys) != len(set(crosswalk_keys)):
        raise ValueError("Municipality-county crosswalk contains duplicate relationships")
    return (
        sorted(universe_rows, key=lambda row: (row["state_fips"], row["municipality"], row["census_gov_id"])),
        sorted(crosswalk_rows, key=lambda row: (row["state_fips"], row["municipality_id"], row["county_geoid"])),
    )


def build_national_state_coverage(
    county_rows: list[dict], municipality_rows: list[dict], scout_rows: dict[str, dict], last_updated: str
) -> list[dict]:
    county_counts: dict[str, int] = defaultdict(int)
    municipalities_by_state: dict[str, list[dict]] = defaultdict(list)
    scout_by_state: dict[str, list[dict]] = defaultdict(list)
    for row in county_rows:
        county_counts[row["state"]] += 1
    for row in municipality_rows:
        municipalities_by_state[row["state"]].append(row)
    for row in scout_rows.values():
        scout_by_state[row["state"]].append(row)

    rows = []
    for state in sorted(county_counts, key=lambda abbr: (STATE_ABBR_TO_FIPS[abbr], abbr)):
        scout_rows_state = scout_by_state.get(state, [])
        rows.append(
            {
                "state": state,
                "county_equivalent_count": county_counts[state],
                "municipalities_in_universe": len(municipalities_by_state.get(state, [])),
                "municipalities_scouted": len(scout_rows_state),
                "municipalities_scout_positive": sum(
                    1 for row in scout_rows_state if int(row["candidate_count"] or 0) > 0
                ),
                "municipalities_with_police_candidate": sum(
                    1 for row in scout_rows_state if int(row["police_candidate_count"] or 0) > 0
                ),
                "municipalities_with_fire_candidate": sum(
                    1 for row in scout_rows_state if int(row["fire_candidate_count"] or 0) > 0
                ),
                "municipalities_with_non_safety_candidate": sum(
                    1 for row in scout_rows_state if int(row["non_safety_candidate_count"] or 0) > 0
                ),
                "municipalities_with_likely_triad": sum(
                    1 for row in scout_rows_state if row["likely_triad"] == "yes"
                ),
                "candidate_rows_total": sum(int(row["candidate_count"] or 0) for row in scout_rows_state),
                # Preserve the existing PA municipality-level aggregation convention exactly.
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
                "scout_total_cost": round(
                    sum(float(row["total_cost"] or 0.0) for row in scout_rows_state), 7
                ),
                "input_tokens_total": sum(
                    float(row["input_tokens_total"] or 0.0) for row in scout_rows_state
                ),
                "reasoning_tokens_total": sum(
                    float(row["reasoning_tokens_total"] or 0.0) for row in scout_rows_state
                ),
                "output_tokens_total": sum(
                    float(row["output_tokens_total"] or 0.0) for row in scout_rows_state
                ),
                "last_updated": last_updated,
                "notes": MUNICIPALITY_SCOPE_NOTE,
            }
        )
    return rows


def validate_scout_state_carry_forward(national_state_rows: list[dict]) -> None:
    """Require national scout metrics to reproduce the existing state rollup."""
    generated = {row["state"]: row for row in national_state_rows}
    path = DOCS / "gabriel_state_source_scout_state_coverage.csv"
    field_map = {
        "municipalities_scouted": "municipalities_scouted",
        "municipalities_with_any_candidate": "municipalities_scout_positive",
        "municipalities_with_police_candidate": "municipalities_with_police_candidate",
        "municipalities_with_fire_candidate": "municipalities_with_fire_candidate",
        "municipalities_with_non_safety_candidate": "municipalities_with_non_safety_candidate",
        "municipalities_with_likely_triad": "municipalities_with_likely_triad",
        "candidate_rows_total": "candidate_rows_total",
        "official_or_union_candidate_rows": "official_or_union_candidate_rows",
        "high_priority_candidate_rows": "high_priority_candidate_rows",
        "total_cost": "scout_total_cost",
        "input_tokens_total": "input_tokens_total",
        "reasoning_tokens_total": "reasoning_tokens_total",
        "output_tokens_total": "output_tokens_total",
    }
    with path.open(newline="", encoding="utf-8") as handle:
        for source_row in csv.DictReader(handle):
            state = source_row["state"]
            target_row = generated.get(state)
            if target_row is None:
                raise ValueError(f"Scout state {state} is missing from national coverage")
            for source_field, target_field in field_map.items():
                if Decimal(str(source_row[source_field] or 0)) != Decimal(str(target_row[target_field] or 0)):
                    raise ValueError(
                        f"Scout carry-forward mismatch for {state} {source_field}: "
                        f"{source_row[source_field]} != {target_row[target_field]}"
                    )


def build_national_county_coverage(
    county_rows: list[dict],
    municipality_rows: list[dict],
    crosswalk_rows: list[dict],
    scout_rows: dict[str, dict],
) -> list[dict]:
    municipality_lookup = {row["municipality_id"]: row for row in municipality_rows}
    associations_by_county: dict[str, list[dict]] = defaultdict(list)
    for relationship in crosswalk_rows:
        associations_by_county[relationship["county_geoid"]].append(
            municipality_lookup[relationship["municipality_id"]]
        )

    rows = []
    for county_row in county_rows:
        county_geoid = county_row["county_geoid"]
        associations = associations_by_county.get(county_geoid, [])
        scouted = [row for row in associations if row["municipality_id"] in scout_rows]
        rows.append(
            {
                "state": county_row["state"],
                "county_geoid": county_geoid,
                "county_name": county_row["county_name"],
                "municipality_associations_in_universe": len(associations),
                "municipality_associations_scouted": len(scouted),
                "municipality_associations_scout_positive": sum(
                    1
                    for municipality in scouted
                    if int(scout_rows[municipality["municipality_id"]]["candidate_count"] or 0) > 0
                ),
                "candidate_rows_total": sum(
                    int(scout_rows[municipality["municipality_id"]]["candidate_count"] or 0)
                    for municipality in scouted
                ),
                "likely_triad_municipality_associations": sum(
                    1
                    for municipality in scouted
                    if scout_rows[municipality["municipality_id"]]["likely_triad"] == "yes"
                ),
                "notes": COUNTY_COVERAGE_NOTE,
            }
        )
    return rows


def main() -> int:
    county_rows = load_county_universe()
    county_state_rows = state_summary_rows(county_rows)
    government_rows = load_government_units()
    place_rows = load_place_county_rows()
    cousub_rows = load_cousub_rows()
    project_known = load_project_known_municipalities()
    scout_rows = load_scout_coverage_rows_by_muni_id()
    municipality_rows, crosswalk_rows = build_municipality_rows_and_crosswalk(
        county_rows,
        government_rows,
        place_rows,
        cousub_rows,
        project_known,
        scout_rows,
    )
    last_updated = datetime.now().replace(microsecond=0).isoformat()
    national_state_rows = build_national_state_coverage(
        county_rows, municipality_rows, scout_rows, last_updated
    )
    validate_scout_state_carry_forward(national_state_rows)
    national_county_rows = build_national_county_coverage(
        county_rows, municipality_rows, crosswalk_rows, scout_rows
    )

    write_csv(DOCS / "national_county_universe.csv", county_rows, COUNTY_UNIVERSE_FIELDS)
    write_csv(DOCS / "national_county_state_summary.csv", county_state_rows, COUNTY_STATE_SUMMARY_FIELDS)
    write_csv(DOCS / "national_municipality_universe.csv", municipality_rows, MUNICIPALITY_UNIVERSE_FIELDS)
    write_csv(
        DOCS / "national_municipality_county_crosswalk.csv",
        crosswalk_rows,
        MUNICIPALITY_COUNTY_CROSSWALK_FIELDS,
    )
    write_csv(DOCS / "national_scout_coverage_state.csv", national_state_rows, NATIONAL_STATE_COVERAGE_FIELDS)
    write_csv(DOCS / "national_scout_coverage_county.csv", national_county_rows, NATIONAL_COUNTY_COVERAGE_FIELDS)

    total_scouted = sum(1 for row in municipality_rows if row["already_scouted"] == "yes")
    total_scout_positive = sum(
        1 for row in municipality_rows if row["scout_positive_status"] == "yes"
    )
    print(f"county_equivalents={len(county_rows)}")
    print(f"municipalities_in_universe={len(municipality_rows)}")
    print(f"municipality_county_relationships={len(crosswalk_rows)}")
    print(
        "multi_county_municipalities="
        f"{sum(1 for row in municipality_rows if row['multi_county_flag'] == 'yes')}"
    )
    print(f"project_known_municipalities_preserved={len(project_known)}")
    print(f"scouted_municipalities={total_scouted}")
    print(f"scout_positive_municipalities={total_scout_positive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
