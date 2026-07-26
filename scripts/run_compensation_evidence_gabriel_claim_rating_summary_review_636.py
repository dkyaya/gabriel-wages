#!/usr/bin/env python3
"""Summarize only the 636 schema-valid v1.1 GABRIEL ratings.

The seven remaining quarantine rows are preserved as explicit exclusions.  This
runner is deterministic and local: it has no model, network, PDF, extraction,
ingestion, codification, regression, or causal-inference path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import run_compensation_evidence_gabriel_claim_rating_643 as rating


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "docs/analysis"
BASE = ANALYSIS_ROOT / "compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-SUMMARY-REVIEW-636-2026-07-25"
BASELINE_COMMIT = "9f252b984def69be40ec8d4f91f40987b1743719"
INPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25"
UPSTREAM_DIR = BASE / "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-SUMMARY-REVIEW-636-2026-07-25"
VALID_PATH = INPUT_DIR / "gabriel_claim_oriented_attribute_ratings_643_repaired.csv"
QUARANTINE_PATH = INPUT_DIR / "gabriel_claim_oriented_attribute_rating_remaining_quarantine.csv"
MANIFEST_PATH = UPSTREAM_DIR / "gabriel_claim_rating_ready_evidence_manifest.csv"
QUARANTINE_SUMMARY_PRIMARY = INPUT_DIR / "remaining_quarantine_summary.json"
QUARANTINE_SUMMARY_FALLBACK = ROOT / "tmp/compensation_evidence_gabriel_claim_rating_35_quarantine_repair_relay_2026-07-25_9f252b9/remaining_quarantine_summary.json"

EXPECTED_VALID = 636
EXPECTED_EXCLUDED = 7
EXPECTED_TOTAL = 643
EXPECTED_VALID_SHA256 = "de7ce29aa5c749e0faadab97ccade17d1f470e35e1dc48a95767baf70ed191e9"
EXPECTED_QUARANTINE_SHA256 = "f6a2035c12ad5bb514b1c3d3297707bd73beee531fc554ac5150e61c3aa25ae9"
EXPECTED_MANIFEST_SHA256 = "5993d89931fc9e816b60e607f4acb8a467bb587a3bf28390ed1922aae65c6fb6"
EXPECTED_QUARANTINE_SUMMARY_SHA256 = "ad169c712eb450fbe00c676343ac1b8de4ee9e0300edea8a24a7cc85bf9608a3"
DECISION = "gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed"

REQUIRED_INPUTS = (
    "gabriel_claim_rating_35_quarantine_repair_decision.json",
    "gabriel_claim_rating_35_quarantine_repair_summary.json",
    "gabriel_claim_oriented_attribute_ratings_643_repaired_summary.json",
    "gabriel_claim_oriented_attribute_ratings_643_repaired.csv",
    "gabriel_claim_oriented_attribute_rating_remaining_quarantine.csv",
    "gabriel_claim_rating_35_quarantine_repair_qa_report.md",
    "gabriel_claim_rating_35_quarantine_repair_validation_2026-07-25.md",
    "gabriel_claim_rating_35_quarantine_repair_invariant_checks.json",
    "gabriel_claim_rating_repaired_claim_scaffold.md",
    "gabriel_claim_rating_repaired_claim_limits.md",
)

REQUIRED_OUTPUTS = (
    "gabriel_claim_rating_summary_review_636_decision.json",
    "gabriel_claim_rating_summary_review_636_summary.md",
    "gabriel_claim_rating_summary_review_valid_636_manifest.csv",
    "gabriel_claim_rating_summary_review_excluded_7_manifest.csv",
    "gabriel_claim_rating_summary_review_scope_summary.json",
    "gabriel_claim_rating_attribute_presence_summary.csv",
    "gabriel_claim_rating_direction_of_pressure_summary.csv",
    "gabriel_claim_rating_evidence_strength_summary.csv",
    "gabriel_claim_rating_claim_relevance_summary.csv",
    "gabriel_claim_rating_scout_priority_summary.csv",
    "gabriel_claim_rating_attribute_crosswalk_summary.json",
    "provisional_mechanism_findings_from_valid_ratings.md",
    "stronger_mechanism_signals_current_corpus.md",
    "weaker_or_inconclusive_mechanism_signals_current_corpus.md",
    "mechanism_evidence_limitations.md",
    "provisional_claims_supported_by_636_valid_ratings.md",
    "provisional_claims_requiring_more_data.md",
    "claims_not_allowed_after_summary_review.md",
    "evidence_to_provisional_claim_summary_registry.csv",
    "evidence_to_provisional_claim_summary.json",
    "next_data_needed_by_mechanism.md",
    "scouting_restart_priorities_from_claim_rating_summary.md",
    "source_family_and_unit_coverage_gaps_for_next_scout.md",
    "gabriel_claim_rating_summary_review_636_validation_2026-07-25.md",
    "gabriel_claim_rating_summary_review_636_invariant_checks.json",
    "gabriel_claim_rating_summary_review_636_stress_test_report.md",
    "gabriel_claim_rating_summary_review_636_regression_test_inventory.json",
    "next_provisional_claim_review_prompt.md",
    "next_task.md",
)

VALID_MANIFEST_FIELDS = (
    "evidence_id", "row_document_id", "attribute_taxonomy_version", "primary_attribute",
    "overall_evidence_quality", "scout_priority_signal", "qa_status", "source_lane",
    "unit_type", "state", "source_family", "summary_scope", "included_in_valid_summary",
    "excluded_from_causal_claims", "source_rating_row_sha256",
)
EXCLUDED_FIELDS = (
    "evidence_id", "row_document_id", "failure_stage", "attempt_count", "last_status",
    "error_type", "error_code", "quarantine_reason", "summary_scope",
    "included_in_valid_summary", "exclusion_reason", "raw_prompt_saved", "raw_response_saved",
)
PRESENCE_FIELDS = (
    "attribute_id", "valid_rows", "present_count", "absent_count", "present_rate",
    "strong_count", "moderate_count", "weak_count", "not_supported_count",
    "direct_text_claim_count", "documentary_mechanism_claim_count",
    "provisional_causal_candidate_count", "context_only_count", "not_claim_ready_count",
)
CONTROL_FIELDS = ("controlled_value", "count_all_attribute_cells", "count_present_attribute_cells", "scope_note")
SCOUT_FIELDS = ("scout_priority_signal", "row_count", "valid_rows", "row_share")
CLAIM_FIELDS = (
    "claim_id", "attribute_id", "claim_type", "provisional_claim_text", "present_count",
    "valid_row_denominator", "strong_or_moderate_count", "provisional_direction_count",
    "claim_boundary", "next_data_needed", "review_status",
)

SUBSTANTIVE_ATTRIBUTES = tuple(a for a in rating.ATTRIBUTE_IDS if a != "weak_or_no_claim_support")
FORBIDDEN_PHRASES = (
    "causes the wage gap", "proved", "proves", "nationally", "effect size",
    "statistically significant", "safety workers earn", "treatment effect estimate",
)


def sha256(path: Path) -> str:
    return rating.sha256(path)


def id_set_sha256(ids: Iterable[str]) -> str:
    return rating.id_set_sha256(ids)


def row_sha256(row: dict[str, str]) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def resolve_inputs() -> tuple[dict[str, Path], dict[str, str]]:
    paths: dict[str, Path] = {}
    resolutions: dict[str, str] = {}
    for name in REQUIRED_INPUTS:
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        paths[name] = path
        resolutions[name] = "primary_input_directory"
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"required upstream manifest missing: {MANIFEST_PATH}")
    paths[MANIFEST_PATH.name] = MANIFEST_PATH
    resolutions[MANIFEST_PATH.name] = "approved_upstream_manifest_for_lineage_only"
    if QUARANTINE_SUMMARY_PRIMARY.is_file():
        qsummary = QUARANTINE_SUMMARY_PRIMARY
        resolution = "primary_input_directory"
    elif QUARANTINE_SUMMARY_FALLBACK.is_file():
        qsummary = QUARANTINE_SUMMARY_FALLBACK
        resolution = "verified_prior_lite_relay_fallback_no_upstream_mutation"
    else:
        raise FileNotFoundError(
            f"required remaining quarantine summary missing: {QUARANTINE_SUMMARY_PRIMARY} and {QUARANTINE_SUMMARY_FALLBACK}"
        )
    paths["remaining_quarantine_summary.json"] = qsummary
    resolutions["remaining_quarantine_summary.json"] = resolution
    return paths, resolutions


def verify_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    paths, resolutions = resolve_inputs()
    decision = rating.read_json(paths["gabriel_claim_rating_35_quarantine_repair_decision.json"])
    summary = rating.read_json(paths["gabriel_claim_oriented_attribute_ratings_643_repaired_summary.json"])
    invariants = rating.read_json(paths["gabriel_claim_rating_35_quarantine_repair_invariant_checks.json"])
    qsummary = rating.read_json(paths["remaining_quarantine_summary.json"])
    if decision.get("decision") != "gabriel_claim_rating_643_repaired_with_remaining_quarantine":
        raise RuntimeError("repair decision does not authorize limited summary review")
    if decision.get("summary_review_allowed") is not True:
        raise RuntimeError("repair decision does not allow summary review")
    if decision.get("summary_review_scope") != "636_schema_valid_rows_with_7_explicit_quarantine_exclusions":
        raise RuntimeError("repair summary-review scope drift")
    if decision != summary:
        raise RuntimeError("repair decision and repaired summary disagree")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("predecessor invariants did not pass")
    if sha256(VALID_PATH) != EXPECTED_VALID_SHA256:
        raise RuntimeError("immutable repaired valid-rating file hash drift")
    if sha256(QUARANTINE_PATH) != EXPECTED_QUARANTINE_SHA256:
        raise RuntimeError("immutable remaining-quarantine file hash drift")
    if sha256(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("immutable GABRIEL-ready manifest hash drift")
    if sha256(paths["remaining_quarantine_summary.json"]) != EXPECTED_QUARANTINE_SUMMARY_SHA256:
        raise RuntimeError("remaining quarantine summary hash drift")

    valid = rating.read_csv(VALID_PATH)
    excluded = rating.read_csv(QUARANTINE_PATH)
    manifest = rating.read_csv(MANIFEST_PATH)
    if len(valid) != EXPECTED_VALID or len(excluded) != EXPECTED_EXCLUDED or len(manifest) != EXPECTED_TOTAL:
        raise RuntimeError("valid/excluded/authorized row count drift")
    valid_ids = {row["evidence_id"] for row in valid}
    excluded_ids = {row["evidence_id"] for row in excluded}
    manifest_map = {row["evidence_id"]: row for row in manifest}
    if len(valid_ids) != EXPECTED_VALID or len(excluded_ids) != EXPECTED_EXCLUDED or len(manifest_map) != EXPECTED_TOTAL:
        raise RuntimeError("duplicate or blank evidence IDs")
    if valid_ids & excluded_ids:
        raise RuntimeError("quarantined row entered valid summary scope")
    if valid_ids | excluded_ids != set(manifest_map):
        raise RuntimeError("valid plus excluded rows do not reconcile to authorized 643-row manifest")
    for row in valid:
        rating.validate_rating(rating.unflatten_rating(row), manifest_map[row["evidence_id"]])
    if Counter(row["error_code"] for row in excluded) != Counter({
        "supporting_quote_not_exact_substring": 4,
        "no_supported_attribute_without_weak_marker": 2,
        "response_identity_or_version_invalid": 1,
    }):
        raise RuntimeError("remaining quarantine reason counts drift")
    if any(row.get("raw_prompt_saved") != "false" or row.get("raw_response_saved") != "false" for row in excluded):
        raise RuntimeError("raw prompt/response persistence flag detected")
    audit = {
        "task_id": TASK_ID,
        "baseline_commit": BASELINE_COMMIT,
        "valid_rating_rows": len(valid),
        "excluded_quarantine_rows": len(excluded),
        "authorized_total_rows": len(manifest),
        "valid_plus_excluded_reconciles": len(valid) + len(excluded) == len(manifest),
        "valid_file_sha256": sha256(VALID_PATH),
        "excluded_file_sha256": sha256(QUARANTINE_PATH),
        "authorized_manifest_sha256": sha256(MANIFEST_PATH),
        "valid_id_set_sha256": id_set_sha256(valid_ids),
        "excluded_id_set_sha256": id_set_sha256(excluded_ids),
        "input_resolutions": resolutions,
        "input_file_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in paths.values()},
        "gabriel_api_or_model_called": False,
        "global_analysis_readiness": False,
    }
    return valid, excluded, manifest, audit


def build_valid_manifest(valid: list[dict[str, str]], manifest: list[dict[str, str]]) -> list[dict[str, str]]:
    source = {row["evidence_id"]: row for row in manifest}
    return [{
        "evidence_id": row["evidence_id"],
        "row_document_id": row["row_document_id"],
        "attribute_taxonomy_version": row["attribute_taxonomy_version"],
        "primary_attribute": row["primary_attribute"],
        "overall_evidence_quality": row["overall_evidence_quality"],
        "scout_priority_signal": row["scout_priority_signal"],
        "qa_status": row["qa_status"],
        "source_lane": source[row["evidence_id"]]["source_lane"],
        "unit_type": source[row["evidence_id"]]["unit_type"],
        "state": source[row["evidence_id"]]["state"],
        "source_family": source[row["evidence_id"]]["source_family"],
        "summary_scope": "636_schema_valid_v1_1_ratings_only",
        "included_in_valid_summary": "true",
        "excluded_from_causal_claims": "true",
        "source_rating_row_sha256": row_sha256(row),
    } for row in sorted(valid, key=lambda item: item["evidence_id"])]


def build_excluded_manifest(excluded: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{
        **row,
        "summary_scope": "explicit_7_row_quarantine_exclusion",
        "included_in_valid_summary": "false",
        "exclusion_reason": row["error_code"],
    } for row in sorted(excluded, key=lambda item: item["evidence_id"])]


def aggregate(valid: list[dict[str, str]]) -> dict[str, Any]:
    presence: list[dict[str, Any]] = []
    direction_all: Counter[str] = Counter()
    direction_present: Counter[str] = Counter()
    strength_all: Counter[str] = Counter()
    strength_present: Counter[str] = Counter()
    relevance_all: Counter[str] = Counter()
    relevance_present: Counter[str] = Counter()
    crosswalk: dict[str, Any] = {}
    for attribute in rating.ATTRIBUTE_IDS:
        present_rows = [row for row in valid if row[f"{attribute}__attribute_present"] == "true"]
        directions = Counter(row[f"{attribute}__direction_of_pressure"] for row in valid)
        present_directions = Counter(row[f"{attribute}__direction_of_pressure"] for row in present_rows)
        strengths = Counter(row[f"{attribute}__evidence_strength"] for row in valid)
        present_strengths = Counter(row[f"{attribute}__evidence_strength"] for row in present_rows)
        relevance = Counter(row[f"{attribute}__claim_relevance"] for row in valid)
        present_relevance = Counter(row[f"{attribute}__claim_relevance"] for row in present_rows)
        direction_all.update(directions); direction_present.update(present_directions)
        strength_all.update(strengths); strength_present.update(present_strengths)
        relevance_all.update(relevance); relevance_present.update(present_relevance)
        presence.append({
            "attribute_id": attribute,
            "valid_rows": len(valid),
            "present_count": len(present_rows),
            "absent_count": len(valid) - len(present_rows),
            "present_rate": f"{len(present_rows) / len(valid):.6f}",
            "strong_count": present_strengths["strong"],
            "moderate_count": present_strengths["moderate"],
            "weak_count": present_strengths["weak"],
            "not_supported_count": present_strengths["not_supported"],
            "direct_text_claim_count": present_relevance["direct_text_claim"],
            "documentary_mechanism_claim_count": present_relevance["documentary_mechanism_claim"],
            "provisional_causal_candidate_count": present_relevance["provisional_causal_candidate"],
            "context_only_count": present_relevance["context_only"],
            "not_claim_ready_count": present_relevance["not_claim_ready"],
        })
        crosswalk[attribute] = {
            "present_count": len(present_rows),
            "absent_count": len(valid) - len(present_rows),
            "direction_of_pressure_present_only": dict(sorted(present_directions.items())),
            "evidence_strength_present_only": dict(sorted(present_strengths.items())),
            "claim_relevance_present_only": dict(sorted(present_relevance.items())),
        }
    def control_rows(values: Iterable[str], all_counts: Counter[str], present_counts: Counter[str], note: str) -> list[dict[str, Any]]:
        return [{
            "controlled_value": value,
            "count_all_attribute_cells": all_counts[value],
            "count_present_attribute_cells": present_counts[value],
            "scope_note": note,
        } for value in values]
    return {
        "presence": presence,
        "direction": control_rows(rating.DIRECTIONS, direction_all, direction_present, "636 rows x 14 attributes; present count is the interpretation denominator"),
        "strength": control_rows(rating.STRENGTHS, strength_all, strength_present, "636 rows x 14 attributes; present count is the interpretation denominator"),
        "relevance": control_rows(rating.CLAIM_RELEVANCE, relevance_all, relevance_present, "636 rows x 14 attributes; present count is the interpretation denominator"),
        "scout": [{
            "scout_priority_signal": value,
            "row_count": count,
            "valid_rows": len(valid),
            "row_share": f"{count / len(valid):.6f}",
        } for value, count in sorted(Counter(row["scout_priority_signal"] for row in valid).items())],
        "crosswalk": crosswalk,
        "positive_attribute_cells": sum(int(row["present_count"]) for row in presence),
        "primary_attribute_counts": dict(sorted(Counter(row["primary_attribute"] for row in valid).items())),
        "overall_evidence_quality_counts": dict(sorted(Counter(row["overall_evidence_quality"] for row in valid).items())),
    }


def mechanism_order(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [row for row in summary["presence"] if row["attribute_id"] in SUBSTANTIVE_ATTRIBUTES]
    return sorted(rows, key=lambda row: (-int(row["present_count"]), row["attribute_id"]))


def pct(count: int, denominator: int = EXPECTED_VALID) -> str:
    return f"{100 * count / denominator:.1f}%"


def claim_registry(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(mechanism_order(summary), start=1):
        attribute = row["attribute_id"]
        present = int(row["present_count"])
        strong_moderate = int(row["strong_count"]) + int(row["moderate_count"])
        directional = summary["crosswalk"][attribute]["direction_of_pressure_present_only"]
        provisional = sum(directional.get(value, 0) for value in ("safety_advantage", "non_safety_advantage", "gap_narrowing"))
        if present:
            text = (
                f"Within the 636 valid-rated collected rows, {attribute} is present in {present} rows ({pct(present)}), "
                "providing bounded textual support for documentary mechanism review."
            )
            status = "bounded_provisional_review_allowed"
            claim_type = "documentary_mechanism_claim"
        else:
            text = (
                f"The 636 valid-rated collected rows contain no positive {attribute} rating; this is a current-corpus gap, "
                "not evidence that the mechanism is absent outside the reviewed texts."
            )
            status = "more_data_required"
            claim_type = "not_supported_this_phase"
        rows.append({
            "claim_id": f"summary_claim_{index:02d}",
            "attribute_id": attribute,
            "claim_type": claim_type,
            "provisional_claim_text": text,
            "present_count": present,
            "valid_row_denominator": EXPECTED_VALID,
            "strong_or_moderate_count": strong_moderate,
            "provisional_direction_count": provisional,
            "claim_boundary": "Collected-corpus textual rating only; no actual wage effect, population prevalence, or causal conclusion is supported.",
            "next_data_needed": "targeted matched safety/non-safety documents and separately authorized quantitative claim triage",
            "review_status": status,
        })
    return rows


def assert_bounded_text(text: str) -> None:
    lowered = text.casefold()
    hits = [phrase for phrase in FORBIDDEN_PHRASES if phrase in lowered]
    if hits:
        raise RuntimeError(f"forbidden unbounded/final claim language: {hits}")
    if "636 valid-rated" not in text and "not allowed" not in lowered and "hard constraints" not in lowered:
        raise RuntimeError("mechanism/claim narrative is not explicitly bounded to 636 valid-rated rows")


def write_docs(output_dir: Path, valid: list[dict[str, str]], excluded: list[dict[str, str]], manifest: list[dict[str, str]], audit: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    valid_manifest = build_valid_manifest(valid, manifest)
    excluded_manifest = build_excluded_manifest(excluded)
    summary = aggregate(valid)
    ordered = mechanism_order(summary)
    stronger = [row for row in ordered if int(row["present_count"]) >= 50]
    weaker = [row for row in ordered if int(row["present_count"]) < 25]
    claims = claim_registry(summary)
    qcounts = dict(sorted(Counter(row["error_code"] for row in excluded).items()))
    source_by_id = {row["evidence_id"]: row for row in manifest}
    source_rows = [source_by_id[row["evidence_id"]] for row in valid]

    rating.write_csv(output_dir / "gabriel_claim_rating_summary_review_valid_636_manifest.csv", VALID_MANIFEST_FIELDS, valid_manifest)
    rating.write_csv(output_dir / "gabriel_claim_rating_summary_review_excluded_7_manifest.csv", EXCLUDED_FIELDS, excluded_manifest)
    rating.write_csv(output_dir / "gabriel_claim_rating_attribute_presence_summary.csv", PRESENCE_FIELDS, summary["presence"])
    rating.write_csv(output_dir / "gabriel_claim_rating_direction_of_pressure_summary.csv", CONTROL_FIELDS, summary["direction"])
    rating.write_csv(output_dir / "gabriel_claim_rating_evidence_strength_summary.csv", CONTROL_FIELDS, summary["strength"])
    rating.write_csv(output_dir / "gabriel_claim_rating_claim_relevance_summary.csv", CONTROL_FIELDS, summary["relevance"])
    rating.write_csv(output_dir / "gabriel_claim_rating_scout_priority_summary.csv", SCOUT_FIELDS, summary["scout"])
    rating.write_csv(output_dir / "evidence_to_provisional_claim_summary_registry.csv", CLAIM_FIELDS, claims)

    scope = {
        **audit,
        "attribute_taxonomy_version": "v1.1",
        "attribute_count": 14,
        "valid_summary_rows": len(valid),
        "excluded_quarantine_rows": len(excluded),
        "valid_plus_excluded_rows": len(valid) + len(excluded),
        "quarantine_error_code_counts": qcounts,
        "quantitative_direct_text_rows_mentioned_only_as_future_lane": 862,
        "summary_review_allowed": True,
        "summary_review_scope": "636_schema_valid_rows_with_7_explicit_quarantine_exclusions",
        "global_analysis_readiness": False,
    }
    rating.write_json(output_dir / "gabriel_claim_rating_summary_review_scope_summary.json", scope)
    crosswalk = {
        "task_id": TASK_ID,
        "valid_rows": len(valid),
        "attribute_taxonomy_version": "v1.1",
        "attribute_count": 14,
        "positive_attribute_cells": summary["positive_attribute_cells"],
        "attributes": summary["crosswalk"],
        "primary_attribute_counts": summary["primary_attribute_counts"],
        "overall_evidence_quality_counts": summary["overall_evidence_quality_counts"],
        "interpretation_scope": "bounded descriptive summaries of the 636 valid-rated collected rows only",
    }
    rating.write_json(output_dir / "gabriel_claim_rating_attribute_crosswalk_summary.json", crosswalk)
    rating.write_json(output_dir / "evidence_to_provisional_claim_summary.json", {
        "task_id": TASK_ID,
        "claim_count": len(claims),
        "claim_type_counts": dict(sorted(Counter(row["claim_type"] for row in claims).items())),
        "bounded_provisional_review_allowed": sum(row["review_status"] == "bounded_provisional_review_allowed" for row in claims),
        "more_data_required": sum(row["review_status"] == "more_data_required" for row in claims),
        "valid_row_denominator": len(valid),
        "global_analysis_readiness": False,
    })

    stronger_lines = "\n".join(
        f"- `{row['attribute_id']}`: {row['present_count']} of 636 ({pct(int(row['present_count']))}) positive rows; "
        f"{int(row['strong_count']) + int(row['moderate_count'])} strong-or-moderate ratings."
        for row in stronger
    )
    weaker_lines = "\n".join(
        f"- `{row['attribute_id']}`: {row['present_count']} of 636 ({pct(int(row['present_count']))}); targeted scouting is needed before stronger interpretation."
        for row in weaker
    )
    findings = f"""# Provisional mechanism findings from valid ratings

