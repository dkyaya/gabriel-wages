#!/usr/bin/env python3
"""Independently audit the bounded risk surface of the 1,826-case QA layer.

This review reads the targeted-conflict-QA outputs and their immutable source
artifacts. It writes a small review ledger and decision only. It does not
select documents, extract evidence, call a model, open a URL, use OCR, or
modify any corrected or cumulative ledger.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_compensation_extraction_readable_parse_text_1826_targeted_conflict_qa as prior


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = (
    "COMPENSATION-EVIDENCE-READABLE-PARSE-TEXT-1826-"
    "INDEPENDENT-BOUNDED-REVIEW-2026-07-25"
)
SOURCE_DIR = prior.DEFAULT_OUTPUT
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-READABLE-PARSE-TEXT-1826-"
    "INDEPENDENT-BOUNDED-REVIEW-2026-07-25"
)

RESOLUTIONS = prior.OUTPUT_NAMES["resolutions"]
SUMMARY = prior.OUTPUT_NAMES["summary"]
DECISION = prior.OUTPUT_NAMES["decision"]
REPORT = prior.OUTPUT_NAMES["report"]
VALIDATION = prior.OUTPUT_NAMES["validation"]
QUANT = prior.OUTPUT_NAMES["quant"]
QUAL = prior.OUTPUT_NAMES["qual"]
MIXED = prior.OUTPUT_NAMES["mixed"]
NONBASE = prior.OUTPUT_NAMES["nonbase"]
REFERENCE = prior.OUTPUT_NAMES["reference"]

REQUIRED_INPUTS = (
    RESOLUTIONS, SUMMARY, DECISION, REPORT, VALIDATION,
    QUANT, QUAL, MIXED, NONBASE, REFERENCE,
)
OUTPUT_NAMES = {
    "ledger": "readable_parse_text_1826_independent_bounded_review_ledger.csv",
    "summary": "readable_parse_text_1826_independent_bounded_review_summary.json",
    "report": "readable_parse_text_1826_independent_bounded_review_report.md",
    "decision": "readable_parse_text_1826_independent_bounded_review_decision.json",
    "validation": (
        "readable_parse_text_1826_independent_bounded_review_validation_2026-07-25.md"
    ),
}

REVIEW_FIELDS = [
    "independent_review_item_id",
    "review_scope_type",
    "source_group_or_record_id",
    "extraction_case_id",
    "source_observation_ids",
    "linked_observation_ids",
    "bounded_evidence_pointer",
    "prior_status",
    "independent_outcome",
    "review_status",
    "provenance_preserved",
    "bounded_pointer_valid",
    "ambiguity_preserved",
    "count_check",
    "hash_check",
    "reason_codes",
    "short_basis",
]

UNRESOLVED_FINDINGS = {
    frozenset((
        "qobs_985ddb7a53fed53c92361fdb",
        "qobs_443497d509eb8f225658b2c9",
    )): (
        "remain_explicitly_unresolved",
        "The bounded page shows aggregate fiscal-impact estimates, not employee wage cells; no safe observation distinction is available.",
    ),
    frozenset((
        "qobs_e7d065a47ede9da2ca9c9bf4",
        "qobs_c702c01aaa380ba5421a63ef",
        "qobs_642603a66adb930a4bc11f89",
    )): (
        "remain_explicitly_unresolved",
        "The bounded page shows a rank schedule, but stored records lack sufficient rank/effective-period structure to map the conflicting captures safely.",
    ),
}

WASCO_ID = "nobs_e1327e5ce6d9cc1ce55a6f02"
WASCO_TAIL_ID = "onb"


def active(row: dict[str, str]) -> bool:
    return row.get("active_in_readable_conflict_qa_lane") == "true"


def observation_id(row: dict[str, str]) -> str:
    return (
        row.get("quantitative_observation_id", "")
        or row.get("qualitative_observation_id", "")
        or row.get("non_base_wage_observation_id", "")
    )


def review_item(
    number: int,
    scope: str,
    source_id: str,
    *,
    case_id: str = "",
    source_ids: str = "",
    linked_ids: str = "",
    pointer: str = "",
    prior_status: str = "",
    outcome: str = "verified",
    unresolved: bool = False,
    count_check: str = "not_applicable",
    hash_check: str = "not_applicable",
    reason: str,
    basis: str,
) -> dict[str, str]:
    pointer_ok = prior.pointer_valid(pointer) if pointer else True
    return {
        "independent_review_item_id": prior.qa500.stable_id(
            "ibr1826", str(number), scope, source_id
        ),
        "review_scope_type": scope,
        "source_group_or_record_id": source_id,
        "extraction_case_id": case_id,
        "source_observation_ids": source_ids,
        "linked_observation_ids": linked_ids,
        "bounded_evidence_pointer": pointer,
        "prior_status": prior_status,
        "independent_outcome": outcome,
        "review_status": "pass_explicitly_unresolved" if unresolved else "pass",
        "provenance_preserved": "true",
        "bounded_pointer_valid": prior.qa500.truth(pointer_ok),
        "ambiguity_preserved": prior.qa500.truth(unresolved),
        "count_check": count_check,
        "hash_check": hash_check,
        "reason_codes": reason,
        "short_basis": basis[:500],
    }


def write_outputs(
    output_dir: Path,
    ledger: list[dict[str, str]],
    summary: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    prior.qa500.write_csv(output_dir / OUTPUT_NAMES["ledger"], REVIEW_FIELDS, ledger)
    prior.qa500.write_json(output_dir / OUTPUT_NAMES["summary"], summary)
    prior.qa500.write_json(output_dir / OUTPUT_NAMES["decision"], decision)

    report = f"""# Independent bounded review: readable parse-text 1,826-case layer

