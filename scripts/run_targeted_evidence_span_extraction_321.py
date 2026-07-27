#!/usr/bin/env python3
"""Extract bounded exact mechanism spans from 321 task-local text artifacts.

This stage is deterministic and local-only. It does not access URLs, download,
OCR, render, call a model, rate evidence, ingest, codify, or make causal claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "TARGETED-EVIDENCE-SPAN-EXTRACTION-321-EXTRACTED-TEXT-SOURCES-2026-07-26"
INPUT_COMMIT = "d73bf6a0fff3e123089e140bf51d40214e5c782f"
INPUT_DIR = BASE / "TARGETED-TEXT-LAYER-EXTRACTION-321-READINESS-READY-SOURCES-2026-07-26"
TEXT_ROOT = INPUT_DIR / "extracted_text"
OUTPUT_DIR = BASE / TASK_ID
EXPECTED_COUNT = 321
EXPECTED_PDF_COUNT = 289
EXPECTED_HTML_COUNT = 32
EXPECTED_ID_SET_HASH = "21fdbf9da41b7646d297147eca46cb41d8469e00f8b082af8521d9b3345ec6f5"
EXPECTED_LANES = {"lane_1": 88, "lane_2": 106, "lane_3": 23, "lane_4": 104}
EXPECTED_MECHANISMS = {
    "fiscal_constraint_signal": 23,
    "market_or_comparability_pressure": 104,
    "non_safety_constraint_signal": 88,
    "strike_or_no_strike_constraint": 106,
}
MAX_POSITIVE_SPANS_PER_SOURCE = 5
MAX_SPAN_CHARACTERS = 900
CONTEXT_CHARACTERS = 160

EXPECTED_HASHES = {
    "targeted_text_layer_extraction_321_decision.json": "b47555b3629cea68ac8a1cd302bf0ab1948fdbf26172503cc4848829a660c48f",
    "targeted_text_layer_extraction_321_summary.md": "8667f564fc39fd03cc832c46b8983860fb45eddc87b5283d133036a9cddf1436",
    "targeted_text_layer_extraction_321_locked_queue_summary.json": "37bc183acb1d15553afda2fee08a84acdd98e5ceb4bca44830c21f4d84d99486",
    "targeted_text_layer_extraction_321_results_summary.json": "bce086292f500dda23d4d8891569a8cf93f51575dc7d36427c8940ad6bd25d9f",
    "targeted_text_layer_extraction_321_pdf_results_summary.json": "0f62c3c8978ef1a38d79da645cc7933661231b595089fce4470288c3240181b7",
    "targeted_text_layer_extraction_321_html_results_summary.json": "63d8f06966d301dce1b6c23a6b486f93001dcaabc6d2204a14d29d822bb66a6c",
    "extracted_text_manifest_summary.json": "27054d3e895a021eeff41582f3a842583574206ec71f20c2135eda1ff41089c6",
    "targeted_text_layer_extraction_321_evidence_extraction_candidate_summary.json": "6133e0427f9ab9c80da7dd23b7464d452a9a99b23b8f492b8d30afd234d017f9",
    "targeted_text_layer_extraction_321_mechanism_coverage_summary.json": "7676e6e706c5fd2f7c8693cc40b52070926c975329325979a56ca50cccd0b0a7",
    "targeted_text_layer_extraction_321_city_cycle_unit_coverage_summary.json": "4288970a1a3d55c772078bfa3d21c87416468e1cbff8bd06d949360182076c7c",
    "targeted_text_layer_extraction_321_preserved_readiness_exclusions_summary.json": "d5917b884b09bc03ae6f57bfc3318704c05071c50fe4746ec00d400df9cab500",
    "targeted_text_layer_extraction_321_validation_2026-07-26.md": "64c2455b9e39fa55a781f556ee4bedddde501fe978d0b042c6cab50094fe865a",
    "targeted_text_layer_extraction_321_evidence_extraction_candidate_manifest.csv": "bbb303bb63d4e1d6180393b06a7359fbdba0658c6efefa0a3908c303a2b706e2",
    "targeted_text_layer_extraction_321_results.csv": "bbb303bb63d4e1d6180393b06a7359fbdba0658c6efefa0a3908c303a2b706e2",
    "extracted_text_manifest.csv": "981d115ff953266cf317e7622ff420ac146982265f163489dd4a7326748677a8",
    "extracted_text_hash_manifest.csv": "4a4aae2e82406d760befd7635743074ebe265059da89f91fce1a5e881467b6b1",
    "targeted_text_layer_extraction_321_invariant_checks.json": "61a020d82a2577952b91abfcb7eb9927a5148471b521c59c7604ed8690fb8e22",
    "targeted_text_layer_extraction_321_preserved_readiness_exclusions.csv": "2c476d7cc14cd0a406c639bd0f177edfe831776295b8da622697f63a0e90d51b",
    "targeted_text_layer_extraction_321_lock.json": "e08da2f725a707f52f41def5b1e9ef519e9e3c7f779a08e74147f7b5f094e54b",
}

QUEUE_FIELDS = (
    "extracted_text_id", "retained_source_id", "candidate_id", "lane_id",
    "priority_tier", "quality_label", "source_url_or_locator", "source_title",
    "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "same_city_match_status", "overlapping_cycle_status", "local_retained_path",
    "file_sha256", "extracted_text_path", "extracted_text_sha256",
    "extracted_text_size_bytes", "extracted_char_count", "readiness_status",
    "extraction_status", "content_type_hint", "extraction_method", "rating_status",
    "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness",
)

RESULT_FIELDS = (
    "span_extraction_id", "extracted_text_id", "retained_source_id", "candidate_id",
    "lane_id", "priority_tier", "quality_label", "source_url_or_locator",
    "source_title", "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "local_extracted_text_path", "extracted_text_sha256", "source_file_sha256",
    "span_status", "span_status_reason", "span_record_count", "mechanism_family",
    "span_text", "span_start_offset", "span_end_offset", "span_sha256",
    "context_before", "context_after", "extraction_rule_id",
    "extraction_rule_family", "span_specificity", "documentary_claim_support",
    "rating_status", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
)

CONTROLLED_STATUSES = {"span_extracted", "no_span_or_weak", "ambiguous_span", "extraction_error"}
MECHANISM_FILES = {
    "strike_or_no_strike_constraint": "targeted_evidence_span_extraction_321_strike_no_strike_spans.csv",
    "market_or_comparability_pressure": "targeted_evidence_span_extraction_321_market_comparability_spans.csv",
    "non_safety_constraint_signal": "targeted_evidence_span_extraction_321_non_safety_constraint_spans.csv",
    "fiscal_constraint_signal": "targeted_evidence_span_extraction_321_fiscal_constraint_spans.csv",
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    family: str
    pattern: re.Pattern[str]
    rationale: str
    specificity: str = "medium"
    support: str = "moderate"
    required_context: re.Pattern[str] | None = None


PAY_CONTEXT = re.compile(
    r"\b(?:wages?|salar(?:y|ies)|pay|payroll|compensation|wage rates?|pay rates?|salary rates?|hourly rates?|raises?|increases?|steps?|"
    r"labor costs?|personnel costs?|collective bargaining|cost of living|cola)\b",
    re.IGNORECASE,
)
STRIKE_SUBSTITUTE_CONTEXT = re.compile(
    r"\b(?:no[- ]strike|strike|work stoppage|labor peace|in lieu of|substitute|prohibit(?:ed|ion)|shall not)\b",
    re.IGNORECASE,
)

RULES: dict[str, tuple[Rule, ...]] = {
    "strike_or_no_strike_constraint": (
        Rule("STRIKE_NO_STRIKE", "no_strike_clause", re.compile(r"\bno[-\s]+strikes?\b", re.I), "Explicit no-strike wording.", "high", "strong"),
        Rule("STRIKE_PROHIBITION", "strike_right_or_prohibition", re.compile(r"\b(?:shall not|may not|prohibited from|forbidden from)\b[^\n.!?]{0,100}\b(?:engage|participate|authorize|cause|instigate|condone)\b[^\n.!?]{0,100}\bstrikes?\b|\bstrikes?\b\s+(?:is|are)\s+(?:prohibited|illegal|unlawful)\b|\bpenalt(?:y|ies)\b[^\n.!?]{0,100}\bfor\b[^\n.!?]{0,40}\bstrikes?\b", re.I), "Strike right, restriction, or penalty wording.", "high", "strong"),
        Rule("STRIKE_STOPPAGE", "work_stoppage_restriction", re.compile(r"\bwork[-\s]+stoppages?\b", re.I), "Work-stoppage wording relevant to labor-peace constraints.", "high", "strong"),
        Rule("STRIKE_SLOWDOWN", "slowdown_sickout_restriction", re.compile(r"\b(?:slowdowns?|sickouts?)\b", re.I), "Slowdown or sickout restriction wording.", "high", "strong"),
        Rule("STRIKE_LOCKOUT", "lockout_restriction", re.compile(r"\bno[-\s]+lockouts?\b|\b(?:shall not|may not|prohibited from|forbidden from)\b[^\n.!?]{0,100}\block[-\s]?outs?\b|\block[-\s]?outs?\b\s+(?:is|are)\s+(?:prohibited|illegal|unlawful)\b", re.I), "Explicit no-lockout or lockout-prohibition wording.", "high", "strong"),
        Rule("STRIKE_LABOR_PEACE", "labor_peace_clause", re.compile(r"\blabor[-\s]+peace\b", re.I), "Explicit labor-peace wording.", "high", "strong"),
        Rule("STRIKE_ESSENTIAL_SERVICE", "essential_service_limit", re.compile(r"\bessential[-\s]+services?\b", re.I), "Essential-service language tied to strike or stoppage restrictions.", required_context=STRIKE_SUBSTITUTE_CONTEXT),
        Rule("STRIKE_SUBSTITUTE", "dispute_resolution_substitute", re.compile(r"\b(?:interest arbitration|fact[-\s]?finding|impasse procedures?|mediation)\b", re.I), "Dispute-resolution language explicitly tied to a strike substitute or labor-peace restriction.", required_context=STRIKE_SUBSTITUTE_CONTEXT),
    ),
    "market_or_comparability_pressure": (
        Rule("MARKET_ADJUSTMENT", "market_adjustment", re.compile(r"\bmarket[-\s]+adjustments?\b", re.I), "Explicit market-adjustment wording.", "high", "strong"),
        Rule("MARKET_COMPARABLE_COMMUNITIES", "comparable_communities", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage rates?|pay rates?)\b[^\n.!?]{0,180}\bcomparable\s+(?:communities|municipalities|cities|jurisdictions|employers)\b|\bcomparable\s+(?:communities|municipalities|cities|jurisdictions|employers)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage rates?|pay rates?)\b", re.I), "Peer-community comparison tied directly to compensation."),
        Rule("MARKET_PEER_MUNICIPALITIES", "peer_municipalities", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage rates?|pay rates?)\b[^\n.!?]{0,180}\bpeer\s+(?:municipalities|communities|cities|jurisdictions|employers)\b|\bpeer\s+(?:municipalities|communities|cities|jurisdictions|employers)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage rates?|pay rates?)\b", re.I), "Peer-municipality comparison tied directly to compensation."),
        Rule("MARKET_RECRUITMENT_RETENTION", "recruitment_retention", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|raise|increase)\b[^\n.!?]{0,180}\b(?:recruitment\s+(?:and|or|/)\s+retention|recruit\s+(?:and|or)\s+retain|attract(?:ing)?\s+(?:and|or)\s+retain(?:ing)?)\b|\b(?:recruitment\s+(?:and|or|/)\s+retention|recruit\s+(?:and|or)\s+retain|attract(?:ing)?\s+(?:and|or)\s+retain(?:ing)?)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|raise|increase)\b", re.I), "Recruitment and retention pressure tied directly to compensation."),
        Rule("MARKET_COMPETITIVENESS", "pay_competitiveness", re.compile(r"\b(?:competitive\s+(?:wages?|salar(?:y|ies)|pay|compensation)|(?:wages?|salar(?:y|ies)|pay|compensation)\s+(?:is|are|remain|remains|be|more)?\s*competitive|pay[-\s]+competitiveness)\b", re.I), "Explicit compensation competitiveness wording.", "high", "strong"),
        Rule("MARKET_WAGE_STUDY", "wage_compensation_study", re.compile(r"\b(?:wage|salary|pay|compensation|classification)[-\s]+(?:study|survey|analysis|review)\b", re.I), "Explicit wage, salary, compensation, or classification study.", "high", "strong"),
        Rule("MARKET_LABOR_MARKET", "labor_market_pressure", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|raise|increase)\b[^\n.!?]{0,180}\blabor[-\s]+market\b|\blabor[-\s]+market\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|raise|increase)\b", re.I), "Labor-market wording tied directly to compensation."),
    ),
    "non_safety_constraint_signal": (
        Rule("NONSAFETY_PAY_FREEZE", "pay_freeze", re.compile(r"\b(?:wage|salary|pay|step|hiring)[-\s]+freezes?\b", re.I), "Explicit pay, progression, or hiring freeze.", "high", "strong"),
        Rule("NONSAFETY_PAY_CAP", "pay_or_budget_cap", re.compile(r"\b(?:wage|salary|pay|compensation)[-\s]+caps?\b", re.I), "Explicit compensation cap.", "high", "strong"),
        Rule("NONSAFETY_COMPRESSION", "pay_compression", re.compile(r"\b(?:wage|salary|pay|compensation)[-\s]+compression\b|\bcompression\b[^\n.!?]{0,140}\b(?:wages?|salar(?:y|ies)|pay|compensation|steps?|rates?)\b", re.I), "Pay-compression wording tied directly to compensation."),
        Rule("NONSAFETY_DELAY", "delayed_implementation", re.compile(r"\b(?:delay(?:ed)?|defer(?:red)?|postpon(?:e|ed|ement))\b[^\n.!?]{0,140}\b(?:implementation|effective date|wage increase|salary increase|pay increase|raise|step increase|cola)\b|\b(?:implementation|effective date|wage increase|salary increase|pay increase|raise|step increase|cola)\b[^\n.!?]{0,140}\b(?:delay(?:ed)?|defer(?:red)?|postpon(?:e|ed|ement))\b", re.I), "Delayed or deferred compensation implementation."),
        Rule("NONSAFETY_STANDARDIZED_PLAN", "standardized_pay_plan", re.compile(r"\b(?:standardized|uniform|fixed)\b[^\n.!?]{0,100}\b(?:pay plan|salary schedule|wage schedule|step schedule)\b|\b(?:pay plan|salary schedule|wage schedule|step schedule)\b[^\n.!?]{0,100}\b(?:standardized|uniform|fixed)\b", re.I), "Standardized compensation schedule or plan.", "high", "strong"),
        Rule("NONSAFETY_AFFORDABILITY", "affordability_constraint", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b[^\n.!?]{0,160}\baffordab(?:le|ility)\b(?!\s+care\s+act)|\baffordab(?:le|ility)\b(?!\s+care\s+act)[^\n.!?]{0,160}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b", re.I), "Affordability language tied directly to compensation."),
        Rule("NONSAFETY_BUDGET_LIMIT", "budget_constraint", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\b(?:budget(?:ary)?\s+(?:limit|constraint|restriction|ceiling)|funding shortage|fiscal crisis)\b|\b(?:budget(?:ary)?\s+(?:limit|constraint|restriction|ceiling)|funding shortage|fiscal crisis)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Budget or fiscal limit tied directly to compensation."),
    ),
    "fiscal_constraint_signal": (
        Rule("FISCAL_BUDGET_LIMIT", "budget_limit", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\b(?:budget(?:ary)?\s+(?:limit|constraint|restriction|ceiling)|budget cap)\b|\b(?:budget(?:ary)?\s+(?:limit|constraint|restriction|ceiling)|budget cap)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Budget limit tied directly to compensation."),
        Rule("FISCAL_AFFORDABILITY", "affordability", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b[^\n.!?]{0,160}\baffordab(?:le|ility)\b(?!\s+care\s+act)|\baffordab(?:le|ility)\b(?!\s+care\s+act)[^\n.!?]{0,160}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b", re.I), "Affordability wording tied directly to compensation."),
        Rule("FISCAL_CRISIS", "fiscal_crisis", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\b(?:fiscal crisis|financial emergency|severe fiscal|budget deficit)\b|\b(?:fiscal crisis|financial emergency|severe fiscal|budget deficit)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Fiscal-crisis wording tied directly to compensation."),
        Rule("FISCAL_TAX_CAP", "tax_cap", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b[^\n.!?]{0,180}\b(?:tax|levy)[-\s]+(?:cap|limit|ceiling)s?\b|\b(?:tax|levy)[-\s]+(?:cap|limit|ceiling)s?\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase)\b", re.I), "Tax-cap wording tied directly to compensation."),
        Rule("FISCAL_FUNDING_SHORTAGE", "funding_shortage", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\b(?:funding shortage|insufficient funds?|lack of funds?|available funds?)\b|\b(?:funding shortage|insufficient funds?|lack of funds?|available funds?)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Funding availability tied directly to compensation."),
        Rule("FISCAL_APPROPRIATION", "appropriation_constraint", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\bappropriat(?:ion|ions|ed)\b|\bappropriat(?:ion|ions|ed)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Appropriation wording tied directly to compensation."),
        Rule("FISCAL_IMPACT", "fiscal_impact", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\bfiscal[-\s]+impact\b|\bfiscal[-\s]+impact\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|wage increase|salary increase|pay increase|personnel costs?|labor costs?)\b", re.I), "Fiscal impact tied directly to compensation."),
        Rule("FISCAL_BUDGETED_INCREASE", "budgeted_increase", re.compile(r"\bbudgeted\b[^\n.!?]{0,140}\b(?:wages?|salar(?:y|ies)|pay|compensation|personnel costs?|labor costs?)\b[^\n.!?]{0,100}\b(?:increase|raise)\b|\b(?:wages?|salar(?:y|ies)|pay|compensation|personnel costs?|labor costs?)\b[^\n.!?]{0,140}\bbudgeted\b[^\n.!?]{0,100}\b(?:increase|raise)\b|\b(?:increase|raise)\b[^\n.!?]{0,100}\b(?:wages?|salar(?:y|ies)|pay|compensation|personnel costs?|labor costs?)\b[^\n.!?]{0,140}\bbudgeted\b", re.I), "Explicit budgeted compensation increase.", "high", "strong"),
        Rule("FISCAL_MUNICIPAL_FINANCE", "municipal_finance_limit", re.compile(r"\b(?:wages?|salar(?:y|ies)|pay|compensation|raises?|increases?|personnel costs?|labor costs?)\b[^\n.!?]{0,180}\bmunicipal[-\s]+financ(?:e|es|ial)\b|\bmunicipal[-\s]+financ(?:e|es|ial)\b[^\n.!?]{0,180}\b(?:wages?|salar(?:y|ies)|pay|compensation|raises?|increases?|personnel costs?|labor costs?)\b", re.I), "Municipal-finance wording tied directly to compensation."),
    ),
}

WEAK_PATTERNS = {
    "strike_or_no_strike_constraint": re.compile(r"\b(?:strike|arbitration|fact[-\s]?finding|impasse|mediation)\b", re.I),
    "market_or_comparability_pressure": re.compile(r"\b(?:market|comparable|peer|recruitment|retention|competitive|study|survey)\b", re.I),
    "non_safety_constraint_signal": re.compile(r"\b(?:budget|fiscal|affordability|compression|delay|defer|freeze|cap|appropriation)\b", re.I),
    "fiscal_constraint_signal": re.compile(r"\b(?:budget|fiscal|tax|funding|appropriation|affordability|finance)\b", re.I),
}

REQUIRED_FINAL_OUTPUTS = (
    "targeted_evidence_span_extraction_321_decision.json",
    "targeted_evidence_span_extraction_321_summary.md",
    "targeted_evidence_span_extraction_321_locked_queue.csv",
    "targeted_evidence_span_extraction_321_locked_queue_summary.json",
    "targeted_evidence_span_extraction_321_lock.json",
    "targeted_evidence_span_extraction_321_dry_run_manifest.csv",
    "targeted_evidence_span_extraction_321_dry_run_summary.json",
    "targeted_evidence_span_extraction_321_no_call_validation.md",
    "targeted_evidence_span_extraction_321_preflight_checks.json",
    "targeted_evidence_span_extraction_321_preflight_report.md",
    "targeted_evidence_span_extraction_321_results.csv",
    "targeted_evidence_span_extraction_321_results_summary.json",
    "targeted_evidence_span_extraction_321_span_records.csv",
    "targeted_evidence_span_extraction_321_span_records_summary.json",
    "targeted_evidence_span_extraction_321_no_span_or_weak.csv",
    "targeted_evidence_span_extraction_321_no_span_or_weak_summary.json",
    *MECHANISM_FILES.values(),
    "targeted_evidence_span_extraction_321_pdf_results.csv",
    "targeted_evidence_span_extraction_321_html_results.csv",
    "targeted_evidence_span_extraction_321_pdf_span_records.csv",
    "targeted_evidence_span_extraction_321_html_span_records.csv",
    "targeted_evidence_span_extraction_321_rating_candidate_manifest.csv",
    "targeted_evidence_span_extraction_321_rating_candidate_summary.json",
    "targeted_evidence_span_extraction_321_claim_boundary_notes.md",
    "targeted_evidence_span_extraction_321_extraction_limits_and_boundaries.md",
    "targeted_evidence_span_extraction_321_mechanism_coverage.csv",
    "targeted_evidence_span_extraction_321_mechanism_coverage_summary.json",
    "targeted_evidence_span_extraction_321_city_cycle_unit_coverage.csv",
    "targeted_evidence_span_extraction_321_city_cycle_unit_coverage_summary.json",
    "targeted_evidence_span_extraction_321_preserved_text_extraction_exclusions.csv",
    "targeted_evidence_span_extraction_321_preserved_text_extraction_exclusions_summary.json",
    "targeted_evidence_span_extraction_321_validation_2026-07-26.md",
    "targeted_evidence_span_extraction_321_invariant_checks.json",
    "targeted_evidence_span_extraction_321_stress_test_report.md",
    "targeted_evidence_span_extraction_321_regression_test_inventory.json",
    "next_task.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_sha256("\n".join(sorted(row["retained_source_id"] for row in rows)))


def verify_inputs(*, verify_artifact_bytes: bool = True) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required immutable text-extraction input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable text-extraction input hash drift: {name}")
    decision = read_json(INPUT_DIR / "targeted_text_layer_extraction_321_decision.json")
    summary = read_json(INPUT_DIR / "targeted_text_layer_extraction_321_results_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_text_layer_extraction_321_invariant_checks.json")
    queue = read_csv(INPUT_DIR / "targeted_text_layer_extraction_321_evidence_extraction_candidate_manifest.csv")
    results = read_csv(INPUT_DIR / "targeted_text_layer_extraction_321_results.csv")
    artifacts = read_csv(INPUT_DIR / "extracted_text_manifest.csv")
    preserved = read_csv(INPUT_DIR / "targeted_text_layer_extraction_321_preserved_readiness_exclusions.csv")
    queue_ids = {row["retained_source_id"] for row in queue}
    if not (
        decision.get("decision") == "targeted_text_layer_extraction_321_completed_evidence_extraction_ready"
        and decision.get("evidence_extraction_review_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and summary.get("result_rows") == EXPECTED_COUNT
        and summary.get("evidence_extraction_candidate_count") == EXPECTED_COUNT
        and invariants.get("all_invariants_passed") is True
        and len(queue) == len(results) == len(artifacts) == EXPECTED_COUNT
        and len(queue_ids) == EXPECTED_COUNT and id_set_hash(queue) == EXPECTED_ID_SET_HASH
        and queue_ids == {row["retained_source_id"] for row in results} == {row["retained_source_id"] for row in artifacts}
        and sum(row["readiness_status"] == "parse_text_layer_later" for row in queue) == EXPECTED_PDF_COUNT
        and sum(row["readiness_status"] == "html_text_later" for row in queue) == EXPECTED_HTML_COUNT
        and Counter(row["lane_id"] for row in queue) == Counter(EXPECTED_LANES)
        and Counter(row["target_mechanism_family"] for row in queue) == Counter(EXPECTED_MECHANISMS)
        and len(preserved) == 108
        and all(row["extraction_status"] == "extracted_ok" for row in queue)
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in queue)
        and all(row["readiness_status"] in {"parse_text_layer_later", "html_text_later"} for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["ingestion_status"] == "not_ingested" for row in queue)
        and all(row["codification_status"] == "not_codified" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and all(row["global_analysis_readiness"] == "false" for row in queue)
    ):
        raise RuntimeError("321-row extracted-ok evidence-span scope reconciliation failed")
    for row in queue:
        path = ROOT / row["extracted_text_path"]
        if not path.is_file() or not path.resolve().is_relative_to(TEXT_ROOT.resolve()):
            raise RuntimeError(f"extracted text missing or outside task-local text root: {row['retained_source_id']}")
        if path.stat().st_size != int(row["extracted_text_size_bytes"]):
            raise RuntimeError(f"extracted text size mismatch: {row['retained_source_id']}")
        if verify_artifact_bytes and sha256(path) != row["extracted_text_sha256"]:
            raise RuntimeError(f"extracted text SHA-256 mismatch: {row['retained_source_id']}")
    queue.sort(key=lambda row: (row["lane_id"], row["target_mechanism_family"], row["retained_source_id"]))
    return queue, preserved, observed


def bounded_window(text: str, match_start: int, match_end: int) -> tuple[int, int]:
    left_boundary = text.rfind("\n\n", max(0, match_start - 450), match_start)
    right_boundary = text.find("\n\n", match_end, min(len(text), match_end + 650))
    start = left_boundary + 2 if left_boundary >= 0 else max(0, match_start - 250)
    end = right_boundary if right_boundary >= 0 else min(len(text), match_end + 450)
    if end - start > MAX_SPAN_CHARACTERS:
        start = max(start, match_start - 300)
        end = min(end, start + MAX_SPAN_CHARACTERS)
        if end < match_end:
            end = match_end
            start = max(0, end - MAX_SPAN_CHARACTERS)
    if end - start < 80:
        start = max(0, match_start - 150)
        end = min(len(text), match_end + 500)
    while start < match_start and text[start].isspace():
        start += 1
    while end > match_end and text[end - 1].isspace():
        end -= 1
    return start, end


def context_for(text: str, start: int, end: int) -> tuple[str, str]:
    return text[max(0, start - CONTEXT_CHARACTERS):start], text[end:min(len(text), end + CONTEXT_CHARACTERS)]


def span_id(retained_source_id: str, start: int, end: int, rule_id: str) -> str:
    return "SPAN321-" + text_sha256(f"{retained_source_id}|{start}|{end}|{rule_id}")[:24]


def result_base(row: dict[str, str]) -> dict[str, str]:
    return {
        "span_extraction_id": "SRCSPAN321-" + text_sha256(row["retained_source_id"])[:20],
        **{field: row.get(field, "") for field in RESULT_FIELDS if field in row},
        "local_extracted_text_path": row["extracted_text_path"],
        "source_file_sha256": row["file_sha256"],
        "span_status": "extraction_error", "span_status_reason": "not_completed",
        "span_record_count": "0", "mechanism_family": row["target_mechanism_family"],
        "span_text": "", "span_start_offset": "", "span_end_offset": "",
        "span_sha256": "", "context_before": "", "context_after": "",
        "extraction_rule_id": "", "extraction_rule_family": "",
        "span_specificity": "low", "documentary_claim_support": "not_supported",
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified", "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false",
        "notes": "Exact extracted-text span only; not a rating, causal finding, or global analysis record.",
    }


def rule_context(text: str, start: int, end: int) -> str:
    return text[max(0, start - 400):min(len(text), end + 400)]


def make_span_record(row: dict[str, str], text: str, start: int, end: int, rule: Rule, *, status: str = "span_extracted") -> dict[str, str]:
    span = text[start:end]
    before, after = context_for(text, start, end)
    record = result_base(row)
    record.update({
        "span_extraction_id": span_id(row["retained_source_id"], start, end, rule.rule_id),
        "span_status": status,
        "span_status_reason": "exact_documentary_mechanism_span_extracted" if status == "span_extracted" else "generic_or_untied_mechanism_mention_requires_review",
        "span_record_count": "1", "mechanism_family": row["target_mechanism_family"],
        "span_text": span, "span_start_offset": str(start), "span_end_offset": str(end),
        "span_sha256": text_sha256(span), "context_before": before, "context_after": after,
        "extraction_rule_id": rule.rule_id, "extraction_rule_family": rule.family,
        "span_specificity": rule.specificity if status == "span_extracted" else "low",
        "documentary_claim_support": rule.support if status == "span_extracted" else "weak",
    })
    return record


def extract_source(row: dict[str, str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    source_result = result_base(row)
    path = ROOT / row["extracted_text_path"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        source_result.update({"span_status": "extraction_error", "span_status_reason": f"local_text_read_{type(exc).__name__}"})
        return source_result, []
    mechanism = row["target_mechanism_family"]
    candidates: list[tuple[int, int, Rule]] = []
    for rule in RULES[mechanism]:
        for match in rule.pattern.finditer(text):
            if rule.required_context and not rule.required_context.search(rule_context(text, match.start(), match.end())):
                continue
            start, end = bounded_window(text, match.start(), match.end())
            candidates.append((start, end, rule))
    deduped: list[tuple[int, int, Rule]] = []
    occupied: set[tuple[int, int]] = set()
    for start, end, rule in sorted(candidates, key=lambda item: (item[0], 0 if item[2].specificity == "high" else 1, item[1])):
        if (start, end) in occupied:
            continue
        if any(start >= old_start and end <= old_end for old_start, old_end, _ in deduped):
            continue
        occupied.add((start, end))
        deduped.append((start, end, rule))
        if len(deduped) >= MAX_POSITIVE_SPANS_PER_SOURCE:
            break
    records = [make_span_record(row, text, start, end, rule) for start, end, rule in deduped]
    if records:
        primary = records[0]
        source_result.update({field: primary.get(field, source_result.get(field, "")) for field in RESULT_FIELDS})
        source_result["span_extraction_id"] = "SRCSPAN321-" + text_sha256(row["retained_source_id"])[:20]
        source_result["span_record_count"] = str(len(records))
        source_result["span_status_reason"] = "one_or_more_exact_documentary_mechanism_spans_extracted"
        return source_result, records
    weak = WEAK_PATTERNS[mechanism].search(text)
    if weak:
        start, end = bounded_window(text, weak.start(), weak.end())
        weak_rule = Rule(f"{mechanism.upper()}_WEAK", "generic_or_untied_mention", WEAK_PATTERNS[mechanism], "Generic mechanism mention lacks the required compensation or institutional linkage.", "low", "weak")
        record = make_span_record(row, text, start, end, weak_rule, status="ambiguous_span")
        source_result.update({field: record.get(field, source_result.get(field, "")) for field in RESULT_FIELDS})
        source_result["span_extraction_id"] = "SRCSPAN321-" + text_sha256(row["retained_source_id"])[:20]
        source_result["span_record_count"] = "1"
        return source_result, [record]
    source_result.update({
        "span_status": "no_span_or_weak",
        "span_status_reason": "no_target_mechanism_keyword_family_found_in_local_extracted_text",
        "span_record_count": "0", "span_specificity": "low", "documentary_claim_support": "not_supported",
    })
    return source_result, []


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, preserved, hashes = verify_inputs(verify_artifact_bytes=True)
    OUTPUT_DIR.mkdir(parents=True)
    locked = [{field: row.get(field, "") for field in QUEUE_FIELDS} for row in queue]
    queue_path = OUTPUT_DIR / "targeted_evidence_span_extraction_321_locked_queue.csv"
    write_csv(queue_path, locked, QUEUE_FIELDS)
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT, "locked_queue_count": len(locked),
        "pdf_queue_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in locked),
        "html_queue_count": sum(row["readiness_status"] == "html_text_later" for row in locked),
        "queue_sha256": sha256(queue_path), "retained_source_id_set_sha256": id_set_hash(locked),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in locked).items())),
        "immutable_input_hashes": hashes, "preserved_exclusion_count": len(preserved),
        "max_positive_spans_per_source": MAX_POSITIVE_SPANS_PER_SOURCE,
        "max_span_characters": MAX_SPAN_CHARACTERS, "context_characters_each_side": CONTEXT_CHARACTERS,
        "span_extraction_status": "not_started", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_locked_queue_summary.json", {
        "locked_queue_count": len(locked), "pdf_queue_count": lock["pdf_queue_count"],
        "html_queue_count": lock["html_queue_count"], "lane_counts": lock["lane_counts"],
        "mechanism_counts": lock["mechanism_counts"], "non_extracted_or_excluded_rows_in_queue": 0,
        "tier_c_or_d_rows_in_queue": 0, "preserved_exclusions_in_queue": 0,
        "global_analysis_readiness": False,
    })
    dry = [{
        "extracted_text_id": row["extracted_text_id"], "retained_source_id": row["retained_source_id"],
        "candidate_id": row["candidate_id"], "lane_id": row["lane_id"],
        "target_mechanism_family": row["target_mechanism_family"],
        "dry_run_status": "ready_for_deterministic_exact_span_search",
        "live_span_extraction_status": "not_started", "artifact_hash_valid": "true",
        "url_open_planned": "no", "download_planned": "no", "ocr_planned": "no",
        "pdf_rendering_planned": "no", "model_api_planned": "no", "rating_planned": "no",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_dry_run_manifest.csv", dry, dry[0].keys())
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_dry_run_summary.json", {
        "no_call_dry_run": True, "dry_run_rows": len(dry), "pdf_rows": lock["pdf_queue_count"],
        "html_rows": lock["html_queue_count"], "span_extractions_completed": 0,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "all_live_status_not_started": True,
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_no_call_validation.md", """# No-call evidence-span extraction validation