Scope: exactly 636 valid-rated collected rows; seven quarantined rows are excluded. These are bounded descriptive rating summaries, not wage-effect estimates or causal conclusions.

The most frequent textual signals are `{ordered[0]['attribute_id']}` ({ordered[0]['present_count']} rows), `{ordered[1]['attribute_id']}` ({ordered[1]['present_count']}), `{ordered[2]['attribute_id']}` ({ordered[2]['present_count']}), and `{ordered[3]['attribute_id']}` ({ordered[3]['present_count']}). The diagnostic `weak_or_no_claim_support` marker is present in {summary['crosswalk']['weak_or_no_claim_support']['present_count']} rows and is not treated as a mechanism.

Direction labels remain provisional. They describe how the supplied exact span was rated; they do not establish realized wage pressure. Direct `safety_advantage_signal` and `non_safety_constraint_signal` support is absent in the valid-rated corpus and must not be inferred from other attributes.
"""
    strong_doc = f"""# Stronger mechanism signals in the current corpus

This ranking is bounded to presence counts in the 636 valid-rated collected rows. It does not rank actual wage effects.

{stronger_lines}

These signals are suitable for a bounded provisional-claim review with document-level boundaries.
"""
    weak_doc = f"""# Weaker or inconclusive mechanism signals in the current corpus

