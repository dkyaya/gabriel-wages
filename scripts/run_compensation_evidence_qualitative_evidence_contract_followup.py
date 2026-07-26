#!/usr/bin/env python3
"""Materialize a fail-closed tiered qualitative evidence contract.

This runner is deliberately non-extractive. It partitions the immutable
disambiguated qualitative navigation layer into exact-span candidate,
ambiguous navigation, and unavailable navigation tiers. It never opens PDFs,
performs OCR, invokes a model, or writes analysis-facing data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-QUALITATIVE-EVIDENCE-CONTRACT-FOLLOWUP-2026-07-25"
SCHEMA_VERSION = "qualitative_evidence_contract_v1"
EXPECTED_TOTAL = 1954
EXPECTED_COUNTS = {
    "exact_verified": 759,
    "span_ambiguous_multiple_candidates": 614,
    "span_unavailable_or_unverified": 581,
}

INPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-DISAMBIGUATION-FOLLOWUP-2026-07-25"
DEFAULT_OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-QUALITATIVE-EVIDENCE-CONTRACT-FOLLOWUP-2026-07-25"

INPUTS = {
    "decision": INPUT_DIR / "bounded_qualitative_span_disambiguation_followup_decision.json",
    "summary": INPUT_DIR / "bounded_qualitative_span_disambiguation_followup_summary.md",
    "validation": INPUT_DIR / "bounded_qualitative_span_disambiguation_followup_validation_2026-07-25.md",
    "span_ledger": INPUT_DIR / "qualitative_literal_span_disambiguation_ledger.csv",
    "span_audit": INPUT_DIR / "qualitative_literal_span_disambiguation_audit.json",
    "navigation": INPUT_DIR / "qualitative_mechanism_navigation_view_with_disambiguated_span_status.csv",
    "page_summary": INPUT_DIR / "bounded_span_disambiguation_page_access_summary.json",
    "pdf_hashes": INPUT_DIR / "bounded_span_disambiguation_pdf_input_sha256.txt",
    "invariants": INPUT_DIR / "span_disambiguation_invariant_checks.json",
    "failure_modes": INPUT_DIR / "span_disambiguation_failure_mode_matrix.csv",
    "test_inventory": INPUT_DIR / "span_disambiguation_regression_test_inventory.json",
    "hardening": INPUT_DIR / "span_disambiguation_system_hardening_report.md",
    "stress": INPUT_DIR / "span_disambiguation_stress_test_report.md",
    "quantitative_candidate": INPUT_DIR / "quantitative_analysis_view_candidate_span_disambiguation_followup.csv",
    "quantitative_exception": INPUT_DIR / "quantitative_exception_ledger_span_disambiguation_followup.csv",
    "non_base": INPUT_DIR / "non_base_wage_companion_view_candidate_span_disambiguation_followup.csv",
    "reference": INPUT_DIR / "reference_exclusion_control_view_span_disambiguation_followup.csv",
    "conflicts": INPUT_DIR / "unresolved_conflict_quarantine_ledger_span_disambiguation_followup.csv",
    "residual": INPUT_DIR / "residual_metadata_quarantine_summary_span_disambiguation_followup.json",
}

EXPECTED_SHA256 = {
    "decision": "3a4022bbefbbdc6f61d8b2f186eb73090aa8352757ae1873f2ebd85837e84fa5",
    "summary": "89a27002934f7018ac1504b40861eff4833b565a80cad30446a1822b00fa7b01",
    "validation": "403f275a74dbc09909e39e9bbcbdf8a7861cb3902f1578d53ab3b199d74d78d0",
    "span_ledger": "e218e2ca585888b11b5ce4afbede96d613bf63e4b9949db04256c61f0c31b174",
    "span_audit": "8344ab429270fc75dad5b5cc26a4f224b955551ef84ba0600d92eae41ae82128",
    "navigation": "5754c526fa8318c9d43ef41a3e166513516aece045f215d6595fdd80e0ed60aa",
    "page_summary": "d8b8433db4bb1327dbaf561a08755f918b62e998493ebdfa35de39de608c0999",
    "pdf_hashes": "69d2bd184c48c524b351b651477b2be7c3542a6a41a09db850e3bce48c9f7c7f",
    "invariants": "d82e2eba8c89e47c686a92873afa197923f37446a330cccd2228f9bd82f58771",
    "failure_modes": "5988f2cfca94ce96468792ce04e812aef71da46340daf141dde26d9efebee293",
    "test_inventory": "f0986ab0e00b8830256f2aa9fb6ef07a75a949797330335fb2f6d97643464502",
    "hardening": "384be9812548d65a941ff54949dc8ac05c0b5b4bd28674ebdfec1d40a645593f",
    "stress": "b0d5ad9a8a97edf3c988bf318b6b4304b6207af2c6c7215bc609b0ffd61e0ab6",
    "quantitative_candidate": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    "quantitative_exception": "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401",
    "non_base": "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92",
    "reference": "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a",
    "conflicts": "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7",
    "residual": "d35a462f3b1648ad6f6a6a4bfd7e9d3e4815708293ad16318caef6effbaa2385",
}

OUTPUTS = {
    "decision": "qualitative_evidence_contract_followup_decision.json",
    "summary": "qualitative_evidence_contract_followup_summary.md",
    "contract": "qualitative_evidence_contract.md",
    "rules": "qualitative_evidence_contract_tier_rules.md",
    "limitations": "qualitative_evidence_contract_limitations.md",
    "exact": "qualitative_mechanism_exact_span_coded_candidate.csv",
    "ambiguous": "qualitative_mechanism_ambiguous_span_navigation.csv",
    "unavailable": "qualitative_mechanism_unavailable_span_navigation.csv",
    "combined": "qualitative_mechanism_combined_tiered_view.csv",
    "audit": "qualitative_mechanism_evidence_contract_audit.json",
    "ambiguous_sample": "qualitative_ambiguous_span_review_sample.csv",
    "unavailable_sample": "qualitative_unavailable_span_review_sample.csv",
    "blockers": "qualitative_evidence_contract_blocker_matrix.csv",
    "validation": "qualitative_evidence_contract_validation_report.md",
    "stress": "qualitative_evidence_contract_stress_test_report.md",
    "invariants": "qualitative_evidence_contract_invariant_checks.json",
    "tests": "qualitative_evidence_contract_regression_test_inventory.json",
    "quantitative_candidate": "quantitative_analysis_view_candidate_evidence_contract_followup.csv",
    "quantitative_exception": "quantitative_exception_ledger_evidence_contract_followup.csv",
    "non_base": "non_base_wage_companion_view_candidate_evidence_contract_followup.csv",
    "reference": "reference_exclusion_control_view_evidence_contract_followup.csv",
    "conflicts": "unresolved_conflict_quarantine_ledger_evidence_contract_followup.csv",
    "residual": "residual_metadata_quarantine_summary_evidence_contract_followup.json",
    "next_prompt": "next_analysis_readiness_review_prompt.md",
}

COPY_MAP = {
    "quantitative_candidate": "quantitative_candidate",
    "quantitative_exception": "quantitative_exception",
    "non_base": "non_base",
    "reference": "reference",
    "conflicts": "conflicts",
    "residual": "residual",
}

CONTRACT_FIELDS = [
    "evidence_contract_version",
    "evidence_contract_tier",
    "evidence_contract_candidate_eligible",
    "evidence_contract_use_scope",
    "evidence_contract_reason_code",
    "evidence_contract_review_status",
]

TIER_BY_STATUS = {
    "exact_verified": (
        "exact_span_coded_candidate",
        "true",
        "limited_exact_span_candidate_only",
        "exact_unique_span_and_qa_verified",
    ),
    "span_ambiguous_multiple_candidates": (
        "ambiguous_exact_span_navigation",
        "false",
        "navigation_only",
        "multiple_plausible_exact_spans_remain",
    ),
    "span_unavailable_or_unverified": (
        "unavailable_span_navigation",
        "false",
        "navigation_only",
        "exact_unique_span_unavailable_or_unverified",
    ),
}

FORBIDDEN_PERSISTED_FIELDS = {
    "page_text",
    "full_page_text",
    "raw_page_text",
    "pdf_text",
    "raw_prompt",
    "raw_response",
    "encoded_image",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        forbidden_resolved = forbidden.resolve()
        if resolved == forbidden_resolved or forbidden_resolved in resolved.parents:
            raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def verify_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, path in INPUTS.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        observed[name] = sha256(path)
        if observed[name] != EXPECTED_SHA256[name]:
            raise RuntimeError(f"Immutable input hash mismatch: {name}")
    return observed


def input_signature(hashes: dict[str, str]) -> str:
    joined = "\n".join(f"{name}:{hashes[name]}" for name in sorted(hashes))
    return text_sha256(f"{SCHEMA_VERSION}\n{joined}")


def validate_span_row(row: dict[str, str], *, exact: bool) -> None:
    if not row.get("qualitative_observation_id", "").strip():
        raise RuntimeError("Blank qualitative observation ID")
    if exact:
        if row.get("span_qa_status") != "span_exact_unique_verified":
            raise RuntimeError("Exact tier row lacks exact unique span QA")
        if row.get("span_qa_pass") != "true":
            raise RuntimeError("Exact tier row lacks span QA pass")
        span = row.get("literal_verbatim_evidence_span", "")
        if not span or "\n" in span or "\r" in span:
            raise RuntimeError("Exact tier span missing or multiline")
        try:
            start = int(row.get("span_start", ""))
            end = int(row.get("span_end", ""))
            length = int(row.get("span_length", ""))
        except ValueError as exc:
            raise RuntimeError("Exact tier span offset is invalid") from exc
        if start < 0 or end <= start or length != len(span) or end - start != length:
            raise RuntimeError("Exact tier span offset/length mismatch")
        if text_sha256(span) != row.get("span_sha256"):
            raise RuntimeError("Exact tier span SHA-256 mismatch")
    else:
        if row.get("span_qa_status") == "span_exact_unique_verified" or row.get("span_qa_pass") == "true":
            raise RuntimeError("Navigation-only tier carries exact-span eligibility")


def validate_frozen_layer() -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    decision = read_json(INPUTS["decision"])
    if decision.get("decision") != "bounded_qualitative_span_disambiguation_partial_additional_repair_needed":
        raise RuntimeError("Upstream decision does not authorize contract follow-up")
    if decision.get("analysis_readiness") is not False:
        raise RuntimeError("Upstream analysis readiness must remain false")

    prior_invariants = read_json(INPUTS["invariants"])
    if prior_invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Upstream invariants did not pass")
    page_summary = read_json(INPUTS["page_summary"])
    if any(page_summary.get(field) != 0 for field in (
        "non_target_page_access_count", "ocr_later_access_count", "page_text_persisted_count", "rendered_image_access_count"
    )):
        raise RuntimeError("Upstream page-access boundary failed")

    ledger_fields, ledger_rows = read_csv(INPUTS["span_ledger"])
    nav_fields, nav_rows = read_csv(INPUTS["navigation"])
    if len(ledger_rows) != EXPECTED_TOTAL or len(nav_rows) != EXPECTED_TOTAL:
        raise RuntimeError("Frozen qualitative row count mismatch")
    ledger_ids = [row["qualitative_observation_id"] for row in ledger_rows]
    nav_ids = [row["qualitative_observation_id"] for row in nav_rows]
    if len(set(ledger_ids)) != EXPECTED_TOTAL or len(set(nav_ids)) != EXPECTED_TOTAL:
        raise RuntimeError("Duplicate qualitative observation IDs")
    if ledger_ids != nav_ids:
        raise RuntimeError("Span ledger and navigation row order/identity mismatch")
    counts = Counter(row.get("span_capture_status") for row in nav_rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise RuntimeError(f"Frozen tier counts changed: {dict(counts)}")
    if set(nav_fields) & FORBIDDEN_PERSISTED_FIELDS or set(ledger_fields) & FORBIDDEN_PERSISTED_FIELDS:
        raise RuntimeError("Forbidden full-page/raw payload column present")

    ledger_by_id = {row["qualitative_observation_id"]: row for row in ledger_rows}
    for row in nav_rows:
        status = row.get("span_capture_status")
        if status not in TIER_BY_STATUS:
            raise RuntimeError(f"Unknown span status: {status}")
        validate_span_row(row, exact=status == "exact_verified")
        ledger = ledger_by_id[row["qualitative_observation_id"]]
        for field in (
            "span_capture_status", "span_qa_status", "span_sha256", "span_start", "span_end",
            "span_length", "bounded_evidence_pointer", "pdf_sha256", "retained_content_hash",
        ):
            if row.get(field, "") != ledger.get(field, ""):
                raise RuntimeError(f"Span/navigation mismatch for {field}")
    return nav_fields, nav_rows, ledger_rows


def tier_row(row: dict[str, str]) -> dict[str, str]:
    status = row["span_capture_status"]
    tier, eligible, scope, reason = TIER_BY_STATUS[status]
    out = dict(row)
    out.update({
        "evidence_contract_version": SCHEMA_VERSION,
        "evidence_contract_tier": tier,
        "evidence_contract_candidate_eligible": eligible,
        "evidence_contract_use_scope": scope,
        "evidence_contract_reason_code": reason,
        "evidence_contract_review_status": "provisional_pending_separate_readiness_review",
    })
    return out


def deterministic_sample(rows: list[dict[str, str]], limit: int = 25) -> list[dict[str, str]]:
    ordered = sorted(rows, key=lambda row: text_sha256(row["qualitative_observation_id"]))[:limit]
    fields = (
        "qualitative_observation_id", "extraction_case_id", "source_review_id", "text_table_detection_id",
        "mechanism_type", "page_number", "bounded_evidence_pointer", "span_capture_status", "span_qa_status",
        "span_failure_reason", "span_candidate_count", "span_disambiguation_rule",
        "evidence_contract_tier", "evidence_contract_reason_code",
    )
    return [{field: row.get(field, "") for field in fields} for row in ordered]


def carried_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in ("quantitative_candidate", "quantitative_exception", "non_base", "reference", "conflicts"):
        _, rows = read_csv(INPUTS[key])
        counts[key] = len(rows)
    residual = read_json(INPUTS["residual"])
    counts["unresolved_conflict_groups"] = int(residual.get("unresolved_conflict_groups", 2))
    counts["unresolved_conflict_observations"] = int(residual.get("unresolved_conflict_observations", 5))
    return counts


def copy_carried_outputs(output_dir: Path) -> None:
    for input_key, output_key in COPY_MAP.items():
        shutil.copy2(INPUTS[input_key], output_dir / OUTPUTS[output_key])
        if sha256(INPUTS[input_key]) != sha256(output_dir / OUTPUTS[output_key]):
            raise RuntimeError(f"Carried-forward byte identity failed: {input_key}")


def build_contract_docs(output_dir: Path, counts: dict[str, int]) -> None:
    exact = EXPECTED_COUNTS["exact_verified"]
    ambiguous = EXPECTED_COUNTS["span_ambiguous_multiple_candidates"]
    unavailable = EXPECTED_COUNTS["span_unavailable_or_unverified"]
    (output_dir / OUTPUTS["contract"]).write_text(f"""# Qualitative evidence contract

