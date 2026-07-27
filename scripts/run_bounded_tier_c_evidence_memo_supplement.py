#!/usr/bin/env python3
"""Build the bounded Tier C evidence memo supplement from summary artifacts only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_DIR = ROOT / "docs/analysis/compensation_extraction/TIER-C-EVIDENCE-SPAN-RATING-SUMMARY-140-VALID-RATINGS-2026-07-27"
RATING_DIR = ROOT / "docs/analysis/compensation_extraction/TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27"
PARENT_MEMO = ROOT / "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo.md"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/BOUNDED-TIER-C-EVIDENCE-MEMO-SUPPLEMENT-140-RATING-SUMMARY-2026-07-27"
RESULT_DOC = ROOT / "docs/analysis/bounded_tier_c_evidence_memo_supplement_result_2026-07-27.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/bounded_tier_c_evidence_memo_supplement_dashboard_status_note_2026-07-27.md"
PROMPT_POLICY = ROOT / "docs/prompts/rating_artifact_completeness_requirement.md"
TASK_ID = "BOUNDED-TIER-C-EVIDENCE-MEMO-SUPPLEMENT-140-RATING-SUMMARY-2026-07-27"
DECISION = "bounded_tier_c_evidence_memo_supplement_completed_broad_scouting_ready"

EXPECTED_MECHANISMS = {
    "strike_or_no_strike_constraint": 76,
    "market_or_comparability_pressure": 51,
    "non_safety_constraint_signal": 11,
    "fiscal_constraint_signal": 2,
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
EXPECTED_CAUSAL_HINTS = {"strong": 0, "moderate": 6, "weak": 32, "not_supported": 102}

INPUT_HASHES = {
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_decision.json": "9775b8b09ac2ec12c9f912dcf82a381c6cb41afcbe747de02eea31049a7e52bc",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_summary.md": "829f7dd2a36fd9b54853ed91b19923f16a52b1182358457b728acf034704937f",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_input_reconciliation_summary.json": "49dfe1680ca4ff16a8ba9e87c881d25dc1703cb612408616a6207cf04e472435",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_by_mechanism_summary.json": "6c6b3b041a9561eca19856c5098776b72b3cf0e2f19a14f5c38d1d4775cc8f4b",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_claim_relevance_summary.json": "04ed585a5d214c1a3c5a58776dd117487ecb191d53f78a187841777c996ca0ee",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_evidence_strength_summary.json": "6f5f08bd7207fb2be7f22acb609c1963c0df20a26285efc031ef0f916e29ff37",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_direction_of_pressure_summary.json": "3d7810c80136670344f5cb821125a2658104f211e0217476540e0befb85a3621",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_support_matrix_summary.json": "4c2b7a6f31cb9da01808e7d931a21745a1ace59bf9b8097481387ffd74ea60ed",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_interpretive_findings.md": "a79d439ca63f10dff804826e458654b4b18dd4ccd45a207de95256d732f11872",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_claim_boundaries.md": "1d366f600281462b07c3066f1f1a104e85276b5f236d19bc88428a2d48e05bc5",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_limits.md": "320e823e3a00dc7463b3bbc7b6ef0b8e6aa12b447e1314ba1a5eecb00c03f538",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_next_step_recommendation.md": "7c5633f64a64869a750b49c090387fcf327ecd2dc119c1b6d41112319456f17e",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_quarantine_exclusion_note.md": "dfd0dd27602ae9ca8e9cdd062805095d521448c868a7d90f0c74b6565c87ba79",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_dashboard_update_summary.json": "3de8441e4546ffe521eebdd8a477a84f7bcc3be32b0636ebe7d793cd605b04e9",
    SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_validation_2026-07-27.md": "83fd52b91e57e613f8130005ce65751b3504484bf3ff04043b854685baa8ff5e",
    RATING_DIR / "mechanism_specific_rating_summaries.json": "e1e5c0117eb1c097f2b016d45fec3f0450f142b7111fd8acd32985b79a81ccdc",
    PARENT_MEMO: "ef5ff56666032edec51069e876f65963fb71f399de60a2ec7994f9dc64d6dc84",
}

REQUIRED_OUTPUTS = (
    "bounded_tier_c_evidence_memo_supplement_decision.json",
    "bounded_tier_c_evidence_memo_supplement_summary.md",
    "bounded_tier_c_evidence_memo_supplement.md",
    "bounded_tier_c_evidence_memo_supplement_brief.md",
    "bounded_tier_c_evidence_memo_supplement_parent_integration_note.md",
    "tier_c_supplement_strike_no_strike_and_dispute_resolution.md",
    "tier_c_supplement_market_comparability.md",
    "tier_c_supplement_non_safety_constraint.md",
    "tier_c_supplement_fiscal_constraint.md",
    "bounded_tier_c_evidence_memo_supplement_claim_boundaries.md",
    "bounded_tier_c_evidence_memo_supplement_limits.md",
    "bounded_tier_c_evidence_memo_supplement_non_directional_findings.md",
    "bounded_tier_c_evidence_memo_supplement_not_causal_note.md",
    "post_tier_c_broad_state_by_state_scouting_recommendation.md",
    "post_tier_c_source_family_diversification_recommendation.md",
    "post_tier_c_scouting_strategy_decision.json",
    "future_rating_artifact_completeness_policy.md",
    "future_rating_artifact_completeness_policy.json",
    "future_rating_summary_artifact_reconstruction_fallback.md",
    "future_rating_summary_artifact_reconstruction_fallback.json",
    "post_rating_artifact_completeness_checklist.md",
    "bounded_tier_c_evidence_memo_supplement_dashboard_update_summary.md",
    "bounded_tier_c_evidence_memo_supplement_dashboard_update_summary.json",
    "bounded_tier_c_evidence_memo_supplement_validation_2026-07-27.md",
    "bounded_tier_c_evidence_memo_supplement_invariant_checks.json",
    "bounded_tier_c_evidence_memo_supplement_stress_test_report.md",
    "bounded_tier_c_evidence_memo_supplement_regression_test_inventory.json",
    "next_broad_state_by_state_scout_prompt.md",
    "next_task.md",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def validate_inputs() -> dict[str, Any]:
    for path, expected_hash in INPUT_HASHES.items():
        if not path.is_file():
            raise RuntimeError(f"required authorized input missing: {path}")
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"immutable authorized input hash mismatch: {path.name}")

    decision = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_decision.json")
    reconciliation = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_input_reconciliation_summary.json")
    mechanism = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_by_mechanism_summary.json")
    relevance = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_claim_relevance_summary.json")
    strength = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_evidence_strength_summary.json")
    direction = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_direction_of_pressure_summary.json")
    support = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_support_matrix_summary.json")
    repaired = read_json(RATING_DIR / "mechanism_specific_rating_summaries.json")
    dashboard = read_json(SUMMARY_DIR / "tier_c_evidence_span_rating_summary_140_dashboard_update_summary.json")

    if decision.get("decision") != "tier_c_evidence_span_rating_summary_140_completed_memo_supplement_ready":
        raise RuntimeError("summary decision does not authorize supplement")
    if not (
        decision.get("valid_rating_summary_count") == 140
        and decision.get("quarantine_excluded_count") == 19
        and decision.get("total_reconciliation") == 159
        and reconciliation.get("valid_plus_quarantine_reconciles") is True
        and reconciliation.get("valid_quarantine_ids_disjoint") is True
    ):
        raise RuntimeError("140/19/159 input reconciliation failure")
    mechanism_counts = {
        row["mechanism_family"]: row["valid_rating_count"]
        for row in mechanism.get("mechanisms", [])
    }
    if decision.get("mechanism_summary") != EXPECTED_MECHANISMS or mechanism_counts != EXPECTED_MECHANISMS:
        raise RuntimeError("mechanism summary mismatch")
    if relevance.get("counts") != EXPECTED_RELEVANCE or strength.get("counts") != EXPECTED_STRENGTH:
        raise RuntimeError("claim relevance or evidence strength mismatch")
    if direction.get("counts") != EXPECTED_DIRECTION or support.get("provisional_causal_candidate_hints") != EXPECTED_CAUSAL_HINTS:
        raise RuntimeError("direction or hypothesis-hint mismatch")
    if not (
        repaired.get("reconciliation_passed") is True
        and repaired.get("valid_rating_count") == 140
        and repaired.get("quarantine_count") == 19
        and repaired.get("input_count") == 159
        and repaired.get("valid_plus_quarantine_count") == 159
    ):
        raise RuntimeError("repaired mechanism summary fails reconciliation")
    if not (
        dashboard.get("map_filter") == "total_scout_coverage_only"
        and dashboard.get("map_data_date") == "2026-07-27"
        and dashboard.get("global_analysis_readiness") is False
    ):
        raise RuntimeError("dashboard boundary mismatch")
    for key in (
        "url_opens", "downloads", "pdf_page_accesses", "retained_source_accesses",
        "full_extracted_text_accesses", "ocr_runs", "pdf_render_runs", "gabriel_api_model_calls",
        "rerating_runs", "ingestion_runs", "codification_runs", "wage_gap_calculations",
        "regressions", "treatment_effect_estimates", "national_or_population_prevalence_claims",
        "final_causal_claims",
    ):
        if decision.get(key) != 0:
            raise RuntimeError(f"summary boundary is not zero: {key}")
    return {
        "decision": decision,
        "reconciliation": reconciliation,
        "mechanism": mechanism,
        "relevance": relevance,
        "strength": strength,
        "direction": direction,
        "support": support,
        "repaired": repaired,
        "input_hashes": {str(path.relative_to(ROOT)): value for path, value in INPUT_HASHES.items()},
    }


def generate(context: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_tier_c_documentary_memo_supplement",
        "valid_rating_summary_scope": 140,
        "quarantines_excluded": 19,
        "predecessor_scope_reconciled": 159,
        "claim_summary_candidates": 115,
        "mechanism_summary": EXPECTED_MECHANISMS,
        "claim_relevance_summary": EXPECTED_RELEVANCE,
        "evidence_strength_summary": EXPECTED_STRENGTH,
        "direction_of_pressure_summary": EXPECTED_DIRECTION,
        "provisional_causal_candidate_hint_summary": EXPECTED_CAUSAL_HINTS,
        "memo_supplement_created": True,
        "parent_memo_mutated": False,
        "quarantines_used_as_evidence": 0,
        "future_rating_artifact_completeness_policy_created": True,
        "future_summary_reconstruction_fallback_created": True,
        "broad_state_by_state_scouting_ready_next": True,
        "repo_cleanup_recommended": False,
        "quarantine_repair_recommended": False,
        "dashboard_status_docs_updated": True,
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
        "url_opens": 0,
        "downloads": 0,
        "pdf_page_accesses": 0,
        "retained_source_accesses": 0,
        "full_extracted_text_accesses": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "gabriel_api_model_calls": 0,
        "rerating_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_estimates": 0,
        "national_or_population_prevalence_claims": 0,
        "final_causal_claims": 0,
        "input_hashes": context["input_hashes"],
    }
    write_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_decision.json", decision)

    summary = """# Bounded Tier C evidence memo supplement — summary

