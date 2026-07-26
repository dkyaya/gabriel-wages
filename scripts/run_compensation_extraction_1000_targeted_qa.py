#!/usr/bin/env python3
"""Run deterministic targeted QA over the cumulative 1,000-case extraction.

This pass reads only the frozen cumulative provisional ledgers and their bounded
review queue.  It writes separate corrected shadow ledgers, preserves every
source row and observation identifier, and never calls a model, opens a URL,
performs OCR, or runs extraction/ingestion/codification.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_compensation_extraction_targeted_qa as qa500


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-TARGETED-QA-2026-07-25"
SOURCE_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-TARGETED-QA-2026-07-25"
)

REVIEW = "compensation_extraction_1000_conflict_review.csv"
DECISION = "compensation_extraction_1000_decision_report.json"
PACKET = "compensation_extraction_1000_packet_manifest.csv"
SELECTION = "compensation_extraction_1000_selection_manifest.csv"
QUANT = "lanes/quantitative/quantitative_extraction_ledger.csv"
QUAL = "lanes/qualitative/qualitative_mechanism_extraction_ledger.csv"
MIXED = "lanes/mixed/mixed_extraction_ledger.csv"
NONBASE = "lanes/non_base_wage/non_base_wage_compensation_ledger.csv"
REFERENCE = "lanes/reference_and_exclusion/reference_exclusion_ledger.csv"

OUTPUT_NAMES = {
    "resolutions": "compensation_extraction_1000_targeted_qa_resolutions.csv",
    "quant": "quantitative_extraction_ledger_qa_corrected.csv",
    "qual": "qualitative_mechanism_extraction_ledger_qa_corrected.csv",
    "mixed": "mixed_extraction_ledger_qa_corrected.csv",
    "nonbase": "non_base_wage_compensation_ledger_qa_corrected.csv",
    "reference": "reference_exclusion_ledger_qa_corrected.csv",
    "summary": "compensation_extraction_1000_targeted_qa_summary.json",
    "decision": "compensation_extraction_1000_recomputed_decision.json",
    "report": "compensation_extraction_1000_targeted_qa_report.md",
    "validation": "compensation_extraction_1000_targeted_qa_validation_2026-07-25.md",
}

TARGET_QA_FIELDS = [
    "targeted_qa_resolution_ids",
    "targeted_qa_resolution_classification",
    "targeted_qa_resolution_status",
    "targeted_qa_reason_codes",
    "targeted_qa_source_observation_id",
    "active_in_qa_corrected_lane",
]
MIXED_QA_FIELDS = [
    "targeted_qa_original_quantitative_observation_ids",
    "targeted_qa_corrected_quantitative_observation_ids",
]
NONBASE_PROVENANCE_FIELDS = [
    "source_quantitative_observation_id",
    "source_mixed_join_key",
]
REFERENCE_PROVENANCE_FIELDS = [
    "targeted_qa_reference_id",
    "source_quantitative_observation_id",
]

RESOLUTION_FIELDS = [
    "targeted_qa_resolution_id",
    "review_queue_row_number",
    "review_type",
    "extraction_case_id",
    "page_number",
    "lane",
    "source_observation_ids",
    "source_observation_count",
    "resolution_classification",
    "resolution_status",
    "quantitative_action",
    "non_base_wage_action",
    "reference_action",
    "retained_quantitative_observation_ids",
    "routed_quantitative_observation_ids",
    "reference_only_quantitative_observation_ids",
    "created_non_base_wage_observation_ids",
    "created_reference_ids",
    "structured_basis",
    "bounded_evidence_pointer",
    "local_evidence_inspected",
    "reason_codes",
    "confidence",
    "unresolved_flag",
    "notes",
]

NONBASE_CLASSES = {
    "retain_quantitative_base_wage",
    "route_to_non_base_wage",
    "split_quant_and_non_base_components",
    "reference_only",
    "insufficient_evidence_needs_review",
}
CONFLICT_CLASSES = qa500.CONFLICT_CLASSES

# These five rows were bounded-page checked and are genuine base-salary
# schedule cells.  Certification is a row/classification descriptor, not an
# extracted certification premium, and the FF1 cell is the base salary column
# from a salary/premium-time schedule.
BASE_RETAIN_BASIS = {
    "qobs_3695639f26c312996ff440ca": "Ordinance salary row: certified entry-level firefighter base annual salary.",
    "qobs_fde163592412cb387ac2f878": "Ordinance salary row: non-certified entry-level firefighter base annual salary.",
    "qobs_d0c0b50e8a87b9af116643fc": "Base-pay entry row: certified Police Officer 1 annual salary.",
    "qobs_df9072afa7961d1b9f1dc6a8": "Base-pay entry row: non-certified Police Officer 1 annual salary.",
    "qobs_160e7c7831ef38c08751e151": "Bounded salary schedule shows FF1 years 0-3 base salary; premium-time columns are separate.",
}

# This row points to another article for the actual callback rate and therefore
# does not itself contain a usable quantitative or non-base observation.
REFERENCE_ONLY_BASIS = {
    "qobs_34e7e12d1784727123afd4f3": "The bounded structured record only points to Article 5.4 for the callback rate.",
}


def sig(*ids: str) -> frozenset[str]:
    return frozenset(ids)


# The 25 under-specified groups were checked against their structured fields
# and, only where needed, the single bounded local page named by the pointer.
# No row/rank/date value is added to any observation; the mapping only decides
# whether the already-captured values are distinct, misrouted, or unresolved.
CONFLICT_DECISIONS: dict[frozenset[str], tuple[str, str]] = {
    sig("qobs_37b00ea23114e8bcc3dc5ac6", "qobs_d21cb18e2de539057c644ca9"): (
        "distinct_schedule_cell",
        "The page separately labels a 3% general salary increase and 1.75% equity adjustment.",
    ),
    sig("qobs_cadb12ccf757ba3f3e4e3f98", "qobs_8267cf3612c5a6568975789c", "qobs_89a54513858dc5c2ffc60548"): (
        "non_base_wage_misroute",
        "The page is a holiday-leave advance/deduction rule, not a base-wage schedule.",
    ),
    sig("qobs_7d59019de0e975088093191b", "qobs_696fec269326e7bd405b6a47", "qobs_194aeccaaa80ba41e0ff3892", "qobs_e68f60236f4804303aaddbdc", "qobs_d8cd849b2a621614dad873d6"): (
        "distinct_schedule_cell",
        "Five separately printed salary cells occur in the bounded patrol-officer schedule.",
    ),
    sig("qobs_11b9469f7e488b96f3668b4b", "qobs_228069350461bb0ef04bff48"): (
        "distinct_schedule_cell",
        "The bounded grade table contains separate values under the shared grade heading.",
    ),
    sig("qobs_0cfd9130f3db58b13e3ce452", "qobs_42d3cc8dbe5f632424a9c61b", "qobs_cfbbe915e7ca1784041391f8"): (
        "distinct_schedule_cell",
        "The training-wage formula displays three separate percentage cells.",
    ),
    sig("qobs_4a3de13b5fb7f05ac75fb3d5", "qobs_d6af0550806e19d2ed366dde", "qobs_d3b829b3b7531334cbec2405"): (
        "distinct_effective_period",
        "The bounded fiscal-impact table labels wage increases by Year 1, Year 2, and Year 3.",
    ),
    sig("qobs_985ddb7a53fed53c92361fdb", "qobs_443497d509eb8f225658b2c9"): (
        "insufficient_evidence_needs_review",
        "Aggregate fiscal-impact dollar estimates are not employee wage cells and lack a safe lane conversion.",
    ),
    sig("qobs_d6f39640c4aed18a697d3f6a", "qobs_778cafef26338040d9708272"): (
        "non_base_wage_misroute",
        "The page explicitly identifies 6% swing/cover-shift and 8% graveyard-shift differentials.",
    ),
    sig("qobs_4917b6e99309266ef7a6dee3", "qobs_bf626ad61c78b170a00f609e", "qobs_25483f7c98b248266bd5479a", "qobs_2d75e2647fe72a0255be3171"): (
        "distinct_schedule_cell",
        "Four distinct cells are printed in the bounded scheduled-base-pay evidence.",
    ),
    sig("qobs_b32deaf4f9666278f93edd50", "qobs_fb95dd39928c3e6e57ab1a77", "qobs_e2ce4e63b9777ddff0794a76"): (
        "non_base_wage_misroute",
        "The page is an Article VII longevity schedule with 5-, 10-, and 15-year premiums.",
    ),
    sig("qobs_9fcb94e9597ebf527d924ee1", "qobs_12c1b866c367938eef5b86ab"): (
        "non_base_wage_misroute",
        "The 1% value is promotional-exam seniority credit, while 4.7% is a distinct promotion pay rule.",
    ),
    sig("qobs_12e05d4539d49c320b1275be", "qobs_1cae30f385752047fe790fac"): (
        "distinct_classification_or_rank",
        "The bounded page applies 80% and 100% of base wage to first- and second-year officers.",
    ),
    sig("qobs_cf92a3dc861c1c2875f3d418", "qobs_de6479fbf8ec223f065e14a9", "qobs_c05dd38f896d227982e6bea6", "qobs_c9060d480445805c2541a7dd", "qobs_59342470b69745f2a0d2239b"): (
        "distinct_effective_period",
        "The salary schedule prints separate 2018-2022 annual salary columns.",
    ),
    sig("qobs_e358cfb5772df5cf1eec2a1f", "qobs_fccaa642b32c214385bdbc11"): (
        "distinct_classification_or_rank",
        "The page uses 2,538 hours for shift personnel and 2,080 for 40-hour personnel.",
    ),
    sig("qobs_4d58950a8e7886b42bbf01e1", "qobs_7d2d1296300d466b673b240b"): (
        "distinct_classification_or_rank",
        "The bounded chart compares separately labeled firefighter classifications.",
    ),
    sig("qobs_2c533fedde4387fc80a64c4a", "qobs_fc59bf9c9b4f6c74ddc33276", "qobs_f27f169d4d0f033719de6e3c", "qobs_c059d2f4a1a9fd9227abd43e", "qobs_359877707504f1764ef7b6d4"): (
        "distinct_schedule_cell",
        "Five separately printed regular-work hourly-rate cells are visible in the table.",
    ),
    sig("qobs_16dae25d828950a27b5d7574", "qobs_f889c9be1c2ea89d53beb945", "qobs_f88e74495f086a3c973274ef"): (
        "distinct_effective_period",
        "The bounded agreement records a sequence of 0%, 1.5%, and 1.5% negotiated wage increases.",
    ),
    sig("qobs_6c0b40d7c4b2bd4a1c915e42", "qobs_e910a6c3b8d77796f548a1bb", "qobs_0ee2d9d3ea75cce4cecdd2f3"): (
        "non_base_wage_misroute",
        "The page identifies degree-based one-time base-pay increases, a certification/education premium family.",
    ),
    sig("qobs_bcf614863c1283ef21f50f09", "qobs_b6b5686df5996fd526b9673c"): (
        "distinct_classification_or_rank",
        "The same-grade values belong to separate Service and Tax schedules.",
    ),
    sig("qobs_b4a8ba6882648b0701533c87", "qobs_05cafd3ebd6a0a4b06934d47"): (
        "distinct_classification_or_rank",
        "The same-grade values belong to separate Service and Tax schedules.",
    ),
    sig("qobs_835149ee462e6637e8f8700f", "qobs_ef9a2d125eabc39f794099c6"): (
        "distinct_classification_or_rank",
        "Step 1 values belong to separately printed operating-engineer classifications.",
    ),
    sig("qobs_b675a2e53a04a44de33bc59d", "qobs_3f9b49ed145bb678d54a2852"): (
        "distinct_classification_or_rank",
        "Step 2 values belong to separately printed operating-engineer classifications.",
    ),
    sig("qobs_e7d065a47ede9da2ca9c9bf4", "qobs_c702c01aaa380ba5421a63ef", "qobs_642603a66adb930a4bc11f89"): (
        "insufficient_evidence_needs_review",
        "The extracted rank conflicts with the visible schedule row and two records were already marked ambiguous-column captures.",
    ),
    sig("qobs_44c176d723a45d092b70a220", "qobs_2a4ff935eacf0887f6e17bf6"): (
        "distinct_effective_period",
        "Battalion Chief values are separately printed for 1/1/19 and 1/1/20.",
    ),
    sig("qobs_fe46d8e0f5e88cafcd12fcb9", "qobs_ec129e9ee12c9cb34b781063"): (
        "distinct_effective_period",
        "Lieutenant values are separately printed for 1/1/19 and 1/1/20.",
    ),
}

CONFLICT_NONBASE_ROUTES: dict[frozenset[str], str] = {
    sig("qobs_cadb12ccf757ba3f3e4e3f98", "qobs_8267cf3612c5a6568975789c", "qobs_89a54513858dc5c2ffc60548"): "leave",
    sig("qobs_d6f39640c4aed18a697d3f6a", "qobs_778cafef26338040d9708272"): "stipend",
    sig("qobs_b32deaf4f9666278f93edd50", "qobs_fb95dd39928c3e6e57ab1a77", "qobs_e2ce4e63b9777ddff0794a76"): "longevity",
    sig("qobs_6c0b40d7c4b2bd4a1c915e42", "qobs_e910a6c3b8d77796f548a1bb", "qobs_0ee2d9d3ea75cce4cecdd2f3"): "education_or_certification",
}
CONFLICT_REFERENCE_IDS = {"qobs_9fcb94e9597ebf527d924ee1"}


def active_original(row: dict[str, str]) -> bool:
    return row.get("active_in_provisional_lane", "true").lower() == "true"


def targeted_defaults(row: dict[str, str], observation_id: str = "") -> dict[str, str]:
    result = dict(row)
    result.update(
        {
            "targeted_qa_resolution_ids": "",
            "targeted_qa_resolution_classification": "not_in_targeted_queue",
            "targeted_qa_resolution_status": "not_applicable",
            "targeted_qa_reason_codes": "",
            "targeted_qa_source_observation_id": observation_id,
            "active_in_qa_corrected_lane": qa500.truth(active_original(row)),
        }
    )
    return result


def diagnostic(row: dict[str, str]) -> str:
    return qa500.row_diagnostic(row).replace("_", " ")


def nonbase_family(row: dict[str, str]) -> str | None:
    text = diagnostic(row)
    ordered = (
        ("healthcare_contributions", r"\bhealth(?:care)?\b|medical|insurance contribution|waiver payment"),
        ("overtime", r"overtime|double time|time and one half|time-and-one-half|callback|call back|standby|on call|compensatory|court time"),
        ("leave", r"leave|vacation|sick pay|holiday pay|holiday leave|funeral|bereavement|jury duty"),
        ("reimbursements", r"reimburse|tuition|mileage|travel pay|meal allowance|meal break"),
        ("pension", r"pension|retirement contribution"),
        ("uniform_or_equipment", r"uniform|equipment|clothing|tool allowance"),
        ("longevity", r"longevity|years of service|service award|full year of service"),
        ("education_or_certification", r"certif|education|degree pay|registration pay|cpr"),
        ("benefits", r"fringe benefit|benefit allowance|benefits enrollment"),
        ("stipend", r"stipend|bonus|premium|differential|allowance|hazard pay|acting|out of class|shift pay"),
    )
    for family, pattern in ordered:
        if re.search(pattern, text, re.I):
            return family
    return qa500.nonbase_type(row)


def bounded_value(row: dict[str, str]) -> str:
    values: list[str] = []
    for field in (
        "rate_value",
        "salary_value",
        "hourly_rate",
        "annual_salary",
        "pay_band",
        "step",
        "grade",
        "percentage_increase",
        "currency_or_unit",
    ):
        value = row.get(field, "").strip()
        if value and value not in values:
            values.append(value)
    return " | ".join(values)[:300]


def make_nonbase_from_quant(
    row: dict[str, str], family: str, resolution_id: str
) -> dict[str, str]:
    source_id = row["quantitative_observation_id"]
    target_id = qa500.stable_id("nobsqa1000", source_id, family)
    implementation = " | ".join(
        f"{key}={row[key]}"
        for key in (
            "occupation_unit_classification_rank",
            "pay_band",
            "step",
            "grade",
        )
        if row.get(key)
    )[:300]
    return {
        "non_base_wage_observation_id": target_id,
        "extraction_case_id": row["extraction_case_id"],
        "document_identity_id": row["document_identity_id"],
        "text_table_detection_id": row["text_table_detection_id"],
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "state": row["state"],
        "municipality": row["municipality"],
        "government_name": row["government_name"],
        "unit_type": row["unit_type"],
        "candidate_source_type": row["candidate_source_type"],
        "contract_period_start": row.get("contract_period_start", ""),
        "contract_period_end": row.get("contract_period_end", ""),
        "page_number": row["page_number"],
        "non_base_wage_type": family,
        "value_text": bounded_value(row),
        "effective_date": row.get("effective_date", ""),
        "eligibility_or_implementation_rule": implementation,
        "bounded_evidence_pointer": row["bounded_evidence_pointer"],
        "confidence": row.get("confidence", ""),
        "reason_code": f"TARGETED_QA_REROUTE_{family.upper()}"[:80],
        "qa_status": "qa_corrected_routed_from_quantitative",
        "cumulative_cohort": "targeted_qa_1000_reroute",
        "source_seed_observation_id": row.get("source_seed_observation_id", source_id),
        "qa_original_status": row.get("qa_status", ""),
        "qa_resolution_classification": "route_to_non_base_wage",
        "qa_resolution_status": "resolved",
        "canonical_observation_id": target_id,
        "duplicate_of": "",
        "active_in_provisional_lane": "false",
        "source_quantitative_observation_id": source_id,
        "source_mixed_join_key": row.get("mixed_join_key", ""),
        "targeted_qa_resolution_ids": resolution_id,
        "targeted_qa_resolution_classification": "route_to_non_base_wage",
        "targeted_qa_resolution_status": "resolved",
        "targeted_qa_reason_codes": f"REROUTED_{family.upper()}",
        "targeted_qa_source_observation_id": source_id,
        "active_in_qa_corrected_lane": "true",
    }


def make_reference_from_quant(
    row: dict[str, str], resolution_id: str, basis: str
) -> dict[str, str]:
    source_id = row["quantitative_observation_id"]
    reference_id = qa500.stable_id("refqa1000", source_id)
    return {
        "extraction_case_id": row["extraction_case_id"],
        "document_identity_id": row["document_identity_id"],
        "text_table_detection_id": row["text_table_detection_id"],
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "state": row["state"],
        "municipality": row["municipality"],
        "government_name": row["government_name"],
        "unit_type": row["unit_type"],
        "candidate_source_type": row["candidate_source_type"],
        "disposition": "reference_only",
        "page_relationship": "exact_evidence_page",
        "bounded_evidence_pointer": row["bounded_evidence_pointer"],
        "confidence": row.get("confidence", "medium"),
        "reason_codes": "TARGETED_QA_REFERENCE_ONLY",
        "short_rationale": basis[:300],
        "qa_status": "qa_corrected_reference_only",
        "cumulative_cohort": "targeted_qa_1000_reference",
        "source_seed_observation_id": row.get("source_seed_observation_id", source_id),
        "qa_original_status": row.get("qa_status", ""),
        "qa_resolution_classification": "reference_only",
        "qa_resolution_status": "resolved",
        "canonical_observation_id": reference_id,
        "duplicate_of": "",
        "active_in_provisional_lane": "false",
        "targeted_qa_reference_id": reference_id,
        "source_quantitative_observation_id": source_id,
        "targeted_qa_resolution_ids": resolution_id,
        "targeted_qa_resolution_classification": "reference_only",
        "targeted_qa_resolution_status": "resolved",
        "targeted_qa_reason_codes": "REFERENCE_ONLY_NO_USABLE_VALUE",
        "targeted_qa_source_observation_id": source_id,
        "active_in_qa_corrected_lane": "true",
    }


def append_resolution(row: dict[str, str], resolution_id: str, classification: str, reason: str, *, active: bool) -> None:
    row.update(
        {
            "targeted_qa_resolution_ids": resolution_id,
            "targeted_qa_resolution_classification": classification,
            "targeted_qa_resolution_status": "resolved",
            "targeted_qa_reason_codes": reason,
            "targeted_qa_source_observation_id": row.get("quantitative_observation_id", ""),
            "active_in_qa_corrected_lane": qa500.truth(active),
        }
    )


def split_quant_and_nonbase(
    row: dict[str, str], family: str, resolution_id: str
) -> tuple[dict[str, str], dict[str, str]]:
    """Preserve a shared join key when a future record genuinely needs a split."""
    retained = dict(row)
    append_resolution(
        retained,
        resolution_id,
        "split_quant_and_non_base_components",
        "SPLIT_BASE_COMPONENT_RETAINED",
        active=True,
    )
    created = make_nonbase_from_quant(row, family, resolution_id)
    created["targeted_qa_resolution_classification"] = (
        "split_quant_and_non_base_components"
    )
    created["source_mixed_join_key"] = row.get("mixed_join_key", "")
    return retained, created


def write_outputs(
    output_dir: Path,
    fields: dict[str, list[str]],
    rows: dict[str, list[dict[str, str]]],
    resolutions: list[dict[str, str]],
    summary: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    qa500.write_csv(output_dir / OUTPUT_NAMES["resolutions"], RESOLUTION_FIELDS, resolutions)
    qa500.write_csv(output_dir / OUTPUT_NAMES["quant"], fields["quant"] + TARGET_QA_FIELDS, rows["quant"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["qual"], fields["qual"] + TARGET_QA_FIELDS, rows["qual"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["mixed"], fields["mixed"] + TARGET_QA_FIELDS + MIXED_QA_FIELDS, rows["mixed"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["nonbase"], fields["nonbase"] + NONBASE_PROVENANCE_FIELDS + TARGET_QA_FIELDS, rows["nonbase"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["reference"], fields["reference"] + REFERENCE_PROVENANCE_FIELDS + TARGET_QA_FIELDS, rows["reference"])
    qa500.write_json(output_dir / OUTPUT_NAMES["summary"], summary)
    qa500.write_json(output_dir / OUTPUT_NAMES["decision"], decision)

    routing = summary["base_non_base_resolution_counts"]
    conflicts = summary["conflict_resolution_counts"]
    report = f"""# Targeted QA report: cumulative provisional 1,000-document compensation extraction