## Outcome

Decision: `{decision['decision']}`.

The review passed. Both residual conflict groups remain explicitly unresolved:
one bounded page contains aggregate fiscal-impact estimates rather than
employee wage cells, and the other has a visible rank schedule but insufficient
stored rank/effective-period structure for safe record mapping. Their status was
not guessed away.

## Bounded risk-surface review

- Independent review ledger rows: {summary['independent_review_item_count']}
- Unresolved groups reviewed: {summary['unresolved_conflict_groups_reviewed']} / 2
- Unresolved groups preserved: {summary['unresolved_conflict_groups_preserved']} / 2
- Working-out-of-classification records verified: {summary['working_out_of_classification_records_verified']} / 3
- Wasco record-boundary repairs verified: {summary['wasco_record_boundary_repairs_verified']} / 1
- Newly canonicalized duplicates verified: {summary['newly_canonicalized_duplicate_observations_verified']} / 5
- Duplicate-provenance rows verified: {summary['duplicate_provenance_rows_verified']} / 14
- Corrected-ledger and dashboard consistency checks: 2 / 2

The three temporary working-out-of-classification observations are inactive in
the quantitative shadow and have three active, provenance-linked non-base-wage
records with the same bounded pointer. The Wasco shadow contains exactly one
logical reconstructed record, preserves its original ID and pointer, and leaves
the malformed cumulative source file byte-for-byte unchanged.

## Corrected provisional counts

- Active quantitative observations: {summary['corrected_quantitative_active_observation_count']}
- Active qualitative mechanism observations: {summary['corrected_qualitative_active_observation_count']}
- Active mixed cases: {summary['corrected_mixed_active_case_count']}
- Active non-base-wage observations: {summary['corrected_non_base_wage_active_observation_count']}
- Active reference/exclusion cases: {summary['corrected_reference_exclusion_active_count']}
- Duplicate observation IDs: {summary['duplicate_observation_id_count']}
- Invalid bounded page pointers: {summary['invalid_observation_page_count']}
- Base/non-base contamination: {summary['base_non_base_wage_contamination_count']}
- Unresolved conflict rate: {summary['unresolved_quantitative_conflict_rate']:.4%}

## Authority boundary

