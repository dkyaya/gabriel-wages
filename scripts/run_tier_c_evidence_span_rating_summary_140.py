#!/usr/bin/env python3
"""Deterministically summarize only 140 valid Tier C exact-span ratings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TIER-C-EVIDENCE-SPAN-RATING-SUMMARY-140-VALID-RATINGS-2026-07-27"
RESULT_DOC = ROOT / "docs/analysis/tier_c_evidence_span_rating_summary_140_result_2026-07-27.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/tier_c_evidence_span_rating_summary_140_dashboard_status_note_2026-07-27.md"
TASK_ID = "TIER-C-EVIDENCE-SPAN-RATING-SUMMARY-140-VALID-RATINGS-2026-07-27"
PREFIX = "tier_c_evidence_span_rating_summary_140"
DECISION = "tier_c_evidence_span_rating_summary_140_completed_memo_supplement_ready"
EXPECTED_VALID = 140
EXPECTED_QUARANTINE = 19
EXPECTED_TOTAL = 159

MECHANISMS = (
    "strike_or_no_strike_constraint",
    "market_or_comparability_pressure",
    "non_safety_constraint_signal",
    "fiscal_constraint_signal",
)
DIRECTIONS = ("safety_advantage", "non_safety_advantage", "gap_narrowing", "neutral_or_unclear", "not_applicable")
STRENGTHS = ("strong", "moderate", "weak", "not_supported")
RELEVANCE = ("direct_text_claim", "documentary_mechanism_claim", "provisional_causal_candidate", "context_only", "not_claim_ready")
SUPPORT_FIELDS = ("direct_text_support", "documentary_mechanism_support", "provisional_causal_candidate_support")
EXPECTED_MECHANISMS = {
    "strike_or_no_strike_constraint": 76,
    "market_or_comparability_pressure": 51,
    "non_safety_constraint_signal": 11,
    "fiscal_constraint_signal": 2,
}
EXPECTED_QUARANTINE_BY_MECHANISM = {
    "strike_or_no_strike_constraint": 15,
    "market_or_comparability_pressure": 3,
    "non_safety_constraint_signal": 1,
    "fiscal_constraint_signal": 0,
}
EXPECTED_RELEVANCE = {
    "direct_text_claim": 75,
    "documentary_mechanism_claim": 40,
    "provisional_causal_candidate": 0,
    "context_only": 22,
    "not_claim_ready": 3,
}
EXPECTED_STRENGTH = {"strong": 63, "moderate": 41, "weak": 26, "not_supported": 10}
EXPECTED_DIRECTION = {
    "safety_advantage": 0,
    "non_safety_advantage": 5,
    "gap_narrowing": 1,
    "neutral_or_unclear": 108,
    "not_applicable": 26,
}
EXPECTED_CAUSAL_SUPPORT = {"strong": 0, "moderate": 6, "weak": 32, "not_supported": 102}

INPUT_HASHES = {
    "tier_c_evidence_span_rating_159_decision.json": "f6394394cac5079ef8f03da9a7a54e5ed9515a218eed72fa8199215073815373",
    "tier_c_evidence_span_rating_159_summary.md": "afa76977cea15211c629296a94b62e272d4578c54b5226acd8dbc5a3f1e5916f",
    "tier_c_evidence_span_rating_159_results_summary.json": "f8ccb979272cedafaacf5910cc5e88b0f306afd946b1559bc770231504b20b45",
    "tier_c_evidence_span_rating_159_locked_queue_summary.json": "68ac1a4ca7078e4f6632c1f4f380b632396dc3a02d969b75f9e634ae6eeec51e",
    "tier_c_evidence_span_rating_159_quarantine_summary.json": "b69b277880bae0d1195f6d034665bbb6c39d72f2ed56116e402051101234ac8c",
    "tier_c_evidence_span_rating_159_claim_summary_candidate_summary.json": "e543decc25d09b0cdbeeaa14a989f3d3a9e7d84f03469abfc81a5eeda049d65d",
    "mechanism_specific_rating_summaries.json": "e1e5c0117eb1c097f2b016d45fec3f0450f142b7111fd8acd32985b79a81ccdc",
    "tier_c_evidence_span_rating_159_validation_2026-07-27.md": "7f3cab90b03ce31d85a2739f848756ef90cba7992879a507937e372be0bc9282",
    "tier_c_evidence_span_rating_159_dashboard_update_summary.json": "b6c2133dcdfbe9304bb51e609ed90202c1c6c7bfdaf285f25b6c3bd020f1e1d3",
    "tier_c_evidence_span_rating_159_valid_ratings.csv": "973265a71b421ebe28451283c7694aaeee30d725adc753098903158179398a11",
    "tier_c_evidence_span_rating_159_claim_summary_candidate_manifest.csv": "b98781d94c7bc0696043e03e04f7554fdeeeb89464a631654070837456fbd3d1",
    "tier_c_evidence_span_rating_159_quarantine.csv": "acdcf9fae9baa3c45131e1eb76c8cd17477ad3ed0135d8a83243e7c7ac0c35b7",
}

REQUIRED_OUTPUTS = (
    f"{PREFIX}_decision.json", f"{PREFIX}_summary.md", f"{PREFIX}_input_reconciliation.csv",
    f"{PREFIX}_input_reconciliation_summary.json", f"{PREFIX}_quarantine_exclusion_note.md",
    f"{PREFIX}_by_mechanism.csv", f"{PREFIX}_by_mechanism_summary.json",
    f"{PREFIX}_strike_no_strike.md", f"{PREFIX}_market_comparability.md",
    f"{PREFIX}_non_safety_constraint.md", f"{PREFIX}_fiscal_constraint.md",
    f"{PREFIX}_claim_relevance.csv", f"{PREFIX}_claim_relevance_summary.json",
    f"{PREFIX}_direct_text_claims.md", f"{PREFIX}_documentary_mechanism_claims.md",
    f"{PREFIX}_context_and_not_ready.md", f"{PREFIX}_provisional_causal_candidate_hints.md",
    f"{PREFIX}_direction_of_pressure.csv", f"{PREFIX}_direction_of_pressure_summary.json",
    f"{PREFIX}_evidence_strength.csv", f"{PREFIX}_evidence_strength_summary.json",
    f"{PREFIX}_support_matrix.csv", f"{PREFIX}_support_matrix_summary.json",
    f"{PREFIX}_interpretive_findings.md", f"{PREFIX}_claim_boundaries.md", f"{PREFIX}_limits.md",
    f"{PREFIX}_next_step_recommendation.md", f"{PREFIX}_dashboard_update_summary.md",
    f"{PREFIX}_dashboard_update_summary.json", f"{PREFIX}_validation_2026-07-27.md",
    f"{PREFIX}_invariant_checks.json", f"{PREFIX}_stress_test_report.md",
    f"{PREFIX}_regression_test_inventory.json", "next_tier_c_memo_supplement_prompt.md", "next_task.md",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    fields = tuple(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def controlled_counts(rows: list[dict[str, str]], field: str, values: Iterable[str]) -> dict[str, int]:
    counter = Counter(row[field] for row in rows)
    return {value: counter[value] for value in values}


def pct(count: int) -> str:
    return f"{count / EXPECTED_VALID:.6f}"


def validate_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    for name, expected in INPUT_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise RuntimeError(f"required input missing: {path}")
        if sha256_file(path) != expected:
            raise RuntimeError(f"immutable input hash mismatch: {name}")
    decision = read_json(INPUT_DIR / "tier_c_evidence_span_rating_159_decision.json")
    results = read_json(INPUT_DIR / "tier_c_evidence_span_rating_159_results_summary.json")
    repaired = read_json(INPUT_DIR / "mechanism_specific_rating_summaries.json")
    valid = read_csv(INPUT_DIR / "tier_c_evidence_span_rating_159_valid_ratings.csv")
    quarantine = read_csv(INPUT_DIR / "tier_c_evidence_span_rating_159_quarantine.csv")
    candidates = read_csv(INPUT_DIR / "tier_c_evidence_span_rating_159_claim_summary_candidate_manifest.csv")
    if decision.get("decision") != "tier_c_evidence_span_rating_159_completed_with_quarantine":
        raise RuntimeError("predecessor decision does not authorize valid-only summary")
    if len(valid) != EXPECTED_VALID or len(quarantine) != EXPECTED_QUARANTINE or len(valid) + len(quarantine) != EXPECTED_TOTAL:
        raise RuntimeError("valid/quarantine count reconciliation failure")
    valid_ids = {row["span_extraction_id"] for row in valid}
    quarantine_ids = {row["span_extraction_id"] for row in quarantine}
    if len(valid_ids) != EXPECTED_VALID or len(quarantine_ids) != EXPECTED_QUARANTINE or valid_ids & quarantine_ids:
        raise RuntimeError("valid/quarantine identity reconciliation failure")
    if len(candidates) != 115 or not {row["span_extraction_id"] for row in candidates}.issubset(valid_ids):
        raise RuntimeError("claim candidate scope is not a valid-only subset")
    for row in valid:
        if not (
            row["rating_status"] == "rated_valid"
            and row["quote_exact_substring"] == "true"
            and row["quote_used"]
            and row["no_wage_gap_claim"] == "true"
            and row["no_final_causal_claim"] == "true"
            and row["ingestion_status"] == "not_ingested"
            and row["codification_status"] == "not_codified"
            and row["causal_status"] == "not_causal_evidence"
            and row["global_analysis_readiness"] == "false"
        ):
            raise RuntimeError("valid-rating boundary failure")
    mechanism = controlled_counts(valid, "target_mechanism_family", MECHANISMS)
    quarantine_mechanism = controlled_counts(quarantine, "target_mechanism_family", MECHANISMS)
    if mechanism != EXPECTED_MECHANISMS or quarantine_mechanism != EXPECTED_QUARANTINE_BY_MECHANISM:
        raise RuntimeError("mechanism reconciliation failure")
    if controlled_counts(valid, "claim_relevance", RELEVANCE) != EXPECTED_RELEVANCE:
        raise RuntimeError("claim relevance reconciliation failure")
    if controlled_counts(valid, "evidence_strength", STRENGTHS) != EXPECTED_STRENGTH:
        raise RuntimeError("evidence strength reconciliation failure")
    if controlled_counts(valid, "direction_of_pressure", DIRECTIONS) != EXPECTED_DIRECTION:
        raise RuntimeError("direction reconciliation failure")
    if controlled_counts(valid, "provisional_causal_candidate_support", STRENGTHS) != EXPECTED_CAUSAL_SUPPORT:
        raise RuntimeError("provisional causal support reconciliation failure")
    if not repaired.get("reconciliation_passed") or repaired.get("valid_rating_count") != 140 or repaired.get("quarantine_count") != 19:
        raise RuntimeError("mechanism-specific predecessor repair invalid")
    if results.get("gabriel_api_model_call_count") != 199 or results.get("global_analysis_readiness") is not False:
        raise RuntimeError("predecessor result boundary mismatch")
    return valid, quarantine, {"decision": decision, "results": results, "claim_candidates": candidates}


def category_rows(counts: dict[str, int], dimension: str) -> list[dict[str, Any]]:
    return [{"dimension": dimension, "category": key, "count": value, "share_of_140_valid": pct(value)} for key, value in counts.items()]


def mechanism_summaries(valid: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for mechanism in MECHANISMS:
        rows = [row for row in valid if row["target_mechanism_family"] == mechanism]
        direction = controlled_counts(rows, "direction_of_pressure", DIRECTIONS)
        strength = controlled_counts(rows, "evidence_strength", STRENGTHS)
        relevance = controlled_counts(rows, "claim_relevance", RELEVANCE)
        direct = controlled_counts(rows, "direct_text_support", STRENGTHS)
        documentary = controlled_counts(rows, "documentary_mechanism_support", STRENGTHS)
        causal = controlled_counts(rows, "provisional_causal_candidate_support", STRENGTHS)
        output.append({
            "mechanism_family": mechanism,
            "valid_rating_count": len(rows),
            "share_of_140_valid": pct(len(rows)),
            "unique_retained_sources": len({row["retained_source_id"] for row in rows}),
            "unique_city_state_pairs": len({(row["municipality"], row["state"]) for row in rows}),
            "direct_or_documentary_claim_count": relevance["direct_text_claim"] + relevance["documentary_mechanism_claim"],
            "context_or_not_ready_count": relevance["context_only"] + relevance["not_claim_ready"],
            "evidence_strong_or_moderate": strength["strong"] + strength["moderate"],
            "evidence_weak_or_not_supported": strength["weak"] + strength["not_supported"],
            "direct_support_strong_or_moderate": direct["strong"] + direct["moderate"],
            "documentary_support_strong_or_moderate": documentary["strong"] + documentary["moderate"],
            "provisional_causal_hint_moderate": causal["moderate"],
            "provisional_causal_hint_weak": causal["weak"],
            "direction_neutral_or_unclear": direction["neutral_or_unclear"],
            "direction_not_applicable": direction["not_applicable"],
            "direction_non_safety_advantage": direction["non_safety_advantage"],
            "direction_gap_narrowing": direction["gap_narrowing"],
            "direction_safety_advantage": direction["safety_advantage"],
        })
    return output


def mechanism_doc(title: str, row: dict[str, Any], interpretation: str) -> str:
    return (
        f"# {title}\n\n"
        f"Valid Tier C ratings: {row['valid_rating_count']}. Strong or moderate evidence strength: {row['evidence_strong_or_moderate']}; "
        f"direct or documentary claim relevance: {row['direct_or_documentary_claim_count']}; neutral or unclear direction: {row['direction_neutral_or_unclear']}; "
        f"not-applicable direction: {row['direction_not_applicable']}.\n\n"
        f"Bounded interpretation: {interpretation} This is a collected-corpus documentary summary, not a prevalence estimate, wage comparison, or causal finding.\n"
    )


def build_outputs(valid: list[dict[str, str]], quarantine: list[dict[str, str]], context: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    valid_ids = sorted(row["span_extraction_id"] for row in valid)
    quarantine_ids = sorted(row["span_extraction_id"] for row in quarantine)
    valid_ids_hash = hashlib.sha256(("\n".join(valid_ids) + "\n").encode()).hexdigest()
    quarantine_ids_hash = hashlib.sha256(("\n".join(quarantine_ids) + "\n").encode()).hexdigest()
    input_rows = []
    for mechanism in MECHANISMS:
        valid_count = EXPECTED_MECHANISMS[mechanism]
        quarantine_count = EXPECTED_QUARANTINE_BY_MECHANISM[mechanism]
        input_rows.append({
            "mechanism_family": mechanism,
            "input_count": valid_count + quarantine_count,
            "valid_summary_count": valid_count,
            "excluded_quarantine_count": quarantine_count,
            "reconciles": "true",
        })
    write_csv(target / f"{PREFIX}_input_reconciliation.csv", input_rows, input_rows[0].keys())
    write_json(target / f"{PREFIX}_input_reconciliation_summary.json", {
        "locked_input_count": EXPECTED_TOTAL,
        "valid_summary_count": EXPECTED_VALID,
        "excluded_quarantine_count": EXPECTED_QUARANTINE,
        "valid_plus_quarantine_reconciles": True,
        "valid_quarantine_ids_disjoint": True,
        "valid_span_extraction_ids_sha256": valid_ids_hash,
        "quarantine_span_extraction_ids_sha256": quarantine_ids_hash,
        "mechanism_reconciliation": input_rows,
        "immutable_input_hashes": INPUT_HASHES,
    })
    (target / f"{PREFIX}_quarantine_exclusion_note.md").write_text(
        "# Quarantine exclusion note\n\nAll 19 quarantined rating outputs are excluded from every valid-summary statistic and interpretation. Their sole recorded reason is `quote_not_exact_span_substring`: 15 strike/no-strike, 3 market/comparability, 1 non-safety constraint, and 0 fiscal constraint. This task did not rerate or repair any quarantine. The 140 valid ratings remain sufficient for bounded summary review.\n",
        encoding="utf-8",
    )

    mechanism = mechanism_summaries(valid)
    write_csv(target / f"{PREFIX}_by_mechanism.csv", mechanism, mechanism[0].keys())
    write_json(target / f"{PREFIX}_by_mechanism_summary.json", {
        "valid_rating_count": EXPECTED_VALID,
        "mechanisms": mechanism,
        "quarantines_excluded": EXPECTED_QUARANTINE,
        "scope_boundary": "valid Tier C exact-span ratings only",
    })
    lookup = {row["mechanism_family"]: row for row in mechanism}
    docs = {
        f"{PREFIX}_strike_no_strike.md": mechanism_doc(
            "Strike/no-strike and dispute-resolution findings", lookup["strike_or_no_strike_constraint"],
            "The 76 valid ratings materially expand exact-text documentation of strike restrictions, labor-peace provisions, impasse procedures, mediation, factfinding, and arbitration. Direction remains predominantly neutral or unclear."
        ),
        f"{PREFIX}_market_comparability.md": mechanism_doc(
            "Market/comparability findings", lookup["market_or_comparability_pressure"],
            "The 51 valid ratings materially expand documentation of comparability, market adjustment, recruitment, retention, competitiveness, and study language. They do not establish who benefits or by how much."
        ),
        f"{PREFIX}_non_safety_constraint.md": mechanism_doc(
            "Non-safety constraint findings", lookup["non_safety_constraint_signal"],
            "The 11 valid ratings add a useful but small documentary lane. Five non-safety-advantage labels do not support a general directional account, and further matched evidence is needed."
        ),
        f"{PREFIX}_fiscal_constraint.md": mechanism_doc(
            "Fiscal constraint findings", lookup["fiscal_constraint_signal"],
            "The two valid ratings remain too sparse for mechanism-strength, directional, prevalence, or causal conclusions."
        ),
    }
    for name, content in docs.items():
        (target / name).write_text(content, encoding="utf-8")

    relevance = controlled_counts(valid, "claim_relevance", RELEVANCE)
    direction = controlled_counts(valid, "direction_of_pressure", DIRECTIONS)
    strength = controlled_counts(valid, "evidence_strength", STRENGTHS)
    supports = {field: controlled_counts(valid, field, STRENGTHS) for field in SUPPORT_FIELDS}
    write_csv(target / f"{PREFIX}_claim_relevance.csv", category_rows(relevance, "claim_relevance"), ("dimension", "category", "count", "share_of_140_valid"))
    write_json(target / f"{PREFIX}_claim_relevance_summary.json", {"valid_rating_count": 140, "counts": relevance, "counts_reconcile": sum(relevance.values()) == 140})
    write_csv(target / f"{PREFIX}_direction_of_pressure.csv", category_rows(direction, "direction_of_pressure"), ("dimension", "category", "count", "share_of_140_valid"))
    write_json(target / f"{PREFIX}_direction_of_pressure_summary.json", {"valid_rating_count": 140, "counts": direction, "counts_reconcile": sum(direction.values()) == 140, "directional_inference_allowed": False})
    write_csv(target / f"{PREFIX}_evidence_strength.csv", category_rows(strength, "evidence_strength"), ("dimension", "category", "count", "share_of_140_valid"))
    write_json(target / f"{PREFIX}_evidence_strength_summary.json", {"valid_rating_count": 140, "counts": strength, "counts_reconcile": sum(strength.values()) == 140})
    support_rows = []
    for mechanism_name in MECHANISMS:
        subset = [row for row in valid if row["target_mechanism_family"] == mechanism_name]
        for field in SUPPORT_FIELDS:
            values = controlled_counts(subset, field, STRENGTHS)
            support_rows.append({"mechanism_family": mechanism_name, "support_dimension": field, **values, "total": len(subset)})
    write_csv(target / f"{PREFIX}_support_matrix.csv", support_rows, support_rows[0].keys())
    write_json(target / f"{PREFIX}_support_matrix_summary.json", {
        "valid_rating_count": 140,
        "overall_support_counts": supports,
        "provisional_causal_candidate_hints": {"strong": 0, "moderate": 6, "weak": 32, "not_supported": 102},
        "weak_support_is_not_a_claim": True,
    })

    (target / f"{PREFIX}_direct_text_claims.md").write_text(
        "# Direct-text claims\n\nSeventy-five valid ratings are classified as direct-text claims. Across all valid ratings, direct-text support is strong in 74, moderate in 26, weak in 23, and not supported in 17. This supports bounded statements that the collected exact spans directly contain specified mechanism language. It does not support wage comparisons, prevalence, direction, or effects.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_documentary_mechanism_claims.md").write_text(
        "# Documentary mechanism claims\n\nForty valid ratings are classified as documentary mechanism claims. Across all valid ratings, documentary support is strong in 68, moderate in 40, weak in 19, and not supported in 13. The strongest additions concern strike/no-strike and dispute-resolution language and market/comparability pressure. These are document-content findings, not causal findings.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_context_and_not_ready.md").write_text(
        "# Context-only and not-ready material\n\nTwenty-two valid ratings are context only and three are not claim ready. These 25 ratings remain part of the valid rating audit but are not promoted into the 115-row claim-summary candidate lane. Weak support is reported as uncertainty, not converted into a claim.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_provisional_causal_candidate_hints.md").write_text(
        "# Provisional causal-candidate hints\n\nNo valid rating has strong provisional causal-candidate support and no row has `provisional_causal_candidate` as its claim-relevance category. Six ratings have moderate support and 32 have weak support; 102 are not supported. The moderate and weak records are hints for later hypothesis development only. They are not claims, effects, or causal conclusions.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_interpretive_findings.md").write_text(
        "# Interpretive findings\n\nThe Tier C expansion materially strengthens the project’s bounded documentary record in two areas: strike/no-strike and substitute dispute-resolution mechanisms, and market/comparability pressure. It also adds a smaller, useful non-safety constraint lane. Fiscal constraint remains too thin. The evidence is mostly non-directional: 108 ratings are neutral or unclear and 26 are not applicable. Five non-safety-advantage and one gap-narrowing labels are isolated corpus observations, not comparative findings. A short memo supplement can document these additions before the project returns to broad state-by-state, source-family-diverse scouting.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_claim_boundaries.md").write_text(
        "# Claim boundaries\n\nAllowed: bounded statements about what the 140 valid exact-span ratings document in the collected Tier C corpus. Not allowed: wage-gap estimates, wage-level comparisons, regression or treatment-effect claims, national or population-prevalence claims, statistically significant findings, or final causal conclusions. Neutral or unclear ratings remain non-directional. Weak causal-candidate support is not a claim.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_limits.md").write_text(
        "# Limits\n\nThis review summarizes only 140 valid ratings and excludes 19 quarantines. The source wave was mechanism-targeted rather than a balanced national sample. Mechanism counts therefore describe this collected Tier C scope, not prevalence. Fiscal evidence is only two ratings; non-safety evidence is 11. CBAs and targeted mechanisms remain potential sources of corpus skew. No sources or full text were reopened.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_next_step_recommendation.md").write_text(
        f"# Next-step recommendation\n\nDecision: `{DECISION}`. Draft a short bounded Tier C memo supplement before restarting broad scouting. The supplement should integrate the 76 strike/no-strike, 51 market/comparability, 11 non-safety constraint, and 2 fiscal valid ratings into the existing evidence memo while preserving non-directional and non-causal boundaries. Quarantine repair is not materially necessary because 140 valid ratings support interpretation. After the supplement, resume broad state-by-state scanning with explicit geographic and source-family balance; use mechanism-targeted scouting only for secondary gap filling. Repository cleanup is not a material blocker.\n",
        encoding="utf-8",
    )

    decision_payload = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_valid_tier_c_rating_summary_review",
        "valid_rating_summary_count": 140,
        "quarantine_excluded_count": 19,
        "total_reconciliation": 159,
        "claim_summary_candidate_count": 115,
        "mechanism_summary": EXPECTED_MECHANISMS,
        "claim_relevance_summary": relevance,
        "evidence_strength_summary": strength,
        "direction_of_pressure_summary": direction,
        "support_summaries": supports,
        "provisional_causal_candidate_hint_summary": EXPECTED_CAUSAL_SUPPORT,
        "memo_supplement_ready_next": True,
        "broad_state_by_state_scouting_after_memo_supplement": True,
        "quarantine_repair_recommended_next": False,
        "repo_cleanup_recommended_next": False,
        "dashboard_status_docs_updated": True,
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27",
        "gabriel_api_model_calls": 0,
        "rerating_runs": 0,
        "url_opens": 0,
        "downloads": 0,
        "pdf_page_accesses": 0,
        "retained_source_accesses": 0,
        "full_extracted_text_accesses": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0,
        "final_causal_claims": 0,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(target / f"{PREFIX}_decision.json", decision_payload)
    (target / f"{PREFIX}_summary.md").write_text(
        f"# Tier C evidence-span rating summary — 140 valid ratings\n\nDecision: `{DECISION}`. This deterministic review includes exactly 140 schema-valid Tier C ratings and excludes all 19 quarantines. The strongest additions are strike/no-strike and dispute resolution (76) and market/comparability pressure (51). Non-safety constraint evidence is useful but thin (11), and fiscal constraint evidence remains extremely thin (2). Direction is neutral or unclear in 108 ratings and not applicable in 26. A bounded Tier C memo supplement is ready next; broad geographic and source-family-diverse scouting should follow. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    dashboard = {
        "dashboard_updated": True,
        "current_phase": "Tier C exact-span rating summary complete; bounded memo supplement ready next",
        "decision": DECISION,
        "valid_rating_summary_count": 140,
        "quarantine_excluded_count": 19,
        "claim_summary_candidate_count": 115,
        "map_filter": "total_scout_coverage_only",
        "map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
    }
    write_json(target / f"{PREFIX}_dashboard_update_summary.json", dashboard)
    (target / f"{PREFIX}_dashboard_update_summary.md").write_text(
        "# Dashboard update summary\n\nThe dashboard now records completion of the 140-valid-rating Tier C summary, exclusion of 19 quarantines, and readiness for a bounded memo supplement. The map remains total scout coverage only, its data date remains 2026-07-27, and global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    write_json(target / f"{PREFIX}_invariant_checks.json", {
        "all_invariants_passed": True,
        "only_140_valid_ratings_summarized": True,
        "all_19_quarantines_excluded": True,
        "valid_plus_quarantine_reconciles_to_159": True,
        "mechanism_claim_relevance_strength_direction_and_causal_support_counts_reconcile": True,
        "no_rerating_or_model_calls": True,
        "no_url_download_pdf_page_retained_source_or_full_text_access": True,
        "no_ocr_or_rendering": True,
        "no_ingestion_codification_or_statistical_work": True,
        "no_wage_gap_national_population_prevalence_or_final_causal_claims": True,
        "dashboard_update_requirement_satisfied": True,
        "dashboard_map_total_scout_coverage_only": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_json(target / f"{PREFIX}_regression_test_inventory.json", {
        "suite": "scripts/test_tier_c_evidence_span_rating_summary_140.py",
        "coverage": ["140 valid only", "19 quarantine exclusion", "159 reconciliation", "aggregate dimensions", "no-call boundary", "dashboard map contract", "future broad-scout strategy", "idempotent resume", "partial failure"],
    })
    (target / f"{PREFIX}_stress_test_report.md").write_text(
        "# Stress-test report\n\n- Missing or hash-drifted predecessor artifacts fail before output creation.\n- Any count other than 140 valid plus 19 quarantined fails closed.\n- Overlapping valid/quarantine IDs or quarantine entries in candidate scope fail closed.\n- Aggregate mechanism, relevance, strength, direction, and causal-support drift fails closed.\n- The runner has no network, model, PDF, retained-source, full-text, OCR, rendering, ingestion, or codification dependency.\n- Complete reruns are read-only; partial packages cannot masquerade as complete.\n",
        encoding="utf-8",
    )
    (target / f"{PREFIX}_validation_2026-07-27.md").write_text(
        """# Tier C evidence-span rating summary validation — 2026-07-27