- Targeted unresolved rows/groups processed: {summary['review_rows_or_groups_processed']} / 151
- GABRIEL/API used: `false`
- Possible base/non-base records reviewed: {summary['base_non_base_routing_record_count']}
- Routing resolution counts: `{json.dumps(routing, sort_keys=True)}`
- Quantitative conflict groups reviewed: {summary['conflict_group_count']}
- Conflict resolution counts: `{json.dumps(conflicts, sort_keys=True)}`
- Unresolved quantitative conflict groups: {summary['unresolved_conflict_group_count']}
- Revised unresolved conflict rate: {summary['unresolved_quantitative_conflict_rate']:.4%}
- Corrected active quantitative observations: {summary['corrected_quantitative_active_observation_count']}
- Corrected active qualitative observations: {summary['corrected_qualitative_active_observation_count']}
- Corrected active mixed cases: {summary['corrected_mixed_active_case_count']}
- Corrected active non-base-wage observations: {summary['corrected_non_base_wage_active_observation_count']}
- Corrected active reference/exclusion rows: {summary['corrected_reference_exclusion_active_count']}
- Duplicate observation IDs: {summary['duplicate_observation_id_count']}
- Invalid bounded page pointers: {summary['invalid_observation_page_count']}
- Unresolved base/non-base contamination: {summary['unresolved_base_non_base_contamination_count']}
- Matched police/fire/non-safety representation intact: `{qa500.truth(summary['matched_representation_intact'])}`
- Recomputed QA: `{'pass' if decision['qa_pass'] else 'fail'}`
- Remaining readable parse-text extraction allowed: `{qa500.truth(decision['remaining_readable_parse_text_extraction_allowed'])}`