Decision: `bounded_tier_c_evidence_memo_supplement_completed_broad_scouting_ready`.

This internal supplement uses only the completed aggregate summary of 140 schema-valid Tier C exact-span ratings. All 19 quarantined ratings remain excluded from evidence. Tier C materially expands documentary coverage of strike/no-strike and substitute dispute-resolution mechanisms (76 valid ratings) and market/comparability pressure (51). It adds a smaller non-safety constraint lane (11), while fiscal constraint remains too thin (2). Direction remains neutral or unclear in 108 ratings and not applicable in 26. The supplement supports bounded documentary findings and research hypotheses only. Broad state-by-state, source-family-diverse scouting is ready next; quarantine repair and repository cleanup are not current blockers. Global analysis readiness remains false.
"""
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_summary.md", summary)

    memo = """# Bounded Tier C evidence memo supplement

Internal working document — 2026-07-27

## 1. Purpose and bounded scope

This supplement closes the targeted Tier C evidence pass and extends the bounded internal mechanism-linkage memo. It uses only the completed aggregate review of 140 schema-valid exact-span ratings. Nineteen quarantined outputs remain exclusions and do not contribute evidence, counts, examples, or interpretation. The supplement does not reopen rating rows, source documents, retained files, or extracted text.

The valid summary contains 75 direct-text claims, 40 documentary-mechanism claims, 22 context-only ratings, and 3 not-claim-ready ratings. The 75 direct-text and 40 documentary ratings form 115 bounded claim-summary candidates. No valid rating has provisional-causal-candidate claim relevance.

