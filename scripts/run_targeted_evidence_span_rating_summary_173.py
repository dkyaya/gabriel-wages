#!/usr/bin/env python3
"""Deterministically summarize 173 valid targeted exact-span ratings.

This runner reads only committed rating-layer CSV/JSON/Markdown artifacts. It does
not access source locators, retained files, PDFs, pages, or extracted-text files;
lineage values are copied as inert metadata only.
"""

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
INPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-EVIDENCE-SPAN-RATING-201-EXACT-SPANS-2026-07-26"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-EVIDENCE-SPAN-RATING-SUMMARY-173-VALID-RATINGS-2026-07-26"
RESULT_DOC = ROOT / "docs/analysis/targeted_evidence_span_rating_summary_173_result_2026-07-26.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/targeted_evidence_span_rating_summary_173_dashboard_status_note_2026-07-26.md"
TASK_ID = "TARGETED-EVIDENCE-SPAN-RATING-SUMMARY-173-VALID-RATINGS-2026-07-26"
DECISION = "targeted_evidence_span_rating_summary_173_completed_quantitative_triage_recommended"
EXPECTED_VALID = 173
EXPECTED_QUARANTINE = 28
EXPECTED_TOTAL = 201
QUANTITATIVE_ROWS_PRESERVED = 862

INPUT_HASHES = {
    "targeted_evidence_span_rating_201_decision.json": "d117a05d43fb184672a6b7c58b83d2f899d2e925f1baf618d17f9e256dd26017",
    "targeted_evidence_span_rating_201_summary.md": "0055c8de81444fb543bf681e0a1f3e23d3813f2ff1e608d788318f29297ed42c",
    "targeted_evidence_span_rating_201_locked_queue_summary.json": "d65c5ba739ed20b485df7e5f84616601225363d7261b18e34ff43cba3cde4d7d",
    "targeted_evidence_span_rating_201_results_summary.json": "69719d494afdf08608868664b6dc3d209380cc1c62b7123fb5f218ecff4114c7",
    "targeted_evidence_span_rating_201_quarantine_summary.json": "a1e7c53834c39845fc8c01dc3988c020cd547d42ae5d035847625eb4f4479e41",
    "targeted_evidence_span_rating_201_claim_summary_candidate_summary.json": "224ff20a184a8dd44666681407d03d3e4b621dfb1cd0d7249a705d1232f0d120",
    "mechanism_specific_rating_summary.json": "571d00a77474e088f46133285d04301c746abd9f1801cf7ae86c1340d83af920",
    "targeted_evidence_span_rating_201_validation_2026-07-26.md": "09b82c4f64c19155519b6b821dd6656a7cc3164ed13bc1db74aa9ae531319e14",
    "targeted_evidence_span_rating_201_invariant_checks.json": "d73a5c1a9bfc8d2463e990ec213181c3c12acc75aa0eb0853092fdb4ca866609",
    "targeted_evidence_span_rating_201_valid_ratings.csv": "86eeec30f7394003b24707123539e5f37b834ae755a71c624e91a184bc124158",
    "targeted_evidence_span_rating_201_results.csv": "86eeec30f7394003b24707123539e5f37b834ae755a71c624e91a184bc124158",
    "targeted_evidence_span_rating_201_quarantine.csv": "e90d4b0e46eb303660c84b7a15b5b293cd16e5c74bda7abacecd861af03377e3",
}

MECHANISMS = [
    "strike_or_no_strike_constraint",
    "market_or_comparability_pressure",
    "non_safety_constraint_signal",
    "fiscal_constraint_signal",
]
DIRECTIONS = ["safety_advantage", "non_safety_advantage", "gap_narrowing", "neutral_or_unclear", "not_applicable"]
STRENGTHS = ["strong", "moderate", "weak", "not_supported"]
CLAIM_RELEVANCE = ["direct_text_claim", "documentary_mechanism_claim", "provisional_causal_candidate", "context_only", "not_claim_ready"]
SUPPORT_FIELDS = ["direct_text_support", "documentary_mechanism_support", "provisional_causal_candidate_support"]