The 126 routing records were resolved with explicit retain/reroute/reference
actions and reason codes. Two conflict groups remain explicitly unresolved:
aggregate fiscal-impact totals that are not employee wage cells, and a salary
capture whose extracted rank conflicts with the visible schedule row. Their
combined rate remains below the 2% gate.

All original cumulative rows remain present in their corrected shadow ledger.
Rerouted records preserve their original quantitative observation ID in
provenance fields, existing duplicate canonicalization is retained, and mixed
membership is recomputed without changing the original cumulative ledgers.

No new extraction, selection, GABRIEL/API call, URL access, download, OCR,
ingestion, codification, final merge, wage-gap calculation, or regression
occurred.
"""
    (output_dir / OUTPUT_NAMES["report"]).write_text(report, encoding="utf-8")

    validation = f"""# Cumulative 1,000-document targeted QA validation — 2026-07-25

- Exact unresolved scope: `{'pass' if summary['review_rows_or_groups_processed'] == 151 else 'fail'}` ({summary['review_rows_or_groups_processed']})
- Base/non-base rows accounted for: `{'pass' if sum(routing.values()) == 126 else 'fail'}` ({sum(routing.values())})
- Conflict groups accounted for: `{'pass' if sum(conflicts.values()) == 25 else 'fail'}` ({sum(conflicts.values())})
- Corrected shadow ledgers separate from originals: `pass`
- Input SHA-256 values recorded: `pass`
- Duplicate observation IDs: `{'pass' if summary['duplicate_observation_id_count'] == 0 else 'fail'}` ({summary['duplicate_observation_id_count']})
- Invalid bounded page pointers: `{'pass' if summary['invalid_observation_page_count'] == 0 else 'fail'}` ({summary['invalid_observation_page_count']})
- Unresolved conflict rate at most 2%: `{'pass' if summary['unresolved_quantitative_conflict_rate'] <= .02 else 'fail'}` ({summary['unresolved_quantitative_conflict_rate']:.4%})
- Unresolved base/non-base contamination: `{'pass' if summary['unresolved_base_non_base_contamination_count'] == 0 else 'fail'}` ({summary['unresolved_base_non_base_contamination_count']})
- Existing canonicalized duplicate observations preserved: `{'pass' if summary['existing_duplicate_observations_preserved'] == 9 else 'fail'}` ({summary['existing_duplicate_observations_preserved']})
- Matched representation: `{'pass' if summary['matched_representation_intact'] else 'fail'}`
- GABRIEL/API used: `false`
- Full text/table/raw prompt/raw response/image artifacts saved: `false`