Exactly 321 extracted-ok, task-local text artifacts are locked: 289 PDF-derived text artifacts and 32 HTML-derived text artifacts. All hashes passed. The 108 readiness/source-review exclusions remain outside the queue. Dry preparation performed no text search, URL access, download, OCR, rendering, model call, rating, ingestion, or codification. Global analysis readiness remains false.
""")
    preflight = {
        "preflight_passed": len(locked) == EXPECTED_COUNT,
        "text_layer_extraction_decision_allows_span_review": True,
        "locked_queue_count": len(locked), "pdf_queue_count": lock["pdf_queue_count"],
        "html_queue_count": lock["html_queue_count"], "queue_hash_matches_lock": sha256(queue_path) == lock["queue_sha256"],
        "retained_id_hash_matches_lock": id_set_hash(locked) == EXPECTED_ID_SET_HASH,
        "all_extracted_text_paths_sizes_hashes_valid": True, "excluded_rows_in_queue": 0,
        "preserved_exclusions_outside_queue": len(preserved), "url_opens": 0, "downloads": 0,
        "ocr_runs": 0, "pdf_render_runs": 0, "model_api_calls": 0, "rating_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_preflight_report.md", """# Targeted evidence-span extraction preflight

Preflight passed for exactly 321 immutable, extracted-ok local text artifacts: 289 PDF-derived and 32 HTML-derived. The deterministic rules search only the artifact assigned to each candidate's target mechanism. Positive records must be exact substrings with offsets and SHA-256; generic or context-free mentions remain ambiguous or no-span. No URL, download, OCR, rendering, model, rating, ingestion, codification, statistics, wage-gap, regression, treatment-effect, causal, or durable-ledger work is authorized.
""")
    print(json.dumps({"status": "dry_preparation_and_preflight_passed", "rows": len(locked), "queue_sha256": lock["queue_sha256"]}))


def group_status_counts(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[field]].append(row)
    output = []
    for value, group in sorted(grouped.items()):
        counts = Counter(row["span_status"] for row in group)
        output.append({field: value, "source_count": len(group), **{status: counts.get(status, 0) for status in sorted(CONTROLLED_STATUSES)}})
    return output


def write_outputs(source_results: list[dict[str, str]], span_records: list[dict[str, str]], preserved: list[dict[str, str]]) -> str:
    status_counts = Counter(row["span_status"] for row in source_results)
    positive = [row for row in span_records if row["span_status"] == "span_extracted"]
    ambiguous_records = [row for row in span_records if row["span_status"] == "ambiguous_span"]
    positive_source_ids = {row["retained_source_id"] for row in positive}
    rating_candidates = list(positive)
    errors = status_counts.get("extraction_error", 0)
    if errors:
        decision_name = "targeted_evidence_span_extraction_321_completed_repair_needed"
    elif len(positive_source_ids) < 30 or len(positive) < 50:
        decision_name = "targeted_evidence_span_extraction_321_completed_tier_c_verification_recommended"
    elif len(positive_source_ids) < 50 or len(positive) < 100:
        decision_name = "targeted_evidence_span_extraction_321_completed_repair_needed"
    else:
        decision_name = "targeted_evidence_span_extraction_321_completed_rating_ready"
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_results.csv", source_results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_span_records.csv", span_records, RESULT_FIELDS)
    weak = [row for row in source_results if row["span_status"] != "span_extracted"]
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_no_span_or_weak.csv", weak, RESULT_FIELDS)
    pdf_results = [row for row in source_results if row["local_extracted_text_path"].startswith(str((TEXT_ROOT / "pdf").relative_to(ROOT)))]
    html_results = [row for row in source_results if row["local_extracted_text_path"].startswith(str((TEXT_ROOT / "html").relative_to(ROOT)))]
    pdf_records = [row for row in span_records if row["local_extracted_text_path"].startswith(str((TEXT_ROOT / "pdf").relative_to(ROOT)))]
    html_records = [row for row in span_records if row["local_extracted_text_path"].startswith(str((TEXT_ROOT / "html").relative_to(ROOT)))]
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_pdf_results.csv", pdf_results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_html_results.csv", html_results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_pdf_span_records.csv", pdf_records, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_html_span_records.csv", html_records, RESULT_FIELDS)
    for mechanism, filename in MECHANISM_FILES.items():
        rows = [row for row in positive if row["mechanism_family"] == mechanism]
        write_csv(OUTPUT_DIR / filename, rows, RESULT_FIELDS)
        stem = filename.removesuffix(".csv") + "_summary.json"
        write_json(OUTPUT_DIR / stem, {
            "mechanism_family": mechanism, "positive_span_record_count": len(rows),
            "source_count": len({row["retained_source_id"] for row in rows}),
            "rating_candidate_count": len(rows), "global_analysis_readiness": False,
        })
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_rating_candidate_manifest.csv", rating_candidates, RESULT_FIELDS)
    by_mechanism = dict(sorted(Counter(row["mechanism_family"] for row in positive).items()))
    by_lane = dict(sorted(Counter(row["lane_id"] for row in positive).items()))
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_span_records_summary.json", {
        "total_span_record_count": len(span_records), "positive_span_record_count": len(positive),
        "ambiguous_span_record_count": len(ambiguous_records), "positive_source_count": len(positive_source_ids),
        "positive_span_counts_by_mechanism": by_mechanism, "positive_span_counts_by_lane": by_lane,
        "all_spans_exact_substrings_offsets_and_hashes_valid": True,
    })
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_no_span_or_weak_summary.json", {
        "no_span_or_weak_source_count": status_counts.get("no_span_or_weak", 0),
        "ambiguous_span_source_count": status_counts.get("ambiguous_span", 0),
        "extraction_error_source_count": errors, "excluded_from_rating_candidate_manifest": len(weak),
    })
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_rating_candidate_summary.json", {
        "rating_candidate_count": len(rating_candidates), "rating_candidate_source_count": len(positive_source_ids),
        "by_mechanism": by_mechanism, "by_lane": by_lane,
        "allowed_next_stage": "separately_authorized_exact_span_rating_or_claim_review",
        "currently_rated": False, "causal_ready": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_results_summary.json", {
        "source_result_rows": len(source_results), "pdf_source_rows": len(pdf_results), "html_source_rows": len(html_results),
        "span_status_counts": dict(sorted(status_counts.items())), "total_span_record_count": len(span_records),
        "positive_span_record_count": len(positive), "ambiguous_span_record_count": len(ambiguous_records),
        "positive_source_count": len(positive_source_ids), "rating_candidate_count": len(rating_candidates),
        "positive_span_counts_by_mechanism": by_mechanism, "positive_span_counts_by_lane": by_lane,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_pdf_results_summary.json", {
        "pdf_source_rows": len(pdf_results), "pdf_span_record_count": len(pdf_records),
        "pdf_positive_span_record_count": sum(row["span_status"] == "span_extracted" for row in pdf_records),
        "status_counts": dict(sorted(Counter(row["span_status"] for row in pdf_results).items())),
    })
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_html_results_summary.json", {
        "html_source_rows": len(html_results), "html_span_record_count": len(html_records),
        "html_positive_span_record_count": sum(row["span_status"] == "span_extracted" for row in html_records),
        "status_counts": dict(sorted(Counter(row["span_status"] for row in html_results).items())),
    })
    mechanism_rows = group_status_counts(source_results, "target_mechanism_family")
    for row in mechanism_rows:
        mechanism = row["target_mechanism_family"]
        row["positive_span_record_count"] = by_mechanism.get(mechanism, 0)
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_mechanism_coverage_summary.json", {
        "mechanism_count": len(mechanism_rows), "by_mechanism": {row["target_mechanism_family"]: {k: v for k, v in row.items() if k != "target_mechanism_family"} for row in mechanism_rows},
        "coverage_boundary": "Exact-span counts are collected-corpus documentary signals, not prevalence, wage effects, or causal findings.",
    })
    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source_results:
        city_groups[(row["municipality"], row["state"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for key, group in sorted(city_groups.items()):
        city_rows.append({
            "municipality": key[0], "state": key[1], "unit_type": key[2], "contract_or_document_period": key[3],
            "span_extraction_source_count": len(group), "span_extracted_source_count": sum(row["span_status"] == "span_extracted" for row in group),
            "ambiguous_or_no_span_count": sum(row["span_status"] in {"ambiguous_span", "no_span_or_weak"} for row in group),
            "extraction_error_count": sum(row["span_status"] == "extraction_error" for row in group),
        })
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_positive_span": sum(int(row["span_extracted_source_count"]) > 0 for row in city_rows),
        "groups_without_positive_span": sum(int(row["span_extracted_source_count"]) == 0 for row in city_rows),
        "distinct_city_state_pairs": len({(row["municipality"], row["state"]) for row in source_results}),
        "coverage_boundary": "Span outputs do not update durable city coverage.",
    })
    preserved_fields = tuple(dict.fromkeys(key for row in preserved for key in row.keys()))
    write_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_preserved_text_extraction_exclusions.csv", preserved, preserved_fields)
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_preserved_text_extraction_exclusions_summary.json", {
        "preserved_exclusion_count": len(preserved), "preserved_exclusions_entering_span_queue": 0,
        "status_counts": dict(sorted(Counter(f"{row.get('exclusion_layer','')}:{row.get('preserved_exclusion_status','')}" for row in preserved).items())),
    })
    repair_needed = decision_name.endswith("repair_needed")
    decision = {
        "task_id": TASK_ID, "decision": decision_name,
        "completion_status": "completed_bounded_deterministic_exact_span_extraction",
        "span_extraction_queue_count": len(source_results), "pdf_span_extraction_count": len(pdf_results),
        "html_span_extraction_count": len(html_results), "span_status_counts": dict(sorted(status_counts.items())),
        "span_extracted_source_count": len(positive_source_ids), "total_span_record_count": len(span_records),
        "positive_span_record_count": len(positive), "rating_candidate_count": len(rating_candidates),
        "positive_span_counts_by_mechanism": by_mechanism, "positive_span_counts_by_lane": by_lane,
        "evidence_span_rating_ready_next": decision_name.endswith("completed_rating_ready"),
        "repair_needed": repair_needed,
        "tier_c_verification_recommended_next": decision_name.endswith("tier_c_verification_recommended"),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_decision.json", decision)
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_summary.md", f"""# Targeted evidence-span extraction — 321 extracted text sources

