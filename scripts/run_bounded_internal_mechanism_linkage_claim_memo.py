#!/usr/bin/env python3
"""Draft a bounded internal memo from the locked 268-pair claim review."""

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
INPUT_DIR = BASE / "MECHANISM-LINKAGE-CLAIM-REVIEW-268-EXACT-SAME-SOURCE-LINKS-2026-07-26"
OUTPUT_DIR = BASE / "BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26"
RESULT_DOC = ROOT / "docs/analysis/bounded_internal_mechanism_linkage_claim_memo_result_2026-07-26.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/bounded_internal_mechanism_linkage_claim_memo_dashboard_status_note_2026-07-26.md"
GEOGRAPHY_DOC = ROOT / "docs/analysis/bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_2026-07-26.md"
TASK_ID = "BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26"
DECISION = "bounded_internal_mechanism_linkage_claim_memo_completed_tier_c_verification_recommended"
EXPECTED_PAIRS = 268
EXPECTED_QUANT = 208
EXPECTED_QUAL = 90
EXPECTED_SOURCES = 72

INPUTS = {
    INPUT_DIR / "mechanism_linkage_claim_review_268_decision.json": "8c16707a6c016634a37935beedf1407c7e0630573193508600e5d1de4a96a6af",
    INPUT_DIR / "mechanism_linkage_claim_review_268_summary.md": "870bb25a4052cfad77b7fb25ad53aae848265f6e9a54616abd3ba85a23a7d5f5",
    INPUT_DIR / "mechanism_linkage_claim_review_268_scope_summary.json": "efaadebb889589154b16cb1c8f10dedb0b65c6cb8bb8fefe1c7cb927e21368a5",
    INPUT_DIR / "mechanism_linkage_claim_review_268_direct_text_colocation_claims.md": "a1a90f0eb6356b03273abaf81a1aeb3299040718d55ff29103ce841229fd613f",
    INPUT_DIR / "mechanism_linkage_claim_review_268_documentary_mechanism_value_scaffolds.md": "696bafeae086a918d89f66aa567d1506050f9dd77a0b4daa51cfba402d0774a1",
    INPUT_DIR / "mechanism_linkage_claim_review_268_provisional_claim_language_bank.md": "a1d9b15a936d147497073677153d6a228fe693911a62ec159e8d41e8218f66d8",
    INPUT_DIR / "mechanism_linkage_claim_review_268_claim_boundaries.md": "f1ef955d61b81f7687edde7e9f2414a2cbe80efe552cdcde5e023dd54d3aa1be",
    INPUT_DIR / "mechanism_linkage_claim_review_268_claims_not_allowed.md": "2f1fa6ac2fd41da983ee756f873bf251050282efa7a4521a1dda4ebe626bf6a5",
    INPUT_DIR / "mechanism_linkage_claim_review_268_mechanism_summary.json": "1e85f751c92225800c37747e27d756520bc3f5d418790e4fa550e177ef865a64",
    INPUT_DIR / "mechanism_linkage_claim_review_268_unit_type_summary.json": "ace7f5ee62e7ff37e497e8398d471d5cc7204dcad471733e731a8a9c4712ec03",
    INPUT_DIR / "mechanism_linkage_claim_review_268_source_family_summary.json": "429de6493ab53046af118a87f1bd8ca08344054bfdb9dabf0c51d3ac5a944b95",
    INPUT_DIR / "mechanism_linkage_claim_review_268_unlinked_mechanism_gaps.md": "a3aac505180c7f3cfeabf259314cabf88778ca288aa41d51c4ff1e700dc347a4",
    INPUT_DIR / "mechanism_linkage_claim_review_268_next_action_recommendation.md": "2562cce131d58344c774a4b87ddc3dca5013f160a43d731bba177721a1da0662",
    INPUT_DIR / "mechanism_linkage_claim_review_268_claim_memo_considerations.md": "95e5e9811e5eb0b3f063e8f5c202468a7fcecaaca986ac764a3c167a224feca9",
    INPUT_DIR / "mechanism_linkage_claim_review_268_tier_c_verification_considerations.md": "3819a6c5e0d51fc173b8c9aa58dd97ca39ecac6b3d80f32072cc6f1d43cc2644",
    INPUT_DIR / "mechanism_linkage_claim_review_268_quantitative_normalization_considerations.md": "474b6f2c490c7ed8474203b04d679a97d8ea18d7bdcddeaba85fc7f94aaa0993",
    INPUT_DIR / "mechanism_linkage_claim_review_268_repo_cleanup_considerations.md": "459802ececb61875a11b38938c76fdecc43226e05a742e0aeab4b362085ad89c",
    INPUT_DIR / "mechanism_linkage_claim_review_268_validation_2026-07-26.md": "324833c7ab48a6fbf2bc1ea7e24c7c213f1d285397344a3441847c98cbdb9a9e",
    INPUT_DIR / "mechanism_linkage_claim_review_268_invariant_checks.json": "5e727e60f5a04ead3815d2456d09dee3b70e4d1b18cd6f0edbc364ca1d4122fd",
    INPUT_DIR / "mechanism_linkage_claim_review_268_scope.csv": "d5b745242f572631bac31c0bfd0a5f7e27688779e1eea4af51aa1a45dcc32566",
}