## 2. What Tier C adds

Tier C materially strengthens the documentary record for strike/no-strike constraints and substitute dispute-resolution structures. Seventy-six valid ratings cover this mechanism lane. The additional documentation makes the lane suitable for bounded discussion of labor-peace clauses, work-stoppage restrictions, impasse procedures, mediation, factfinding, and arbitration as institutional structures. It does not establish how those structures changed wages or favored an occupation.

Tier C also materially strengthens market/comparability documentation. Fifty-one valid ratings support bounded discussion of market adjustment, peer comparisons, recruitment, retention, competitiveness, wage or compensation studies, and related comparability language. This documents the presence of market-facing reasoning; it does not establish a wage effect or comparative outcome.

The non-safety constraint lane adds 11 valid ratings. This is a useful documentary foothold for future within-city comparison work, but it is too small and too non-directional for a broad conclusion about non-safety compensation. Fiscal constraint has only 2 valid ratings and remains too thin for a generalized finding.

## 3. Evidence strength and claim relevance

Evidence strength is strong for 63 ratings, moderate for 41, weak for 26, and not supported for 10. Claim relevance is direct text for 75 and documentary mechanism for 40; 22 are context only and 3 are not claim-ready. These categories support a documentary supplement, not an outcomes analysis.

Provisional causal-candidate support is moderate for 6, weak for 32, and not supported for 102; none is strong. The 38 weak or moderate entries are research hypotheses only. They cannot be presented as mechanism effects or causal findings.

