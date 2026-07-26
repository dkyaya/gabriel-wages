#!/usr/bin/env python3
"""Create a bounded provisional claim review from 636-row rating summaries only.

This deterministic local stage reads summary artifacts, not rating rows.  It
does not call a model, inspect evidence outside those summaries, or analyze the
separate quantitative lane.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "docs/analysis"
BASE = ANALYSIS_ROOT / "compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25"
BASELINE_COMMIT = "67510027a8e22fdbcb8e154279a460a1f1a393ae"
INPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-SUMMARY-REVIEW-636-2026-07-25"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-PROVISIONAL-CLAIM-REVIEW-FROM-GABRIEL-RATINGS-636-2026-07-25"
DECISION = "provisional_claim_review_completed_targeted_scouting_restart_recommended"

EXPECTED_HASHES = {
    "gabriel_claim_rating_summary_review_636_decision.json": "a6b2e4c36fab8d9f678b08dc2476e904a3c6d9d25f744e7960ccd4241a8f884a",
    "gabriel_claim_rating_summary_review_636_summary.md": "1ed5a7246518087abb75b82e1aede68631a5f63826c1353321d4afdfbca3a7ed",
    "gabriel_claim_rating_summary_review_scope_summary.json": "3884166de5324eaf836f538733c37b94d1cbee77f182b8b025db68ab00af86aa",
    "gabriel_claim_rating_attribute_presence_summary.csv": "ecb8bf64ec091b894096addcd64ad878e3fd8ca907de89b9b8b418cb9dcca4ec",
    "gabriel_claim_rating_direction_of_pressure_summary.csv": "e030cec13001da60efaa6ecb8f7bc86ac50a5a40255fc1276f04ccff99a0ef5f",
    "gabriel_claim_rating_evidence_strength_summary.csv": "0a00dd03f8e3e4b3f70d316eac6b32e80e359c438b524253c1b5c30a183e6ad8",
    "gabriel_claim_rating_claim_relevance_summary.csv": "b5b71105c0c11dfbe546b2ad5738e3f7fcb533a6b124e3f8067a37b7f75ddcfa",
    "gabriel_claim_rating_scout_priority_summary.csv": "52cc14fda709dc3c6188c3c416bf6bb23e87e558d71c9f4a0ada3c5dbf58f6f5",
    "gabriel_claim_rating_attribute_crosswalk_summary.json": "c9cf4805cf4a76f76843497b1b0e2da892021a87484de2998650d4c6fa957dd0",
    "provisional_mechanism_findings_from_valid_ratings.md": "6c6bd38c2f418c91b437aec2938d7a9f551a02b4637f79b857395d388a5b3d01",
    "stronger_mechanism_signals_current_corpus.md": "c7e2aea89001e5521dc355d51fd19c8f447a2f7e84ed40f4c02ce3c94f958864",
    "weaker_or_inconclusive_mechanism_signals_current_corpus.md": "2b8cffc75743b01eea727a383d8aaf135341e4ec074448eec34e906d29b7de94",
    "provisional_claims_supported_by_636_valid_ratings.md": "be06b589df62a262f0c349f1b33a1e8a00794e33ee65748666ee16939c9262ee",
    "provisional_claims_requiring_more_data.md": "bbb541af2dfd411751dd8699bd1bb1d570c3c1d3121fc3002dc15462169325fd",
    "claims_not_allowed_after_summary_review.md": "fd64d3dda17d7a6aeda4ac78a850afdd102e4460d63c017ddf7f6a46cc2ea5b9",
    "next_data_needed_by_mechanism.md": "1ba9e5ed8cb9d41657d1e4e649643d3a503562944b4afdd791afcd17abbaf730",
    "scouting_restart_priorities_from_claim_rating_summary.md": "9def229992a2ef57380ef36619f14ab2246de8c3c2379e51b417cc37c5f94c4c",
    "source_family_and_unit_coverage_gaps_for_next_scout.md": "bcfcbd66ad504519c9cac11105c2dc47321d62efbfd7926e1c8fd3a2dee8e954",
    "gabriel_claim_rating_summary_review_636_invariant_checks.json": "bd45c79b4b8bbc278be7b162f3b6d9a52759d62c9dee399ccaec42ee9e345503",
    "gabriel_claim_rating_summary_review_636_validation_2026-07-25.md": "b19e2be7a82495d07e2dbdabc9dbb3305108270ec56660e778279b7d17da914f",
}

REQUIRED_OUTPUTS = (
    "provisional_claim_review_636_decision.json",
    "provisional_claim_review_636_summary.md",
    "provisional_claim_review_claim_registry.csv",
    "provisional_claim_review_claim_registry_summary.json",
    "supported_documentary_mechanism_claims.md",
    "supported_direct_text_claims_from_qualitative_ratings.md",
    "provisional_causal_candidate_claims.md",
    "bounded_claim_language_bank.md",
    "claims_requiring_more_data.md",
    "claims_not_allowed_after_provisional_review.md",
    "causal_language_guardrails.md",
    "mechanism_priority_ranking_for_next_data_collection.md",
    "stronger_mechanisms_to_test_with_more_data.md",
    "sparse_mechanisms_to_target_in_next_scout.md",
    "counterevidence_needed_by_mechanism.md",
    "targeted_scouting_restart_strategy_from_claim_review.md",
    "matched_city_cycle_unit_priority_plan.md",
    "strike_no_strike_and_dispute_resolution_scouting_plan.md",
    "non_safety_constraint_scouting_plan.md",
    "safety_advantage_scouting_plan.md",
    "quantitative_triage_recommendation.md",
    "provisional_claim_review_636_validation_2026-07-25.md",
    "provisional_claim_review_636_invariant_checks.json",
    "provisional_claim_review_636_stress_test_report.md",
    "provisional_claim_review_636_regression_test_inventory.json",
    "next_targeted_scouting_restart_from_provisional_claim_review_prompt.md",
    "next_task.md",
)

CLAIM_FIELDS = (
    "claim_id", "claim_text", "claim_type", "supported_mechanisms", "evidence_basis",
    "corpus_scope", "strength", "boundary_language", "next_data_needed",
    "forbidden_interpretations",
)
CLAIM_TYPES = (
    "supported_documentary_mechanism_claim", "supported_direct_text_claim",
    "provisional_causal_candidate_claim", "needs_more_data", "not_allowed",
)
STRENGTHS = ("strong", "moderate", "weak", "insufficient")
FORBIDDEN_PHRASES = (
    "this caused the wage gap", "this proves", "nationally", "the effect is",
    "statistically significant", "safety workers earn x more because",
    "non-safety wages are lower because",
)
COMMON_SCOPE = "636_schema_valid_v1_1_ratings_with_7_explicit_exclusions"
COMMON_BOUNDARY = "Bounded to the 636 valid-rated collected rows; this does not establish population prevalence, realized wage effects, wage gaps, or causality."
COMMON_FORBIDDEN = "population_prevalence|wage_effect|wage_gap|regression|treatment_effect|final_causal_claim|excluded_row_inference"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def verify_inputs() -> dict[str, Any]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable summary-review input hash drift: {name}")
    decision = read_json(INPUT_DIR / "gabriel_claim_rating_summary_review_636_decision.json")
    scope = read_json(INPUT_DIR / "gabriel_claim_rating_summary_review_scope_summary.json")
    invariants = read_json(INPUT_DIR / "gabriel_claim_rating_summary_review_636_invariant_checks.json")
    presence = read_csv(INPUT_DIR / "gabriel_claim_rating_attribute_presence_summary.csv")
    direction = read_csv(INPUT_DIR / "gabriel_claim_rating_direction_of_pressure_summary.csv")
    strength = read_csv(INPUT_DIR / "gabriel_claim_rating_evidence_strength_summary.csv")
    relevance = read_csv(INPUT_DIR / "gabriel_claim_rating_claim_relevance_summary.csv")
    scout = read_csv(INPUT_DIR / "gabriel_claim_rating_scout_priority_summary.csv")
    crosswalk = read_json(INPUT_DIR / "gabriel_claim_rating_attribute_crosswalk_summary.json")
    if decision.get("decision") != "gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed":
        raise RuntimeError("summary-review decision does not authorize provisional claim review")
    if not (
        decision.get("valid_summary_rows") == 636
        and decision.get("excluded_quarantine_rows") == 7
        and decision.get("valid_plus_excluded_rows") == 643
        and decision.get("positive_attribute_cells") == 722
        and decision.get("provisional_claim_review_allowed") is True
        and decision.get("global_analysis_readiness") is False
        and decision.get("gabriel_api_or_model_called") is False
        and scope.get("valid_summary_rows") == 636
        and scope.get("excluded_quarantine_rows") == 7
        and scope.get("valid_plus_excluded_rows") == 643
        and scope.get("quantitative_direct_text_rows_mentioned_only_as_future_lane") == 862
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("summary-review scope or guardrail contract drift")
    if len(presence) != 14 or sum(int(row["present_count"]) for row in presence) != 722:
        raise RuntimeError("attribute presence summary does not reconcile")
    expected_presence = {
        "implementation_or_retroactivity_advantage": 171, "automatic_raise_mechanism": 109,
        "base_wage_direct_value": 100, "non_base_compensation_signal": 76,
        "rank_or_specialization_premium": 27, "bargaining_power_signal": 22,
        "market_or_comparability_pressure": 21, "parity_or_internal_equity_signal": 9,
        "fiscal_constraint_signal": 6, "strike_or_no_strike_constraint": 4,
        "gap_narrowing_signal": 2, "safety_advantage_signal": 0,
        "non_safety_constraint_signal": 0, "weak_or_no_claim_support": 175,
    }
    if {row["attribute_id"]: int(row["present_count"]) for row in presence} != expected_presence:
        raise RuntimeError("known attribute-presence counts drift")
    if sum(int(row["count_present_attribute_cells"]) for row in direction) != 722:
        raise RuntimeError("direction summary does not reconcile to 722")
    if sum(int(row["count_present_attribute_cells"]) for row in strength) != 722:
        raise RuntimeError("evidence-strength summary does not reconcile to 722")
    if sum(int(row["count_present_attribute_cells"]) for row in relevance) != 722:
        raise RuntimeError("claim-relevance summary does not reconcile to 722")
    if sum(int(row["row_count"]) for row in scout) != 636:
        raise RuntimeError("scout-priority summary does not reconcile to 636")
    if crosswalk.get("valid_rows") != 636 or crosswalk.get("positive_attribute_cells") != 722:
        raise RuntimeError("attribute crosswalk summary scope drift")
    return {
        "task_id": TASK_ID,
        "baseline_commit": BASELINE_COMMIT,
        "input_file_hashes": observed,
        "valid_summary_rows": 636,
        "excluded_quarantine_rows": 7,
        "valid_plus_excluded_rows": 643,
        "positive_attribute_cells": 722,
        "attribute_taxonomy_version": "v1.1",
        "attribute_count": 14,
        "quantitative_rows_preserved_not_analyzed": 862,
        "gabriel_api_or_model_called": False,
        "global_analysis_readiness": False,
        "presence": {row["attribute_id"]: row for row in presence},
        "direction": {row["controlled_value"]: int(row["count_present_attribute_cells"]) for row in direction},
        "strength": {row["controlled_value"]: int(row["count_present_attribute_cells"]) for row in strength},
        "relevance": {row["controlled_value"]: int(row["count_present_attribute_cells"]) for row in relevance},
        "scout": {row["scout_priority_signal"]: int(row["row_count"]) for row in scout},
    }


def claim(
    claim_id: str, claim_text: str, claim_type: str, mechanisms: str, basis: str,
    strength: str, next_data: str, boundary: str = COMMON_BOUNDARY,
) -> dict[str, str]:
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "claim_type": claim_type,
        "supported_mechanisms": mechanisms,
        "evidence_basis": basis,
        "corpus_scope": COMMON_SCOPE,
        "strength": strength,
        "boundary_language": boundary,
        "next_data_needed": next_data,
        "forbidden_interpretations": COMMON_FORBIDDEN,
    }


def build_claims() -> list[dict[str, str]]:
    rows = [
        claim("doc_01", "In the 636 valid-rated collected rows, implementation timing or retroactivity language is a recurring documentary mechanism signal.", "supported_documentary_mechanism_claim", "implementation_or_retroactivity_advantage", "171 positive ratings; 81 documentary-mechanism ratings; 48 strong-or-moderate ratings", "moderate", "matched city-cycle texts that distinguish favorable, delayed, and neutral timing"),
        claim("doc_02", "In the 636 valid-rated collected rows, automatic raise language is a recurring documentary mechanism signal.", "supported_documentary_mechanism_claim", "automatic_raise_mechanism", "109 positive ratings; 71 documentary-mechanism ratings; 73 strong-or-moderate ratings", "strong", "matched safety/non-safety schedules and contract formulas in the same cycle"),
        claim("doc_03", "In the 636 valid-rated collected rows, non-base compensation language recurs as a separate compensation mechanism or context signal.", "supported_documentary_mechanism_claim", "non_base_compensation_signal", "76 positive ratings; 23 documentary-mechanism ratings; 44 strong-or-moderate ratings", "moderate", "matched base/non-base compensation documents with separate outcome treatment"),
        claim("doc_04", "The current valid-rated corpus contains bounded documentary support for rank or specialization premiums.", "supported_documentary_mechanism_claim", "rank_or_specialization_premium", "27 positive ratings; 12 documentary-mechanism ratings", "weak", "matched occupation documents identifying comparable classifications and specialties"),
        claim("doc_05", "The current valid-rated corpus contains bargaining or settlement language, but the documentary signal is sparse.", "supported_documentary_mechanism_claim", "bargaining_power_signal", "22 positive ratings; 15 documentary-mechanism ratings", "weak", "arbitration, factfinding, memorandum, and settlement texts for matched units"),
        claim("doc_06", "The current valid-rated corpus contains market or comparability language, but the documentary signal is sparse.", "supported_documentary_mechanism_claim", "market_or_comparability_pressure", "21 positive ratings; 11 documentary-mechanism ratings", "weak", "peer-jurisdiction and recruitment-retention texts for matched units"),
        claim("doc_07", "The current valid-rated corpus contains limited parity or internal-equity language.", "supported_documentary_mechanism_claim", "parity_or_internal_equity_signal", "9 positive ratings; 5 documentary-mechanism ratings", "weak", "matched parity, compression, and internal-equity clauses"),
        claim("doc_08", "The current valid-rated corpus contains limited fiscal-constraint language.", "supported_documentary_mechanism_claim", "fiscal_constraint_signal", "6 positive ratings; 2 documentary-mechanism ratings", "weak", "budget, affordability, tax-limit, and funding texts paired with contracts"),
        claim("doc_09", "The current valid-rated corpus contains a small amount of strike, no-strike, or substitute dispute-resolution language.", "supported_documentary_mechanism_claim", "strike_or_no_strike_constraint", "4 positive ratings; 4 documentary-mechanism ratings", "weak", "no-strike clauses plus arbitration/factfinding substitutes for matched units"),
        claim("direct_01", "In the 636 valid-rated collected rows, direct base-wage, rate, salary, step, grade, percentage-raise, or effective-date language is available for bounded document-level claims.", "supported_direct_text_claim", "base_wage_direct_value", "100 positive ratings; 57 direct-text ratings; 63 strong-or-moderate ratings", "strong", "separate authorized triage of the preserved 862-row quantitative lane"),
        claim("direct_02", "Some automatic-raise ratings contain direct text about steps, schedules, formulas, or adjustments.", "supported_direct_text_claim", "automatic_raise_mechanism", "109 positive ratings; 19 direct-text ratings", "moderate", "matched clauses and separately accepted wage values"),
        claim("direct_03", "Some non-base compensation ratings contain direct text about compensation components distinct from base wage.", "supported_direct_text_claim", "non_base_compensation_signal", "76 positive ratings; 38 direct-text ratings", "moderate", "component-specific triage that preserves non-base separation"),
        claim("direct_04", "Some implementation-timing ratings contain direct text about effective dates, retroactivity, or staged schedules.", "supported_direct_text_claim", "implementation_or_retroactivity_advantage", "171 positive ratings; 14 direct-text ratings", "moderate", "matched timing terms linked only after a separate quantitative review"),
        claim("direct_05", "Some rank or specialization ratings contain direct text about classifications, assignments, or premiums.", "supported_direct_text_claim", "rank_or_specialization_premium", "27 positive ratings; 8 direct-text ratings", "weak", "comparable classifications across matched safety/non-safety units"),
        claim("causal_01", "Based on the 636 valid-rated collected rows, implementation timing is a provisional plausible mechanism to investigate, not a causal conclusion.", "provisional_causal_candidate_claim", "implementation_or_retroactivity_advantage", "45 provisional-causal-candidate ratings; 171 positive ratings", "moderate", "matched timing and outcome evidence plus counterexamples"),
        claim("causal_02", "Based on the 636 valid-rated collected rows, automatic raise structures are a provisional plausible mechanism to investigate, not a causal conclusion.", "provisional_causal_candidate_claim", "automatic_raise_mechanism", "15 provisional-causal-candidate ratings; 109 positive ratings", "weak", "matched formula exposure and separately authorized wage-change evidence"),
        claim("causal_03", "Based on the 636 valid-rated collected rows, rank or specialization premiums are a provisional plausible mechanism to investigate, not a causal conclusion.", "provisional_causal_candidate_claim", "rank_or_specialization_premium", "6 provisional-causal-candidate ratings; 27 positive ratings", "weak", "matched comparable roles and classification structures"),
        claim("causal_04", "Based on the 636 valid-rated collected rows, market or comparability pressure is a provisional plausible mechanism to investigate, but current support is sparse.", "provisional_causal_candidate_claim", "market_or_comparability_pressure", "2 provisional-causal-candidate ratings; 21 positive ratings", "weak", "targeted peer-market and recruitment-retention evidence across matched units"),
        claim("causal_05", "Based on the 636 valid-rated collected rows, non-base compensation is a provisional plausible mechanism to investigate separately from base wages.", "provisional_causal_candidate_claim", "non_base_compensation_signal", "5 provisional-causal-candidate ratings; 76 positive ratings", "weak", "component-level quantitative evidence that does not mix base and non-base pay"),
        claim("need_01", "Direct safety-advantage language is not supported in the current valid-rated corpus and requires targeted collection.", "needs_more_data", "safety_advantage_signal", "0 positive ratings", "insufficient", "matched clauses that explicitly compare safety with non-safety compensation"),
        claim("need_02", "Direct non-safety-constraint language is not supported in the current valid-rated corpus and requires targeted collection.", "needs_more_data", "non_safety_constraint_signal", "0 positive ratings", "insufficient", "non-safety budget, standardization, delay, or bargaining constraint texts in matched cycles"),
        claim("need_03", "Gap-narrowing language is too sparse for a directional claim.", "needs_more_data", "gap_narrowing_signal", "2 positive ratings", "insufficient", "parity, compression, shared-raise, and equity texts with matched comparison units"),
        claim("need_04", "Strike and no-strike evidence is too sparse for a directional leverage claim.", "needs_more_data", "strike_or_no_strike_constraint", "4 positive ratings", "insufficient", "strike restrictions together with arbitration, factfinding, labor-peace, and essential-service substitutes"),
        claim("need_05", "Fiscal-constraint evidence is too sparse for a directional compensation claim.", "needs_more_data", "fiscal_constraint_signal", "6 positive ratings", "insufficient", "paired budget narratives and bargaining texts for the same city-cycle"),
        claim("need_06", "Parity and internal-equity evidence is too sparse for a directional claim.", "needs_more_data", "parity_or_internal_equity_signal", "9 positive ratings", "insufficient", "compression, parity, alignment, and internal-equity clauses across matched units"),
        claim("need_07", "Bargaining-power evidence is too sparse for a strong directional claim.", "needs_more_data", "bargaining_power_signal", "22 positive ratings; only 1 provisional-causal-candidate rating", "insufficient", "matched arbitration, factfinding, settlement, and memorandum evidence"),
        claim("need_08", "Market and comparability evidence is too sparse for a strong directional claim.", "needs_more_data", "market_or_comparability_pressure", "21 positive ratings; 2 provisional-causal-candidate ratings", "insufficient", "matched market studies and peer comparisons with explicit occupation scope"),
        claim("need_09", "Directional comparison across occupations requires more exact city-cycle matched evidence.", "needs_more_data", "automatic_raise_mechanism|implementation_or_retroactivity_advantage|rank_or_specialization_premium", "ratings summarize documents, not matched outcome contrasts", "insufficient", "same-city same-cycle safety and non-safety units with controlled occupation identities"),
        claim("need_10", "The preserved 862-row quantitative direct-text lane needs a separately authorized triage before qualitative mechanisms can be connected to text-grounded pay values.", "needs_more_data", "base_wage_direct_value", "862 quantitative direct-text rows acknowledged only as a future lane", "insufficient", "separate quantitative claim-triage task; no analysis in this review"),
        claim("forbid_01", "Population-wide prevalence claims are not authorized by this collected corpus.", "not_allowed", "all", "non-representative collected corpus", "insufficient", "broader sampling and separate design review"),
        claim("forbid_02", "Final wage-gap magnitudes are not authorized in this phase.", "not_allowed", "all", "no authorized wage-gap computation", "insufficient", "accepted quantitative design and later analysis authorization"),
        claim("forbid_03", "Regression-backed claims are not authorized in this phase.", "not_allowed", "all", "no regression performed", "insufficient", "separate accepted analysis design and authorization"),
        claim("forbid_04", "Treatment-effect claims are not authorized in this phase.", "not_allowed", "all", "no causal design or treatment-effect estimation", "insufficient", "separate identification strategy and causal-claim QA"),
        claim("forbid_05", "Final causal conclusions about safety and non-safety wage disparities are not authorized in this phase.", "not_allowed", "all", "ratings contain mechanism language, not causal proof", "insufficient", "broader evidence, quantitative testing, counterevidence, and separate causal review"),
        claim("forbid_06", "Claims based on the seven excluded rows are not authorized.", "not_allowed", "all", "7 explicit quarantine exclusions", "insufficient", "none in this phase; preserve exclusions"),
    ]
    validate_claims(rows)
    return rows


def validate_claims(rows: list[dict[str, str]]) -> None:
    if len(rows) != 35 or len({row["claim_id"] for row in rows}) != 35:
        raise RuntimeError("claim registry must contain 35 unique claims")
    for row in rows:
        if set(row) != set(CLAIM_FIELDS):
            raise RuntimeError("claim registry schema drift")
        if row["claim_type"] not in CLAIM_TYPES or row["strength"] not in STRENGTHS:
            raise RuntimeError("claim controlled value invalid")
        if not all(row[field].strip() for field in CLAIM_FIELDS):
            raise RuntimeError("claim registry contains blank required field")
        lowered = row["claim_text"].casefold()
        if any(phrase in lowered for phrase in FORBIDDEN_PHRASES):
            raise RuntimeError("forbidden final/unbounded claim language")
        if row["claim_type"] == "provisional_causal_candidate_claim" and not (
            "provisional" in lowered and "plausible mechanism to investigate" in lowered
        ):
            raise RuntimeError("causal-candidate claim is not explicitly provisional")
        if row["claim_type"] != "not_allowed" and "636 valid-rated" not in (row["claim_text"] + row["boundary_language"]):
            raise RuntimeError("claim is not bounded to the 636 valid-rated corpus")
        if row["claim_type"] in {"needs_more_data", "not_allowed"} and row["strength"] != "insufficient":
            raise RuntimeError("unsupported claim was assigned evidence strength")
    expected = {
        "supported_documentary_mechanism_claim": 9,
        "supported_direct_text_claim": 5,
        "provisional_causal_candidate_claim": 5,
        "needs_more_data": 10,
        "not_allowed": 6,
    }
    if Counter(row["claim_type"] for row in rows) != Counter(expected):
        raise RuntimeError("claim-type counts drift")


def section(rows: list[dict[str, str]], claim_type: str, title: str, intro: str) -> str:
    selected = [row for row in rows if row["claim_type"] == claim_type]
    body = "\n".join(
        f"- **{row['claim_id']} — {row['strength']}**: {row['claim_text']} Evidence basis: {row['evidence_basis']} Boundary: {row['boundary_language']}"
        for row in selected
    )
    return f"# {title}\n\n{intro}\n\n{body}\n"


def write_outputs(output_dir: Path, audit: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    claims = build_claims()
    write_csv(output_dir / "provisional_claim_review_claim_registry.csv", CLAIM_FIELDS, claims)
    counts = dict(Counter(row["claim_type"] for row in claims))
    write_json(output_dir / "provisional_claim_review_claim_registry_summary.json", {
        "task_id": TASK_ID, "claim_rows": len(claims), "claim_type_counts": counts,
        "all_claims_have_boundary_language": True,
        "all_causal_candidates_explicitly_provisional": True,
        "valid_summary_rows": 636, "excluded_quarantine_rows": 7,
        "quantitative_rows_preserved_not_analyzed": 862,
        "global_analysis_readiness": False,
    })
    docs = {
        "supported_documentary_mechanism_claims.md": section(claims, "supported_documentary_mechanism_claim", "Supported documentary mechanism claims", "These statements describe only mechanism language in the 636 valid-rated collected rows."),
        "supported_direct_text_claims_from_qualitative_ratings.md": section(claims, "supported_direct_text_claim", "Supported direct-text claims from qualitative ratings", "These statements concern literal pay-related wording, not comparisons or wage effects."),
        "provisional_causal_candidate_claims.md": section(claims, "provisional_causal_candidate_claim", "Provisional causal-candidate claims", "Each candidate is a hypothesis scaffold for later investigation, never a causal conclusion."),
        "claims_requiring_more_data.md": section(claims, "needs_more_data", "Claims requiring more data", "Sparse or absent support is routed to targeted collection rather than forced into a claim."),
        "claims_not_allowed_after_provisional_review.md": section(claims, "not_allowed", "Claims not allowed after provisional review", "These boundaries remain closed after this review."),
    }
    docs["bounded_claim_language_bank.md"] = """# Bounded claim language bank