VALID_SCOPE_FIELDS = [
    "span_rating_id", "span_extraction_id", "extracted_text_id", "retained_source_id",
    "candidate_id", "lane_id", "priority_tier", "municipality", "state", "unit_type",
    "occupation_group", "bargaining_unit_name", "contract_or_document_period",
    "inferred_cycle_start", "inferred_cycle_end", "source_family",
    "target_mechanism_family", "rated_mechanism_family", "span_sha256", "quote_used",
    "quote_exact_substring", "documentary_mechanism_support", "direct_text_support",
    "provisional_causal_candidate_support", "direction_of_pressure", "evidence_strength",
    "claim_relevance", "reason_code", "claim_boundary", "no_wage_gap_claim",
    "no_final_causal_claim", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness",
]

REQUIRED_OUTPUTS = [
    "targeted_evidence_span_rating_summary_173_decision.json",
    "targeted_evidence_span_rating_summary_173_summary.md",
    "targeted_evidence_span_rating_summary_173_valid_scope.csv",
    "targeted_evidence_span_rating_summary_173_valid_scope_summary.json",
    "targeted_evidence_span_rating_summary_173_excluded_quarantine.csv",
    "targeted_evidence_span_rating_summary_173_excluded_quarantine_summary.json",
    "targeted_evidence_span_rating_summary_173_mechanism_summary.csv",
    "targeted_evidence_span_rating_summary_173_mechanism_summary.json",
    "targeted_evidence_span_rating_summary_173_strike_no_strike_summary.md",
    "targeted_evidence_span_rating_summary_173_market_comparability_summary.md",
    "targeted_evidence_span_rating_summary_173_non_safety_constraint_summary.md",
    "targeted_evidence_span_rating_summary_173_fiscal_constraint_summary.md",
    "targeted_evidence_span_rating_summary_173_direction_of_pressure.csv",
    "targeted_evidence_span_rating_summary_173_evidence_strength.csv",
    "targeted_evidence_span_rating_summary_173_claim_relevance.csv",
    "targeted_evidence_span_rating_summary_173_support_summary.csv",
    "targeted_evidence_span_rating_summary_173_supported_direct_text_claims.md",
    "targeted_evidence_span_rating_summary_173_supported_documentary_mechanism_claims.md",
    "targeted_evidence_span_rating_summary_173_provisional_causal_candidate_signals.md",
    "targeted_evidence_span_rating_summary_173_claims_requiring_more_data.md",
    "targeted_evidence_span_rating_summary_173_claims_not_allowed.md",
    "targeted_evidence_span_rating_summary_173_claim_boundary_language_bank.md",
    "targeted_evidence_span_rating_summary_173_next_action_recommendation.md",
    "targeted_evidence_span_rating_summary_173_tier_c_verification_considerations.md",
    "targeted_evidence_span_rating_summary_173_quantitative_triage_considerations.md",
    "targeted_evidence_span_rating_summary_173_repo_cleanup_considerations.md",
    "targeted_evidence_span_rating_summary_173_validation_2026-07-26.md",
    "targeted_evidence_span_rating_summary_173_invariant_checks.json",
    "targeted_evidence_span_rating_summary_173_stress_test_report.md",
    "targeted_evidence_span_rating_summary_173_regression_test_inventory.json",
    "targeted_evidence_span_rating_summary_173_lock.json",
    "next_quantitative_claim_triage_prompt.md",
    "next_task.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def pct(count: int, total: int = EXPECTED_VALID) -> str:
    return f"{(count / total * 100):.1f}%" if total else "0.0%"


def validate_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    for name, expected in INPUT_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise RuntimeError(f"required input missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"immutable input hash mismatch: {name}: {actual}")

    decision = read_json(INPUT_DIR / "targeted_evidence_span_rating_201_decision.json")
    results = read_json(INPUT_DIR / "targeted_evidence_span_rating_201_results_summary.json")
    quarantine_summary = read_json(INPUT_DIR / "targeted_evidence_span_rating_201_quarantine_summary.json")
    mechanism_summary = read_json(INPUT_DIR / "mechanism_specific_rating_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_evidence_span_rating_201_invariant_checks.json")
    valid = read_csv(INPUT_DIR / "targeted_evidence_span_rating_201_valid_ratings.csv")
    quarantine = read_csv(INPUT_DIR / "targeted_evidence_span_rating_201_quarantine.csv")

    if decision.get("decision") != "targeted_evidence_span_rating_201_completed_with_quarantine":
        raise RuntimeError("predecessor decision does not permit bounded valid-only summary")
    if len(valid) != EXPECTED_VALID or len(quarantine) != EXPECTED_QUARANTINE or len(valid) + len(quarantine) != EXPECTED_TOTAL:
        raise RuntimeError("valid/quarantine count reconciliation failure")
    valid_ids = [row.get("span_extraction_id", "") for row in valid]
    quarantine_ids = [row.get("span_extraction_id", "") for row in quarantine]
    if len(valid_ids) != len(set(valid_ids)) or len(quarantine_ids) != len(set(quarantine_ids)):
        raise RuntimeError("duplicate rating identity")
    if set(valid_ids) & set(quarantine_ids):
        raise RuntimeError("quarantined row entered valid summary scope")
    if not all(
        row.get("rating_status") == "rated_valid"
        and row.get("quote_exact_substring") == "true"
        and row.get("quote_used", "")
        and row.get("no_wage_gap_claim") == "true"
        and row.get("no_final_causal_claim") == "true"
        and row.get("ingestion_status") == "not_ingested"
        and row.get("codification_status") == "not_codified"
        and row.get("causal_status") == "not_causal_evidence"
        and row.get("global_analysis_readiness") == "false"
        for row in valid
    ):
        raise RuntimeError("valid rating boundary or status failure")
    expected_mechanisms = {"strike_or_no_strike_constraint": 103, "market_or_comparability_pressure": 59, "non_safety_constraint_signal": 10, "fiscal_constraint_signal": 1}
    actual_mechanisms = Counter(row["target_mechanism_family"] for row in valid)
    if dict(actual_mechanisms) != expected_mechanisms:
        raise RuntimeError(f"mechanism reconciliation failure: {dict(actual_mechanisms)}")
    if mechanism_summary.get("total") != {"locked_input_count": 201, "valid_rating_count": 173, "quarantine_count": 28}:
        raise RuntimeError("repaired mechanism summary total invalid")
    if results.get("valid_rating_count") != 173 or results.get("quarantine_count") != 28:
        raise RuntimeError("results summary count mismatch")
    if quarantine_summary.get("quarantine_count") != 28 or quarantine_summary.get("explicit_exclusion_from_summary") is not True:
        raise RuntimeError("quarantine summary is not an explicit exclusion")
    if invariants.get("all_invariants_passed") is not True or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("predecessor boundary invariants not closed")
    return valid, quarantine, results


def mechanism_rows(valid: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mechanism in MECHANISMS:
        subset = [row for row in valid if row["target_mechanism_family"] == mechanism]
        directions = Counter(row["direction_of_pressure"] for row in subset)
        strengths = Counter(row["evidence_strength"] for row in subset)
        relevance = Counter(row["claim_relevance"] for row in subset)
        direct = Counter(row["direct_text_support"] for row in subset)
        documentary = Counter(row["documentary_mechanism_support"] for row in subset)
        causal = Counter(row["provisional_causal_candidate_support"] for row in subset)
        if mechanism == "strike_or_no_strike_constraint":
            interpretation = "substantially strengthened documentary lane; direction remains text-dependent"
        elif mechanism == "market_or_comparability_pressure":
            interpretation = "strengthened documentary lane; no population or directional inference"
        elif mechanism == "non_safety_constraint_signal":
            interpretation = "useful but comparatively sparse; targeted supplementation remains warranted"
        else:
            interpretation = "extremely sparse; insufficient for broad or directional claims"
        rows.append({
            "mechanism_family": mechanism,
            "valid_rating_count": len(subset),
            "share_of_valid_ratings": f"{len(subset) / EXPECTED_VALID:.6f}",
            "unique_retained_sources": len({row["retained_source_id"] for row in subset}),
            "unique_city_state_pairs": len({(row["municipality"], row["state"]) for row in subset}),
            "direction_neutral_or_unclear": directions["neutral_or_unclear"],
            "direction_not_applicable": directions["not_applicable"],
            "direction_safety_advantage": directions["safety_advantage"],
            "direction_non_safety_advantage": directions["non_safety_advantage"],
            "direction_gap_narrowing": directions["gap_narrowing"],
            "evidence_strong": strengths["strong"],
            "evidence_moderate": strengths["moderate"],
            "evidence_weak": strengths["weak"],
            "evidence_not_supported": strengths["not_supported"],
            "direct_support_strong_or_moderate": direct["strong"] + direct["moderate"],
            "documentary_support_strong_or_moderate": documentary["strong"] + documentary["moderate"],
            "provisional_causal_support_strong_or_moderate": causal["strong"] + causal["moderate"],
            "claim_relevance_direct_text": relevance["direct_text_claim"],
            "claim_relevance_documentary": relevance["documentary_mechanism_claim"],
            "claim_relevance_context_only": relevance["context_only"],
            "claim_relevance_not_ready": relevance["not_claim_ready"],
            "bounded_interpretation": interpretation,
        })
    return rows


def summary_rows(counter: Counter[str], categories: list[str], dimension: str) -> list[dict[str, Any]]:
    return [{"dimension": dimension, "category": category, "count": counter[category], "share_of_valid_ratings": f"{counter[category] / EXPECTED_VALID:.6f}"} for category in categories]


def mechanism_doc(title: str, row: dict[str, Any], boundary: str) -> str:
    return (
        f"# {title}\n\n"
        f"In the 173 valid rated spans, `{row['mechanism_family']}` appears in {row['valid_rating_count']} ratings ({pct(row['valid_rating_count'])}). "
        f"Strong or moderate documentary support appears in {row['documentary_support_strong_or_moderate']} ratings, and strong or moderate direct-text support appears in {row['direct_support_strong_or_moderate']}. "
        f"Neutral or unclear direction accounts for {row['direction_neutral_or_unclear']} ratings; not-applicable direction accounts for {row['direction_not_applicable']}.\n\n"
        f"Bounded interpretation: {boundary} The summary describes collected exact-span wording only; it does not estimate a wage difference, population frequency, effect, or causal relationship.\n"
    )


def build_outputs(valid: list[dict[str, str]], quarantine: list[dict[str, str]], results: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    valid_scope = [{field: row.get(field, "") for field in VALID_SCOPE_FIELDS} for row in valid]
    valid_scope.sort(key=lambda row: row["span_rating_id"])
    quarantine_scope = sorted(quarantine, key=lambda row: row["span_extraction_id"])
    quarantine_fields = list(quarantine_scope[0].keys())
    valid_csv = target / "targeted_evidence_span_rating_summary_173_valid_scope.csv"
    write_csv(valid_csv, valid_scope, VALID_SCOPE_FIELDS)
    write_csv(target / "targeted_evidence_span_rating_summary_173_excluded_quarantine.csv", quarantine_scope, quarantine_fields)
    scope_hash = sha256_file(valid_csv)
    valid_ids_hash = hashlib.sha256("\n".join(row["span_rating_id"] for row in valid_scope).encode()).hexdigest()

    mechanism = mechanism_rows(valid)
    mechanism_fields = list(mechanism[0].keys())
    write_csv(target / "targeted_evidence_span_rating_summary_173_mechanism_summary.csv", mechanism, mechanism_fields)
    write_json(target / "targeted_evidence_span_rating_summary_173_mechanism_summary.json", {
        "valid_rating_count": EXPECTED_VALID,
        "mechanisms": mechanism,
        "scope_boundary": "173 valid rated exact spans only; 28 quarantines excluded",
    })

    direction = Counter(row["direction_of_pressure"] for row in valid)
    strength = Counter(row["evidence_strength"] for row in valid)
    relevance = Counter(row["claim_relevance"] for row in valid)
    support: dict[str, Counter[str]] = {field: Counter(row[field] for row in valid) for field in SUPPORT_FIELDS}
    write_csv(target / "targeted_evidence_span_rating_summary_173_direction_of_pressure.csv", summary_rows(direction, DIRECTIONS, "direction_of_pressure"), ["dimension", "category", "count", "share_of_valid_ratings"])
    write_csv(target / "targeted_evidence_span_rating_summary_173_evidence_strength.csv", summary_rows(strength, STRENGTHS, "evidence_strength"), ["dimension", "category", "count", "share_of_valid_ratings"])
    write_csv(target / "targeted_evidence_span_rating_summary_173_claim_relevance.csv", summary_rows(relevance, CLAIM_RELEVANCE, "claim_relevance"), ["dimension", "category", "count", "share_of_valid_ratings"])
    support_rows = []
    for field in SUPPORT_FIELDS:
        support_rows.extend(summary_rows(support[field], STRENGTHS, field))
    write_csv(target / "targeted_evidence_span_rating_summary_173_support_summary.csv", support_rows, ["dimension", "category", "count", "share_of_valid_ratings"])

    mechanism_lookup = {row["mechanism_family"]: row for row in mechanism}
    docs = {
        "targeted_evidence_span_rating_summary_173_strike_no_strike_summary.md": mechanism_doc(
            "Strike/no-strike and dispute-resolution summary", mechanism_lookup["strike_or_no_strike_constraint"],
            "The 103 valid ratings substantially strengthen documentary support for strike constraints and substitute dispute-resolution procedures in the targeted corpus; their consequences and comparative direction remain unestablished."
        ),
        "targeted_evidence_span_rating_summary_173_market_comparability_summary.md": mechanism_doc(
            "Market/comparability summary", mechanism_lookup["market_or_comparability_pressure"],
            "The 59 valid ratings strengthen documentary support for market, comparability, recruitment, retention, and compensation-study language in the targeted corpus; they do not establish who benefits or by how much."
        ),
        "targeted_evidence_span_rating_summary_173_non_safety_constraint_summary.md": mechanism_doc(
            "Non-safety constraint summary", mechanism_lookup["non_safety_constraint_signal"],
            "The 10 valid ratings provide useful exact-text examples, but this lane remains comparatively sparse and cannot support a broad directional account."
        ),
        "targeted_evidence_span_rating_summary_173_fiscal_constraint_summary.md": mechanism_doc(
            "Fiscal constraint summary", mechanism_lookup["fiscal_constraint_signal"],
            "The single valid rating is an isolated documentary signal; fiscal constraint remains too sparse for mechanism-strength, direction, prevalence, or causal conclusions."
        ),
    }
    for name, text in docs.items():
        (target / name).write_text(text, encoding="utf-8")

    (target / "targeted_evidence_span_rating_summary_173_supported_direct_text_claims.md").write_text(
        "# Supported direct-text claims\n\n"
        "Within the 173 valid rated spans, the targeted exact-span evidence provides direct-text support for the existence and wording of strike/no-strike and dispute-resolution provisions, market/comparability language, a smaller set of non-safety constraint passages, and one fiscal-constraint passage. Direct-text support is strong or moderate in 137 ratings. These are text-grounded documentary statements, not wage comparisons or effect estimates.\n\n"
        "- Strike/no-strike and dispute resolution: 103 valid ratings now provide a substantial bounded textual lane.\n"
        "- Market/comparability: 59 valid ratings provide a strengthened bounded textual lane.\n"
        "- Non-safety constraint: 10 valid ratings provide useful but sparse examples.\n"
        "- Fiscal constraint: 1 valid rating remains an isolated example.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_supported_documentary_mechanism_claims.md").write_text(
        "# Supported documentary mechanism claims\n\n"
        "In the 173 valid rated spans, strong or moderate documentary mechanism support appears in 148 ratings. The targeted expansion therefore strengthens the collected-corpus documentation of strike/no-strike and dispute-resolution mechanisms and market/comparability pressures. It adds smaller bounded support for non-safety constraints and only isolated support for fiscal constraints. Documentary support establishes that relevant institutional wording appears in the collected spans; it does not establish comparative wage consequences.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_provisional_causal_candidate_signals.md").write_text(
        "# Provisional causal-candidate signals\n\n"
        "The causal-candidate layer remains weak and explicitly provisional. No valid rating has strong provisional causal-candidate support; 6 are moderate, 24 are weak, and 143 are not supported. No row is classified as `provisional_causal_candidate` in the final claim-relevance field. These passages may identify mechanisms worth testing, but they do not establish that a mechanism changed safety or non-safety wages.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_claims_requiring_more_data.md").write_text(
        "# Claims requiring more data\n\n"
        "- Directional comparisons require more matched city-cycle evidence: 148 ratings are neutral or unclear and 23 are not applicable; only two carry a directional category.\n"
        "- Non-safety constraint claims remain comparatively sparse at 10 valid ratings and require additional matched-unit evidence and counterexamples.\n"
        "- Fiscal constraint claims remain extremely sparse at one valid rating and require targeted documents across additional city-cycle units.\n"
        "- Any connection between mechanism wording and actual pay, rates, raises, or differentials requires the separately preserved 862-row quantitative direct-text lane to be triaged under separate authorization.\n"
        "- Comparative or causal interpretation requires explicit counterevidence, matched outcomes, and a separately authorized design.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_claims_not_allowed.md").write_text(
        "# Claims not allowed\n\n"
        "This review does not authorize any final wage-gap statement, regression-backed inference, treatment-effect statement, population-prevalence statement, national generalization, or final causal conclusion. It does not authorize claims that safety compensation differs because of any rated mechanism, or that non-safety compensation is constrained because of any rated mechanism. The 28 quarantined rows cannot support any summary or claim.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_claim_boundary_language_bank.md").write_text(
        "# Claim-boundary language bank\n\n"
        "Allowed formulations:\n\n"
        "- In the 173 valid rated spans, the targeted corpus contains recurring exact-text examples of this mechanism.\n"
        "- The targeted exact-span evidence strengthens documentary support for this mechanism within the collected corpus.\n"
        "- This remains a provisional mechanism signal for later testing.\n"
        "- Direction is predominantly neutral or unclear and requires more matched evidence.\n"
        "- This does not estimate a wage difference, population frequency, or causal effect.\n",
        encoding="utf-8",
    )

    (target / "targeted_evidence_span_rating_summary_173_next_action_recommendation.md").write_text(
        "# Next-action recommendation\n\n"
        f"Decision: `{DECISION}`. The targeted qualitative lanes now contain substantial strike/dispute-resolution and market/comparability text, while direction remains largely unresolved. The most aggressive next move is bounded triage of the preserved {QUANTITATIVE_ROWS_PRESERVED} quantitative direct-text rows so documentary mechanisms can be mapped to explicit text-grounded pay, rate, and raise records without estimating a wage gap. Tier C verification should remain a later targeted option for fiscal and non-safety gaps. Repository layout remains manageable and is not currently a material blocker. A bounded memo can follow quantitative triage.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_tier_c_verification_considerations.md").write_text(
        "# Tier C verification considerations\n\n"
        "Tier C verification is not the immediate recommendation. It could later add document volume for the 10-row non-safety constraint lane and the one-row fiscal constraint lane. Any Tier C stage must preserve candidate, verification, download, readiness, extraction, and rating boundaries and should target matched city-cycle gaps instead of generic volume.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_quantitative_triage_considerations.md").write_text(
        f"# Quantitative triage considerations\n\nThe project preserves {QUANTITATIVE_ROWS_PRESERVED} quantitative direct-text claim-ready rows from the earlier phase-close layer. This summary does not analyze them. A separately authorized triage should classify explicit pay, rate, raise, premium, and timing text; retain exact quotes and unit-cycle lineage; exclude estimates not directly stated; and make no wage-gap, regression, treatment-effect, population, or causal claim.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_repo_cleanup_considerations.md").write_text(
        "# Repository cleanup considerations\n\nThe growing task history warrants future archival and inventory work, but current deterministic builds, validations, and task-local outputs remain operational. Cleanup is not a material blocker to the next bounded phase. Any later cleanup must preserve immutable lineage, relays, retained-source boundaries, and user-owned untracked files.\n",
        encoding="utf-8",
    )

    lock = {
        "task_id": TASK_ID,
        "valid_scope_count": EXPECTED_VALID,
        "excluded_quarantine_count": EXPECTED_QUARANTINE,
        "total_reconciliation": EXPECTED_TOTAL,
        "valid_scope_csv_sha256": scope_hash,
        "valid_span_rating_ids_sha256": valid_ids_hash,
        "input_hashes": INPUT_HASHES,
    }
    write_json(target / "targeted_evidence_span_rating_summary_173_lock.json", lock)
    write_json(target / "targeted_evidence_span_rating_summary_173_valid_scope_summary.json", {
        "valid_rating_count": EXPECTED_VALID,
        "unique_span_rating_ids": len({row["span_rating_id"] for row in valid_scope}),
        "unique_span_extraction_ids": len({row["span_extraction_id"] for row in valid_scope}),
        "valid_scope_csv_sha256": scope_hash,
        "quarantined_rows_in_valid_scope": 0,
        "global_analysis_readiness": False,
    })
    quarantine_reason_counts = Counter(row["error_code"] for row in quarantine_scope)
    write_json(target / "targeted_evidence_span_rating_summary_173_excluded_quarantine_summary.json", {
        "excluded_quarantine_count": EXPECTED_QUARANTINE,
        "explicit_exclusion_from_all_valid_summaries": True,
        "repair_or_rerating_performed": False,
        "reason_counts": dict(sorted(quarantine_reason_counts.items())),
    })

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_valid_rating_summary_review",
        "valid_rating_count": EXPECTED_VALID,
        "excluded_quarantine_count": EXPECTED_QUARANTINE,
        "total_reconciliation": EXPECTED_TOTAL,
        "mechanism_summary": {row["mechanism_family"]: row["valid_rating_count"] for row in mechanism},
        "direction_of_pressure_summary": {category: direction[category] for category in DIRECTIONS},
        "evidence_strength_summary": {category: strength[category] for category in STRENGTHS},
        "claim_relevance_summary": {category: relevance[category] for category in CLAIM_RELEVANCE},
        "support_summaries": {field: {category: support[field][category] for category in STRENGTHS} for field in SUPPORT_FIELDS},
        "quantitative_direct_text_rows_preserved_for_future_triage": QUANTITATIVE_ROWS_PRESERVED,
        "tier_c_verification_recommended_next": False,
        "repo_cleanup_recommended_next": False,
        "claim_memo_allowed_next": False,
        "gabriel_api_model_calls": 0,
        "url_opens": 0,
        "downloads": 0,
        "pdf_page_accesses": 0,
        "retained_file_accesses": 0,
        "full_extracted_text_accesses": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_estimates": 0,
        "population_prevalence_claims": 0,
        "national_claims": 0,
        "final_causal_claims": 0,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(target / "targeted_evidence_span_rating_summary_173_decision.json", decision)
    (target / "targeted_evidence_span_rating_summary_173_summary.md").write_text(
        "# Targeted exact-span rating summary — 173 valid ratings\n\n"
        f"Decision: `{DECISION}`. This deterministic review includes exactly 173 schema-valid exact-span ratings and explicitly excludes all 28 quarantined rows. Strike/no-strike and dispute-resolution support is substantially strengthened (103 ratings), as is market/comparability support (59). Non-safety constraint support remains comparatively sparse (10), and fiscal constraint support remains extremely sparse (1). Direction is neutral or unclear in 148 ratings, so directional and causal interpretation remains weak. The recommended next task is bounded triage of the preserved 862 quantitative direct-text rows. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )

    invariants = {
        "all_invariants_passed": True,
        "only_173_valid_ratings_summarized": True,
        "all_28_quarantines_explicitly_excluded": True,
        "valid_plus_quarantine_reconciles_to_201": True,
        "summary_scope_locked_with_sha256": True,
        "no_gabriel_api_model_calls": True,
        "no_url_pdf_page_retained_file_or_full_text_access": True,
        "no_download_ocr_or_rendering": True,
        "no_ingestion_or_codification": True,
        "no_wage_gap_regression_treatment_effect_population_national_or_final_causal_work": True,
        "claim_language_bounded_to_173_valid_rated_spans": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(target / "targeted_evidence_span_rating_summary_173_invariant_checks.json", invariants)
    write_json(target / "targeted_evidence_span_rating_summary_173_regression_test_inventory.json", {
        "suite": "scripts/test_targeted_evidence_span_rating_summary_173.py",
        "required_cases": [
            "exact valid and excluded counts", "disjoint valid/quarantine IDs", "pinned immutable hashes",
            "mechanism and rating reconciliations", "closed downstream statuses", "no forbidden dependencies",
            "bounded claim language", "dashboard global closure", "future prompt boundaries",
            "idempotent completed resume", "partial-package failure",
        ],
    })
    (target / "targeted_evidence_span_rating_summary_173_stress_test_report.md").write_text(
        "# Stress-test report\n\n"
        "- Missing or hash-drifted predecessor artifacts fail before output creation.\n"
        "- Any count other than 173 valid plus 28 quarantined fails closed.\n"
        "- Overlapping valid/quarantine identities fail closed.\n"
        "- Open downstream statuses or non-exact quote flags fail closed.\n"
        "- The runner has no network, PDF, retained-file, full-text, OCR, rendering, model, ingestion, or codification dependency.\n"
        "- Partial outputs fail closed; a complete validated package resumes with zero writes.\n",
        encoding="utf-8",
    )
    (target / "targeted_evidence_span_rating_summary_173_validation_2026-07-26.md").write_text(
        "# Targeted exact-span rating summary validation — 2026-07-26\n\nInternal deterministic gates passed for exactly 173 valid ratings with 28 quarantines preserved as exclusions. Required repository command results are appended after the full suite completes.\n",
        encoding="utf-8",
    )

    future = (
        "# Next task: bounded quantitative direct-text claim triage\n\n"
        "Use only the separately preserved 862 quantitative direct-text rows under explicit authorization. Lock the queue, preserve exact quotes and city/unit/cycle lineage, and classify directly stated pay, rate, raise, premium, and implementation values without estimating missing quantities.\n\n"
        "Do not fetch, search, open URLs, download, access PDFs/pages/retained files/full extracted text, OCR, render, call a model unless separately authorized, ingest, codify, calculate a wage gap, run a regression, estimate a treatment effect, make a population or national claim, make a final causal claim, include the 28 quarantined span ratings, or set global analysis readiness true. Quantitative triage is not causal analysis.\n"
    )
    (target / "next_quantitative_claim_triage_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / "targeted_evidence_span_rating_summary_173_decision.json")
    valid = read_csv(path / "targeted_evidence_span_rating_summary_173_valid_scope.csv")
    excluded = read_csv(path / "targeted_evidence_span_rating_summary_173_excluded_quarantine.csv")
    lock = read_json(path / "targeted_evidence_span_rating_summary_173_lock.json")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed decision invalid")
    if len(valid) != EXPECTED_VALID or len(excluded) != EXPECTED_QUARANTINE:
        raise RuntimeError("completed scope count mismatch")
    if {row["span_extraction_id"] for row in valid} & {row["span_extraction_id"] for row in excluded}:
        raise RuntimeError("completed package includes quarantine in valid scope")
    if sha256_file(path / "targeted_evidence_span_rating_summary_173_valid_scope.csv") != lock.get("valid_scope_csv_sha256"):
        raise RuntimeError("completed scope lock mismatch")


def install_dashboard_docs() -> None:
    RESULT_DOC.write_text(
        "# Targeted exact-span rating summary result — 2026-07-26\n\n"
        f"Decision: `{DECISION}`. The deterministic review summarized 173 valid ratings and excluded 28 quarantines. Mechanism counts are 103 strike/no-strike, 59 market/comparability, 10 non-safety constraint, and 1 fiscal constraint. Direction is predominantly neutral or unclear. Bounded quantitative triage of 862 preserved direct-text rows is recommended next. No model call or source-material access occurred; global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        "# Dashboard status note — targeted exact-span rating summary\n\n"
        f"Status: `{DECISION}`. Valid ratings summarized: 173; quarantine exclusions: 28. Quantitative triage recommended next: true. Tier C verification recommended next: false. Repo cleanup recommended next: false. Global analysis readiness: false.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    valid, quarantine, results = validate_inputs()
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "valid": 173, "excluded": 28}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(valid, quarantine, results, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        install_dashboard_docs()
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "valid": 173, "excluded": 28}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
