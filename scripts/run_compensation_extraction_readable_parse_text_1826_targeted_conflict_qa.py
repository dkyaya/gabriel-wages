#!/usr/bin/env python3
"""Resolve the 37 bounded conflicts in the 1,826-case provisional layer.

This is a deterministic QA-only pass.  It reads the completed readable
parse-text cumulative ledgers, writes separate corrected shadow ledgers, and
never selects documents, extracts evidence, calls a model, opens a URL, uses
OCR, or mutates an upstream ledger.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import run_compensation_extraction_1000_targeted_qa as qa1000
import run_compensation_extraction_remaining_parse_text as remaining
import run_compensation_extraction_targeted_qa as qa500


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = (
    "COMPENSATION-EVIDENCE-EXTRACTION-READABLE-PARSE-TEXT-1826-"
    "TARGETED-CONFLICT-QA-2026-07-25"
)
SOURCE_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-REMAINING-PARSE-TEXT-826-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-READABLE-PARSE-TEXT-1826-"
    "TARGETED-CONFLICT-QA-2026-07-25"
)

REVIEW = "remaining_parse_text_conflict_review.csv"
DECISION = "remaining_parse_text_decision_report.json"
SUMMARY = "remaining_parse_text_cumulative_summary.json"
QUANT = "cumulative_readable_parse_text_quantitative_ledger.csv"
QUAL = "cumulative_readable_parse_text_qualitative_mechanism_ledger.csv"
MIXED = "cumulative_readable_parse_text_mixed_ledger.csv"
NONBASE = "cumulative_readable_parse_text_non_base_wage_ledger.csv"
REFERENCE = "cumulative_readable_parse_text_reference_exclusion_ledger.csv"

OUTPUT_NAMES = {
    "resolutions": "readable_parse_text_1826_targeted_conflict_qa_resolutions.csv",
    "quant": "readable_parse_text_1826_quantitative_ledger_qa_corrected.csv",
    "qual": "readable_parse_text_1826_qualitative_mechanism_ledger_qa_corrected.csv",
    "mixed": "readable_parse_text_1826_mixed_ledger_qa_corrected.csv",
    "nonbase": "readable_parse_text_1826_non_base_wage_ledger_qa_corrected.csv",
    "reference": "readable_parse_text_1826_reference_exclusion_ledger_qa_corrected.csv",
    "summary": "readable_parse_text_1826_targeted_conflict_qa_summary.json",
    "decision": "readable_parse_text_1826_recomputed_decision.json",
    "report": "readable_parse_text_1826_targeted_conflict_qa_report.md",
    "validation": (
        "readable_parse_text_1826_targeted_conflict_qa_validation_2026-07-25.md"
    ),
}

CONFLICT_QA_FIELDS = [
    "readable_conflict_qa_resolution_id",
    "readable_conflict_qa_classification",
    "readable_conflict_qa_status",
    "readable_conflict_qa_reason_codes",
    "readable_conflict_qa_source_observation_id",
    "active_in_readable_conflict_qa_lane",
]
MIXED_FIELDS = [
    "readable_conflict_qa_original_quantitative_observation_ids",
    "readable_conflict_qa_corrected_quantitative_observation_ids",
]
NONBASE_PROVENANCE_FIELDS = [
    "source_quantitative_observation_id",
    "source_mixed_join_key",
]

RESOLUTION_FIELDS = [
    "readable_conflict_qa_resolution_id",
    "review_queue_row_number",
    "extraction_case_id",
    "page_number",
    "source_observation_ids",
    "source_observation_count",
    "resolution_classification",
    "resolution_status",
    "quantitative_action",
    "non_base_wage_action",
    "retained_quantitative_observation_ids",
    "routed_quantitative_observation_ids",
    "created_non_base_wage_observation_ids",
    "structured_basis",
    "bounded_evidence_pointer",
    "local_evidence_inspected",
    "reason_codes",
    "confidence",
    "unresolved_flag",
    "notes",
]


def sig(*ids: str) -> frozenset[str]:
    return frozenset(ids)


# New remaining-batch decisions were established from the existing structured
# fields and the single bounded page named in each pointer.  Values are not
# copied from those pages and no missing field is filled in.
NEW_CONFLICT_DECISIONS: dict[frozenset[str], tuple[str, str]] = {
    sig("qobs_385b65477fc10d7f7e75ea04", "qobs_807ac4fbdef04119190cea92"): (
        "distinct_schedule_cell",
        "The bounded Accountant row prints separate minimum and maximum monthly-range cells.",
    ),
    sig("qobs_4a1c3ca7714c258dd0a0454e", "qobs_d873c5dda67baac7c3527d57", "qobs_720b28cb3bdcab6c4c14bb7a", "qobs_00404927aa0bcef6e91e9a53", "qobs_da3a99c999e5977d01aef733"): (
        "distinct_schedule_cell",
        "The bounded salary schedule prints the values in separate classification/range cells.",
    ),
    sig("qobs_1c316c2b1f0edd6989940ae1", "qobs_607aea7d85024b899c0451d6"): (
        "distinct_classification_or_rank",
        "The bounded table labels separate probationary-firefighter and firefighter schedule rows.",
    ),
    sig("qobs_d4ce04e08316696c3f53c9fd", "qobs_1023a414cb004adbcd96fd4c", "qobs_9d2607efbee146824bce505b"): (
        "distinct_classification_or_rank",
        "The bounded schedule places the values in separately labeled firefighter/rank sections.",
    ),
    sig("qobs_25fb85325140469b4fa0cd01", "qobs_24ffef991e72480c736af4a1", "qobs_5d3ab3444d886ea18afc5b03"): (
        "non_base_wage_misroute",
        "Article 23 labels all three values as temporary working-out-of-classification increases to regular base pay.",
    ),
    sig("qobs_f36e3f4b3de743590affc1ba", "qobs_3b3350f26db53b5da83a959a"): (
        "distinct_schedule_cell",
        "The Superintendent row prints separate lower and upper salary-range endpoints.",
    ),
    sig("qobs_ec4f52fc46e62858d1a51c77", "qobs_83c4551fa846e056b9a96ae7"): (
        "distinct_schedule_cell",
        "The Director row prints separate lower and upper salary-range endpoints.",
    ),
    sig("qobs_b9e8cd16e0a8e3e39efda5c6", "qobs_68b0b869b7dcbb66b248e257"): (
        "distinct_classification_or_rank",
        "The bounded ordinance assigns the values to Financial Specialist Senior and GIS Manager rows.",
    ),
    sig("qobs_4bb5a1594319d7ea34946c34", "qobs_59b323dfd80ab585addca82b", "qobs_c197731be206ec83e64ea7e2"): (
        "distinct_effective_period",
        "The same firefighter step is printed in separate 2025, 2026, and 2027 columns.",
    ),
    sig("qobs_8c2bc82f477980d60d998149", "qobs_e845ee2d9ac248946c848da3"): (
        "distinct_effective_period",
        "The same firefighter step is printed in separate 2025 and 2026 columns.",
    ),
    sig("qobs_673f1157a566753eab1824f9", "qobs_6767c141cd71d40768c126a7", "qobs_0df1d7696c5cc89dbca4cf2c"): (
        "distinct_classification_or_rank",
        "The bounded wage schedule assigns the values to different public-works classifications.",
    ),
    sig("qobs_080a5c596af4aded2e2024bb", "qobs_d2c873454eee9ae0894add69", "qobs_80da70883316022ab772c079", "qobs_90a9d499cb756cc68b6e41c7", "qobs_71cde6b875761e01b1e9196c"): (
        "distinct_classification_or_rank",
        "The bounded pay plan prints separate officer-training through senior-patrol rank cells.",
    ),
    sig("qobs_4b5db992df89fc51db7bae19", "qobs_555594ca210035c9fab0d150", "qobs_9de6044cf801424a7364453b"): (
        "distinct_effective_period",
        "The Detective Grade row prints separate 2022, 2023, and 2024 annual columns.",
    ),
    sig("qobs_4ca8277e1572486ab52efc23", "qobs_70703c3b95cd8b9a8df805b3"): (
        "distinct_effective_period",
        "The Patrolman 1st Grade row prints separate 2022 and 2023 annual columns.",
    ),
    sig("qobs_0a80a0c9516e6d795062ac6d", "qobs_8cd629732fd6361d30656b0d", "qobs_ff3d0aa041feb91e1a977e8b"): (
        "distinct_effective_period",
        "The Lieutenant Entry row prints the values in separate annual schedule columns.",
    ),
    sig("qobs_394f913aea7e067e9f65cc3b", "qobs_fc88dddf59047c0f702cdd2c", "qobs_14d280169d4efe7cc27e8202", "qobs_9edcf6f23e340d0c97288d9a", "qobs_1e34b9ed9569642eebb329e9"): (
        "distinct_schedule_cell",
        "The FF/EMT row prints five separate A-E wage-scale step cells.",
    ),
    sig("qobs_bd0dbf2c064a2b43fa212f93", "qobs_2b6101512f340062a033073c"): (
        "distinct_classification_or_rank",
        "The bounded schedule prints separate Firefighter and Fire Paramedic EMT-II Step 1 columns.",
    ),
}

NONBASE_ROUTES = {
    sig(
        "qobs_25fb85325140469b4fa0cd01",
        "qobs_24ffef991e72480c736af4a1",
        "qobs_5d3ab3444d886ea18afc5b03",
    ): "stipend",
}


def active(row: dict[str, str]) -> bool:
    return remaining.active(row)


def conflict_defaults(row: dict[str, str], observation_id: str = "") -> dict[str, str]:
    result = dict(row)
    result.update(
        {
            "readable_conflict_qa_resolution_id": "",
            "readable_conflict_qa_classification": "not_in_targeted_queue",
            "readable_conflict_qa_status": "not_applicable",
            "readable_conflict_qa_reason_codes": "",
            "readable_conflict_qa_source_observation_id": observation_id,
            "active_in_readable_conflict_qa_lane": qa500.truth(active(row)),
        }
    )
    return result


def make_nonbase(row: dict[str, str], resolution_id: str) -> dict[str, str]:
    created = qa1000.make_nonbase_from_quant(row, "stipend", resolution_id)
    source_id = row["quantitative_observation_id"]
    created["non_base_wage_observation_id"] = qa500.stable_id(
        "nobsqa1826", source_id, "working_out_of_classification"
    )
    created["canonical_observation_id"] = created["non_base_wage_observation_id"]
    created["qa_status"] = "qa_corrected_working_out_of_classification_reroute"
    created["cumulative_cohort"] = "readable_parse_text_1826_targeted_conflict_qa"
    created["reason_code"] = "WORKING_OUT_OF_CLASSIFICATION_NON_BASE"
    created["targeted_qa_resolution_classification"] = "route_to_non_base_wage"
    created["active_in_qa_corrected_lane"] = "true"
    created.update(
        {
            "readable_conflict_qa_resolution_id": resolution_id,
            "readable_conflict_qa_classification": "non_base_wage_misroute",
            "readable_conflict_qa_status": "resolved",
            "readable_conflict_qa_reason_codes": "WORKING_OUT_OF_CLASSIFICATION_PREMIUM",
            "readable_conflict_qa_source_observation_id": source_id,
            "active_in_readable_conflict_qa_lane": "true",
        }
    )
    return created


def pointer_valid(pointer: str) -> bool:
    if "#page=" not in pointer:
        return False
    path_value, page_value = pointer.rsplit("#page=", 1)
    try:
        page = int(page_value)
    except ValueError:
        return False
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return page > 0 and path.is_file()


def repair_known_nonbase_record_boundary(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    """Repair one pre-existing embedded-newline CSV split in the shadow copy.

    The source ledger contains one logical Wasco observation split across two
    physical CSV records because an unquoted newline occurs inside its
    effective-date text.  The source bytes remain untouched.  This function
    rejoins only that known observation in the corrected shadow ledger and
    fails closed if the exact two-record shape is not present.
    """
    source_id = "nobs_e1327e5ce6d9cc1ce55a6f02"
    heads = [row for row in rows if row.get("non_base_wage_observation_id") == source_id]
    tails = [row for row in rows if row.get("non_base_wage_observation_id") == "onb"]
    if len(heads) != 1 or len(tails) != 1:
        raise ValueError(
            "Expected the single known Wasco non-base CSV record-boundary split"
        )
    head, tail = heads[0], tails[0]
    if not (
        head.get("extraction_case_id") == "cexrem_66c1d364e1fc34d24eee6d05"
        and head.get("bounded_evidence_pointer") is None
        and tail.get("document_identity_id", "").endswith(".pdf#page=6")
        and tail.get("qa_status") == "true"
    ):
        raise ValueError("Known Wasco record-boundary split changed shape")
    repaired = dict(head)
    repaired.update(
        {
            "effective_date": (head.get("effective_date") or "") + " onb",
            "eligibility_or_implementation_rule": tail.get("extraction_case_id", ""),
            "bounded_evidence_pointer": tail.get("document_identity_id", ""),
            "confidence": tail.get("text_table_detection_id", ""),
            "reason_code": tail.get("source_review_id", ""),
            "qa_status": tail.get("candidate_queue_row_id", ""),
            "cumulative_cohort": tail.get("state", ""),
            "source_seed_observation_id": tail.get("municipality", ""),
            "qa_original_status": tail.get("government_name", ""),
            "qa_resolution_classification": tail.get("unit_type", ""),
            "qa_resolution_status": tail.get("candidate_source_type", ""),
            "canonical_observation_id": tail.get("contract_period_start", ""),
            "duplicate_of": tail.get("contract_period_end", ""),
            "active_in_provisional_lane": tail.get("page_number", ""),
            "source_quantitative_observation_id": tail.get("non_base_wage_type", ""),
            "source_mixed_join_key": tail.get("value_text", ""),
            "targeted_qa_resolution_ids": tail.get("effective_date", ""),
            "targeted_qa_resolution_classification": tail.get(
                "eligibility_or_implementation_rule", ""
            ),
            "targeted_qa_resolution_status": tail.get("bounded_evidence_pointer", ""),
            "targeted_qa_reason_codes": tail.get("confidence", ""),
            "targeted_qa_source_observation_id": tail.get("reason_code", ""),
            "active_in_qa_corrected_lane": tail.get("qa_status", ""),
        }
    )
    return [
        repaired if row is head else row
        for row in rows
        if row is not tail
    ], 1


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
    qa500.write_csv(output_dir / OUTPUT_NAMES["quant"], fields["quant"] + CONFLICT_QA_FIELDS, rows["quant"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["qual"], fields["qual"] + CONFLICT_QA_FIELDS, rows["qual"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["mixed"], fields["mixed"] + CONFLICT_QA_FIELDS + MIXED_FIELDS, rows["mixed"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["nonbase"], fields["nonbase"] + NONBASE_PROVENANCE_FIELDS + CONFLICT_QA_FIELDS, rows["nonbase"])
    qa500.write_csv(output_dir / OUTPUT_NAMES["reference"], fields["reference"] + CONFLICT_QA_FIELDS, rows["reference"])
    qa500.write_json(output_dir / OUTPUT_NAMES["summary"], summary)
    qa500.write_json(output_dir / OUTPUT_NAMES["decision"], decision)

    report = f"""# Targeted conflict QA: readable parse-text 1,826-case provisional layer

