#!/usr/bin/env python3
"""Build static dashboard JSON from national scout accounting outputs.

This builder is local-only and non-destructive. It reads existing analysis CSVs
and writes summary JSON under ``docs/dashboard/data``. It does not open source
URLs, call a model, verify or ingest sources, codify text, or modify canonical
contract/city-coverage data.

The generated files intentionally preserve stage boundaries. Scout candidates
remain unverified leads. Project-wide verified-source, ingestion, wage, and
regression metrics are null until dedicated dashboard inputs exist.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "docs" / "analysis"
OUTPUT_DIR = ROOT / "docs" / "dashboard" / "data"

STATE_COVERAGE_PATH = ANALYSIS_DIR / "national_scout_coverage_state.csv"
MUNICIPALITY_COVERAGE_PATH = (
    ANALYSIS_DIR / "national_scout_coverage_municipality_2026-07-20.csv"
)
MUNICIPALITY_UNIVERSE_PATH = ANALYSIS_DIR / "national_municipality_universe.csv"
CANDIDATE_QUEUE_PATH = (
    ANALYSIS_DIR / "national_scout_candidate_queue_2026-07-20.csv"
)
PRIORITY_TIERS_PATH = (
    ANALYSIS_DIR / "national_municipality_priority_tiers_2026-07-22.csv"
)
STATE_PRIORITY_PATH = ANALYSIS_DIR / "state_priority_summary_2026-07-22.csv"
TOP_PRIORITY_TARGETS_PATH = (
    ANALYSIS_DIR / "national_priority_tier_top_targets_2026-07-22.csv"
)
SCOUT_YIELD_STATE_PATH = ANALYSIS_DIR / "scout_yield_learning_by_state_2026-07-22.csv"
SCOUT_YIELD_WAVE_PATH = ANALYSIS_DIR / "scout_yield_learning_by_wave_2026-07-22.csv"
HOSTED_SEARCH_RECOMMENDATION_PATH = (
    ANALYSIS_DIR / "hosted_search_transport_recommendation_2026-07-22.md"
)
CLAIM_REGISTER_PATH = ANALYSIS_DIR / "claim_register_2026-07-12.csv"
STATE_CITY_CLAIM_MAP_PATH = ANALYSIS_DIR / "state_city_claim_map_2026-07-12.csv"
HYPOTHESIS_TRACKER_PATH = ANALYSIS_DIR / "hypothesis_tracker_2026-07-12.csv"
REPORTS_INDEX_SOURCE_PATH = (
    ROOT / "docs" / "dashboard" / "reports" / "reports_index.json"
)
VERIFICATION_ROUTING_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "verification_ledgers"
    / "verified_source_routing_summary_latest.json"
)
VERIFICATION_ROUND2_LIVE_STATUS_PATH = (
    ANALYSIS_DIR
    / "verification_rounds"
    / "VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24"
    / "verification_live_collection_summary.json"
)
CONTENT_TRIAGE_ROUND1_MANIFEST_PATH = (
    ANALYSIS_DIR
    / "content_triage_rounds"
    / "CONTENT-TRIAGE-ROUND1-1000-2026-07-24"
    / "content_triage_round_manifest.json"
)
CONTENT_TRIAGE_ROUND1_METADATA_STATUS_PATH = (
    ANALYSIS_DIR
    / "content_triage_rounds"
    / "CONTENT-TRIAGE-ROUND1-1000-2026-07-24"
    / "metadata_only_collection_summary.json"
)
CONTENT_TRIAGE_REMAINDER_MANIFEST_PATH = (
    ANALYSIS_DIR
    / "content_triage_rounds"
    / "CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24"
    / "content_triage_round_manifest.json"
)
CONTENT_TRIAGE_REMAINDER_METADATA_STATUS_PATH = (
    ANALYSIS_DIR
    / "content_triage_rounds"
    / "CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24"
    / "metadata_only_collection_summary.json"
)
CONTENT_TRIAGE_CUMULATIVE_LEDGER_PATH = (
    ANALYSIS_DIR
    / "content_triage_ledgers"
    / "content_triage_ledger_latest.csv"
)
CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "content_triage_ledgers"
    / "content_triage_summary_latest.json"
)
SOURCE_REVIEW_PILOT_MANIFEST_PATH = (
    ANALYSIS_DIR
    / "source_review_pilots"
    / "SOURCE-REVIEW-PILOT1-150-2026-07-24"
    / "source_review_pilot_manifest.json"
)

SCOUT_CHECKPOINT_TARGET = 2_000
COORDINATED_WAVE_SIZE = 150
CURRENT_SOURCE_ACCOUNTING_COMMIT = "98ad608"
PARALLEL_SCOUT_ROUND_ID = "POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23"
FIRST_VERIFICATION_ROUND_ID = "VERIFICATION-SCALE-ROUND1-3X750-2026-07-23"
SECOND_VERIFICATION_ROUND_ID = (
    "VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24"
)
FIRST_VERIFICATION_ROUND_ROWS = 2_250
VERIFICATION_BATCH_SIZE = 750
VERIFICATION_LANES = 3
VERIFICATION_CONCURRENCY_PER_LANE = 8
NEXT_PARALLEL_SCOUT_ROUND_ID = "NONE-BROAD-SCOUTING-PAUSED-AFTER-CHECKPOINT"
NEXT_ROUND_LANES = 0
NEXT_ROUND_ROWS_PER_LANE = 0
NEXT_ROUND_ATTEMPTED = 0
NEXT_ROUND_EXPECTED_PARSEABLE = 0
NEXT_ROUND_EXPECTED_POST_COVERAGE = 2_436

REQUIRED_PATHS = [
    STATE_COVERAGE_PATH,
    MUNICIPALITY_COVERAGE_PATH,
    MUNICIPALITY_UNIVERSE_PATH,
    CANDIDATE_QUEUE_PATH,
    PRIORITY_TIERS_PATH,
    STATE_PRIORITY_PATH,
    TOP_PRIORITY_TARGETS_PATH,
    SCOUT_YIELD_STATE_PATH,
    SCOUT_YIELD_WAVE_PATH,
    REPORTS_INDEX_SOURCE_PATH,
]
OPTIONAL_PATHS = [
    CLAIM_REGISTER_PATH,
    STATE_CITY_CLAIM_MAP_PATH,
    HYPOTHESIS_TRACKER_PATH,
    HOSTED_SEARCH_RECOMMENDATION_PATH,
    VERIFICATION_ROUTING_SUMMARY_PATH,
    VERIFICATION_ROUND2_LIVE_STATUS_PATH,
    CONTENT_TRIAGE_ROUND1_MANIFEST_PATH,
    CONTENT_TRIAGE_ROUND1_METADATA_STATUS_PATH,
    CONTENT_TRIAGE_REMAINDER_MANIFEST_PATH,
    CONTENT_TRIAGE_REMAINDER_METADATA_STATUS_PATH,
    CONTENT_TRIAGE_CUMULATIVE_LEDGER_PATH,
    CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH,
    SOURCE_REVIEW_PILOT_MANIFEST_PATH,
]

STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

VERIFY_BUCKETS = {
    "high_priority_later_verify": "high",
    "medium_priority_later_verify": "medium",
    "low_priority_later_verify": "low",
}

GLOBAL_LIMITATIONS = [
    "Scout coverage records parseable source-discovery outcomes, not source verification.",
    "Candidate rows are unverified leads and must not be cited as claim evidence.",
    "A parseable empty candidate list is a completed scout outcome, not proof that no source exists.",
    "Connection-only failures are excluded from discovery coverage and counted separately.",
    "Likely matched-set groups are scheduling leads inferred from scout unit labels, not verified city-cycle matches.",
    "URL-routing outcomes cover the current candidate queue; content relevance, ingestion, wage extraction, codification, and regression metrics are not yet available project-wide.",
    "Municipality priority tiers are transparent research-operational heuristics, not claims about unionization, departments, source availability, wage gaps, or causal effects.",
    "The 2,000-municipality checkpoint is a project-management target, not an evidentiary threshold.",
]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def as_int(value: str | int | None) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def as_float(value: str | float | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def percent(numerator: int, denominator: int) -> float:
    return round((100.0 * numerator / denominator), 4) if denominator else 0.0


def generated_at() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def base_metadata(
    *,
    timestamp: str,
    source_paths: list[Path],
    data_vintage: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "generated_at": timestamp,
        "data_vintage": data_vintage,
        "source_files": [relative(path) for path in source_paths if path.exists()],
        "warnings": warnings,
        "limitations": GLOBAL_LIMITATIONS,
    }


def write_json(name: str, payload: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {relative(path)}")
    return payload


def build_reports_index_layer(
    *, source_index: dict[str, Any], metadata: dict[str, Any]
) -> dict[str, Any]:
    required_report_fields = {
        "id",
        "title",
        "report_type",
        "date",
        "checkpoint",
        "summary",
        "pdf_path",
        "markdown_source_path",
        "tags",
        "current",
        "created_commit",
        "metrics_snapshot",
    }
    required_metric_fields = {
        "scout_covered",
        "candidate_queue_rows",
        "candidate_positive",
        "parseable_empty",
        "failure_only",
        "tier1_eligible",
        "tier2_eligible",
    }
    reports = source_index.get("reports")
    if not isinstance(reports, list) or not reports:
        raise ValueError("Report index must contain a non-empty reports list")

    report_ids: list[str] = []
    current_count = 0
    for index, report in enumerate(reports, start=1):
        if not isinstance(report, dict):
            raise ValueError(f"Report index entry {index} must be an object")
        missing = sorted(required_report_fields - set(report))
        if missing:
            raise ValueError(f"Report index entry {index} is missing: {missing}")
        if not all(isinstance(report[field], str) and report[field].strip() for field in required_report_fields - {"tags", "current", "metrics_snapshot"}):
            raise ValueError(f"Report index entry {index} has a missing text value")
        if not isinstance(report["tags"], list) or not all(
            isinstance(tag, str) and tag.strip() for tag in report["tags"]
        ):
            raise ValueError(f"Report index entry {index} tags must be non-empty strings")
        if not isinstance(report["current"], bool):
            raise ValueError(f"Report index entry {index} current must be boolean")
        current_count += int(report["current"])
        metrics = report["metrics_snapshot"]
        if not isinstance(metrics, dict) or set(metrics) != required_metric_fields:
            raise ValueError(
                f"Report index entry {index} metrics_snapshot must contain exactly "
                f"{sorted(required_metric_fields)}"
            )
        if any(not isinstance(value, int) or value < 0 for value in metrics.values()):
            raise ValueError(f"Report index entry {index} metrics must be nonnegative integers")
        pdf_path = ROOT / "docs" / "dashboard" / report["pdf_path"]
        markdown_path = ROOT / report["markdown_source_path"]
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Dashboard report PDF is missing: {relative(pdf_path)}")
        if not markdown_path.is_file():
            raise FileNotFoundError(
                f"Dashboard report Markdown source is missing: {relative(markdown_path)}"
            )
        report_ids.append(report["id"])

    if len(report_ids) != len(set(report_ids)):
        raise ValueError("Report index contains duplicate report IDs")
    if current_count != 1:
        raise ValueError("Report index must contain exactly one current report")

    return {
        "schema_version": source_index.get("schema_version", "1.0.0"),
        "generated_at": metadata["generated_at"],
        "data_vintage": source_index.get("data_vintage", metadata["data_vintage"]),
        "source_file": relative(REPORTS_INDEX_SOURCE_PATH),
        "reports": reports,
        "disclaimer": (
            "Reports summarize source-discovery and research-operations status. "
            "Candidate rows remain unverified leads; no report in this index should "
            "be interpreted as a wage-gap estimate or causal finding."
        ),
    }


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def discovery_readiness_score(
    *,
    covered: int,
    candidate_positive: int,
    high_priority_rows: int,
    likely_matched_sets: int,
    has_claim_context: bool,
) -> float:
    """Return an operational triage score, not an evidence-strength score."""

    if covered == 0 and not has_claim_context:
        return 0.0
    score = 0.0
    if covered:
        score += 20.0
        score += 20.0 * candidate_positive / covered
        score += 20.0 * min(high_priority_rows / 10.0, 1.0)
        score += 30.0 * min(likely_matched_sets / 10.0, 1.0)
    if has_claim_context:
        score += 10.0
    return round(min(score, 100.0), 1)


def claim_readiness_level(
    *,
    covered: int,
    candidate_positive: int,
    likely_matched_sets: int,
    has_claim_context: bool,
) -> str:
    if likely_matched_sets:
        return "matched_set_leads_need_verification"
    if candidate_positive:
        return "candidate_leads_need_verification"
    if covered:
        return "scout_coverage_only"
    if has_claim_context:
        return "claim_context_without_current_scout_coverage"
    return "not_started"


def build_state_summary(
    *,
    state_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    claim_rows: list[dict[str, str]],
    claim_map_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    claim_ids_by_state: dict[str, set[str]] = defaultdict(set)
    for row in claim_rows:
        for state in split_semicolon(row.get("states_in_scope", "")):
            claim_ids_by_state[state].add(row.get("claim_id", ""))

    claim_map_count_by_state = Counter(row.get("state", "") for row in claim_map_rows)
    queue_municipalities_by_state: dict[str, set[str]] = defaultdict(set)
    queue_bucket_by_state: dict[str, Counter[str]] = defaultdict(Counter)
    for row in queue_rows:
        state = row.get("state", "")
        municipality_key = row.get("municipality_id") or row.get("municipality", "")
        queue_municipalities_by_state[state].add(municipality_key)
        queue_bucket_by_state[state][row.get("triage_bucket", "unknown")] += 1

    states: list[dict[str, Any]] = []
    for row in sorted(state_rows, key=lambda item: item["state"]):
        state = row["state"]
        if state not in STATE_NAMES:
            raise ValueError(f"Unknown state abbreviation in coverage table: {state}")

        universe = as_int(row["municipalities_in_universe"])
        covered = as_int(row["municipalities_scouted"])
        candidate_positive = as_int(row["municipalities_scouted_with_candidates"])
        no_candidate = as_int(row["municipalities_scouted_no_candidates"])
        failure_only = as_int(row["municipalities_scout_attempt_failed_connection"])
        candidate_rows = as_int(row["candidate_rows_total"])
        likely_sets = as_int(row["municipalities_with_likely_triad"])
        high_priority = as_int(row["high_priority_candidate_rows"])
        claim_ids = sorted(item for item in claim_ids_by_state[state] if item)
        claim_map_count = claim_map_count_by_state[state]
        has_claim_context = bool(claim_ids or claim_map_count)
        score = discovery_readiness_score(
            covered=covered,
            candidate_positive=candidate_positive,
            high_priority_rows=high_priority,
            likely_matched_sets=likely_sets,
            has_claim_context=has_claim_context,
        )
        level = claim_readiness_level(
            covered=covered,
            candidate_positive=candidate_positive,
            likely_matched_sets=likely_sets,
            has_claim_context=has_claim_context,
        )

        if covered:
            narrative = (
                f"{covered:,} of {universe:,} municipal governments have parseable "
                f"scout outcomes; {candidate_positive:,} are candidate-positive, "
                f"{no_candidate:,} returned parseable empty lists, and {likely_sets:,} "
                "have likely police/fire/non-safety lead groups. All national-queue "
                "leads remain unverified unless separately documented."
            )
        elif has_claim_context:
            narrative = (
                "The claim registry contains prior structured context for this state, "
                "but the current national scout coverage table records no successful "
                "municipality discovery run."
            )
        else:
            narrative = (
                "No successful national source-discovery run is recorded for this "
                "state yet; evidence and wage-analysis readiness are not established."
            )

        bucket_counts = queue_bucket_by_state[state]
        states.append(
            {
                "state": state,
                "state_name": STATE_NAMES[state],
                "municipality_universe": universe,
                "scout_coverage_count": covered,
                "scout_coverage_rate": percent(covered, universe),
                "candidate_positive_count": candidate_positive,
                "no_candidate_count": no_candidate,
                "failed_scout_municipality_count": failure_only,
                "failed_scout_attempt_count": as_int(
                    row["connection_failed_attempts_excluded_from_coverage"]
                ),
                "candidate_rows": candidate_rows,
                "high_priority_queue_count": high_priority,
                "medium_priority_queue_count": bucket_counts[
                    "medium_priority_later_verify"
                ],
                "low_priority_queue_count": bucket_counts[
                    "low_priority_later_verify"
                ],
                "hold_or_rejected_queue_count": sum(
                    count
                    for bucket, count in bucket_counts.items()
                    if bucket not in VERIFY_BUCKETS
                ),
                "queued_municipality_count": len(queue_municipalities_by_state[state]),
                "likely_matched_set_count": likely_sets,
                "calibration_verified_municipality_count": as_int(
                    row["calibration_verified_municipalities"]
                ),
                "verified_count": None,
                "ingested_count": None,
                "claim_ids_in_prior_registry": claim_ids,
                "claim_mapped_city_count": claim_map_count,
                "claim_readiness_level": level,
                "evidence_readiness_score": score,
                "map_color_metric": {
                    "field": "evidence_readiness_score",
                    "value": score,
                    "scale": "0_to_100_operational_triage_only",
                },
                "short_state_narrative": narrative,
                "printable_report_data": {
                    "route": f"#/state/{state}",
                    "title": f"{STATE_NAMES[state]} municipal labor evidence brief",
                    "headline_metrics": [
                        {"label": "Municipal universe", "value": universe},
                        {"label": "Scout covered", "value": covered},
                        {"label": "Candidate positive", "value": candidate_positive},
                        {"label": "Likely matched-set leads", "value": likely_sets},
                    ],
                    "narrative": narrative,
                    "status_caveat": (
                        "Discovery-stage counts do not establish source validity, "
                        "contract completeness, matched bargaining cycles, wage gaps, "
                        "causal mechanisms, or claim support."
                    ),
                },
            }
        )

    active_states = sum(item["scout_coverage_count"] > 0 for item in states)
    return {
        "metadata": metadata,
        "metric_definition": {
            "evidence_readiness_score": (
                "Operational dashboard triage score: 20 points for any parseable "
                "coverage, up to 20 for candidate-positive share, up to 20 for high-"
                "priority lead volume, up to 30 for likely matched-set lead volume, "
                "and 10 for prior claim-registry context. It is not evidence strength "
                "and cannot make a state claim-ready."
            ),
            "map_color_metric": "evidence_readiness_score",
        },
        "totals": {
            "states_and_dc": len(states),
            "states_with_scout_coverage": active_states,
            "municipality_universe": sum(item["municipality_universe"] for item in states),
            "scout_covered_municipalities": sum(
                item["scout_coverage_count"] for item in states
            ),
            "candidate_positive_municipalities": sum(
                item["candidate_positive_count"] for item in states
            ),
            "no_candidate_municipalities": sum(
                item["no_candidate_count"] for item in states
            ),
            "failed_scout_municipalities": sum(
                item["failed_scout_municipality_count"] for item in states
            ),
            "failed_scout_attempts": sum(
                item["failed_scout_attempt_count"] for item in states
            ),
            "candidate_rows": sum(item["candidate_rows"] for item in states),
            "likely_matched_set_groups": sum(
                item["likely_matched_set_count"] for item in states
            ),
            "verified_sources": None,
            "ingested_sources": None,
            "wage_observations": None,
        },
        "states": states,
    }


def build_candidate_queue_summary(
    *,
    queue_rows: list[dict[str, str]],
    state_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    triage = Counter(row.get("triage_bucket", "unknown") for row in queue_rows)
    by_unit = Counter(row.get("unit_type_scouted", "unknown") for row in queue_rows)
    by_confidence = Counter(row.get("confidence", "unknown") for row in queue_rows)
    by_verification_priority = Counter(
        row.get("verification_priority", "unknown") for row in queue_rows
    )
    likely_sets = {
        row["state"]: as_int(row["municipalities_with_likely_triad"])
        for row in state_rows
    }

    state_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in queue_rows:
        state_groups[row.get("state", "")].append(row)

    by_state: list[dict[str, Any]] = []
    for state, rows in sorted(state_groups.items()):
        buckets = Counter(row.get("triage_bucket", "unknown") for row in rows)
        municipality_keys = {
            row.get("municipality_id") or f"{state}:{row.get('municipality', '')}"
            for row in rows
        }
        by_state.append(
            {
                "state": state,
                "state_name": STATE_NAMES[state],
                "candidate_rows": len(rows),
                "municipalities_with_queue_rows": len(municipality_keys),
                "high_priority_rows": buckets["high_priority_later_verify"],
                "medium_priority_rows": buckets["medium_priority_later_verify"],
                "low_priority_rows": buckets["low_priority_later_verify"],
                "hold_or_rejected_rows": sum(
                    count
                    for bucket, count in buckets.items()
                    if bucket not in VERIFY_BUCKETS
                ),
                "likely_matched_set_municipalities": likely_sets.get(state, 0),
            }
        )

    municipality_keys = {
        row.get("municipality_id") or f"{row.get('state', '')}:{row.get('municipality', '')}"
        for row in queue_rows
    }
    later_verify_total = sum(triage[bucket] for bucket in VERIFY_BUCKETS)
    return {
        "metadata": metadata,
        "stage": "unverified_scout_candidate_queue",
        "totals": {
            "candidate_rows": len(queue_rows),
            "municipalities_with_queue_rows": len(municipality_keys),
            "high_priority_rows": triage["high_priority_later_verify"],
            "medium_priority_rows": triage["medium_priority_later_verify"],
            "low_priority_rows": triage["low_priority_later_verify"],
            "later_verification_rows": later_verify_total,
            "hold_or_rejected_rows": len(queue_rows) - later_verify_total,
        },
        "by_state": by_state,
        "by_unit_type": dict(sorted(by_unit.items())),
        "by_triage_bucket": dict(sorted(triage.items())),
        "by_scout_confidence": dict(sorted(by_confidence.items())),
        "by_verification_priority_label": dict(
            sorted(by_verification_priority.items())
        ),
        "interpretation": (
            "Priority is a later-verification scheduling field. It is not source "
            "verification, ingestion approval, codified evidence, or claim support."
        ),
    }


def build_coverage_funnel(
    *,
    state_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    total = lambda field: sum(as_int(row[field]) for row in state_rows)
    return {
        "metadata": metadata,
        "current_funnel": [
            {
                "stage": "municipality_universe",
                "label": "Municipal governments in universe",
                "value": total("municipalities_in_universe"),
                "status": "current",
            },
            {
                "stage": "scout_covered",
                "label": "Parseable scout-covered municipalities",
                "value": total("municipalities_scouted"),
                "status": "current",
            },
            {
                "stage": "candidate_positive",
                "label": "Candidate-positive municipalities",
                "value": total("municipalities_scouted_with_candidates"),
                "status": "current_unverified",
            },
            {
                "stage": "queued_for_later_verification",
                "label": "Municipalities queued for later verification",
                "value": total("municipalities_queued_for_later_verification"),
                "status": "current_unverified",
            },
            {
                "stage": "likely_matched_set_leads",
                "label": "Likely matched-set lead groups",
                "value": total("municipalities_with_likely_triad"),
                "status": "current_unverified",
            },
        ],
        "future_funnel": [
            {
                "stage": "verified_sources",
                "label": "Project-wide verified sources",
                "value": None,
                "status": "future_input_required",
            },
            {
                "stage": "ingested_contracts",
                "label": "Dashboard-ready ingested contracts",
                "value": None,
                "status": "future_input_required",
            },
            {
                "stage": "extracted_wage_observations",
                "label": "Structured wage observations",
                "value": None,
                "status": "future_input_required",
            },
            {
                "stage": "codified_mechanism_evidence",
                "label": "Dashboard-ready codified mechanism evidence",
                "value": None,
                "status": "future_input_required",
            },
            {
                "stage": "claim_ready_matched_sets",
                "label": "Claim-ready matched city-cycle sets",
                "value": None,
                "status": "future_input_required",
            },
        ],
        "separate_failure_accounting": {
            "failure_only_municipalities": total(
                "municipalities_scout_attempt_failed_connection"
            ),
            "connection_failed_attempts_excluded_from_coverage": total(
                "connection_failed_attempts_excluded_from_coverage"
            ),
            "note": (
                "Attempts are infrastructure outcomes, not source findings, and are "
                "not included in scout-covered counts."
            ),
        },
    }


def build_analysis_readiness(
    *,
    state_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    claim_rows: list[dict[str, str]],
    claim_map_rows: list[dict[str, str]],
    hypothesis_rows: list[dict[str, str]],
    optional_availability: dict[str, bool],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    total = lambda field: sum(as_int(row[field]) for row in state_rows)
    claim_statuses = Counter(row.get("claim_status", "unknown") for row in claim_rows)
    report_ready = Counter(row.get("report_ready", "unknown") for row in claim_rows)
    hypothesis_support = Counter(
        row.get("current_support_level", "unknown") for row in hypothesis_rows
    )
    return {
        "metadata": metadata,
        "overall_status": "verification_scale_up_planned_after_discovery_checkpoint",
        "current_inputs": {
            "national_queue_available": bool(queue_rows),
            "national_coverage_available": bool(state_rows),
            "claim_register_available": optional_availability[relative(CLAIM_REGISTER_PATH)],
            "state_city_claim_map_available": optional_availability[
                relative(STATE_CITY_CLAIM_MAP_PATH)
            ],
            "hypothesis_tracker_available": optional_availability[
                relative(HYPOTHESIS_TRACKER_PATH)
            ],
        },
        "source_discovery_readiness": {
            "municipalities_scout_covered": total("municipalities_scouted"),
            "candidate_rows": len(queue_rows),
            "candidate_positive_municipalities": total(
                "municipalities_scouted_with_candidates"
            ),
            "likely_matched_set_leads": total("municipalities_with_likely_triad"),
            "assessment": "ready_for_PI_facing_discovery_status_reporting",
        },
        "claim_inventory_context": {
            "claim_count": len(claim_rows) if optional_availability[relative(CLAIM_REGISTER_PATH)] else None,
            "claim_status_counts": dict(sorted(claim_statuses.items())),
            "report_ready_label_counts": dict(sorted(report_ready.items())),
            "state_city_claim_map_rows": len(claim_map_rows)
            if optional_availability[relative(STATE_CITY_CLAIM_MAP_PATH)]
            else None,
            "hypothesis_count": len(hypothesis_rows)
            if optional_availability[relative(HYPOTHESIS_TRACKER_PATH)]
            else None,
            "hypothesis_support_counts": dict(sorted(hypothesis_support.items())),
            "caveat": (
                "These are prior structured claim/codify contexts. New national "
                "scout leads do not strengthen them without verification, ingestion, "
                "and appropriate evidence review."
            ),
        },
        "stage_availability": {
            "scout_stage": {
                "available": True,
                "display_status": "current",
            },
            "verification_stage": {
                "available": False,
                "display_status": "framework_prepared_live_verification_not_started",
                "count": 0,
            },
            "ingestion_stage": {
                "available": False,
                "display_status": "dashboard_input_not_available",
                "count": None,
            },
            "codified_stage": {
                "available": bool(claim_rows or hypothesis_rows),
                "display_status": "prior_claim_context_only_not_national_queue_promotion",
                "count": None,
            },
            "wage_extraction_stage": {
                "available": False,
                "display_status": "planned_after_scout_checkpoint_and_verification",
                "observation_count": None,
            },
            "regression_stage": {
                "available": False,
                "display_status": "deferred_until_much_later",
                "estimate_count": None,
            },
        },
        "analyses_available_now": [
            "municipal universe and scout coverage rates",
            "candidate yield and parseable-empty rates",
            "connection-failure accounting",
            "candidate priority and unit-type composition",
            "likely matched-set lead counts for later verification planning",
            "state-level discovery-readiness comparisons",
        ],
        "analyses_not_yet_supported": [
            "verified source completeness rates across the national queue",
            "structured police, fire, and non-safety wage-gap estimates",
            "causal or mechanism regressions using scout metadata",
            "confidence levels for national substantive claims",
            "claim promotion based only on candidate counts",
        ],
        "promotion_gate": (
            "Do not show wage-gap or regression results until a dedicated, validated "
            "structured wage input supplies municipality, bargaining unit, occupation, "
            "cycle, wage concept, provenance, and matched-set identifiers."
        ),
    }


def build_priority_summary(
    *,
    priority_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    eligible = [
        row for row in priority_rows if row["future_scout_eligible_flag"] == "yes"
    ]
    tier_eligible = Counter(row["priority_tier"] for row in eligible)
    confidence = Counter(row["priority_confidence"] for row in priority_rows)
    covered = sum(
        row["scout_coverage_status"]
        in {"scouted_with_candidates", "scouted_no_candidates"}
        for row in priority_rows
    )
    return {
        **metadata,
        "stage": "research_operational_priority_heuristic",
        "priority_vintage_status": "current_after_aggressive_attempt3_merge",
        "successful_scouts_since_priority_refresh": 0,
        "selection_guard": (
            "Reconcile targets against current coverage and failure-only status before "
            "selecting another ordinary wave."
        ),
        "totals": {
            "municipality_universe": len(priority_rows),
            "scout_covered": covered,
            "future_scout_eligible": len(eligible),
            "tier_1_eligible": tier_eligible["Tier 1"],
            "tier_2_eligible": tier_eligible["Tier 2"],
            "tier_3_eligible": tier_eligible["Tier 3"],
            "tier_4_eligible": tier_eligible["Tier 4"],
            "tier_5_eligible": tier_eligible["Tier 5"],
            "failure_only_retry_targets": sum(
                row["failure_only_flag"] == "yes" for row in priority_rows
            ),
            "priority_confidence": {
                "high": confidence["high"],
                "medium": confidence["medium"],
                "low": confidence["low"],
            },
        },
        "tier_definitions": [
            {"tier": "Tier 1", "label": "Highest-priority scout targets"},
            {"tier": "Tier 2", "label": "Strong-priority scout targets"},
            {"tier": "Tier 3", "label": "Strategic or moderate-priority targets"},
            {"tier": "Tier 4", "label": "Low-priority targets"},
            {"tier": "Tier 5", "label": "Defer for current research design"},
        ],
        "disclaimer": (
            "Scores rank research-operational scouting value only. They do not establish "
            "unionization, department existence, source availability, wage differences, "
            "or causal effects."
        ),
    }


def build_state_priority_layer(
    *,
    state_priority_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    states: list[dict[str, Any]] = []
    for row in state_priority_rows:
        tier1 = as_int(row["tier_1_eligible_count"])
        tier2 = as_int(row["tier_2_eligible_count"])
        covered = as_int(row["scout_covered_count"])
        universe = as_int(row["universe_count"])
        states.append(
            {
                "state": row["state"],
                "state_name": STATE_NAMES[row["state"]],
                "total_universe": universe,
                "covered": covered,
                "eligible": as_int(row["future_scout_eligible_count"]),
                "tier_1_eligible": tier1,
                "tier_2_eligible": tier2,
                "tier_3_eligible": as_int(row["tier_3_eligible_count"]),
                "tier_4_eligible": as_int(row["tier_4_eligible_count"]),
                "tier_5_eligible": as_int(row["tier_5_eligible_count"]),
                "tier_1_plus_2_remaining": tier1 + tier2,
                "high_priority_coverage_rate_pct": (
                    round(100.0 * float(row["high_priority_coverage_rate"]), 4)
                    if row["high_priority_coverage_rate"]
                    else 0.0
                ),
                "state_yield_score": as_float(row["state_yield_score"]),
                "state_score_confidence": row["state_score_confidence"],
                "candidate_positive_rate_pct": (
                    round(100.0 * float(row["candidate_positive_rate"]), 4)
                    if row["candidate_positive_rate"]
                    else None
                ),
                "recommended_next_wave_status": row[
                    "recommended_next_wave_status"
                ],
            }
        )
    return {
        **metadata,
        "stage": "research_operational_priority_heuristic",
        "priority_vintage_status": "current_after_aggressive_attempt3_merge",
        "successful_scouts_since_priority_refresh": 0,
        "safe_map_metrics": [
            "tier_1_eligible",
            "high_priority_coverage_rate_pct",
            "tier_1_plus_2_remaining",
        ],
        "states": states,
        "disclaimer": (
            "State priority values guide scouting order only; sparse-state yield estimates "
            "are smoothed and confidence-labeled."
        ),
    }


def build_top_priority_targets_layer(
    *,
    top_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    targets = [
        {
            "rank": as_int(row["rank"]),
            "state": row["state"],
            "municipality": row["municipality"],
            "municipality_id": row["municipality_id"],
            "government_name": row["government_name"],
            "government_type": row["government_type"],
            "population": as_int(row["population"]),
            "score": as_float(row["total_priority_score"]),
            "tier": row["priority_tier"],
            "confidence": row["priority_confidence"],
            "retry_flag": row["retry_flag"] == "yes",
            "recommended_future_wave": row["recommended_future_wave"],
        }
        for row in top_rows
    ]
    return {
        **metadata,
        "stage": "research_operational_priority_heuristic",
        "priority_vintage_status": "current_after_aggressive_attempt3_merge",
        "selection_guard": (
            "Reconcile targets against current coverage and failure-only status before "
            "locking the next ordinary discovery round."
        ),
        "target_count": len(targets),
        "targets": targets,
        "disclaimer": (
            "Targets are unverified scouting priorities, not evidence that a qualifying "
            "agreement or matched safety/non-safety set exists."
        ),
    }


def current_preflight_recommendation() -> str:
    if not HOSTED_SEARCH_RECOMMENDATION_PATH.exists():
        return "run_strengthened_preflight_gate_before_next_live_wave"
    text = HOSTED_SEARCH_RECOMMENDATION_PATH.read_text(encoding="utf-8").lower()
    if "recommendation a" in text or "category a" in text:
        return (
            "last_bounded_diagnostic_was_healthy; nevertheless_run_the_strengthened_"
            "preflight_gate_immediately_before_the_next_live_wave"
        )
    return "hosted_search_health_not_confirmed; do_not_run_full_live_wave"


def build_scout_operations_summary(
    *,
    state_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    wave_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    latest = wave_rows[-1]
    covered = sum(as_int(row["municipalities_scouted"]) for row in state_rows)
    positive = sum(
        as_int(row["municipalities_scouted_with_candidates"]) for row in state_rows
    )
    empty = sum(
        as_int(row["municipalities_scouted_no_candidates"]) for row in state_rows
    )
    failure_only = sum(
        as_int(row["municipalities_scout_attempt_failed_connection"])
        for row in state_rows
    )
    remaining = max(SCOUT_CHECKPOINT_TARGET - covered, 0)
    return {
        **metadata,
        "stage": "scout_operations_unverified_discovery",
        "current_totals": {
            "scout_covered_municipalities": covered,
            "candidate_queue_rows": len(queue_rows),
            "candidate_positive_municipalities": positive,
            "parseable_empty_municipalities": empty,
            "failure_only_municipalities": failure_only,
        },
        "active_strategy": {
            "current_phase": "Post-checkpoint verification planning",
            "checkpoint_target_scout_covered": SCOUT_CHECKPOINT_TARGET,
            "remaining_to_checkpoint": remaining,
            "checkpoint_status": "reached_exceeded",
            "checkpoint_margin": covered - SCOUT_CHECKPOINT_TARGET,
            "estimated_150_row_waves_remaining": str(
                math.ceil(remaining / COORDINATED_WAVE_SIZE)
            ),
            "full_150_row_waves_to_reach_or_exceed_checkpoint": math.ceil(
                remaining / COORDINATED_WAVE_SIZE
            ),
            "ordinary_discovery_lane": (
                "Paused after the successful aggressive 3x300 serial merge crossed "
                "the approximately 2,000-covered checkpoint. Do not run another "
                "ordinary discovery wave without explicit user or PI authorization."
            ),
            "next_planned_round_id": NEXT_PARALLEL_SCOUT_ROUND_ID,
            "next_planned_round_lanes": NEXT_ROUND_LANES,
            "next_planned_round_rows_per_lane": NEXT_ROUND_ROWS_PER_LANE,
            "next_planned_round_expected_attempted": NEXT_ROUND_ATTEMPTED,
            "next_planned_round_expected_parseable": (
                NEXT_ROUND_EXPECTED_PARSEABLE
            ),
            "next_planned_round_expected_post_coverage": (
                NEXT_ROUND_EXPECTED_POST_COVERAGE
            ),
            "checkpoint_overshoot_intent": "completed_intentional_user_approved",
            "superseded_round_id": "POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23",
            "next_phase": (
                "Verification, extraction, ingestion, rating, and descriptive "
                "wage-growth-gap and mechanism analysis"
            ),
            "regressions_status": "Deferred",
        },
        "latest_wave": {
            "wave_id": latest["wave_id"],
            "label": latest["wave_label"],
            "runtime_seconds": as_float(latest["runtime_seconds"]),
            "rows_per_hour": as_float(latest["rows_per_hour"]),
            "candidate_rows_per_hour": as_float(latest["candidate_rows_per_hour"]),
            "candidate_rows_per_parseable_municipality": as_float(
                latest["candidate_rows_per_parseable_municipality"]
            ),
            "timeout_or_failure_rows": as_int(latest["failure_only_rows"]),
        },
        "priority_refresh_recommendation": (
            "The unchanged national priority methodology was refreshed after the "
            "Aggressive Attempt 3 merge added 899 successful scouts and crossed the "
            "workflow checkpoint. Treat the layer as current but do not use it to "
            "schedule another ordinary discovery wave while broad scouting is paused."
        ),
        "preflight_gate_recommendation": current_preflight_recommendation(),
        "disclaimer": (
            "Scout candidates remain unverified leads. Runtime and yield metrics are "
            "operational diagnostics, not evidence of source quality or wage effects."
        ),
    }


def build_scout_yield_state_layer(
    *, state_yield_rows: list[dict[str, str]], metadata: dict[str, Any]
) -> dict[str, Any]:
    states = []
    for row in state_yield_rows:
        states.append(
            {
                "state": row["state"],
                "state_name": STATE_NAMES[row["state"]],
                "successful_scout_count": as_int(row["successful_scout_count"]),
                "candidate_positive_rate": as_float(row["candidate_positive_rate"]),
                "candidate_rows_per_covered_municipality": as_float(
                    row["candidate_rows_per_covered_municipality"]
                ),
                "parseable_empty_rate": as_float(row["parseable_empty_rate"]),
                "failure_only_rate": as_float(row["failure_only_rate"]),
                "connection_failure_attempt_rate": as_float(
                    row["connection_failure_attempt_rate"]
                ),
                "sample_confidence": row["sample_confidence"],
                "recommended_next_wave_status": row[
                    "recommended_next_wave_status"
                ],
            }
        )
    leaderboard = sorted(
        [row for row in states if row["successful_scout_count"] >= 10],
        key=lambda row: (
            -(row["candidate_rows_per_covered_municipality"] or 0),
            -(row["candidate_positive_rate"] or 0),
            row["state"],
        ),
    )
    return {
        **metadata,
        "stage": "scout_operations_unverified_discovery",
        "leaderboard_minimum_successful_scouts": 10,
        "state_yield_leaderboard": leaderboard,
        "states": states,
        "disclaimer": "Sparse-state estimates are confidence-labeled and must not drive selection alone.",
    }


def build_scout_runtime_trends(
    *,
    wave_rows: list[dict[str, str]],
    state_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    waves = []
    for row in wave_rows:
        waves.append(
            {
                "wave_id": row["wave_id"],
                "label": row["wave_label"],
                "attempted_rows": as_int(row["attempted_rows"]),
                "parseable_rows": as_int(row["parseable_rows"]),
                "candidate_rows": as_int(row["candidate_rows"]),
                "failure_only_rows": as_int(row["failure_only_rows"]),
                "runtime_seconds": as_float(row["runtime_seconds"]),
                "rows_per_hour": as_float(row["rows_per_hour"]),
                "candidate_rows_per_hour": as_float(row["candidate_rows_per_hour"]),
                "candidate_rows_per_parseable_municipality": as_float(
                    row["candidate_rows_per_parseable_municipality"]
                ),
                "sleep_between_prompts_seconds": as_float(
                    row["sleep_between_prompts_seconds"]
                ),
            }
        )
    return {
        **metadata,
        "stage": "scout_operations_unverified_discovery",
        "waves": waves,
        "checkpoint_context": {
            "target_scout_covered": SCOUT_CHECKPOINT_TARGET,
            "current_scout_covered": sum(
                as_int(row["municipalities_scouted"]) for row in state_rows
            ),
            "note": (
                "The current total comes from national coverage accounting; runtime "
                f"waves shown here are the {len(waves)} reviewed coordinated waves/rounds."
            ),
        },
        "next_run_instrumentation": [
            "compact prompt character/token proxy",
            "adaptive planned and actual sleep",
            "per-row elapsed time and failure type",
        ],
    }


def build_project_phase_summary(
    *,
    state_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build the PI-aligned source-discovery checkpoint layer."""

    covered = sum(as_int(row["municipalities_scouted"]) for row in state_rows)
    positive = sum(
        as_int(row["municipalities_scouted_with_candidates"]) for row in state_rows
    )
    failure_only = sum(
        as_int(row["municipalities_scout_attempt_failed_connection"])
        for row in state_rows
    )
    remaining = max(SCOUT_CHECKPOINT_TARGET - covered, 0)
    return {
        **metadata,
        "stage": "post_scout_checkpoint_transition",
        "current_phase": "Scaled verification routing and source triage",
        "checkpoint_target_scout_covered": SCOUT_CHECKPOINT_TARGET,
        "current_scout_covered": covered,
        "remaining_to_checkpoint": remaining,
        "checkpoint_status": "reached_exceeded",
        "checkpoint_margin": covered - SCOUT_CHECKPOINT_TARGET,
        "progress_percentage": round(
            100.0 * covered / SCOUT_CHECKPOINT_TARGET, 1
        ),
        "estimated_150_row_waves_remaining": str(
            math.ceil(remaining / COORDINATED_WAVE_SIZE)
        ),
        "full_150_row_waves_to_reach_or_exceed_checkpoint": math.ceil(
            remaining / COORDINATED_WAVE_SIZE
        ),
        "current_candidate_queue_rows": len(queue_rows),
        "current_candidate_positive_municipalities": positive,
        "current_failure_only_municipalities": failure_only,
        "next_planned_round": {
            "round_id": NEXT_PARALLEL_SCOUT_ROUND_ID,
            "status": "none_broad_scouting_paused",
            "profile": "none",
            "lanes": NEXT_ROUND_LANES,
            "rows_per_lane": NEXT_ROUND_ROWS_PER_LANE,
            "expected_attempted": NEXT_ROUND_ATTEMPTED,
            "expected_parseable_at_recent_rate": (
                NEXT_ROUND_EXPECTED_PARSEABLE
            ),
            "expected_post_round_scout_covered": (
                NEXT_ROUND_EXPECTED_POST_COVERAGE
            ),
            "expected_checkpoint_margin": covered - SCOUT_CHECKPOINT_TARGET,
            "checkpoint_overshoot_intent": "completed_intentional_user_approved",
            "lane_start_stagger_minutes": 0,
            "projection_status": "no_additional_round_planned",
        },
        "superseded_plans": [
            {
                "round_id": "POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23",
                "status": "superseded_preserved_not_active",
                "reason": "User explicitly selected the aggressive 3x300 round.",
            }
        ],
        "checkpoint_pause_rule": (
            "Active: the user-approved aggressive round was merged and the "
            "approximately 2,000-covered checkpoint was exceeded. Broad scouting "
            "is paused; begin the documented downstream cycle."
        ),
        "next_phase": (
            "Verification, extraction, ingestion, rating, descriptive wage-growth-gap "
            "analysis, and mechanism-correlation documentation"
        ),
        "next_phase_sequence": [
            "verify candidate sources",
            "extract wage data",
            "ingest structured observations",
            "rate source quality and extractability",
            "analyze descriptive wage-growth gaps",
            "document correlated wage mechanisms",
            "add wage-growth-gap map filtering",
            "decide the most efficient repeat strategy",
        ],
        "regressions_status": "Deferred",
        "last_updated_commit": CURRENT_SOURCE_ACCOUNTING_COMMIT,
        "last_updated_context": "verification_round1_routing_merged",
        "future_live_controls": [
            "stronger preflight gate",
            "compact prompts",
            "deterministic search hints",
            "adaptive sleep and backoff",
            "isolated parallel lane processes with each lane internally serialized",
            "one serial accounting merge after combined lane audit",
        ],
        "caveats": [
            "Candidate rows are unverified.",
            "Wage gaps have not been calculated.",
            "Mechanisms have not been analyzed for correlation with wage-growth gaps.",
            "Priority tiers are operational scheduling inputs, not findings.",
            "The checkpoint is a workflow pause point, not an evidentiary threshold.",
        ],
    }