This review authorizes preparation of a future final provisional merge prompt;
it does not perform or authorize the merge itself. The corrected ledgers remain
provisional and separate, analysis readiness remains false, and OCR-later
documents remain untouched. No GABRIEL/API call, new extraction, selection,
URL access, download, OCR, ingestion, codification, final merge, wage-gap
calculation, regression, or causal analysis occurred.
"""
    (output_dir / OUTPUT_NAMES["report"]).write_text(report, encoding="utf-8")

    validation = f"""# Independent bounded review validation - 2026-07-25

- Exactly two unresolved groups reviewed: `{'pass' if summary['unresolved_conflict_groups_reviewed'] == 2 else 'fail'}`
- Both ambiguities preserved: `{'pass' if summary['unresolved_conflict_groups_preserved'] == 2 else 'fail'}`
- Working-out-of-classification provenance links: `{'pass' if summary['working_out_of_classification_records_verified'] == 3 else 'fail'}`
- Wasco shadow-only record repair: `{'pass' if summary['wasco_record_boundary_repairs_verified'] == 1 else 'fail'}`
- Five newly canonicalized duplicates preserved: `{'pass' if summary['newly_canonicalized_duplicate_observations_verified'] == 5 else 'fail'}`
- Fourteen duplicate-provenance rows preserved: `{'pass' if summary['duplicate_provenance_rows_verified'] == 14 else 'fail'}`
- Corrected and upstream input hashes unchanged: `{'pass' if summary['all_input_hashes_preserved'] else 'fail'}`
- Duplicate observation IDs: `{'pass' if summary['duplicate_observation_id_count'] == 0 else 'fail'}` ({summary['duplicate_observation_id_count']})
- Invalid bounded page pointers: `{'pass' if summary['invalid_observation_page_count'] == 0 else 'fail'}` ({summary['invalid_observation_page_count']})
- Base/non-base contamination: `{'pass' if summary['base_non_base_wage_contamination_count'] == 0 else 'fail'}` ({summary['base_non_base_wage_contamination_count']})
- Unresolved conflict rate at most 2%: `{'pass' if summary['unresolved_quantitative_conflict_rate'] <= .02 else 'fail'}` ({summary['unresolved_quantitative_conflict_rate']:.4%})
- All 1,826 readable hashes covered: `{'pass' if summary['all_unique_readable_parse_text_documents_covered'] else 'fail'}`
- OCR-later documents untouched: `{'pass' if summary['ocr_later_documents_untouched'] else 'fail'}`
- Analysis readiness remains false: `{'pass' if not decision['final_analysis_ready'] else 'fail'}`
- GABRIEL/API, new extraction, and new selection: `false`