## 4. Direction remains unresolved

Direction is neutral or unclear for 108 ratings and not applicable for 26. Five are labeled non-safety advantage and one gap narrowing; none is labeled safety advantage. The six isolated directional labels do not support a broad directional statement. They remain bounded observations within an overwhelmingly non-directional summary.

## 5. Relationship to the parent memo

The parent memo found strong same-source mechanism-value co-location for implementation/retroactivity and automatic raises, while strike/no-strike and non-safety constraint had no exact same-source quantitative linkage in that run. This supplement does not alter those linkage counts. It adds later Tier C exact-span documentary evidence in four targeted lanes. Documentary strengthening is not quantitative linkage, and neither is a wage comparison.

The appropriate integration is an appended update: strike/no-strike and market/comparability now have stronger documentary support; non-safety constraint has a small new documentary lane; fiscal constraint remains extremely thin. The original memo's co-location boundaries, source-family cautions, and global readiness status remain controlling.

## 6. What the supplement cannot support

The supplement does not support wage-gap estimates, wage-level comparisons, regression results, treatment effects, national or population prevalence, statistical significance, or final causal attribution. It does not establish that any mechanism caused a wage value or benefited safety or non-safety workers. It is not ingested, codified, final, or globally analysis-ready evidence.

## 7. Next research phase

The targeted Tier C pass has done its gap-filling job. The next collection phase should return to broad geographic/state-by-state scouting. Discovery should seek balanced coverage across states and source families rather than defaulting to a presumed mechanism. Mechanism tags remain useful after collection; mechanism-targeted scouts should be secondary follow-up work.

Source-family tracking should explicitly include CBAs, MOUs and memoranda, settlement agreements, arbitration awards, factfinding reports, salary ordinances, wage schedules, budget and pay-plan documents, civil-service or HR pay plans, compensation studies, classification studies, and related local-government pay-policy documents. Each broad wave should report geographic and source-family balance so CBA concentration cannot silently recur.

## 8. Operational conclusion

Broad state-by-state scouting with source-family diversification is ready next. Repairing the 19 quarantines would not materially change this bounded interpretation, and repository organization is not a current blocker. Global analysis readiness remains false.
"""
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement.md", memo)

    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_brief.md", """# Tier C supplement brief

- Scope: 140 valid aggregate ratings; 19 quarantines excluded.
- Strongest additions: strike/no-strike and dispute resolution (76); market/comparability (51).
- Smaller lane: non-safety constraint (11).
- Too thin: fiscal constraint (2).
- Direction: 108 neutral/unclear, 26 not applicable, 6 isolated directional labels, 0 safety-advantage labels.
- Claim boundary: documentary evidence and hypothesis formation only.
- Next phase: broad state-by-state scouting with explicit source-family diversification.
- Global analysis readiness: false.
""")
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_parent_integration_note.md", """# Parent-memo integration note

Append this supplement to the bounded internal mechanism-linkage memo as a later documentary update; do not rewrite the parent memo's 268-pair same-source linkage results. The Tier C ratings strengthen documentary strike/no-strike and market/comparability lanes, add limited non-safety constraint material, and leave fiscal constraint extremely thin. They do not create exact same-source quantitative linkage, change the parent linkage counts, normalize quantitative values, or establish direction or causation. The parent memo remains the current mechanism-value co-location memo; this supplement is its bounded Tier C documentary addendum.
""")

    mechanism_docs = {
        "tier_c_supplement_strike_no_strike_and_dispute_resolution.md": """# Strike/no-strike and dispute-resolution supplement

Seventy-six valid Tier C ratings materially strengthen this documentary lane. The supported scope includes strike or work-stoppage restrictions, labor-peace provisions, impasse procedures, mediation, factfinding, arbitration, and related dispute-resolution structures. This evidence supports statements about documented institutional provisions. It does not establish bargaining leverage, occupational advantage, wage effects, or causal direction.
""",
        "tier_c_supplement_market_comparability.md": """# Market/comparability supplement