def build_parallel_scout_status(
    *, state_rows: list[dict[str, str]], metadata: dict[str, Any]
) -> dict[str, Any]:
    """Describe completed parallel work and the post-checkpoint pause."""

    covered = sum(as_int(row["municipalities_scouted"]) for row in state_rows)
    remaining = max(SCOUT_CHECKPOINT_TARGET - covered, 0)
    return {
        **metadata,
        "stage": "parallel_scout_operations_status",
        "parallel_mode_status": "aggressive_3x300_completed_accounting_merged",
        "current_parallel_mode": "three_lane_aggressive_round_successfully_merged",
        "supported_lanes_initial": 2,
        "supported_lanes_future": 3,
        "rows_per_lane": 300,
        "latest_completed_round_id": PARALLEL_SCOUT_ROUND_ID,
        "current_parallel_round_id": PARALLEL_SCOUT_ROUND_ID,
        "next_parallel_test": "none_broad_scouting_paused",
        "aggressive_mode_planned": "completed_checkpoint_exceeded",
        "current_scout_covered": covered,
        "target_checkpoint": SCOUT_CHECKPOINT_TARGET,
        "remaining_to_checkpoint": remaining,
        "planned_round_expected_attempted": NEXT_ROUND_ATTEMPTED,
        "planned_round_expected_parseable": NEXT_ROUND_EXPECTED_PARSEABLE,
        "planned_round_expected_post_coverage": covered,
        "planned_round_expected_checkpoint_margin": (
            covered - SCOUT_CHECKPOINT_TARGET
        ),
        "planned_round_status": "none_broad_scouting_paused",
        "checkpoint_overshoot_intent": "completed_intentional_user_approved",
        "superseded_round": {
            "round_id": "POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23",
            "status": "superseded_preserved_not_active",
        },
        "lane_start_stagger_minutes": 8,
        "3x150_expected_attempted": 450,
        "3x300_expected_attempted": 900,
        "accounting_policy": "serial_merge_after_lane_audit",
        "lane_export_policy": "lane_local_candidate_exports",
        "latest_round": {
            "lanes_completed_merge_eligible": 3,
            "attempted_rows": 900,
            "parseable_rows": 899,
            "candidate_positive_municipalities": 591,
            "parseable_empty_municipalities": 308,
            "failure_only_municipalities": 1,
            "candidate_lead_rows": 1389,
            "url_bearing_queue_rows_added": 1379,
            "merge_recommendation": "merge_all_lanes",
            "accounting_merge_status": "completed_serially",
        },
        "lane_execution_policy": (
            "Each lane is internally serialized and writes only to its own output "
            "directory; lane processes do not rebuild shared accounting."
        ),
        "post_checkpoint_policy": (
            "Broad scouting is paused after the successfully merged aggressive "
            "round exceeded the approximately 2,000 checkpoint. Proceed to "
            "verification, extraction, ingestion, rating, descriptive "
            "wage-growth-gap analysis, mechanism-correlation documentation, and "
            "the planned wage-gap dashboard filter."
        ),
        "caveat": (
            "The user-approved aggressive 3x300 Attempt 3 completed and was merged "
            "serially after audit. The checkpoint overshoot was intentional. Broad "
            "scouting is paused; all candidate leads remain unverified, and no "
            "wage-gap layer is active."
        ),
    }