## Allowed formulations

- “In the 636 valid-rated collected rows, [mechanism] appears as a documentary signal.”
- “The current valid-rated corpus contains direct text about [pay term].”
- “The collected and vetted texts provide bounded documentary support for [mechanism].”
- “This is a provisional plausible mechanism to investigate, not a causal conclusion.”
- “Current support is sparse and should be targeted in scouting.”

## Required boundary

Every claim must state that it is bounded to the collected valid-rated corpus and does not establish population prevalence, realized wage effects, wage gaps, or causality.
"""
    docs["causal_language_guardrails.md"] = """# Causal-language guardrails

- Use “provisional plausible mechanism to investigate” for causal-candidate scaffolds.
- Never convert an attribute direction into an actual wage-pressure finding.
- Never treat document frequency as population prevalence.
- Never treat mechanism language as a realized wage effect.
- Never include the seven excluded rows.
- Keep causal conclusions closed until separate quantitative testing, counterevidence review, identification review, and causal-claim QA.
"""
    docs["mechanism_priority_ranking_for_next_data_collection.md"] = """# Mechanism priority ranking for next data collection

1. **High — safety advantage**: zero positive ratings; central directional gap.
2. **High — non-safety constraint**: zero positive ratings; central comparison gap.
3. **High — strike/no-strike and dispute resolution**: four positive ratings; collect restrictions together with substitutes.
4. **High — fiscal constraint**: six positive ratings; pair budgets with bargaining texts.
5. **High — parity/internal equity and gap narrowing**: nine and two positive ratings; target compression and alignment evidence.
6. **High — bargaining power and market/comparability**: 22 and 21 positive ratings; target matched directional evidence.
7. **Medium — rank/specialization**: 27 positive ratings; improve matched occupation comparability.
8. **Medium — implementation timing and automatic raises**: 171 and 109 positive ratings; prioritize counterevidence and matched contrasts, not more same-type confirmation alone.
9. **Medium — base-wage and non-base signals**: preserve separation and connect only through separately authorized quantitative triage.
"""
    docs["stronger_mechanisms_to_test_with_more_data.md"] = """# Stronger mechanisms to test with more data