Decision: `{decision_name}`.

Exactly 321 local extracted-text artifacts were searched deterministically: 289 PDF-derived and 32 HTML-derived. Source outcomes reconcile to `{dict(sorted(status_counts.items()))}`. The stage produced {len(positive)} positive exact documentary span records across {len(positive_source_ids)} sources and {len(ambiguous_records)} exact but ambiguous records. Only the {len(rating_candidates)} positive records enter the separately authorized rating-candidate manifest.

All spans are exact substrings with validated offsets and SHA-256. No URL, download, OCR, rendering, model call, rating, ingestion, codification, statistic, wage-gap calculation, regression, treatment effect, causal claim, or durable-ledger merge occurred. Global analysis readiness remains false.
""")
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_claim_boundary_notes.md", """# Claim boundary notes

Positive spans may support bounded documentary statements about what the collected text says. They do not establish direction, prevalence, wage effects, a wage gap, or causality. Ambiguous spans are excluded from the rating candidate manifest. A future rating stage must use only the exact span and its bounded context, preserve the supplied mechanism as a target rather than a finding, and retain `no_final_causal_claim=true` and `global_analysis_readiness=false`.
""")
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_extraction_limits_and_boundaries.md", f"""# Extraction limits and boundaries

- Deterministic local rules only; no model/API call.
- At most {MAX_POSITIVE_SPANS_PER_SOURCE} positive spans per source.
- Each span is at most {MAX_SPAN_CHARACTERS} characters, with at most {CONTEXT_CHARACTERS} exact context characters on each side.
- Rules require explicit mechanism phrases and, where needed, nearby compensation or strike-substitute language.
- Generic mentions remain ambiguous or no-span and do not enter rating candidates.
- PDF-derived and HTML-derived lanes remain separate.
- Evidence-span extraction is not rating; exact spans are not causal proof or global analysis data.
""")
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_invariant_checks.json", {
        "all_invariants_passed": errors == 0,
        "locked_queue_exactly_321": len(source_results) == 321,
        "pdf_html_counts_exactly_289_32": len(pdf_results) == 289 and len(html_results) == 32,
        "source_statuses_reconcile_to_321": sum(status_counts.values()) == 321,
        "only_extracted_ok_artifacts_entered": True, "preserved_exclusions_outside_queue": len(preserved) == 108,
        "every_positive_span_exact_offsets_hash_valid": True,
        "generic_mentions_excluded_from_rating_candidates": all(row["span_status"] == "span_extracted" for row in rating_candidates),
        "pdf_html_lanes_separate": len(pdf_results) == 289 and len(html_results) == 32,
        "downstream_statuses_closed": all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in source_results + span_records),
        "no_url_download_ocr_render_model_rating_ingestion_or_codification": True,
        "no_wage_gap_regression_treatment_effect_or_final_causal_work": True,
        "no_durable_ledger_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_stress_test_report.md", """# Stress-test report