def build_verification_status_summary(
    *, queue_rows: list[dict[str, str]], metadata: dict[str, Any]
) -> dict[str, Any]:
    """Describe merged routing outcomes without claiming content verification."""

    triage = Counter(row.get("triage_bucket", "") for row in queue_rows)
    scheduled = sum(triage[bucket] for bucket in VERIFY_BUCKETS)
    held_or_context = (
        triage["context_only_hold"]
        + triage["insufficient_hold"]
        + triage["rejected_from_calibration"]
    )
    duplicate_or_canonical = (
        triage["likely_duplicate_hold"] + triage["already_canonical_hold"]
    )
    capacity_3x750 = VERIFICATION_BATCH_SIZE * VERIFICATION_LANES
    capacity_3x1000 = 3_000
    routing_summary = (
        read_json(VERIFICATION_ROUTING_SUMMARY_PATH)
        if VERIFICATION_ROUTING_SUMMARY_PATH.exists()
        else None
    )
    if routing_summary:
        status_counts = routing_summary["verification_status_counts"]
        merged_rows = int(routing_summary["ledger_rows"])
        full_routing_merged = (
            routing_summary.get("summary_scope") == "cumulative_project_wide"
            and merged_rows == len(queue_rows)
        )
        scheduled_remaining = 0 if full_routing_merged else max(
            scheduled - merged_rows, 0
        )
        full_remaining = max(len(queue_rows) - merged_rows, 0)
        reachable_or_reused = int(routing_summary["reachable_or_reused_total"])
        round_rows = routing_summary.get("round_rows", {})
        round1_rows = int(round_rows.get(FIRST_VERIFICATION_ROUND_ID, merged_rows))
        round2_rows = int(round_rows.get(SECOND_VERIFICATION_ROUND_ID, 0))
        round2_live = (
            read_json(VERIFICATION_ROUND2_LIVE_STATUS_PATH)
            if VERIFICATION_ROUND2_LIVE_STATUS_PATH.exists()
            else {}
        )
        latest_round_id = routing_summary.get(
            "latest_merged_round_id", routing_summary["verification_round_id"]
        )
        latest_merge_id = routing_summary.get(
            "latest_merge_id", routing_summary["verification_merge_id"]
        )
        payload = {
            **metadata,
            "stage": "candidate_source_verification_routing",
            "verification_phase": (
                "full_url_routing_merged"
                if full_routing_merged
                else "round1_3x750_merged"
            ),
            "latest_merged_round_id": latest_round_id,
            "latest_merge_id": latest_merge_id,
            "live_verification_status": (
                "all_candidate_urls_routed"
                if full_routing_merged
                else "round1_merged"
            ),
            "verification_live_status": (
                "all_candidate_urls_routed"
                if full_routing_merged
                else "round1_merged"
            ),
            "total_url_bearing_candidate_rows": len(queue_rows),
            "scheduled_verification_rows": scheduled,
            "held_or_context_rows": held_or_context,
            "duplicate_or_already_canonical_rows": duplicate_or_canonical,
            "held_rejected_context_duplicate_canonical_total": (
                len(queue_rows) - scheduled
            ),
            "rows_verified_routing_total": merged_rows,
            "url_bearing_routing_coverage_rate": round(
                merged_rows / len(queue_rows), 6
            ),
            "round1_rows_verified_routing_total": round1_rows,
            "round2_rows_verified_routing_total": round2_rows,
            "url_opens_total": int(routing_summary["url_opens_total"]),
            "reachable_or_reused_total": reachable_or_reused,
            "reachable_or_reused_rate": round(
                reachable_or_reused / merged_rows, 5
            ),
            "cumulative_reachable_or_reused_total": reachable_or_reused,
            "cumulative_reachable_or_reused_rate": round(
                reachable_or_reused / merged_rows, 6
            ),
            "reachable_pdf_or_document_total": int(
                status_counts.get("reachable_pdf_or_document", 0)
            ),
            "reachable_html_total": int(status_counts.get("reachable_html", 0)),
            "reachable_http_total": int(status_counts.get("reachable_http", 0)),
            "cumulative_reachable_pdf_or_document_total": int(
                status_counts.get("reachable_pdf_or_document", 0)
            ),
            "cumulative_reachable_html_total": int(
                status_counts.get("reachable_html", 0)
            ),
            "cumulative_reachable_http_total": int(
                status_counts.get("reachable_http", 0)
            ),
            "blocked_or_forbidden_total": int(
                status_counts.get("blocked_or_forbidden", 0)
            ),
            "not_found_total": int(status_counts.get("not_found", 0)),
            "too_large_total": int(status_counts.get("too_large", 0)),
            "error_total": int(status_counts.get("error", 0)),
            "ssl_error_total": int(status_counts.get("ssl_error", 0)),
            "timeout_total": int(status_counts.get("timeout", 0)),
            "connection_error_total": int(
                status_counts.get("connection_error", 0)
            ),
            "cumulative_blocked_or_forbidden_total": int(
                status_counts.get("blocked_or_forbidden", 0)
            ),
            "cumulative_not_found_total": int(
                status_counts.get("not_found", 0)
            ),
            "cumulative_too_large_total": int(
                status_counts.get("too_large", 0)
            ),
            "cumulative_error_total": int(status_counts.get("error", 0)),
            "cumulative_ssl_error_total": int(
                status_counts.get("ssl_error", 0)
            ),
            "cumulative_timeout_total": int(status_counts.get("timeout", 0)),
            "cumulative_connection_error_total": int(
                status_counts.get("connection_error", 0)
            ),
            "duplicate_reuse_rows": int(routing_summary["duplicate_reuse_rows"]),
            "cumulative_duplicate_reuse_rows": int(
                routing_summary["duplicate_reuse_rows"]
            ),
            "round2_reachable_or_reused_total": int(
                round2_live.get("reachable_or_reused_total", 0)
            ),
            "round2_reachable_or_reused_rate": round(
                float(round2_live.get("reachable_or_reused_rate", 0)), 6
            ),
            "round2_merge_status": (
                "merged" if full_routing_merged and round2_rows else "not_started"
            ),
            "scheduled_verification_rows_remaining_estimate": scheduled_remaining,
            "full_url_bearing_rows_remaining_estimate": full_remaining,
            "future_bulk_verification_profile": "bulk_2x2000",
            "future_bulk_profile_status": (
                "available_for_future_unrouted_candidate_queues"
            ),
            "current_queue_bulk_rerun_status": (
                "not_needed" if full_routing_merged else "not_applicable"
            ),
            "current_queue_unrouted_url_bearing_rows": full_remaining,
            "recommended_next_round_id": (
                "NONE-FULL-URL-ROUTING-COMPLETE"
                if full_routing_merged
                else "VERIFICATION-SCALE-ROUND2-3X750-2026-07-24"
            ),
            "recommended_concurrency_per_lane": VERIFICATION_CONCURRENCY_PER_LANE,
            "recommended_timeout_seconds": 20,
            "recommended_max_redirects": 5,
            "recommended_max_bytes": 10_485_760,
            "scheduled_verification_estimated_rounds_3x750": math.ceil(
                scheduled_remaining / capacity_3x750
            ),
            "full_backlog_estimated_rounds_3x750": math.ceil(
                full_remaining / capacity_3x750
            ),
            "full_backlog_estimated_rounds_3x1000": math.ceil(
                full_remaining / capacity_3x1000
            ),
            "scheduled_pool_estimated_rounds": math.ceil(
                scheduled_remaining / capacity_3x750
            ),
            "full_backlog_estimated_rounds": math.ceil(
                full_remaining / capacity_3x750
            ),
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "stage_boundaries": [
                "candidate lead",
                "verified-source routing outcome",
                "ingested source",
                "codified evidence",
                "analysis-ready wage observation",
            ],
            "routing_summary_source": relative(VERIFICATION_ROUTING_SUMMARY_PATH),
            "routing_summary_scope": routing_summary.get(
                "summary_scope", "round_specific"
            ),
            "caveats": [
                "URL routing coverage is complete, but source relevance and content extraction are not."
                if full_routing_merged
                else "Verification routing does not equal ingestion.",
                "A reachable PDF/document does not equal extracted wage data or a confirmed employer/unit match.",
                "Blocked, not-found, oversized, and transport statuses are URL-routing outcomes, not municipality source-absence findings.",
                "Held, context, duplicate, canonical, and rejected rows retain their original lower dispositions.",
                "No wage gaps have been calculated.",
            ],
        }
        if VERIFICATION_ROUND2_LIVE_STATUS_PATH.exists() and not full_routing_merged:
            round2 = round2_live
            payload.update(
                {
                    "live_verification_status": (
                        "round2_3x1000_remainder_collected_not_merged"
                    ),
                    "verification_live_status": (
                        "round2_3x1000_remainder_collected_not_merged"
                    ),
                    "latest_live_round_id": round2["round_id"],
                    "round2_selected_rows": int(round2["selected_rows"]),
                    "round2_terminal_rows": int(round2["terminal_rows"]),
                    "round2_url_opens": int(round2["url_opens"]),
                    "round2_reachable_or_reused_total": int(
                        round2["reachable_or_reused_total"]
                    ),
                    "round2_reachable_or_reused_rate": round(
                        float(round2["reachable_or_reused_rate"]), 6
                    ),
                    "round2_duplicate_reuse_rows": int(
                        round2["duplicate_reuse_rows"]
                    ),
                    "round2_lane_audit_recommendation": round2[
                        "lane_audit_recommendation"
                    ],
                    "round2_merge_status": "not_started",
                    "cumulative_merged_rows_verified_routing_total": merged_rows,
                    "latest_live_collection_status_source": relative(
                        VERIFICATION_ROUND2_LIVE_STATUS_PATH
                    ),
                }
            )
        return payload
    return {
        **metadata,
        "stage": "candidate_source_verification_planning",
        "verification_phase": "live_path_implemented_planned_scale_up",
        "total_url_bearing_candidate_rows": len(queue_rows),
        "scheduled_verification_rows": scheduled,
        "held_or_context_rows": held_or_context,
        "duplicate_or_already_canonical_rows": duplicate_or_canonical,
        "held_rejected_context_duplicate_canonical_total": (
            len(queue_rows) - scheduled
        ),
        "first_verification_round_id": FIRST_VERIFICATION_ROUND_ID,
        "first_live_round_recommended": FIRST_VERIFICATION_ROUND_ID,
        "first_round_candidate_rows": FIRST_VERIFICATION_ROUND_ROWS,
        "first_round_lanes": VERIFICATION_LANES,
        "first_round_rows_per_lane": VERIFICATION_BATCH_SIZE,
        "lane_count": VERIFICATION_LANES,
        "rows_per_lane": VERIFICATION_BATCH_SIZE,
        "recommended_concurrency_per_lane": VERIFICATION_CONCURRENCY_PER_LANE,
        "recommended_timeout_seconds": 20,
        "recommended_max_redirects": 5,
        "recommended_max_bytes": 10_485_760,
        "scheduled_verification_estimated_rounds_3x750": math.ceil(
            scheduled / capacity_3x750
        ),
        "full_backlog_estimated_rounds_3x750": math.ceil(
            len(queue_rows) / capacity_3x750
        ),
        "full_backlog_estimated_rounds_3x1000": math.ceil(
            len(queue_rows) / capacity_3x1000
        ),
        # Backward-compatible aliases consumed by the current dashboard panel.
        "scheduled_pool_estimated_rounds": math.ceil(
            scheduled / capacity_3x750
        ),
        "full_backlog_estimated_rounds": math.ceil(
            len(queue_rows) / capacity_3x750
        ),
        "additional_rounds_for_full_backlog": (
            math.ceil(len(queue_rows) / capacity_3x750)
            - math.ceil(scheduled / capacity_3x750)
        ),
        "verification_live_status": "ready_not_started",
        "verification_dry_run_status": "three_lanes_passed_offline",
        "ingestion_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "stage_boundaries": [
            "candidate lead",
            "verified source",
            "ingested source",
            "codified evidence",
            "analysis-ready wage observation",
        ],
        "caveats": [
            "The bounded live path is implemented and mock-tested, but no candidate URL has been opened.",
            "Candidate rows remain unverified until separately authorized live verification runs.",
            "Verification is not ingestion, codification, wage extraction, or analysis-ready evidence.",
            "Wage gaps have not been calculated.",
        ],
    }