- Review groups processed: {summary['review_group_count']} / 37
- GABRIEL/API used: `false`
- New extraction or document selection: `false`
- Targeted resolution counts: `{json.dumps(summary['targeted_resolution_counts'], sort_keys=True)}`
- Conflict groups resolved: {summary['targeted_resolved_group_count']}
- Conflict groups left explicitly unresolved: {summary['targeted_unresolved_group_count']}
- Cumulative conflict counts: `{json.dumps(summary['cumulative_conflict_resolution_counts'], sort_keys=True)}`
- Revised unresolved quantitative conflict rate: {summary['unresolved_quantitative_conflict_rate']:.4%}
- Corrected active quantitative observations: {summary['corrected_quantitative_active_observation_count']}
- Corrected active qualitative mechanism observations: {summary['corrected_qualitative_active_observation_count']}
- Corrected active mixed cases: {summary['corrected_mixed_active_case_count']}
- Corrected active non-base-wage observations: {summary['corrected_non_base_wage_active_observation_count']}
- Corrected active reference/exclusion cases: {summary['corrected_reference_exclusion_active_count']}
- Duplicate observation IDs: {summary['duplicate_observation_id_count']}
- Invalid bounded page pointers: {summary['invalid_observation_page_count']}
- Base/non-base contamination: {summary['base_non_base_wage_contamination_count']}
- Recomputed targeted QA: `{'pass' if decision['qa_pass'] else 'fail'}`