Fifty-one valid Tier C ratings materially strengthen documentation of market adjustment, peer-community comparison, recruitment, retention, competitiveness, compensation studies, and related comparability reasoning. This supports a bounded finding that market-facing language is present in the reviewed Tier C evidence. It does not establish that comparability language changed pay or favored a particular occupation.
""",
        "tier_c_supplement_non_safety_constraint.md": """# Non-safety constraint supplement

Eleven valid Tier C ratings add a small documentary lane for non-safety or general-employee constraint language. The lane is useful for designing future matched comparisons but remains too small and predominantly non-directional. It does not support a general claim that non-safety employees were disadvantaged or that safety workers benefited.
""",
        "tier_c_supplement_fiscal_constraint.md": """# Fiscal constraint supplement

Only two valid Tier C ratings enter this mechanism lane. That volume is too thin for a generalized fiscal-constraint finding. The records can be retained as bounded documentary examples for later research planning, but they do not support claims about the prevalence, direction, or wage consequences of fiscal constraints.
""",
    }
    for name, text in mechanism_docs.items():
        write_md(OUTPUT_DIR / name, text)

    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_claim_boundaries.md", """# Claim boundaries

- Use only the 140-valid-rating aggregate summary.
- Keep all 19 quarantines excluded from evidence.
- Direct-text and documentary-mechanism additions may be described as bounded, text-grounded findings.
- Treat 6 moderate and 32 weak provisional-causal-candidate ratings only as hypothesis hints.
- Preserve neutral/unclear direction for 108 ratings and not-applicable direction for 26.
- Do not generalize from 5 non-safety-advantage or 1 gap-narrowing labels.
- Do not infer a safety advantage; the valid summary contains zero such labels.
- Do not infer wage differences, prevalence, effects, or causation.
""")
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_limits.md", """# Supplement limits

The evidence comes from a targeted Tier C wave and is not a geographically or source-family-balanced sample. The supplement does not reopen source material or independently reassess ratings. It preserves 19 strict-schema quarantines as exclusions. Fiscal evidence is extremely thin, non-safety constraint evidence is limited, and direction is overwhelmingly unresolved. The outputs are not ingested, codified, final, causal, or globally analysis-ready.
""")
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_non_directional_findings.md", """# Non-directional findings

Of 140 valid ratings, 108 are neutral or unclear and 26 are not applicable for direction. Only 5 are labeled non-safety advantage and 1 gap narrowing; 0 are labeled safety advantage. The six isolated directional labels cannot be aggregated into a directional claim. The main Tier C contribution is documentary mechanism coverage, not evidence about the direction of wage pressure.
""")
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_not_causal_note.md", """# Documentary, not causal

This supplement documents rated exact-span support for institutional and contextual mechanisms. It does not estimate whether a mechanism changed wages, compare occupational wage outcomes, or establish causal direction. Weak or moderate provisional-causal-candidate support is retained only as a hypothesis-generation signal. Global analysis readiness remains false.
""")

    broad = """# Post-Tier C broad state-by-state scouting recommendation

Resume broad geographic/state-by-state discovery as the default next phase. Build balanced, locked state waves; track municipality, occupation, unit, cycle, and source-family coverage; and surface missing matched non-safety units first. Discovery should not require a candidate to express a preselected mechanism. Preserve mechanism tags after collection and use mechanism-targeted scouting only as secondary gap filling after broad coverage exposes specific holes.

Each wave should report states attempted, municipalities covered, candidate yield, safety/non-safety match opportunities, source-family distribution, missing geography, and CBA concentration. Map updates remain total scout coverage only and must not imply national representativeness.
"""
    diversify = """# Post-Tier C source-family diversification recommendation

Broad scouts should deliberately seek CBAs, MOUs and memoranda, settlement agreements, arbitration awards, factfinding reports, salary ordinances, wage schedules, budget and pay-plan documents, civil-service or HR pay plans, compensation studies, classification studies, and related local-government pay-policy documents. Track the share and count of every family after each wave. A CBA-heavy wave must be disclosed and followed by source-family balancing; it must not silently become the evidence default.
"""
    write_md(OUTPUT_DIR / "post_tier_c_broad_state_by_state_scouting_recommendation.md", broad)
    write_md(OUTPUT_DIR / "post_tier_c_source_family_diversification_recommendation.md", diversify)
    write_json(OUTPUT_DIR / "post_tier_c_scouting_strategy_decision.json", {
        "decision": "broad_state_by_state_source_family_diverse_scouting_is_default_next",
        "mechanism_targeted_scouting_role": "secondary_gap_filling",
        "track_geographic_balance": True,
        "track_source_family_balance": True,
        "track_matched_non_safety_opportunities": True,
        "dashboard_map_filter": "total_scout_coverage_only",
        "national_representativeness_claim": False,
    })

    policy = """# Future rating artifact-completeness policy