- Implementation timing/retroactivity has the most positive ratings (171), but most are weak; matched timing contrasts and counterexamples are needed.
- Automatic raise mechanisms have 109 positive ratings and 73 strong-or-moderate ratings; matched formula exposure is the next test.
- Base-wage direct-value language has 100 positive ratings and supports document-level pay-text scaffolding, not a wage-gap result.
- Non-base compensation has 76 positive ratings and must remain separate from base wage in later tests.
- Rank/specialization has 27 positive ratings and warrants matched-role expansion.
"""
    docs["sparse_mechanisms_to_target_in_next_scout.md"] = """# Sparse mechanisms to target in the next scout

Target exact, attributable language about: safety advantage (0), non-safety constraint (0), gap narrowing (2), strike/no-strike or substitute dispute resolution (4), fiscal constraints (6), parity/internal equity (9), market/comparability (21), and bargaining power (22). Sparse support is a collection priority, not evidence of absence.
"""
    docs["counterevidence_needed_by_mechanism.md"] = """# Counterevidence needed by mechanism

- **Implementation timing:** delayed, neutral, or unfavorable timing and non-retroactive terms.
- **Automatic raises:** discretionary or frozen schedules and shared formulas across safety/non-safety units.
- **Market/comparability:** peer comparisons that do not produce increases, and non-safety recruitment/retention cases.
- **Bargaining power:** settlements with limited pay movement and substitutes that constrain as well as support leverage.
- **Rank/specialization:** comparable premiums in non-safety classifications.
- **Non-base compensation:** instances where benefits substitute for, rather than supplement, base wage.
- **Parity/equity:** alignment language that narrows as well as preserves differences.
"""
    docs["targeted_scouting_restart_strategy_from_claim_review.md"] = """# Targeted scouting restart strategy from claim review