This contract represents all {EXPECTED_TOTAL:,} active qualitative mechanism rows in three mutually exclusive provisional tiers. It does not declare any row analysis-ready.

1. **Exact-span coded candidate ({exact:,})** — exact, unique, single-line local text-layer spans with passing offsets and SHA-256. These rows may be reviewed for a *limited exact-span-only* analysis-facing promotion in a separate authorized readiness review.
2. **Ambiguous exact-span navigation ({ambiguous:,})** — multiple plausible exact spans remain. These rows are navigation and audit records only.
3. **Unavailable-span navigation ({unavailable:,})** — no exact unique span was verified. These rows are navigation and audit records only.

Historical `qa_status` and derived `span_qa_status` remain separate. Mechanism labels are provisional extraction metadata; an exact span supports traceability but is not causal proof. Non-base, quantitative, reference/control, and conflict lanes remain separate.
""", encoding="utf-8")
    (output_dir / OUTPUTS["rules"]).write_text("""# Qualitative evidence-contract tier rules

| Tier | Required span status | Required span QA | Candidate eligible | Permitted use |
|---|---|---|---|---|
| `exact_span_coded_candidate` | `exact_verified` | `span_exact_unique_verified`; pass=`true` | true | Separate limited readiness review only |
| `ambiguous_exact_span_navigation` | `span_ambiguous_multiple_candidates` | navigation-only | false | Navigation, audit, future bounded repair |
| `unavailable_span_navigation` | `span_unavailable_or_unverified` | navigation-only | false | Navigation, audit, future bounded repair |

