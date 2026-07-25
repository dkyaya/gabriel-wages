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
SOURCE_REVIEW_PILOT_LIVE_SUMMARY_PATH = (
    SOURCE_REVIEW_PILOT_MANIFEST_PATH.parent
    / "source_review_live_collection_summary.json"
)
SOURCE_REVIEW_CONNECTION_DIAGNOSTIC_SUMMARY_PATH = (
    SOURCE_REVIEW_PILOT_MANIFEST_PATH.parent
    / "source_review_connection_diagnostic_summary.json"
)
SOURCE_REVIEW_HTTPX_RETRY_SUMMARY_PATH = (
    SOURCE_REVIEW_PILOT_MANIFEST_PATH.parent
    / "source_review_httpx_retry_collection_summary.json"
)
SOURCE_REVIEW_DURABLE_LEDGER_PATH = (
    ANALYSIS_DIR
    / "source_review_ledgers"
    / "source_review_ledger_latest.csv"
)
SOURCE_REVIEW_DURABLE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "source_review_ledgers"
    / "source_review_summary_latest.json"
)
SOURCE_REVIEW_CUMULATIVE_LEDGER_PATH = (
    ANALYSIS_DIR
    / "source_review_ledgers"
    / "source_review_ledger_cumulative.csv"
)
SOURCE_REVIEW_CUMULATIVE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "source_review_ledgers"
    / "source_review_summary_cumulative.json"
)
SOURCE_REVIEW_BATCH2_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "source_review_pilots"
    / "SOURCE-REVIEW-BATCH2-500-2026-07-24"
    / "source_review_batch2_500_collection_summary.json"
)
SOURCE_REVIEW_BATCH3_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "source_review_pilots"
    / "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
    / "source_review_batch3_3x500_collection_summary.json"
)
SOURCE_REVIEW_BATCH3_DURABLE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "source_review_ledgers"
    / "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
    / "source_review_summary.json"
)
PDF_READINESS_PILOT1_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "pdf_readiness_pilots"
    / "PDF-READINESS-PILOT1-150-2026-07-24"
    / "pdf_readiness_collection_summary.json"
)
PDF_READINESS_REMAINDER_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "pdf_readiness_pilots"
    / "PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24"
    / "pdf_readiness_collection_summary.json"
)
PDF_READINESS_DURABLE_LEDGER_PATH = (
    ANALYSIS_DIR
    / "pdf_readiness_ledgers"
    / "pdf_readiness_ledger_latest.csv"
)
PDF_READINESS_DURABLE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "pdf_readiness_ledgers"
    / "pdf_readiness_summary_cumulative.json"
)
TEXT_TABLE_DETECTION_PILOT1_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_pilots"
    / "TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24"
    / "text_table_detection_collection_summary.json"
)
TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_pilots"
    / "TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24"
    / "text_table_detection_collection_summary.json"
)
TEXT_TABLE_DETECTION_DURABLE_LEDGER_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_ledgers"
    / "text_table_detection_ledger_latest.csv"
)
TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_ledgers"
    / "text_table_detection_summary_cumulative.json"
)
TEXT_TABLE_CALIBRATION_SUBSET1_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
    / "calibration_sampling_summary.json"
)
TEXT_TABLE_CALIBRATION_SUBSET1_INPUT_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
    / "calibration_review_input.csv"
)
TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
    / "calibration_review_summary.json"
)
TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_LEDGER_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
    / "calibration_reviewed.csv"
)
TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_SUMMARY_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24"
    / "calibration_review_summary.json"
)
TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_LEDGER_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24"
    / "calibration_reviewed.csv"
)
TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_DECISION_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24"
    / "calibration_review2_decision.json"
)
TEXT_TABLE_CALIBRATION_REFINE1_READINESS_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_refine1_readiness_audit_2026-07-24.md"
)
TEXT_TABLE_CALIBRATION_REFINED_SCHEMA_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_refined_schema_2026-07-24.md"
)
TEXT_TABLE_CALIBRATION_REFINED_RUBRIC_PATH = (
    ANALYSIS_DIR
    / "text_table_detection_refined_review_rubric_2026-07-24.md"
)
TEXT_TABLE_CALIBRATION_REFINED_REVIEW_PROMPT_PATH = (
    ANALYSIS_DIR
    / "text_table_calibration_subset1_refined_re_review_prompt_2026-07-24.md"
)
TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_DIR = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24"
)
TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_MANIFEST_PATH = (
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_DIR
    / "independent_adjudication_manifest.json"
)
TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_BLINDED_INPUT_PATH = (
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_DIR
    / "independent_adjudication_blinded_review_input.csv"
)
TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_RENDER_MANIFEST_PATH = (
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_DIR
    / "independent_adjudication_render_manifest.csv"
)
TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_SAMPLING_SUMMARY_PATH = (
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_DIR
    / "independent_adjudication_sampling_summary.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE1_DIR = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24"
)
TEXT_TABLE_AUTO_GABRIEL_GATE1_SUMMARY_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE1_DIR
    / "auto_gabriel_adjudication_summary.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE1_LEDGER_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE1_DIR
    / "auto_gabriel_adjudication_ledger.csv"
)
TEXT_TABLE_AUTO_GABRIEL_GATE1_DECISION_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE1_DIR
    / "auto_gabriel_adjudication_gate_decision.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE2_DIR = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25"
)
TEXT_TABLE_AUTO_GABRIEL_GATE2_SUMMARY_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE2_DIR
    / "auto_gabriel_adjudication_summary.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE2_LEDGER_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE2_DIR
    / "auto_gabriel_adjudication_ledger.csv"
)
TEXT_TABLE_AUTO_GABRIEL_GATE2_DECISION_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE2_DIR
    / "auto_gabriel_adjudication_gate_decision.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE3_DIR = (
    ANALYSIS_DIR
    / "text_table_calibration"
    / "TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25"
)
TEXT_TABLE_AUTO_GABRIEL_GATE3_SUMMARY_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE3_DIR
    / "auto_gabriel_compensation_adjudication_summary.json"
)
TEXT_TABLE_AUTO_GABRIEL_GATE3_LEDGER_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE3_DIR
    / "auto_gabriel_compensation_adjudication_ledger.csv"
)
TEXT_TABLE_AUTO_GABRIEL_GATE3_DECISION_PATH = (
    TEXT_TABLE_AUTO_GABRIEL_GATE3_DIR
    / "auto_gabriel_compensation_gate_decision.json"
)
COMPENSATION_EXTRACTION_500_DIR = (
    ANALYSIS_DIR
    / "compensation_extraction"
    / "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25"
)
COMPENSATION_EXTRACTION_500_SELECTION_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "compensation_extraction_500_selection_manifest.csv"
)
COMPENSATION_EXTRACTION_500_PACKET_SUMMARY_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "compensation_extraction_500_packet_summary.json"
)
COMPENSATION_EXTRACTION_500_DECISION_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "compensation_extraction_500_decision_report.json"
)
COMPENSATION_EXTRACTION_500_QUANT_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "lanes/quantitative/quantitative_extraction_ledger.csv"
)
COMPENSATION_EXTRACTION_500_QUAL_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv"
)
COMPENSATION_EXTRACTION_500_MIXED_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "lanes/mixed/mixed_extraction_ledger.csv"
)
COMPENSATION_EXTRACTION_500_NONBASE_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "lanes/non_base_wage/non_base_wage_compensation_ledger.csv"
)
COMPENSATION_EXTRACTION_500_REFERENCE_PATH = (
    COMPENSATION_EXTRACTION_500_DIR
    / "lanes/reference_and_exclusion/reference_exclusion_ledger.csv"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR = (
    ANALYSIS_DIR
    / "compensation_extraction"
    / "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_DECISION_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "compensation_extraction_500_recomputed_decision.json"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_SUMMARY_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "compensation_extraction_500_targeted_qa_summary.json"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_QUANT_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "quantitative_extraction_ledger_qa_corrected.csv"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_QUAL_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "qualitative_mechanism_extraction_ledger_qa_corrected.csv"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_MIXED_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "mixed_extraction_ledger_qa_corrected.csv"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_NONBASE_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "non_base_wage_compensation_ledger_qa_corrected.csv"
)
COMPENSATION_EXTRACTION_500_TARGETED_QA_REFERENCE_PATH = (
    COMPENSATION_EXTRACTION_500_TARGETED_QA_DIR
    / "reference_exclusion_ledger_qa_corrected.csv"
)
COMPENSATION_EXTRACTION_1000_DIR = (
    ANALYSIS_DIR
    / "compensation_extraction"
    / "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
)
COMPENSATION_EXTRACTION_1000_SELECTION_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_selection_manifest.csv"
)
COMPENSATION_EXTRACTION_1000_SELECTION_SUMMARY_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_selection_summary.json"
)
COMPENSATION_EXTRACTION_1000_PACKET_SUMMARY_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_packet_summary.json"
)
COMPENSATION_EXTRACTION_1000_PREFLIGHT_REPORT_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_preflight_report.md"
)
COMPENSATION_EXTRACTION_1000_REQUEST_METADATA_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_request_metadata.csv"
)
COMPENSATION_EXTRACTION_1000_DECISION_PATH = (
    COMPENSATION_EXTRACTION_1000_DIR
    / "compensation_extraction_1000_decision_report.json"
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
    SOURCE_REVIEW_PILOT_LIVE_SUMMARY_PATH,
    SOURCE_REVIEW_CONNECTION_DIAGNOSTIC_SUMMARY_PATH,
    SOURCE_REVIEW_HTTPX_RETRY_SUMMARY_PATH,
    SOURCE_REVIEW_DURABLE_LEDGER_PATH,
    SOURCE_REVIEW_DURABLE_SUMMARY_PATH,
    SOURCE_REVIEW_CUMULATIVE_LEDGER_PATH,
    SOURCE_REVIEW_CUMULATIVE_SUMMARY_PATH,
    SOURCE_REVIEW_BATCH2_SUMMARY_PATH,
    SOURCE_REVIEW_BATCH3_SUMMARY_PATH,
    SOURCE_REVIEW_BATCH3_DURABLE_SUMMARY_PATH,
    PDF_READINESS_PILOT1_SUMMARY_PATH,
    PDF_READINESS_REMAINDER_SUMMARY_PATH,
    PDF_READINESS_DURABLE_LEDGER_PATH,
    PDF_READINESS_DURABLE_SUMMARY_PATH,
    TEXT_TABLE_DETECTION_PILOT1_SUMMARY_PATH,
    TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH,
    TEXT_TABLE_DETECTION_DURABLE_LEDGER_PATH,
    TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_SUMMARY_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_INPUT_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_SUMMARY_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_LEDGER_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_SUMMARY_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_LEDGER_PATH,
    TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_DECISION_PATH,
    TEXT_TABLE_CALIBRATION_REFINE1_READINESS_PATH,
    TEXT_TABLE_CALIBRATION_REFINED_SCHEMA_PATH,
    TEXT_TABLE_CALIBRATION_REFINED_RUBRIC_PATH,
    TEXT_TABLE_CALIBRATION_REFINED_REVIEW_PROMPT_PATH,
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_MANIFEST_PATH,
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_BLINDED_INPUT_PATH,
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_RENDER_MANIFEST_PATH,
    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_SAMPLING_SUMMARY_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE1_SUMMARY_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE1_LEDGER_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE1_DECISION_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE2_SUMMARY_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE2_LEDGER_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE2_DECISION_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE3_SUMMARY_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE3_LEDGER_PATH,
    TEXT_TABLE_AUTO_GABRIEL_GATE3_DECISION_PATH,
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
    extraction_completed = all(path.exists() for path in (
        COMPENSATION_EXTRACTION_500_SELECTION_PATH,
        COMPENSATION_EXTRACTION_500_DECISION_PATH,
        COMPENSATION_EXTRACTION_500_QUANT_PATH,
        COMPENSATION_EXTRACTION_500_QUAL_PATH,
        COMPENSATION_EXTRACTION_500_MIXED_PATH,
        COMPENSATION_EXTRACTION_500_NONBASE_PATH,
        COMPENSATION_EXTRACTION_500_REFERENCE_PATH,
    ))
    targeted_qa_completed = all(path.exists() for path in (
        COMPENSATION_EXTRACTION_500_TARGETED_QA_DECISION_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_SUMMARY_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_QUANT_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_QUAL_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_MIXED_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_NONBASE_PATH,
        COMPENSATION_EXTRACTION_500_TARGETED_QA_REFERENCE_PATH,
    ))
    scale_1000_attempted = COMPENSATION_EXTRACTION_1000_DECISION_PATH.exists()
    scale_1000_decision = (
        read_json(COMPENSATION_EXTRACTION_1000_DECISION_PATH)
        if scale_1000_attempted else {}
    )
    extraction_decision = (
        read_json(COMPENSATION_EXTRACTION_500_TARGETED_QA_DECISION_PATH)
        if targeted_qa_completed
        else read_json(COMPENSATION_EXTRACTION_500_DECISION_PATH)
        if extraction_completed
        else {}
    )
    extraction_quant_count = (
        sum(
            row.get("active_in_corrected_lane") == "true"
            for row in read_csv(COMPENSATION_EXTRACTION_500_TARGETED_QA_QUANT_PATH)
        )
        if targeted_qa_completed
        else len(read_csv(COMPENSATION_EXTRACTION_500_QUANT_PATH))
        if extraction_completed
        else 0
    )
    extraction_qual_count = (
        sum(
            row.get("active_in_corrected_lane") == "true"
            for row in read_csv(COMPENSATION_EXTRACTION_500_TARGETED_QA_QUAL_PATH)
        )
        if targeted_qa_completed
        else len(read_csv(COMPENSATION_EXTRACTION_500_QUAL_PATH))
        if extraction_completed
        else 0
    )
    return {
        "metadata": metadata,
        "overall_status": (
            "provisional_1000_compensation_extraction_live_incomplete_499_of_500"
            if scale_1000_attempted
            else "provisional_500_compensation_extraction_targeted_qa_pass_1000_authorized"
            if targeted_qa_completed
            else "provisional_500_compensation_extraction_complete_scale_qa_hold"
            if extraction_completed
            else "verification_scale_up_planned_after_discovery_checkpoint"
        ),
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
                "available": extraction_completed,
                "display_status": (
                    "cumulative_1000_live_incomplete_499_of_500_no_materialization"
                    if scale_1000_attempted
                    else "targeted_qa_pass_1000_authorized_provisional_not_analysis_ready"
                    if targeted_qa_completed
                    else "provisional_500_complete_not_analysis_ready"
                    if extraction_completed
                    else "planned_after_scout_checkpoint_and_verification"
                ),
                "observation_count": (
                    extraction_quant_count if extraction_completed else None
                ),
                "qualitative_mechanism_observation_count": (
                    extraction_qual_count if extraction_completed else None
                ),
                "qa_status": extraction_decision.get("qa_status"),
                "scale_1000_recommendation": extraction_decision.get(
                    "scale_1000_recommendation"
                ) if not scale_1000_attempted else scale_1000_decision.get(
                    "decision"
                ),
                "analysis_ready": False,
                "targeted_qa_completed": targeted_qa_completed,
                "scale_1000_allowed": extraction_decision.get(
                    "scale_1000_allowed", False
                ) if not scale_1000_attempted else False,
                "scale_1000_live_started": scale_1000_decision.get(
                    "live_extraction_started", False
                ),
                "scale_beyond_1000_recommendation": scale_1000_decision.get(
                    "scale_beyond_1000_recommendation"
                ),
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
        ] + (
            ["provisional compensation-extraction QA diagnostics"]
            if extraction_completed
            else []
        ),
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
    payload = {
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
    if SOURCE_REVIEW_PILOT_LIVE_SUMMARY_PATH.exists():
        live = read_json(SOURCE_REVIEW_PILOT_LIVE_SUMMARY_PATH)
        if (
            live.get("status") != "pilot1_live_collected_not_merged"
            or live.get("pilot_id") != manifest["pilot_id"]
            or int(live.get("selected_rows", 0)) != selected_rows
            or int(live.get("ledger_rows", 0)) != selected_rows
            or int(live.get("terminal_rows", 0)) != selected_rows
        ):
            raise ValueError("Source-review live summary fails locked pilot gates")
        payload.update(
            {
                "stage": "source_review_pilot_live_collection",
                "source_review_phase": "pilot1_live_collected_not_merged",
                "source_review_live_status": "pilot1_collected_not_merged",
                "latest_source_review_pilot_id": live["pilot_id"],
                "pilot1_live_rows_collected": int(live["ledger_rows"]),
                "pilot1_terminal_rows": int(live["terminal_rows"]),
                "pilot1_source_review_merge_status": "not_started",
                "source_rating_status": "pilot1_collected_not_merged",
                "content_download_status": "pilot1_collected_not_merged",
                "extraction_readiness_status": "preliminary_pilot1_not_merged",
                "pilot1_source_review_status_counts": live[
                    "source_review_status_counts"
                ],
                "pilot1_url_access_status_counts": live[
                    "url_access_status_counts"
                ],
                "pilot1_download_status_counts": live[
                    "download_status_counts"
                ],
                "pilot1_content_type_observed_counts": live[
                    "content_type_observed_counts"
                ],
                "pilot1_content_artifact_count": int(
                    live["content_artifact_count"]
                ),
                "pilot1_metadata_artifact_count": int(
                    live["metadata_artifact_count"]
                ),
                "pilot1_total_artifact_bytes": int(
                    live["total_artifact_bytes"]
                ),
                "pilot1_manual_review_burden_rows": int(
                    live["manual_review_burden_rows"]
                ),
                "pilot1_lane_audit_recommendation": live[
                    "lane_audit_recommendation"
                ],
                "next_scaling_decision": live["scaling_recommendation"],
                "live_collection_summary_source": relative(
                    SOURCE_REVIEW_PILOT_LIVE_SUMMARY_PATH
                ),
                "caveats": live["caveats"]
                + [
                    "Preliminary source-review transport outcomes are not a durable merged source-rating ledger.",
                    "No source was ingested or codified and no wage data or wage gaps were calculated.",
                ],
            }
        )
    if SOURCE_REVIEW_CONNECTION_DIAGNOSTIC_SUMMARY_PATH.exists():
        diagnostic = read_json(
            SOURCE_REVIEW_CONNECTION_DIAGNOSTIC_SUMMARY_PATH
        )
        if (
            diagnostic.get("status")
            != "connection_diagnosis_completed_probe_succeeded"
            or diagnostic.get("pilot_id") != manifest["pilot_id"]
            or int(diagnostic.get("selected_rows", 0)) != 10
            or int(diagnostic.get("terminal_rows", 0)) != 10
            or int(diagnostic.get("connection_error_rows", -1)) != 0
            or int(diagnostic.get("content_artifact_count", 0)) != 9
            or int(diagnostic.get("rows_with_content_hash", 0)) != 9
        ):
            raise ValueError(
                "Source-review connection diagnostic summary fails probe gates"
            )
        payload.update(
            {
                "stage": "source_review_connection_diagnosis",
                "source_review_phase": (
                    "pilot1_connection_diagnosed_retry_not_started"
                ),
                "source_review_live_status": (
                    "pilot1_original_content_yield_failed_diagnosis_complete"
                ),
                "bounded_live_source_review_path": (
                    "httpx_patch_probe_succeeded"
                ),
                "connection_diagnosis_status": "completed_probe_succeeded",
                "diagnostic_probe_rows": int(diagnostic["selected_rows"]),
                "diagnostic_probe_terminal_rows": int(
                    diagnostic["terminal_rows"]
                ),
                "diagnostic_probe_source_review_status_counts": diagnostic[
                    "source_review_status_counts"
                ],
                "diagnostic_probe_url_access_status_counts": diagnostic[
                    "url_access_status_counts"
                ],
                "diagnostic_probe_download_status_counts": diagnostic[
                    "download_status_counts"
                ],
                "diagnostic_probe_content_type_observed_counts": diagnostic[
                    "content_type_observed_counts"
                ],
                "diagnostic_probe_connection_error_rows": int(
                    diagnostic["connection_error_rows"]
                ),
                "diagnostic_probe_content_artifact_count": int(
                    diagnostic["content_artifact_count"]
                ),
                "diagnostic_probe_rows_with_content_hash": int(
                    diagnostic["rows_with_content_hash"]
                ),
                "diagnostic_probe_content_artifact_bytes": int(
                    diagnostic["content_artifact_bytes"]
                ),
                "diagnostic_probe_root_cause": diagnostic["root_cause"],
                "pilot1_source_review_merge_status": "not_started",
                "source_rating_status": "diagnostic_probe_only_not_merged",
                "content_download_status": "diagnostic_probe_only_not_merged",
                "extraction_readiness_status": (
                    "preliminary_diagnostic_probe_only_not_merged"
                ),
                "next_scaling_decision": diagnostic[
                    "scaling_recommendation"
                ],
                "connection_diagnostic_summary_source": relative(
                    SOURCE_REVIEW_CONNECTION_DIAGNOSTIC_SUMMARY_PATH
                ),
                "caveats": [
                    "The original 150-row source-review attempt failed its content-yield gate and remains unmerged.",
                    "A verifier-compatible HTTP client diagnostic probe saved nine bounded PDF artifacts and retained one expected forbidden outcome.",
                    "The ten-row diagnostic proves repaired access mechanics; it is not a durable source-rating ledger or authorization to scale.",
                    "A full Pilot 1 retry requires separate authorization and fresh output directories.",
                    "No source was ingested or codified and no wage data or wage gaps were calculated.",
                ],
            }
        )
    if SOURCE_REVIEW_HTTPX_RETRY_SUMMARY_PATH.exists():
        retry = read_json(SOURCE_REVIEW_HTTPX_RETRY_SUMMARY_PATH)
        if (
            retry.get("status")
            != "pilot1_httpx_retry_collected_not_merged"
            or retry.get("pilot_id") != manifest["pilot_id"]
            or int(retry.get("selected_rows", 0)) != selected_rows
            or int(retry.get("ledger_rows", 0)) != selected_rows
            or int(retry.get("terminal_rows", 0)) != selected_rows
            or int(retry.get("connection_error_rows", -1)) != 0
            or int(retry.get("content_artifact_count", 0)) != 149
            or int(retry.get("rows_with_matching_content_hash", 0)) != 149
        ):
            raise ValueError(
                "Source-review HTTPX retry summary fails locked pilot gates"
            )
        payload.update(
            {
                "stage": "source_review_pilot_httpx_retry_collection",
                "source_review_phase": (
                    "pilot1_httpx_retry_collected_not_merged"
                ),
                "source_review_live_status": (
                    "pilot1_httpx_retry_collected_not_merged"
                ),
                "bounded_live_source_review_path": (
                    "httpx_retry_succeeded_not_merged"
                ),
                "latest_source_review_pilot_id": retry["pilot_id"],
                "pilot1_httpx_retry_rows_collected": int(
                    retry["ledger_rows"]
                ),
                "pilot1_httpx_retry_terminal_rows": int(
                    retry["terminal_rows"]
                ),
                "pilot1_httpx_retry_source_review_status_counts": retry[
                    "source_review_status_counts"
                ],
                "pilot1_httpx_retry_url_access_status_counts": retry[
                    "url_access_status_counts"
                ],
                "pilot1_httpx_retry_download_status_counts": retry[
                    "download_status_counts"
                ],
                "pilot1_httpx_retry_content_type_observed_counts": retry[
                    "content_type_observed_counts"
                ],
                "pilot1_httpx_retry_content_artifact_count": int(
                    retry["content_artifact_count"]
                ),
                "pilot1_httpx_retry_content_artifact_bytes": int(
                    retry["content_artifact_bytes"]
                ),
                "pilot1_httpx_retry_metadata_artifact_count": int(
                    retry["metadata_artifact_count"]
                ),
                "pilot1_httpx_retry_rows_with_content_hash": int(
                    retry["rows_with_content_hash"]
                ),
                "pilot1_httpx_retry_manual_review_burden_rows": int(
                    retry["manual_review_burden_rows"]
                ),
                "pilot1_httpx_retry_lane_audit_recommendation": retry[
                    "lane_audit_recommendation"
                ],
                "pilot1_source_review_merge_status": "not_started",
                "source_rating_status": (
                    "pilot1_httpx_retry_collected_not_merged"
                ),
                "content_download_status": (
                    "pilot1_httpx_retry_collected_not_merged"
                ),
                "extraction_readiness_status": (
                    "preliminary_pilot1_httpx_retry_not_merged"
                ),
                "next_scaling_decision": retry[
                    "scaling_recommendation"
                ],
                "httpx_retry_collection_summary_source": relative(
                    SOURCE_REVIEW_HTTPX_RETRY_SUMMARY_PATH
                ),
                "caveats": retry["caveats"],
            }
        )
    if SOURCE_REVIEW_DURABLE_SUMMARY_PATH.exists():
        durable = read_json(SOURCE_REVIEW_DURABLE_SUMMARY_PATH)
        statuses = durable.get("source_review_status_counts", {})
        readiness = durable.get(
            "extraction_readiness_rating_counts", {}
        )
        if durable.get("status") == "pilot1_httpx_merged":
            if (
                durable.get("source_review_pilot_id")
                != manifest["pilot_id"]
                or int(durable.get("ledger_rows", 0)) != selected_rows
                or int(durable.get("terminal_rows", 0)) != selected_rows
                or int(durable.get("content_artifact_count", 0)) != 149
                or int(durable.get("rows_with_matching_content_hash", 0))
                != 149
                or int(durable.get("merge_urls_opened", -1)) != 0
                or int(durable.get("merge_network_calls", -1)) != 0
            ):
                raise ValueError(
                    "Durable source-review summary fails Pilot 1 merge gates"
                )
            payload.update(
                {
                    "stage": "source_review_pilot_httpx_merged",
                    "source_review_phase": "pilot1_httpx_merged",
                    "source_review_live_status": "pilot1_httpx_merged",
                    "bounded_live_source_review_path": (
                        "implemented_httpx_pilot1_merged"
                    ),
                    "latest_source_review_pilot_id": durable[
                        "source_review_pilot_id"
                    ],
                    "latest_source_review_merge_id": durable[
                        "source_review_merge_id"
                    ],
                    "pilot1_rows_merged": int(durable["ledger_rows"]),
                    "pilot1_source_review_merge_status": "merged",
                    "pilot1_artifact_saved_rows": int(
                        statuses.get(
                            "reviewed_metadata_and_artifact_saved", 0
                        )
                    ),
                    "pilot1_forbidden_rows": int(
                        statuses.get("download_forbidden", 0)
                    ),
                    "pilot1_connection_error_rows": int(
                        statuses.get("download_connection_error", 0)
                    ),
                    "pilot1_content_artifact_bytes": int(
                        durable["content_artifact_bytes"]
                    ),
                    "pilot1_max_content_artifact_bytes": int(
                        durable["maximum_content_artifact_bytes"]
                    ),
                    "pilot1_preliminary_medium_extraction_readiness_rows": int(
                        readiness.get("medium", 0)
                    ),
                    "durable_source_review_ledger_latest": relative(
                        SOURCE_REVIEW_DURABLE_LEDGER_PATH
                    ),
                    "original_failed_attempt_status": durable[
                        "original_failed_attempt_status"
                    ],
                    "source_rating_status": (
                        "pilot1_preliminary_artifact_review_merged"
                    ),
                    "content_download_status": (
                        "pilot1_bounded_artifacts_merged"
                    ),
                    "extraction_readiness_status": (
                        "pilot1_preliminary_artifact_metadata_only"
                    ),
                    "ingestion_status": "not_started",
                    "codify_status": "not_started",
                    "wage_extraction_status": "not_started",
                    "wage_gap_analysis_status": "not_started",
                    "next_scaling_recommendation": (
                        "plan_500_after_relay_review"
                    ),
                    "next_scaling_decision": (
                        "plan_500_after_relay_review"
                    ),
                    "durable_source_review_summary_source": relative(
                        SOURCE_REVIEW_DURABLE_SUMMARY_PATH
                    ),
                    "caveats": [
                        "Source-review ratings are preliminary access/artifact signals.",
                        "PDFs were not parsed or OCRed.",
                        "Wage data were not extracted.",
                        "The original failed attempt is superseded and excluded from operative results.",
                    ],
                }
            )
        elif durable.get("status") == "source_review_cumulative_merged":
            durable_gate_by_batch = {
                "SOURCE-REVIEW-BATCH2-500-2026-07-24": {
                    "merge_id": "SOURCE-REVIEW-BATCH2-500-MERGE-2026-07-24",
                    "rows": 650,
                    "artifacts": 644,
                },
                "SOURCE-REVIEW-BATCH3-3X500-2026-07-24": {
                    "merge_id": (
                        "SOURCE-REVIEW-BATCH3-3X500-MERGE-2026-07-24"
                    ),
                    "rows": 2150,
                    "artifacts": 2124,
                },
            }
            durable_batch_id = durable.get(
                "latest_source_review_pilot_id"
            )
            gate = durable_gate_by_batch.get(durable_batch_id)
            if (
                gate is None
                or durable.get("latest_source_review_merge_id")
                != gate["merge_id"]
                or int(durable.get("ledger_rows", 0)) != gate["rows"]
                or int(durable.get("terminal_rows", 0)) != gate["rows"]
                or int(durable.get("content_artifact_count", 0))
                != gate["artifacts"]
                or int(durable.get("rows_with_matching_content_hash", 0))
                != gate["artifacts"]
                or int(durable.get("merge_urls_opened", -1)) != 0
                or int(durable.get("merge_network_calls", -1)) != 0
            ):
                raise ValueError(
                    "Cumulative source-review summary fails durable merge gates"
                )
            payload.update(
                {
                    "stage": "source_review_batch2_500_merged",
                    "source_review_phase": "batch2_500_merged",
                    "source_review_live_status": "batch2_500_merged",
                    "bounded_live_source_review_path": (
                        "implemented_httpx_batch2_merged"
                    ),
                    "latest_source_review_batch_id": durable[
                        "latest_source_review_pilot_id"
                    ],
                    "latest_source_review_merge_id": durable[
                        "latest_source_review_merge_id"
                    ],
                    "batch2_500_rows_merged": 500,
                    "batch2_500_artifact_saved_rows": 495,
                    "batch2_500_timeout_rows": 5,
                    "batch2_500_connection_error_rows": 0,
                    "batch2_500_content_artifact_bytes": 1008783033,
                    "batch2_500_total_artifact_bytes": 1009326270,
                    "batch2_500_max_content_artifact_bytes": 9476151,
                    "batch2_500_merge_status": "merged",
                    "cumulative_merged_source_review_rows": int(
                        durable["ledger_rows"]
                    ),
                    "cumulative_artifact_saved_rows": int(
                        statuses.get(
                            "reviewed_metadata_and_artifact_saved", 0
                        )
                    ),
                    "cumulative_content_artifact_bytes": int(
                        durable["content_artifact_bytes"]
                    ),
                    "cumulative_max_content_artifact_bytes": int(
                        durable["maximum_content_artifact_bytes"]
                    ),
                    "durable_source_review_ledger_latest": relative(
                        SOURCE_REVIEW_DURABLE_LEDGER_PATH
                    ),
                    "durable_source_review_ledger_cumulative": relative(
                        SOURCE_REVIEW_CUMULATIVE_LEDGER_PATH
                    ),
                    "source_rating_status": (
                        "batch2_preliminary_artifact_review_merged"
                    ),
                    "content_download_status": (
                        "batch2_bounded_artifacts_merged"
                    ),
                    "extraction_readiness_status": (
                        "preliminary_artifact_metadata_only"
                    ),
                    "ingestion_status": "not_started",
                    "codify_status": "not_started",
                    "wage_extraction_status": "not_started",
                    "wage_gap_analysis_status": "not_started",
                    "next_scaling_recommendation": "prepare_batch3_1000",
                    "next_scaling_decision": "prepare_batch3_1000",
                    "durable_source_review_summary_source": relative(
                        SOURCE_REVIEW_DURABLE_SUMMARY_PATH
                    ),
                    "durable_source_review_cumulative_summary_source": relative(
                        SOURCE_REVIEW_CUMULATIVE_SUMMARY_PATH
                    ),
                    "caveats": [
                        "Source-review ratings are preliminary access/artifact signals.",
                        "PDFs were not parsed or OCRed.",
                        "Wage data were not extracted.",
                        "Batch 3 may be planned at 1,000 only after this merge relay is reviewed.",
                    ],
                }
            )
        else:
            raise ValueError("Unrecognized durable source-review status")
    if SOURCE_REVIEW_BATCH2_SUMMARY_PATH.exists():
        batch2 = read_json(SOURCE_REVIEW_BATCH2_SUMMARY_PATH)
        if (
            batch2.get("status") != "batch2_500_collected_not_merged"
            or batch2.get("batch_id")
            != "SOURCE-REVIEW-BATCH2-500-2026-07-24"
            or int(batch2.get("planned_rows", 0)) != 500
            or int(batch2.get("ledger_rows", 0)) != 500
            or int(batch2.get("terminal_rows", 0)) != 500
            or int(batch2.get("pilot1_candidate_overlap", -1)) != 0
            or int(batch2.get("pilot1_source_review_id_overlap", -1)) != 0
            or int(batch2.get("content_artifact_count", 0)) != 495
            or int(batch2.get("rows_with_matching_content_hash", 0)) != 495
            or int(batch2.get("documents_parsed", -1)) != 0
            or int(batch2.get("pdfs_parsed", -1)) != 0
            or int(batch2.get("ocr_runs", -1)) != 0
            or int(batch2.get("content_sample_count", -1)) != 0
            or batch2.get("durable_batch2_merge_status") != "not_started"
            or batch2.get("merge_recommendation")
            != "merge_all_source_review_lanes"
        ):
            raise ValueError(
                "Source-review Batch 2 summary fails collection gates"
            )
        payload.update(
            {
                "latest_source_review_batch_id": batch2["batch_id"],
                "batch2_500_rows_collected": int(batch2["ledger_rows"]),
                "batch2_500_terminal_rows": int(batch2["terminal_rows"]),
                "batch2_500_source_review_status_counts": batch2[
                    "source_review_status_counts"
                ],
                "batch2_500_url_access_status_counts": batch2[
                    "url_access_status_counts"
                ],
                "batch2_500_download_status_counts": batch2[
                    "download_status_counts"
                ],
                "batch2_500_content_type_observed_counts": batch2[
                    "content_type_observed_counts"
                ],
                "batch2_500_content_artifact_count": int(
                    batch2["content_artifact_count"]
                ),
                "batch2_500_content_artifact_bytes": int(
                    batch2["content_artifact_bytes"]
                ),
                "batch2_500_maximum_content_artifact_bytes": int(
                    batch2["maximum_content_artifact_bytes"]
                ),
                "batch2_500_rows_with_content_hash": int(
                    batch2["rows_with_content_hash"]
                ),
                "batch2_500_manual_review_burden_rows": int(
                    batch2["manual_review_burden_rows"]
                ),
                "batch2_500_lane_audit_recommendation": batch2[
                    "merge_recommendation"
                ],
                "batch2_collection_summary_source": relative(
                    SOURCE_REVIEW_BATCH2_SUMMARY_PATH
                ),
            }
        )
        if payload.get("source_review_phase") != "batch2_500_merged":
            payload.update(
                {
                    "stage": "source_review_batch2_500_collection",
                    "bounded_live_source_review_path": (
                        "implemented_httpx_batch2_collected"
                    ),
                    "source_review_phase": (
                        "batch2_500_collected_not_merged"
                    ),
                    "source_review_live_status": (
                        "batch2_500_collected_not_merged"
                    ),
                    "batch2_500_merge_status": "not_started",
                    "cumulative_merged_source_review_rows": int(
                        batch2["cumulative_merged_source_review_rows"]
                    ),
                    "source_rating_status": (
                        "batch2_500_collected_not_merged"
                    ),
                    "content_download_status": (
                        "batch2_500_collected_not_merged"
                    ),
                    "extraction_readiness_status": (
                        "preliminary_batch2_not_merged"
                    ),
                    "ingestion_status": "not_started",
                    "codify_status": "not_started",
                    "wage_extraction_status": "not_started",
                    "wage_gap_analysis_status": "not_started",
                    "next_scaling_decision": batch2[
                        "next_scaling_recommendation"
                    ],
                    "next_scaling_recommendation": batch2[
                        "next_scaling_recommendation"
                    ],
                    "caveats": batch2["caveats"],
                }
            )
    if SOURCE_REVIEW_BATCH3_SUMMARY_PATH.exists():
        batch3 = read_json(SOURCE_REVIEW_BATCH3_SUMMARY_PATH)
        if (
            batch3.get("status")
            != "batch3_3x500_collected_not_merged"
            or batch3.get("batch_id")
            != "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
            or int(batch3.get("planned_rows", 0)) != 1500
            or int(batch3.get("ledger_rows", 0)) != 1500
            or int(batch3.get("terminal_rows", 0)) != 1500
            or int(batch3.get("prior_candidate_overlap", -1)) != 0
            or int(batch3.get("prior_source_review_id_overlap", -1)) != 0
            or int(batch3.get("content_artifact_count", 0)) != 1480
            or int(batch3.get("rows_with_matching_content_hash", 0))
            != 1480
            or int(batch3.get("documents_parsed", -1)) != 0
            or int(batch3.get("pdfs_parsed", -1)) != 0
            or int(batch3.get("ocr_runs", -1)) != 0
            or int(batch3.get("content_sample_count", -1)) != 0
            or batch3.get("durable_batch3_merge_status") != "not_started"
            or batch3.get("merge_recommendation")
            != "merge_all_source_review_lanes"
            or int(batch3.get("cumulative_merged_source_review_rows", 0))
            != 650
        ):
            raise ValueError(
                "Source-review Batch 3 summary fails collection gates"
            )
        payload.update(
            {
                "stage": "source_review_batch3_3x500_collection",
                "source_review_phase": (
                    "batch3_3x500_collected_not_merged"
                ),
                "source_review_live_status": (
                    "batch3_3x500_collected_not_merged"
                ),
                "bounded_live_source_review_path": (
                    "implemented_httpx_batch3_collected"
                ),
                "latest_source_review_batch_id": batch3["batch_id"],
                "batch3_3x500_rows_collected": int(
                    batch3["ledger_rows"]
                ),
                "batch3_3x500_terminal_rows": int(
                    batch3["terminal_rows"]
                ),
                "batch3_3x500_merge_status": "not_started",
                "batch3_3x500_priority_distribution": batch3[
                    "selected_priority_distribution"
                ],
                "batch3_3x500_source_review_status_counts": batch3[
                    "source_review_status_counts"
                ],
                "batch3_3x500_url_access_status_counts": batch3[
                    "url_access_status_counts"
                ],
                "batch3_3x500_download_status_counts": batch3[
                    "download_status_counts"
                ],
                "batch3_3x500_content_type_observed_counts": batch3[
                    "content_type_observed_counts"
                ],
                "batch3_3x500_content_artifact_count": int(
                    batch3["content_artifact_count"]
                ),
                "batch3_3x500_content_artifact_bytes": int(
                    batch3["content_artifact_bytes"]
                ),
                "batch3_3x500_total_artifact_bytes": int(
                    batch3["total_artifact_bytes"]
                ),
                "batch3_3x500_max_content_artifact_bytes": int(
                    batch3["maximum_content_artifact_bytes"]
                ),
                "batch3_3x500_rows_with_content_hash": int(
                    batch3["rows_with_content_hash"]
                ),
                "batch3_3x500_timeout_rows": int(
                    batch3["source_review_status_counts"].get(
                        "download_timeout", 0
                    )
                ),
                "batch3_3x500_forbidden_rows": int(
                    batch3["source_review_status_counts"].get(
                        "download_forbidden", 0
                    )
                ),
                "batch3_3x500_connection_error_rows": int(
                    batch3["source_review_status_counts"].get(
                        "download_connection_error", 0
                    )
                ),
                "batch3_3x500_manual_review_burden_rows": int(
                    batch3["manual_review_burden_rows"]
                ),
                "batch3_3x500_lane_audit_recommendation": batch3[
                    "merge_recommendation"
                ],
                "batch3_collection_summary_source": relative(
                    SOURCE_REVIEW_BATCH3_SUMMARY_PATH
                ),
                "cumulative_merged_source_review_rows": 650,
                "source_rating_status": (
                    "batch3_3x500_collected_not_merged"
                ),
                "content_download_status": (
                    "batch3_3x500_collected_not_merged"
                ),
                "extraction_readiness_status": (
                    "preliminary_batch3_not_merged"
                ),
                "ingestion_status": "not_started",
                "codify_status": "not_started",
                "wage_extraction_status": "not_started",
                "wage_gap_analysis_status": "not_started",
                "next_scaling_decision": batch3[
                    "next_phase_recommendation"
                ],
                "next_scaling_recommendation": batch3[
                    "next_phase_recommendation"
                ],
                "caveats": batch3["caveats"],
            }
        )
    if SOURCE_REVIEW_BATCH3_DURABLE_SUMMARY_PATH.exists():
        batch3_durable = read_json(
            SOURCE_REVIEW_BATCH3_DURABLE_SUMMARY_PATH
        )
        durable = read_json(SOURCE_REVIEW_CUMULATIVE_SUMMARY_PATH)
        if (
            batch3_durable.get("status") != "batch3_3x500_merged"
            or batch3_durable.get("source_review_pilot_id")
            != "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
            or batch3_durable.get("source_review_merge_id")
            != "SOURCE-REVIEW-BATCH3-3X500-MERGE-2026-07-24"
            or int(batch3_durable.get("ledger_rows", 0)) != 1500
            or int(batch3_durable.get("terminal_rows", 0)) != 1500
            or int(batch3_durable.get("content_artifact_count", 0)) != 1480
            or int(batch3_durable.get("rows_with_matching_content_hash", 0))
            != 1480
            or int(batch3_durable.get("merge_urls_opened", -1)) != 0
            or int(batch3_durable.get("merge_network_calls", -1)) != 0
            or int(durable.get("ledger_rows", 0)) != 2150
            or int(durable.get("terminal_rows", 0)) != 2150
            or int(durable.get("content_artifact_count", 0)) != 2124
            or int(durable.get("rows_with_matching_content_hash", 0))
            != 2124
            or int(durable.get("content_artifact_bytes", 0))
            != 4500367582
            or int(durable.get("merge_urls_opened", -1)) != 0
            or int(durable.get("merge_network_calls", -1)) != 0
        ):
            raise ValueError(
                "Source-review Batch 3 durable summaries fail merge gates"
            )
        payload.update(
            {
                "stage": "source_review_batch3_3x500_merged",
                "source_review_phase": "batch3_3x500_merged",
                "source_review_live_status": "batch3_3x500_merged",
                "bounded_live_source_review_path": (
                    "implemented_httpx_batch3_merged"
                ),
                "latest_source_review_batch_id": batch3_durable[
                    "source_review_pilot_id"
                ],
                "latest_source_review_merge_id": batch3_durable[
                    "source_review_merge_id"
                ],
                "batch3_3x500_rows_merged": int(
                    batch3_durable["ledger_rows"]
                ),
                "batch3_3x500_artifact_saved_rows": int(
                    batch3_durable["source_review_status_counts"].get(
                        "reviewed_metadata_and_artifact_saved", 0
                    )
                ),
                "batch3_3x500_timeout_rows": int(
                    batch3_durable["source_review_status_counts"].get(
                        "download_timeout", 0
                    )
                ),
                "batch3_3x500_forbidden_rows": int(
                    batch3_durable["source_review_status_counts"].get(
                        "download_forbidden", 0
                    )
                ),
                "batch3_3x500_connection_error_rows": int(
                    batch3_durable["source_review_status_counts"].get(
                        "download_connection_error", 0
                    )
                ),
                "batch3_3x500_content_artifact_bytes": int(
                    batch3_durable["content_artifact_bytes"]
                ),
                "batch3_3x500_total_artifact_bytes": int(
                    batch3_durable["total_artifact_bytes"]
                ),
                "batch3_3x500_max_content_artifact_bytes": int(
                    batch3_durable["maximum_content_artifact_bytes"]
                ),
                "batch3_3x500_merge_status": "merged",
                "cumulative_merged_source_review_rows": int(
                    durable["ledger_rows"]
                ),
                "cumulative_artifact_saved_rows": int(
                    durable["source_review_status_counts"].get(
                        "reviewed_metadata_and_artifact_saved", 0
                    )
                ),
                "cumulative_content_artifact_bytes": int(
                    durable["content_artifact_bytes"]
                ),
                "cumulative_total_artifact_bytes": int(
                    durable["total_artifact_bytes"]
                ),
                "cumulative_max_content_artifact_bytes": int(
                    durable["maximum_content_artifact_bytes"]
                ),
                "durable_source_review_ledger_latest": relative(
                    SOURCE_REVIEW_DURABLE_LEDGER_PATH
                ),
                "durable_source_review_ledger_cumulative": relative(
                    SOURCE_REVIEW_CUMULATIVE_LEDGER_PATH
                ),
                "source_rating_status": (
                    "batch3_preliminary_artifact_review_merged"
                ),
                "content_download_status": (
                    "batch3_bounded_artifacts_merged"
                ),
                "extraction_readiness_status": (
                    "preliminary_artifact_metadata_only"
                ),
                "ingestion_status": "not_started",
                "codify_status": "not_started",
                "wage_extraction_status": "not_started",
                "wage_gap_analysis_status": "not_started",
                "next_recommendation": (
                    "text_layer_page_count_readiness_pilot"
                ),
                "next_scaling_decision": (
                    "text_layer_page_count_readiness_pilot"
                ),
                "next_scaling_recommendation": (
                    "text_layer_page_count_readiness_pilot"
                ),
                "durable_source_review_summary_source": relative(
                    SOURCE_REVIEW_DURABLE_SUMMARY_PATH
                ),
                "durable_source_review_cumulative_summary_source": relative(
                    SOURCE_REVIEW_CUMULATIVE_SUMMARY_PATH
                ),
                "batch3_durable_summary_source": relative(
                    SOURCE_REVIEW_BATCH3_DURABLE_SUMMARY_PATH
                ),
                "caveats": [
                    "Source-review ratings are preliminary access/artifact signals.",
                    "PDFs were not parsed or OCRed.",
                    "Wage data were not extracted.",
                    "The next step should test text-layer and page-count readiness before more bulk downloading.",
                ],
            }
        )
    return payload


def build_pdf_readiness_status_summary(
    *, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Build the local-only PDF-readiness collection status."""

    if not PDF_READINESS_PILOT1_SUMMARY_PATH.exists():
        return {
            **metadata,
            "pdf_readiness_phase": "not_started",
            "latest_pdf_readiness_pilot_id": None,
            "pilot_rows_collected": 0,
            "pdf_readiness_merge_status": "not_started",
            "source_review_rows_available": 2150,
            "retained_pdf_artifacts_available": 2124,
            "text_layer_status_counts": {},
            "technical_parseability_rating_counts": {},
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "caveats": [
                "PDF readiness has not started.",
                "No OCR, wage extraction, or ingestion has occurred.",
            ],
        }
    pilot = read_json(PDF_READINESS_PILOT1_SUMMARY_PATH)
    if (
        pilot.get("status") != "pdf_readiness_pilot1_collected_not_merged"
        or pilot.get("pilot_id")
        != "PDF-READINESS-PILOT1-150-2026-07-24"
        or int(pilot.get("planned_rows", 0)) != 150
        or int(pilot.get("ledger_rows", 0)) != 150
        or int(pilot.get("terminal_rows", 0)) != 150
        or pilot.get("lane_rows") != [50, 50, 50]
        or int(pilot.get("parser_error_rows", -1)) != 0
        or int(pilot.get("hash_failure_rows", -1)) != 0
        or int(pilot.get("missing_artifact_rows", -1)) != 0
        or int(pilot.get("urls_opened", -1)) != 0
        or int(pilot.get("network_calls", -1)) != 0
        or int(pilot.get("downloads", -1)) != 0
        or int(pilot.get("ocr_runs", -1)) != 0
        or int(pilot.get("full_text_artifacts_written", -1)) != 0
        or int(pilot.get("wage_values_extracted", -1)) != 0
        or int(pilot.get("ingestion_actions", -1)) != 0
        or int(pilot.get("codify_actions", -1)) != 0
        or pilot.get("durable_readiness_merge_status") != "not_started"
        or pilot.get("merge_recommendation")
        != "merge_all_pdf_readiness_lanes"
    ):
        raise ValueError("PDF-readiness Pilot 1 summary fails collection gates")
    if PDF_READINESS_DURABLE_SUMMARY_PATH.exists():
        durable = read_json(PDF_READINESS_DURABLE_SUMMARY_PATH)
        retained = int(durable.get("retained_pdf_artifacts_available", 0))
        merged = int(durable.get("pdf_readiness_rows_merged", 0))
        identity = durable.get("exact_retained_pdf_identity_equality", {})
        forbidden_fields = (
            "urls_opened",
            "network_calls",
            "downloads",
            "redownloads",
            "ocr_runs",
            "full_text_artifacts_written",
            "wage_tables_extracted",
            "wage_values_extracted",
            "ingestion_actions",
            "codify_actions",
            "scout_accounting_mutations",
            "routing_ledger_mutations",
            "metadata_triage_ledger_mutations",
            "source_review_ledger_mutations",
        )
        if (
            durable.get("status") != "pdf_readiness_full_retained_merged"
            or durable.get("pdf_readiness_merge_id")
            != "PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24"
            or durable.get("pdf_readiness_stage")
            != "technical_readiness_checked_not_extracted"
            or merged != retained
            or float(
                durable.get("retained_pdf_readiness_coverage_rate", 0)
            )
            != 1.0
            or int(durable.get("unique_pdf_readiness_ids", 0)) != merged
            or int(durable.get("unique_source_review_ids", 0)) != merged
            or int(durable.get("unique_candidate_queue_row_ids", 0))
            != merged
            or any(
                int(durable.get(field, -1)) != 0
                for field in (
                    "duplicate_pdf_readiness_ids",
                    "duplicate_source_review_ids",
                    "duplicate_candidate_queue_row_ids",
                    "missing_artifacts",
                    "hash_failures",
                    "invalid_pdf_signatures",
                    "parser_errors",
                    *forbidden_fields,
                )
            )
            or int(durable.get("durable_readiness_merges", 0)) != 1
            or identity.get("source_review_id_set_equal") is not True
            or identity.get("candidate_queue_row_id_set_equal") is not True
            or identity.get("authority_field_mismatch_counts") != {}
            or durable.get("readiness_status_counts")
            != {"readiness_checked": merged}
            or int(
                durable.get("page_count_summary", {}).get("count", 0)
            )
            != merged
            or not PDF_READINESS_DURABLE_LEDGER_PATH.exists()
        ):
            raise ValueError(
                "durable full-retained PDF-readiness summary fails gates"
            )
        text_counts = durable["text_layer_status_counts"]
        action_counts = durable["recommended_next_action_counts"]
        pages = durable["page_count_summary"]
        return {
            **metadata,
            "pdf_readiness_phase": "full_retained_merged",
            "latest_pdf_readiness_pilot_id": pilot["pilot_id"],
            "latest_pdf_readiness_round_id": (
                "PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24"
            ),
            "latest_pdf_readiness_merge_id": durable[
                "pdf_readiness_merge_id"
            ],
            "pdf_readiness_merge_status": "merged",
            "source_review_rows_available": int(
                durable["source_review_rows"]
            ),
            "retained_pdf_artifacts_available": retained,
            "pdf_readiness_rows_merged": merged,
            "retained_pdf_readiness_coverage_rate": float(
                durable["retained_pdf_readiness_coverage_rate"]
            ),
            "readiness_status_counts": durable["readiness_status_counts"],
            "text_layer_status_counts": text_counts,
            "text_layer_present_rows": int(text_counts.get("present", 0)),
            "text_layer_partial_rows": int(text_counts.get("partial", 0)),
            "text_layer_absent_rows": int(text_counts.get("absent", 0)),
            "technical_parseability_rating_counts": durable[
                "technical_parseability_rating_counts"
            ],
            "recommended_next_action_counts": action_counts,
            "parse_text_layer_later_rows": int(
                action_counts.get("parse_text_layer_later", 0)
            ),
            "ocr_later_rows": int(action_counts.get("ocr_later", 0)),
            "page_count_summary": pages,
            "total_pages_represented": int(pages["total_pages"]),
            "median_page_count": pages["median"],
            "max_page_count": pages["maximum"],
            "sampled_pages_checked": int(
                durable["sampled_pages_checked"]
            ),
            "sampled_pages_with_text": int(
                durable["sampled_pages_with_text"]
            ),
            "parser_library_counts": durable["parser_library_counts"],
            "parser_version_counts": durable["parser_version_counts"],
            "parser_error_rows": int(durable["parser_errors"]),
            "hash_failure_rows": int(durable["hash_failures"]),
            "missing_artifact_rows": int(durable["missing_artifacts"]),
            "durable_pdf_readiness_ledger_latest": relative(
                PDF_READINESS_DURABLE_LEDGER_PATH
            ),
            "technical_readiness_status": "complete_for_retained_pdfs",
            "next_recommendation": "text_layer_table_detection_pilot",
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "summary_source": relative(
                PDF_READINESS_DURABLE_SUMMARY_PATH
            ),
            "caveats": [
                "PDF-readiness is technical parseability only.",
                "Text-layer presence does not prove wage data exists.",
                "OCR has not run.",
                "Wage extraction has not started.",
                "No ingestion or codification has occurred.",
            ],
        }
    if PDF_READINESS_REMAINDER_SUMMARY_PATH.exists():
        full = read_json(PDF_READINESS_REMAINDER_SUMMARY_PATH)
        if (
            full.get("status")
            != "pdf_readiness_full_retained_collected_not_merged"
            or full.get("round_id")
            != "PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24"
            or full.get("pilot1_id")
            != "PDF-READINESS-PILOT1-150-2026-07-24"
            or int(full.get("pilot1_rows", 0)) != 150
            or int(full.get("remainder_rows", 0)) != 1974
            or int(full.get("full_retained_rows_collected", 0)) != 2124
            or int(full.get("retained_pdf_artifacts_available", 0)) != 2124
            or full.get("remainder_lane_rows") != [494, 494, 493, 493]
            or int(full.get("remainder_terminal_rows", 0)) != 1974
            or full.get("remainder_lane_classification_counts")
            != {"completed_merge_eligible": 4}
            or full.get("full_readiness_status_counts")
            != {"readiness_checked": 2124}
            or int(full.get("full_page_count_summary", {}).get("count", 0))
            != 2124
            or any(
                int(full.get(field, -1)) != 0
                for field in (
                    "hash_failures",
                    "missing_artifacts",
                    "invalid_pdf_signatures",
                    "parser_errors",
                    "urls_opened",
                    "network_calls",
                    "downloads",
                    "redownloads",
                    "ocr_runs",
                    "full_text_artifacts_written",
                    "wage_tables_extracted",
                    "wage_values_extracted",
                    "ingestion_actions",
                    "codify_actions",
                    "durable_readiness_merges",
                )
            )
            or full.get("pilot1_merge_status") != "not_started"
            or full.get("remainder_merge_status") != "not_started"
        ):
            raise ValueError(
                "full-retained PDF-readiness summary fails collection gates"
            )
        return {
            **metadata,
            "pdf_readiness_phase": "full_retained_collected_not_merged",
            "latest_pdf_readiness_pilot_id": pilot["pilot_id"],
            "latest_pdf_readiness_round_id": full["round_id"],
            "pilot_rows_collected": int(full["pilot1_rows"]),
            "remainder_rows_collected": int(full["remainder_rows"]),
            "full_retained_pdf_readiness_rows_collected": int(
                full["full_retained_rows_collected"]
            ),
            "remainder_lane_rows": full["remainder_lane_rows"],
            "pdf_readiness_merge_status": "not_started",
            "source_review_rows_available": int(
                full["source_review_rows_available"]
            ),
            "retained_pdf_artifacts_available": int(
                full["retained_pdf_artifacts_available"]
            ),
            "readiness_status_counts": full[
                "full_readiness_status_counts"
            ],
            "text_layer_status_counts": full[
                "full_text_layer_status_counts"
            ],
            "technical_parseability_rating_counts": full[
                "full_technical_parseability_rating_counts"
            ],
            "recommended_next_action_counts": full[
                "full_recommended_next_action_counts"
            ],
            "page_count_summary": full["full_page_count_summary"],
            "sampled_pages_checked": int(
                full["full_sampled_pages_checked"]
            ),
            "sampled_pages_with_text": int(
                full["full_sampled_pages_with_text"]
            ),
            "parser_library": full["parser_library"],
            "parser_version": full["parser_version"],
            "parser_error_rows": int(full["parser_errors"]),
            "hash_failure_rows": int(full["hash_failures"]),
            "missing_artifact_rows": int(full["missing_artifacts"]),
            "next_recommendation": full["next_recommendation"],
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "summary_source": relative(
                PDF_READINESS_REMAINDER_SUMMARY_PATH
            ),
            "caveats": [
                "Readiness records technical parseability only.",
                "Text-layer presence does not prove wage data exist.",
                "No OCR, full-text retention, wage extraction, or ingestion occurred.",
                "Pilot 1 and the remainder are collected but not durably merged.",
            ],
        }
    return {
        **metadata,
        "pdf_readiness_phase": "pilot1_collected_not_merged",
        "latest_pdf_readiness_pilot_id": pilot["pilot_id"],
        "pilot_rows_collected": int(pilot["ledger_rows"]),
        "pilot_terminal_rows": int(pilot["terminal_rows"]),
        "pilot_lane_rows": pilot["lane_rows"],
        "pdf_readiness_merge_status": "not_started",
        "source_review_rows_available": int(
            pilot["source_review_rows_available"]
        ),
        "retained_pdf_artifacts_available": int(
            pilot["retained_pdf_artifacts_available"]
        ),
        "readiness_status_counts": pilot["readiness_status_counts"],
        "text_layer_status_counts": pilot["text_layer_status_counts"],
        "technical_parseability_rating_counts": pilot[
            "technical_parseability_rating_counts"
        ],
        "recommended_next_action_counts": pilot[
            "recommended_next_action_counts"
        ],
        "page_count_summary": pilot["page_count_summary"],
        "sampled_pages_checked": int(pilot["sampled_pages_checked"]),
        "sampled_pages_with_text": int(
            pilot["sampled_pages_with_text"]
        ),
        "parser_library": pilot["parser_library"],
        "parser_version": pilot["parser_version"],
        "parser_error_rows": int(pilot["parser_error_rows"]),
        "hash_failure_rows": int(pilot["hash_failure_rows"]),
        "missing_artifact_rows": int(pilot["missing_artifact_rows"]),
        "next_recommendation": pilot["next_recommendation"],
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "summary_source": relative(PDF_READINESS_PILOT1_SUMMARY_PATH),
        "caveats": [
            "Readiness only samples already-retained local artifacts.",
            "The sample is diversity-weighted and is not a prevalence estimate.",
            "Text-layer presence does not prove wage data exist.",
            "No OCR, full-text retention, wage extraction, or ingestion occurred.",
            "Pilot outcomes are collected but not durably merged.",
        ],
    }


def build_text_table_detection_status_summary(
    *, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Build bounded local text/table-detection collection status."""

    if (
        not TEXT_TABLE_DETECTION_PILOT1_SUMMARY_PATH.exists()
        and not TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH.exists()
        and not TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH.exists()
    ):
        return {
            **metadata,
            "text_table_detection_phase": "not_started",
            "latest_text_table_detection_pilot_id": None,
            "pilot_rows_collected": 0,
            "text_table_detection_merge_status": "not_started",
            "parse_text_layer_later_rows_available": 1828,
            "ocr_later_rows": 296,
            "wage_table_signal_counts": {},
            "contract_period_signal_counts": {},
            "table_like_structure_signal_counts": {},
            "extraction_pilot_priority_counts": {},
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "caveats": [
                "Text/table detection has not started.",
                "No OCR, wage extraction, or ingestion has occurred.",
            ],
        }

    forbidden_fields = (
        "urls_opened",
        "network_calls",
        "downloads",
        "redownloads",
        "ocr_runs",
        "full_text_artifacts_written",
        "final_wage_values_extracted",
        "ingestion_actions",
        "codify_actions",
        "durable_text_table_merges",
    )
    if TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH.exists():
        durable = read_json(TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH)
        durable_rows = int(durable.get("full_parse_text_rows_merged", 0))
        durable_ledger_rows = len(
            read_csv(TEXT_TABLE_DETECTION_DURABLE_LEDGER_PATH)
        )
        authority_equality = durable.get(
            "exact_parse_text_authority_equality", {}
        )
        durable_failure_fields = (
            "hash_failures",
            "missing_artifacts",
            "parser_errors",
            "invalid_candidate_page_hints",
            "bounded_hint_overruns",
            "heuristic_mismatches",
            "urls_opened",
            "network_calls",
            "downloads",
            "redownloads",
            "ocr_runs",
            "full_text_artifacts_written",
            "final_wage_values_extracted",
            "ingestion_actions",
            "codify_actions",
            "scout_accounting_mutations",
            "routing_ledger_mutations",
            "metadata_triage_ledger_mutations",
            "source_review_ledger_mutations",
            "pdf_readiness_ledger_mutations",
        )
        if (
            durable.get("status")
            != "text_table_detection_full_parse_text_merged"
            or durable.get("text_table_detection_merge_id")
            != "TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-MERGE-2026-07-24"
            or durable.get("text_table_detection_stage")
            != "heuristic_text_table_detection_not_extracted"
            or durable_rows != int(
                durable.get("parse_text_layer_later_rows_available", 0)
            )
            or durable_rows != durable_ledger_rows
            or float(durable.get("parse_text_coverage_rate", 0)) != 1.0
            or int(durable.get("unique_text_table_detection_ids", 0))
            != durable_rows
            or int(durable.get("unique_pdf_readiness_ids", 0))
            != durable_rows
            or int(durable.get("unique_source_review_ids", 0))
            != durable_rows
            or int(durable.get("unique_candidate_queue_row_ids", 0))
            != durable_rows
            or any(
                int(durable.get(field, -1)) != 0
                for field in (
                    "duplicate_text_table_detection_ids",
                    "duplicate_pdf_readiness_ids",
                    "duplicate_source_review_ids",
                    "duplicate_candidate_queue_row_ids",
                    *durable_failure_fields,
                )
            )
            or int(durable.get("durable_text_table_merges", 0)) != 1
            or durable.get("detection_status_counts")
            != {"detection_checked": durable_rows}
            or durable.get("heuristic_version_counts")
            != {"bounded_keyword_numeric_structure_v1": durable_rows}
            or not all(
                authority_equality.get(field) is True
                for field in (
                    "pdf_readiness_id_set_equal",
                    "source_review_id_set_equal",
                    "candidate_queue_row_id_set_equal",
                )
            )
            or authority_equality.get("authority_field_mismatch_counts")
            != {}
        ):
            raise ValueError(
                "durable text/table detection summary fails merge gates"
            )
        return {
            **metadata,
            "text_table_detection_phase": "full_parse_text_merged",
            "latest_text_table_detection_round_id": durable["full_run_id"],
            "latest_text_table_detection_merge_id": durable[
                "text_table_detection_merge_id"
            ],
            "text_table_detection_merge_status": "merged",
            "full_parse_text_rows_merged": durable_rows,
            "parse_text_layer_later_rows_available": int(
                durable["parse_text_layer_later_rows_available"]
            ),
            "ocr_later_rows": int(durable["ocr_later_rows"]),
            "detection_status_counts": durable["detection_status_counts"],
            "wage_table_signal_counts": durable[
                "wage_table_signal_counts"
            ],
            "wage_table_signal_confidence_counts": durable[
                "wage_table_signal_confidence_counts"
            ],
            "contract_period_signal_counts": durable[
                "contract_period_signal_counts"
            ],
            "contract_period_confidence_counts": durable[
                "contract_period_confidence_counts"
            ],
            "table_like_structure_signal_counts": durable[
                "table_like_structure_signal_counts"
            ],
            "extraction_pilot_priority_counts": durable[
                "extraction_pilot_priority_counts"
            ],
            "recommended_next_action_counts": durable[
                "recommended_next_action_counts"
            ],
            "pages_scanned": int(durable["pages_scanned"]),
            "pages_with_text": int(durable["pages_with_text"]),
            "bounded_text_characters_inspected": int(
                durable["total_text_chars_scanned"]
            ),
            "candidate_wage_page_hints": int(
                durable["candidate_wage_page_hints"]
            ),
            "parser_library": next(
                iter(durable["parser_library_counts"]), ""
            ),
            "parser_version": next(
                iter(durable["parser_version_counts"]), ""
            ),
            "heuristic_version": next(
                iter(durable["heuristic_version_counts"]), ""
            ),
            "parser_error_rows": int(durable["parser_errors"]),
            "hash_failure_rows": int(durable["hash_failures"]),
            "missing_artifact_rows": int(durable["missing_artifacts"]),
            "durable_text_table_detection_ledger_latest": relative(
                TEXT_TABLE_DETECTION_DURABLE_LEDGER_PATH
            ),
            "next_recommendation": (
                "manual_calibration_subset_before_extraction"
            ),
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "summary_source": relative(
                TEXT_TABLE_DETECTION_DURABLE_SUMMARY_PATH
            ),
            "caveats": [
                "Table detection is deterministic, heuristic, and preliminary.",
                "Candidate wage pages are page hints, not wage observations.",
                "No final wage values were extracted.",
                "No OCR, ingestion, or codification occurred.",
                "Manual calibration is required before extraction.",
            ],
        }

    if TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH.exists():
        full_run = read_json(TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH)
        if (
            full_run.get("status")
            != "text_table_detection_full_parse_text_collected_not_merged"
            or full_run.get("round_id")
            != "TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24"
            or int(full_run.get("planned_rows", 0)) != 1828
            or int(full_run.get("ledger_rows", 0)) != 1828
            or int(full_run.get("terminal_rows", 0)) != 1828
            or full_run.get("lane_rows") != [457, 457, 457, 457]
            or full_run.get("lane_classification_counts")
            != {"completed_merge_eligible": 4}
            or full_run.get("detection_status_counts")
            != {"detection_checked": 1828}
            or full_run.get("heuristic_version")
            != "bounded_keyword_numeric_structure_v1"
            or int(full_run.get("heuristic_mismatches", -1)) != 0
            or int(full_run.get("hash_failures", -1)) != 0
            or int(full_run.get("missing_artifacts", -1)) != 0
            or int(full_run.get("parser_errors", -1)) != 0
            or int(full_run.get("candidate_page_errors", -1)) != 0
            or int(full_run.get("hint_overruns", -1)) != 0
            or int(full_run.get("full_text_artifacts_found", -1)) != 0
            or int(
                full_run.get("contract_hint_money_pattern_violations", -1)
            )
            != 0
            or any(
                int(full_run.get(field, -1)) != 0
                for field in forbidden_fields
            )
            or full_run.get("durable_text_table_merge_status")
            != "not_started"
            or full_run.get("merge_recommendation")
            != "merge_all_text_table_detection_lanes"
        ):
            raise ValueError(
                "full text/table detection summary fails collection gates"
            )

        return {
            **metadata,
            "text_table_detection_phase": (
                "full_parse_text_collected_not_merged"
            ),
            "latest_text_table_detection_round_id": full_run["round_id"],
            "full_parse_text_rows_collected": int(full_run["ledger_rows"]),
            "full_parse_text_terminal_rows": int(full_run["terminal_rows"]),
            "full_parse_text_lane_rows": full_run["lane_rows"],
            "full_parse_text_lane_input_sha256": full_run[
                "lane_input_sha256"
            ],
            "text_table_detection_merge_status": "not_started",
            "parse_text_layer_later_rows_available": int(
                full_run["parse_text_layer_later_rows_available"]
            ),
            "ocr_later_rows": int(full_run["ocr_later_rows"]),
            "detection_status_counts": full_run["detection_status_counts"],
            "wage_table_signal_counts": full_run[
                "wage_table_signal_counts"
            ],
            "wage_table_signal_confidence_counts": full_run[
                "wage_table_signal_confidence_counts"
            ],
            "contract_period_signal_counts": full_run[
                "contract_period_signal_counts"
            ],
            "contract_period_confidence_counts": full_run[
                "contract_period_confidence_counts"
            ],
            "table_like_structure_signal_counts": full_run[
                "table_like_structure_signal_counts"
            ],
            "extraction_pilot_priority_counts": full_run[
                "extraction_pilot_priority_counts"
            ],
            "recommended_next_action_counts": full_run[
                "recommended_next_action_counts"
            ],
            "pages_scanned": int(full_run["pages_scanned"]),
            "pages_with_text": int(full_run["pages_with_text"]),
            "bounded_text_characters_inspected": int(
                full_run["total_text_chars_scanned"]
            ),
            "candidate_wage_page_hints": int(
                full_run["candidate_wage_page_hints"]
            ),
            "parser_library": full_run["parser_library"],
            "parser_version": full_run["parser_version"],
            "heuristic_version": full_run["heuristic_version"],
            "parser_error_rows": int(full_run["parser_errors"]),
            "hash_failure_rows": int(full_run["hash_failures"]),
            "missing_artifact_rows": int(full_run["missing_artifacts"]),
            "next_recommendation": full_run["next_recommendation"],
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_extraction_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "summary_source": relative(
                TEXT_TABLE_DETECTION_FULL_RUN_SUMMARY_PATH
            ),
            "caveats": [
                "Table detection is deterministic, heuristic, and preliminary.",
                "Candidate wage pages are page hints, not wage observations.",
                "No final wage values were extracted.",
                "No OCR, ingestion, or codification occurred.",
                "Manual calibration is required before wage extraction.",
                "Full-run outcomes are collected but not durably merged.",
            ],
        }

    pilot = read_json(TEXT_TABLE_DETECTION_PILOT1_SUMMARY_PATH)
    if (
        pilot.get("status")
        != "text_table_detection_pilot1_collected_not_merged"
        or pilot.get("pilot_id")
        != "TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24"
        or int(pilot.get("planned_rows", 0)) != 150
        or int(pilot.get("ledger_rows", 0)) != 150
        or int(pilot.get("terminal_rows", 0)) != 150
        or pilot.get("lane_rows") != [50, 50, 50]
        or pilot.get("lane_classification_counts")
        != {"completed_merge_eligible": 3}
        or pilot.get("detection_status_counts")
        != {"detection_checked": 150}
        or int(pilot.get("hash_failures", -1)) != 0
        or int(pilot.get("missing_artifacts", -1)) != 0
        or int(pilot.get("parser_errors", -1)) != 0
        or int(pilot.get("candidate_page_errors", -1)) != 0
        or int(pilot.get("hint_overruns", -1)) != 0
        or int(pilot.get("full_text_artifacts_found", -1)) != 0
        or int(
            pilot.get("contract_hint_money_pattern_violations", -1)
        )
        != 0
        or any(int(pilot.get(field, -1)) != 0 for field in forbidden_fields)
        or pilot.get("durable_text_table_merge_status") != "not_started"
        or pilot.get("merge_recommendation")
        != "merge_all_text_table_detection_lanes"
    ):
        raise ValueError(
            "text/table detection Pilot 1 summary fails collection gates"
        )

    return {
        **metadata,
        "text_table_detection_phase": "pilot1_collected_not_merged",
        "latest_text_table_detection_pilot_id": pilot["pilot_id"],
        "pilot_rows_collected": int(pilot["ledger_rows"]),
        "pilot_terminal_rows": int(pilot["terminal_rows"]),
        "pilot_lane_rows": pilot["lane_rows"],
        "text_table_detection_merge_status": "not_started",
        "parse_text_layer_later_rows_available": int(
            pilot["parse_text_layer_later_rows_available"]
        ),
        "ocr_later_rows": int(pilot["ocr_later_rows"]),
        "detection_status_counts": pilot["detection_status_counts"],
        "wage_table_signal_counts": pilot["wage_table_signal_counts"],
        "wage_table_signal_confidence_counts": pilot[
            "wage_table_signal_confidence_counts"
        ],
        "contract_period_signal_counts": pilot[
            "contract_period_signal_counts"
        ],
        "contract_period_confidence_counts": pilot[
            "contract_period_confidence_counts"
        ],
        "table_like_structure_signal_counts": pilot[
            "table_like_structure_signal_counts"
        ],
        "extraction_pilot_priority_counts": pilot[
            "extraction_pilot_priority_counts"
        ],
        "recommended_next_action_counts": pilot[
            "recommended_next_action_counts"
        ],
        "pages_scanned": int(pilot["pages_scanned"]),
        "pages_with_text": int(pilot["pages_with_text"]),
        "candidate_wage_page_hints": int(
            pilot["candidate_wage_page_hints"]
        ),
        "parser_library": pilot["parser_library"],
        "parser_version": pilot["parser_version"],
        "parser_error_rows": int(pilot["parser_errors"]),
        "hash_failure_rows": int(pilot["hash_failures"]),
        "missing_artifact_rows": int(pilot["missing_artifacts"]),
        "next_recommendation": pilot["next_recommendation"],
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "summary_source": relative(
            TEXT_TABLE_DETECTION_PILOT1_SUMMARY_PATH
        ),
        "caveats": [
            "Table detection is deterministic, heuristic, and preliminary.",
            "Candidate wage pages are page hints, not wage observations.",
            "No final wage values were extracted.",
            "No OCR, ingestion, or codification occurred.",
            "Manual calibration is required before wage extraction.",
        ],
    }


def build_text_table_calibration_status_summary(
    *, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Build calibration packet/review status without extraction inference."""

    if TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_SUMMARY_PATH.exists():
        summary = read_json(
            TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_SUMMARY_PATH
        )
        review_rows = read_csv(
            TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_LEDGER_PATH
        )
        decision = read_json(
            TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_DECISION_PATH
        )
        forbidden_fields = (
            "urls_opened",
            "network_calls",
            "downloads_or_redownloads",
            "ocr_runs",
            "full_text_artifacts_written",
            "final_wage_values_extracted",
            "ingestion_actions",
            "codify_actions",
            "durable_ledger_mutations",
        )
        identity_fields = (
            "calibration_id",
            "text_table_detection_id",
            "pdf_readiness_id",
            "source_review_id",
            "candidate_queue_row_id",
        )
        decision_forbidden = decision.get(
            "forbidden_activity_counters", {}
        )
        if (
            summary.get("status")
            != "calibration_review_complete_assisted_local"
            or summary.get("review_id")
            != (
                "TEXT-TABLE-CALIBRATION-SUBSET1-"
                "REFINED-REVIEW2-2026-07-24"
            )
            or summary.get("review_method")
            != "codex_refined_visual_table_gate_v1"
            or summary.get("review_mode") != "refined_visual_gate_v1"
            or int(summary.get("rows", 0)) != 150
            or int(summary.get("reviewed_rows", 0)) != 150
            or len(review_rows) != 150
            or not summary.get("original_input_preserved")
            or any(
                int(summary.get(field, -1)) != 0
                for field in forbidden_fields
            )
            or any(
                int(decision_forbidden.get(field, -1)) != 0
                for field in forbidden_fields
            )
            or any(
                len(values) != len(set(values))
                or any(not value for value in values)
                for values in (
                    [row.get(field, "") for row in review_rows]
                    for field in identity_fields
                )
            )
            or any(
                row.get("reviewer") != "codex_refined_visual_gate_review"
                or row.get("refined_review_mode")
                != "refined_visual_gate_v1"
                for row in review_rows
            )
            or int(decision.get("reviewed_rows", 0)) != 150
            or decision.get("extraction_decision")
            != "continue_schema_refinement"
            or decision.get("five_hundred_doc_extraction_allowed")
            is not False
            or decision.get("smaller_extraction_pilot_allowed") is not False
            or float(
                decision.get(
                    "independent_visual_qa_primary_agreement_rate", -1
                )
            )
            != 0.555556
        ):
            raise ValueError(
                "refined text/table calibration REVIEW2 fails dashboard gates"
            )
        adjudication_prepared = (
            TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_MANIFEST_PATH.exists()
        )
        adjudication_manifest: dict[str, Any] = {}
        adjudication_rows: list[dict[str, str]] = []
        adjudication_render_rows: list[dict[str, str]] = []
        if adjudication_prepared:
            adjudication_manifest = read_json(
                TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_MANIFEST_PATH
            )
            adjudication_rows = read_csv(
                TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_BLINDED_INPUT_PATH
            )
            adjudication_render_rows = read_csv(
                TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_RENDER_MANIFEST_PATH
            )
            human_forbidden_fields = {
                "wage_table_signal",
                "extraction_gate_label",
                "wage_schedule_table_confirmed_label",
                "candidate_page_relationship_label",
                "recommended_extraction_action",
                "recommended_next_action",
                "reviewer",
                "review_id",
                "review_method",
            }
            per_case_render_counts = Counter(
                row["adjudication_case_id"]
                for row in adjudication_render_rows
            )
            if (
                adjudication_manifest.get("adjudication_prep_id")
                != (
                    "TEXT-TABLE-INDEPENDENT-ADJUDICATION-"
                    "PREP1-2026-07-24"
                )
                or adjudication_manifest.get("status")
                != "packet_generated_with_bounded_renders"
                or int(adjudication_manifest.get("cases_prepared", 0)) != 150
                or len(adjudication_rows) != 150
                or len(
                    {
                        row.get("adjudication_case_id", "")
                        for row in adjudication_rows
                    }
                )
                != 150
                or any(
                    not row.get(field)
                    for row in adjudication_rows
                    for field in (
                        "adjudication_case_id",
                        "calibration_id",
                        "source_review_id",
                        "pdf_readiness_id",
                        "candidate_queue_row_id",
                        "content_artifact_path",
                    )
                )
                or any(
                    row.get("human_review_status") != "not_reviewed"
                    for row in adjudication_rows
                )
                or (
                    adjudication_rows
                    and human_forbidden_fields
                    & set(adjudication_rows[0])
                )
                or adjudication_manifest.get(
                    "review2_labels_in_human_facing_files"
                )
                is not False
                or adjudication_manifest.get("full_text_saved") is not False
                or adjudication_manifest.get("full_tables_saved") is not False
                or adjudication_manifest.get("structured_wage_values_saved")
                is not False
                or int(adjudication_manifest.get("urls_opened", -1)) != 0
                or int(adjudication_manifest.get("network_calls", -1)) != 0
                or int(adjudication_manifest.get("ocr_runs", -1)) != 0
                or int(adjudication_manifest.get("wage_extraction_runs", -1))
                != 0
                or int(adjudication_manifest.get("ingestion_actions", -1))
                != 0
                or int(adjudication_manifest.get("codify_actions", -1)) != 0
                or int(
                    adjudication_manifest.get("render_manifest_rows", -1)
                )
                != len(adjudication_render_rows)
                or int(adjudication_manifest.get("render_failures", -1)) != 0
                or (
                    per_case_render_counts
                    and max(per_case_render_counts.values()) > 6
                )
            ):
                raise ValueError(
                    "independent adjudication packet fails dashboard gates"
                )
        gate2_completed = (
            TEXT_TABLE_AUTO_GABRIEL_GATE2_SUMMARY_PATH.exists()
            and TEXT_TABLE_AUTO_GABRIEL_GATE2_LEDGER_PATH.exists()
            and TEXT_TABLE_AUTO_GABRIEL_GATE2_DECISION_PATH.exists()
        )
        gate3_completed = (
            TEXT_TABLE_AUTO_GABRIEL_GATE3_SUMMARY_PATH.exists()
            and TEXT_TABLE_AUTO_GABRIEL_GATE3_LEDGER_PATH.exists()
            and TEXT_TABLE_AUTO_GABRIEL_GATE3_DECISION_PATH.exists()
        )
        auto_summary_path = (
            TEXT_TABLE_AUTO_GABRIEL_GATE3_SUMMARY_PATH
            if gate3_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE2_SUMMARY_PATH
            if gate2_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE1_SUMMARY_PATH
        )
        auto_ledger_path = (
            TEXT_TABLE_AUTO_GABRIEL_GATE3_LEDGER_PATH
            if gate3_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE2_LEDGER_PATH
            if gate2_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE1_LEDGER_PATH
        )
        auto_decision_path = (
            TEXT_TABLE_AUTO_GABRIEL_GATE3_DECISION_PATH
            if gate3_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE2_DECISION_PATH
            if gate2_completed
            else TEXT_TABLE_AUTO_GABRIEL_GATE1_DECISION_PATH
        )
        auto_gate_completed = (
            auto_summary_path.exists()
            and auto_ledger_path.exists()
            and auto_decision_path.exists()
        )
        auto_summary: dict[str, Any] = {}
        auto_decision: dict[str, Any] = {}
        auto_rows: list[dict[str, str]] = []
        if auto_gate_completed:
            auto_summary = read_json(auto_summary_path)
            auto_decision = read_json(auto_decision_path)
            auto_rows = read_csv(auto_ledger_path)
            gate_id = (
                "TEXT-TABLE-AUTO-GABRIEL-GATE3-"
                "COMPENSATION-EVIDENCE-2026-07-25"
                if gate3_completed
                else "TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25"
                if gate2_completed
                else (
                    "TEXT-TABLE-AUTO-GABRIEL-"
                    "ADJUDICATION-GATE1-2026-07-24"
                )
            )
            auto_identity_fields = (
                "gate3_compensation_id"
                if gate3_completed
                else "auto_adjudication_id",
                "adjudication_case_id",
                "calibration_id",
                "source_review_id",
                "pdf_readiness_id",
                "candidate_queue_row_id",
            )
            if gate3_completed and (
                auto_summary.get("gate_id") != gate_id
                or auto_summary.get("status")
                != "auto_gabriel_compensation_adjudication_completed"
                or auto_summary.get("mode") not in {"live", "live_resume"}
                or auto_summary.get("gate_mode")
                != "auto_gabriel_gate3_compensation_evidence"
                or int(auto_summary.get("cases", 0)) != 150
                or len(auto_rows) != 150
                or int(auto_summary.get("failed_cases", -1)) != 0
                or auto_summary.get("gabriel_schema_valid_counts")
                != {"true": 150}
                or auto_summary.get("image_evidence_used") is not True
                or auto_summary.get("full_text_saved") is not False
                or auto_summary.get("full_tables_saved") is not False
                or auto_summary.get("structured_wage_values_saved") is not False
                or auto_summary.get("final_qualitative_observations_saved")
                is not False
                or auto_summary.get("raw_prompts_saved") is not False
                or auto_summary.get("raw_responses_saved") is not False
                or int(auto_summary.get("urls_opened", -1)) != 0
                or int(auto_summary.get("hosted_search_calls", -1)) != 0
                or int(auto_summary.get("ocr_runs", -1)) != 0
                or int(auto_summary.get("wage_extraction_runs", -1)) != 0
                or int(auto_summary.get("qualitative_extraction_runs", -1))
                != 0
                or int(auto_summary.get("ingestion_actions", -1)) != 0
                or int(auto_summary.get("codify_actions", -1)) != 0
                or auto_decision.get("gate_id") != gate_id
                or auto_decision.get("gate_mode")
                != "auto_gabriel_gate3_compensation_evidence"
                or auto_decision.get("extraction_decision")
                != "500_doc_compensation_extraction_allowed"
                or auto_decision.get(
                    "five_hundred_doc_compensation_extraction_allowed"
                )
                is not True
                or auto_decision.get(
                    "smaller_compensation_extraction_pilot_allowed"
                )
                is not False
                or float(
                    auto_decision.get("gabriel_schema_valid_rate", -1)
                )
                != 1.0
                or any(
                    len(values) != len(set(values))
                    or any(not value for value in values)
                    for values in (
                        [row.get(field, "") for row in auto_rows]
                        for field in auto_identity_fields
                    )
                )
                or any(
                    row.get("gabriel_schema_valid") != "true"
                    or row.get("gabriel_status") != "success"
                    for row in auto_rows
                )
            ):
                raise ValueError(
                    "Gate 3 compensation adjudication fails dashboard gates"
                )
            elif not gate3_completed and (
                auto_summary.get("gate_id") != gate_id
                or auto_summary.get("status")
                != "auto_gabriel_adjudication_completed"
                or auto_summary.get("mode") != "live"
                or int(auto_summary.get("cases", 0)) != 150
                or len(auto_rows) != 150
                or int(auto_summary.get("failed_cases", -1)) != 0
                or auto_summary.get("gabriel_schema_valid_counts")
                != {"true": 150}
                or auto_summary.get("full_text_saved") is not False
                or auto_summary.get("full_tables_saved") is not False
                or auto_summary.get("structured_wage_values_saved")
                is not False
                or int(auto_summary.get("urls_opened", -1)) != 0
                or int(auto_summary.get("hosted_search_calls", -1)) != 0
                or int(auto_summary.get("ocr_runs", -1)) != 0
                or int(auto_summary.get("wage_extraction_runs", -1)) != 0
                or int(auto_summary.get("ingestion_actions", -1)) != 0
                or int(auto_summary.get("codify_actions", -1)) != 0
                or auto_decision.get("gate_id") != gate_id
                or (
                    gate2_completed
                    and auto_summary.get("gate_mode")
                    != "auto_gabriel_gate2_navigation_table_refine"
                )
                or (
                    gate2_completed
                    and auto_decision.get("gate_mode")
                    != "auto_gabriel_gate2_navigation_table_refine"
                )
                or auto_decision.get("extraction_decision")
                != "continue_schema_refinement"
                or auto_decision.get(
                    "five_hundred_doc_extraction_allowed"
                )
                is not False
                or auto_decision.get("smaller_extraction_pilot_allowed")
                is not False
                or float(
                    auto_decision.get("gabriel_schema_valid_rate", -1)
                )
                != 1.0
                or any(
                    len(values) != len(set(values))
                    or any(not value for value in values)
                    for values in (
                        [row.get(field, "") for row in auto_rows]
                        for field in auto_identity_fields
                    )
                )
                or any(
                    row.get("gabriel_schema_valid") != "true"
                    or row.get("gabriel_status") != "success"
                    for row in auto_rows
                )
            ):
                raise ValueError(
                    "automated GABRIEL adjudication gate fails dashboard gates"
                )
        gate2_summary = (
            read_json(TEXT_TABLE_AUTO_GABRIEL_GATE2_SUMMARY_PATH)
            if gate2_completed
            else {}
        )
        gate2_decision = (
            read_json(TEXT_TABLE_AUTO_GABRIEL_GATE2_DECISION_PATH)
            if gate2_completed
            else {}
        )
        extraction_completed = all(path.exists() for path in (
            COMPENSATION_EXTRACTION_500_SELECTION_PATH,
            COMPENSATION_EXTRACTION_500_PACKET_SUMMARY_PATH,
            COMPENSATION_EXTRACTION_500_DECISION_PATH,
            COMPENSATION_EXTRACTION_500_QUANT_PATH,
            COMPENSATION_EXTRACTION_500_QUAL_PATH,
            COMPENSATION_EXTRACTION_500_MIXED_PATH,
            COMPENSATION_EXTRACTION_500_NONBASE_PATH,
            COMPENSATION_EXTRACTION_500_REFERENCE_PATH,
        ))
        extraction_decision: dict[str, Any] = {}
        extraction_selection: list[dict[str, str]] = []
        extraction_quant: list[dict[str, str]] = []
        extraction_qual: list[dict[str, str]] = []
        extraction_mixed: list[dict[str, str]] = []
        extraction_nonbase: list[dict[str, str]] = []
        extraction_reference: list[dict[str, str]] = []
        targeted_qa_completed = all(path.exists() for path in (
            COMPENSATION_EXTRACTION_500_TARGETED_QA_DECISION_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_SUMMARY_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_QUANT_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_QUAL_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_MIXED_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_NONBASE_PATH,
            COMPENSATION_EXTRACTION_500_TARGETED_QA_REFERENCE_PATH,
        ))
        targeted_qa_decision: dict[str, Any] = {}
        targeted_qa_summary: dict[str, Any] = {}
        targeted_qa_quant: list[dict[str, str]] = []
        targeted_qa_qual: list[dict[str, str]] = []
        targeted_qa_mixed: list[dict[str, str]] = []
        targeted_qa_nonbase: list[dict[str, str]] = []
        targeted_qa_reference: list[dict[str, str]] = []
        scale_1000_attempted = all(path.exists() for path in (
            COMPENSATION_EXTRACTION_1000_SELECTION_PATH,
            COMPENSATION_EXTRACTION_1000_SELECTION_SUMMARY_PATH,
            COMPENSATION_EXTRACTION_1000_PACKET_SUMMARY_PATH,
            COMPENSATION_EXTRACTION_1000_PREFLIGHT_REPORT_PATH,
            COMPENSATION_EXTRACTION_1000_REQUEST_METADATA_PATH,
            COMPENSATION_EXTRACTION_1000_DECISION_PATH,
        ))
        scale_1000_decision: dict[str, Any] = {}
        scale_1000_selection_summary: dict[str, Any] = {}
        scale_1000_packet_summary: dict[str, Any] = {}
        if extraction_completed:
            extraction_decision = read_json(
                COMPENSATION_EXTRACTION_500_DECISION_PATH
            )
            packet_summary = read_json(
                COMPENSATION_EXTRACTION_500_PACKET_SUMMARY_PATH
            )
            extraction_selection = read_csv(
                COMPENSATION_EXTRACTION_500_SELECTION_PATH
            )
            extraction_quant = read_csv(COMPENSATION_EXTRACTION_500_QUANT_PATH)
            extraction_qual = read_csv(COMPENSATION_EXTRACTION_500_QUAL_PATH)
            extraction_mixed = read_csv(COMPENSATION_EXTRACTION_500_MIXED_PATH)
            extraction_nonbase = read_csv(
                COMPENSATION_EXTRACTION_500_NONBASE_PATH
            )
            extraction_reference = read_csv(
                COMPENSATION_EXTRACTION_500_REFERENCE_PATH
            )
            if (
                len(extraction_selection) != 500
                or len({row["document_identity_id"] for row in extraction_selection}) != 500
                or extraction_decision.get("task_id")
                != "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25"
                or extraction_decision.get("integrity_qa_pass") is not True
                or extraction_decision.get("packet_compliant") is not True
                or int(extraction_decision.get("result_count", 0)) != 500
                or extraction_decision.get("final_merge_allowed") is not False
                or extraction_decision.get("ingestion_allowed") is not False
                or int(packet_summary.get("case_count", 0)) != 500
                or int(packet_summary.get("max_pages_per_case", 99)) > 6
                or int(packet_summary.get("max_text_chars_per_page", 99999)) > 1500
                or int(packet_summary.get("max_text_chars_per_case", 99999)) > 6000
                or packet_summary.get("full_text_saved") is not False
                or packet_summary.get("full_tables_saved") is not False
                or packet_summary.get("raw_prompts_saved") is not False
                or packet_summary.get("raw_responses_saved") is not False
            ):
                raise ValueError(
                    "provisional 500-document compensation extraction fails dashboard gates"
                )
        if targeted_qa_completed:
            targeted_qa_decision = read_json(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_DECISION_PATH
            )
            targeted_qa_summary = read_json(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_SUMMARY_PATH
            )
            targeted_qa_quant = read_csv(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_QUANT_PATH
            )
            targeted_qa_qual = read_csv(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_QUAL_PATH
            )
            targeted_qa_mixed = read_csv(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_MIXED_PATH
            )
            targeted_qa_nonbase = read_csv(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_NONBASE_PATH
            )
            targeted_qa_reference = read_csv(
                COMPENSATION_EXTRACTION_500_TARGETED_QA_REFERENCE_PATH
            )
            active_counts = {
                "quantitative": sum(
                    row.get("active_in_corrected_lane") == "true"
                    for row in targeted_qa_quant
                ),
                "qualitative": sum(
                    row.get("active_in_corrected_lane") == "true"
                    for row in targeted_qa_qual
                ),
                "mixed": sum(
                    row.get("active_in_corrected_lane") == "true"
                    for row in targeted_qa_mixed
                ),
                "nonbase": sum(
                    row.get("active_in_corrected_lane") == "true"
                    for row in targeted_qa_nonbase
                ),
                "reference": sum(
                    row.get("active_in_corrected_lane") == "true"
                    for row in targeted_qa_reference
                ),
            }
            if (
                targeted_qa_decision.get("task_id")
                != "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-AND-DASHBOARD-PUSH-2026-07-25"
                or targeted_qa_decision.get("integrity_qa_pass") is not True
                or targeted_qa_decision.get("scale_qa_pass") is not True
                or targeted_qa_decision.get("scale_1000_allowed") is not True
                or targeted_qa_decision.get("decision")
                != "recommend_1000_document_extraction"
                or int(targeted_qa_decision.get("review_rows_processed", 0)) != 187
                or int(targeted_qa_decision.get("duplicate_observation_id_count", -1)) != 0
                or int(targeted_qa_decision.get("invalid_observation_page_count", -1)) != 0
                or float(targeted_qa_decision.get("unresolved_quantitative_conflict_rate", 1)) > 0.02
                or int(targeted_qa_decision.get("unresolved_base_non_base_contamination_count", -1)) != 0
                or targeted_qa_decision.get("matched_representation_intact") is not True
                or targeted_qa_decision.get("corrected_ledgers_provisional_and_separate") is not True
                or active_counts != {
                    "quantitative": int(targeted_qa_summary["corrected_quantitative_active_observation_count"]),
                    "qualitative": int(targeted_qa_summary["corrected_qualitative_active_observation_count"]),
                    "mixed": int(targeted_qa_summary["corrected_mixed_active_case_count"]),
                    "nonbase": int(targeted_qa_summary["corrected_non_base_wage_active_observation_count"]),
                    "reference": int(targeted_qa_summary["corrected_reference_exclusion_active_case_count"]),
                }
            ):
                raise ValueError(
                    "targeted compensation extraction QA fails dashboard gates"
                )
        if scale_1000_attempted:
            scale_1000_decision = read_json(
                COMPENSATION_EXTRACTION_1000_DECISION_PATH
            )
            scale_1000_selection_summary = read_json(
                COMPENSATION_EXTRACTION_1000_SELECTION_SUMMARY_PATH
            )
            scale_1000_packet_summary = read_json(
                COMPENSATION_EXTRACTION_1000_PACKET_SUMMARY_PATH
            )
            scale_1000_requests = read_csv(
                COMPENSATION_EXTRACTION_1000_REQUEST_METADATA_PATH
            )
            scale_1000_preflight_requests = [
                row for row in scale_1000_requests
                if row.get("request_phase", "").startswith("preflight_1000_")
            ]
            scale_1000_live_requests = [
                row for row in scale_1000_requests
                if row.get("request_phase") == "live_1000"
            ]
            scale_1000_live_valid_case_ids = {
                row.get("extraction_case_id", "")
                for row in scale_1000_live_requests
                if row.get("schema_valid") == "true"
            }
            if (
                scale_1000_decision.get("task_id")
                != "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-PREFLIGHT-REPAIR-AND-LIVE-500NEW-2026-07-25"
                or scale_1000_decision.get("decision")
                != "live_incomplete_schema_invalid"
                or scale_1000_decision.get("live_extraction_started") is not True
                or int(scale_1000_decision.get("selection_count", 0)) != 1000
                or int(scale_1000_decision.get("corrected_seed_case_count", 0)) != 500
                or int(scale_1000_decision.get("new_document_count", 0)) != 500
                or int(scale_1000_decision.get("preflight_case_count", 0)) != 6
                or int(scale_1000_decision.get("preflight_schema_valid_count", 0)) != 6
                or len(scale_1000_preflight_requests) != 6
                or sum(row.get("schema_valid") == "true" for row in scale_1000_preflight_requests) != 6
                or len(scale_1000_live_requests) != 551
                or len(scale_1000_live_valid_case_ids) != 499
                or int(scale_1000_decision.get("live_schema_valid_case_count", 0)) != 499
                or int(scale_1000_decision.get("live_unresolved_case_count", 0)) != 1
                or int(scale_1000_decision.get("seed_gabriel_calls", -1)) != 0
                or scale_1000_decision.get("cumulative_materialization_completed") is not False
                or int(scale_1000_selection_summary.get("selection_count", 0)) != 1000
                or int(scale_1000_packet_summary.get("case_count", 0)) != 1000
                or int(scale_1000_packet_summary.get("max_pages_per_case", 99)) > 6
                or int(scale_1000_packet_summary.get("max_text_chars_per_page", 99999)) > 1500
                or int(scale_1000_packet_summary.get("max_text_chars_per_case", 99999)) > 6000
                or any(
                    row.get(field) == "true"
                    for row in scale_1000_requests
                    for field in (
                        "raw_prompt_saved", "raw_response_saved",
                        "encoded_image_saved", "credential_value_saved",
                        "authorization_header_saved",
                    )
                )
            ):
                raise ValueError(
                    "provisional 1,000-document incomplete live run fails dashboard gates"
                )
        return {
            **metadata,
            "calibration_phase": (
                "compensation_extraction_1000_live_incomplete_499_of_500"
                if scale_1000_attempted
                else "compensation_extraction_500_targeted_qa_completed"
                if targeted_qa_completed
                else "compensation_extraction_500_provisional_completed"
                if extraction_completed
                else "auto_gabriel_gate3_compensation_completed"
                if gate3_completed
                else "auto_gabriel_gate2_completed"
                if gate2_completed
                else "auto_gabriel_gate1_completed"
                if auto_gate_completed
                else "independent_adjudication_packet_prepared"
                if adjudication_prepared
                else "refined_review2_completed"
            ),
            "latest_calibration_id": (
                "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
            ),
            "latest_calibration_review_id": decision["review_id"],
            "latest_adjudication_prep_id": (
                adjudication_manifest.get("adjudication_prep_id")
                if adjudication_prepared
                else None
            ),
            "latest_auto_adjudication_gate_id": (
                auto_decision.get("gate_id")
                if auto_gate_completed
                else None
            ),
            "latest_compensation_extraction_id": (
                "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
                if scale_1000_attempted
                else "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25"
                if extraction_completed else None
            ),
            "latest_compensation_extraction_qa_id": (
                "COMPENSATION-EVIDENCE-EXTRACTION-500DOC-TARGETED-QA-2026-07-25"
                if targeted_qa_completed else None
            ),
            "targeted_qa_review_rows_processed": (
                int(targeted_qa_decision.get("review_rows_processed", 0))
                if targeted_qa_completed else 0
            ),
            "targeted_qa_duplicate_observations_canonicalized": (
                int(targeted_qa_decision.get("duplicate_observations_canonicalized", 0))
                if targeted_qa_completed else 0
            ),
            "targeted_qa_conflict_resolution_counts": (
                targeted_qa_decision.get("conflict_resolution_counts", {})
                if targeted_qa_completed else {}
            ),
            "targeted_qa_unresolved_conflict_rate": (
                float(targeted_qa_decision.get("unresolved_quantitative_conflict_rate", 0))
                if targeted_qa_completed else None
            ),
            "targeted_qa_quantitative_reroutes": (
                int(targeted_qa_decision.get("quantitative_records_routed_to_non_base_wage", 0))
                if targeted_qa_completed else 0
            ),
            "compensation_extraction_case_count": (
                500 if extraction_completed else 0
            ),
            "compensation_extraction_schema_valid_rate": (
                1.0 if extraction_completed else None
            ),
            "compensation_extraction_disposition_counts": (
                extraction_decision.get("disposition_counts", {})
                if extraction_completed else {}
            ),
            "quantitative_observation_count": (
                int(targeted_qa_summary["corrected_quantitative_active_observation_count"])
                if targeted_qa_completed
                else len(extraction_quant) if extraction_completed else 0
            ),
            "qualitative_mechanism_observation_count": (
                int(targeted_qa_summary["corrected_qualitative_active_observation_count"])
                if targeted_qa_completed
                else len(extraction_qual) if extraction_completed else 0
            ),
            "mixed_case_count": (
                int(targeted_qa_summary["corrected_mixed_active_case_count"])
                if targeted_qa_completed
                else len(extraction_mixed) if extraction_completed else 0
            ),
            "non_base_wage_observation_count": (
                int(targeted_qa_summary["corrected_non_base_wage_active_observation_count"])
                if targeted_qa_completed
                else len(extraction_nonbase) if extraction_completed else 0
            ),
            "reference_exclusion_case_count": (
                len(extraction_reference) if extraction_completed else 0
            ),
            "compensation_extraction_qa_status": (
                targeted_qa_decision.get("qa_status")
                if targeted_qa_completed
                else extraction_decision.get("qa_status")
                if extraction_completed else None
            ),
            "compensation_extraction_conflict_groups": (
                int(extraction_decision.get("conflicting_quantitative_group_count", 0))
                if extraction_completed else 0
            ),
            "scale_1000_recommendation": (
                targeted_qa_decision.get("scale_1000_recommendation")
                if targeted_qa_completed
                else extraction_decision.get("scale_1000_recommendation")
                if extraction_completed else None
            ),
            "scale_1000_allowed": (
                False
                if scale_1000_attempted
                else bool(targeted_qa_decision.get("scale_1000_allowed", False))
                if targeted_qa_completed else False
            ),
            "compensation_extraction_1000_selection_count": (
                int(scale_1000_selection_summary.get("selection_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_corrected_seed_count": (
                int(scale_1000_selection_summary.get("corrected_500_seed_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_new_document_count": (
                int(scale_1000_selection_summary.get("new_document_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_preflight_schema_valid_rate": (
                float(scale_1000_decision.get("preflight_schema_valid_rate", 0))
                if scale_1000_attempted else None
            ),
            "compensation_extraction_1000_live_started": (
                bool(scale_1000_decision.get("live_extraction_started", False))
                if scale_1000_attempted else False
            ),
            "compensation_extraction_1000_live_attempt_count": (
                int(scale_1000_decision.get("live_case_attempt_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_live_schema_valid_case_count": (
                int(scale_1000_decision.get("live_schema_valid_case_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_live_schema_valid_rate": (
                float(scale_1000_decision.get(
                    "live_schema_valid_rate_against_frozen_new_cases", 0
                ))
                if scale_1000_attempted else None
            ),
            "compensation_extraction_1000_live_unresolved_case_count": (
                int(scale_1000_decision.get("live_unresolved_case_count", 0))
                if scale_1000_attempted else 0
            ),
            "compensation_extraction_1000_cumulative_materialized": (
                bool(scale_1000_decision.get(
                    "cumulative_materialization_completed", False
                ))
                if scale_1000_attempted else False
            ),
            "scale_beyond_1000_recommendation": (
                scale_1000_decision.get("scale_beyond_1000_recommendation")
                if scale_1000_attempted else None
            ),
            "prior_auto_adjudication_gate_id": (
                "TEXT-TABLE-AUTO-GABRIEL-GATE2-REFINEMENT-2026-07-25"
                if gate3_completed
                else "TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24"
                if gate2_completed
                else None
            ),
            "auto_adjudication_method": (
                auto_decision.get("method")
                if auto_gate_completed
                else None
            ),
            "auto_gate_case_count": (
                int(auto_summary.get("cases", 0))
                if auto_gate_completed
                else 0
            ),
            "gabriel_schema_valid_rate": (
                float(auto_decision.get("gabriel_schema_valid_rate", 0))
                if auto_gate_completed
                else None
            ),
            "auto_gate_label_counts": (
                auto_summary.get("auto_gate_label_counts", {})
                if auto_gate_completed and not gate3_completed
                else {}
            ),
            "auto_gate_confidence_counts": (
                auto_summary.get("auto_gate_confidence_counts", {})
                if auto_gate_completed and not gate3_completed
                else {}
            ),
            "gate2_schema_valid_rate": (
                float(gate2_decision.get("gabriel_schema_valid_rate", 0))
                if gate2_completed
                else None
            ),
            "gate2_auto_gate_label_counts": (
                gate2_summary.get("auto_gate_label_counts", {})
                if gate2_completed
                else {}
            ),
            "gate2_wrong_page_rate": (
                float(gate2_decision.get("wrong_page_rate", 0))
                if gate2_completed
                else None
            ),
            "gate2_likely_p1_ready_rate": (
                float(
                    gate2_decision.get("original_likely_p1_ready_rate", 0)
                )
                if gate2_completed
                else None
            ),
            "gate3_schema_valid_rate": (
                float(auto_decision.get("gabriel_schema_valid_rate", 0))
                if gate3_completed
                else None
            ),
            "gate3_compensation_evidence_category_counts": (
                auto_summary.get("compensation_evidence_category_counts", {})
                if gate3_completed
                else {}
            ),
            "gate3_quantitative_evidence_present_counts": (
                auto_summary.get("quantitative_evidence_present_counts", {})
                if gate3_completed
                else {}
            ),
            "gate3_qualitative_mechanism_evidence_present_counts": (
                auto_summary.get(
                    "qualitative_mechanism_evidence_present_counts", {}
                )
                if gate3_completed
                else {}
            ),
            "prior_refined_review_id": decision["review_id"],
            "prior_extraction_decision": decision["extraction_decision"],
            "independent_human_review_status": (
                "packet_prepared_not_reviewed"
                if adjudication_prepared
                else "not_prepared"
            ),
            "latest_refinement_id": (
                "TEXT-TABLE-DETECTION-REFINE1-"
                "VISUAL-TABLE-GATE-2026-07-24"
            ),
            "prior_calibration_review_id": (
                "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
            ),
            "prior_calibration_pass_status": "fail",
            "calibration_subset_rows": 150,
            "reviewed_rows": 150,
            "review_method": "codex_assisted_refined_visual_gate",
            "refined_label_counts": {
                "wage_language_present_label": summary[
                    "wage_language_present_label"
                ],
                "pay_numeric_language_present_label": summary[
                    "pay_numeric_language_present_label"
                ],
                "visual_table_structure_label": summary[
                    "visual_table_structure_label"
                ],
                "wage_schedule_table_confirmed_label": summary[
                    "wage_schedule_table_confirmed_label"
                ],
                "candidate_page_relationship_label": summary[
                    "candidate_page_relationship_label"
                ],
                "table_navigation_signal": summary[
                    "table_navigation_signal"
                ],
                "visual_confirmation_method": summary[
                    "visual_confirmation_method"
                ],
                "extraction_gate_label": summary[
                    "extraction_gate_label"
                ],
            },
            "calibration_status_counts": summary["calibration_status"],
            "extraction_complexity_label_counts": summary[
                "extraction_complexity_label"
            ],
            "recommended_extraction_action_counts": summary[
                "recommended_extraction_action"
            ],
            "visual_qa_rows": int(
                decision["independent_visual_qa_rows"]
            ),
            "visual_qa_agreement_rate": float(
                decision[
                    "independent_visual_qa_primary_agreement_rate"
                ]
            ),
            "visual_qa_exact_gate_agreement_rate": float(
                decision[
                    "independent_visual_qa_exact_gate_agreement_rate"
                ]
            ),
            "likely_signal_visual_confirmation_rate": float(
                decision["likely_signal_visually_confirmed_yes_rate"]
            ),
            "wrong_page_rate": (
                0.0
                if gate3_completed
                else float(auto_decision["wrong_page_rate"])
                if auto_gate_completed
                else float(decision["wrong_page_rate"])
            ),
            "extraction_decision": (
                scale_1000_decision.get("decision")
                if scale_1000_attempted
                else targeted_qa_decision.get("decision")
                if targeted_qa_completed
                else extraction_decision.get("decision")
                if extraction_completed
                else auto_decision["extraction_decision"]
                if auto_gate_completed
                else decision["extraction_decision"]
            ),
            "five_hundred_doc_extraction_allowed": False,
            "smaller_extraction_pilot_allowed": False,
            "five_hundred_doc_compensation_extraction_allowed": (
                bool(
                    auto_decision.get(
                        "five_hundred_doc_compensation_extraction_allowed",
                        False,
                    )
                )
                if gate3_completed
                else False
            ),
            "smaller_compensation_extraction_pilot_allowed": (
                bool(
                    auto_decision.get(
                        "smaller_compensation_extraction_pilot_allowed", False
                    )
                )
                if gate3_completed
                else False
            ),
            "next_recommendation": (
                scale_1000_decision.get("next_recommendation")
                if scale_1000_attempted
                else "targeted_conflict_and_non_base_wage_qa_before_1000"
                if extraction_completed
                else auto_decision["next_recommendation"]
                if auto_gate_completed
                else "independent_human_adjudication"
                if adjudication_prepared
                else decision["next_recommendation"]
            ),
            "manual_review_status": (
                "packet_prepared_not_reviewed"
                if adjudication_prepared
                else (
                    "assisted_refined_review_complete_"
                    "independent_human_review_needed"
                )
            ),
            "wage_extraction_status": (
                "provisional_1000_live_incomplete_499_of_500_no_cumulative"
                if scale_1000_attempted
                else "provisional_500_completed_qa_hold"
                if extraction_completed else "not_started"
            ),
            "qualitative_extraction_status": (
                "provisional_1000_live_incomplete_499_of_500_no_cumulative"
                if scale_1000_attempted
                else "provisional_500_completed_qa_hold"
                if extraction_completed else "not_started"
            ),
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "auto_gate_summary_source": (
                relative(auto_summary_path)
                if auto_gate_completed
                else None
            ),
            "auto_gate_ledger": (
                relative(auto_ledger_path)
                if auto_gate_completed
                else None
            ),
            "auto_gate_decision_source": (
                relative(auto_decision_path)
                if auto_gate_completed
                else None
            ),
            "summary_source": relative(
                TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_SUMMARY_PATH
            ),
            "reviewed_ledger": relative(
                TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_LEDGER_PATH
            ),
            "decision_source": relative(
                TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW2_DECISION_PATH
            ),
            "adjudication_packet_manifest": (
                relative(
                    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_MANIFEST_PATH
                )
                if adjudication_prepared
                else None
            ),
            "adjudication_blinded_input": (
                relative(
                    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_BLINDED_INPUT_PATH
                )
                if adjudication_prepared
                else None
            ),
            "adjudication_render_manifest": (
                relative(
                    TEXT_TABLE_INDEPENDENT_ADJUDICATION_PREP1_RENDER_MANIFEST_PATH
                )
                if adjudication_prepared
                else None
            ),
            "adjudication_cases_prepared": (
                int(adjudication_manifest.get("cases_prepared", 0))
                if adjudication_prepared
                else 0
            ),
            "adjudication_rendered_page_count": (
                int(adjudication_manifest.get("rendered_page_count", 0))
                if adjudication_prepared
                else 0
            ),
            "adjudication_rendered_bytes": (
                int(adjudication_manifest.get("rendered_bytes", 0))
                if adjudication_prepared
                else 0
            ),
            "caveats": (
                [
                    "The 1,000-document selection and bounded packets are frozen, but live extraction did not start because the representative preflight failed strict semantic schema.",
                    "The corrected 500-document targeted-QA ledgers remain the latest valid provisional extraction layer.",
                    "No 1,000-document observation, conflict, contamination, or QA metrics were computed.",
                    "No OCR, ingestion, codification, wage-gap calculation, or regression occurred.",
                    "GABRIEL evaluated six bounded new-case preflight packets only; the corrected seed was not resent.",
                ]
                if scale_1000_attempted
                else
                [
                    "The 500-document ledgers are provisional and are not a final analysis dataset.",
                    "Integrity QA passed, but targeted conflict and non-base-wage QA is required before scaling.",
                    "No OCR, ingestion, codification, wage-gap calculation, or regression occurred.",
                    "GABRIEL evaluated bounded local page packets only.",
                ]
                if extraction_completed
                else
                [
                    "Automated adjudication is calibration, not extraction.",
                    "No final wage values were extracted.",
                    "No final qualitative mechanism observations were extracted.",
                    "No OCR or ingestion occurred.",
                    "GABRIEL evaluated bounded page packets only.",
                ]
                if auto_gate_completed
                else [
                    "REVIEW2 did not authorize extraction.",
                    "The human adjudication packet is blinded to prior labels.",
                    "No wage extraction has started.",
                    "Neither the 500-document nor smaller extraction run is authorized.",
                    "No OCR, ingestion, or codification occurred.",
                ]
                if adjudication_prepared
                else [
                    "Refined review is calibration, not final wage extraction.",
                    "No wage values were extracted into a final dataset.",
                    "Independent rendered-page QA agreement was 55.56 percent, below the 80 percent gate.",
                    "The 500-document and smaller extraction runs are not authorized.",
                    "No OCR, ingestion, or codification occurred.",
                ]
            ),
        }

    if TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_SUMMARY_PATH.exists():
        summary = read_json(
            TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_SUMMARY_PATH
        )
        review_rows = read_csv(
            TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_LEDGER_PATH
        )
        forbidden_fields = (
            "urls_opened",
            "network_calls",
            "downloads_or_redownloads",
            "ocr_runs",
            "full_text_artifacts_written",
            "final_wage_values_extracted",
            "ingestion_actions",
            "codify_actions",
            "durable_ledger_mutations",
        )
        identity_fields = (
            "calibration_id",
            "text_table_detection_id",
            "pdf_readiness_id",
            "source_review_id",
            "candidate_queue_row_id",
        )
        if (
            summary.get("status")
            != "calibration_review_complete_assisted_local"
            or summary.get("review_id")
            != "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
            or summary.get("review_method")
            != "codex_assisted_local_adjudication"
            or int(summary.get("rows", 0)) != 150
            or int(summary.get("reviewed_rows", 0)) != 150
            or len(review_rows) != 150
            or summary.get("calibration_pass_status")
            not in {"pass", "caution", "fail"}
            or not summary.get("original_input_preserved")
            or any(
                int(summary.get(field, -1)) != 0
                for field in forbidden_fields
            )
            or any(
                len(values) != len(set(values))
                or any(not value for value in values)
                for values in (
                    [row.get(field, "") for row in review_rows]
                    for field in identity_fields
                )
            )
            or any(
                row.get("reviewer") != "codex_assisted_local_review"
                or row.get("calibration_status")
                not in {"reviewed", "needs_second_review"}
                for row in review_rows
            )
        ):
            raise ValueError(
                "text/table calibration review fails dashboard gates"
            )
        refinement_paths = (
            TEXT_TABLE_CALIBRATION_REFINE1_READINESS_PATH,
            TEXT_TABLE_CALIBRATION_REFINED_SCHEMA_PATH,
            TEXT_TABLE_CALIBRATION_REFINED_RUBRIC_PATH,
            TEXT_TABLE_CALIBRATION_REFINED_REVIEW_PROMPT_PATH,
        )
        refinement_prepared = all(path.exists() for path in refinement_paths)
        if refinement_prepared and (
            summary.get("calibration_pass_status") != "fail"
            or int(
                summary.get("visual_qa", {}).get(
                    "challenge_rows_with_material_disagreement", -1
                )
            )
            != 5
            or int(
                summary.get("visual_qa", {}).get(
                    "challenge_rows_checked", -1
                )
            )
            != 5
        ):
            raise ValueError(
                "refinement status requires the recorded failed gate and "
                "five-of-five visual challenge disagreement"
            )
        return {
            **metadata,
            "calibration_phase": (
                "refinement_prepared_after_failed_review"
                if refinement_prepared
                else "subset1_reviewed"
            ),
            "latest_calibration_id": (
                "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
            ),
            "latest_calibration_review_id": summary["review_id"],
            "latest_refinement_id": (
                "TEXT-TABLE-DETECTION-REFINE1-VISUAL-TABLE-GATE-2026-07-24"
                if refinement_prepared
                else None
            ),
            "prior_calibration_review_id": summary["review_id"],
            "prior_calibration_pass_status": summary[
                "calibration_pass_status"
            ],
            "calibration_subset_rows": int(summary["rows"]),
            "reviewed_rows": int(summary["reviewed_rows"]),
            "review_method": summary["review_method"],
            "calibration_status_counts": summary["calibration_status"],
            "wage_table_present_label_counts": summary[
                "wage_table_present_label"
            ],
            "page_hint_precision_label_counts": summary[
                "page_hint_precision_label"
            ],
            "contract_period_present_label_counts": summary[
                "contract_period_present_label"
            ],
            "contract_period_hint_match_label_counts": summary[
                "contract_period_hint_match_label"
            ],
            "extraction_complexity_label_counts": summary[
                "extraction_complexity_label"
            ],
            "recommended_extraction_action_counts": summary[
                "recommended_extraction_action"
            ],
            "reviewer_confidence_counts": summary["reviewer_confidence"],
            "calibration_pass_status": summary[
                "calibration_pass_status"
            ],
            "next_recommendation": (
                "refined_re_review_before_extraction"
                if refinement_prepared
                else summary["next_recommendation"]
            ),
            "manual_review_status": (
                "refined_re_review_not_started"
                if refinement_prepared
                else "assisted_review_complete"
            ),
            "wage_extraction_status": "not_started",
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "summary_source": relative(
                TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_SUMMARY_PATH
            ),
            "reviewed_ledger": relative(
                TEXT_TABLE_CALIBRATION_SUBSET1_REVIEW_LEDGER_PATH
            ),
            "refined_schema": (
                relative(TEXT_TABLE_CALIBRATION_REFINED_SCHEMA_PATH)
                if refinement_prepared
                else None
            ),
            "refined_review_rubric": (
                relative(TEXT_TABLE_CALIBRATION_REFINED_RUBRIC_PATH)
                if refinement_prepared
                else None
            ),
            "caveats": [
                (
                    "The prior assisted review failed the extraction gate."
                    if refinement_prepared
                    else "Calibration used deterministic Codex-assisted "
                    "local adjudication, not independent human ground truth."
                ),
                (
                    "Visual/table confirmation refinement is prepared; "
                    "the refined re-review has not run."
                    if refinement_prepared
                    else "Candidate-page concordance is not a final "
                    "precision estimate."
                ),
                "A five-row rendered-page challenge materially disagreed with all five assisted outcomes.",
                (
                    "No wage extraction is authorized."
                    if refinement_prepared
                    else "Detector/review-schema refinement and independent "
                    "calibration are required before extraction."
                ),
                "No final wage values were extracted.",
                "No OCR, ingestion, or codification occurred.",
            ],
        }

    if not TEXT_TABLE_CALIBRATION_SUBSET1_SUMMARY_PATH.exists():
        return {
            **metadata,
            "calibration_phase": "not_started",
            "latest_calibration_id": None,
            "calibration_subset_rows": 0,
            "manual_review_status": "not_started",
            "wage_extraction_status": "not_started",
            "ingestion_status": "not_started",
            "codify_status": "not_started",
            "wage_gap_analysis_status": "not_started",
            "caveats": [
                "No manual calibration packet has been prepared.",
                "No wage values, OCR, or ingestion outputs exist.",
            ],
        }

    summary = read_json(TEXT_TABLE_CALIBRATION_SUBSET1_SUMMARY_PATH)
    review_rows = read_csv(TEXT_TABLE_CALIBRATION_SUBSET1_INPUT_PATH)
    forbidden_fields = (
        "pdfs_opened",
        "urls_opened",
        "network_calls",
        "additional_text_extractions",
        "ocr_runs",
        "full_text_artifacts_written",
        "final_wage_values_extracted",
        "ingestion_actions",
        "codify_actions",
        "durable_ledger_mutations",
    )
    calibration_ids = [row.get("calibration_id", "") for row in review_rows]
    identity_fields = (
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    )
    if (
        summary.get("status")
        != "text_table_calibration_subset1_prepared_not_reviewed"
        or summary.get("calibration_id")
        != "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
        or int(summary.get("calibration_subset_rows", 0)) != 150
        or len(review_rows) != 150
        or summary.get("wage_table_signal_counts")
        != {"likely": 80, "possible": 58, "unlikely": 12}
        or summary.get("manual_review_status") != "not_started"
        or int(
            summary.get("manual_fields_initialized_not_reviewed", 0)
        )
        != 150
        or any(int(summary.get(field, -1)) != 0 for field in forbidden_fields)
        or len(calibration_ids) != len(set(calibration_ids))
        or any(not value for value in calibration_ids)
        or any(
            len(values) != len(set(values)) or any(not value for value in values)
            for values in (
                [row.get(field, "") for row in review_rows]
                for field in identity_fields
            )
        )
        or any(
            row.get("calibration_status") != "not_reviewed"
            or row.get("reviewer")
            or row.get("reviewed_at")
            for row in review_rows
        )
    ):
        raise ValueError(
            "text/table calibration subset fails preparation gates"
        )
    return {
        **metadata,
        "calibration_phase": "subset1_prepared_not_reviewed",
        "latest_calibration_id": summary["calibration_id"],
        "calibration_subset_rows": int(
            summary["calibration_subset_rows"]
        ),
        "wage_table_signal_counts": summary[
            "wage_table_signal_counts"
        ],
        "extraction_pilot_priority_counts": summary[
            "extraction_pilot_priority_counts"
        ],
        "unit_type_counts": summary["unit_type_counts"],
        "candidate_source_type_counts": summary[
            "candidate_source_type_counts"
        ],
        "source_officialness_rating_counts": summary[
            "source_officialness_rating_counts"
        ],
        "source_review_batch_counts": summary[
            "source_review_batch_counts"
        ],
        "page_count_bin_counts": summary["page_count_bin_counts"],
        "unique_states": int(summary["unique_states"]),
        "unique_municipalities": int(summary["unique_municipalities"]),
        "candidate_wage_page_hints": int(
            summary["candidate_wage_page_hints"]
        ),
        "manual_review_status": "not_started",
        "wage_extraction_status": "not_started",
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "summary_source": relative(
            TEXT_TABLE_CALIBRATION_SUBSET1_SUMMARY_PATH
        ),
        "review_input": relative(
            TEXT_TABLE_CALIBRATION_SUBSET1_INPUT_PATH
        ),
        "caveats": [
            "The calibration subset has not been manually reviewed.",
            "Candidate pages remain heuristic hints, not wage observations.",
            "No wage values were extracted.",
            "No OCR, ingestion, or codification occurred.",
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
    pdf_readiness_status_summary = build_pdf_readiness_status_summary(
        metadata=metadata
    )
    text_table_detection_status_summary = (
        build_text_table_detection_status_summary(metadata=metadata)
    )
    text_table_calibration_status_summary = (
        build_text_table_calibration_status_summary(metadata=metadata)
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
        write_json(
            "pdf_readiness_status_summary.json",
            pdf_readiness_status_summary,
        ),
        write_json(
            "text_table_detection_status_summary.json",
            text_table_detection_status_summary,
        ),
        write_json(
            "text_table_calibration_status_summary.json",
            text_table_calibration_status_summary,
        ),
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
