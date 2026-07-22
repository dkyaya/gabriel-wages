#!/usr/bin/env python3
"""Build the durable national queue from preserved scout candidate files.

This script is deterministic and local-only. It does not open candidate URLs,
call a model, verify a source, ingest a document, or edit canonical data. Texas
and Massachusetts verification ledgers are calibration inputs only: their
findings are carried with an explicit ``calibration_`` prefix and do not become
project-wide verification or ingestion decisions.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "analysis"
OUTPUT = DOCS / "national_scout_candidate_queue_2026-07-20.csv"

QUEUE_FIELDS = [
    "queue_id",
    "source_wave",
    "source_candidate_file",
    "scout_run_id",
    "scout_date",
    "state",
    "municipality",
    "municipality_id",
    "unit_type_scouted",
    "document_title",
    "union_name",
    "employer",
    "contract_years_scouted",
    "source_url",
    "source_owner_type",
    "document_type_scouted",
    "document_completeness_scouted",
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
    "triage_bucket",
    "triage_score",
    "later_verification_recommendation",
    "later_ingestion_queue_status",
    "calibration_status",
    "calibration_verification_id",
    "calibration_notes",
    "raw_response_ref",
    "notes",
]

SOURCE_SPECS = [
    {
        "state": "PA",
        "wave": "PA-PILOT-BATCH25-2026-07-15",
        "path": DOCS / "gabriel_state_source_scout_candidates_pa_2026-07-15_114435.csv",
        "run_id": "",
    },
    {
        "state": "PA",
        "wave": "PA-PILOT-BATCH25-2026-07-15",
        "path": DOCS / "gabriel_state_source_scout_candidates_pa_2026-07-15_120857.csv",
        "run_id": "",
    },
    {
        "state": "TX",
        "wave": "NWMS-2026-07-16-01",
        "path": DOCS / "national_batch01_tx_live_scout_candidates_2026-07-16.csv",
        "run_id": "tx_2026-07-16_164549",
    },
    {
        "state": "MA",
        "wave": "NWMS-2026-07-16-01",
        "path": DOCS / "national_batch01_ma_live_scout_candidates_2026-07-20.csv",
        "run_id": "ma_2026-07-20_150025",
    },
    {
        "state": "NJ",
        "wave": "NWMS-2026-07-16-01",
        "path": DOCS / "national_batch01_nj_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "nj_2026-07-20_165402",
    },
    {
        "state": "IL",
        "wave": "IL25-2026-07-20",
        "path": DOCS / "national_batch01_il25_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "il_2026-07-20_184849",
    },
    {
        "state": "IL",
        "wave": "IL25.2-2026-07-20",
        "path": DOCS / "national_batch01_il25_2_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "il_2026-07-20_205824",
    },
    {
        "state": "IL",
        "wave": "IL25.3-2026-07-20",
        "path": DOCS / "national_batch01_il25_3_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "il_2026-07-20_215904",
    },
    {
        "state": "NY",
        "wave": "NY25-2026-07-20",
        "path": DOCS / "national_batch01_ny25_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "ny_2026-07-20_200033",
    },
    {
        "state": "CA",
        "wave": "CA25-2026-07-20",
        "path": DOCS / "national_batch01_ca25_live_direct_sdk_scout_candidates_2026-07-20.csv",
        "run_id": "ca_2026-07-21_101012",
    },
    {
        "state": "CA",
        "wave": "SERIALIZED-STAGE1-W01-CA25.2-2026-07-21",
        "path": DOCS
        / "serialized_stage1_worker_01_ca25_live_direct_sdk_scout_candidates_2026-07-21.csv",
        "run_id": "ca_2026-07-21_165516",
    },
    {
        "state": "NJ",
        "wave": "SERIALIZED-STAGE1-W02-NJ25-2026-07-21",
        "path": DOCS
        / "serialized_stage1_worker_02_nj25_live_direct_sdk_scout_candidates_2026-07-21.csv",
        "run_id": "nj_2026-07-21_172457",
    },
    {
        "state": "ALL",
        "allowed_states": {"CA", "NJ", "TX"},
        "wave": "COORD-SERIAL150-2026-07-21",
        "path": DOCS / "gabriel_state_source_scout_candidates_all_2026-07-21_193524.csv",
        "run_id": "all_2026-07-21_193524",
    },
    {
        "state": "ALL",
        "allowed_states": {"CA", "IL", "TX"},
        "wave": "COORD-SERIAL150-WAVE2-2026-07-22",
        "path": DOCS / "gabriel_state_source_scout_candidates_all_2026-07-22_114424.csv",
        "run_id": "all_2026-07-22_114424",
    },
    {
        "state": "ALL",
        "allowed_states": {
            "AK", "AL", "AR", "AZ", "CO", "CT", "DC", "FL", "GA", "HI",
            "IA", "ID", "IN", "KS", "KY", "LA", "MA", "MD", "MI", "MN",
            "MO", "MS", "NC", "NE", "NM", "NV", "OH", "OK", "OR", "RI",
            "SC", "SD", "TN", "UT", "VA", "WA", "WI",
        },
        "wave": "COORD-TIER1-WAVE1-SERIAL150-2026-07-22",
        "path": DOCS / "gabriel_state_source_scout_candidates_all_2026-07-22_164144.csv",
        "run_id": "all_2026-07-22_164144",
    },
]

CALIBRATION_FILES = {
    "TX": DOCS / "national_batch01_tx_source_verification_2026-07-16.csv",
    "MA": DOCS / "national_batch01_ma_source_verification_2026-07-20.csv",
}

TRIAGE_BUCKETS = {
    "high_priority_later_verify",
    "medium_priority_later_verify",
    "low_priority_later_verify",
    "context_only_hold",
    "likely_duplicate_hold",
    "insufficient_hold",
    "rejected_from_calibration",
    "already_canonical_hold",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scout_date(run_id: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", run_id)
    if not match:
        raise ValueError(f"Run ID lacks an ISO date: {run_id}")
    return match.group(1)


def normalized_flag(value: str, default: str = "unclear") -> str:
    value = (value or "").strip().lower()
    if value in {"yes", "no"}:
        return value
    return default


def candidate_stage(row: dict[str, str]) -> str:
    value = (row.get("candidate_stage") or "").strip()
    if value:
        return value
    if (row.get("document_type") or "").strip() in {
        "context_only",
        "agenda_cover_sheet",
        "meeting_minutes",
        "index_page",
    }:
        return "context_only_candidate"
    return "legacy_unverified_candidate"


def load_calibration() -> dict[str, dict[str, dict[str, str]]]:
    result: dict[str, dict[str, dict[str, str]]] = {}
    for state, path in CALIBRATION_FILES.items():
        by_url: dict[str, dict[str, str]] = {}
        for row in read_csv(path):
            url = row["source_url"]
            if url in by_url:
                raise ValueError(f"Duplicate calibration URL in {path}: {url}")
            by_url[url] = row
        result[state] = by_url
    return result


def load_canonical_urls() -> set[str]:
    with (ROOT / "data" / "contracts.csv").open(newline="", encoding="utf-8") as handle:
        return {row["source_url_or_cite"].strip() for row in csv.DictReader(handle)}


def calibration_status(calibration: dict[str, str] | None) -> str:
    if not calibration:
        return "not_calibrated"
    status = calibration["verification_status"]
    mapping = {
        "verified_candidate": "calibration_verified_candidate",
        "partially_verified_candidate": "calibration_partially_verified_candidate",
        "context_only_verified": "calibration_context_only",
        "duplicate_or_superseded": "calibration_already_canonical",
        "unreachable": "calibration_unreachable",
        "insufficient_evidence": "calibration_insufficient_or_rejected",
        "trace_only_not_candidate": "calibration_trace_only",
    }
    return mapping.get(status, f"calibration_{status}")


def is_calibration_wrong_unit(
    row: dict[str, str], calibration: dict[str, str] | None
) -> bool:
    if not calibration:
        return False
    original = (row.get("unit_type") or "").strip()
    verified = (calibration.get("verified_unit_type") or "").strip()
    return original == "non_safety" and verified in {"police", "fire"}


def triage_score(
    row: dict[str, str],
    municipality_units: set[str],
    calibration: dict[str, str] | None,
    exact_canonical: bool,
) -> int:
    score = 25
    calibration_verified = bool(
        calibration
        and calibration["verification_status"]
        in {"verified_candidate", "partially_verified_candidate"}
    )
    owner = (
        calibration.get("source_owner_type", "")
        if calibration_verified
        else row.get("source_owner_type", "")
    ) or "unknown"
    owner = owner.strip()
    if owner in {"city", "state_labor_board"}:
        score += 12
    elif owner == "union":
        score += 8
    elif owner in {"third_party", "news", "school"}:
        score -= 8

    document_type = (
        calibration.get("document_type_verified", "")
        if calibration_verified
        else row.get("document_type", "")
    ) or "unknown"
    document_type = document_type.strip()
    if document_type in {
        "cba",
        "arbitration_award",
        "factfinding",
        "memorandum_or_settlement",
        "wage_schedule_or_compensation_plan",
    }:
        score += 15
    if document_type in {"context_only", "meeting_minutes", "agenda_cover_sheet", "index_page"}:
        score -= 20

    completeness = (
        calibration.get("document_completeness", "")
        if calibration_verified
        else row.get("document_completeness", "")
    ).strip()
    if completeness in {"full", "full_document", "full_document_with_exhibits"}:
        score += 12
    elif completeness in {"partial", "partial_document"}:
        score += 3
    elif completeness in {
        "index_or_landing_page",
        "blocked_or_unreadable",
        "dead_or_unreachable",
    }:
        score -= 15

    if {"police", "fire", "non_safety"}.issubset(municipality_units):
        score += 20
    elif len(municipality_units & {"police", "fire", "non_safety"}) >= 2:
        score += 8

    if (row.get("overlap_with_anchor_cycle") or "").strip() == "overlap":
        score += 12
    elif (row.get("overlap_with_anchor_cycle") or "").strip() == "non_overlap_deferred":
        score -= 15

    visible_year = (row.get("visible_year_evidence") or "").strip()
    if visible_year in {"cover_or_title", "duration_clause", "award_period", "other_operative_text"}:
        score += 6
    elif visible_year in {"index_or_snippet_only", "model_inference_only"}:
        score -= 4

    if (row.get("confidence") or "").strip().lower() == "high":
        score += 5
    elif (row.get("confidence") or "").strip().lower() == "medium":
        score += 2

    if (
        calibration
        and calibration["verification_status"] == "context_only_verified"
    ) or (
        not calibration_verified
        and (
            candidate_stage(row) == "context_only_candidate"
            or normalized_flag(row.get("context_only_flag", ""), default="no") == "yes"
        )
    ):
        score -= 30
    duplicate = (row.get("duplicate_risk") or "none").strip()
    if duplicate == "possible":
        score -= 15
    elif duplicate == "exact_known_source":
        score -= 45
    if exact_canonical:
        score -= 60

    wrong_employer = (row.get("wrong_employer_risk") or "none").strip()
    if wrong_employer == "possible":
        score -= 6
    elif wrong_employer == "high":
        score -= 25
    if normalized_flag(row.get("blocked_or_unreadable_flag", ""), default="no") == "yes":
        score -= 15

    year_text = f"{row.get('contract_years', '')} {row.get('document_title', '')}"
    years = [int(value) for value in re.findall(r"\b(?:19|20)\d{2}\b", year_text)]
    if years and max(years) >= 2018:
        score += 5
    if years and min(years) > 2024:
        score -= 25
    elif years and max(years) < 2014:
        score -= 15

    if calibration:
        recommendation = calibration["ingestion_recommendation"]
        status = calibration["verification_status"]
        if recommendation == "later_ingest_candidate":
            score += 15
        elif recommendation in {"do_not_ingest", "unreachable_do_not_ingest"}:
            score -= 30
        if status == "context_only_verified":
            score -= 30
        elif status == "duplicate_or_superseded":
            score -= 60
        elif status in {"unreachable", "insufficient_evidence"}:
            score -= 35
        if is_calibration_wrong_unit(row, calibration):
            score -= 60
    return max(0, min(100, score))


def triage_bucket(
    row: dict[str, str],
    score: int,
    calibration: dict[str, str] | None,
    exact_canonical: bool,
) -> str:
    status = calibration["verification_status"] if calibration else ""
    if exact_canonical or status == "duplicate_or_superseded":
        return "already_canonical_hold"
    if is_calibration_wrong_unit(row, calibration):
        return "rejected_from_calibration"
    if status == "insufficient_evidence":
        return "rejected_from_calibration"
    if status == "unreachable":
        return "insufficient_hold"
    if status == "context_only_verified":
        return "context_only_hold"
    calibration_overrides_scout_context = status in {
        "verified_candidate",
        "partially_verified_candidate",
    }
    if not calibration_overrides_scout_context and (
        candidate_stage(row) == "context_only_candidate"
        or normalized_flag(row.get("context_only_flag", ""), default="no") == "yes"
    ):
        return "context_only_hold"
    if (row.get("duplicate_risk") or "none").strip() in {"possible", "exact_known_source"}:
        return "likely_duplicate_hold"
    completeness = (
        calibration.get("document_completeness", "")
        if calibration_overrides_scout_context and calibration
        else row.get("document_completeness", "")
    ).strip()
    scout_blocked_applies = not calibration_overrides_scout_context and normalized_flag(
        row.get("blocked_or_unreadable_flag", ""), default="no"
    ) == "yes"
    if completeness in {"blocked_or_unreadable", "dead_or_unreachable"} or scout_blocked_applies:
        return "insufficient_hold"
    if score >= 70:
        return "high_priority_later_verify"
    if score >= 50:
        return "medium_priority_later_verify"
    return "low_priority_later_verify"


def queue_status(bucket: str, calibration: dict[str, str] | None, exact_canonical: bool) -> str:
    if calibration:
        if exact_canonical or bucket == "already_canonical_hold":
            return "calibration_already_canonical"
        status = calibration_status(calibration)
        if bucket == "rejected_from_calibration":
            return "calibration_rejected_or_insufficient"
        return status
    return "unverified_scout_candidate"


def later_ingestion_status(
    bucket: str, calibration: dict[str, str] | None, exact_canonical: bool
) -> str:
    if exact_canonical or bucket == "already_canonical_hold":
        return "already_ingested_canonical"
    if calibration and calibration["ingestion_recommendation"] == "later_ingest_candidate":
        return "verified_later_ingest_candidate"
    if bucket in {
        "context_only_hold",
        "rejected_from_calibration",
        "insufficient_hold",
        "likely_duplicate_hold",
    }:
        return "not_queued_for_ingestion"
    return "ingestion_deferred_pending_coordinated_verification"


def later_verification_recommendation(bucket: str) -> str:
    mapping = {
        "high_priority_later_verify": "include_in_earliest_coordinated_verification_wave",
        "medium_priority_later_verify": "include_after_high_priority_matched_set_leads",
        "low_priority_later_verify": "retain_for_later_gap_or_pattern_review",
        "context_only_hold": "hold_as_locator_or_mechanism_context; verify only with linked qualifying need",
        "likely_duplicate_hold": "deduplicate_against_canonical_and_queue_before source review",
        "insufficient_hold": "hold until a bounded access or completeness task is justified",
        "rejected_from_calibration": "do not re-verify absent new project need or new source evidence",
        "already_canonical_hold": "do not verify or ingest again; retain only for scout-quality accounting",
    }
    return mapping[bucket]


def build_rows() -> list[dict[str, str]]:
    calibration_by_state = load_calibration()
    canonical_urls = load_canonical_urls()
    source_rows: list[tuple[dict, dict[str, str]]] = []
    skipped_missing_locator: dict[str, int] = defaultdict(int)
    for spec in SOURCE_SPECS:
        for row in read_csv(spec["path"]):
            allowed_states = set(spec.get("allowed_states", {spec["state"]}))
            if row["state"] not in allowed_states:
                raise ValueError(f"Unexpected state in {spec['path']}: {row['state']}")
            if not row.get("source_url", "").strip():
                skipped_missing_locator[row["state"]] += 1
                continue
            source_rows.append((spec, row))

    units_by_municipality: dict[str, set[str]] = defaultdict(set)
    for _, row in source_rows:
        units_by_municipality[row["municipality_id"]].add(row["unit_type"])

    counters: dict[str, int] = defaultdict(int)
    output: list[dict[str, str]] = []
    calibration_match_count: dict[str, int] = defaultdict(int)
    for spec, row in source_rows:
        state = row["state"]
        counters[state] += 1
        run_id = (row.get("run_id") or spec["run_id"]).strip()
        calibration = calibration_by_state.get(state, {}).get(row["source_url"])
        if calibration:
            calibration_match_count[state] += 1
        exact_canonical = row["source_url"].strip() in canonical_urls
        score = triage_score(
            row, units_by_municipality[row["municipality_id"]], calibration, exact_canonical
        )
        bucket = triage_bucket(row, score, calibration, exact_canonical)
        if bucket not in TRIAGE_BUCKETS:
            raise ValueError(f"Unexpected triage bucket: {bucket}")

        calibration_note = ""
        calibration_id = ""
        if calibration:
            calibration_id = calibration.get("verification_id", "")
            calibration_note = (
                f"Calibration finding only: verification_status={calibration['verification_status']}; "
                f"ingestion_recommendation={calibration['ingestion_recommendation']}; "
                f"verified_unit_type={calibration.get('verified_unit_type', '')}; "
                f"verified_years={calibration.get('contract_years_verified', '')}; "
                f"next_action={calibration.get('next_action', '')}"
            )

        source_file = spec["path"].relative_to(ROOT).as_posix()
        output.append(
            {
                "queue_id": f"NSCQ-{state}-20260720-{counters[state]:04d}",
                "source_wave": spec["wave"],
                "source_candidate_file": source_file,
                "scout_run_id": run_id,
                "scout_date": scout_date(run_id),
                "state": state,
                "municipality": row["municipality"],
                "municipality_id": row["municipality_id"],
                "unit_type_scouted": row["unit_type"],
                "document_title": row.get("document_title", ""),
                "union_name": row.get("union_name", ""),
                "employer": row.get("employer", ""),
                "contract_years_scouted": row.get("contract_years", ""),
                "source_url": row.get("source_url", ""),
                "source_owner_type": row.get("source_owner_type", "unknown") or "unknown",
                "document_type_scouted": row.get("document_type", "unknown") or "unknown",
                "document_completeness_scouted": row.get(
                    "document_completeness", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "comparator_role": row.get("comparator_role", "not_available_from_legacy_scout")
                or "not_available_from_legacy_scout",
                "wrong_employer_risk": row.get(
                    "wrong_employer_risk", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "context_only_flag": row.get(
                    "context_only_flag", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "visible_year_evidence": row.get(
                    "visible_year_evidence", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "overlap_with_anchor_cycle": row.get(
                    "overlap_with_anchor_cycle", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "duplicate_risk": row.get("duplicate_risk", "not_assessed_in_legacy_scout")
                or "not_assessed_in_legacy_scout",
                "blocked_or_unreadable_flag": row.get(
                    "blocked_or_unreadable_flag", "not_available_from_legacy_scout"
                )
                or "not_available_from_legacy_scout",
                "cycle_match_notes": row.get("cycle_match_notes", ""),
                "why_relevant": row.get("why_relevant", ""),
                "confidence": row.get("confidence", ""),
                "candidate_stage": candidate_stage(row),
                "needs_verification_reason": row.get("needs_verification_reason", "")
                or "Legacy scout row; verify source identity, employer, unit, years, completeness, wages, duplicates, and cycle overlap in a later coordinated wave.",
                "scout_stage_status": queue_status(bucket, calibration, exact_canonical),
                "verification_priority": row.get("verification_priority", "")
                or row.get("likely_ingest_priority", "")
                or "unranked_legacy",
                "triage_bucket": bucket,
                "triage_score": str(score),
                "later_verification_recommendation": later_verification_recommendation(bucket),
                "later_ingestion_queue_status": later_ingestion_status(
                    bucket, calibration, exact_canonical
                ),
                "calibration_status": calibration_status(calibration),
                "calibration_verification_id": calibration_id,
                "calibration_notes": calibration_note,
                "raw_response_ref": row.get("raw_response_ref", ""),
                "notes": (
                    f"Built from {source_file}. Triage uses preserved scout metadata and, where "
                    "present, explicitly non-final TX/MA calibration findings; no new URL review."
                ),
            }
        )

    expected = {
        "AK": 3,
        "AL": 4,
        "AZ": 12,
        "PA": 75,
        "TX": 113,
        "MA": 46,
        "NJ": 94,
        "IL": 295,
        "NY": 57,
        "CA": 351,
        "CO": 11,
        "CT": 10,
        "DC": 5,
        "FL": 38,
        "GA": 2,
        "HI": 3,
        "IA": 11,
        "ID": 2,
        "KS": 3,
        "KY": 5,
        "LA": 5,
        "MD": 3,
        "MI": 8,
        "MN": 10,
        "MO": 6,
        "NC": 3,
        "NE": 7,
        "NM": 6,
        "NV": 12,
        "OH": 7,
        "OK": 8,
        "OR": 11,
        "RI": 3,
        "SC": 1,
        "SD": 3,
        "TN": 9,
        "UT": 3,
        "VA": 7,
        "WA": 14,
        "WI": 11,
    }
    observed = {state: counters[state] for state in expected}
    if observed != expected:
        raise ValueError(f"Unexpected queue source counts: {observed} != {expected}")
    if dict(skipped_missing_locator) != {"IL": 1}:
        raise ValueError(
            "Expected one preserved IL25.3 parsed row to remain outside the source queue "
            f"because it lacks a locator: {dict(skipped_missing_locator)}"
        )
    if calibration_match_count != {"TX": 6, "MA": 24}:
        raise ValueError(f"Calibration joins are incomplete: {dict(calibration_match_count)}")
    return output


def write_and_validate(rows: list[dict[str, str]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    parsed = read_csv(OUTPUT)
    if len(parsed) != len(rows):
        raise ValueError("Queue row count changed on parse-back")
    if len({row["queue_id"] for row in parsed}) != len(parsed):
        raise ValueError("Queue IDs are not unique")
    if set(parsed[0]) != set(QUEUE_FIELDS):
        raise ValueError("Queue output schema changed on parse-back")
    invalid = sorted({row["triage_bucket"] for row in parsed} - TRIAGE_BUCKETS)
    if invalid:
        raise ValueError(f"Invalid triage buckets: {invalid}")
    missing_urls = [row["queue_id"] for row in parsed if not row["source_url"].strip()]
    if missing_urls:
        raise ValueError(f"Queue rows are missing source URLs: {missing_urls}")


def main() -> int:
    rows = build_rows()
    write_and_validate(rows)
    counts: dict[str, int] = defaultdict(int)
    buckets: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["state"]] += 1
        buckets[row["triage_bucket"]] += 1
    print(f"queue_rows={len(rows)}")
    print("queue_rows_by_state=" + ",".join(f"{key}:{counts[key]}" for key in sorted(counts)))
    print("triage_buckets=" + ",".join(f"{key}:{buckets[key]}" for key in sorted(buckets)))
    print(f"output={OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