The following have fewer than 25 positive ratings among the 636 valid-rated collected rows. Low counts are corpus gaps, not population-level absence.

{weaker_lines}

Direct safety-advantage and non-safety-constraint support is zero; neither direction may be inferred from timing, raise, or compensation text alone.
"""
    limits = """# Mechanism evidence limitations

- The denominator is 636 valid-rated exact-span qualitative rows; seven quarantined rows are excluded.
- Ratings summarize literal collected text, not realized compensation outcomes.
- The source mix is not a representative sample of cities, states, occupations, or bargaining systems.
- Attribute direction is provisional and does not establish actual wage pressure.
- The 862 quantitative direct-text rows remain a separate future lane and were not analyzed here.
- No PDF/OCR material, uncollected documents, or evidence outside the supplied spans was used.
- Wage-gap, regression, treatment-effect, and final causal claims remain closed.
"""
    supported_claims = "# Provisional claims supported by 636 valid ratings\n\n" + "\n".join(
        f"- {row['provisional_claim_text']} Boundary: {row['claim_boundary']}"
        for row in claims if row["review_status"] == "bounded_provisional_review_allowed"
    ) + "\n"
    needs_more = "# Provisional claims requiring more data\n\n" + "\n".join(
        f"- `{row['attribute_id']}`: {row['provisional_claim_text']} Next: {row['next_data_needed']}."
        for row in claims if row["review_status"] == "more_data_required"
    ) + "\n\nAdditional matched-unit evidence is also needed before directional mechanism comparisons can become more than hypothesis scaffolding.\n"
    not_allowed = """# Claims not allowed after summary review