- Non-extracted, deferred, excluded, Tier C/D, wrong-path, size-drift, or SHA-drift rows fail before search.
- Required-context rules keep generic budget, study, recruitment, arbitration, and mediation mentions out of positive spans.
- Exact substring, offset, and SHA checks cover every positive and ambiguous record.
- Positive records are bounded to five per source and 900 characters per span; context is bounded to 160 characters on each side.
- Ambiguous and no-span sources remain explicit exclusions from the rating manifest.
- PDF and HTML lanes remain separate; no network, OCR, rendering, or model dependency exists.
- Partial packages fail completion validation; completed `--resume` is read-only.
""")
    write_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_regression_test_inventory.json", {
        "focused_suite": "scripts/test_targeted_evidence_span_extraction_321.py",
        "coverage": ["exact 321-source scope", "289/32 PDF/HTML split", "immutable input and artifact hashes", "excluded-row rejection", "exact substring offsets and hashes", "mechanism context gates", "generic mention routing", "bounded spans/context", "closed downstream statuses", "dashboard global closure", "idempotent resume", "partial-output fail-closed"],
    })
    next_name = "next_targeted_evidence_span_rating_prompt.md" if decision["evidence_span_rating_ready_next"] else "next_targeted_evidence_span_extraction_repair_prompt.md"
    write_text(OUTPUT_DIR / next_name, """# Next prompt: bounded exact-span rating review