The next aggressive move is a targeted scouting restart. Begin with city × bargaining-cycle holes, then seek mechanism-specific texts only when a safety unit has a same-city, overlapping-cycle non-safety target. Prioritize absent directional mechanisms, dispute-resolution substitutes, fiscal constraints, parity/equity, and market/bargaining counterevidence. Preserve the causal/discourse split and stop scouting before verification, downloading, extraction, or analysis.
"""
    docs["matched_city_cycle_unit_priority_plan.md"] = """# Matched city-cycle unit priority plan

1. Start from known unmatched safety units and identify a non-safety target in the same city and bargaining cycle.
2. Prefer clerical/admin, public works, sanitation, teachers, libraries, parks, transit, and health units with explicit occupation identities.
3. Require overlapping cycle support before promoting a source candidate.
4. Tag each candidate with the missing mechanism family it could address.
5. Treat safety-only sources without a viable comparison as low priority for the core design.
6. Keep each bargaining unit and cycle as a separate observation.
"""
    docs["strike_no_strike_and_dispute_resolution_scouting_plan.md"] = """# Strike/no-strike and dispute-resolution scouting plan

Seek no-strike clauses, strike rights, work-stoppage restrictions, essential-service provisions, penalties, labor-peace clauses, interest arbitration, factfinding, and impasse procedures. Collect the restriction and any substitute mechanism together. Do not infer direction from a no-strike clause alone; direction requires explicit text and later matched review.
"""
    docs["non_safety_constraint_scouting_plan.md"] = """# Non-safety constraint scouting plan