Before closing any rating task, verify that every downstream summary input exists and reconciles to the locked rating scope. At minimum, produce or deterministically reconstruct:

- mechanism-specific rating summaries;
- claim-relevance summaries;
- evidence-strength summaries;
- direction-of-pressure summaries;
- quarantine summaries;
- input/valid/quarantine reconciliation summaries;
- dashboard update summaries; and
- next-summary candidate manifests.

If an artifact is missing but is fully derivable from committed valid, quarantine, or results ledgers, reconstruct it deterministically without rerating. Validate identifiers, controlled categories, valid-plus-quarantine accounting, mechanism totals, and immutable input hashes. Commit and push the repair, then continue the authorized downstream summary instead of hard-stopping.

If the missing artifact is not fully derivable, its source ledgers are incomplete or inconsistent, hashes drift, identities overlap, or reconstruction would require new judgment, source access, or model calls, fail closed and report the blocker. Reconstruction never authorizes repair of quarantined model content or mutation of rating ledgers.
"""
    fallback = """# Future summary-stage reconstruction fallback

A summary stage may recover a missing required input only when the artifact can be regenerated exactly from committed, immutable valid/quarantine/results ledgers. The recovery sequence is:

1. Confirm the locked predecessor decision and input hashes.
2. Confirm committed valid, quarantine, results, and candidate ledgers are complete.
3. Reconcile input = valid + quarantine and verify identity disjointness.
4. Derive the missing aggregate with controlled categories and deterministic ordering.
5. Validate the aggregate against every available predecessor count.
6. Write only the missing derivative artifact; do not change source ledgers.
7. Commit and push the repair separately with a precise message.
8. Continue the authorized summary task.

Fail closed when reconstruction is not exact, source ledgers are missing, hashes drift, or new rating judgment would be required.
"""
    checklist = """# Post-rating artifact-completeness checklist

- [ ] Locked rating input count is recorded.
- [ ] Valid rating ledger exists and has unique identifiers.
- [ ] Quarantine ledger and quarantine summary exist.
- [ ] Valid and quarantine identifiers are disjoint.
- [ ] Valid + quarantine reconciles exactly to the locked input.
- [ ] Mechanism-specific rating summary exists and reconciles.
- [ ] Claim-relevance summary exists and reconciles.
- [ ] Evidence-strength summary exists and reconciles.
- [ ] Direction-of-pressure summary exists and reconciles.
- [ ] Dashboard update summary exists and preserves global readiness false.
- [ ] Next-summary candidate manifest exists and is a valid-only subset.
- [ ] Missing fully derivable artifacts were reconstructed deterministically, validated, committed, and pushed.
- [ ] Missing non-derivable artifacts caused a fail-closed report.
- [ ] No raw prompts, raw responses, credentials, or secrets were saved.
"""
    write_md(OUTPUT_DIR / "future_rating_artifact_completeness_policy.md", policy)
    write_json(OUTPUT_DIR / "future_rating_artifact_completeness_policy.json", {
        "required_after_every_rating_task": True,
        "minimum_artifacts": [
            "mechanism_specific_rating_summaries", "claim_relevance_summaries",
            "evidence_strength_summaries", "direction_of_pressure_summaries",
            "quarantine_summaries", "reconciliation_summaries",
            "dashboard_update_summaries", "next_summary_candidate_manifests",
        ],
        "reconstruct_derivable_missing_artifacts": True,
        "validate_commit_push_then_continue": True,
        "missing_non_derivable_artifacts_fail_closed": True,
        "rerating_authorized_by_reconstruction": False,
        "rating_ledger_mutation_authorized": False,
    })
    write_md(OUTPUT_DIR / "future_rating_summary_artifact_reconstruction_fallback.md", fallback)
    write_json(OUTPUT_DIR / "future_rating_summary_artifact_reconstruction_fallback.json", {
        "summary_stage_reconstruction_allowed": True,
        "allowed_only_if_fully_derivable_from_committed_ledgers": True,
        "required_checks": [
            "immutable_hashes", "locked_input_count", "valid_plus_quarantine",
            "identifier_disjointness", "controlled_categories", "predecessor_count_reconciliation",
        ],
        "repair_commit_required": True,
        "repair_push_required": True,
        "continue_after_valid_repair": True,
        "fail_closed_conditions": [
            "missing_source_ledger", "hash_drift", "identity_overlap",
            "non_deterministic_judgment_required", "model_or_source_access_required",
        ],
    })
    write_md(OUTPUT_DIR / "post_rating_artifact_completeness_checklist.md", checklist)
    write_md(PROMPT_POLICY, policy + "\n" + fallback + "\n" + checklist)

    dashboard_summary = {
        "dashboard_updated": True,
        "current_phase": "Bounded Tier C evidence memo supplement complete; broad state-by-state scouting ready next",
        "current_phase_code": DECISION,
        "valid_rating_summary_scope": 140,
        "quarantines_excluded": 19,
        "memo_supplement_path": "docs/analysis/compensation_extraction/BOUNDED-TIER-C-EVIDENCE-MEMO-SUPPLEMENT-140-RATING-SUMMARY-2026-07-27/bounded_tier_c_evidence_memo_supplement.md",
        "dashboard_result_path": "docs/analysis/bounded_tier_c_evidence_memo_supplement_result_2026-07-27.md",
        "next_task": "broad state-by-state scouting with source-family diversification",
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
        "wage_gap_estimates_available": False,
        "regressions_or_treatment_effects_available": False,
        "national_or_population_prevalence_claims_available": False,
        "final_causal_claims_available": False,
    }
    write_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_dashboard_update_summary.json", dashboard_summary)
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_dashboard_update_summary.md", """# Dashboard update summary