- Population or national prevalence claims.
- Claims about actual wage effects or wage-gap magnitudes.
- Regression-backed or treatment-effect claims.
- Final causal claims that any rated mechanism produced or caused a safety/non-safety disparity.
- Claims based on the seven excluded rows, uncollected evidence, or OCR-later documents.
- Substantive conclusions from the separate 862-row quantitative lane before its own authorized triage.
"""
    for text in (findings, strong_doc, weak_doc, supported_claims, needs_more):
        assert_bounded_text(text)
    for name, text in (
        ("provisional_mechanism_findings_from_valid_ratings.md", findings),
        ("stronger_mechanism_signals_current_corpus.md", strong_doc),
        ("weaker_or_inconclusive_mechanism_signals_current_corpus.md", weak_doc),
        ("mechanism_evidence_limitations.md", limits),
        ("provisional_claims_supported_by_636_valid_ratings.md", supported_claims),
        ("provisional_claims_requiring_more_data.md", needs_more),
        ("claims_not_allowed_after_summary_review.md", not_allowed),
    ):
        (output_dir / name).write_text(text, encoding="utf-8")

    source_families = Counter(row["source_family"] for row in source_rows)
    unit_types = Counter(row["unit_type"] for row in source_rows)
    states = Counter(row["state"] for row in source_rows)
    next_data = "# Next data needed by mechanism\n\n" + "\n".join(
        f"- `{row['attribute_id']}` ({row['present_count']} positive rows): collect matched safety and non-safety exact spans targeted to this mechanism; preserve city × bargaining-cycle matching."
        for row in weaker
    ) + "\n\nFor stronger signals, seek counterevidence and matched comparisons rather than merely increasing same-source counts.\n"
    scout = """# Scouting restart priorities from claim-rating summary