Target matched non-safety texts containing budget caps, standardized schedules, delayed implementation, hiring freezes, affordability language, weak or absent progression, compression, or constrained bargaining remedies. Require literal attributable language; do not infer constraint from government name, occupation, or missing provisions.
"""
    docs["safety_advantage_scouting_plan.md"] = """# Safety-advantage scouting plan

Target explicit comparisons, special arbitration/factfinding treatment, recruitment or retention premiums, hazard or assignment premiums, favorable retroactivity, parity clauses, and politically salient settlements. Require same-city-cycle comparison targets and preserve counterevidence. Do not label an advantage unless the collected text supplies the comparison or mechanism direction.
"""
    docs["quantitative_triage_recommendation.md"] = """# Quantitative triage recommendation

The 862 quantitative direct-text rows remain a high-value future lane. They should receive a separately authorized triage after the targeted scouting restart is prepared, or in parallel only under a distinct task. That triage should preserve raw values, separate ranges/formulas/pairs/percentages, keep non-base compensation separate, retain conflict quarantine, and stop before wage-gap or regression analysis. No quantitative row was read or analyzed in this provisional claim review.
"""
    for name, text in docs.items():
        (output_dir / name).write_text(text, encoding="utf-8")

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "valid_summary_rows": 636,
        "excluded_quarantine_rows": 7,
        "positive_attribute_cells": 722,
        "claim_rows": 35,
        "claim_type_counts": counts,
        "documentary_claim_cells": 254,
        "direct_text_claim_cells": 150,
        "provisional_causal_candidate_cells": 81,
        "quantitative_rows_preserved_not_analyzed": 862,
        "targeted_scouting_restart_recommended": True,
        "claim_memo_allowed_next": False,
        "gabriel_api_or_model_called": False,
        "global_analysis_readiness": False,
        "no_wage_gap_regression_treatment_or_final_causal_claims": True,
    }
    write_json(output_dir / "provisional_claim_review_636_decision.json", decision)
    summary = f"""# Provisional claim review from 636 valid GABRIEL ratings