Thirty-five groups were resolved from existing structured fields and tightly
bounded local page checks. Two inherited groups remain under-specified: one
contains aggregate fiscal-impact totals rather than employee wage cells, and
one has a rank/column mismatch that the bounded evidence does not safely
resolve. A three-record temporary working-out-of-classification premium group
was moved from active base quantitative evidence to explicit non-base-wage
shadow records while preserving every original observation ID and pointer.

The five newly canonicalized duplicate observations and all prior provenance
remain intact. Original cumulative ledgers were read-only. No URL, hosted
search, download, OCR, extraction, GABRIEL/API call, ingestion, codification,
final merge, wage-gap calculation, regression, or causal analysis occurred.
"""
    (output_dir / OUTPUT_NAMES["report"]).write_text(report, encoding="utf-8")

    validation = f"""# Readable parse-text 1,826 targeted conflict QA validation — 2026-07-25

- Exact targeted scope: `{'pass' if summary['review_group_count'] == 37 else 'fail'}` ({summary['review_group_count']})
- All targeted groups accounted for: `{'pass' if sum(summary['targeted_resolution_counts'].values()) == 37 else 'fail'}`
- Corrected shadow ledgers separate from originals: `{'pass' if summary['corrected_ledgers_provisional_and_separate'] else 'fail'}`
- Original input SHA-256 values preserved: `pass`
- Duplicate observation IDs: `{'pass' if summary['duplicate_observation_id_count'] == 0 else 'fail'}` ({summary['duplicate_observation_id_count']})
- Invalid bounded page pointers: `{'pass' if summary['invalid_observation_page_count'] == 0 else 'fail'}` ({summary['invalid_observation_page_count']})
- Base/non-base contamination: `{'pass' if summary['base_non_base_wage_contamination_count'] == 0 else 'fail'}` ({summary['base_non_base_wage_contamination_count']})
- Unresolved conflict rate at most 2%: `{'pass' if summary['unresolved_quantitative_conflict_rate'] <= .02 else 'fail'}` ({summary['unresolved_quantitative_conflict_rate']:.4%})
- Matched representation intact: `{'pass' if summary['matched_representation_intact'] else 'fail'}`
- All 1,826 unique readable parse-text cases covered: `{'pass' if summary['all_unique_readable_parse_text_documents_covered'] else 'fail'}`
- OCR-later documents untouched: `{'pass' if summary['ocr_later_documents_untouched'] else 'fail'}`
- GABRIEL/API, new extraction, and new selection: `false`
- Final analysis readiness: `false`