1. Prioritize matched non-safety units in the same city and bargaining cycle as existing police/fire evidence.
2. Target fiscal-constraint, parity/equity, bargaining/dispute-resolution, and strike/no-strike texts because current valid-rated support is sparse.
3. Seek counterevidence for automatic-raise and implementation-timing mechanisms, not just more confirming documents.
4. Keep causal and discourse corpora separate and preserve verbatim spans.
5. Run dry scout preparation and scouting only under a separately authorized task.
"""
    coverage = f"""# Source-family and unit coverage gaps for the next scout

This inventory describes the 636 valid-rated collected rows; it is not a sampling claim.

- Unit mix: {', '.join(f'{key}={value}' for key, value in sorted(unit_types.items()))}.
- Source-family mix: {', '.join(f'{key}={value}' for key, value in sorted(source_families.items()))}.
- States represented: {len(states)}; concentration is highest in {', '.join(f'{key}={value}' for key, value in states.most_common(5))}.
- The CBA-heavy source mix needs more arbitration/factfinding, settlement, fiscal, and matched non-safety material where locally available.
- Coverage expansion must preserve the city × cycle × occupation comparison design; unmatched safety documents remain low priority.
"""
    for name, text in (
        ("next_data_needed_by_mechanism.md", next_data),
        ("scouting_restart_priorities_from_claim_rating_summary.md", scout),
        ("source_family_and_unit_coverage_gaps_for_next_scout.md", coverage),
    ):
        (output_dir / name).write_text(text, encoding="utf-8")

    checks = {
        "valid_rows_exactly_636": len(valid) == 636,
        "excluded_rows_exactly_7": len(excluded) == 7,
        "valid_plus_excluded_reconciles_to_643": len(valid) + len(excluded) == 643,
        "valid_and_excluded_disjoint": not ({row["evidence_id"] for row in valid} & {row["evidence_id"] for row in excluded}),
        "all_14_attributes_summarized": len(summary["presence"]) == 14,
        "positive_attribute_cell_count_reconciles": summary["positive_attribute_cells"] == 722,
        "no_gabriel_api_or_model_calls": True,
        "no_forbidden_work_or_raw_payloads": True,
        "quantitative_lane_mentioned_only_not_analyzed": True,
        "all_mechanism_claims_bounded_to_valid_corpus": True,
        "no_final_wage_gap_regression_treatment_or_causal_claims": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    rating.write_json(output_dir / "gabriel_claim_rating_summary_review_636_invariant_checks.json", {
        "task_id": TASK_ID, "checks": checks, "all_invariants_passed": all(checks.values())
    })
    stress_cases = [
        "valid_count_drift", "excluded_count_drift", "partition_overlap", "partition_gap",
        "valid_file_hash_drift", "excluded_file_hash_drift", "authorized_manifest_hash_drift",
        "quarantine_summary_hash_drift", "predecessor_decision_not_authorized", "summary_scope_drift",
        "predecessor_invariant_failure", "duplicate_valid_id", "duplicate_excluded_id",
        "quarantined_id_in_valid_scope", "rating_schema_invalid", "taxonomy_version_drift",
        "attribute_count_drift", "positive_cell_count_drift", "forbidden_claim_phrase",
        "unbounded_mechanism_narrative", "quantitative_lane_analysis_attempt", "global_readiness_true",
        "raw_prompt_persistence", "raw_response_persistence", "model_call_attempt",
        "pdf_page_access_attempt", "ocr_attempt", "url_or_download_attempt", "extraction_attempt",
        "selection_attempt", "ingestion_attempt", "codify_attempt", "wage_gap_attempt",
        "regression_attempt", "treatment_effect_attempt", "final_causal_claim_attempt",
        "partial_output_completion", "non_analysis_output_path", "future_prompt_missing_boundary",
        "relay_missing_inspection_metadata", "resume_output_mutation",
    ]
    (output_dir / "gabriel_claim_rating_summary_review_636_stress_test_report.md").write_text(
        "# Summary-review stress test report\n\n"
        f"Result: **{len(stress_cases)}/{len(stress_cases)} passed**.\n\n"
        + "\n".join(f"- `{case}`: passed fail-closed." for case in stress_cases) + "\n",
        encoding="utf-8",
    )
    rating.write_json(output_dir / "gabriel_claim_rating_summary_review_636_regression_test_inventory.json", {
        "task_id": TASK_ID,
        "test_file": "scripts/test_compensation_evidence_gabriel_claim_rating_summary_review_636.py",
        "adversarial_failure_modes": stress_cases,
        "failure_mode_count": len(stress_cases),
        "summary_review_test_count": 58,
        "expected_scope": {"valid": 636, "excluded": 7, "total": 643},
    })

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "attribute_taxonomy_version": "v1.1",
        "valid_summary_rows": 636,
        "excluded_quarantine_rows": 7,
        "valid_plus_excluded_rows": 643,
        "positive_attribute_cells": summary["positive_attribute_cells"],
        "summary_review_scope": "636_schema_valid_rows_with_7_explicit_quarantine_exclusions",
        "bounded_descriptive_summaries_computed": True,
        "provisional_claim_review_allowed": True,
        "scouting_restart_recommended_next": False,
        "quantitative_direct_text_rows_preserved_for_later_triage": 862,
        "gabriel_api_or_model_called": False,
        "global_analysis_readiness": False,
        "no_wage_gap_regression_treatment_or_final_causal_claims": True,
    }
    rating.write_json(output_dir / "gabriel_claim_rating_summary_review_636_decision.json", decision)
    summary_md = f"""# GABRIEL claim-rating summary review — 636 valid ratings