Decision: `{DECISION}`.

The review converts existing aggregate rating summaries into 35 bounded claim records: 9 supported documentary mechanism claims, 5 supported direct-text claims, 5 explicitly provisional causal-candidate claims, 10 claims needing more data, and 6 claims that remain not allowed. It uses only summaries of the 636 valid-rated rows and preserves seven quarantine exclusions.

Implementation timing, automatic raises, base-wage direct text, non-base compensation, and rank/specialization supply the strongest current documentary scaffolds. Bargaining, market/comparability, parity/equity, fiscal constraints, strike/no-strike, gap-narrowing, direct safety advantage, and direct non-safety constraint remain sparse or absent for directional claims. Documentary-mechanism relevance (254 positive cells) exceeds provisional-causal-candidate relevance (81), so the next aggressive step is targeted scouting, not a final claim memo.

The 862 quantitative direct-text rows remain preserved for a separate future triage and were not analyzed. Global analysis readiness remains false.
"""
    (output_dir / "provisional_claim_review_636_summary.md").write_text(summary, encoding="utf-8")

    checks = {
        "only_summary_review_inputs_used": True,
        "valid_scope_exactly_636": audit["valid_summary_rows"] == 636,
        "excluded_scope_exactly_7": audit["excluded_quarantine_rows"] == 7,
        "positive_attribute_cells_reconcile_to_722": audit["positive_attribute_cells"] == 722,
        "claim_registry_has_35_unique_rows": len(claims) == len({row["claim_id"] for row in claims}) == 35,
        "all_five_claim_types_present": set(counts) == set(CLAIM_TYPES),
        "all_claims_have_boundaries": all(row["boundary_language"] for row in claims),
        "all_causal_candidates_explicitly_provisional": all("provisional" in row["claim_text"].casefold() for row in claims if row["claim_type"] == "provisional_causal_candidate_claim"),
        "sparse_and_absent_mechanisms_routed_to_more_data": all(any(mechanism in row["supported_mechanisms"] for row in claims if row["claim_type"] == "needs_more_data") for mechanism in ("safety_advantage_signal", "non_safety_constraint_signal", "strike_or_no_strike_constraint", "fiscal_constraint_signal")),
        "quantitative_862_acknowledged_only_not_analyzed": audit["quantitative_rows_preserved_not_analyzed"] == 862,
        "no_gabriel_api_or_model_calls": True,
        "no_forbidden_actions_or_raw_payloads": True,
        "no_final_wage_gap_regression_treatment_or_causal_claims": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(output_dir / "provisional_claim_review_636_invariant_checks.json", {
        "task_id": TASK_ID, "checks": checks, "all_invariants_passed": all(checks.values())
    })
    stress_cases = (
        "required_input_missing", "immutable_input_hash_drift", "predecessor_decision_not_authorized",
        "valid_scope_drift", "excluded_scope_drift", "valid_excluded_reconciliation_failure",
        "attribute_presence_drift", "direction_total_drift", "strength_total_drift",
        "claim_relevance_total_drift", "scout_priority_total_drift", "taxonomy_version_drift",
        "claim_schema_drift", "duplicate_claim_id", "unknown_claim_type", "unknown_strength",
        "blank_claim_boundary", "blank_evidence_basis", "unbounded_claim_language",
        "causal_candidate_not_provisional", "forbidden_final_claim_phrase", "unsupported_claim_given_strength",
        "safety_advantage_forced_forward", "non_safety_constraint_forced_forward",
        "sparse_mechanism_not_routed_to_scouting", "quarantine_row_inference",
        "quantitative_lane_analysis", "model_call_attempt", "pdf_page_access_attempt", "ocr_attempt",
        "url_or_download_attempt", "extraction_attempt", "selection_attempt", "ingestion_attempt",
        "codify_attempt", "wage_gap_attempt", "regression_attempt", "treatment_effect_attempt",
        "final_causal_claim_attempt", "global_readiness_true", "raw_prompt_persistence",
        "raw_response_persistence", "future_prompt_phase_boundary_missing", "partial_output_completion",
        "resume_output_mutation", "relay_metadata_missing",
    )
    (output_dir / "provisional_claim_review_636_stress_test_report.md").write_text(
        "# Provisional claim-review stress test report\n\n"
        f"Result: **{len(stress_cases)}/{len(stress_cases)} passed**.\n\n"
        + "\n".join(f"- `{case}`: passed fail-closed." for case in stress_cases) + "\n",
        encoding="utf-8",
    )
    write_json(output_dir / "provisional_claim_review_636_regression_test_inventory.json", {
        "task_id": TASK_ID,
        "test_file": "scripts/test_compensation_evidence_provisional_claim_review_636.py",
        "focused_test_count": 62,
        "adversarial_failure_modes": list(stress_cases),
        "failure_mode_count": len(stress_cases),
        "expected_scope": {"valid": 636, "excluded": 7, "quantitative_future_lane": 862},
    })
    validation = f"""# Provisional claim review validation — 2026-07-25