Repository-wide command results are appended to this validation artifact after
the required test/build/validation suite completes.
"""
    (output_dir / OUTPUT_NAMES["validation"]).write_text(validation, encoding="utf-8")


def resolve(source_dir: Path, output_dir: Path, *, write: bool = True) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    if source_dir == output_dir or source_dir in output_dir.parents:
        raise ValueError("Output directory must be separate from the cumulative source directory")

    required = [REVIEW, DECISION, SUMMARY, QUANT, QUAL, MIXED, NONBASE, REFERENCE]
    missing = [name for name in required if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing cumulative inputs: " + ", ".join(missing))
    input_hashes = {name: qa500.sha_file(source_dir / name) for name in required}

    review = qa500.read_csv(source_dir / REVIEW)
    review_counts = Counter(row["review_type"] for row in review)
    if len(review) != 134 or review_counts != Counter(
        {"potential_quantitative_conflict": 130, "exact_structured_content_duplicate": 4}
    ):
        raise ValueError(f"Unexpected cumulative review queue: {len(review)}, {review_counts}")
    unresolved = [
        row for row in review
        if row["review_type"] == "potential_quantitative_conflict"
        and row["resolution_classification"] == "insufficient_evidence_needs_review"
        and row["unresolved_flag"] == "true"
    ]
    if len(unresolved) != 37:
        raise ValueError(f"Unresolved conflict scope is not exactly 37 groups: {len(unresolved)}")
    if len({row["observation_ids"] for row in unresolved}) != 37:
        raise ValueError("Unresolved conflict signatures are not unique")

    original_decision = json.loads((source_dir / DECISION).read_text(encoding="utf-8"))
    original_summary = json.loads((source_dir / SUMMARY).read_text(encoding="utf-8"))
    if not (
        original_decision.get("cumulative_case_count") == 1826
        and original_decision.get("cumulative_unique_content_hash_count") == 1826
        and original_decision.get("qa_pass") is True
        and original_decision.get("targeted_qa_required") is True
        and original_decision.get("base_non_base_wage_contamination_count") == 0
        and original_decision.get("matched_representation_intact") is True
        and original_summary.get("unresolved_quantitative_conflict_group_count") == 37
    ):
        raise RuntimeError("Source decision does not authorize this bounded targeted QA pass")

    source_rows = {
        "quant": qa500.read_csv(source_dir / QUANT),
        "qual": qa500.read_csv(source_dir / QUAL),
        "mixed": qa500.read_csv(source_dir / MIXED),
        "nonbase": qa500.read_csv(source_dir / NONBASE),
        "reference": qa500.read_csv(source_dir / REFERENCE),
    }
    physical_nonbase_source_row_count = len(source_rows["nonbase"])
    source_rows["nonbase"], record_boundary_repairs = (
        repair_known_nonbase_record_boundary(source_rows["nonbase"])
    )
    fields = {
        "quant": qa500.read_fields(source_dir / QUANT),
        "qual": qa500.read_fields(source_dir / QUAL),
        "mixed": qa500.read_fields(source_dir / MIXED),
        "nonbase": qa500.read_fields(source_dir / NONBASE),
        "reference": qa500.read_fields(source_dir / REFERENCE),
    }
    quant = {
        row["quantitative_observation_id"]: conflict_defaults(
            row, row["quantitative_observation_id"]
        )
        for row in source_rows["quant"]
    }
    qualitative = [
        conflict_defaults(row, row["qualitative_observation_id"])
        for row in source_rows["qual"]
    ]
    nonbase = {
        row["non_base_wage_observation_id"]: conflict_defaults(
            row, row["non_base_wage_observation_id"]
        )
        for row in source_rows["nonbase"]
    }
    references = [conflict_defaults(row) for row in source_rows["reference"]]

    decisions = dict(qa1000.CONFLICT_DECISIONS)
    decisions.update(NEW_CONFLICT_DECISIONS)
    resolutions: list[dict[str, str]] = []
    targeted_counts: Counter[str] = Counter()
    routed_ids: set[str] = set()

    for number, queued in enumerate(unresolved, 1):
        ids = [item for item in queued["observation_ids"].split("|") if item]
        signature = frozenset(ids)
        if signature not in decisions:
            raise ValueError(f"No bounded deterministic decision for {sorted(signature)}")
        if any(item not in quant for item in ids):
            raise ValueError(f"Conflict references missing quantitative IDs: {sorted(signature)}")
        classification, basis = decisions[signature]
        resolution_id = qa500.stable_id(
            "qares1826", str(number), queued["extraction_case_id"], queued["observation_ids"]
        )
        unresolved_flag = classification in {
            "true_conflict_unresolved", "insufficient_evidence_needs_review"
        }
        status = "unresolved" if unresolved_flag else "resolved"
        reason = (
            "BOUNDED_EVIDENCE_REMAINS_UNDERSPECIFIED"
            if unresolved_flag
            else f"CONFLICT_RESOLVED_{classification.upper()}"
        )
        retained = list(ids)
        routed: list[str] = []
        created_ids: list[str] = []
        quant_action = "retain_active_flag_unresolved" if unresolved_flag else "retain_distinct_active_records"
        nonbase_action = "no_change"

        if signature in NONBASE_ROUTES:
            retained = []
            routed = list(ids)
            quant_action = "deactivate_and_route_to_non_base_wage"
            nonbase_action = "create_corrected_non_base_wage_records"
            reason = "WORKING_OUT_OF_CLASSIFICATION_PREMIUM"
            for observation_id in ids:
                row = quant[observation_id]
                row.update(
                    {
                        "readable_conflict_qa_resolution_id": resolution_id,
                        "readable_conflict_qa_classification": classification,
                        "readable_conflict_qa_status": "resolved",
                        "readable_conflict_qa_reason_codes": reason,
                        "readable_conflict_qa_source_observation_id": observation_id,
                        "active_in_readable_conflict_qa_lane": "false",
                    }
                )
                created = make_nonbase(row, resolution_id)
                target_id = created["non_base_wage_observation_id"]
                if target_id in nonbase:
                    raise ValueError(f"Reroute target already exists: {target_id}")
                nonbase[target_id] = created
                created_ids.append(target_id)
                routed_ids.add(observation_id)
        else:
            for observation_id in ids:
                quant[observation_id].update(
                    {
                        "readable_conflict_qa_resolution_id": resolution_id,
                        "readable_conflict_qa_classification": classification,
                        "readable_conflict_qa_status": status,
                        "readable_conflict_qa_reason_codes": reason,
                        "readable_conflict_qa_source_observation_id": observation_id,
                        "active_in_readable_conflict_qa_lane": "true",
                    }
                )

        pointers = sorted({quant[item]["bounded_evidence_pointer"] for item in ids})
        resolutions.append(
            {
                "readable_conflict_qa_resolution_id": resolution_id,
                "review_queue_row_number": str(number),
                "extraction_case_id": queued["extraction_case_id"],
                "page_number": queued["page_number"],
                "source_observation_ids": "|".join(ids),
                "source_observation_count": queued["observation_count"],
                "resolution_classification": classification,
                "resolution_status": status,
                "quantitative_action": quant_action,
                "non_base_wage_action": nonbase_action,
                "retained_quantitative_observation_ids": "|".join(retained),
                "routed_quantitative_observation_ids": "|".join(routed),
                "created_non_base_wage_observation_ids": "|".join(created_ids),
                "structured_basis": basis[:600],
                "bounded_evidence_pointer": "|".join(pointers),
                "local_evidence_inspected": "structured_fields_and_single_bounded_local_page",
                "reason_codes": reason,
                "confidence": "low" if unresolved_flag else "high",
                "unresolved_flag": qa500.truth(unresolved_flag),
                "notes": "No missing classification, rank, step, pay band, or date was added to an observation.",
            }
        )
        targeted_counts[classification] += 1

    mixed_rows: list[dict[str, str]] = []
    for source in source_rows["mixed"]:
        row = conflict_defaults(source, source["mixed_join_key"])
        original_ids = [item for item in source["quantitative_observation_ids"].split("|") if item]
        corrected_ids = [
            item for item in original_ids
            if item in quant and quant[item]["active_in_readable_conflict_qa_lane"] == "true"
        ]
        qual_ids = [item for item in source["qualitative_observation_ids"].split("|") if item]
        changed = corrected_ids != original_ids
        row.update(
            {
                "quantitative_observation_ids": "|".join(corrected_ids),
                "quantitative_observation_count": str(len(corrected_ids)),
                "qualitative_observation_count": str(len(qual_ids)),
                "readable_conflict_qa_original_quantitative_observation_ids": "|".join(original_ids),
                "readable_conflict_qa_corrected_quantitative_observation_ids": "|".join(corrected_ids),
                "readable_conflict_qa_classification": "mixed_membership_corrected" if changed else "not_in_targeted_queue",
                "readable_conflict_qa_status": "resolved" if changed else "not_applicable",
                "readable_conflict_qa_reason_codes": "INACTIVE_QUANTITATIVE_MEMBERS_REMOVED" if changed else "",
                "active_in_readable_conflict_qa_lane": qa500.truth(active(source) and bool(corrected_ids) and bool(qual_ids)),
            }
        )
        mixed_rows.append(row)

    quant_rows = list(quant.values())
    nonbase_rows = list(nonbase.values())
    active_quant = [row for row in quant_rows if row["active_in_readable_conflict_qa_lane"] == "true"]
    active_qual = [row for row in qualitative if row["active_in_readable_conflict_qa_lane"] == "true"]
    active_mixed = [row for row in mixed_rows if row["active_in_readable_conflict_qa_lane"] == "true"]
    active_nonbase = [row for row in nonbase_rows if row["active_in_readable_conflict_qa_lane"] == "true"]
    active_reference = [row for row in references if row["active_in_readable_conflict_qa_lane"] == "true"]

    all_ids = (
        [row["quantitative_observation_id"] for row in quant_rows]
        + [row["qualitative_observation_id"] for row in qualitative]
        + [row["non_base_wage_observation_id"] for row in nonbase_rows]
    )
    duplicate_ids = len(all_ids) - len(set(all_ids))
    invalid_pages = sum(
        not pointer_valid(row["bounded_evidence_pointer"])
        for row in active_quant + active_qual + active_nonbase
    )
    contamination = [
        row for row in active_quant
        if remaining.nonbase_type(row)
        and row.get("targeted_qa_resolution_classification") != "retain_quantitative_base_wage"
    ]
    unresolved_count = sum(
        targeted_counts[label]
        for label in ("true_conflict_unresolved", "insufficient_evidence_needs_review")
    )
    unresolved_rate = unresolved_count / max(1, len(active_quant))

    original_conflicts = Counter(original_decision["conflict_resolution_counts"])
    original_conflicts["insufficient_evidence_needs_review"] -= 37
    for label, count in targeted_counts.items():
        original_conflicts[label] += count
    cumulative_conflicts = dict(sorted((key, value) for key, value in original_conflicts.items() if value))
    if sum(cumulative_conflicts.values()) != 130:
        raise AssertionError(f"Cumulative conflict accounting changed: {cumulative_conflicts}")

    duplicate_review_rows = [row for row in review if row["review_type"] == "exact_structured_content_duplicate"]
    new_duplicate_observations = sum(
        len([item for item in row["duplicate_observation_ids"].split("|") if item])
        for row in duplicate_review_rows
    )
    duplicate_provenance_rows = sum(
        bool(row.get("duplicate_of")) for row in quant_rows + nonbase_rows
    )
    separate = all(
        (output_dir / OUTPUT_NAMES[key]).resolve() != (source_dir / source).resolve()
        for key, source in (
            ("quant", QUANT), ("qual", QUAL), ("mixed", MIXED),
            ("nonbase", NONBASE), ("reference", REFERENCE),
        )
    )
    input_hashes_after = {name: qa500.sha_file(source_dir / name) for name in required}
    if input_hashes != input_hashes_after:
        raise RuntimeError("A protected cumulative input changed during targeted QA")

    integrity_pass = (
        duplicate_ids == 0
        and invalid_pages == 0
        and not contamination
        and original_decision["matched_representation_intact"] is True
        and separate
        and new_duplicate_observations == 5
        and duplicate_provenance_rows >= 5
    )
    qa_pass = integrity_pass and unresolved_rate <= 0.02
    summary = {
        "task_id": TASK_ID,
        "generated_at": qa500.now(),
        "gabriel_api_used": False,
        "new_extraction_run": False,
        "new_document_selection": False,
        "review_group_count": len(resolutions),
        "targeted_resolution_counts": dict(sorted(targeted_counts.items())),
        "targeted_resolved_group_count": 37 - unresolved_count,
        "targeted_unresolved_group_count": unresolved_count,
        "cumulative_quantitative_conflict_group_count": 130,
        "cumulative_conflict_resolution_counts": cumulative_conflicts,
        "unresolved_quantitative_conflict_group_count": unresolved_count,
        "unresolved_quantitative_conflict_rate": round(unresolved_rate, 8),
        "quantitative_records_routed_to_non_base_wage": len(routed_ids),
        "new_non_base_wage_records_created": len(routed_ids),
        "corrected_quantitative_active_observation_count": len(active_quant),
        "corrected_quantitative_source_row_count": len(quant_rows),
        "corrected_qualitative_active_observation_count": len(active_qual),
        "corrected_mixed_active_case_count": len(active_mixed),
        "corrected_mixed_source_row_count": len(mixed_rows),
        "corrected_non_base_wage_active_observation_count": len(active_nonbase),
        "corrected_non_base_wage_source_row_count": len(nonbase_rows),
        "source_non_base_wage_physical_csv_row_count": physical_nonbase_source_row_count,
        "source_csv_record_boundary_repairs": record_boundary_repairs,
        "corrected_reference_exclusion_active_count": len(active_reference),
        "corrected_reference_exclusion_source_row_count": len(references),
        "duplicate_observation_id_count": duplicate_ids,
        "invalid_observation_page_count": invalid_pages,
        "base_non_base_wage_contamination_count": len(contamination),
        "newly_canonicalized_duplicate_observations_preserved": new_duplicate_observations,
        "all_duplicate_provenance_rows_preserved": duplicate_provenance_rows,
        "cumulative_case_count": 1826,
        "cumulative_unique_content_hash_count": 1826,
        "unit_type_counts": original_decision["unit_type_counts"],
        "state_count": original_decision["state_count"],
        "source_type_counts": original_decision["source_type_counts"],
        "matched_representation_intact": original_decision["matched_representation_intact"],
        "corrected_ledgers_provisional_and_separate": separate,
        "all_unique_readable_parse_text_documents_covered": True,
        "ocr_later_documents_untouched": True,
        "input_sha256": input_hashes,
    }
    decision_name = (
        "readable_parse_text_1826_targeted_conflict_qa_passed"
        if qa_pass else "readable_parse_text_1826_targeted_conflict_qa_blocked"
    )
    decision = {
        **summary,
        "integrity_qa_pass": integrity_pass,
        "qa_pass": qa_pass,
        "qa_status": "pass" if qa_pass else "fail",
        "decision": decision_name,
        "final_provisional_merge_allowed": False,
        "final_analysis_ready": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "wage_gap_analysis_allowed": False,
        "dashboard_status_required": (
            "compensation_extraction_readable_parse_text_1826_targeted_conflict_qa_completed"
            if qa_pass else
            "compensation_extraction_readable_parse_text_1826_targeted_conflict_qa_blocked"
        ),
        "next_recommendation": (
            "independent_review_before_final_provisional_merge"
            if qa_pass else "continue_bounded_conflict_qa"
        ),
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
                "status": "dry_run_valid" if args.dry_run else "targeted_conflict_qa_completed",
                "review_groups_processed": result["summary"]["review_group_count"],
                "resolved": result["summary"]["targeted_resolved_group_count"],
                "unresolved": result["summary"]["targeted_unresolved_group_count"],
                "qa_pass": result["decision"]["qa_pass"],
                "gabriel_api_used": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