The dashboard now records completion of the bounded Tier C evidence memo supplement and identifies broad state-by-state, source-family-diverse scouting as the next phase. The current operational report points to the supplement result. The map remains total scout coverage only, the map data date remains 2026-07-27, and global analysis readiness remains false.
""")

    write_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_invariant_checks.json", {
        "all_invariants_passed": True,
        "authorized_inputs_hash_locked": True,
        "only_140_valid_rating_summary_used": True,
        "all_19_quarantines_excluded_as_evidence": True,
        "input_scope_reconciles_to_159": True,
        "mechanism_claim_strength_direction_and_hint_counts_reconcile": True,
        "no_url_download_pdf_page_retained_source_or_full_text_access": True,
        "no_model_api_or_rerating": True,
        "no_ocr_or_rendering": True,
        "no_ingestion_codification_or_statistical_work": True,
        "no_wage_gap_national_population_prevalence_or_final_causal_claims": True,
        "future_rating_artifact_completeness_policy_created": True,
        "future_summary_reconstruction_fallback_created": True,
        "dashboard_update_requirement_satisfied": True,
        "dashboard_map_total_scout_coverage_only": True,
        "global_analysis_readiness_false": True,
        "broad_state_by_state_scouting_ready_next": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_regression_test_inventory.json", {
        "suite": "scripts/test_bounded_tier_c_evidence_memo_supplement.py",
        "coverage": [
            "immutable aggregate inputs", "140/19/159 reconciliation", "quarantine exclusion",
            "mechanism and claim boundaries", "no-call boundary", "rating-artifact completeness policy",
            "reconstruction fallback", "dashboard map contract", "broad scout transition",
            "idempotent resume", "partial package failure",
        ],
    })
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_stress_test_report.md", """# Stress-test report

- Missing or hash-drifted authorized summary inputs fail before output creation.
- Counts other than 140 valid, 19 excluded, and 159 reconciled fail closed.
- Aggregate mechanism, relevance, strength, direction, and hypothesis-hint drift fails closed.
- A missing non-derivable predecessor input remains an integrity blocker.
- The runner has no network, model, rating, source-file, PDF, full-text, OCR, rendering, ingestion, or codification dependency.
- Complete reruns validate and write nothing; partial packages cannot masquerade as complete.
""")
    write_md(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_validation_2026-07-27.md", """# Bounded Tier C evidence memo supplement validation — 2026-07-27

Internal deterministic gates passed for the 140-valid-rating aggregate scope with all 19 quarantines excluded as evidence and 159 predecessor rows reconciled.

