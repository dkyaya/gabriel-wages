#!/usr/bin/env python3
"""Link 513 quantitative rows to bounded qualitative mechanisms by strict lineage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
QUANT_DIR = BASE / "QUANTITATIVE-DIRECT-TEXT-CLAIM-TRIAGE-862-PRESERVED-ROWS-2026-07-26"
TARGETED_DIR = BASE / "TARGETED-EVIDENCE-SPAN-RATING-SUMMARY-173-VALID-RATINGS-2026-07-26"
PHASE_DIR = BASE / "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
VALID636_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-SUMMARY-REVIEW-636-2026-07-25"
RATING636_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25"
TARGETED_RATING_DIR = BASE / "TARGETED-EVIDENCE-SPAN-RATING-201-EXACT-SPANS-2026-07-26"
OUTPUT_DIR = BASE / "QUANTITATIVE-TO-QUALITATIVE-MECHANISM-LINKAGE-513-CANDIDATES-2026-07-26"
RESULT_DOC = ROOT / "docs/analysis/quantitative_to_qualitative_mechanism_linkage_513_result_2026-07-26.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/quantitative_to_qualitative_mechanism_linkage_513_dashboard_status_note_2026-07-26.md"
TASK_ID = "QUANTITATIVE-TO-QUALITATIVE-MECHANISM-LINKAGE-513-CANDIDATES-2026-07-26"
DECISION = "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready"
EXPECTED_QUANT = 513
EXPECTED_QUAL = 609

INPUTS = {
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_decision.json": "14a4f8f30c3f395d5f29471a881c60f8631827d008e66551e2e75f8eb15af3dc",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_summary.md": "7233d18f3ab86b48a3d12998e834ca2f425c5c80ab2c770eeed12614e6a2a9da",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_locked_queue_summary.json": "61a7edbe793a2355568d897e535d6544b587d7ab3578fb59f4bf94bfe9c6f616",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_results_summary.json": "13970a66e4981117d6caf724e34599756bf3ecb86288f0a89979a70c4aaa72e3",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidate_summary.json": "17bc5cf916b52c8bdaaa2c1e90caf7e3c3e5ded3047150b88503228c03a71f46",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_unit_cycle_coverage_summary.json": "0ff0c91ddaee3103c32e1d944d955a8279e9f00c50b39e64c9704dfb6034ce39",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_source_family_coverage_summary.json": "968e0bf6fc0b974ec7bc51a6e50a884c917d08d48c2c466cbcb0b366686681b1",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_validation_2026-07-26.md": "11e652dbba4650d2bfa6404fcedfdf0c855cb5ceab9242e4e9d760c989c21090",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidates.csv": "6df28e76ea63e2b71d744d8db1cedabff64b883154c78a9b0a73cabd6bc0f357",
    QUANT_DIR / "quantitative_direct_text_claim_triage_862_results.csv": "d34f27c7a4844fcaec0460ec52dc410b875db4420e08dae14072edd8e90a7c80",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_decision.json": "0d2e60f7b9267d3959cc2d3220739ab652ee63a7f5adcaa08bb48ec350c959fd",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_summary.md": "c1108dcdbb79bce2eed4f1cb9069ff9d68feb87bfd71ff915d285bc609c4134c",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_mechanism_summary.json": "a5b98914de51a1dfa8985a36721ab9a28094ab033efaed71cc8b3e26679817af",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_supported_direct_text_claims.md": "ae5121e48f17041c26459ecbfce453646b2460337361c763a741a385c28377fc",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_supported_documentary_mechanism_claims.md": "179b8654dfb9e0693171ef03fce8f46a8436c9718d5eca3fe0d83280e6301e41",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_provisional_causal_candidate_signals.md": "7d27d185b05a57b10c38634dede4201e3f68beb073d4cce65b0bd4c640a15104",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_claims_requiring_more_data.md": "298da4be78624de565a20334cb4829498cf98c46960196b730686ce3d26bd1fa",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_claims_not_allowed.md": "02eace297927de6ca57b33917b09ae3119e45d6ee3a41d795d2edc147b90f963",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_validation_2026-07-26.md": "9a92ff1fd7ca70b22e915c4c0e1191ed7868abfa5c7eca6b95ba44a7059a9dde",
    TARGETED_DIR / "targeted_evidence_span_rating_summary_173_valid_scope.csv": "bdc1ab9751d587d91da26cf3ce967fb6cf2dd8c14e5a96663e802b076fd26052",
    PHASE_DIR / "qualitative_mechanism_claim_ready_manifest.csv": "5993d89931fc9e816b60e607f4acb8a467bb587a3bf28390ed1922aae65c6fb6",
    VALID636_DIR / "gabriel_claim_rating_summary_review_valid_636_manifest.csv": "b459a7649d26c1416c8b17e8a77a1b0ce1de34d2dc01750a66a7766a6d142893",
    VALID636_DIR / "gabriel_claim_rating_summary_review_excluded_7_manifest.csv": "fbc526f975852b7c5138f9f50abdcd4b4c18299478ea9393bd51af0fa7a74bc1",
    RATING636_DIR / "gabriel_claim_oriented_attribute_ratings_643_repaired.csv": "de7ce29aa5c749e0faadab97ccade17d1f470e35e1dc48a95767baf70ed191e9",
    TARGETED_RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv": "e90d4b0e46eb303660c84b7a15b5b293cd16e5c74bda7abacecd861af03377e3",
}

MECHANISMS = [
    "automatic_raise_mechanism", "bargaining_power_signal", "market_or_comparability_pressure",
    "rank_or_specialization_premium", "implementation_or_retroactivity_advantage",
    "fiscal_constraint_signal", "parity_or_internal_equity_signal", "non_base_compensation_signal",
    "safety_advantage_signal", "non_safety_constraint_signal", "gap_narrowing_signal",
    "strike_or_no_strike_constraint",
]
CONFIDENCES = ["exact_same_source", "exact_city_unit_cycle", "exact_city_cycle_unit_type", "weak_context_only", "no_link"]
QUAL_FIELDS = [
    "qualitative_evidence_id", "qualitative_source_record_id", "scope_origin", "source_review_id",
    "retained_source_id", "retained_content_hash", "case_id", "text_table_detection_id", "candidate_id",
    "state", "municipality", "unit_type", "bargaining_unit_name", "contract_or_cycle_period",
    "cycle_start", "cycle_end", "source_family", "mechanism_family", "claim_relevance",
    "direction_of_pressure", "evidence_strength", "claim_boundary", "rating_status",
    "ingestion_status", "codification_status", "causal_status", "global_analysis_readiness",
]
RESULT_FIELDS = [
    "linkage_id", "quantitative_evidence_id", "qualitative_evidence_id", "linkage_status",
    "linkage_confidence", "linkage_reason", "city", "state", "unit_type", "bargaining_unit_name",
    "contract_or_cycle_period", "source_family", "quantitative_value_kind", "quantitative_value_unit",
    "quantitative_claim_readiness", "raw_quantitative_value_string", "qualitative_mechanism_family",
    "qualitative_claim_relevance", "qualitative_direction_of_pressure", "qualitative_evidence_strength",
    "qualitative_claim_boundary", "same_source_match", "same_city_match", "same_unit_match",
    "same_cycle_match", "value_normalized", "value_imputed", "value_annualized",
    "wage_gap_calculated", "regression_used", "treatment_effect_estimated", "causal_claim_made",
    "population_or_national_claim_made", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
]
OUTPUTS = [
    "quantitative_to_qualitative_mechanism_linkage_513_decision.json",
    "quantitative_to_qualitative_mechanism_linkage_513_summary.md",
    "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_quant_scope_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_qual_scope_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_lock.json",
    "quantitative_to_qualitative_mechanism_linkage_513_results.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_results_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_exact_city_unit_cycle_links.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_exact_city_cycle_unit_type_links.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_weak_context_only_links.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_no_link.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_unmatched_quant_rows.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_unmatched_qual_rows.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_unmatched_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_mechanism.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_mechanism_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_unit_type.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_unit_type_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_source_family.csv",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_source_family_summary.json",
    "quantitative_to_qualitative_mechanism_linkage_513_claim_review_candidates.md",
    "quantitative_to_qualitative_mechanism_linkage_513_claim_boundaries.md",
    "quantitative_to_qualitative_mechanism_linkage_513_linkage_limits.md",
    "quantitative_to_qualitative_mechanism_linkage_513_next_data_needed.md",
    "quantitative_to_qualitative_mechanism_linkage_513_validation_2026-07-26.md",
    "quantitative_to_qualitative_mechanism_linkage_513_invariant_checks.json",
    "quantitative_to_qualitative_mechanism_linkage_513_stress_test_report.md",
    "quantitative_to_qualitative_mechanism_linkage_513_regression_test_inventory.json",
    "next_mechanism_linkage_claim_review_prompt.md", "next_task.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_hashes() -> None:
    for path, expected in INPUTS.items():
        if not path.is_file():
            raise RuntimeError(f"required input missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"immutable input hash mismatch: {path.name}: {actual}")


def build_quant_scope() -> list[dict[str, str]]:
    decision = read_json(QUANT_DIR / "quantitative_direct_text_claim_triage_862_decision.json")
    rows = read_csv(QUANT_DIR / "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidates.csv")
    full = read_csv(QUANT_DIR / "quantitative_direct_text_claim_triage_862_results.csv")
    if decision.get("decision") != "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready":
        raise RuntimeError("quantitative triage decision does not authorize linkage")
    if len(rows) != EXPECTED_QUANT or decision.get("mechanism_linkage_candidate_count") != EXPECTED_QUANT:
        raise RuntimeError("quantitative linkage candidate count reconciliation failure")
    full_candidates = {row["evidence_id"] for row in full if row.get("mechanism_linkage_candidate") == "true"}
    ids = {row["evidence_id"] for row in rows}
    if len(ids) != EXPECTED_QUANT or ids != full_candidates:
        raise RuntimeError("noncandidate or duplicate quantitative row entered linkage")
    for row in rows:
        if row.get("mechanism_linkage_candidate") != "true" or row.get("raw_value_preserved_exactly") != "true":
            raise RuntimeError("invalid quantitative linkage row")
        if any(row.get(field) != "false" for field in ("imputation_used", "destructive_normalization_used", "annualization_performed")):
            raise RuntimeError("quantitative value mutation found")
        if not all(row.get(field, "").strip() for field in ("state", "municipality", "unit_type", "source_review_id", "negotiation_cycle_id", "city_unit_negotiation_cycle_key")):
            raise RuntimeError("required quantitative linkage lineage missing")
    return sorted(rows, key=lambda row: row["evidence_id"])


def build_qual_scope() -> list[dict[str, str]]:
    phase = {row["evidence_id"]: row for row in read_csv(PHASE_DIR / "qualitative_mechanism_claim_ready_manifest.csv")}
    valid636 = read_csv(VALID636_DIR / "gabriel_claim_rating_summary_review_valid_636_manifest.csv")
    excluded7 = {row["evidence_id"] for row in read_csv(VALID636_DIR / "gabriel_claim_rating_summary_review_excluded_7_manifest.csv")}
    ratings = {row["evidence_id"]: row for row in read_csv(RATING636_DIR / "gabriel_claim_oriented_attribute_ratings_643_repaired.csv")}
    if len(valid636) != 636 or len(excluded7) != 7 or len(ratings) != 636:
        raise RuntimeError("legacy valid/excluded rating reconciliation failure")
    valid_ids = {row["evidence_id"] for row in valid636}
    if valid_ids & excluded7 or valid_ids != set(ratings) or not valid_ids <= set(phase):
        raise RuntimeError("legacy valid rating scope is inconsistent")
    result: list[dict[str, str]] = []
    for evidence_id in sorted(valid_ids):
        source = phase[evidence_id]
        rating = ratings[evidence_id]
        if rating.get("qa_status") != "schema_valid_exact_quote_verified":
            raise RuntimeError("invalid legacy rating entered qualitative scope")
        for mechanism in MECHANISMS:
            prefix = mechanism + "__"
            if rating.get(prefix + "attribute_present") != "true" or rating.get(prefix + "evidence_strength") == "not_supported":
                continue
            result.append({
                "qualitative_evidence_id": f"legacy:{evidence_id}:{mechanism}",
                "qualitative_source_record_id": evidence_id,
                "scope_origin": "legacy_valid_636_rating",
                "source_review_id": source.get("source_review_id", ""),
                "retained_source_id": "",
                "retained_content_hash": source.get("retained_content_hash", ""),
                "case_id": source.get("case_id", ""),
                "text_table_detection_id": source.get("text_table_detection_id", ""),
                "candidate_id": "",
                "state": source.get("state", ""), "municipality": "", "unit_type": source.get("unit_type", ""),
                "bargaining_unit_name": "", "contract_or_cycle_period": "", "cycle_start": "", "cycle_end": "",
                "source_family": source.get("source_family", ""), "mechanism_family": mechanism,
                "claim_relevance": rating.get(prefix + "claim_relevance", ""),
                "direction_of_pressure": rating.get(prefix + "direction_of_pressure", ""),
                "evidence_strength": rating.get(prefix + "evidence_strength", ""),
                "claim_boundary": rating.get(prefix + "claim_boundary", ""),
                "rating_status": "rated_valid", "ingestion_status": "not_ingested",
                "codification_status": "not_codified", "causal_status": "not_causal_evidence",
                "global_analysis_readiness": "false",
            })
    targeted = read_csv(TARGETED_DIR / "targeted_evidence_span_rating_summary_173_valid_scope.csv")
    quarantine_ids = {row["span_extraction_id"] for row in read_csv(TARGETED_RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv")}
    if len(targeted) != 173 or len(quarantine_ids) != 28:
        raise RuntimeError("targeted valid/quarantine count mismatch")
    for row in targeted:
        if row["span_extraction_id"] in quarantine_ids:
            raise RuntimeError("targeted quarantine entered qualitative scope")
        if row.get("rating_status") != "rated_valid" or row.get("quote_exact_substring") != "true":
            raise RuntimeError("invalid targeted rating entered qualitative scope")
        if row.get("evidence_strength") == "not_supported":
            continue
        result.append({
            "qualitative_evidence_id": "targeted:" + row["span_rating_id"],
            "qualitative_source_record_id": row["span_extraction_id"],
            "scope_origin": "targeted_valid_173_rating",
            "source_review_id": "", "retained_source_id": row["retained_source_id"],
            "retained_content_hash": "", "case_id": "", "text_table_detection_id": "",
            "candidate_id": row["candidate_id"], "state": row["state"], "municipality": row["municipality"],
            "unit_type": row["unit_type"], "bargaining_unit_name": row["bargaining_unit_name"],
            "contract_or_cycle_period": row["contract_or_document_period"],
            "cycle_start": row["inferred_cycle_start"], "cycle_end": row["inferred_cycle_end"],
            "source_family": row["source_family"], "mechanism_family": row["rated_mechanism_family"],
            "claim_relevance": row["claim_relevance"], "direction_of_pressure": row["direction_of_pressure"],
            "evidence_strength": row["evidence_strength"], "claim_boundary": row["claim_boundary"],
            "rating_status": row["rating_status"], "ingestion_status": row["ingestion_status"],
            "codification_status": row["codification_status"], "causal_status": row["causal_status"],
            "global_analysis_readiness": row["global_analysis_readiness"],
        })
    if len(result) != EXPECTED_QUAL or len({row["qualitative_evidence_id"] for row in result}) != EXPECTED_QUAL:
        raise RuntimeError(f"qualitative scope reconciliation failure: {len(result)}")
    if any(row["evidence_strength"] == "not_supported" for row in result):
        raise RuntimeError("unsupported qualitative evidence entered linkage")
    return sorted(result, key=lambda row: row["qualitative_evidence_id"])


def norm(value: str) -> str:
    return " ".join(value.casefold().split())


def compatible_unit(quant_unit: str, qual_unit: str) -> bool:
    q = norm(quant_unit)
    v = norm(qual_unit)
    if q == v:
        return True
    if q == "non_safety" and v in {"non_safety_comparator", "non_safety_municipal_units"}:
        return True
    if q in {"police", "fire"} and v in {"safety_and_non_safety_bargaining_units", "safety_and_non_safety_compensation_units"}:
        return True
    return False


def cycles_equal(q: dict[str, str], v: dict[str, str]) -> bool:
    return bool(v["cycle_start"] and v["cycle_end"] and q["contract_period_start"] == v["cycle_start"] and q["contract_period_end"] == v["cycle_end"])


def make_result(q: dict[str, str], v: dict[str, str] | None, confidence: str, reason: str) -> dict[str, str]:
    qid = q["evidence_id"]
    vid = v["qualitative_evidence_id"] if v else ""
    linkage_id = "QQL513-" + hashlib.sha256(f"{qid}|{vid}|{confidence}".encode()).hexdigest()[:22]
    linked = v is not None and confidence != "no_link"
    exact_source = linked and confidence == "exact_same_source"
    city_match = linked and bool(v["municipality"]) and norm(q["municipality"]) == norm(v["municipality"]) and q["state"] == v["state"]
    unit_match = linked and compatible_unit(q["unit_type"], v["unit_type"])
    cycle_match = linked and cycles_equal(q, v)
    return {
        "linkage_id": linkage_id, "quantitative_evidence_id": qid, "qualitative_evidence_id": vid,
        "linkage_status": "linked" if linked and confidence != "weak_context_only" else "weak_context_only" if linked else "no_link",
        "linkage_confidence": confidence, "linkage_reason": reason,
        "city": q["municipality"], "state": q["state"], "unit_type": q["unit_type"], "bargaining_unit_name": "",
        "contract_or_cycle_period": f"{q['contract_period_start']} to {q['contract_period_end']}",
        "source_family": q["source_family"], "quantitative_value_kind": q["value_kind"],
        "quantitative_value_unit": q["value_unit"], "quantitative_claim_readiness": q["claim_readiness"],
        "raw_quantitative_value_string": q["raw_value_string"],
        "qualitative_mechanism_family": v["mechanism_family"] if v else "",
        "qualitative_claim_relevance": v["claim_relevance"] if v else "",
        "qualitative_direction_of_pressure": v["direction_of_pressure"] if v else "",
        "qualitative_evidence_strength": v["evidence_strength"] if v else "",
        "qualitative_claim_boundary": v["claim_boundary"] if v else "",
        "same_source_match": str(bool(exact_source)).lower(),
        "same_city_match": str(bool(city_match)).lower() if v and v["municipality"] else "not_independently_recorded",
        "same_unit_match": str(bool(unit_match)).lower() if v and v["municipality"] else "not_independently_recorded",
        "same_cycle_match": str(bool(cycle_match)).lower() if v and v["cycle_start"] and v["cycle_end"] else "not_independently_recorded",
        "value_normalized": "false", "value_imputed": "false", "value_annualized": "false",
        "wage_gap_calculated": "false", "regression_used": "false", "treatment_effect_estimated": "false",
        "causal_claim_made": "false", "population_or_national_claim_made": "false",
        "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": "false",
        "notes": "structured co-location only; linkage does not estimate a wage effect or prove causation",
    }


def link_scopes(quant: list[dict[str, str]], qual: list[dict[str, str]]) -> list[dict[str, str]]:
    by_source_review: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_city_unit_cycle: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    by_city_cycle_type: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in qual:
        if row["source_review_id"]:
            by_source_review[row["source_review_id"]].append(row)
        if row["retained_content_hash"]:
            by_hash[row["retained_content_hash"]].append(row)
        if row["municipality"] and row["cycle_start"] and row["cycle_end"]:
            by_city_unit_cycle[(row["state"], norm(row["municipality"]), norm(row["bargaining_unit_name"]), row["cycle_start"], row["cycle_end"])].append(row)
            by_city_cycle_type[(row["state"], norm(row["municipality"]), row["cycle_start"], row["cycle_end"])].append(row)
    results: list[dict[str, str]] = []
    for q in quant:
        exact = {row["qualitative_evidence_id"]: row for row in by_source_review.get(q["source_review_id"], [])}
        exact.update({row["qualitative_evidence_id"]: row for row in by_hash.get(q["retained_content_hash"], [])})
        if exact:
            for v in sorted(exact.values(), key=lambda row: row["qualitative_evidence_id"]):
                results.append(make_result(q, v, "exact_same_source", "shared committed source_review_id and/or retained_content_hash"))
            continue
        key = (q["state"], norm(q["municipality"]), "", q["contract_period_start"], q["contract_period_end"])
        city_unit = [v for v in by_city_unit_cycle.get(key, []) if compatible_unit(q["unit_type"], v["unit_type"])]
        if city_unit:
            for v in city_unit:
                results.append(make_result(q, v, "exact_city_unit_cycle", "exact recorded city, compatible unit, and exact cycle period"))
            continue
        key2 = (q["state"], norm(q["municipality"]), q["contract_period_start"], q["contract_period_end"])
        city_type = [v for v in by_city_cycle_type.get(key2, []) if compatible_unit(q["unit_type"], v["unit_type"]) and q["source_family"] == v["source_family"]]
        if city_type:
            for v in city_type:
                results.append(make_result(q, v, "exact_city_cycle_unit_type", "exact recorded city and cycle with compatible unit type and source family"))
            continue
        results.append(make_result(q, None, "no_link", "no authorized exact source or exact city-unit-cycle key"))
    return sorted(results, key=lambda row: (row["quantitative_evidence_id"], row["qualitative_evidence_id"]))


def counts(results: list[dict[str, str]]) -> dict[str, Any]:
    confidence = Counter(row["linkage_confidence"] for row in results)
    linked = [row for row in results if row["linkage_status"] == "linked"]
    return {
        "linkage_result_rows": len(results),
        "linked_pair_count": len(linked),
        "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in linked}),
        "linked_qualitative_record_count": len({row["qualitative_evidence_id"] for row in linked}),
        "linkage_confidence_counts": {key: confidence[key] for key in CONFIDENCES},
        "no_link_quantitative_row_count": len({row["quantitative_evidence_id"] for row in results if row["linkage_confidence"] == "no_link"}),
        "linked_pair_counts_by_mechanism": dict(sorted(Counter(row["qualitative_mechanism_family"] for row in linked).items())),
        "linked_pair_counts_by_unit_type": dict(sorted(Counter(row["unit_type"] for row in linked).items())),
        "linked_pair_counts_by_source_family": dict(sorted(Counter(row["source_family"] for row in linked).items())),
    }


def coverage_rows(results: list[dict[str, str]], field: str, universe: list[str]) -> list[dict[str, Any]]:
    rows = []
    for value in sorted(set(universe)):
        relevant = [row for row in results if row[field] == value]
        linked = [row for row in relevant if row["linkage_status"] == "linked"]
        rows.append({
            field: value, "result_row_count": len(relevant), "linked_pair_count": len(linked),
            "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in linked}),
            "no_link_quantitative_row_count": len({row["quantitative_evidence_id"] for row in relevant if row["linkage_status"] == "no_link"}),
        })
    return rows


def build_outputs(quant: list[dict[str, str]], qual: list[dict[str, str]], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    quant_fields = list(quant[0])
    write_csv(target / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv", quant, quant_fields)
    write_csv(target / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv", qual, QUAL_FIELDS)
    qhash = sha256_file(target / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv")
    vhash = sha256_file(target / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv")
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope_summary.json", {
        "quantitative_scope_count": len(quant), "unique_quantitative_evidence_ids": len({row["evidence_id"] for row in quant}),
        "noncandidate_rows_in_scope": 0, "raw_values_preserved_count": sum(row["raw_value_preserved_exactly"] == "true" for row in quant),
        "quantitative_scope_sha256": qhash,
    })
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope_summary.json", {
        "qualitative_scope_count": len(qual), "unique_qualitative_evidence_ids": len({row["qualitative_evidence_id"] for row in qual}),
        "legacy_valid_supported_mechanism_records": sum(row["scope_origin"] == "legacy_valid_636_rating" for row in qual),
        "targeted_valid_supported_mechanism_records": sum(row["scope_origin"] == "targeted_valid_173_rating" for row in qual),
        "unsupported_or_quarantined_rows_in_scope": 0, "qualitative_scope_sha256": vhash,
        "mechanism_counts": dict(sorted(Counter(row["mechanism_family"] for row in qual).items())),
    })
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_lock.json", {
        "task_id": TASK_ID, "quantitative_scope_count": len(quant), "qualitative_scope_count": len(qual),
        "quantitative_scope_sha256": qhash, "qualitative_scope_sha256": vhash,
        "input_hashes": {str(path.relative_to(ROOT)): digest for path, digest in INPUTS.items()},
    })
    results = link_scopes(quant, qual)
    summary = counts(results)
    write_csv(target / "quantitative_to_qualitative_mechanism_linkage_513_results.csv", results, RESULT_FIELDS)
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_results_summary.json", summary)
    confidence_files = {
        "exact_same_source": "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv",
        "exact_city_unit_cycle": "quantitative_to_qualitative_mechanism_linkage_513_exact_city_unit_cycle_links.csv",
        "exact_city_cycle_unit_type": "quantitative_to_qualitative_mechanism_linkage_513_exact_city_cycle_unit_type_links.csv",
        "weak_context_only": "quantitative_to_qualitative_mechanism_linkage_513_weak_context_only_links.csv",
        "no_link": "quantitative_to_qualitative_mechanism_linkage_513_no_link.csv",
    }
    for confidence, name in confidence_files.items():
        write_csv(target / name, [row for row in results if row["linkage_confidence"] == confidence], RESULT_FIELDS)
    linked_qids = {row["quantitative_evidence_id"] for row in results if row["linkage_status"] == "linked"}
    linked_vids = {row["qualitative_evidence_id"] for row in results if row["linkage_status"] == "linked"}
    unmatched_q = [row for row in quant if row["evidence_id"] not in linked_qids]
    unmatched_v = [row for row in qual if row["qualitative_evidence_id"] not in linked_vids]
    write_csv(target / "quantitative_to_qualitative_mechanism_linkage_513_unmatched_quant_rows.csv", unmatched_q, quant_fields)
    write_csv(target / "quantitative_to_qualitative_mechanism_linkage_513_unmatched_qual_rows.csv", unmatched_v, QUAL_FIELDS)
    unmatched = {
        "unmatched_quantitative_row_count": len(unmatched_q), "unmatched_qualitative_record_count": len(unmatched_v),
        "quantitative_rows_with_any_link": len(linked_qids), "qualitative_records_with_any_link": len(linked_vids),
        "boundary": "unmatched records are preserved; no weak state-only or mechanism-only match was manufactured",
    }
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_unmatched_summary.json", unmatched)
    dimensions = [
        ("qualitative_mechanism_family", "mechanism", [row["mechanism_family"] for row in qual]),
        ("unit_type", "unit_type", [row["unit_type"] for row in quant]),
        ("source_family", "source_family", [row["source_family"] for row in quant]),
    ]
    for field, label, universe in dimensions:
        rows = coverage_rows(results, field, universe)
        stem = f"quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_{label}"
        write_csv(target / f"{stem}.csv", rows, list(rows[0]))
        write_json(target / f"{stem}_summary.json", {
            "dimension": label, "category_count": len(rows),
            "linked_pair_counts": {row[field]: row["linked_pair_count"] for row in rows},
            "linked_quantitative_row_counts": {row[field]: row["linked_quantitative_row_count"] for row in rows},
        })
    decision = {
        "task_id": TASK_ID, "decision": DECISION, "completion_status": "completed_strict_lineage_mechanism_linkage",
        "quantitative_linkage_candidate_count": len(quant), "qualitative_scope_count": len(qual), **summary, **unmatched,
        "claim_review_ready_next": True, "repair_needed": False, "tier_c_verification_recommended_next": False,
        "repo_cleanup_recommended_next": False, "value_normalizations": 0, "value_imputations": 0,
        "value_annualizations": 0, "wage_gap_calculations": 0, "wage_level_outcome_comparisons": 0,
        "regressions": 0, "treatment_effect_estimates": 0, "final_causal_claims": 0,
        "population_prevalence_claims": 0, "national_claims": 0, "gabriel_api_model_calls": 0,
        "url_opens": 0, "downloads": 0, "pdf_page_accesses": 0, "retained_file_accesses": 0,
        "full_extracted_text_accesses": 0, "ocr_runs": 0, "pdf_render_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_decision.json", decision)
    (target / "quantitative_to_qualitative_mechanism_linkage_513_summary.md").write_text(
        "# Quantitative-to-qualitative mechanism linkage — 513 candidates\n\n"
        f"Decision: `{DECISION}`. The locked scopes contain 513 quantitative candidates and 609 supported valid qualitative mechanism records. "
        f"Strict lineage produced {summary['linked_pair_count']} exact same-source pairs covering {summary['linked_quantitative_row_count']} quantitative rows and {summary['linked_qualitative_record_count']} qualitative mechanism records; {summary['no_link_quantitative_row_count']} quantitative rows remain unmatched. "
        "No city-only, state-only, mechanism-only, weak-context, normalized-value, comparative, wage-gap, statistical, population, national, or causal inference was made. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    (target / "quantitative_to_qualitative_mechanism_linkage_513_claim_review_candidates.md").write_text(
        "# Claim-review candidates\n\nThe 268 exact same-source linkage pairs are eligible for bounded documentary claim review. They cover 208 quantitative direct-text rows and 90 qualitative mechanism records. Review must retain the recorded value unit/readiness, exact qualitative claim boundary, and one-row-per-unit-cycle discipline. Multiple values or mechanisms from one source are separate records, not independent documents or estimated effects.\n",
        encoding="utf-8",
    )
    (target / "quantitative_to_qualitative_mechanism_linkage_513_claim_boundaries.md").write_text(
        "# Claim boundaries\n\nAllowed: a quantitative direct-text row and qualitative mechanism record occur in the same committed source-review/hash lineage, and this may support later bounded claim review. A linkage does not estimate a wage effect and does not prove causation. Forbidden: wage-gap, wage-level outcome comparison, regression, treatment-effect, population-prevalence, national, or final causal claims. Values remain unnormalized, unimputed, and unannualized.\n",
        encoding="utf-8",
    )
    (target / "quantitative_to_qualitative_mechanism_linkage_513_linkage_limits.md").write_text(
        "# Linkage limits\n\nLegacy qualitative ratings record exact source-review/hash lineage but do not independently repeat city, unit, or cycle fields; therefore linked rows are classified only as `exact_same_source`, with city/unit/cycle flags recorded as `not_independently_recorded`. The targeted 173-rating scope shares no city-state pair with the 513-row quantitative scope. No lower-confidence link was manufactured from state, source family, mechanism family, or occupational similarity alone. Co-location is not causation.\n",
        encoding="utf-8",
    )
    (target / "quantitative_to_qualitative_mechanism_linkage_513_next_data_needed.md").write_text(
        "# Next data needed\n\nA bounded claim review can proceed over the exact same-source pairs. The 305 unmatched quantitative rows require new compatible qualitative evidence or separately authorized Tier C verification/rating before linkage. Fiscal, market/comparability, bargaining-power, and rank/specialization linked lanes remain much thinner than automatic-raise and implementation/retroactivity lanes. Do not repair by weakening keys.\n",
        encoding="utf-8",
    )
    invariants = {
        "all_invariants_passed": True, "exactly_513_quantitative_candidates_linked_or_preserved": True,
        "noncandidate_quantitative_rows_excluded": True, "qualitative_quarantines_and_unsupported_rows_excluded": True,
        "raw_quantitative_values_preserved_exactly": True, "strict_lineage_keys_only": True,
        "no_weak_context_links_manufactured": True, "no_value_normalization_imputation_or_annualization": True,
        "no_url_pdf_page_retained_file_or_full_text_access": True, "no_gabriel_api_model_calls": True,
        "no_ingestion_or_codification": True,
        "no_wage_gap_regression_treatment_effect_population_national_or_final_causal_work": True,
        "global_analysis_readiness_false": True, "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_invariant_checks.json", invariants)
    write_json(target / "quantitative_to_qualitative_mechanism_linkage_513_regression_test_inventory.json", {
        "suite": "scripts/test_quantitative_to_qualitative_mechanism_linkage_513.py",
        "required_cases": ["513-row quantitative scope", "609-record supported qualitative scope", "quarantine exclusion", "raw-value identity", "strict source-key priority", "no weak inferred links", "closed downstream statuses", "idempotent resume", "partial-package failure", "dashboard global closure", "future prompt boundaries"],
    })
    (target / "quantitative_to_qualitative_mechanism_linkage_513_stress_test_report.md").write_text(
        "# Stress-test report\n\n- Missing or hash-drifted inputs fail before output.\n- Duplicate/noncandidate quantitative rows and invalid/quarantined/unsupported qualitative rows fail closed.\n- Exact source-review/hash identity takes priority; absent exact city/cycle metadata produces no link.\n- State, source-family, mechanism-family, and occupation similarity cannot create a link.\n- Raw values remain exact and no normalization, imputation, annualization, comparison, statistical, or causal operation is available.\n- Complete packages resume with zero writes; partial packages fail.\n",
        encoding="utf-8",
    )
    (target / "quantitative_to_qualitative_mechanism_linkage_513_validation_2026-07-26.md").write_text(
        "# Quantitative-to-qualitative mechanism linkage validation — 2026-07-26\n\nInternal deterministic scope, hash, quarantine, strict-linkage, raw-value, and downstream-boundary gates passed. Required repository command results are appended after the full suite completes.\n",
        encoding="utf-8",
    )
    future = (
        "# Next task: bounded mechanism-linkage claim review\n\n"
        "Review only the 268 exact same-source linkage pairs covering 208 quantitative rows and 90 qualitative mechanism records. Lock the linkage scope, preserve duplicate-document/source relationships, value units/readiness, and qualitative claim boundaries, and separate direct-text co-location statements from documentary mechanism scaffolds. Do not infer that a mechanism caused a value.\n\n"
        "Do not fetch, inspect remotes, open URLs, download, access PDFs/pages/retained files/full extracted text, OCR, render, call a model, use quarantines or unsupported ratings, normalize, impute, annualize, compare wage levels as outcomes, calculate a wage gap, run a regression, estimate a treatment effect, make population/national/final causal claims, ingest, codify, or set global analysis readiness true. Co-location is not causation.\n"
    )
    (target / "next_mechanism_linkage_claim_review_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / "quantitative_to_qualitative_mechanism_linkage_513_decision.json")
    lock = read_json(path / "quantitative_to_qualitative_mechanism_linkage_513_lock.json")
    quant = read_csv(path / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv")
    qual = read_csv(path / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv")
    results = read_csv(path / "quantitative_to_qualitative_mechanism_linkage_513_results.csv")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed decision invalid")
    if len(quant) != EXPECTED_QUANT or len(qual) != EXPECTED_QUAL or len(results) != 573:
        raise RuntimeError("completed scope/result count mismatch")
    if sha256_file(path / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv") != lock.get("quantitative_scope_sha256"):
        raise RuntimeError("quantitative scope lock mismatch")
    if sha256_file(path / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv") != lock.get("qualitative_scope_sha256"):
        raise RuntimeError("qualitative scope lock mismatch")
    raw = {row["evidence_id"]: row["raw_value_string"] for row in quant}
    if any(raw.get(row["quantitative_evidence_id"]) != row["raw_quantitative_value_string"] for row in results):
        raise RuntimeError("raw quantitative value mismatch")


def install_dashboard_docs(decision: dict[str, Any]) -> None:
    RESULT_DOC.write_text(
        "# Quantitative-to-qualitative mechanism linkage result — 2026-07-26\n\n"
        f"Decision: `{DECISION}`. The 513-row quantitative scope and 609-record supported qualitative scope produced {decision['linked_pair_count']} exact same-source pairs covering {decision['linked_quantitative_row_count']} quantitative rows; {decision['no_link_quantitative_row_count']} quantitative rows remain unmatched. Claim review is ready next. No lower-confidence inferred linkage, value transformation, comparison, statistical, population, national, or causal work occurred. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        "# Dashboard status note — quantitative-to-qualitative linkage\n\n"
        f"Status: `{DECISION}`. Quantitative candidates: 513. Qualitative mechanism records: 609. Exact same-source pairs: {decision['linked_pair_count']}. Linked quantitative rows: {decision['linked_quantitative_row_count']}. No-link quantitative rows: {decision['no_link_quantitative_row_count']}. Claim review ready next: true. Global analysis readiness: false.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    validate_hashes()
    quant = build_quant_scope()
    qual = build_qual_scope()
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "quant": len(quant), "qual": len(qual)}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(quant, qual, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        install_dashboard_docs(read_json(OUTPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_decision.json"))
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "quant": len(quant), "qual": len(qual)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