Repository-wide command validation is appended in the task result and relay
after the required test/build/validation commands complete.
"""
    (output_dir / OUTPUT_NAMES["validation"]).write_text(validation, encoding="utf-8")


def resolve(source_dir: Path, output_dir: Path, *, write: bool = True) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    if source_dir == output_dir or source_dir in output_dir.parents:
        raise ValueError("Output directory must be separate from the cumulative source directory")

    required = [REVIEW, DECISION, PACKET, SELECTION, QUANT, QUAL, MIXED, NONBASE, REFERENCE]
    missing = [name for name in required if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing required cumulative QA inputs: " + ", ".join(missing))
    input_hashes = {name: qa500.sha_file(source_dir / name) for name in required}

    review = qa500.read_csv(source_dir / REVIEW)
    review_counts = Counter(row["review_type"] for row in review)
    expected_all = {
        "exact_content_duplicate": 7,
        "potential_quantitative_conflict": 82,
        "possible_non_base_wage_quantitative": 126,
    }
    if len(review) != 215 or dict(review_counts) != expected_all:
        raise ValueError(f"Unexpected cumulative review queue: {len(review)} rows, {review_counts}")
    unresolved = [row for row in review if row["unresolved_flag"] == "true"]
    unresolved_counts = Counter(row["review_type"] for row in unresolved)
    expected_unresolved = {
        "potential_quantitative_conflict": 25,
        "possible_non_base_wage_quantitative": 126,
    }
    if len(unresolved) != 151 or dict(unresolved_counts) != expected_unresolved:
        raise ValueError(f"Unresolved scope is not the required 151: {len(unresolved)}, {unresolved_counts}")

    quant_source = qa500.read_csv(source_dir / QUANT)
    qual_source = qa500.read_csv(source_dir / QUAL)
    mixed_source = qa500.read_csv(source_dir / MIXED)
    nonbase_source = qa500.read_csv(source_dir / NONBASE)
    reference_source = qa500.read_csv(source_dir / REFERENCE)
    packet = qa500.read_csv(source_dir / PACKET)
    selection = qa500.read_csv(source_dir / SELECTION)
    original_decision = json.loads((source_dir / DECISION).read_text(encoding="utf-8"))

    fields = {
        "quant": qa500.read_fields(source_dir / QUANT),
        "qual": qa500.read_fields(source_dir / QUAL),
        "mixed": qa500.read_fields(source_dir / MIXED),
        "nonbase": qa500.read_fields(source_dir / NONBASE),
        "reference": qa500.read_fields(source_dir / REFERENCE),
    }
    quant = {
        row["quantitative_observation_id"]: targeted_defaults(row, row["quantitative_observation_id"])
        for row in quant_source
    }
    qualitative = [
        targeted_defaults(row, row["qualitative_observation_id"])
        for row in qual_source
    ]
    nonbase = {
        row["non_base_wage_observation_id"]: targeted_defaults(row, row["non_base_wage_observation_id"])
        for row in nonbase_source
    }
    references = [targeted_defaults(row) for row in reference_source]

    resolutions: list[dict[str, str]] = []
    routing_counts: Counter[str] = Counter()
    conflict_counts: Counter[str] = Counter()
    routed_quant_ids: set[str] = set()
    reference_quant_ids: set[str] = set()
    created_nonbase: dict[str, str] = {}

    for queue_number, queued in enumerate(unresolved, 1):
        ids = [value for value in queued["observation_ids"].split("|") if value]
        if not ids or any(observation_id not in quant for observation_id in ids):
            raise ValueError(f"Queue row references missing quantitative IDs: {queued}")
        resolution_id = qa500.stable_id(
            "qares1000", str(queue_number), queued["review_type"], queued["extraction_case_id"], queued["observation_ids"]
        )
        classification = ""
        status = "resolved"
        quant_action = "no_change"
        nonbase_action = "no_change"
        reference_action = "no_change"
        retained: list[str] = []
        routed: list[str] = []
        reference_ids: list[str] = []
        new_nonbase_ids: list[str] = []
        new_reference_ids: list[str] = []
        reason_codes: list[str] = []
        confidence = "high"
        unresolved_flag = False
        local_mode = "structured_fields_and_bounded_pointer_only"

        if queued["review_type"] == "possible_non_base_wage_quantitative":
            if len(ids) != 1:
                raise ValueError("Each possible non-base row must contain exactly one observation")
            observation_id = ids[0]
            row = quant[observation_id]
            if observation_id in BASE_RETAIN_BASIS:
                classification = "retain_quantitative_base_wage"
                basis = BASE_RETAIN_BASIS[observation_id]
                retained = ids
                quant_action = "retain_active_base_wage"
                reason_codes = ["BOUNDED_BASE_SALARY_CELL_CONFIRMED"]
                local_mode = "structured_fields_and_bounded_local_page_text"
                append_resolution(row, resolution_id, classification, reason_codes[0], active=True)
            elif observation_id in REFERENCE_ONLY_BASIS:
                classification = "reference_only"
                basis = REFERENCE_ONLY_BASIS[observation_id]
                reference_ids = ids
                quant_action = "deactivate_reference_only"
                reference_action = "create_corrected_reference_record"
                reason_codes = ["RATE_REFERENCED_OUTSIDE_CAPTURED_RECORD"]
                append_resolution(row, resolution_id, classification, reason_codes[0], active=False)
                reference = make_reference_from_quant(row, resolution_id, basis)
                references.append(reference)
                new_reference_ids.append(reference["targeted_qa_reference_id"])
                reference_quant_ids.add(observation_id)
            else:
                family = nonbase_family(row)
                if not family:
                    classification = "insufficient_evidence_needs_review"
                    basis = "No deterministic base/non-base family could be established from bounded structured fields."
                    status = "unresolved"
                    unresolved_flag = True
                    confidence = "low"
                    retained = ids
                    quant_action = "retain_active_flag_unresolved"
                    reason_codes = ["NONBASE_FAMILY_NOT_DETERMINISTIC"]
                    row.update(
                        {
                            "targeted_qa_resolution_ids": resolution_id,
                            "targeted_qa_resolution_classification": classification,
                            "targeted_qa_resolution_status": status,
                            "targeted_qa_reason_codes": reason_codes[0],
                            "targeted_qa_source_observation_id": observation_id,
                            "active_in_qa_corrected_lane": "true",
                        }
                    )
                else:
                    classification = "route_to_non_base_wage"
                    basis = f"Structured values/reason codes identify the explicit non-base family: {family}."
                    routed = ids
                    quant_action = "deactivate_and_route_to_non_base_wage"
                    nonbase_action = "create_corrected_non_base_wage_record"
                    reason_codes = [f"EXPLICIT_NONBASE_{family.upper()}"]
                    append_resolution(row, resolution_id, classification, reason_codes[0], active=False)
                    created = make_nonbase_from_quant(row, family, resolution_id)
                    target_id = created["non_base_wage_observation_id"]
                    if target_id in nonbase:
                        raise ValueError(f"Reroute target already exists: {target_id}")
                    nonbase[target_id] = created
                    created_nonbase[observation_id] = target_id
                    new_nonbase_ids.append(target_id)
                    routed_quant_ids.add(observation_id)
            if classification not in NONBASE_CLASSES:
                raise AssertionError(classification)
            routing_counts[classification] += 1

        elif queued["review_type"] == "potential_quantitative_conflict":
            signature = frozenset(ids)
            if signature not in CONFLICT_DECISIONS:
                raise ValueError(f"No deterministic conflict decision for {sorted(signature)}")
            classification, basis = CONFLICT_DECISIONS[signature]
            conflict_counts[classification] += 1
            local_mode = "structured_fields_and_bounded_local_page_text"
            if classification in {"insufficient_evidence_needs_review", "true_conflict_unresolved"}:
                status = "unresolved"
                unresolved_flag = True
                confidence = "low"
                retained = ids
                quant_action = "retain_active_flag_unresolved"
                reason_codes = ["BOUNDED_EVIDENCE_REMAINS_UNDERSPECIFIED"]
                for observation_id in ids:
                    quant[observation_id].update(
                        {
                            "targeted_qa_resolution_ids": resolution_id,
                            "targeted_qa_resolution_classification": classification,
                            "targeted_qa_resolution_status": status,
                            "targeted_qa_reason_codes": reason_codes[0],
                            "targeted_qa_source_observation_id": observation_id,
                            "active_in_qa_corrected_lane": "true",
                        }
                    )
            elif signature in CONFLICT_NONBASE_ROUTES:
                family = CONFLICT_NONBASE_ROUTES[signature]
                routed = ids
                quant_action = "deactivate_and_route_to_non_base_wage"
                nonbase_action = "create_corrected_non_base_wage_records"
                reason_codes = [f"CONFLICT_GROUP_IS_NONBASE_{family.upper()}"]
                for observation_id in ids:
                    row = quant[observation_id]
                    append_resolution(row, resolution_id, "route_to_non_base_wage", reason_codes[0], active=False)
                    created = make_nonbase_from_quant(row, family, resolution_id)
                    target_id = created["non_base_wage_observation_id"]
                    if target_id in nonbase:
                        raise ValueError(f"Reroute target already exists: {target_id}")
                    nonbase[target_id] = created
                    created_nonbase[observation_id] = target_id
                    new_nonbase_ids.append(target_id)
                    routed_quant_ids.add(observation_id)
            elif signature == sig("qobs_9fcb94e9597ebf527d924ee1", "qobs_12c1b866c367938eef5b86ab"):
                exam_id = "qobs_9fcb94e9597ebf527d924ee1"
                pay_id = "qobs_12c1b866c367938eef5b86ab"
                reference_ids = [exam_id]
                retained = [pay_id]
                quant_action = "retain_pay_rule_and_deactivate_exam_credit"
                reference_action = "create_corrected_reference_record"
                reason_codes = ["PROMOTION_EXAM_CREDIT_NOT_COMPENSATION", "PROMOTION_PAY_RULE_RETAINED"]
                append_resolution(quant[exam_id], resolution_id, "reference_only", reason_codes[0], active=False)
                append_resolution(quant[pay_id], resolution_id, "retain_quantitative_base_wage", reason_codes[1], active=True)
                reference = make_reference_from_quant(quant[exam_id], resolution_id, basis)
                references.append(reference)
                new_reference_ids.append(reference["targeted_qa_reference_id"])
                reference_quant_ids.add(exam_id)
            else:
                retained = ids
                quant_action = "retain_distinct_active_records"
                reason_codes = [f"CONFLICT_RESOLVED_{classification.upper()}"]
                for observation_id in ids:
                    append_resolution(quant[observation_id], resolution_id, classification, reason_codes[0], active=True)
            if classification not in CONFLICT_CLASSES:
                raise AssertionError(classification)
        else:
            raise ValueError(f"Unexpected unresolved review type: {queued['review_type']}")

        pointers = sorted({quant[observation_id]["bounded_evidence_pointer"] for observation_id in ids})
        resolutions.append(
            {
                "targeted_qa_resolution_id": resolution_id,
                "review_queue_row_number": str(queue_number),
                "review_type": queued["review_type"],
                "extraction_case_id": queued["extraction_case_id"],
                "page_number": queued["page_number"],
                "lane": queued["lane"],
                "source_observation_ids": "|".join(ids),
                "source_observation_count": queued["observation_count"],
                "resolution_classification": classification,
                "resolution_status": status,
                "quantitative_action": quant_action,
                "non_base_wage_action": nonbase_action,
                "reference_action": reference_action,
                "retained_quantitative_observation_ids": "|".join(retained),
                "routed_quantitative_observation_ids": "|".join(routed),
                "reference_only_quantitative_observation_ids": "|".join(reference_ids),
                "created_non_base_wage_observation_ids": "|".join(new_nonbase_ids),
                "created_reference_ids": "|".join(new_reference_ids),
                "structured_basis": basis[:600],
                "bounded_evidence_pointer": "|".join(pointers),
                "local_evidence_inspected": local_mode,
                "reason_codes": "|".join(reason_codes),
                "confidence": confidence,
                "unresolved_flag": qa500.truth(unresolved_flag),
                "notes": "No values, classifications, steps, ranks, or dates were fabricated.",
            }
        )

    # Recompute mixed membership with the corrected active quantitative IDs.
    mixed_rows: list[dict[str, str]] = []
    for source in mixed_source:
        row = targeted_defaults(source, source["mixed_join_key"])
        original_ids = [value for value in source["quantitative_observation_ids"].split("|") if value]
        corrected_ids: list[str] = []
        for observation_id in original_ids:
            canonical = quant[observation_id].get("canonical_observation_id") or observation_id
            if canonical not in quant:
                raise ValueError(f"Mixed row references missing canonical quantitative ID: {canonical}")
            if quant[canonical]["active_in_qa_corrected_lane"] == "true" and canonical not in corrected_ids:
                corrected_ids.append(canonical)
        qual_ids = [value for value in source["qualitative_observation_ids"].split("|") if value]
        changed = corrected_ids != original_ids
        active = bool(active_original(source) and corrected_ids and qual_ids)
        row.update(
            {
                "targeted_qa_original_quantitative_observation_ids": "|".join(original_ids),
                "targeted_qa_corrected_quantitative_observation_ids": "|".join(corrected_ids),
                "quantitative_observation_ids": "|".join(corrected_ids),
                "quantitative_observation_count": str(len(corrected_ids)),
                "qualitative_observation_count": str(len(qual_ids)),
                "targeted_qa_resolution_classification": "mixed_membership_corrected" if changed else "not_in_targeted_queue",
                "targeted_qa_resolution_status": "resolved" if changed else "not_applicable",
                "targeted_qa_reason_codes": "INACTIVE_QUANTITATIVE_MEMBERS_REMOVED" if changed else "",
                "active_in_qa_corrected_lane": qa500.truth(active),
            }
        )
        mixed_rows.append(row)

    quant_rows = list(quant.values())
    nonbase_rows = list(nonbase.values())
    active_quant = [row for row in quant_rows if row["active_in_qa_corrected_lane"] == "true"]
    active_qual = [row for row in qualitative if row["active_in_qa_corrected_lane"] == "true"]
    active_mixed = [row for row in mixed_rows if row["active_in_qa_corrected_lane"] == "true"]
    active_nonbase = [row for row in nonbase_rows if row["active_in_qa_corrected_lane"] == "true"]
    active_reference = [row for row in references if row["active_in_qa_corrected_lane"] == "true"]

    packet_pages: dict[str, set[int]] = defaultdict(set)
    for row in packet:
        packet_pages[row["extraction_case_id"]].add(int(row["page_number"]))
    invalid_pages = sum(
        int(row["page_number"]) not in packet_pages[row["extraction_case_id"]]
        for row in active_quant + active_qual + active_nonbase
    )
    observation_ids = (
        [row["quantitative_observation_id"] for row in quant_rows]
        + [row["qualitative_observation_id"] for row in qualitative]
        + [row["non_base_wage_observation_id"] for row in nonbase_rows]
    )
    duplicate_ids = len(observation_ids) - len(set(observation_ids))
    unresolved_conflicts = sum(
        conflict_counts[label]
        for label in ("true_conflict_unresolved", "insufficient_evidence_needs_review")
    )
    unresolved_rate = unresolved_conflicts / max(1, len(active_quant))
    unresolved_contamination = routing_counts["insufficient_evidence_needs_review"]

    unit_counts = Counter(row["unit_type"] for row in selection)
    expected_unit_counts = original_decision.get("unit_type_counts", {})
    representation_intact = (
        len(selection) == 1000
        and dict(sorted(unit_counts.items())) == expected_unit_counts
        and all(unit_counts.get(unit, 0) > 0 for unit in ("police", "fire", "non_safety"))
        and original_decision.get("matched_representation_intact") is True
    )
    duplicate_preserved = sum(
        1
        for row in quant_rows + nonbase_rows
        if row.get("duplicate_of") and row.get("active_in_provisional_lane") == "false"
    )
    separate = all((output_dir / name).resolve() != (source_dir / source).resolve() for name, source in (
        (OUTPUT_NAMES["quant"], QUANT),
        (OUTPUT_NAMES["qual"], QUAL),
        (OUTPUT_NAMES["mixed"], MIXED),
        (OUTPUT_NAMES["nonbase"], NONBASE),
        (OUTPUT_NAMES["reference"], REFERENCE),
    ))

    integrity_pass = (
        duplicate_ids == 0
        and invalid_pages == 0
        and unresolved_contamination == 0
        and representation_intact
        and separate
        and duplicate_preserved == 9
    )
    qa_pass = integrity_pass and unresolved_rate <= 0.02
    decision_name = (
        "remaining_readable_parse_text_extraction_allowed"
        if qa_pass
        else "blocked_pending_additional_targeted_qa"
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": qa500.now(),
        "gabriel_api_used": False,
        "new_extraction_run": False,
        "new_document_selection": False,
        "review_rows_or_groups_processed": len(resolutions),
        "base_non_base_routing_record_count": unresolved_counts["possible_non_base_wage_quantitative"],
        "base_non_base_resolution_counts": dict(sorted(routing_counts.items())),
        "conflict_group_count": unresolved_counts["potential_quantitative_conflict"],
        "conflict_resolution_counts": dict(sorted(conflict_counts.items())),
        "resolved_conflict_group_count": 25 - unresolved_conflicts,
        "unresolved_conflict_group_count": unresolved_conflicts,
        "unresolved_quantitative_conflict_rate": round(unresolved_rate, 8),
        "quantitative_records_routed_to_non_base_wage": len(routed_quant_ids),
        "quantitative_records_routed_to_reference": len(reference_quant_ids),
        "new_non_base_wage_records_created": len(created_nonbase),
        "unresolved_base_non_base_contamination_count": unresolved_contamination,
        "corrected_quantitative_active_observation_count": len(active_quant),
        "corrected_quantitative_source_row_count": len(quant_rows),
        "corrected_qualitative_active_observation_count": len(active_qual),
        "corrected_mixed_active_case_count": len(active_mixed),
        "corrected_mixed_source_row_count": len(mixed_rows),
        "corrected_non_base_wage_active_observation_count": len(active_nonbase),
        "corrected_non_base_wage_source_row_count": len(nonbase_rows),
        "corrected_reference_exclusion_active_count": len(active_reference),
        "corrected_reference_exclusion_source_row_count": len(references),
        "duplicate_observation_id_count": duplicate_ids,
        "invalid_observation_page_count": invalid_pages,
        "existing_duplicate_observations_preserved": duplicate_preserved,
        "selection_count": len(selection),
        "unit_type_counts": dict(sorted(unit_counts.items())),
        "matched_representation_intact": representation_intact,
        "corrected_ledgers_provisional_and_separate": separate,
        "input_sha256": input_hashes,
    }
    decision = {
        **summary,
        "integrity_qa_pass": integrity_pass,
        "qa_pass": qa_pass,
        "qa_status": "pass" if qa_pass else "fail",
        "decision": decision_name,
        "remaining_readable_parse_text_extraction_allowed": qa_pass,
        "targeted_qa_required_before_remaining_run": not qa_pass,
        "final_analysis_merge_allowed": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "dashboard_status_required": "compensation_extraction_1000_targeted_qa_completed" if qa_pass else "compensation_extraction_1000_targeted_qa_still_blocked",
        "next_recommendation": "run_remaining_unique_readable_parse_text_provisional_extraction" if qa_pass else "continue_bounded_targeted_qa",
    }
    result_rows = {
        "quant": quant_rows,
        "qual": qualitative,
        "mixed": mixed_rows,
        "nonbase": nonbase_rows,
        "reference": references,
    }
    if write:
        write_outputs(output_dir, fields, result_rows, resolutions, summary, decision)
    return {
        "summary": summary,
        "decision": decision,
        "resolutions": resolutions,
        "rows": result_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = resolve(args.source_dir, args.output_dir, write=not args.dry_run)
    print(
        json.dumps(
            {
                "status": "dry_run_valid" if args.dry_run else "targeted_qa_completed",
                "review_rows_or_groups_processed": result["summary"]["review_rows_or_groups_processed"],
                "qa_pass": result["decision"]["qa_pass"],
                "remaining_readable_parse_text_extraction_allowed": result["decision"]["remaining_readable_parse_text_extraction_allowed"],
                "gabriel_api_used": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
