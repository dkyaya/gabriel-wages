#!/usr/bin/env python3
"""Build the normalized, unverified IL25.3 scout-candidate handoff CSV.

This is a deterministic local-only transform. It does not open URLs, verify
sources, ingest documents, edit canonical data, or codify text.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUN_DIR = (
    ROOT
    / "tmp"
    / "gabriel_state_source_scout"
    / "IL"
    / "national_batch01_il25_3_live_direct_sdk_2026-07-20"
)
INPUT = RUN_DIR / "parsed_candidates.csv"
OUTPUT = (
    ROOT
    / "docs"
    / "analysis"
    / "national_batch01_il25_3_live_direct_sdk_scout_candidates_2026-07-20.csv"
)
EXPECTED_ROWS = 70

FIELDS = [
    "municipality",
    "state",
    "municipality_id",
    "unit_type",
    "document_title",
    "union_name",
    "employer",
    "contract_years",
    "source_url",
    "source_owner_type",
    "document_type",
    "document_completeness",
    "comparator_role",
    "wrong_employer_risk",
    "context_only_flag",
    "visible_year_evidence",
    "overlap_with_anchor_cycle",
    "duplicate_risk",
    "blocked_or_unreadable_flag",
    "cycle_match_notes",
    "why_relevant",
    "confidence",
    "candidate_stage",
    "needs_verification_reason",
    "scout_stage_status",
    "verification_priority",
    "verification_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verification_notes(row: dict[str, str]) -> str:
    prefix = ""
    if not row.get("source_url", "").strip():
        prefix = (
            "Parsed response lacks a source URL; preserve this row in the scout handoff "
            "but do not place it in the source-candidate queue or infer a locator. "
        )
    elif row.get("blocked_or_unreadable_flag") == "yes":
        prefix = "Resolve blocked/unreadable access without treating the source as dead. "
    elif row.get("context_only_flag") == "yes":
        prefix = (
            "Retain as context/locator only unless a binding wage-setting instrument "
            "is established later. "
        )
    elif row.get("candidate_stage") == "insufficient_candidate":
        prefix = (
            "Retain as insufficient unless later evidence establishes a qualifying source. "
        )
    return (
        prefix
        + "Later coordinated verification must confirm the exact municipal employer and "
        "bargaining unit, authoritative provenance, executed/binding and complete-document "
        "status, visible operative dates, wage-setting content, duplicate status, and "
        "same-city cycle overlap. Do not ingest or use for claims before that gate."
    )


def build_rows() -> list[dict[str, str]]:
    source_rows = read_csv(INPUT)
    if len(source_rows) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} live IL25.3 candidates, found {len(source_rows)}"
        )

    output: list[dict[str, str]] = []
    for row in source_rows:
        if row.get("state") != "IL":
            raise ValueError(f"Unexpected state in IL25.3 input: {row.get('state')}")
        priority = (row.get("likely_ingest_priority") or "low").strip().lower()
        if priority not in {"high", "medium", "low"}:
            priority = "low"
        rendered = {field: row.get(field, "") for field in FIELDS}
        rendered["scout_stage_status"] = "unverified_scout_candidate"
        rendered["verification_priority"] = priority
        rendered["verification_notes"] = verification_notes(row)
        output.append(rendered)
    return output


def main() -> int:
    rows = build_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    parsed = read_csv(OUTPUT)
    if len(parsed) != EXPECTED_ROWS:
        raise ValueError("IL25.3 handoff row count changed on parse-back")
    if set(parsed[0]) != set(FIELDS):
        raise ValueError("IL25.3 handoff schema changed on parse-back")
    if {row["scout_stage_status"] for row in parsed} != {
        "unverified_scout_candidate"
    }:
        raise ValueError("IL25.3 handoff contains a non-scout-stage status")
    if sum(not row["source_url"].strip() for row in parsed) != 1:
        raise ValueError("Expected exactly one preserved IL25.3 missing-locator row")
    print(f"candidate_rows={len(parsed)}")
    print("queueable_source_rows=69 missing_locator_rows=1")
    print(f"output={OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