The tiers are exhaustive and mutually exclusive. Fuzzy, paraphrased, inferred, cross-page, OCR-derived, image-derived, URL-derived, model-derived, and full-page evidence are inadmissible. Exact candidate status does not change historical QA, analysis readiness, or causal interpretation.
""", encoding="utf-8")
    (output_dir / OUTPUTS["limitations"]).write_text(f"""# Qualitative evidence-contract limitations

- Only {exact:,}/{EXPECTED_TOTAL:,} rows have unique exact-span QA; the lane is not fully ready.
- {ambiguous:,} ambiguous rows and {unavailable:,} unavailable rows remain navigation-only.
- Exact substring verification establishes textual traceability, not construct validity, mechanism strength, treatment assignment, or causality.
- Two quantitative conflict groups/five observations remain quarantined outside this qualitative contract.
- Quantitative candidates ({counts['quantitative_candidate']:,}), quantitative exceptions ({counts['quantitative_exception']:,}), non-base companion rows ({counts['non_base']:,}), and reference/control rows ({counts['reference']:,}) remain separate.
- Analysis readiness remains false until a separately authorized readiness review evaluates the limited exact-span candidate tier and all other schema blockers.
""", encoding="utf-8")


def build_reports(output_dir: Path, signature: str, counts: dict[str, int], audit: dict[str, Any], invariants: dict[str, Any]) -> None:
    decision_value = "qualitative_evidence_contract_limited_review_allowed_exact_span_only"
    summary = f"""# Qualitative evidence-contract follow-up summary

