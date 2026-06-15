#!/usr/bin/env python3
"""
validate.py — schema validator for the GABRIEL municipal-wage corpus.

Run from repo root:  python scripts/validate.py
Exits 0 if all checks pass, 1 otherwise. Prints every violation with location.

Enforces docs/schema.md: required fields present, controlled vocabularies,
derived safety_flag consistency, ISO dates, unique primary keys, and
predecessor_obs_id resolution.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def valid_date(v):
    try:
        datetime.strptime(v, "%Y-%m-%d")
        return True
    except ValueError:
        return False

OCCUPATIONS = {
    "police", "fire", "teacher", "sanitation", "clerical_admin",
    "public_works", "transit", "parks_rec", "library", "nurse_health", "other",
}
SAFETY = {"police", "fire"}
RETRIEVAL = {
    "public_download", "foia", "westlaw", "lexis",
    "bloomberg", "factiva", "newsbank", "other",
}
QUALITY = {"clean", "ocr_messy", "partial"}
CORPUS = {"causal", "discourse"}
CONTRACT_SRC = {"cba", "arbitration_award", "factfinding"}
DISCOURSE_SRC = {"news", "op_ed", "budget_narrative", "pension_report", "academic"}

errors = []


def err(table, row, msg):
    errors.append(f"[{table}] row {row}: {msg}")


def read(table):
    path = DATA / table
    if not path.exists():
        err(table, "-", "file missing")
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def check_required(table, rows, fields):
    for i, r in enumerate(rows, start=2):  # row 1 is header
        for fld in fields:
            if not (r.get(fld) or "").strip():
                err(table, i, f"missing required '{fld}'")


def check_enum(table, rows, field, allowed, required=True):
    for i, r in enumerate(rows, start=2):
        v = (r.get(field) or "").strip()
        if not v:
            if required:
                err(table, i, f"missing required '{field}'")
            continue
        if v not in allowed:
            err(table, i, f"'{field}'='{v}' not in {sorted(allowed)}")


def check_dates(table, rows, fields):
    for i, r in enumerate(rows, start=2):
        for fld in fields:
            v = (r.get(fld) or "").strip()
            if v and not valid_date(v):
                err(table, i, f"'{fld}'='{v}' not a valid ISO calendar date (YYYY-MM-DD)")


def check_unique(table, rows, key):
    seen = {}
    for i, r in enumerate(rows, start=2):
        v = (r.get(key) or "").strip()
        if not v:
            continue
        if v in seen:
            err(table, i, f"duplicate {key} '{v}' (first at row {seen[v]})")
        else:
            seen[v] = i
    return set(seen)


def check_safety_flag(table, rows):
    for i, r in enumerate(rows, start=2):
        occ = (r.get("occupation_class") or "").strip()
        sf = (r.get("safety_flag") or "").strip()
        if occ not in OCCUPATIONS:
            # occupation is independently flagged by the enum check; still
            # verify the flag value itself is a legal 0/1
            if sf not in {"0", "1"}:
                err(table, i, f"safety_flag='{sf}' must be 0 or 1")
            continue
        expected = "1" if occ in SAFETY else "0"
        if sf != expected:
            err(table, i, f"safety_flag='{sf}' inconsistent with occupation_class='{occ}' (expected {expected})")


def main():
    # ---- contracts.csv ----
    _, contracts = read("contracts.csv")
    req = ["obs_id", "city_id", "city_name", "state", "bargaining_unit_name",
           "occupation_class", "safety_flag", "cycle_start", "cycle_end",
           "source_type", "source_corpus", "source_url_or_cite",
           "retrieval_date", "retrieval_method", "full_text_path", "text_quality"]
    check_required("contracts.csv", contracts, req)
    check_enum("contracts.csv", contracts, "occupation_class", OCCUPATIONS)
    check_enum("contracts.csv", contracts, "source_type", CONTRACT_SRC)
    check_enum("contracts.csv", contracts, "source_corpus", {"causal"})
    check_enum("contracts.csv", contracts, "retrieval_method", RETRIEVAL)
    check_enum("contracts.csv", contracts, "text_quality", QUALITY)
    check_dates("contracts.csv", contracts, ["cycle_start", "cycle_end", "retrieval_date"])
    check_safety_flag("contracts.csv", contracts)
    obs_ids = check_unique("contracts.csv", contracts, "obs_id")
    # predecessor resolution
    for i, r in enumerate(contracts, start=2):
        pred = (r.get("predecessor_obs_id") or "").strip()
        if pred and pred not in obs_ids:
            err("contracts.csv", i, f"predecessor_obs_id '{pred}' does not resolve to any obs_id")

    # ---- discourse.csv ----
    _, discourse = read("discourse.csv")
    req_d = ["disc_id", "city_id", "occupation_class", "text_date",
             "explanation_text", "source_type", "source_corpus",
             "source_url_or_cite", "retrieval_date", "retrieval_method",
             "full_text_path", "text_quality"]
    check_required("discourse.csv", discourse, req_d)
    check_enum("discourse.csv", discourse, "occupation_class", OCCUPATIONS)
    check_enum("discourse.csv", discourse, "source_type", DISCOURSE_SRC)
    check_enum("discourse.csv", discourse, "source_corpus", {"discourse"})
    check_enum("discourse.csv", discourse, "retrieval_method", RETRIEVAL)
    check_enum("discourse.csv", discourse, "text_quality", QUALITY)
    check_dates("discourse.csv", discourse, ["text_date", "retrieval_date"])
    check_unique("discourse.csv", discourse, "disc_id")

    # ---- city_coverage.csv ----
    _, coverage = read("city_coverage.csv")
    req_c = ["city_id", "city_name", "state", "occupation_class",
             "safety_flag", "cycle_window", "have_contract"]
    check_required("city_coverage.csv", coverage, req_c)
    check_enum("city_coverage.csv", coverage, "occupation_class", OCCUPATIONS)
    check_safety_flag("city_coverage.csv", coverage)
    for i, r in enumerate(coverage, start=2):
        hc = (r.get("have_contract") or "").strip()
        oid = (r.get("obs_id") or "").strip()
        if hc == "1" and not oid:
            err("city_coverage.csv", i, "have_contract=1 but obs_id is blank")
        if hc == "1" and oid and oid not in obs_ids:
            err("city_coverage.csv", i, f"obs_id '{oid}' not found in contracts.csv")

    # ---- city_attributes.csv ----
    _, attrs = read("city_attributes.csv")
    check_required("city_attributes.csv", attrs, ["city_id", "city_name", "state"])
    check_unique("city_attributes.csv", attrs, "city_id")

    # ---- report ----
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print("VALIDATION PASSED — all rows conform to docs/schema.md")
    print(f"  contracts: {len(contracts)} | discourse: {len(discourse)} | "
          f"coverage: {len(coverage)} | city_attributes: {len(attrs)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