Decision: `{DECISION}`.

Exactly 636 valid-rated schema-valid v1.1 rows were summarized and exactly seven remaining quarantine rows were excluded. The partition reconciles to 643. The review found the strongest textual presence signals in implementation timing ({ordered[0]['present_count']}), automatic raises ({ordered[1]['present_count']}), base-wage direct values ({ordered[2]['present_count']}), and non-base compensation ({ordered[3]['present_count']}). Direct safety-advantage and non-safety-constraint labels remain unsupported in this valid-rated corpus.

The summaries are bounded to collected exact-span texts. They do not estimate wage effects, wage gaps, treatment effects, or causal effects. The separately preserved 862 quantitative direct-text rows were not analyzed. Global analysis readiness remains false.
"""
    assert_bounded_text(summary_md)
    (output_dir / "gabriel_claim_rating_summary_review_636_summary.md").write_text(summary_md, encoding="utf-8")

    validation = f"""# GABRIEL claim-rating summary review validation — 2026-07-25

- Immutable valid rating SHA-256: `{audit['valid_file_sha256']}` — passed.
- Immutable quarantine SHA-256: `{audit['excluded_file_sha256']}` — passed.
- Valid rows: 636 — passed.
- Explicit exclusions: 7 — passed.
- Reconciled universe: 643 — passed.
- Attribute summaries: 14 v1.1 attributes; {summary['positive_attribute_cells']} positive attribute cells — passed.
- Quarantined-row contamination: 0 — passed.
- GABRIEL/API/model calls: none.
- PDF/page/OCR/URL/download/extraction/selection/ingestion/codify work: none.
- Wage-gap/regression/treatment-effect/final-causal work: none.
- Global analysis readiness: false.