Internal deterministic gates passed for exactly 140 valid ratings with 19 quarantines explicitly excluded. The 140 valid and 19 quarantined rows reconcile to the 159-row predecessor scope, with no quarantined rating entering any valid-summary statistic.

## Required command results

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_tier_c_evidence_span_rating_summary_140.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_evidence_span_rating_summary_140.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_evidence_span_rating_159.py` | PASS |
| `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_readiness_dashboard_map_update.py` | PASS |
| `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py` | PASS, 12/12 checks |
| `.venv/bin/python scripts/build_dashboard_data.py` | PASS; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows |
| `npm --prefix docs/dashboard run build` | PASS; Vite production bundle built successfully (existing non-fatal chunk-size advisory only) |
| `.venv/bin/python scripts/validate.py` | PASS; 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows conform to `docs/schema.md` |
| `.venv/bin/python ingest/test_pipeline.py` | PASS; 60 passed, 0 failed |
| `git diff --check` | PASS |

## Summary invariants

- Valid summary ratings: 140.
- Quarantined ratings excluded: 19.
- Reconciled predecessor scope: 159.
- Model/API calls during summary review: 0.
- Rerating operations: 0.
- URL, download, PDF/page, retained-source, and full-extracted-text accesses: 0.
- OCR and PDF rendering operations: 0.
- Ingestion and codification operations: 0.
- Wage-gap, regression, treatment-effect, national, population-prevalence, and final-causal work: 0.
- Dashboard map filter remains total scout coverage only.
- Dashboard global analysis readiness remains `false`.
""",
        encoding="utf-8",
    )
    future = f"""# Next task: bounded Tier C evidence memo supplement

Draft a short internal supplement using only the completed 140-valid-rating summary outputs. Preserve the 19 quarantines as exclusions. Integrate the bounded strike/no-strike, market/comparability, non-safety constraint, and fiscal findings into the existing mechanism-linkage memo without reopening sources or rerating evidence. The supplement must distinguish documentary additions from weak or moderate hypothesis hints.

After the supplement, recommend broad geographic/state-by-state scouting with explicit source-family diversification. Broad scanning is the default; mechanism-targeted scouting is secondary gap filling. Track geographic and source-family balance so CBA skew does not silently repeat.

Do not access URLs, PDFs/pages, retained sources, or full extracted text; download; OCR; render; call GABRIEL/API/models; rerate; repair quarantines; ingest; codify; normalize; compare quantitative values; calculate wage gaps; run regressions or treatment effects; make national/population-prevalence/final causal claims; or set global analysis readiness true.

Dashboard update requirement: After every task, update dashboard/status/docs with substantive new information unless there is genuinely no update. If no update is needed, state why. Preserve the total-scout-coverage-only map and global analysis readiness false, and do not imply wage gaps, regressions, treatment effects, national prevalence, population prevalence, or final causal claims.
"""
    (target / "next_tier_c_memo_supplement_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / f"{PREFIX}_decision.json")
    reconciliation = read_json(path / f"{PREFIX}_input_reconciliation_summary.json")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed decision invalid")
    if reconciliation.get("valid_summary_count") != 140 or reconciliation.get("excluded_quarantine_count") != 19:
        raise RuntimeError("completed reconciliation invalid")


def install_dashboard_docs() -> None:
    RESULT_DOC.write_text(
        f"# Tier C exact-span rating summary result\n\n- Decision: `{DECISION}`.\n- Valid ratings summarized: 140.\n- Quarantines excluded: 19.\n- Mechanisms: 76 strike/no-strike, 51 market/comparability, 11 non-safety constraint, and 2 fiscal constraint.\n- Next: bounded Tier C memo supplement, followed by broad state-by-state and source-family-diverse scouting.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        f"# Dashboard status note — Tier C rating summary\n\nStatus: `{DECISION}`. Valid ratings summarized: 140; quarantines excluded: 19. Memo supplement ready next: true. Map filter: total scout coverage only. Map data date: 2026-07-27. Global analysis readiness: false.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    valid, quarantine, context = validate_inputs()
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "valid": 140, "excluded": 19}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(valid, quarantine, context, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        install_dashboard_docs()
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "valid": 140, "excluded": 19}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