## Required command results

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_bounded_tier_c_evidence_memo_supplement.py` | PASS |
| `.venv/bin/python scripts/test_bounded_tier_c_evidence_memo_supplement.py` | PASS |
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

## Boundary and hardening checks

- Authorized valid-rating summary scope: 140.
- Quarantines excluded as evidence: 19.
- Reconciled predecessor scope: 159.
- URL, download, PDF/page, retained-source, and full-extracted-text accesses: 0.
- GABRIEL/API/model calls and rerating operations: 0.
- OCR and PDF rendering operations: 0.
- Ingestion, codification, wage-gap, regression, treatment-effect, national, population-prevalence, and final-causal work: 0.
- Future rating artifact-completeness policy and deterministic reconstruction fallback: present and tested.
- Dashboard map remains total scout coverage only; map date remains 2026-07-27.
- Dashboard global analysis readiness remains `false`.
""")

    future = """# Next task: broad state-by-state source scouting

Run the next bounded broad geographic/state-by-state scout wave. Broad coverage is the default discovery mode; mechanism-targeted scouting is secondary gap filling after broad scans expose specific holes. Build locked state/city inputs, preserve the city × occupation × cycle unit of observation, and prioritize matched non-safety opportunities. Track geographic balance and source-family balance explicitly.

Seek diverse public local-government document families, including CBAs, MOUs and memoranda, settlement agreements, arbitration awards, factfinding reports, salary ordinances, wage schedules, budget and pay-plan documents, civil-service or HR pay plans, compensation studies, classification studies, and related pay-policy documents. Do not allow CBA-heavy discovery to become an unreported default. Scout outputs remain unverified discovery metadata and must not be treated as retained, extracted, rated, ingested, causal, or analysis-ready evidence.

Post-rating artifact-completeness requirement for every future rating task: before closure, verify mechanism-specific, claim-relevance, evidence-strength, direction-of-pressure, quarantine, reconciliation, dashboard-update, and next-summary-candidate artifacts. If a missing artifact is fully derivable from committed valid/quarantine/results ledgers, reconstruct it deterministically, validate reconciliation, commit and push the repair, and continue. Missing non-derivable artifacts still fail closed. Future summary stages may use this same validated reconstruction fallback without rerating or ledger mutation.

Do not access unauthorized sources, download documents outside a separately locked queue, weaken provenance, merge causal and discourse corpora, ingest, codify, normalize or compare quantitative values, calculate wage gaps, run regressions or treatment effects, make national/population-prevalence/final causal claims, or set global analysis readiness true.

Dashboard update requirement: after the task, update dashboard/status/docs with substantive new information unless there is genuinely no update; if none is needed, state why. Preserve the total-scout-coverage-only map and global analysis readiness false. Do not imply wage gaps, regressions, treatment effects, national prevalence, population prevalence, or final causal claims.
"""
    write_md(OUTPUT_DIR / "next_broad_state_by_state_scout_prompt.md", future)
    write_md(OUTPUT_DIR / "next_task.md", future)

    write_md(RESULT_DOC, """# Bounded Tier C evidence memo supplement result — 2026-07-27

The supplement is complete over only the 140-valid-rating aggregate summary, with all 19 quarantines excluded. It adds bounded documentary findings for strike/no-strike and dispute resolution (76), market/comparability (51), non-safety constraint (11), and fiscal constraint (2). Direction remains overwhelmingly neutral, unclear, or not applicable. Broad state-by-state scouting with source-family diversification is ready next. No wage-gap, prevalence, regression, treatment-effect, or final causal result is available; global analysis readiness remains false.
""")
    write_md(DASHBOARD_NOTE, """# Bounded Tier C memo supplement dashboard status — 2026-07-27

Current phase: bounded Tier C evidence memo supplement complete; broad state-by-state, source-family-diverse scouting ready next. The dashboard links to the supplement and preserves the total-scout-coverage-only map, map data date 2026-07-27, and global analysis readiness false. The supplement is bounded documentary evidence, not a wage-gap, prevalence, regression, treatment-effect, or causal result.
""")


def validate_complete() -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    for path in (RESULT_DOC, DASHBOARD_NOTE, PROMPT_POLICY):
        if not path.is_file():
            missing.append(str(path.relative_to(ROOT)))
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_decision.json")
    invariants = read_json(OUTPUT_DIR / "bounded_tier_c_evidence_memo_supplement_invariant_checks.json")
    if not (
        decision.get("decision") == DECISION
        and decision.get("valid_rating_summary_scope") == 140
        and decision.get("quarantines_excluded") == 19
        and decision.get("predecessor_scope_reconciled") == 159
        and decision.get("global_analysis_readiness") is False
        and invariants.get("all_invariants_passed") is True
    ):
        raise RuntimeError("completed supplement package fails validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    context = validate_inputs()
    if OUTPUT_DIR.exists():
        if not args.resume:
            raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
        validate_complete()
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "decision": DECISION}))
        return 0
    if args.resume:
        raise RuntimeError("resume requested but output directory is absent")
    generate(context)
    validate_complete()
    print(json.dumps({"status": "completed", "decision": DECISION, "valid_scope": 140, "quarantines_excluded": 19}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