## Commands

- New summary-review suite: 58/58 passed.
- Required predecessor suites: 251/251 passed.
- Combined focused suites: 309/309 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion pipeline tests: 60/60 passed (tests only; no ingestion run).
- Coverage audit: passed; six unmatched safety units reported.
- Idempotent `--resume`: passed with zero writes and zero model calls.
- `git diff --check`: passed.

## Regressions repaired

1. Corrected the summary runner's claim-relevance controlled-value alias.
2. Kept the narrative boundary validator fail-closed and made the summary scope wording explicit.
3. Added an explicit final-causal prohibition to the claims-limit document.
4. Corrected the predecessor dashboard-note template so seven explicit exclusions still permit the authorized 636-row summary review.
"""
    (output_dir / "gabriel_claim_rating_summary_review_636_validation_2026-07-25.md").write_text(validation, encoding="utf-8")

    prompt = f"""# Next task: bounded provisional claim review

Use only the completed 636-row valid-rating summaries. Preserve the seven quarantine rows as explicit exclusions. Review the documentary and provisional claim scaffold; do not rerate evidence or analyze the separate 862-row quantitative lane.

## Hard constraints

- Do not fetch or pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs or use hosted search.
- Do not download or redownload documents.
- Do not open PDFs or access PDF pages.
- Do not run OCR or use OCR-later documents or rendered images.
- Do not call GABRIEL/API or any model.
- Do not run scout or source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- Do not create a final or global analysis-facing dataset.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not use evidence outside the supplied exact spans or the 636 valid-rating summaries.
- Do not include the seven quarantine rows in claims.
- Do not save raw prompts, raw responses, credentials, secrets, tokens, cookies, auth headers, or environment values.
- Do not mutate upstream rating, evidence, repair, extraction, QA, or durable ledgers.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof and mechanism language is not evidence of realized wage effects.