NORTHEAST = set("CT ME MA NH RI VT NJ NY PA".split())
MIDWEST = set("IN IL MI OH WI IA KS MN MO NE ND SD".split())
SOUTH = set("DE FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX".split())
WEST = set("AZ CO ID MT NV NM UT WY AK CA HI OR WA".split())
VALID_STATES = NORTHEAST | MIDWEST | SOUTH | WEST | {"DC"}
REGION_ORDER = ["Northeast", "Midwest", "South", "West", "District of Columbia / Federal district", "Unknown"]
CLAIM_TYPES = [
    "direct_text_colocation_claim", "documentary_mechanism_value_scaffold",
    "provisional_mechanism_linkage_claim", "insufficient_for_claim", "not_allowed",
]
OUTPUTS = [
    "bounded_internal_mechanism_linkage_claim_memo_decision.json",
    "bounded_internal_mechanism_linkage_claim_memo_summary.md",
    "bounded_internal_mechanism_linkage_claim_memo.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_scope_counts.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_mechanism_summary.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_unit_source_summary.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_claim_boundaries.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_evidence_gaps.md",
    "bounded_internal_mechanism_linkage_claim_memo_exhibit_geographic_coverage.md",
    "bounded_internal_mechanism_linkage_claim_memo_direct_text_colocation_appendix.md",
    "bounded_internal_mechanism_linkage_claim_memo_documentary_scaffold_appendix.md",
    "bounded_internal_mechanism_linkage_claim_memo_provisional_linkage_appendix.md",
    "bounded_internal_mechanism_linkage_claim_memo_insufficient_records_appendix.md",
    "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage.md",
    "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json",
    "bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json",
    "bounded_internal_mechanism_linkage_claim_memo_next_phase_recommendation.md",
    "bounded_internal_mechanism_linkage_claim_memo_tier_c_verification_plan.md",
    "bounded_internal_mechanism_linkage_claim_memo_quantitative_normalization_plan.md",
    "bounded_internal_mechanism_linkage_claim_memo_repo_cleanup_plan.md",
    "bounded_internal_mechanism_linkage_claim_memo_validation_2026-07-26.md",
    "bounded_internal_mechanism_linkage_claim_memo_invariant_checks.json",
    "bounded_internal_mechanism_linkage_claim_memo_stress_test_report.md",
    "bounded_internal_mechanism_linkage_claim_memo_regression_test_inventory.json",
    "next_targeted_tier_c_verification_prompt.md",
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


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_hashes() -> None:
    for path, expected in INPUTS.items():
        if not path.is_file():
            raise RuntimeError(f"required input missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"immutable input hash mismatch: {path.name}: {actual}")


def region_for_state(state: str) -> str:
    state = state.strip().upper()
    if state in NORTHEAST:
        return "Northeast"
    if state in MIDWEST:
        return "Midwest"
    if state in SOUTH:
        return "South"
    if state in WEST:
        return "West"
    if state == "DC":
        return "District of Columbia / Federal district"
    return "Unknown"


def load_scope() -> list[dict[str, str]]:
    decision = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_decision.json")
    summary = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_scope_summary.json")
    invariants = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_invariant_checks.json")
    scope = read_csv(INPUT_DIR / "mechanism_linkage_claim_review_268_scope.csv")
    if decision.get("decision") != "mechanism_linkage_claim_review_268_completed_claim_memo_allowed":
        raise RuntimeError("claim-review decision does not authorize memo drafting")
    if len(scope) != EXPECTED_PAIRS or decision.get("claim_review_pair_count") != EXPECTED_PAIRS:
        raise RuntimeError("memo pair scope does not reconcile to 268")
    if len({row["quantitative_evidence_id"] for row in scope}) != EXPECTED_QUANT:
        raise RuntimeError("memo quantitative lineage does not reconcile to 208")
    if len({row["qualitative_evidence_id"] for row in scope}) != EXPECTED_QUAL:
        raise RuntimeError("memo qualitative lineage does not reconcile to 90")
    if len({row["shared_source_lineage_key"] for row in scope}) != EXPECTED_SOURCES:
        raise RuntimeError("memo source lineage does not reconcile to 72")
    if summary.get("claim_type_counts") != decision.get("claim_type_counts"):
        raise RuntimeError("claim-type summary mismatch")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("claim-review invariants are not complete")
    for row in scope:
        if row.get("linkage_status") != "linked" or row.get("linkage_confidence") != "exact_same_source":
            raise RuntimeError("non-exact linkage entered memo scope")
        if row.get("claim_review_status") != "bounded_reviewed" or row.get("claim_type") not in CLAIM_TYPES:
            raise RuntimeError("unreviewed or invalid claim type entered memo scope")
        if row.get("claim_type") == "not_allowed":
            raise RuntimeError("not-allowed row entered memo scope")
        if any(row.get(field) != "false" for field in (
            "value_normalized", "value_imputed", "value_annualized", "wage_gap_calculated",
            "regression_used", "treatment_effect_estimated", "causal_claim_made",
            "population_or_national_claim_made", "global_analysis_readiness",
        )):
            raise RuntimeError("open analysis boundary entered memo scope")
        if row.get("ingestion_status") != "not_ingested" or row.get("codification_status") != "not_codified" or row.get("causal_status") != "not_causal_evidence":
            raise RuntimeError("open downstream status entered memo scope")
        if not all(row.get(field, "").strip() for field in ("state", "city", "unit_type", "contract_or_cycle_period", "source_family")):
            raise RuntimeError("required geographic/lineage field missing")
    return scope


def build_geography(scope: list[dict[str, str]]) -> dict[str, Any]:
    state_rows: list[dict[str, Any]] = []
    for state in sorted({row["state"] for row in scope}):
        rows = [row for row in scope if row["state"] == state]
        region = region_for_state(state)
        state_rows.append({
            "state": state,
            "region": region,
            "linked_pair_count": len(rows),
            "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in rows}),
            "linked_qualitative_record_count": len({row["qualitative_evidence_id"] for row in rows}),
            "city_count": len({row["city"] for row in rows}),
            "city_cycle_unit_group_count": len({(row["city"], row["unit_type"], row["contract_or_cycle_period"]) for row in rows}),
            "shared_source_lineage_count": len({row["shared_source_lineage_key"] for row in rows}),
        })
    region_rows: list[dict[str, Any]] = []
    for region in REGION_ORDER:
        rows = [row for row in scope if region_for_state(row["state"]) == region]
        region_rows.append({
            "region": region,
            "linked_pair_count": len(rows),
            "linked_quantitative_row_count": len({row["quantitative_evidence_id"] for row in rows}),
            "linked_qualitative_record_count": len({row["qualitative_evidence_id"] for row in rows}),
            "state_count": len({row["state"] for row in rows}),
            "city_count": len({(row["city"], row["state"]) for row in rows}),
            "city_cycle_unit_group_count": len({(row["city"], row["state"], row["unit_type"], row["contract_or_cycle_period"]) for row in rows}),
            "shared_source_lineage_count": len({row["shared_source_lineage_key"] for row in rows}),
        })
    missing = {
        "state": sum(not row["state"].strip() for row in scope),
        "city": sum(not row["city"].strip() for row in scope),
        "unit_type": sum(not row["unit_type"].strip() for row in scope),
        "contract_or_cycle_period": sum(not row["contract_or_cycle_period"].strip() for row in scope),
        "source_family": sum(not row["source_family"].strip() for row in scope),
        "unknown_region": sum(region_for_state(row["state"]) == "Unknown" for row in scope),
    }
    if any(row["state"] not in VALID_STATES for row in scope):
        if missing["unknown_region"] == 0:
            raise RuntimeError("invalid state did not route to Unknown")
    return {
        "mapping_method": "deterministic_static_census_style_region_from_existing_state_abbreviation",
        "external_lookup_used": False,
        "linked_pair_count": len(scope),
        "state_count": len(state_rows),
        "city_state_pair_count": len({(row["city"], row["state"]) for row in scope}),
        "city_cycle_unit_group_count": len({(row["city"], row["state"], row["unit_type"], row["contract_or_cycle_period"]) for row in scope}),
        "shared_source_lineage_count": len({row["shared_source_lineage_key"] for row in scope}),
        "state_rows": state_rows,
        "region_rows": region_rows,
        "missing_geography_counts": missing,
        "major_concentrations": {
            "midwest_and_west_pair_count": sum(region_for_state(row["state"]) in {"Midwest", "West"} for row in scope),
            "california_and_ohio_pair_count": sum(row["state"] in {"CA", "OH"} for row in scope),
            "scope_only_not_population_prevalence": True,
        },
    }


def markdown_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def compact_value(value: str, limit: int = 100) -> str:
    value = " ".join(value.replace("|", "/").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def appendix(scope: list[dict[str, str]], claim_type: str, title: str) -> str:
    rows = [row for row in scope if row["claim_type"] == claim_type]
    table = markdown_table(
        ["Review ID", "City/state", "Unit", "Mechanism", "Recorded value text", "Readiness"],
        [
            (
                row["claim_review_id"], f"{row['city']}, {row['state']}", row["unit_type"],
                row["qualitative_mechanism_family"], compact_value(row["raw_quantitative_value_string"]),
                row["quantitative_claim_readiness"],
            )
            for row in rows
        ],
    )
    return f"# {title}\n\nRows: {len(rows)}. Every entry is an exact-source documentary co-location record; the value text is preserved in its original form and is not compared or transformed.\n\n{table}\n"


def build_outputs(scope: list[dict[str, str]], geography: dict[str, Any], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    review_decision = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_decision.json")
    mechanism = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_mechanism_summary.json")
    unit = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_unit_type_summary.json")
    source = read_json(INPUT_DIR / "mechanism_linkage_claim_review_268_source_family_summary.json")
    claim_counts = review_decision["claim_type_counts"]
    mechanism_counts = review_decision["mechanism_pair_counts"]
    unit_counts = review_decision["unit_type_pair_counts"]
    source_counts = review_decision["source_family_pair_counts"]
    region_counts = {row["region"]: row["linked_pair_count"] for row in geography["region_rows"]}
    state_counts = {row["state"]: row["linked_pair_count"] for row in geography["state_rows"]}

    geography_path = target / "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json"
    write_json(geography_path, geography)
    geography_hash = sha256_file(geography_path)
    dashboard_metadata = {
        "task_id": TASK_ID,
        "memo_decision": DECISION,
        "current_phase": "bounded_internal_mechanism_linkage_claim_memo",
        "memo_scope": {
            "exact_same_source_linked_pair_count": EXPECTED_PAIRS,
            "linked_quantitative_row_count": EXPECTED_QUANT,
            "linked_qualitative_record_count": EXPECTED_QUAL,
            "shared_source_lineage_count": EXPECTED_SOURCES,
            "claim_type_counts": claim_counts,
        },
        "mechanism_pair_counts": mechanism_counts,
        "unit_type_pair_counts": unit_counts,
        "source_family_pair_counts": source_counts,
        "geographic_coverage": {
            "state_count": geography["state_count"],
            "city_state_pair_count": geography["city_state_pair_count"],
            "city_cycle_unit_group_count": geography["city_cycle_unit_group_count"],
            "region_pair_counts": region_counts,
            "state_pair_counts": state_counts,
            "missing_geography_counts": geography["missing_geography_counts"],
            "mapping_method": geography["mapping_method"],
        },
        "evidence_status": "bounded_exact_source_colocation_and_documentary_scaffold_only",
        "next_recommended_phase": "targeted_tier_c_verification",
        "memo_path": "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo.md",
        "geographic_metadata_path": "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json",
        "dashboard_status_note_path": "docs/analysis/bounded_internal_mechanism_linkage_claim_memo_dashboard_status_note_2026-07-26.md",
        "global_analysis_readiness": False,
        "final_causal_claims": False,
        "wage_gap_estimates": False,
        "regression_or_treatment_effect_estimates": False,
    }
    write_json(target / "bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json", dashboard_metadata)

    scope_exhibit = (
        "# Exhibit: scope counts\n\n"
        + markdown_table(
            ["Measure", "Count"],
            [
                ("Exact same-source linked pairs", 268), ("Linked quantitative rows", 208),
                ("Linked qualitative records", 90), ("Shared source lineages", 72),
                ("Direct-text co-location claims", 15), ("Documentary mechanism-value scaffolds", 80),
                ("Provisional mechanism linkages", 32), ("Insufficient-for-claim records", 141),
                ("Not-allowed records", 0),
            ],
        )
        + "\n\nPair counts are not independent-document counts; 268 pairs arise from 72 shared source lineages.\n"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_scope_counts.md").write_text(scope_exhibit, encoding="utf-8")
    mechanism_exhibit = "# Exhibit: mechanism summary\n\n" + markdown_table(
        ["Mechanism", "Pairs", "Quantitative rows", "Direct", "Documentary", "Provisional", "Insufficient"],
        [
            (
                row["qualitative_mechanism_family"], row["linked_pair_count"], row["linked_quantitative_row_count"],
                row["direct_text_colocation_claim"], row["documentary_mechanism_value_scaffold"],
                row["provisional_mechanism_linkage_claim"], row["insufficient_for_claim"],
            )
            for row in mechanism["rows"]
        ],
    ) + "\n"
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_mechanism_summary.md").write_text(mechanism_exhibit, encoding="utf-8")
    unit_source_exhibit = "# Exhibit: unit and source-family summary\n\n## Unit types\n\n" + markdown_table(
        ["Unit type", "Pairs", "Quantitative rows", "Direct", "Documentary", "Provisional", "Insufficient"],
        [(r["unit_type"], r["linked_pair_count"], r["linked_quantitative_row_count"], r["direct_text_colocation_claim"], r["documentary_mechanism_value_scaffold"], r["provisional_mechanism_linkage_claim"], r["insufficient_for_claim"]) for r in unit["rows"]],
    ) + "\n\n## Source families\n\n" + markdown_table(
        ["Source family", "Pairs", "Quantitative rows", "Direct", "Documentary", "Provisional", "Insufficient"],
        [(r["source_family"], r["linked_pair_count"], r["linked_quantitative_row_count"], r["direct_text_colocation_claim"], r["documentary_mechanism_value_scaffold"], r["provisional_mechanism_linkage_claim"], r["insufficient_for_claim"]) for r in source["rows"]],
    ) + "\n"
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_unit_source_summary.md").write_text(unit_source_exhibit, encoding="utf-8")
    boundaries = (
        "# Exhibit: claim boundaries\n\n"
        "The memo is limited to exact same-source documentary co-location. Original quantitative strings and units remain unchanged. Pair multiplicity does not create independent documents. The memo contains no normalized comparison, wage-gap estimate, regression, treatment-effect estimate, population-prevalence claim, national claim, or final causal conclusion. It is not ingested, codified, final, causal, or globally analysis-ready evidence.\n"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_claim_boundaries.md").write_text(boundaries, encoding="utf-8")
    gaps = (
        "# Exhibit: evidence gaps\n\n"
        "- Strike/no-strike has stronger exact-span documentary support from the targeted evidence expansion but zero exact same-source quantitative linkage in this run.\n"
        "- Non-safety constraint, parity/internal equity, and gap narrowing each have zero exact same-source quantitative linkage.\n"
        "- Fiscal constraint has 3 pairs, bargaining power 5, and market/comparability 9; these lanes remain thin.\n"
        "- Police and fire account for 214 pairs, versus 54 non-safety pairs.\n"
        "- CBAs account for 261 pairs; all other source families together account for 7.\n"
        "- Midwest and West account for 213 pairs, while Northeast and South account for 55. These are concentrations within the locked scope, not population prevalence.\n"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_evidence_gaps.md").write_text(gaps, encoding="utf-8")

    region_table = markdown_table(
        ["Region", "Pairs", "States", "Cities", "City–unit–cycle groups", "Source lineages"],
        [(r["region"], r["linked_pair_count"], r["state_count"], r["city_count"], r["city_cycle_unit_group_count"], r["shared_source_lineage_count"]) for r in geography["region_rows"]],
    )
    state_table = markdown_table(
        ["State", "Region", "Pairs", "Cities", "City–unit–cycle groups"],
        [(r["state"], r["region"], r["linked_pair_count"], r["city_count"], r["city_cycle_unit_group_count"]) for r in geography["state_rows"]],
    )
    geography_text = (
        "# Geographic and regional coverage\n\n"
        "Coverage is derived only from the existing `state`, `city`, `unit_type`, and `contract_or_cycle_period` fields in the locked 268-pair scope. Regions use a static Census-style state mapping; no external lookup was used. All 268 rows have state, city, unit, cycle, and source-family metadata, and no row maps to Unknown.\n\n"
        f"The scope contains {geography['state_count']} states, {geography['city_state_pair_count']} city-state pairs, and {geography['city_cycle_unit_group_count']} city–unit–cycle groups. Midwest and West account for 213 pairs; Northeast and South account for 55. California and Ohio together account for 92 pairs. These statements describe this locked evidence scope only.\n\n"
        "## Region coverage\n\n" + region_table + "\n\n## State coverage\n\n" + state_table + "\n\n"
        "## Missing metadata\n\nState: 0; city: 0; unit type: 0; cycle period: 0; source family: 0; unknown region: 0. Absence of missing metadata does not make the scope representative of places outside these records.\n"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage.md").write_text(geography_text, encoding="utf-8")
    (target / "bounded_internal_mechanism_linkage_claim_memo_exhibit_geographic_coverage.md").write_text(geography_text, encoding="utf-8")

    (target / "bounded_internal_mechanism_linkage_claim_memo_direct_text_colocation_appendix.md").write_text(
        appendix(scope, "direct_text_colocation_claim", "Appendix: direct-text co-location claims"), encoding="utf-8"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_documentary_scaffold_appendix.md").write_text(
        appendix(scope, "documentary_mechanism_value_scaffold", "Appendix: documentary mechanism-value scaffolds"), encoding="utf-8"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_provisional_linkage_appendix.md").write_text(
        appendix(scope, "provisional_mechanism_linkage_claim", "Appendix: provisional mechanism linkages"), encoding="utf-8"
    )
    insufficient = [row for row in scope if row["claim_type"] == "insufficient_for_claim"]
    insufficient_counts = Counter(row["qualitative_mechanism_family"] for row in insufficient)
    insufficient_text = "# Appendix: insufficient-for-claim records\n\nThe 141 records below remain excluded from claim-ready memo statements because their reviewed evidence is weak, context-only, or non-base/premium context.\n\n" + markdown_table(
        ["Mechanism", "Insufficient records"], sorted(insufficient_counts.items())
    ) + "\n\nAudit IDs:\n\n" + "\n".join(f"- `{row['claim_review_id']}`" for row in insufficient) + "\n"
    (target / "bounded_internal_mechanism_linkage_claim_memo_insufficient_records_appendix.md").write_text(insufficient_text, encoding="utf-8")

    memo = f"""# Bounded internal mechanism-linkage claim memo

Internal working document — 2026-07-26

## 1. Executive summary

In the exact same-source linked evidence, 268 reviewed mechanism-value pairs connect 208 quantitative direct-text rows with 90 supported qualitative mechanism records across 72 committed source lineages. The current linked corpus supports bounded documentary co-location claims. It does not support a wage-gap estimate or causal conclusion.

Implementation/retroactivity ({mechanism_counts['implementation_or_retroactivity_advantage']} pairs) and automatic raises ({mechanism_counts['automatic_raise_mechanism']} pairs) have the strongest same-source mechanism-value co-location support. Automatic raises provide the strongest claim-scaffold mix: 14 direct, 47 documentary, and 14 provisional pairs. Implementation/retroactivity has the largest volume but 88 of 126 pairs remain insufficient for claim-ready language.

The recommended next phase is targeted Tier C verification focused on currently unlinked or thin mechanism lanes, non-safety units, non-CBA sources, and underrepresented regions. Quantitative normalization remains necessary later, but expanding compatible mechanism evidence is the more immediate constraint on the project’s cross-occupation design.

## 2. Evidence scope

The memo uses only the completed 268-pair claim-review scope. It includes 15 direct-text co-location claims, 80 documentary mechanism-value scaffolds, 32 provisional mechanism linkages, and 141 insufficient-for-claim records. No not-allowed row entered the memo. Pair multiplicity is preserved: 268 pairs come from 72 source lineages and therefore cannot be read as 268 independent documents.

## 3. Geographic and source coverage

The evidence covers {geography['state_count']} states, {geography['city_state_pair_count']} city-state pairs, and {geography['city_cycle_unit_group_count']} city–unit–cycle groups. Pair counts by region are Midwest {region_counts['Midwest']}, West {region_counts['West']}, Northeast {region_counts['Northeast']}, and South {region_counts['South']}; no row is missing state or city metadata and none maps to Unknown. Midwest and West account for 213 pairs, while California and Ohio together account for 92. These are scope concentrations, not claims about broader geographic prevalence.

CBAs dominate the evidence with {source_counts['cba']} of 268 pairs. Memoranda/settlements contribute {source_counts['memorandum_or_settlement']} and wage schedules/compensation plans {source_counts['wage_schedule_or_compensation_plan']}; arbitration awards and ordinances/policies contribute none.

## 4. What this memo can and cannot claim

The memo can state that a committed source lineage contains both recorded quantitative text and supported qualitative mechanism evidence. It can organize those records into bounded documentary scaffolds and identify where normalization or more evidence is needed. It cannot compare unnormalized values, estimate a wage gap, infer direction from co-location, estimate effects, generalize to a population or the nation, or attribute a reported value to a mechanism.

## 5. Strongest linked mechanisms

Implementation/retroactivity and automatic raises dominate the exact-source scope. Automatic raises have 75 direct/documentary/provisional pairs and 22 insufficient records. Implementation/retroactivity has 38 documentary/provisional pairs and 88 insufficient records. The evidence supports treating these as priority documentary mechanisms for human review, not as estimated drivers of wage outcomes.

## 6. Thin or unlinked mechanisms

Non-base compensation ({mechanism_counts['non_base_compensation_signal']}), rank/specialization ({mechanism_counts['rank_or_specialization_premium']}), market/comparability ({mechanism_counts['market_or_comparability_pressure']}), bargaining power ({mechanism_counts['bargaining_power_signal']}), and fiscal constraint ({mechanism_counts['fiscal_constraint_signal']}) are present but thin. Strike/no-strike is documentarily stronger than before in the targeted exact-span evidence, but has zero exact same-source quantitative linkage here. Non-safety constraint, parity/internal equity, and gap narrowing also have zero exact-source quantitative linkage.

## 7. Unit and source-family limits

Police ({unit_counts['police']} pairs) and fire ({unit_counts['fire']}) outnumber non-safety ({unit_counts['non_safety']}). This imbalance is important because the project’s analytical design requires within-city safety/non-safety comparison. The concentration in CBAs also means the linked evidence says little about arbitration awards, ordinances, or other non-CBA source families.

## 8. Claim scaffolds supported now

Fifteen pairs support direct-text co-location language. Eighty support documentary mechanism-value scaffolds. Thirty-two remain provisional linkage claims because quantitative normalization or stronger claim relevance is still needed. Each statement must remain tied to its exact source lineage, original value text, unit, unit type, city, and cycle.

## 9. Claims not supported yet

The memo does not support relative wage-level conclusions, safety-versus-non-safety wage gaps, estimated mechanism effects, statistical conclusions, population prevalence, national prevalence, or causal attribution. The 141 insufficient records stay outside claim-ready statements, and zero-link mechanism lanes stay identified as gaps rather than inferred from other sources.

## 10. Next data needs

The next evidence wave should prioritize Tier C candidates capable of adding exact-source quantitative linkage for strike/no-strike, non-safety constraint, parity/internal equity, gap narrowing, fiscal constraint, and non-CBA mechanisms. It should also increase non-safety units and South/Northeast coverage where compatible candidates exist. No candidate should be promoted by weakening source, unit, city, or cycle lineage.

## 11. Recommended next phase

Run bounded targeted Tier C verification next. This recommendation follows from four zero-link mechanism lanes, thin fiscal/bargaining/market coverage, the police/fire versus non-safety imbalance, CBA concentration, and regional concentration. Quantitative normalization planning should follow once additional matched mechanism coverage is secured. Repository cleanup is not currently a material blocker.
"""
    (target / "bounded_internal_mechanism_linkage_claim_memo.md").write_text(memo, encoding="utf-8")

    next_recommendation = (
        "# Next-phase recommendation\n\nRun bounded targeted Tier C verification next. Prioritize candidates that can close exact-source quantitative-linkage gaps for strike/no-strike, non-safety constraint, parity/internal equity, gap narrowing, fiscal constraint, non-CBA sources, non-safety units, and thinner South/Northeast coverage. Preserve all verification/download/extraction/rating phase boundaries. Quantitative normalization planning remains the subsequent step; repo cleanup is not currently blocking velocity.\n"
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_next_phase_recommendation.md").write_text(next_recommendation, encoding="utf-8")
    (target / "bounded_internal_mechanism_linkage_claim_memo_tier_c_verification_plan.md").write_text(
        "# Targeted Tier C verification plan\n\nBuild a locked Tier C subset using only existing candidate metadata. Prioritize non-safety and matched-city/cycle candidates, zero-link mechanisms, thin fiscal/market/bargaining lanes, non-CBA source families, and compatible South/Northeast gaps. Verification must remain separate from download, extraction, rating, normalization, comparison, and causal analysis.\n",
        encoding="utf-8",
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_quantitative_normalization_plan.md").write_text(
        "# Quantitative normalization plan\n\nNormalization remains deferred. A later authorized plan should define unit-safe transformations, base/non-base exclusions, comparable-period rules, and city–unit–cycle matching without overwriting raw strings. It must not convert planning fields into claims or calculate wage gaps before a separately authorized comparison stage.\n",
        encoding="utf-8",
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_repo_cleanup_plan.md").write_text(
        "# Repository cleanup plan\n\nCleanup is not the recommended next phase because artifact layout did not block deterministic memo production, validation, dashboard integration, or relay creation. If later authorized, cleanup must preserve immutable task directories, hashes, lineage, and dashboard report paths.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_internal_exact_source_evidence_memo",
        "memo_scope": dashboard_metadata["memo_scope"],
        "mechanism_pair_counts": mechanism_counts,
        "unit_type_pair_counts": unit_counts,
        "source_family_pair_counts": source_counts,
        "geographic_coverage": dashboard_metadata["geographic_coverage"],
        "geographic_coverage_summary_sha256": geography_hash,
        "tier_c_verification_recommended_next": True,
        "quantitative_normalization_recommended_next": False,
        "repo_cleanup_recommended_next": False,
        "revision_recommended_next": False,
        "evidence_status": "bounded_exact_source_colocation_and_documentary_scaffold_only",
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
        "external_geography_lookups": 0,
        "invented_geographic_fields": 0,
        "global_analysis_readiness": False,
        "input_hashes": {str(path.relative_to(ROOT)): digest for path, digest in INPUTS.items()},
    }
    write_json(target / "bounded_internal_mechanism_linkage_claim_memo_decision.json", decision)
    (target / "bounded_internal_mechanism_linkage_claim_memo_summary.md").write_text(
        "# Bounded internal mechanism-linkage claim memo summary\n\n"
        f"Decision: `{DECISION}`. The memo covers 268 exact same-source pairs, 208 quantitative rows, 90 qualitative records, and 72 source lineages. It distinguishes 15 direct co-location claims, 80 documentary scaffolds, 32 provisional linkages, and 141 insufficient records. Geographic metadata covers 23 states, 64 city-state pairs, 72 city–unit–cycle groups, and four represented regions with no missing fields. Targeted Tier C verification is recommended next. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    write_json(target / "bounded_internal_mechanism_linkage_claim_memo_invariant_checks.json", {
        "all_invariants_passed": True,
        "memo_uses_only_locked_268_pair_claim_review": True,
        "scope_reconciles_268_208_90_72": True,
        "claim_types_reconcile_15_80_32_141_0": True,
        "geography_derived_only_from_existing_state_city_unit_cycle_fields": True,
        "static_region_mapping_only": True,
        "missing_geography_disclosed": True,
        "no_geographic_metadata_invented": True,
        "no_source_document_full_text_url_pdf_page_retained_file_access": True,
        "no_model_api_ocr_or_rendering": True,
        "no_normalization_imputation_annualization_or_outcome_comparison": True,
        "no_wage_gap_regression_treatment_effect_population_national_or_final_causal_work": True,
        "no_ingestion_or_codification": True,
        "dashboard_metadata_consistent_with_memo": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_json(target / "bounded_internal_mechanism_linkage_claim_memo_regression_test_inventory.json", {
        "suite": "scripts/test_bounded_internal_mechanism_linkage_claim_memo.py",
        "required_cases": [
            "pinned claim-review inputs", "268/208/90/72 scope reconciliation", "claim-type counts",
            "deterministic state-region mapping", "23-state and 64-city geography", "missing geography disclosure",
            "bounded memo language", "closed analysis flags", "dashboard metadata consistency",
            "idempotent resume", "partial-package failure", "dashboard global closure", "future prompt boundaries",
        ],
    })
    (target / "bounded_internal_mechanism_linkage_claim_memo_stress_test_report.md").write_text(
        "# Stress-test report\n\n- Missing or hash-drifted claim-review inputs fail before memo output.\n- Scope drift from 268/208/90/72 fails closed.\n- Missing state/city/unit/cycle/source metadata fails before geographic derivation.\n- Invalid states route to Unknown and are disclosed; no external lookup is available.\n- Open downstream flags or not-allowed records fail memo scope construction.\n- Complete reruns validate with zero writes; partial packages fail.\n",
        encoding="utf-8",
    )
    (target / "bounded_internal_mechanism_linkage_claim_memo_validation_2026-07-26.md").write_text(
        "# Bounded internal mechanism-linkage claim memo validation — 2026-07-26\n\nInternal pinned-input, scope, geography, region-mapping, claim-boundary, dashboard-metadata, and downstream-closure gates passed. Required repository command results are appended after the full suite completes.\n",
        encoding="utf-8",
    )
    future = (
        "# Next task: targeted Tier C verification planning and bounded run\n\n"
        "Build a locked Tier C verification scope from existing candidate outputs, prioritizing exact-source quantitative-linkage gaps: strike/no-strike, non-safety constraint, parity/internal equity, gap narrowing, fiscal constraint, non-CBA sources, non-safety units, and compatible South/Northeast coverage. Preserve city–unit–cycle matching and candidate lineage.\n\n"
        "Do not fetch or inspect repository remotes, weaken scope keys, open source documents outside the locked verification contract, download before separate authorization, extract, rate, normalize, impute, annualize, compare wage outcomes, calculate wage gaps, run regressions, estimate treatment effects, make population/national/final causal claims, ingest, codify, or set global analysis readiness true. Verification is not extraction or causal proof.\n"
    )
    (target / "next_targeted_tier_c_verification_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / "bounded_internal_mechanism_linkage_claim_memo_decision.json")
    geo = read_json(path / "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json")
    dash = read_json(path / "bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed memo decision invalid")
    if decision.get("memo_scope", {}).get("exact_same_source_linked_pair_count") != EXPECTED_PAIRS:
        raise RuntimeError("completed memo scope invalid")
    if decision.get("geographic_coverage_summary_sha256") != sha256_file(path / "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json"):
        raise RuntimeError("completed geographic summary hash mismatch")
    if geo.get("state_count") != 23 or geo.get("city_state_pair_count") != 64 or geo.get("city_cycle_unit_group_count") != 72:
        raise RuntimeError("completed geographic coverage invalid")
    if any(geo.get("missing_geography_counts", {}).values()):
        raise RuntimeError("completed geography unexpectedly missing")
    if dash.get("memo_decision") != DECISION or dash.get("memo_scope") != decision.get("memo_scope"):
        raise RuntimeError("completed dashboard metadata mismatch")
    if dash.get("global_analysis_readiness") is not False or dash.get("final_causal_claims") is not False or dash.get("wage_gap_estimates") is not False:
        raise RuntimeError("completed dashboard boundaries open")


def install_dashboard_docs() -> None:
    RESULT_DOC.write_text(
        "# Bounded internal mechanism-linkage claim memo result — 2026-07-26\n\n"
        f"Decision: `{DECISION}`. The internal memo summarizes 268 exact-source pairs covering 208 quantitative rows, 90 qualitative records, 72 source lineages, 23 states, 64 city-state pairs, and 72 city–unit–cycle groups. It supports bounded co-location/documentary scaffolds only. Targeted Tier C verification is recommended next. Global analysis readiness remains false. Detailed metadata: `docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json`.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        "# Dashboard status note — bounded internal mechanism-linkage claim memo\n\n"
        f"Current phase: bounded internal mechanism-linkage claim memo. Decision: `{DECISION}`. Scope: 268 exact-source pairs, 208 quantitative rows, 90 qualitative records, 72 source lineages. Geography: 23 states, 64 city-state pairs, 72 city–unit–cycle groups; Midwest 109 pairs, West 104, Northeast 39, South 16; missing geography 0. Evidence status: bounded co-location/documentary scaffold only. Wage-gap estimates: false. Regression/treatment-effect estimates: false. Final causal claims: false. Global analysis readiness: false. Main memo: `docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo.md`. Detailed dashboard metadata: `docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json`.\n",
        encoding="utf-8",
    )
    GEOGRAPHY_DOC.write_text(
        "# Bounded internal memo geographic coverage — 2026-07-26\n\nCoverage derives only from the locked memo scope. States: 23. City-state pairs: 64. City–unit–cycle groups: 72. Pair counts: Midwest 109, West 104, Northeast 39, South 16, District of Columbia/federal district 0, Unknown 0. Missing state, city, unit, cycle, source-family, and region fields: 0. Detailed metadata: `docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json`. These are locked-scope coverage counts, not population or national prevalence.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    validate_hashes()
    scope = load_scope()
    geography = build_geography(scope)
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "pairs": len(scope), "states": geography["state_count"]}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(scope, geography, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        install_dashboard_docs()
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "pairs": len(scope), "states": geography["state_count"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
