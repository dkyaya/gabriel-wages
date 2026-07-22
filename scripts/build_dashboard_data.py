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
CLAIM_REGISTER_PATH = ANALYSIS_DIR / "claim_register_2026-07-12.csv"
STATE_CITY_CLAIM_MAP_PATH = ANALYSIS_DIR / "state_city_claim_map_2026-07-12.csv"
HYPOTHESIS_TRACKER_PATH = ANALYSIS_DIR / "hypothesis_tracker_2026-07-12.csv"

REQUIRED_PATHS = [
    STATE_COVERAGE_PATH,
    MUNICIPALITY_COVERAGE_PATH,
    MUNICIPALITY_UNIVERSE_PATH,
    CANDIDATE_QUEUE_PATH,
    PRIORITY_TIERS_PATH,
    STATE_PRIORITY_PATH,
    TOP_PRIORITY_TARGETS_PATH,
]
OPTIONAL_PATHS = [
    CLAIM_REGISTER_PATH,
    STATE_CITY_CLAIM_MAP_PATH,
    HYPOTHESIS_TRACKER_PATH,
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
    "Project-wide verified, ingested, wage-extraction, codified, and regression metrics are not yet wired into this dashboard build.",
    "Municipality priority tiers are transparent research-operational heuristics, not claims about unionization, departments, source availability, wage gaps, or causal effects.",
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
        "overall_status": "source_discovery_dashboard_mvp",
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
                "display_status": "project_wide_dashboard_input_not_available",
                "count": None,
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
                "display_status": "not_available",
                "observation_count": None,
            },
            "regression_stage": {
                "available": False,
                "display_status": "not_available",
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
        "target_count": len(targets),
        "targets": targets,
        "disclaimer": (
            "Targets are unverified scouting priorities, not evidence that a qualifying "
            "agreement or matched safety/non-safety set exists."
        ),
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

    outputs = [
        write_json("state_summary.json", state_summary),
        write_json("candidate_queue_summary.json", candidate_summary),
        write_json("coverage_funnel.json", funnel),
        write_json("analysis_readiness.json", readiness),
        write_json("priority_summary.json", priority_summary),
        write_json("state_priority_summary.json", state_priority_summary),
        write_json("top_priority_targets.json", top_priority_targets),
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