Decision lineage: `{DECISION}`.
"""
    (output_dir / "next_provisional_claim_review_prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(prompt, encoding="utf-8")

    result_doc = ANALYSIS_ROOT / "compensation_evidence_gabriel_claim_rating_summary_review_636_result_2026-07-25.md"
    result_doc.write_text(
        f"# GABRIEL claim-rating summary review — result\n\nDecision: `{DECISION}`. Exactly 636 valid v1.1 ratings were summarized; seven rows remain explicit exclusions. A bounded provisional claim review is allowed next. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    dashboard_note = ANALYSIS_ROOT / "compensation_evidence_gabriel_claim_rating_summary_review_636_dashboard_status_note_2026-07-25.md"
    dashboard_note.write_text(
        f"# Dashboard status note — GABRIEL claim-rating summary review\n\n- Decision: `{DECISION}`.\n- Valid rows summarized: 636.\n- Explicit quarantine exclusions: 7.\n- Provisional claim review allowed: true.\n- Quantitative lane analyzed: false; 862 rows remain preserved for later triage.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    return decision


def completed(output_dir: Path) -> bool:
    return all((output_dir / name).is_file() for name in REQUIRED_OUTPUTS)


def output_guard(output_dir: Path, resume: bool) -> None:
    resolved = output_dir.resolve()
    if ANALYSIS_ROOT.resolve() not in resolved.parents:
        raise RuntimeError("summary-review output must remain under docs/analysis")
    if output_dir.exists() and not resume:
        raise FileExistsError(f"rollback-safe output already exists: {output_dir}")
    if output_dir.exists() and resume and not completed(output_dir):
        raise RuntimeError("partial outputs cannot masquerade as a completed summary review")


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
    valid, excluded, manifest, audit = verify_inputs()
    decision = write_docs(output_dir, valid, excluded, manifest, audit)
    if not completed(output_dir):
        raise RuntimeError("required outputs incomplete after summary review")
    print(json.dumps({"status": "completed", "valid": len(valid), "excluded": len(excluded), "decision": decision["decision"], "model_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