def build_content_triage_status_summary(
    *, queue_rows: list[dict[str, str]], metadata: dict[str, Any]
) -> dict[str, Any]:
    """Describe offline triage planning without implying content review."""

    routing_summary = read_json(VERIFICATION_ROUTING_SUMMARY_PATH)
    manifest = read_json(CONTENT_TRIAGE_ROUND1_MANIFEST_PATH)
    metadata_collection = (
        read_json(CONTENT_TRIAGE_ROUND1_METADATA_STATUS_PATH)
        if CONTENT_TRIAGE_ROUND1_METADATA_STATUS_PATH.exists()
        else {}
    )
    remainder_manifest = (
        read_json(CONTENT_TRIAGE_REMAINDER_MANIFEST_PATH)
        if CONTENT_TRIAGE_REMAINDER_MANIFEST_PATH.exists()
        else {}
    )
    remainder_collection = (
        read_json(CONTENT_TRIAGE_REMAINDER_METADATA_STATUS_PATH)
        if CONTENT_TRIAGE_REMAINDER_METADATA_STATUS_PATH.exists()
        else {}
    )
    cumulative_triage = (
        read_json(CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH)
        if CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH.exists()
        else {}
    )
    status_counts = routing_summary["verification_status_counts"]
    routed_rows = int(routing_summary["ledger_rows"])
    reachable_or_reused = int(routing_summary["reachable_or_reused_total"])
    if routed_rows != len(queue_rows):
        raise ValueError(
            "Content-triage planning requires complete current-queue routing"
        )
    if int(manifest["total_routed_rows"]) != routed_rows:
        raise ValueError("Content-triage manifest/routing row counts disagree")
    selected_rows = int(manifest["selected_rows"])
    lane_rows = {
        str(lane["lane_id"]): int(lane["expected_rows"])
        for lane in manifest["lanes"]
    }
    if sum(lane_rows.values()) != selected_rows:
        raise ValueError("Content-triage lane rows do not sum to the round total")
    collected_rows = int(metadata_collection.get("terminal_rows", 0))
    collected_not_merged = (
        metadata_collection.get("status") == "metadata_only_collected_not_merged"
        and collected_rows == selected_rows
    )
    remainder_collected_rows = int(
        remainder_collection.get("terminal_rows", 0)
    )
    remainder_collected = (
        remainder_collection.get("status")
        == "metadata_only_collected_not_merged"
        and remainder_collected_rows
        == int(remainder_manifest.get("selected_rows", 0))
    )
    full_collected_rows = collected_rows + remainder_collected_rows
    full_universe_collected = (
        collected_not_merged
        and remainder_collected
        and full_collected_rows == routed_rows
        and int(remainder_manifest.get("selected_plus_excluded_rows", 0))
        == routed_rows
    )
    full_universe_merged = (
        cumulative_triage.get("status")
        == "metadata_only_full_universe_merged"
        and int(cumulative_triage.get("ledger_rows", 0)) == routed_rows
        and int(cumulative_triage.get("terminal_rows", 0)) == routed_rows
        and bool(cumulative_triage.get("routing_identity_equality"))
    )

    def merge_counts(field: str) -> dict[str, int]:
        combined: Counter[str] = Counter()
        combined.update(metadata_collection.get(field, {}))
        combined.update(remainder_collection.get(field, {}))
        return dict(sorted(combined.items()))

    payload = {
        **metadata,
        "stage": "content_triage_and_extraction_readiness_planning",
        "content_triage_phase": (
            "metadata_only_full_universe_merged"
            if full_universe_merged
            else "metadata_only_full_universe_collected_not_merged"
            if full_universe_collected
            else "metadata_only_round1_collected_not_merged"
            if collected_not_merged
            else "planned_not_started"
        ),
        "routing_coverage_complete": True,
        "routed_url_bearing_rows": routed_rows,
        "reachable_or_reused_rows": reachable_or_reused,
        "routing_eligible_rows_including_duplicate_pending": int(
            manifest["routing_eligible_rows_including_duplicate_pending"]
        ),
        "initial_triage_round_id": manifest["round_id"],
        "initial_triage_round_rows": selected_rows,
        "initial_triage_lane_count": int(manifest["num_lanes"]),
        "initial_triage_lane_rows": lane_rows,
        "initial_triage_priority_scope": manifest["priority_scope"],
        "initial_triage_status": manifest["status"],
        "triage_live_status": (
            "metadata_only_full_universe_merged"
            if full_universe_merged
            else "metadata_only_full_universe_collected_not_merged"
            if full_universe_collected
            else "metadata_only_collected_not_merged"
            if collected_not_merged
            else "not_started"
        ),
        "latest_content_triage_round_id": (
            remainder_manifest["round_id"]
            if full_universe_collected
            else manifest["round_id"]
            if collected_not_merged
            else ""
        ),
        "latest_content_triage_mode": (
            "metadata_only" if collected_not_merged else ""
        ),
        "latest_content_triage_merge_id": (
            cumulative_triage.get("content_triage_merge_id", "")
            if full_universe_merged
            else ""
        ),
        "metadata_only_triage_rows_collected": full_collected_rows,
        "metadata_only_triage_rows_merged": (
            int(cumulative_triage["ledger_rows"])
            if full_universe_merged
            else 0
        ),
        "full_routed_rows_metadata_triaged": (
            full_collected_rows if full_universe_collected else collected_rows
        ),
        "round1_metadata_only_rows_collected": collected_rows,
        "remainder_metadata_only_rows_collected": remainder_collected_rows,
        "metadata_only_triage_lane_count_collected": (
            int(manifest["num_lanes"])
            + int(remainder_manifest.get("num_lanes", 0))
        ),
        "metadata_only_triage_merge_status": (
            "merged" if full_universe_merged else "not_started"
        ),
        "durable_content_triage_ledger_latest": (
            relative(CONTENT_TRIAGE_CUMULATIVE_LEDGER_PATH)
            if full_universe_merged
            else ""
        ),
        "content_download_status": "not_started",
        "source_rating_status": "not_started",
        "extraction_readiness_status": (
            "preliminary_metadata_only_merged"
            if full_universe_merged
            else "preliminary_metadata_only_not_merged"
            if collected_not_merged
            else "planned_not_started"
        ),
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "oversized_rows_deferred": int(status_counts.get("too_large", 0)),
        "duplicate_group_count_in_routing_eligible_pool": int(
            manifest["duplicate_group_count_in_routing_eligible_pool"]
        ),
        "linked_duplicate_rows_in_routing_eligible_pool": int(
            manifest["linked_duplicate_rows_in_routing_eligible_pool"]
        ),
        "selected_state_distribution": manifest["selected_state_distribution"],
        "selected_source_type_distribution": manifest[
            "selected_source_type_distribution"
        ],
        "selected_content_type_distribution": manifest[
            "selected_content_type_distribution"
        ],
        "selected_candidate_disposition_distribution": manifest[
            "selected_candidate_disposition_distribution"
        ],
        "round_manifest_source": relative(CONTENT_TRIAGE_ROUND1_MANIFEST_PATH),
        "metadata_collection_source": (
            relative(CONTENT_TRIAGE_ROUND1_METADATA_STATUS_PATH)
            if collected_not_merged
            else ""
        ),
        "remainder_round_manifest_source": (
            relative(CONTENT_TRIAGE_REMAINDER_MANIFEST_PATH)
            if remainder_collected
            else ""
        ),
        "remainder_metadata_collection_source": (
            relative(CONTENT_TRIAGE_REMAINDER_METADATA_STATUS_PATH)
            if remainder_collected
            else ""
        ),
        "routing_summary_source": relative(VERIFICATION_ROUTING_SUMMARY_PATH),
        "cumulative_content_triage_summary_source": (
            relative(CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH)
            if full_universe_merged
            else ""
        ),
        "caveats": [
            (
                "The merged full-universe metadata-only triage has not inspected source content."
                if full_universe_merged
                else "Full-universe metadata-only triage has not inspected source content."
                if full_universe_collected
                else "Metadata-only triage has not inspected source content."
                if collected_not_merged
                else "Content triage has not opened URLs or downloaded source content."
            ),
            "Routing reachability does not equal source relevance or employer/unit validation.",
            "Preliminary extraction-readiness signals are scheduling aids until content is reviewed.",
            "Reachable documents are not ingested, codified, or extracted wage observations.",
            "No source content was downloaded or parsed and no wage data or wage gaps were calculated.",
        ],
    }
    if full_universe_merged:
        triage_counts = cumulative_triage["triage_status_counts"]
        action_counts = cumulative_triage["recommended_next_action_counts"]
        payload.update(
            {
                "metadata_only_triage_status_counts": triage_counts,
                "metadata_only_recommended_next_action_counts": action_counts,
                "metadata_only_extraction_readiness_prelim_counts": (
                    cumulative_triage["extraction_readiness_prelim_counts"]
                ),
                "metadata_only_source_relevance_prelim_counts": (
                    cumulative_triage["source_relevance_prelim_counts"]
                ),
                "metadata_only_priority_for_content_review_counts": (
                    cumulative_triage["priority_for_content_review_counts"]
                ),
                "high_priority_content_review_rows": int(
                    triage_counts.get("high_priority_content_review", 0)
                ),
                "medium_priority_content_review_rows": int(
                    triage_counts.get("medium_priority_content_review", 0)
                ),
                "low_priority_content_review_rows": int(
                    triage_counts.get("low_priority_content_review", 0)
                ),
                "duplicate_defer_to_canonical_rows": int(
                    triage_counts.get("duplicate_defer_to_canonical", 0)
                ),
                "oversized_needs_separate_pass_rows": int(
                    triage_counts.get("oversized_needs_separate_pass", 0)
                ),
                "blocked_or_unreachable_defer_rows": int(
                    triage_counts.get("blocked_or_unreachable_defer", 0)
                ),
                "needs_manual_review_rows": int(
                    triage_counts.get("needs_manual_review", 0)
                ),
                "content_review_download_allowed_later_rows": int(
                    action_counts.get(
                        "content_review_download_allowed_later", 0
                    )
                ),
                "metadata_review_only_rows": int(
                    action_counts.get("metadata_review_only", 0)
                ),
                "metadata_only_lane_audit_recommendation": (
                    "merge_all_content_triage_lanes"
                ),
            }
        )
    elif collected_not_merged:
        payload.update(
            {
                "metadata_only_triage_status_counts": merge_counts(
                    "triage_status_counts"
                ),
                "metadata_only_recommended_next_action_counts": (
                    merge_counts("recommended_next_action_counts")
                ),
                "metadata_only_extraction_readiness_prelim_counts": (
                    merge_counts("extraction_readiness_prelim_counts")
                ),
                "metadata_only_source_relevance_prelim_counts": (
                    merge_counts("source_relevance_prelim_counts")
                ),
                "metadata_only_lane_audit_recommendation": (
                    remainder_collection.get("merge_recommendation", "")
                    if full_universe_collected
                    else metadata_collection.get("merge_recommendation", "")
                ),
            }
        )
    return payload