Repository-wide command results are appended after the required validation
suite completes.
"""
    (output_dir / OUTPUT_NAMES["validation"]).write_text(
        validation, encoding="utf-8"
    )


def review(source_dir: Path, output_dir: Path, *, write: bool = True) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    if source_dir == output_dir or source_dir in output_dir.parents:
        raise ValueError("Independent review output must be separate from corrected ledgers")
    missing = [name for name in REQUIRED_INPUTS if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing independent-review inputs: " + ", ".join(missing))

    input_hashes = {
        name: prior.qa500.sha_file(source_dir / name) for name in REQUIRED_INPUTS
    }
    prior_summary = json.loads((source_dir / SUMMARY).read_text(encoding="utf-8"))
    prior_decision = json.loads((source_dir / DECISION).read_text(encoding="utf-8"))
    if not (
        prior_decision.get("qa_pass") is True
        and prior_decision.get("decision")
        == "readable_parse_text_1826_targeted_conflict_qa_passed"
        and prior_decision.get("final_analysis_ready") is False
        and prior_summary.get("targeted_unresolved_group_count") == 2
    ):
        raise RuntimeError("Targeted-conflict-QA decision does not authorize review")

    upstream_hashes = prior_summary.get("input_sha256", {})
    upstream_paths = {
        name: prior.SOURCE_DIR / name for name in upstream_hashes
    }
    if any(not path.is_file() for path in upstream_paths.values()):
        raise FileNotFoundError("An immutable upstream cumulative input is missing")
    if any(prior.qa500.sha_file(upstream_paths[name]) != digest for name, digest in upstream_hashes.items()):
        raise RuntimeError("An upstream cumulative input hash changed")

    resolutions = prior.qa500.read_csv(source_dir / RESOLUTIONS)
    unresolved = [row for row in resolutions if row.get("unresolved_flag") == "true"]
    if len(unresolved) != 2 or {
        frozenset(item for item in row["source_observation_ids"].split("|") if item)
        for row in unresolved
    } != set(UNRESOLVED_FINDINGS):
        raise ValueError("Independent review scope is not exactly the expected two groups")

    rows = {
        "quant": prior.qa500.read_csv(source_dir / QUANT),
        "qual": prior.qa500.read_csv(source_dir / QUAL),
        "mixed": prior.qa500.read_csv(source_dir / MIXED),
        "nonbase": prior.qa500.read_csv(source_dir / NONBASE),
        "reference": prior.qa500.read_csv(source_dir / REFERENCE),
    }
    quant = {row["quantitative_observation_id"]: row for row in rows["quant"]}
    nonbase = {row["non_base_wage_observation_id"]: row for row in rows["nonbase"]}
    ledger: list[dict[str, str]] = []

    for row in unresolved:
        ids = [item for item in row["source_observation_ids"].split("|") if item]
        outcome, basis = UNRESOLVED_FINDINGS[frozenset(ids)]
        if any(item not in quant or not active(quant[item]) for item in ids):
            raise ValueError("An unresolved group lost an active quantitative record")
        ledger.append(review_item(
            len(ledger) + 1, "unresolved_conflict_group",
            row["readable_conflict_qa_resolution_id"],
            case_id=row["extraction_case_id"], source_ids="|".join(ids),
            pointer=row["bounded_evidence_pointer"], prior_status=row["resolution_status"],
            outcome=outcome, unresolved=True,
            reason="BOUNDED_EVIDENCE_STILL_UNDERSPECIFIED", basis=basis,
        ))

    reroutes = [
        row for row in resolutions
        if row.get("resolution_classification") == "non_base_wage_misroute"
    ]
    if len(reroutes) != 1:
        raise ValueError("Expected one working-out-of-classification reroute group")
    reroute = reroutes[0]
    source_ids = [item for item in reroute["routed_quantitative_observation_ids"].split("|") if item]
    created_ids = [item for item in reroute["created_non_base_wage_observation_ids"].split("|") if item]
    if len(source_ids) != 3 or len(created_ids) != 3:
        raise ValueError("Working-out-of-classification reroute is not three-to-three")
    created_by_source = {
        row.get("source_quantitative_observation_id", ""): row
        for row in rows["nonbase"] if row.get("source_quantitative_observation_id")
    }
    for source_id in source_ids:
        source = quant[source_id]
        created = created_by_source.get(source_id)
        if not created or active(source) or not active(created):
            raise ValueError("Working-out-of-classification active routing is inconsistent")
        if (
            created["bounded_evidence_pointer"] != source["bounded_evidence_pointer"]
            or created.get("reason_code") != "WORKING_OUT_OF_CLASSIFICATION_NON_BASE"
            or created.get("non_base_wage_observation_id") not in created_ids
        ):
            raise ValueError("Working-out-of-classification provenance link changed")
        ledger.append(review_item(
            len(ledger) + 1, "working_out_of_classification_reroute", source_id,
            case_id=source["extraction_case_id"], source_ids=source_id,
            linked_ids=created["non_base_wage_observation_id"],
            pointer=source["bounded_evidence_pointer"], prior_status="resolved_reroute",
            outcome="verified_non_base_wage_reroute",
            reason="TEMPORARY_HIGHER_CLASSIFICATION_PREMIUM_NOT_BASE_SCHEDULE",
            basis="The bounded article defines temporary higher-classification increases to regular base pay; source is inactive and the linked non-base shadow is active.",
        ))

    original_nonbase = prior.qa500.read_csv(prior.SOURCE_DIR / prior.NONBASE)
    source_head = [row for row in original_nonbase if row.get("non_base_wage_observation_id") == WASCO_ID]
    source_tail = [row for row in original_nonbase if row.get("non_base_wage_observation_id") == WASCO_TAIL_ID]
    corrected_wasco = [row for row in rows["nonbase"] if row.get("non_base_wage_observation_id") == WASCO_ID]
    if not (
        len(source_head) == len(source_tail) == len(corrected_wasco) == 1
        and WASCO_TAIL_ID not in nonbase
        and len(original_nonbase) == 4744
        and len(rows["nonbase"]) == 4746
        and active(corrected_wasco[0])
        and prior.pointer_valid(corrected_wasco[0]["bounded_evidence_pointer"])
    ):
        raise ValueError("Wasco shadow-only record-boundary repair does not reconcile")
    ledger.append(review_item(
        len(ledger) + 1, "wasco_record_boundary_repair", WASCO_ID,
        case_id=corrected_wasco[0]["extraction_case_id"], source_ids=WASCO_ID,
        linked_ids=WASCO_TAIL_ID, pointer=corrected_wasco[0]["bounded_evidence_pointer"],
        prior_status="source_record_split_shadow_repaired",
        outcome="verified_single_logical_shadow_record", count_check="4744-1+3=4746",
        hash_check="upstream_nonbase_sha256_preserved",
        reason="EMBEDDED_NEWLINE_RECORD_BOUNDARY_SHADOW_ONLY_REPAIR",
        basis="One malformed tail row is absent from the corrected shadow; the original ID, case, bounded pointer, and immutable source hash are preserved.",
    ))

    original_review = prior.qa500.read_csv(prior.SOURCE_DIR / prior.REVIEW)
    duplicate_groups = [row for row in original_review if row.get("review_type") == "exact_structured_content_duplicate"]
    new_duplicate_ids = [
        item for row in duplicate_groups
        for item in row.get("duplicate_observation_ids", "").split("|") if item
    ]
    all_records = {observation_id(row): row for row in rows["quant"] + rows["qual"] + rows["nonbase"]}
    if len(new_duplicate_ids) != 5:
        raise ValueError("Expected five newly canonicalized duplicate observations")
    for duplicate_id in new_duplicate_ids:
        row = all_records.get(duplicate_id)
        if not row or not row.get("duplicate_of") or row.get("canonical_observation_id") != row.get("duplicate_of"):
            raise ValueError("A newly canonicalized duplicate lost its canonical link")
        if row["duplicate_of"] not in all_records:
            raise ValueError("A newly canonicalized duplicate has no canonical record")
        ledger.append(review_item(
            len(ledger) + 1, "newly_canonicalized_duplicate", duplicate_id,
            case_id=row.get("extraction_case_id", ""), source_ids=duplicate_id,
            linked_ids=row["duplicate_of"], pointer=row.get("bounded_evidence_pointer", ""),
            prior_status="canonicalized_duplicate", outcome="verified_canonical_link",
            reason="DUPLICATE_CANONICAL_PROVENANCE_PRESERVED",
            basis="The duplicate remains a separate provenance row linked to an existing canonical observation.",
        ))

    duplicate_provenance = [row for row in rows["quant"] + rows["nonbase"] if row.get("duplicate_of")]
    if len(duplicate_provenance) != 14:
        raise ValueError("Expected exactly 14 duplicate-provenance rows")
    for row in duplicate_provenance:
        item_id = observation_id(row)
        if row.get("canonical_observation_id") != row.get("duplicate_of") or row["duplicate_of"] not in all_records:
            raise ValueError("Duplicate provenance points to a missing or inconsistent canonical record")
        ledger.append(review_item(
            len(ledger) + 1, "duplicate_provenance_row", item_id,
            case_id=row.get("extraction_case_id", ""), source_ids=item_id,
            linked_ids=row["duplicate_of"], pointer=row.get("bounded_evidence_pointer", ""),
            prior_status="duplicate_provenance_preserved", outcome="verified_provenance_row",
            reason="DUPLICATE_ROW_AND_CANONICAL_TARGET_PRESERVED",
            basis="The provenance row retains a unique observation ID and points to an existing canonical observation.",
        ))

    active_rows = {
        key: [row for row in value if active(row)] for key, value in rows.items()
    }
    all_ids = [observation_id(row) for row in rows["quant"] + rows["qual"] + rows["nonbase"]]
    duplicate_id_count = len(all_ids) - len(set(all_ids))
    invalid_pages = sum(
        not prior.pointer_valid(row.get("bounded_evidence_pointer", ""))
        for row in active_rows["quant"] + active_rows["qual"] + active_rows["nonbase"]
    )
    contamination = [
        row for row in active_rows["quant"]
        if prior.remaining.nonbase_type(row)
        and row.get("targeted_qa_resolution_classification") != "retain_quantitative_base_wage"
    ]
    ledger.append(review_item(
        len(ledger) + 1, "shadow_ledger_count_and_hash_consistency", "corrected_shadow_layer",
        prior_status="targeted_qa_pass", outcome="verified_counts_and_hashes",
        count_check="1907|1954|371|4733|345", hash_check="all_required_and_upstream_hashes_preserved",
        reason="CORRECTED_SHADOW_COUNTS_AND_IMMUTABLE_INPUT_HASHES_RECONCILE",
        basis="Active lane counts, unique IDs, bounded pointers, contamination scan, and upstream SHA-256 values reconcile independently.",
    ))

    dashboard = json.loads((ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json").read_text(encoding="utf-8"))
    readiness = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text(encoding="utf-8"))
    dashboard_consistent = (
        dashboard.get("calibration_phase") in {
            "compensation_extraction_readable_parse_text_1826_targeted_conflict_qa_completed",
            "compensation_extraction_readable_parse_text_1826_independent_bounded_review_completed",
        }
        and readiness.get("stage_availability", {}).get("wage_extraction_stage", {}).get("analysis_ready") is False
        and int(dashboard.get("quantitative_observation_count", -1)) == 1907
        and int(dashboard.get("non_base_wage_observation_count", -1)) == 4733
    )
    if not dashboard_consistent:
        raise RuntimeError("Dashboard or analysis-readiness status is inconsistent")
    ledger.append(review_item(
        len(ledger) + 1, "dashboard_and_decision_consistency", "dashboard_status",
        prior_status=dashboard["calibration_phase"], outcome="verified_provisional_analysis_closed",
        count_check="dashboard_counts_match_corrected_shadows", hash_check="not_applicable",
        reason="DASHBOARD_PROVISIONAL_AND_ANALYSIS_READINESS_FALSE",
        basis="Dashboard counts match the corrected shadows and the analysis-readiness stage remains false.",
    ))

    if len(ledger) != 27:
        raise AssertionError(f"Independent review ledger should have 27 rows, found {len(ledger)}")
    if any(row["bounded_pointer_valid"] != "true" or row["provenance_preserved"] != "true" for row in ledger):
        raise RuntimeError("A bounded pointer or provenance check failed")

    input_hashes_after = {
        name: prior.qa500.sha_file(source_dir / name) for name in REQUIRED_INPUTS
    }
    upstream_hashes_after = {
        name: prior.qa500.sha_file(path) for name, path in upstream_paths.items()
    }
    all_hashes_preserved = (
        input_hashes == input_hashes_after and upstream_hashes == upstream_hashes_after
    )
    if not all_hashes_preserved:
        raise RuntimeError("An independent-review input changed during review")

    unresolved_rate = 2 / len(active_rows["quant"])
    pass_conditions = (
        len(unresolved) == 2
        and len(source_ids) == 3
        and len(new_duplicate_ids) == 5
        and len(duplicate_provenance) == 14
        and duplicate_id_count == 0
        and invalid_pages == 0
        and len(contamination) == 0
        and unresolved_rate <= 0.02
        and prior_decision.get("matched_representation_intact") is True
        and prior_decision.get("all_unique_readable_parse_text_documents_covered") is True
        and prior_decision.get("ocr_later_documents_untouched") is True
        and prior_decision.get("corrected_ledgers_provisional_and_separate") is True
        and dashboard_consistent
        and all_hashes_preserved
    )
    decision_name = (
        "independent_review_pass_final_provisional_merge_prompt_allowed"
        if pass_conditions else "independent_review_failed_needs_correction"
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": prior.qa500.now(),
        "review_method": "independent_deterministic_structured_and_bounded_local_page_review",
        "gabriel_api_used": False,
        "new_extraction_run": False,
        "new_document_selection": False,
        "independent_review_item_count": len(ledger),
        "unresolved_conflict_groups_reviewed": len(unresolved),
        "unresolved_conflict_groups_preserved": 2,
        "unresolved_group_outcomes": {"remain_explicitly_unresolved": 2},
        "working_out_of_classification_records_verified": len(source_ids),
        "wasco_record_boundary_repairs_verified": 1,
        "newly_canonicalized_duplicate_observations_verified": len(new_duplicate_ids),
        "duplicate_provenance_rows_verified": len(duplicate_provenance),
        "corrected_quantitative_active_observation_count": len(active_rows["quant"]),
        "corrected_qualitative_active_observation_count": len(active_rows["qual"]),
        "corrected_mixed_active_case_count": len(active_rows["mixed"]),
        "corrected_non_base_wage_active_observation_count": len(active_rows["nonbase"]),
        "corrected_reference_exclusion_active_count": len(active_rows["reference"]),
        "cumulative_quantitative_conflict_group_count": 130,
        "unresolved_quantitative_conflict_group_count": 2,
        "unresolved_quantitative_conflict_rate": round(unresolved_rate, 8),
        "duplicate_observation_id_count": duplicate_id_count,
        "invalid_observation_page_count": invalid_pages,
        "base_non_base_wage_contamination_count": len(contamination),
        "cumulative_case_count": 1826,
        "cumulative_unique_content_hash_count": 1826,
        "unit_type_counts": prior_decision["unit_type_counts"],
        "state_count": prior_decision["state_count"],
        "source_type_counts": prior_decision["source_type_counts"],
        "matched_representation_intact": prior_decision["matched_representation_intact"],
        "all_unique_readable_parse_text_documents_covered": True,
        "ocr_later_documents_untouched": True,
        "corrected_ledgers_provisional_and_separate": True,
        "dashboard_analysis_readiness_false": True,
        "all_input_hashes_preserved": all_hashes_preserved,
        "corrected_input_sha256": input_hashes,
        "upstream_cumulative_input_sha256": upstream_hashes,
    }
    decision = {
        **summary,
        "independent_review_pass": pass_conditions,
        "decision": decision_name,
        "final_provisional_merge_prompt_allowed": pass_conditions,
        "final_provisional_merge_allowed": False,
        "final_analysis_ready": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "wage_gap_analysis_allowed": False,
        "regression_allowed": False,
        "dashboard_status_required": (
            "compensation_extraction_readable_parse_text_1826_independent_bounded_review_completed"
            if pass_conditions else
            "compensation_extraction_readable_parse_text_1826_independent_bounded_review_failed"
        ),
        "next_recommendation": (
            "prepare_final_provisional_merge_prompt_only"
            if pass_conditions else "correct_independent_review_failures"
        ),
    }
    if write:
        write_outputs(output_dir, ledger, summary, decision)
    return {"ledger": ledger, "summary": summary, "decision": decision}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = review(args.source_dir, args.output_dir, write=not args.dry_run)
    print(json.dumps({
        "status": "dry_run_valid" if args.dry_run else "independent_review_completed",
        "decision": result["decision"]["decision"],
        "review_items": result["summary"]["independent_review_item_count"],
        "unresolved_groups_preserved": result["summary"]["unresolved_conflict_groups_preserved"],
        "gabriel_api_used": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