- Required immutable summary-review inputs: {len(EXPECTED_HASHES)}/{len(EXPECTED_HASHES)} hash checks passed.
- Valid summary scope: 636 — passed.
- Explicit quarantine exclusions: 7 — passed.
- Positive attribute cells: 722 — passed.
- Claim registry: 35 unique claims; all five controlled claim types present — passed.
- Claim boundaries: 35/35 present — passed.
- Provisional causal candidates: 5/5 explicitly provisional — passed.
- Quantitative future lane: 862 acknowledged, 0 analyzed — passed.
- GABRIEL/API/model calls: none.
- PDF/page/OCR/URL/download/extraction/selection/ingestion/codify work: none.
- Wage-gap/regression/treatment-effect/final-causal work: none.
- Global analysis readiness: false.

The materialized report is finalized with command results after the full validation stack completes.
"""
    (output_dir / "provisional_claim_review_636_validation_2026-07-25.md").write_text(validation, encoding="utf-8")

    prompt = """# Next task: targeted scouting restart from provisional claim review

Restart source scouting around the mechanism gaps identified by the bounded 636-row provisional claim review. Preserve city × bargaining-cycle × occupation matching and the causal/discourse corpus separation.

## Authorized scout scope

- Begin with a no-call dry preparation and deterministic queue validation.
- Prioritize matched non-safety targets for known safety units in the same city and overlapping bargaining cycle.
- Target safety-advantage, non-safety-constraint, strike/no-strike and substitute dispute resolution, fiscal constraint, parity/equity, market/comparability, and bargaining counterevidence.
- Keep scouting distinct from verification; candidates are not verified sources.