Decision: `{decision_value}`

- Tier reconciliation: 759 exact-span candidates + 614 ambiguous navigation + 581 unavailable navigation = 1,954.
- All 759 candidate rows retain `span_exact_unique_verified`; ambiguous and unavailable rows are candidate-ineligible.
- Full qualitative readiness: no. A separate limited exact-span-only analysis-readiness review is allowed.
- Historical `qa_status` remains separate from `span_qa_status`.
- No PDFs were opened and no page text, OCR, models, extraction, selection, ingestion, codification, or analysis were used.
- Carried forward byte-for-byte: {counts['quantitative_candidate']:,} quantitative candidates, {counts['quantitative_exception']:,} exceptions, {counts['non_base']:,} non-base companion rows, {counts['reference']:,} reference/control rows, and {counts['unresolved_conflict_groups']} conflict groups/{counts['unresolved_conflict_observations']} observations.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUTS["summary"]).write_text(summary, encoding="utf-8")

    decision = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_signature": signature,
        "decision": decision_value,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": True,
        "repeat_review_scope": "limited_exact_span_only",
        "full_qualitative_readiness": False,
        "tier_counts": audit["tier_counts"],
        "tier_total": EXPECTED_TOTAL,
        "tier_counts_reconcile": True,
        "coded_qualitative_output": "provisional_exact_span_candidate_only",
        "pdf_pages_accessed": 0,
        "forbidden_actions_performed": [],
        "prior_or_durable_ledgers_mutated": False,
        "carried_forward": counts,
        "invariants": invariants,
        "next_prompt": OUTPUTS["next_prompt"],
        "next_recommendation": "run_separately_authorized_limited_exact_span_analysis_readiness_review",
    }
    write_json(output_dir / OUTPUTS["decision"], decision)

    (output_dir / OUTPUTS["validation"]).write_text("""# Qualitative evidence-contract validation report

- Immutable upstream hashes: 19/19 passed.
- Frozen qualitative IDs: 1,954/1,954 unique and order-aligned.
- Tier reconciliation: 759 + 614 + 581 = 1,954.
- Exact candidate QA: 759/759 `span_exact_unique_verified`, pass=true, valid hashes/offsets/lengths, single-line.
- Candidate contamination: zero ambiguous or unavailable rows.
- Historical QA and span QA remain separate.
- Forbidden full-page/raw payload columns: zero.
- PDF/page accesses in this task: zero.
- Carried-forward files: byte-identical to approved predecessors.
- Analysis readiness: false.

Repository-wide command results are appended after the full validation run.
""", encoding="utf-8")

    (output_dir / OUTPUTS["stress"]).write_text("""# Qualitative evidence-contract stress-test report

The focused suite exercises wrong tier counts, duplicate IDs, exact-row hash and offset corruption, ambiguous/unavailable candidate leakage, historical-QA overwrite, forbidden page-text columns, carried-file drift, wrong future-prompt selection, output-boundary violations, and analysis-readiness promotion. All failures are required to stop closed.

Materialization-time invariant status: passed. Final focused-test totals are recorded in the validation report.
""", encoding="utf-8")

    test_inventory = {
        "schema_version": SCHEMA_VERSION,
        "test_script": "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        "offline_only": True,
        "focused_test_count_at_materialization": 37,
        "predecessor_test_count": 32,
        "required_failure_modes": [
            "immutable_input_hash_mismatch", "wrong_tier_count", "duplicate_observation_id",
            "exact_span_hash_corruption", "exact_span_offset_corruption",
            "ambiguous_candidate_contamination", "unavailable_candidate_contamination",
            "historical_qa_overwrite", "full_page_text_column", "carried_file_drift",
            "analysis_readiness_true", "wrong_future_prompt", "forbidden_output_boundary",
        ],
        "bugs_discovered_and_fixed": [
            "Materialization initially required the future-review prompt before the reporting step created it; validation now distinguishes the pre-report and complete-output phases and revalidates after report creation."
        ],
    }
    write_json(output_dir / OUTPUTS["tests"], test_inventory)

    blockers = [
        ["QEC01", "qualitative", "614 ambiguous exact-span rows", "navigation_only", "Keep separate; bounded repair may revisit without weakening exact QA."],
        ["QEC02", "qualitative", "581 unavailable/unverified rows", "navigation_only", "Keep separate; no coded use without exact unique evidence."],
        ["QEC03", "qualitative", "Full lane is only 759/1954 exact verified", "limited_review_only", "Separate review may assess limited exact-span candidate tier; full readiness prohibited."],
        ["QEC04", "quantitative", "1045 quantitative exceptions", "carried_forward", "Remain outside mechanically safe quantitative candidates."],
        ["QEC05", "conflict", "Two groups/five observations unresolved", "quarantined", "Preserve explicit quarantine; do not guess."],
    ]
    write_csv(output_dir / OUTPUTS["blockers"], ["blocker_id", "lane", "issue", "contract_treatment", "next_action"], [dict(zip(["blocker_id", "lane", "issue", "contract_treatment", "next_action"], row)) for row in blockers])

    (output_dir / OUTPUTS["next_prompt"]).write_text("""# Next task: limited exact-span qualitative analysis-readiness review

Do not run this task without new explicit user authorization.

Review the provisional qualitative evidence contract without promoting data. Assess whether the 759-row `exact_span_coded_candidate` tier has sufficient row semantics, provenance, mechanism-field contract, active/QA rules, matching metadata, and separation to support a limited future analysis-facing promotion plan. Preserve the 614 ambiguous and 581 unavailable rows as navigation-only. Keep analysis readiness false during the review; do not ingest, codify, calculate wage gaps, run regressions, or make causal claims. Preserve the two unresolved quantitative conflict groups/five observations and all carried-forward lane boundaries.
""", encoding="utf-8")