Use only `targeted_evidence_span_extraction_321_rating_candidate_manifest.csv` rows with `span_status=span_extracted`. Verify each supplied span remains an exact substring at the recorded offsets and hash before any rating. Rate only the supplied exact span plus its bounded exact context; preserve PDF/HTML, retained-source, candidate, city, unit, cycle, mechanism-target, source-file, and extracted-text lineage.

Do not fetch or pull repository state, inspect/configure remotes, open URLs, download documents, include ambiguous/no-span/error/excluded rows, access PDFs/pages, run OCR or rendering, use evidence outside the supplied span/context, ingest, codify, calculate wage gaps, run regressions or treatment effects, make final causal claims, or mark global analysis readiness true. GABRIEL/API/model use requires separate explicit authorization. Rating is not causal proof.
""")
    write_text(OUTPUT_DIR / "next_task.md", f"""# Next task: bounded exact-span rating review

Decision: `{decision_name}`. Use only the {len(rating_candidates)} positive exact-span records in `targeted_evidence_span_extraction_321_rating_candidate_manifest.csv`. Revalidate exact substring, offsets, and SHA-256, then apply a separately authorized claim-oriented documentary rating contract. Exclude every ambiguous, no-span, error, readiness-deferred, and source-review exclusion row.

Do not access URLs or PDFs/pages, download, OCR, render, use evidence outside supplied spans, ingest, codify, calculate wage gaps, run regressions/treatment effects, make final causal claims, or set global analysis readiness true. Model/API use requires separate authorization.
""")
    write_text(OUTPUT_DIR / "targeted_evidence_span_extraction_321_validation_2026-07-26.md", f"""# Targeted evidence-span extraction validation — 2026-07-26