def build_source_review_status_summary(
    *, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Describe the mock-tested source-review path without implying content access."""

    triage_summary = read_json(CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH)
    manifest = read_json(SOURCE_REVIEW_PILOT_MANIFEST_PATH)
    if (
        triage_summary.get("status")
        != "metadata_only_full_universe_merged"
        or int(triage_summary.get("ledger_rows", 0)) != 4_726
    ):
        raise ValueError(
            "Source-review planning requires the merged full-universe "
            "metadata-only triage layer"
        )
    priority_counts = triage_summary["priority_for_content_review_counts"]
    action_counts = triage_summary["recommended_next_action_counts"]
    selected_rows = int(manifest["selected_rows"])
    lane_rows = {
        str(lane["lane_id"]): int(lane["expected_rows"])
        for lane in manifest["lanes"]
    }
    if selected_rows != 150 or sum(lane_rows.values()) != selected_rows:
        raise ValueError("Source-review pilot manifest is not the locked 150-row plan")
    if any(
        int(manifest.get(field, -1))
        for field in (
            "urls_opened",
            "network_calls",
            "documents_downloaded",
            "documents_parsed",
            "pdfs_parsed",
            "ocr_runs",
            "content_artifacts_written",
        )
    ):
        raise ValueError("Source-review plan records prohibited source access")
    return {
        **metadata,
        "stage": "source_rating_and_bounded_content_review_readiness",
        "source_review_phase": "live_path_implemented_ready_for_pilot",
        "metadata_triage_complete": True,
        "metadata_triage_rows": int(triage_summary["ledger_rows"]),
        "p1_rows": int(priority_counts.get("p1", 0)),
        "content_review_download_allowed_later_rows": int(
            action_counts.get("content_review_download_allowed_later", 0)
        ),
        "initial_source_review_pilot_id": manifest["pilot_id"],
        "initial_source_review_pilot_rows": selected_rows,
        "initial_source_review_lane_count": int(manifest["num_lanes"]),
        "initial_source_review_lane_rows": lane_rows,
        "initial_source_review_states": len(
            manifest["selected_state_distribution"]
        ),
        "initial_source_review_unique_municipalities": int(
            manifest["selected_unique_municipalities"]
        ),
        "source_review_live_status": "ready_not_started",
        "bounded_live_source_review_path": "implemented_mock_tested",
        "recommended_initial_live_concurrency": 4,
        "recommended_initial_timeout_seconds": 30,
        "recommended_initial_connect_timeout_seconds": 8,
        "recommended_initial_read_timeout_seconds": 20,
        "recommended_initial_max_redirects": 5,
        "recommended_initial_max_bytes": 26_214_400,
        "next_scaling_decision": "after_150_row_live_pilot",
        "content_download_status": "ready_for_pilot_not_started",
        "source_rating_status": "ready_for_pilot_not_started",
        "extraction_readiness_status": "not_started",
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "selected_state_distribution": manifest["selected_state_distribution"],
        "selected_source_type_distribution": manifest[
            "selected_source_type_distribution"
        ],
        "selected_content_type_distribution": manifest[
            "selected_content_type_distribution"
        ],
        "selected_candidate_disposition_distribution": manifest[
            "selected_candidate_disposition_distribution"
        ],
        "selected_unit_type_distribution": manifest[
            "selected_unit_type_distribution"
        ],
        "pilot_manifest_source": relative(SOURCE_REVIEW_PILOT_MANIFEST_PATH),
        "metadata_triage_summary_source": relative(
            CONTENT_TRIAGE_CUMULATIVE_SUMMARY_PATH
        ),
        "caveats": [
            "Source review has not opened real URLs or downloaded real source content.",
            "Source ratings require observed source content and provenance review.",
            "The live path has been tested only with synthetic and mocked transport.",
            "Metadata-only pilot selection does not establish officialness, relevance, employer/unit match, document type, or extraction readiness.",
            "No source was ingested or codified and no wage data or wage gaps were calculated.",
        ],
    }


def validate_inputs(
    *,
    state_rows: list[dict[str, str]],
    municipality_rows: list[dict[str, str]],
    universe_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    priority_rows: list[dict[str, str]],
    state_priority_rows: list[dict[str, str]],
    top_priority_rows: list[dict[str, str]],
) -> None:
    state_codes = [row["state"] for row in state_rows]
    if len(state_codes) != len(set(state_codes)):
        raise ValueError("State coverage contains duplicate state rows")
    if set(state_codes) != set(STATE_NAMES):
        missing = sorted(set(STATE_NAMES) - set(state_codes))
        extra = sorted(set(state_codes) - set(STATE_NAMES))
        raise ValueError(f"State coverage mismatch; missing={missing}, extra={extra}")

    universe_total = sum(as_int(row["municipalities_in_universe"]) for row in state_rows)
    if universe_total != len(universe_rows):
        raise ValueError(
            f"Universe mismatch: state summary={universe_total}, universe rows={len(universe_rows)}"
        )
    if universe_total != len(municipality_rows):
        raise ValueError(
            "Coverage mismatch: state universe total="
            f"{universe_total}, municipality coverage rows={len(municipality_rows)}"
        )

    municipality_ids = [row["municipality_id"] for row in municipality_rows]
    if len(municipality_ids) != len(set(municipality_ids)):
        raise ValueError("Municipality coverage contains duplicate municipality_id values")

    queue_ids = [row["queue_id"] for row in queue_rows]
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Candidate queue contains duplicate queue_id values")

    invalid_scout_statuses = sorted(
        {
            row.get("scout_stage_status", "")
            for row in queue_rows
            if row.get("scout_stage_status", "") != "unverified_scout_candidate"
            and not row.get("scout_stage_status", "").startswith("calibration_")
        }
    )
    if invalid_scout_statuses:
        raise ValueError(
            "Candidate queue contains unexpected scout/calibration status values: "
            + ", ".join(invalid_scout_statuses)
        )

    priority_ids = [row["municipality_id"] for row in priority_rows]
    if len(priority_ids) != len(universe_rows) or set(priority_ids) != set(municipality_ids):
        raise ValueError("Priority tier rows do not exactly match the municipality universe")
    if len(priority_ids) != len(set(priority_ids)):
        raise ValueError("Priority tier input contains duplicate municipality IDs")
    if {row["state"] for row in state_priority_rows} != set(STATE_NAMES):
        raise ValueError("State priority summary does not contain exactly 50 states plus DC")
    top_ranks = [as_int(row["rank"]) for row in top_priority_rows]
    if top_ranks != list(range(1, len(top_ranks) + 1)):
        raise ValueError("Top-priority target ranks are not contiguous from one")
    if any(row["future_scout_eligible_flag"] != "yes" for row in priority_rows if row["municipality_id"] in {target["municipality_id"] for target in top_priority_rows}):
        raise ValueError("Top-priority targets include an ineligible municipality")


def main() -> int:
    for path in REQUIRED_PATHS:
        if not path.exists():
            raise FileNotFoundError(f"Required dashboard source is missing: {relative(path)}")

    warnings: list[str] = []
    optional_availability = {relative(path): path.exists() for path in OPTIONAL_PATHS}
    for path in OPTIONAL_PATHS:
        if not path.exists():
            warnings.append(
                f"Optional input missing: {relative(path)}; related fields are empty or null."
            )

    state_rows = read_csv(STATE_COVERAGE_PATH)
    municipality_rows = read_csv(MUNICIPALITY_COVERAGE_PATH)
    universe_rows = read_csv(MUNICIPALITY_UNIVERSE_PATH)
    queue_rows = read_csv(CANDIDATE_QUEUE_PATH)
    priority_rows = read_csv(PRIORITY_TIERS_PATH)
    state_priority_rows = read_csv(STATE_PRIORITY_PATH)
    top_priority_rows = read_csv(TOP_PRIORITY_TARGETS_PATH)
    scout_yield_state_rows = read_csv(SCOUT_YIELD_STATE_PATH)
    scout_yield_wave_rows = read_csv(SCOUT_YIELD_WAVE_PATH)
    reports_index_source = read_json(REPORTS_INDEX_SOURCE_PATH)
    claim_rows = read_csv(CLAIM_REGISTER_PATH) if CLAIM_REGISTER_PATH.exists() else []
    claim_map_rows = (
        read_csv(STATE_CITY_CLAIM_MAP_PATH) if STATE_CITY_CLAIM_MAP_PATH.exists() else []
    )
    hypothesis_rows = (
        read_csv(HYPOTHESIS_TRACKER_PATH) if HYPOTHESIS_TRACKER_PATH.exists() else []
    )

    validate_inputs(
        state_rows=state_rows,
        municipality_rows=municipality_rows,
        universe_rows=universe_rows,
        queue_rows=queue_rows,
        priority_rows=priority_rows,
        state_priority_rows=state_priority_rows,
        top_priority_rows=top_priority_rows,
    )
    if {row["state"] for row in scout_yield_state_rows} != set(STATE_NAMES):
        raise ValueError("Scout-yield state output does not contain exactly 50 states plus DC")
    if len(scout_yield_wave_rows) < 3:
        raise ValueError("Scout runtime trends require at least the three reviewed waves")

    timestamp = generated_at()
    data_vintage = max(row.get("last_updated", "") for row in state_rows)
    source_paths = REQUIRED_PATHS + OPTIONAL_PATHS
    metadata = base_metadata(
        timestamp=timestamp,
        source_paths=source_paths,
        data_vintage=data_vintage,
        warnings=warnings,
    )

    state_summary = build_state_summary(
        state_rows=state_rows,
        queue_rows=queue_rows,
        claim_rows=claim_rows,
        claim_map_rows=claim_map_rows,
        metadata=metadata,
    )
    candidate_summary = build_candidate_queue_summary(
        queue_rows=queue_rows,
        state_rows=state_rows,
        metadata=metadata,
    )
    funnel = build_coverage_funnel(state_rows=state_rows, metadata=metadata)
    readiness = build_analysis_readiness(
        state_rows=state_rows,
        queue_rows=queue_rows,
        claim_rows=claim_rows,
        claim_map_rows=claim_map_rows,
        hypothesis_rows=hypothesis_rows,
        optional_availability=optional_availability,
        metadata=metadata,
    )
    priority_summary = build_priority_summary(
        priority_rows=priority_rows,
        metadata=metadata,
    )
    state_priority_summary = build_state_priority_layer(
        state_priority_rows=state_priority_rows,
        metadata=metadata,
    )
    top_priority_targets = build_top_priority_targets_layer(
        top_rows=top_priority_rows,
        metadata=metadata,
    )
    scout_operations = build_scout_operations_summary(
        state_rows=state_rows,
        queue_rows=queue_rows,
        wave_rows=scout_yield_wave_rows,
        metadata=metadata,
    )
    scout_yield_by_state = build_scout_yield_state_layer(
        state_yield_rows=scout_yield_state_rows,
        metadata=metadata,
    )
    scout_runtime_trends = build_scout_runtime_trends(
        wave_rows=scout_yield_wave_rows,
        state_rows=state_rows,
        metadata=metadata,
    )
    project_phase_summary = build_project_phase_summary(
        state_rows=state_rows,
        queue_rows=queue_rows,
        metadata=metadata,
    )
    parallel_scout_status = build_parallel_scout_status(
        state_rows=state_rows, metadata=metadata
    )
    verification_status_summary = build_verification_status_summary(
        queue_rows=queue_rows, metadata=metadata
    )
    content_triage_status_summary = build_content_triage_status_summary(
        queue_rows=queue_rows, metadata=metadata
    )
    source_review_status_summary = build_source_review_status_summary(
        metadata=metadata
    )
    reports_index = build_reports_index_layer(
        source_index=reports_index_source,
        metadata=metadata,
    )

    outputs = [
        write_json("state_summary.json", state_summary),
        write_json("candidate_queue_summary.json", candidate_summary),
        write_json("coverage_funnel.json", funnel),
        write_json("analysis_readiness.json", readiness),
        write_json("priority_summary.json", priority_summary),
        write_json("state_priority_summary.json", state_priority_summary),
        write_json("top_priority_targets.json", top_priority_targets),
        write_json("scout_operations_summary.json", scout_operations),
        write_json("scout_yield_by_state.json", scout_yield_by_state),
        write_json("scout_runtime_trends.json", scout_runtime_trends),
        write_json("project_phase_summary.json", project_phase_summary),
        write_json("parallel_scout_status.json", parallel_scout_status),
        write_json("verification_status_summary.json", verification_status_summary),
        write_json(
            "content_triage_status_summary.json", content_triage_status_summary
        ),
        write_json("source_review_status_summary.json", source_review_status_summary),
        write_json("reports_index.json", reports_index),
    ]

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    totals = state_summary["totals"]
    print(
        "Dashboard data built: "
        f"{len(state_summary['states'])} states/DC; "
        f"{totals['municipality_universe']:,} municipalities; "
        f"{totals['scout_covered_municipalities']:,} scout-covered; "
        f"{totals['candidate_rows']:,} candidate rows."
    )
    for path in outputs:
        print(relative(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