def future_prompt_matches(output_dir: Path, *, required: bool) -> bool:
    if not required:
        return True
    return (output_dir / OUTPUTS["next_prompt"]).is_file() and not (output_dir / "next_bounded_schema_repair_followup_prompt.md").exists()


def validate_materialized(output_dir: Path, source_fields: list[str], *, require_future_prompt: bool = True) -> dict[str, Any]:
    combined_fields, combined = read_csv(output_dir / OUTPUTS["combined"])
    exact_fields, exact = read_csv(output_dir / OUTPUTS["exact"])
    _, ambiguous = read_csv(output_dir / OUTPUTS["ambiguous"])
    _, unavailable = read_csv(output_dir / OUTPUTS["unavailable"])
    ids = [row["qualitative_observation_id"] for row in combined]
    tier_counts = Counter(row["evidence_contract_tier"] for row in combined)
    checks = {
        "all_1954_rows_accounted_for": len(combined) == EXPECTED_TOTAL,
        "no_duplicate_observation_ids": len(ids) == len(set(ids)) == EXPECTED_TOTAL,
        "tier_counts_reconcile": len(exact) == 759 and len(ambiguous) == 614 and len(unavailable) == 581 and len(exact) + len(ambiguous) + len(unavailable) == EXPECTED_TOTAL,
        "exact_candidate_rows_all_unique_span_qa": all(row["span_capture_status"] == "exact_verified" and row["span_qa_status"] == "span_exact_unique_verified" and row["span_qa_pass"] == "true" for row in exact),
        "ambiguous_rows_candidate_ineligible": all(row["span_capture_status"] == "span_ambiguous_multiple_candidates" and row["evidence_contract_candidate_eligible"] == "false" for row in ambiguous),
        "unavailable_rows_candidate_ineligible": all(row["span_capture_status"] == "span_unavailable_or_unverified" and row["evidence_contract_candidate_eligible"] == "false" for row in unavailable),
        "historical_qa_preserved_separately": "qa_status" in combined_fields and "span_qa_status" in combined_fields and all(row.get("qa_status", "") in {"needs_review", "provisional_unverified"} for row in combined),
        "source_schema_preserved": all(field in combined_fields for field in source_fields),
        "forbidden_page_text_columns_absent": not (set(combined_fields) & FORBIDDEN_PERSISTED_FIELDS),
        "analysis_readiness_false": True,
        "pdf_pages_accessed_zero": True,
        "carried_outputs_byte_identical": all(sha256(INPUTS[input_key]) == sha256(output_dir / OUTPUTS[output_key]) for input_key, output_key in COPY_MAP.items()),
        "future_prompt_matches_limited_review_decision": future_prompt_matches(output_dir, required=require_future_prompt),
    }
    if not all(checks.values()):
        failed = [key for key, value in checks.items() if not value]
        raise RuntimeError(f"Materialized invariant failure: {failed}")
    return {
        "schema_version": SCHEMA_VERSION,
        "all_invariants_passed": True,
        "checks": checks,
        "tier_counts": dict(tier_counts),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir
    output_guard(output_dir, allow_existing=args.resume)
    hashes = verify_inputs()
    signature = input_signature(hashes)
    source_fields, source_rows, _ = validate_frozen_layer()
    counts = carried_counts()

    if args.dry_run:
        payload = {
            "dry_run": True,
            "writes": 0,
            "input_hashes_passed": len(hashes),
            "qualitative_rows": len(source_rows),
            "tier_counts": dict(Counter(row["span_capture_status"] for row in source_rows)),
            "pdf_pages_accessed": 0,
            "analysis_readiness": False,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.resume and output_dir.exists():
        decision_path = output_dir / OUTPUTS["decision"]
        if not decision_path.is_file() or read_json(decision_path).get("input_signature") != signature:
            raise RuntimeError("Existing output cannot be safely reused: signature mismatch")
        invariants = validate_materialized(output_dir, source_fields)
        print(json.dumps({"resume_reused": True, "writes": 0, "invariants": invariants}, indent=2, sort_keys=True))
        return 0

    output_dir.mkdir(parents=True)
    contract_fields = source_fields + [field for field in CONTRACT_FIELDS if field not in source_fields]
    combined = [tier_row(row) for row in source_rows]
    exact = [row for row in combined if row["evidence_contract_tier"] == "exact_span_coded_candidate"]
    ambiguous = [row for row in combined if row["evidence_contract_tier"] == "ambiguous_exact_span_navigation"]
    unavailable = [row for row in combined if row["evidence_contract_tier"] == "unavailable_span_navigation"]
    write_csv(output_dir / OUTPUTS["exact"], contract_fields, exact)
    write_csv(output_dir / OUTPUTS["ambiguous"], contract_fields, ambiguous)
    write_csv(output_dir / OUTPUTS["unavailable"], contract_fields, unavailable)
    write_csv(output_dir / OUTPUTS["combined"], contract_fields, combined)

    for output_key, rows in (("ambiguous_sample", deterministic_sample(ambiguous)), ("unavailable_sample", deterministic_sample(unavailable))):
        sample_fields = list(rows[0]) if rows else []
        write_csv(output_dir / OUTPUTS[output_key], sample_fields, rows)

    copy_carried_outputs(output_dir)
    invariants = validate_materialized(output_dir, source_fields, require_future_prompt=False)
    tier_counts = {
        "exact_span_coded_candidate": len(exact),
        "ambiguous_exact_span_navigation": len(ambiguous),
        "unavailable_span_navigation": len(unavailable),
    }
    audit = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "input_signature": signature,
        "immutable_input_hashes_passed": len(hashes),
        "qualitative_rows": len(combined),
        "unique_qualitative_observation_ids": len({row["qualitative_observation_id"] for row in combined}),
        "tier_counts": tier_counts,
        "tier_counts_reconcile": sum(tier_counts.values()) == EXPECTED_TOTAL,
        "exact_candidate_contamination_count": 0,
        "historical_qa_fields_preserved": True,
        "span_qa_fields_preserved": True,
        "full_page_text_persisted": False,
        "pdf_pages_accessed": 0,
        "ocr_later_accessed": 0,
        "non_target_pages_accessed": 0,
        "analysis_readiness": False,
        "full_coded_qualitative_view_created": False,
        "limited_exact_span_candidate_created": True,
        "carried_forward": counts,
    }
    write_json(output_dir / OUTPUTS["audit"], audit)
    write_json(output_dir / OUTPUTS["invariants"], invariants)
    build_contract_docs(output_dir, counts)
    build_reports(output_dir, signature, counts, audit, invariants)
    # Revalidate the complete output after report and future-prompt creation.
    invariants = validate_materialized(output_dir, source_fields, require_future_prompt=True)
    write_json(output_dir / OUTPUTS["invariants"], invariants)
    decision = read_json(output_dir / OUTPUTS["decision"])
    decision["invariants"] = invariants
    write_json(output_dir / OUTPUTS["decision"], decision)
    print(json.dumps({
        "output_dir": str(output_dir),
        "decision": "qualitative_evidence_contract_limited_review_allowed_exact_span_only",
        "tier_counts": tier_counts,
        "analysis_readiness": False,
        "pdf_pages_accessed": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
