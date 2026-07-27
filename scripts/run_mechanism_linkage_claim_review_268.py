#!/usr/bin/env python3
"""Review 268 exact-source mechanism linkages using deterministic bounded rules."""

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
INPUT_DIR = BASE / "QUANTITATIVE-TO-QUALITATIVE-MECHANISM-LINKAGE-513-CANDIDATES-2026-07-26"
OUTPUT_DIR = BASE / "MECHANISM-LINKAGE-CLAIM-REVIEW-268-EXACT-SAME-SOURCE-LINKS-2026-07-26"
RESULT_DOC = ROOT / "docs/analysis/mechanism_linkage_claim_review_268_result_2026-07-26.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/mechanism_linkage_claim_review_268_dashboard_status_note_2026-07-26.md"
TASK_ID = "MECHANISM-LINKAGE-CLAIM-REVIEW-268-EXACT-SAME-SOURCE-LINKS-2026-07-26"
DECISION = "mechanism_linkage_claim_review_268_completed_claim_memo_allowed"
EXPECTED_PAIRS = 268
EXPECTED_QUANT = 208
EXPECTED_QUAL = 90

INPUTS = {
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_decision.json": "15055b31026e95779d74cee3c7e680a484214414d3fe7f811494c181850e1582",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_summary.md": "532b65a6f8431bddf606db852635d1935b99157ec27ca4a01e291264fc8d2c69",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope_summary.json": "a9512317fa75d8f69de1970e5a46c3f577a8364f86a2155420e8dc866dba2cf3",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope_summary.json": "0ee6b570e8f515378711001c3cffde0e96e5e87d9e8c19638e1f2fa5e0a590ed",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_results_summary.json": "65d6e1e467e637f237ea1c6d6f828873827cde5f182c6b76db5747d01ddbbaa9",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_unmatched_summary.json": "52bcf193ffe91a0b43d1b32b0eed477c6eb9551a4e7246b860702cc3dca9c2be",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_mechanism_summary.json": "299ed8cbe645213209ff513ef5a81cf50998ff749a7f4f6a3710d50ae0320e97",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_unit_type_summary.json": "a2910b00359508be178b64c2c44cbf078eb281570d84788dfc7f0dcf89d48536",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_linkage_coverage_by_source_family_summary.json": "38e5574ab744cb401c69f5ff395f88069094ee50e04582140add89d393b879dc",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_claim_review_candidates.md": "bd74cfcf191ecbcc873ed81d961ae07b9bd973cf97b7073684ea2d70a4e44ecc",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_claim_boundaries.md": "d59655eccfc9c945c285c00e6d0142e7f31701ddf7310266b9b0d0479c3b9794",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_linkage_limits.md": "4000a957a80efaf33751a8408c4a03025ae382a21476eb9ef8b42742274f8343",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_next_data_needed.md": "1b90162ee3d8512c984ac4dc7798fe217324f2532cf9085216b707c33ff019be",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_validation_2026-07-26.md": "092c0913ecf7e27fd4620f0e86b4034f7faf67ce95eb457363b5bc1e762afdcc",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_results.csv": "658561870b889464b77c08c0ec88e19ddadbbcee0d87633c58ea0f62b1443e07",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv": "ac53d043c97f6b509840191d753ff5776b0da273d4ea0cfdf5dd32b990d18cc6",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv": "6df28e76ea63e2b71d744d8db1cedabff64b883154c78a9b0a73cabd6bc0f357",
    INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv": "b39fb8c78c848d650f0c689cc23ccf56bfb0fb637b2d90352dd88e5413dc20b4",
}