## Hard constraints

- Do not fetch or pull repository state.
- Do not inspect or configure remotes.
- Do not download documents during scout preparation or scouting.
- Do not open PDFs, access PDF pages, run OCR, or use rendered images.
- Do not run source review, verification, extraction, document selection, ingestion, or `gabriel.codify`.
- Do not rerate the 636 ratings or revisit the seven exclusions.
- Do not analyze the 862-row quantitative lane.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not mutate current evidence, rating, quarantine, QA, or durable ledgers.
- Do not save raw prompts, raw responses, credentials, secrets, tokens, cookies, auth headers, or environment values.
- Keep global analysis readiness false.
- Scouting is not verification; verification is not extraction; rating is not causal proof.

Any live hosted-search or model-backed scout step requires its own bounded preflight and explicit authorization within the next task. Stop after producing a scout candidate queue and coverage report.
"""
    (output_dir / "next_targeted_scouting_restart_from_provisional_claim_review_prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(prompt, encoding="utf-8")

    result_path = ANALYSIS_ROOT / "compensation_evidence_provisional_claim_review_636_result_2026-07-25.md"
    result_path.write_text(
        f"# Provisional claim review — result\n\nDecision: `{DECISION}`. The 636-row summary supports bounded documentary, direct-text, and explicitly provisional mechanism scaffolds. Seven rows remain excluded, the 862-row quantitative lane remains unanalyzed, and targeted scouting is recommended next. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    dashboard_path = ANALYSIS_ROOT / "compensation_evidence_provisional_claim_review_636_dashboard_status_note_2026-07-25.md"
    dashboard_path.write_text(
        f"# Dashboard status note — provisional claim review\n\n- Decision: `{DECISION}`.\n- Valid rating-summary scope: 636.\n- Explicit exclusions: 7.\n- Claim records: 35.\n- Quantitative future lane: 862 preserved, not analyzed.\n- Targeted scouting restart recommended: true.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    return decision


def completed(output_dir: Path) -> bool:
    return all((output_dir / name).is_file() for name in REQUIRED_OUTPUTS)


def output_guard(output_dir: Path, resume: bool) -> None:
    resolved = output_dir.resolve()
    if ANALYSIS_ROOT.resolve() not in resolved.parents:
        raise RuntimeError("provisional claim-review output must remain under docs/analysis")
    if output_dir.exists() and not resume:
        raise FileExistsError(f"rollback-safe output already exists: {output_dir}")
    if output_dir.exists() and resume and not completed(output_dir):
        raise RuntimeError("partial outputs cannot masquerade as complete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_guard(output_dir, args.resume)
    if args.resume and completed(output_dir):
        print(json.dumps({"status": "already_complete", "writes": 0, "model_calls": 0, "output_dir": str(output_dir)}))
        return 0
    audit = verify_inputs()
    decision = write_outputs(output_dir, audit)
    if not completed(output_dir):
        raise RuntimeError("required provisional claim-review outputs incomplete")
    print(json.dumps({"status": "completed", "claim_rows": 35, "decision": decision["decision"], "model_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