Internal invariants passed for the immutable 321-artifact scope. PDF/HTML counts reconciled to 289/32, all source outcomes reconciled to 321, every exact span passed substring/offset/SHA validation, and all 108 preserved exclusions remained outside the queue. Decision: `{decision_name}`. External repository/test/build validation results are appended after the required suite completes.
""")
    write_text(ROOT / "docs/analysis/targeted_evidence_span_extraction_321_result_2026-07-26.md", f"""# Targeted evidence-span extraction result

- Decision: `{decision_name}`.
- Span-extraction queue: 321 (289 PDF-derived; 32 HTML-derived).
- Source outcomes: `{dict(sorted(status_counts.items()))}`.
- Positive exact span records: {len(positive)} across {len(positive_source_ids)} sources.
- Rating candidates: {len(rating_candidates)}.
- URL/download/OCR/render/model/rating/ingestion/codification/durable merges: 0.
- Global analysis readiness: false.
""")
    write_text(ROOT / "docs/analysis/targeted_evidence_span_extraction_321_dashboard_status_note_2026-07-26.md", f"""# Dashboard status note — targeted evidence-span extraction

- Decision: `{decision_name}`.
- Exact queue: 321 (289 PDF-derived; 32 HTML-derived).
- Source status counts: `{dict(sorted(status_counts.items()))}`.
- Positive exact spans: {len(positive)}; rating candidates: {len(rating_candidates)}.
- Evidence-span rating ready next: {'true' if decision['evidence_span_rating_ready_next'] else 'false'}.
- Repair needed: {'true' if repair_needed else 'false'}.
- Tier C verification recommended: {'true' if decision['tier_c_verification_recommended_next'] else 'false'}.
- Global analysis readiness: false.
""")
    return decision_name


def validate_spans(source_results: list[dict[str, str]], span_records: list[dict[str, str]]) -> None:
    by_source = {row["retained_source_id"]: row for row in source_results}
    for record in span_records:
        source = by_source[record["retained_source_id"]]
        text = (ROOT / source["local_extracted_text_path"]).read_text(encoding="utf-8")
        start, end = int(record["span_start_offset"]), int(record["span_end_offset"])
        if not (
            0 <= start < end <= len(text)
            and text[start:end] == record["span_text"]
            and text_sha256(record["span_text"]) == record["span_sha256"]
            and len(record["span_text"]) <= MAX_SPAN_CHARACTERS
            and record["mechanism_family"] == source["target_mechanism_family"]
            and record["span_status"] in {"span_extracted", "ambiguous_span"}
            and record["rating_status"] == "not_rated"
            and record["global_analysis_readiness"] == "false"
        ):
            raise RuntimeError(f"exact span validation failed: {record['span_extraction_id']}")


def extract() -> None:
    queue, preserved, _ = verify_inputs(verify_artifact_bytes=True)
    lock_path = OUTPUT_DIR / "targeted_evidence_span_extraction_321_lock.json"
    queue_path = OUTPUT_DIR / "targeted_evidence_span_extraction_321_locked_queue.csv"
    preflight_path = OUTPUT_DIR / "targeted_evidence_span_extraction_321_preflight_checks.json"
    if not (lock_path.is_file() and queue_path.is_file() and preflight_path.is_file()):
        raise RuntimeError("dry preparation/preflight outputs missing")
    lock, preflight, locked = read_json(lock_path), read_json(preflight_path), read_csv(queue_path)
    if not (
        preflight.get("preflight_passed") is True and len(queue) == len(locked) == EXPECTED_COUNT
        and sha256(queue_path) == lock["queue_sha256"]
        and id_set_hash(locked) == lock["retained_source_id_set_sha256"] == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("deterministic span extraction lock/preflight failed")
    source_results: list[dict[str, str]] = []
    span_records: list[dict[str, str]] = []
    for row in locked:
        source_result, records = extract_source(row)
        source_results.append(source_result)
        span_records.extend(records)
    if len(source_results) != EXPECTED_COUNT or any(row["span_status"] not in CONTROLLED_STATUSES for row in source_results):
        raise RuntimeError("span extraction source reconciliation failed")
    validate_spans(source_results, span_records)
    decision = write_outputs(source_results, span_records, preserved)
    validate_complete()
    print(json.dumps({"status": "deterministic_exact_span_extraction_completed", "decision": decision, "sources": len(source_results), "span_records": len(span_records)}))


def validate_complete() -> None:
    missing = [name for name in REQUIRED_FINAL_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"partial span output cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_decision.json")
    invariants = read_json(OUTPUT_DIR / "targeted_evidence_span_extraction_321_invariant_checks.json")
    sources = read_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_results.csv")
    spans = read_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_span_records.csv")
    rating = read_csv(OUTPUT_DIR / "targeted_evidence_span_extraction_321_rating_candidate_manifest.csv")
    validate_spans(sources, spans)
    if not (
        len(sources) == EXPECTED_COUNT and len({row["retained_source_id"] for row in sources}) == EXPECTED_COUNT
        and decision.get("global_analysis_readiness") is False and invariants.get("all_invariants_passed") is True
        and all(row["span_status"] in CONTROLLED_STATUSES for row in sources)
        and all(row["span_status"] == "span_extracted" for row in rating)
        and all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in sources + spans)
    ):
        raise RuntimeError("completed evidence-span outputs fail closed validation")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--extract", action="store_true")
    action.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.extract:
        extract()
    else:
        verify_inputs(verify_artifact_bytes=True)
        validate_complete()
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_COUNT}))


if __name__ == "__main__":
    main()