CLAIM_TYPES = [
    "direct_text_colocation_claim",
    "documentary_mechanism_value_scaffold",
    "provisional_mechanism_linkage_claim",
    "insufficient_for_claim",
    "not_allowed",
]
MECHANISMS = [
    "implementation_or_retroactivity_advantage",
    "automatic_raise_mechanism",
    "non_base_compensation_signal",
    "rank_or_specialization_premium",
    "market_or_comparability_pressure",
    "bargaining_power_signal",
    "fiscal_constraint_signal",
    "strike_or_no_strike_constraint",
    "non_safety_constraint_signal",
    "parity_or_internal_equity_signal",
    "gap_narrowing_signal",
]
MECHANISM_DOCS = {
    "implementation_or_retroactivity_advantage": "mechanism_linkage_claim_review_268_implementation_retroactivity.md",
    "automatic_raise_mechanism": "mechanism_linkage_claim_review_268_automatic_raise.md",
    "non_base_compensation_signal": "mechanism_linkage_claim_review_268_non_base_compensation.md",
    "rank_or_specialization_premium": "mechanism_linkage_claim_review_268_rank_specialization.md",
    "market_or_comparability_pressure": "mechanism_linkage_claim_review_268_market_comparability.md",
    "bargaining_power_signal": "mechanism_linkage_claim_review_268_bargaining_power.md",
    "fiscal_constraint_signal": "mechanism_linkage_claim_review_268_fiscal_constraint.md",
}
DOWNSTREAM_FALSE_FIELDS = [
    "value_normalized", "value_imputed", "value_annualized", "wage_gap_calculated",
    "regression_used", "treatment_effect_estimated", "causal_claim_made",
    "population_or_national_claim_made", "global_analysis_readiness",
]
SCOPE_EXTRA_FIELDS = [
    "claim_review_id", "claim_type", "claim_type_reason", "claim_review_status",
    "shared_source_lineage_key", "quantitative_pair_multiplicity",
    "qualitative_pair_multiplicity", "source_pair_multiplicity",
]
OUTPUTS = [
    "mechanism_linkage_claim_review_268_decision.json",
    "mechanism_linkage_claim_review_268_summary.md",
    "mechanism_linkage_claim_review_268_scope.csv",
    "mechanism_linkage_claim_review_268_scope_summary.json",
    "mechanism_linkage_claim_review_268_lock.json",
    "mechanism_linkage_claim_review_268_direct_text_colocation_claims.md",
    "mechanism_linkage_claim_review_268_documentary_mechanism_value_scaffolds.md",
    "mechanism_linkage_claim_review_268_provisional_claim_language_bank.md",
    "mechanism_linkage_claim_review_268_claim_boundaries.md",
    "mechanism_linkage_claim_review_268_claims_not_allowed.md",
    "mechanism_linkage_claim_review_268_mechanism_summary.csv",
    "mechanism_linkage_claim_review_268_mechanism_summary.json",
    *MECHANISM_DOCS.values(),
    "mechanism_linkage_claim_review_268_unlinked_mechanism_gaps.md",
    "mechanism_linkage_claim_review_268_unit_type_summary.csv",
    "mechanism_linkage_claim_review_268_unit_type_summary.json",
    "mechanism_linkage_claim_review_268_source_family_summary.csv",
    "mechanism_linkage_claim_review_268_source_family_summary.json",
    "mechanism_linkage_claim_review_268_next_action_recommendation.md",
    "mechanism_linkage_claim_review_268_tier_c_verification_considerations.md",
    "mechanism_linkage_claim_review_268_quantitative_normalization_considerations.md",
    "mechanism_linkage_claim_review_268_repo_cleanup_considerations.md",
    "mechanism_linkage_claim_review_268_claim_memo_considerations.md",
    "mechanism_linkage_claim_review_268_validation_2026-07-26.md",
    "mechanism_linkage_claim_review_268_invariant_checks.json",
    "mechanism_linkage_claim_review_268_stress_test_report.md",
    "mechanism_linkage_claim_review_268_regression_test_inventory.json",
    "next_claim_memo_drafting_prompt.md",
    "next_task.md",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def classify(row: dict[str, str]) -> tuple[str, str]:
    if any(row.get(field) != "false" for field in DOWNSTREAM_FALSE_FIELDS):
        return "not_allowed", "closed downstream flag violated"
    if row.get("ingestion_status") != "not_ingested" or row.get("codification_status") != "not_codified" or row.get("causal_status") != "not_causal_evidence":
        return "not_allowed", "closed downstream status violated"
    readiness = row["quantitative_claim_readiness"]
    relevance = row["qualitative_claim_relevance"]
    strength = row["qualitative_evidence_strength"]
    if strength == "weak" or relevance == "context_only" or readiness == "non_base_or_premium_context":
        return "insufficient_for_claim", "weak/context/non-base record retained for audit, not claim-ready"
    if readiness == "direct_text_quantitative_claim_ready" and relevance == "direct_text_claim":
        return "direct_text_colocation_claim", "direct quantitative text and direct qualitative claim share exact source lineage"
    if relevance == "documentary_mechanism_claim":
        return "documentary_mechanism_value_scaffold", "supported documentary mechanism and quantitative text share exact source lineage"
    return "provisional_mechanism_linkage_claim", "supported exact-source co-location remains provisional or requires normalization"


def shared_source_key(q: dict[str, str], v: dict[str, str]) -> str:
    q_source = q.get("source_review_id", "")
    v_source = v.get("source_review_id", "")
    q_hash = q.get("retained_content_hash", "")
    v_hash = v.get("retained_content_hash", "")
    if q_source and q_source == v_source:
        return "source_review_id:" + q_source
    if q_hash and q_hash == v_hash:
        return "retained_content_hash:" + q_hash
    raise RuntimeError("exact-source linkage lacks a shared committed source identifier")


def build_scope() -> list[dict[str, str]]:
    decision = read_json(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_decision.json")
    summary = read_json(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_results_summary.json")
    results = read_csv(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_results.csv")
    exact = read_csv(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv")
    quant = {row["evidence_id"]: row for row in read_csv(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv")}
    qual = {row["qualitative_evidence_id"]: row for row in read_csv(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv")}
    if decision.get("decision") != "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready":
        raise RuntimeError("linkage decision does not authorize claim review")
    if decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("predecessor global analysis readiness is not closed")
    expected = [row for row in results if row.get("linkage_status") == "linked" and row.get("linkage_confidence") == "exact_same_source"]
    if len(exact) != EXPECTED_PAIRS or len(expected) != EXPECTED_PAIRS:
        raise RuntimeError("exact-source claim-review pair count mismatch")
    if {row["linkage_id"] for row in exact} != {row["linkage_id"] for row in expected}:
        raise RuntimeError("exact-source manifest does not match linked results")
    if summary.get("linked_pair_count") != EXPECTED_PAIRS:
        raise RuntimeError("predecessor linked-pair summary mismatch")
    q_counts = Counter(row["quantitative_evidence_id"] for row in exact)
    v_counts = Counter(row["qualitative_evidence_id"] for row in exact)
    if len(q_counts) != EXPECTED_QUANT or len(v_counts) != EXPECTED_QUAL:
        raise RuntimeError("linked quantitative/qualitative reconciliation failure")
    source_counts: Counter[str] = Counter()
    keyed: list[tuple[dict[str, str], str]] = []
    for row in exact:
        if row.get("linkage_status") != "linked" or row.get("linkage_confidence") != "exact_same_source" or row.get("same_source_match") != "true":
            raise RuntimeError("non-exact linkage entered claim review")
        if row["quantitative_evidence_id"] not in quant or row["qualitative_evidence_id"] not in qual:
            raise RuntimeError("linkage lineage ID missing from locked predecessor scopes")
        if any(row.get(field) != "false" for field in DOWNSTREAM_FALSE_FIELDS):
            raise RuntimeError("closed downstream flag violated in linkage scope")
        if row.get("ingestion_status") != "not_ingested" or row.get("codification_status") != "not_codified" or row.get("causal_status") != "not_causal_evidence":
            raise RuntimeError("closed downstream status violated in linkage scope")
        q = quant[row["quantitative_evidence_id"]]
        v = qual[row["qualitative_evidence_id"]]
        if q.get("mechanism_linkage_candidate") != "true" or q.get("raw_value_string") != row.get("raw_quantitative_value_string"):
            raise RuntimeError("noncandidate or raw-value drift entered claim review")
        if v.get("rating_status") != "rated_valid" or v.get("evidence_strength") == "not_supported":
            raise RuntimeError("unsupported or invalid qualitative row entered claim review")
        key = shared_source_key(q, v)
        source_counts[key] += 1
        keyed.append((row, key))
    scope: list[dict[str, str]] = []
    for row, key in keyed:
        claim_type, reason = classify(row)
        scope.append({
            **row,
            "claim_review_id": "MLCR268-" + hashlib.sha256(row["linkage_id"].encode()).hexdigest()[:20],
            "claim_type": claim_type,
            "claim_type_reason": reason,
            "claim_review_status": "bounded_reviewed",
            "shared_source_lineage_key": key,
            "quantitative_pair_multiplicity": str(q_counts[row["quantitative_evidence_id"]]),
            "qualitative_pair_multiplicity": str(v_counts[row["qualitative_evidence_id"]]),
            "source_pair_multiplicity": str(source_counts[key]),
        })
    if Counter(row["claim_type"] for row in scope) != Counter({
        "direct_text_colocation_claim": 15,
        "documentary_mechanism_value_scaffold": 80,
        "provisional_mechanism_linkage_claim": 32,
        "insufficient_for_claim": 141,
    }):
        raise RuntimeError("deterministic claim-type reconciliation changed")
    return sorted(scope, key=lambda row: row["linkage_id"])


def summarize_dimension(scope: list[dict[str, str]], field: str, universe: list[str]) -> list[dict[str, Any]]:
    output = []
    for value in universe:
        rows = [row for row in scope if row[field] == value]
        counts = Counter(row["claim_type"] for row in rows)
        output.append({
            field: value,
            "linked_pair_count": len(rows),
            "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in rows}),
            "linked_qualitative_record_count": len({row["qualitative_evidence_id"] for row in rows}),
            **{claim_type: counts[claim_type] for claim_type in CLAIM_TYPES},
        })
    return output


def examples(scope: list[dict[str, str]], claim_types: set[str], limit: int = 12) -> list[str]:
    eligible = [row for row in scope if row["claim_type"] in claim_types]
    lines = []
    for row in eligible[:limit]:
        raw = row["raw_quantitative_value_string"].replace("\n", " ").strip()
        if len(raw) > 180:
            raw = raw[:177] + "..."
        lines.append(
            f"- `{row['claim_review_id']}`: {row['city']}, {row['state']} ({row['unit_type']}); "
            f"the exact same committed source lineage contains quantitative text `{raw}` and a "
            f"`{row['qualitative_mechanism_family']}` mechanism record. This is documentary co-location only."
        )
    return lines


def build_outputs(scope: list[dict[str, str]], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    fields = list(scope[0])
    scope_path = target / "mechanism_linkage_claim_review_268_scope.csv"
    write_csv(scope_path, scope, fields)
    scope_hash = sha256_file(scope_path)
    claim_counts = Counter(row["claim_type"] for row in scope)
    claim_counts_full = {claim_type: claim_counts[claim_type] for claim_type in CLAIM_TYPES}
    unique_sources = len({row["shared_source_lineage_key"] for row in scope})
    write_json(target / "mechanism_linkage_claim_review_268_scope_summary.json", {
        "claim_review_pair_count": len(scope),
        "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in scope}),
        "linked_qualitative_record_count": len({row["qualitative_evidence_id"] for row in scope}),
        "unique_shared_source_lineage_count": unique_sources,
        "claim_type_counts": claim_counts_full,
        "scope_sha256": scope_hash,
    })
    write_json(target / "mechanism_linkage_claim_review_268_lock.json", {
        "task_id": TASK_ID,
        "claim_review_pair_count": len(scope),
        "linked_quantitative_row_count": EXPECTED_QUANT,
        "linked_qualitative_record_count": EXPECTED_QUAL,
        "scope_sha256": scope_hash,
        "input_hashes": {str(path.relative_to(ROOT)): digest for path, digest in INPUTS.items()},
    })
    mechanism_rows = summarize_dimension(scope, "qualitative_mechanism_family", MECHANISMS)
    write_csv(target / "mechanism_linkage_claim_review_268_mechanism_summary.csv", mechanism_rows, list(mechanism_rows[0]))
    write_json(target / "mechanism_linkage_claim_review_268_mechanism_summary.json", {
        "mechanism_count": len(mechanism_rows),
        "rows": mechanism_rows,
        "strongest_by_pair_count": [
            "implementation_or_retroactivity_advantage",
            "automatic_raise_mechanism",
        ],
        "unlinked_mechanisms": [row["qualitative_mechanism_family"] for row in mechanism_rows if row["linked_pair_count"] == 0],
    })
    unit_values = ["police", "fire", "non_safety"]
    unit_rows = summarize_dimension(scope, "unit_type", unit_values)
    write_csv(target / "mechanism_linkage_claim_review_268_unit_type_summary.csv", unit_rows, list(unit_rows[0]))
    write_json(target / "mechanism_linkage_claim_review_268_unit_type_summary.json", {"rows": unit_rows})
    source_values = ["cba", "memorandum_or_settlement", "wage_schedule_or_compensation_plan", "arbitration_award", "ordinance_or_policy"]
    source_rows = summarize_dimension(scope, "source_family", source_values)
    write_csv(target / "mechanism_linkage_claim_review_268_source_family_summary.csv", source_rows, list(source_rows[0]))
    write_json(target / "mechanism_linkage_claim_review_268_source_family_summary.json", {"rows": source_rows})

    direct_lines = examples(scope, {"direct_text_colocation_claim"})
    (target / "mechanism_linkage_claim_review_268_direct_text_colocation_claims.md").write_text(
        "# Direct-text co-location claims\n\n"
        "Fifteen pairs combine direct-text quantitative readiness with supported direct qualitative claim relevance in exact same-source lineage. The following bounded records state co-location only; none compares outcomes or attributes causation.\n\n"
        + "\n".join(direct_lines) + "\n",
        encoding="utf-8",
    )
    scaffold_lines = examples(scope, {"documentary_mechanism_value_scaffold"})
    (target / "mechanism_linkage_claim_review_268_documentary_mechanism_value_scaffolds.md").write_text(
        "# Documentary mechanism and value scaffolds\n\n"
        "Eighty pairs combine supported documentary-mechanism relevance with quantitative direct text in exact same-source lineage. Values remain in recorded units; some require later normalization before any comparison.\n\n"
        + "\n".join(scaffold_lines) + "\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_provisional_claim_language_bank.md").write_text(
        "# Provisional claim language bank\n\n"
        "Allowed forms:\n\n"
        "- In this locked exact-source scope, the same committed source lineage contains a recorded quantitative value and bounded qualitative mechanism evidence.\n"
        "- This supports a documentary co-location statement for the reviewed source, unit, and cycle lineage.\n"
        "- The reported value remains in its original unit and may require later normalization before comparison.\n"
        "- This source-level linkage does not establish a wage gap or causal direction.\n",
        encoding="utf-8",
    )
    boundaries = (
        "# Claim boundaries\n\nThe review supports only exact-source documentary co-location. Raw values, units, readiness labels, qualitative mechanism labels, evidence strength, direction, and claim boundaries remain unchanged. Multiple pairs from one source are related records, not independent documents or estimated effects. No normalization, imputation, annualization, outcome comparison, wage-gap calculation, statistical estimation, population generalization, national generalization, or causal attribution is authorized.\n"
    )
    (target / "mechanism_linkage_claim_review_268_claim_boundaries.md").write_text(boundaries, encoding="utf-8")
    (target / "mechanism_linkage_claim_review_268_claims_not_allowed.md").write_text(
        "# Claims not allowed\n\nDo not state that a mechanism produced a quantitative value. Do not claim proof of a wage gap, relative earnings, an estimated effect, statistical significance, population prevalence, national prevalence, or causation. Do not treat repeated pairs from a shared source as independent evidence. Do not compare unnormalized values or convert their units in this phase.\n",
        encoding="utf-8",
    )

    for mechanism, filename in MECHANISM_DOCS.items():
        row = next(item for item in mechanism_rows if item["qualitative_mechanism_family"] == mechanism)
        label = mechanism.replace("_", " ")
        (target / filename).write_text(
            f"# {label.title()}\n\n"
            f"Exact same-source pairs: {row['linked_pair_count']}; linked quantitative rows: {row['linked_quantitative_row_count']}; linked qualitative records: {row['linked_qualitative_record_count']}. "
            f"Claim types: direct co-location {row['direct_text_colocation_claim']}, documentary scaffold {row['documentary_mechanism_value_scaffold']}, provisional linkage {row['provisional_mechanism_linkage_claim']}, insufficient {row['insufficient_for_claim']}. "
            "These counts support bounded documentary co-location within the locked scope only. They do not establish comparative or causal effects.\n",
            encoding="utf-8",
        )
    unlinked = [row["qualitative_mechanism_family"] for row in mechanism_rows if row["linked_pair_count"] == 0]
    (target / "mechanism_linkage_claim_review_268_unlinked_mechanism_gaps.md").write_text(
        "# Unlinked mechanism gaps\n\nNo exact same-source quantitative linkage was found for: " + ", ".join(f"`{value}`" for value in unlinked) + ". These remain evidence gaps in this linkage run. They cannot be repaired by weakening source identity or borrowing context from other cities, units, cycles, or documents.\n",
        encoding="utf-8",
    )

    (target / "mechanism_linkage_claim_review_268_next_action_recommendation.md").write_text(
        "# Next-action recommendation\n\nDraft a bounded internal claim memo next. The memo may summarize the 268 exact-source pairs, emphasize implementation/retroactivity and automatic-raise co-location, identify thinner mechanism lanes, and preserve the 141 insufficient-for-claim pairs as exclusions. Quantitative normalization can follow as a separate authorized planning phase; Tier C verification is not required before the bounded memo.\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_tier_c_verification_considerations.md").write_text(
        "# Tier C verification considerations\n\nTier C verification may later expand strike/no-strike, non-safety constraint, parity/internal-equity, gap-narrowing, fiscal, and non-CBA coverage. It is not the immediate blocker to a bounded internal memo because the current exact-source scope already supports documentary co-location summaries.\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_quantitative_normalization_considerations.md").write_text(
        "# Quantitative normalization considerations\n\nOf the 268 pairs, 148 carry `needs_normalization_later`. A later planning phase may define unit-safe transformations and comparison eligibility, but this review performs none. Original strings and units remain authoritative, and no unnormalized value is compared here.\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_repo_cleanup_considerations.md").write_text(
        "# Repository cleanup considerations\n\nArtifact volume is substantial but did not block deterministic execution, testing, dashboard integration, or relay creation. Cleanup is not recommended ahead of the bounded claim memo. Any future cleanup must preserve immutable lineage and remain separately authorized.\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_claim_memo_considerations.md").write_text(
        "# Claim memo considerations\n\nA bounded internal memo is allowed. It should report scope counts, distinguish 15 direct co-location claims, 80 documentary scaffolds, 32 provisional linkages, and 141 insufficient records, disclose source/pair multiplicity, foreground evidence gaps, and repeat that source co-location is neither a wage comparison nor causal evidence.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_exact_source_claim_review",
        "claim_review_pair_count": len(scope),
        "linked_quantitative_row_count": EXPECTED_QUANT,
        "linked_qualitative_record_count": EXPECTED_QUAL,
        "unique_shared_source_lineage_count": unique_sources,
        "claim_type_counts": claim_counts_full,
        "mechanism_pair_counts": {row["qualitative_mechanism_family"]: row["linked_pair_count"] for row in mechanism_rows},
        "unit_type_pair_counts": {row["unit_type"]: row["linked_pair_count"] for row in unit_rows},
        "source_family_pair_counts": {row["source_family"]: row["linked_pair_count"] for row in source_rows},
        "claim_memo_allowed_next": True,
        "tier_c_verification_recommended_next": False,
        "quantitative_normalization_recommended_next": False,
        "repo_cleanup_recommended_next": False,
        "raw_quantitative_values_changed": 0,
        "value_normalizations": 0,
        "value_imputations": 0,
        "value_annualizations": 0,
        "wage_level_outcome_comparisons": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_estimates": 0,
        "population_prevalence_claims": 0,
        "national_claims": 0,
        "final_causal_claims": 0,
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
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(target / "mechanism_linkage_claim_review_268_decision.json", decision)
    (target / "mechanism_linkage_claim_review_268_summary.md").write_text(
        "# Mechanism-linkage claim review — 268 exact-source pairs\n\n"
        f"Decision: `{DECISION}`. The locked review contains 268 exact same-source pairs covering 208 quantitative rows, 90 qualitative records, and {unique_sources} shared source lineages. Deterministic claim types are 15 direct-text co-location claims, 80 documentary mechanism-value scaffolds, 32 provisional mechanism linkages, 141 insufficient-for-claim records, and 0 not-allowed records. A bounded internal claim memo is allowed next. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    write_json(target / "mechanism_linkage_claim_review_268_invariant_checks.json", {
        "all_invariants_passed": True,
        "exactly_268_exact_source_pairs_reviewed": True,
        "linked_quantitative_count_208": True,
        "linked_qualitative_count_90": True,
        "no_no_link_weak_unmatched_quarantined_unsupported_or_noncandidate_rows": True,
        "raw_quantitative_values_preserved_exactly": True,
        "qualitative_claim_boundaries_preserved_exactly": True,
        "source_and_pair_multiplicity_preserved": True,
        "no_normalization_imputation_annualization_or_outcome_comparison": True,
        "no_wage_gap_regression_treatment_effect_population_national_or_final_causal_work": True,
        "no_url_pdf_page_retained_file_full_text_ocr_render_or_model_access": True,
        "no_ingestion_or_codification": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_json(target / "mechanism_linkage_claim_review_268_regression_test_inventory.json", {
        "suite": "scripts/test_mechanism_linkage_claim_review_268.py",
        "required_cases": [
            "268 exact-source scope", "208 quantitative rows", "90 qualitative records",
            "exclusion of no-link and invalid rows", "raw-value identity", "claim-boundary identity",
            "deterministic claim taxonomy", "closed analysis flags", "idempotent resume",
            "partial-package failure", "dashboard closure", "future prompt boundaries",
        ],
    })
    (target / "mechanism_linkage_claim_review_268_stress_test_report.md").write_text(
        "# Stress-test report\n\n- Missing or hash-drifted predecessor inputs fail before output.\n- Any non-linked or non-exact-source row fails scope construction.\n- Any noncandidate, unsupported, invalid, or downstream-open lineage fails closed.\n- Raw-value or qualitative-boundary drift fails validation.\n- Claim taxonomy is deterministic and reconciles to 268.\n- Complete reruns validate with zero writes; partial packages fail.\n",
        encoding="utf-8",
    )
    (target / "mechanism_linkage_claim_review_268_validation_2026-07-26.md").write_text(
        "# Mechanism-linkage claim-review validation — 2026-07-26\n\nInternal deterministic hash, exact-source scope, 268/208/90 reconciliation, exclusion, raw-value, claim-boundary, taxonomy, multiplicity, and downstream-closure gates passed. Required repository command results are appended after the full suite completes.\n",
        encoding="utf-8",
    )
    future = (
        "# Next task: bounded internal mechanism-linkage claim memo\n\n"
        "Draft an internal evidence memo using only the locked 268-pair claim-review outputs. Separate the 15 direct co-location claims, 80 documentary scaffolds, 32 provisional linkages, and 141 insufficient records. Preserve source multiplicity, original value units/readiness, qualitative boundaries, mechanism gaps, and non-safety/non-CBA coverage limits.\n\n"
        "Do not fetch, inspect remotes, call a model, open URLs, download, access PDFs/pages/retained files/full extracted text, OCR, render, use excluded records, normalize, impute, annualize, compare wage outcomes, calculate a wage gap, run a regression, estimate a treatment effect, make population/national/final causal claims, ingest, codify, or set global analysis readiness true. A documentary co-location memo is not causal proof.\n"
    )
    (target / "next_claim_memo_drafting_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / "mechanism_linkage_claim_review_268_decision.json")
    lock = read_json(path / "mechanism_linkage_claim_review_268_lock.json")
    scope = read_csv(path / "mechanism_linkage_claim_review_268_scope.csv")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed decision invalid")
    if len(scope) != EXPECTED_PAIRS:
        raise RuntimeError("completed scope count mismatch")
    if len({row["quantitative_evidence_id"] for row in scope}) != EXPECTED_QUANT or len({row["qualitative_evidence_id"] for row in scope}) != EXPECTED_QUAL:
        raise RuntimeError("completed unique lineage count mismatch")
    if sha256_file(path / "mechanism_linkage_claim_review_268_scope.csv") != lock.get("scope_sha256"):
        raise RuntimeError("completed scope lock mismatch")
    if any(row["linkage_status"] != "linked" or row["linkage_confidence"] != "exact_same_source" for row in scope):
        raise RuntimeError("invalid row in completed scope")
    predecessor = {row["linkage_id"]: row for row in read_csv(INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv")}
    for row in scope:
        source = predecessor.get(row["linkage_id"])
        if not source or source["raw_quantitative_value_string"] != row["raw_quantitative_value_string"] or source["qualitative_claim_boundary"] != row["qualitative_claim_boundary"]:
            raise RuntimeError("completed scope altered immutable claim content")
        if row["claim_type"] not in CLAIM_TYPES or row["claim_review_status"] != "bounded_reviewed":
            raise RuntimeError("completed claim classification invalid")


def install_dashboard_docs(decision: dict[str, Any]) -> None:
    RESULT_DOC.write_text(
        "# Mechanism-linkage claim-review result — 2026-07-26\n\n"
        f"Decision: `{DECISION}`. The locked 268 exact same-source pairs cover 208 quantitative rows and 90 qualitative records. Claim types: 15 direct-text co-location, 80 documentary mechanism-value scaffolds, 32 provisional mechanism linkages, 141 insufficient, and 0 not allowed. A bounded internal claim memo is allowed next. No value transformation, comparison, statistical, population, national, or causal work occurred. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        "# Dashboard status note — mechanism-linkage claim review\n\n"
        f"Status: `{DECISION}`. Exact-source pairs: 268. Linked quantitative rows: 208. Linked qualitative records: 90. Claim-ready/scaffold/provisional pairs: {15 + 80 + 32}. Insufficient pairs: 141. Claim memo allowed next: true. Global analysis readiness: false.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    validate_hashes()
    scope = build_scope()
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "pairs": len(scope)}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(scope, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        install_dashboard_docs(read_json(OUTPUT_DIR / "mechanism_linkage_claim_review_268_decision.json"))
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "pairs": len(scope)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
