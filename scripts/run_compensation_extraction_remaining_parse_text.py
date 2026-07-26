#!/usr/bin/env python3
"""Freeze and run the bounded remaining-readable parse-text extraction batch."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_compensation_evidence_extraction as base
from run_compensation_extraction_targeted_qa import (
    conflict_resolution,
    nonbase_type,
)


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-EXTRACTION-REMAINING-PARSE-TEXT-826-2026-07-25"
OUTPUT_ID = "COMPENSATION-EVIDENCE-EXTRACTION-REMAINING-PARSE-TEXT-826-2026-07-25"
EXPECTED_NEW = 826
EXPECTED_SEED = 1000
EXPECTED_CUMULATIVE = 1826

SEED_DIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-TARGETED-QA-2026-07-25"
)
FROZEN_1000_SELECTION = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25/"
    "compensation_extraction_1000_selection_manifest.csv"
)
FROZEN_1000_PACKET = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25/"
    "compensation_extraction_1000_packet_manifest.csv"
)

SELECTION_FIELDS = base.SELECTION_1000_FIELDS + [
    "inventory_rows_for_content_hash",
    "duplicate_hash_representative_rule",
    "excluded_duplicate_detection_ids",
]
PACKET_FIELDS = base.PACKET_1000_FIELDS

SEED_PATHS = {
    "quant": "quantitative_extraction_ledger_qa_corrected.csv",
    "qual": "qualitative_mechanism_extraction_ledger_qa_corrected.csv",
    "mixed": "mixed_extraction_ledger_qa_corrected.csv",
    "nonbase": "non_base_wage_compensation_ledger_qa_corrected.csv",
    "refs": "reference_exclusion_ledger_qa_corrected.csv",
}
NEW_PATHS = {
    "quant": "lanes_new/quantitative/quantitative_extraction_ledger.csv",
    "qual": "lanes_new/qualitative/qualitative_mechanism_extraction_ledger.csv",
    "mixed": "lanes_new/mixed/mixed_extraction_ledger.csv",
    "nonbase": "lanes_new/non_base_wage/non_base_wage_compensation_ledger.csv",
    "refs": "lanes_new/reference_and_exclusion/reference_exclusion_ledger.csv",
}
CUMULATIVE_PATHS = {
    "quant": "cumulative_readable_parse_text_quantitative_ledger.csv",
    "qual": "cumulative_readable_parse_text_qualitative_mechanism_ledger.csv",
    "mixed": "cumulative_readable_parse_text_mixed_ledger.csv",
    "nonbase": "cumulative_readable_parse_text_non_base_wage_ledger.csv",
    "refs": "cumulative_readable_parse_text_reference_exclusion_ledger.csv",
}
ID_FIELDS = {
    "quant": "quantitative_observation_id",
    "qual": "qualitative_observation_id",
    "mixed": "mixed_join_key",
    "nonbase": "non_base_wage_observation_id",
    "refs": "extraction_case_id",
}
BASE_FIELDS = {
    "quant": base.QUANT_FIELDS,
    "qual": base.QUAL_FIELDS,
    "mixed": base.MIXED_FIELDS,
    "nonbase": base.NONBASE_FIELDS,
    "refs": base.REFERENCE_FIELDS,
}
REVIEW_FIELDS = base.CONFLICT_1000_FIELDS


def read_csv_with_fields(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def active(row: dict[str, str]) -> bool:
    final_flag = row.get("active_in_qa_corrected_lane", "")
    if final_flag:
        return final_flag == "true"
    return row.get("active_in_provisional_lane", "true") == "true"


def require_authority(seed_dir: Path) -> dict[str, Any]:
    decision = base.read_json(
        seed_dir / "compensation_extraction_1000_recomputed_decision.json"
    )
    if not (
        decision.get("decision")
        == "remaining_readable_parse_text_extraction_allowed"
        and decision.get("integrity_qa_pass") is True
        and decision.get("remaining_readable_parse_text_extraction_allowed") is True
        and decision.get("unresolved_base_non_base_contamination_count") == 0
        and float(decision.get("unresolved_quantitative_conflict_rate", 1)) <= 0.02
        and decision.get("corrected_ledgers_provisional_and_separate") is True
    ):
        raise RuntimeError("corrected 1,000-document authority does not permit this run")
    for relative in SEED_PATHS.values():
        if not (seed_dir / relative).is_file():
            raise RuntimeError(f"corrected seed ledger missing: {relative}")
    return decision


def eligible_raw_rows(remaining_hashes: set[str]) -> list[dict[str, str]]:
    readiness = {r["pdf_readiness_id"]: r for r in base.read_csv(base.READINESS)}
    source_ids = {r["source_review_id"] for r in base.read_csv(base.SOURCE_REVIEW)}
    rows: list[dict[str, str]] = []
    for row in base.read_csv(base.DETECTION):
        if row.get("content_hash") not in remaining_hashes:
            continue
        ready = readiness.get(row.get("pdf_readiness_id", ""), {})
        artifact = Path(row.get("content_artifact_path", ""))
        if not artifact.is_absolute():
            artifact = ROOT / artifact
        if (
            row.get("source_review_id") in source_ids
            and row.get("detection_status") == "detection_checked"
            and row.get("text_layer_status") in {"present", "partial"}
            and ready.get("readiness_status") == "readiness_checked"
            and ready.get("artifact_exists") == "yes"
            and ready.get("artifact_hash_verified") == "yes"
            and ready.get("pdf_signature_valid") == "yes"
            and ready.get("ocr_needed_signal") == "no"
            and artifact.is_file()
        ):
            rows.append(row)
    return rows


def freeze_selection(output: Path, seed_dir: Path, limit: int) -> list[dict[str, str]]:
    if limit != EXPECTED_NEW:
        raise ValueError(f"remaining selection requires exactly {EXPECTED_NEW} cases")
    require_authority(seed_dir)
    frozen = base.read_csv(FROZEN_1000_SELECTION)
    frozen_hashes = {row["content_hash"] for row in frozen}
    if len(frozen) != EXPECTED_SEED or len(frozen_hashes) != EXPECTED_SEED:
        raise RuntimeError("frozen 1,000-document selection is not unique and complete")

    eligible, _ = base.load_inputs(base.GATE3)
    remaining = [row for row in eligible if row["content_hash"] not in frozen_hashes]
    if len(remaining) != EXPECTED_NEW:
        raise RuntimeError(
            f"expected {EXPECTED_NEW} unique remaining hashes, found {len(remaining)}"
        )
    remaining_hashes = {row["content_hash"] for row in remaining}
    if len(remaining_hashes) != EXPECTED_NEW:
        raise RuntimeError("remaining eligible inventory contains duplicate chosen hashes")
    raw = eligible_raw_rows(remaining_hashes)
    raw_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        raw_by_hash[row["content_hash"]].append(row)
    if len(raw) != 827 or len(raw_by_hash) != EXPECTED_NEW:
        raise RuntimeError(
            f"remaining inventory discrepancy changed: {len(raw)} rows / "
            f"{len(raw_by_hash)} hashes"
        )
    duplicate_groups = {
        value: rows for value, rows in raw_by_hash.items() if len(rows) > 1
    }
    if len(duplicate_groups) != 1 or sum(len(v) - 1 for v in duplicate_groups.values()) != 1:
        raise RuntimeError("expected exactly one duplicated remaining content hash")

    seed_partner: dict[tuple[str, str], str] = {
        (row["state"], row["municipality"]): row["extraction_case_id"]
        for row in frozen
        if row["unit_type"] == "non_safety"
    }
    case_by_hash = {
        row["content_hash"]: base.stable_id(
            "cexrem", TASK_ID, row["text_table_detection_id"]
        )
        for row in remaining
    }
    partner_by_group = dict(seed_partner)
    for row in remaining:
        if row["unit_type"] == "non_safety":
            partner_by_group[(row["state"], row["municipality"])] = case_by_hash[
                row["content_hash"]
            ]

    ordered = sorted(
        remaining,
        key=lambda row: (
            row["state"],
            row["municipality"],
            row["unit_type"],
            -float(row["_score"]),
            row["text_table_detection_id"],
        ),
    )
    output_rows: list[dict[str, str]] = []
    for rank, row in enumerate(ordered, 1):
        review = row["_source"]
        g3 = row["_gate3"]
        group = (row["state"], row["municipality"])
        candidates = sorted(
            raw_by_hash[row["content_hash"]],
            key=lambda item: item["text_table_detection_id"],
        )
        excluded = [
            item["text_table_detection_id"]
            for item in candidates
            if item["text_table_detection_id"] != row["text_table_detection_id"]
        ]
        reasons = [
            "LOCAL_RETAINED_VERIFIED",
            "TEXT_LAYER_READABLE",
            "OUTSIDE_FROZEN_1000_HASHES",
            "TARGETED_QA_ROUTING_V2",
            "FINAL_READABLE_PARSE_TEXT_BATCH",
        ]
        if row["wage_table_signal"] == "likely":
            reasons.append("LIKELY_P1_PRIORITY")
        if group in partner_by_group:
            reasons.append("MATCHED_NON_SAFETY_OPPORTUNITY")
        if excluded:
            reasons.append("DUPLICATE_HASH_REPRESENTATIVE")
        output_rows.append(
            {
                "selection_rank": str(rank),
                "extraction_case_id": case_by_hash[row["content_hash"]],
                "document_identity_id": base.stable_id("doc", row["content_hash"]),
                "text_table_detection_id": row["text_table_detection_id"],
                "pdf_readiness_id": row["pdf_readiness_id"],
                "source_review_id": row["source_review_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "triage_id": row["triage_id"],
                "verification_id": row["verification_id"],
                "state": row["state"],
                "municipality": row["municipality"],
                "government_name": row["government_name"],
                "unit_type": row["unit_type"],
                "candidate_source_type": row["candidate_source_type"],
                "contract_period_start": review.get(
                    "contract_or_document_period_start", ""
                ),
                "contract_period_end": review.get(
                    "contract_or_document_period_end", ""
                ),
                "content_artifact_path": row["content_artifact_path"],
                "content_hash": row["content_hash"],
                "pdf_page_count": row["pdf_page_count"],
                "text_layer_status": row["text_layer_status"],
                "wage_table_signal": row["wage_table_signal"],
                "extraction_pilot_priority": row["extraction_pilot_priority"],
                "candidate_wage_pages": row["candidate_wage_pages"],
                "selection_score": f"{float(row['_score']):.3f}",
                "selection_reason_codes": "|".join(reasons),
                "matched_group_id": base.stable_id(
                    "match", row["state"], row["municipality"]
                ),
                "matched_non_safety_selected": "yes"
                if group in partner_by_group
                else "no",
                "matched_non_safety_case_id": partner_by_group.get(group, ""),
                "planned_lane": "pending_packet_features",
                "gate3_category": g3.get("compensation_evidence_category", ""),
                "gate3_confidence": g3.get("gate3_confidence", ""),
                "existing_rendered_page_count": "0",
                "selection_status": "frozen_remaining_requires_api",
                "cumulative_cohort": "remaining_parse_text_826_new",
                "requires_gabriel": "yes",
                "seed_selection_rank": "",
                "inventory_rows_for_content_hash": str(len(candidates)),
                "duplicate_hash_representative_rule": (
                    "highest_evidence_score_then_detection_id"
                    if excluded
                    else "single_eligible_identity"
                ),
                "excluded_duplicate_detection_ids": "|".join(excluded),
            }
        )
    if (
        len(output_rows) != EXPECTED_NEW
        or len({row["content_hash"] for row in output_rows}) != EXPECTED_NEW
        or {row["content_hash"] for row in output_rows} & frozen_hashes
    ):
        raise RuntimeError("remaining selection identity/hash exclusion gate failed")
    base.write_csv(
        output / "remaining_parse_text_selection_manifest.csv",
        SELECTION_FIELDS,
        output_rows,
    )
    return output_rows


def freeze_packets(
    output: Path, selection: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[base.PagePacket]]]:
    renders = base.render_lookup()
    packet_rows: list[dict[str, str]] = []
    packet_map: dict[str, list[base.PagePacket]] = {}
    for row in selection:
        pages = base.build_packet(row, renders)
        packet_map[row["extraction_case_id"]] = pages
        row["planned_lane"] = base.planned_lane(pages)
        row["existing_rendered_page_count"] = str(sum(bool(page.image) for page in pages))
        total = sum(len(page.text) for page in pages)
        for page in pages:
            packet_rows.append(
                {
                    "extraction_case_id": row["extraction_case_id"],
                    "document_identity_id": row["document_identity_id"],
                    "text_table_detection_id": row["text_table_detection_id"],
                    "page_number": str(page.page),
                    "page_role": page.role,
                    "bounded_evidence_pointer": (
                        f"{row['content_artifact_path']}#page={page.page}"
                    ),
                    "text_chars": str(len(page.text)),
                    "wage_term_count": str(page.wage),
                    "numeric_token_count": str(page.numeric),
                    "table_like_line_count": str(page.table),
                    "qualitative_mechanism_term_count": str(page.qual),
                    "non_base_wage_term_count": str(page.nonbase),
                    "reference_signal": "yes" if page.reference else "no",
                    "rendered_image_available": "yes" if page.image else "no",
                    "rendered_image_path": page.image,
                    "packet_page_count": str(len(pages)),
                    "packet_text_chars": str(total),
                    "packet_status": "bounded_valid",
                    "cumulative_cohort": "remaining_parse_text_826_new",
                }
            )
    base.write_csv(
        output / "remaining_parse_text_selection_manifest.csv",
        SELECTION_FIELDS,
        selection,
    )
    base.write_csv(
        output / "remaining_parse_text_packet_manifest.csv",
        PACKET_FIELDS,
        packet_rows,
    )
    return packet_rows, packet_map


def write_freeze_outputs(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    seed_dir: Path,
) -> None:
    manifest = output / "remaining_parse_text_selection_manifest.csv"
    digest = base.sha_file(manifest)
    (output / "remaining_parse_text_selection_sha256.txt").write_text(
        f"{digest}  {manifest.name}\n", encoding="utf-8"
    )
    duplicate_rows = [
        row for row in selection if int(row["inventory_rows_for_content_hash"]) > 1
    ]
    summary = {
        "task_id": TASK_ID,
        "status": "frozen_no_gabriel_calls",
        "remaining_inventory_row_count": 827,
        "selection_count": len(selection),
        "unique_content_hash_count": len({row["content_hash"] for row in selection}),
        "unique_document_identity_count": len(
            {row["document_identity_id"] for row in selection}
        ),
        "duplicate_hash_group_count": len(duplicate_rows),
        "duplicate_extra_row_count": 1,
        "duplicate_hash": duplicate_rows[0]["content_hash"],
        "duplicate_hash_selected_detection_id": duplicate_rows[0][
            "text_table_detection_id"
        ],
        "duplicate_hash_excluded_detection_ids": duplicate_rows[0][
            "excluded_duplicate_detection_ids"
        ].split("|"),
        "corrected_1000_seed_count": EXPECTED_SEED,
        "seed_gabriel_calls": 0,
        "new_gabriel_required_count": len(selection),
        "unit_type_counts": dict(Counter(row["unit_type"] for row in selection)),
        "state_count": len({row["state"] for row in selection}),
        "state_counts": dict(Counter(row["state"] for row in selection)),
        "source_type_counts": dict(
            Counter(row["candidate_source_type"] for row in selection)
        ),
        "priority_counts": dict(
            Counter(row["extraction_pilot_priority"] for row in selection)
        ),
        "planned_lane_counts": dict(Counter(row["planned_lane"] for row in selection)),
        "matched_non_safety_opportunity_count": sum(
            row["matched_non_safety_selected"] == "yes" for row in selection
        ),
        "manifest_sha256": digest,
        "frozen_1000_selection_sha256": base.sha_file(FROZEN_1000_SELECTION),
        "targeted_qa_decision_sha256": base.sha_file(
            seed_dir / "compensation_extraction_1000_recomputed_decision.json"
        ),
        "gabriel_calls": 0,
    }
    base.write_json(output / "remaining_parse_text_selection_summary.json", summary)
    packet_summary = {
        "case_count": len({row["extraction_case_id"] for row in packet_rows}),
        "packet_page_rows": len(packet_rows),
        "max_pages_per_case": max(int(row["packet_page_count"]) for row in packet_rows),
        "max_text_chars_per_page": max(int(row["text_chars"]) for row in packet_rows),
        "max_text_chars_per_case": max(int(row["packet_text_chars"]) for row in packet_rows),
        "rendered_page_available_count": sum(
            row["rendered_image_available"] == "yes" for row in packet_rows
        ),
        "full_text_saved": False,
        "full_tables_saved": False,
        "raw_prompts_saved": False,
        "raw_responses_saved": False,
        "encoded_images_saved": False,
    }
    base.write_json(output / "remaining_parse_text_packet_summary.json", packet_summary)
    audit = f"""# Remaining readable parse-text selection audit

- Durable remaining rows outside the frozen 1,000 hashes: 827
- Frozen unique remaining content hashes: {len(selection)}
- Corrected 1,000-document seed retained without GABRIEL: 1,000
- New GABRIEL-required cases: {len(selection)}
- Units: `{json.dumps(summary['unit_type_counts'], sort_keys=True)}`
- States/DC represented: {summary['state_count']}
- Priorities: `{json.dumps(summary['priority_counts'], sort_keys=True)}`
- Source families: `{json.dumps(summary['source_type_counts'], sort_keys=True)}`
- Matched non-safety opportunities retained: {summary['matched_non_safety_opportunity_count']}
- Packet page rows: {packet_summary['packet_page_rows']}
- Maximum pages per case: {packet_summary['max_pages_per_case']}
- Maximum text characters per page/case: {packet_summary['max_text_chars_per_page']} / {packet_summary['max_text_chars_per_case']}
- Selection SHA-256: `{digest}`

The 827-row / 826-hash discrepancy is one exact retained-content duplicate in
North Miami, Florida. Both durable rows point to the same SHA-256
`{summary['duplicate_hash']}`. The selected representative is
`{summary['duplicate_hash_selected_detection_id']}`; the excluded duplicate
detection identity is `{summary['duplicate_hash_excluded_detection_ids'][0]}`.
The deterministic rule selects the highest evidence score and then the lexical
detection ID. The duplicate hash is sent once, not twice, and both identities
remain documented here and in the selection summary.

The freeze made no GABRIEL/API calls and saved no full document/page text,
full table, raw prompt/response, or encoded image copy. OCR-later documents and
all hashes in the frozen 1,000-document selection are excluded.
"""
    (output / "remaining_parse_text_selection_audit.md").write_text(
        audit, encoding="utf-8"
    )


def load_selection(output: Path) -> list[dict[str, str]]:
    path = output / "remaining_parse_text_selection_manifest.csv"
    rows = base.read_csv(path)
    digest = (output / "remaining_parse_text_selection_sha256.txt").read_text(
        encoding="utf-8"
    ).split()[0]
    frozen_hashes = {row["content_hash"] for row in base.read_csv(FROZEN_1000_SELECTION)}
    if (
        len(rows) != EXPECTED_NEW
        or len({row["content_hash"] for row in rows}) != EXPECTED_NEW
        or len({row["extraction_case_id"] for row in rows}) != EXPECTED_NEW
        or sha_file(path) != digest
        or {row["content_hash"] for row in rows} & frozen_hashes
        or any(row["requires_gabriel"] != "yes" for row in rows)
    ):
        raise RuntimeError("frozen remaining selection integrity failure")
    return rows


def sha_file(path: Path) -> str:
    return base.sha_file(path)


def packet_rows_and_map(
    output: Path, selection: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, list[base.PagePacket]]]:
    existing = base.read_csv(output / "remaining_parse_text_packet_manifest.csv")
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in existing:
        by_case[row["extraction_case_id"]].append(row)
    renders = base.render_lookup()
    packet_map: dict[str, list[base.PagePacket]] = {}
    for row in selection:
        pages = base.build_packet(row, renders)
        expected = {
            (int(item["page_number"]), item["text_chars"])
            for item in by_case[row["extraction_case_id"]]
        }
        if {(page.page, str(len(page.text))) for page in pages} != expected:
            raise RuntimeError("remaining packet reconstruction differs from freeze")
        packet_map[row["extraction_case_id"]] = pages
    if len(packet_map) != EXPECTED_NEW:
        raise RuntimeError("packet reconstruction did not yield 826 cases")
    if not all(
        int(row["packet_page_count"]) <= 6
        and int(row["packet_text_chars"]) <= 6000
        and int(row["text_chars"]) <= 1500
        for row in existing
    ):
        raise RuntimeError("bounded packet caps violated")
    return existing, packet_map


def role_score(row: dict[str, str], pages: list[base.PagePacket], role: str) -> tuple[int, str]:
    values = {
        "quantitative_base_wage": sum(
            page.table * 4 + page.numeric * 2 + page.wage * 3 for page in pages
        ),
        "qualitative_mechanism": sum(
            page.qual * 5 + page.wage - page.table for page in pages
        ),
        "mixed_quant_qual": sum(
            page.qual * 3 + page.table * 3 + page.numeric + page.wage
            for page in pages
        ),
        "non_base_wage": sum(page.nonbase * 6 + page.numeric for page in pages),
        "reference_exclusion": sum(
            int(page.reference) * 8 - page.table for page in pages
        ),
        "effective_date_or_classification_conflict": sum(
            page.table * 3 + page.numeric * 3 + page.wage * 2 for page in pages
        ),
    }
    return values[role], row["extraction_case_id"]


def choose_preflight(
    selection: list[dict[str, str]],
    packet_map: dict[str, list[base.PagePacket]],
) -> list[tuple[str, dict[str, str]]]:
    by_lane: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selection:
        by_lane[row["planned_lane"]].append(row)
    duplicate = [
        row for row in selection if int(row["inventory_rows_for_content_hash"]) > 1
    ]
    if len(duplicate) != 1:
        raise RuntimeError("duplicate-hash provenance preflight case unavailable")
    chosen: list[tuple[str, dict[str, str]]] = [
        ("duplicate_hash_selection_provenance", duplicate[0])
    ]
    used = {duplicate[0]["extraction_case_id"]}
    roles = [
        "quantitative_base_wage",
        "qualitative_mechanism",
        "mixed_quant_qual",
        "non_base_wage",
        "reference_exclusion",
        "effective_date_or_classification_conflict",
    ]
    preferred = {
        "quantitative_base_wage": ("quantitative", "mixed"),
        "qualitative_mechanism": ("qualitative", "mixed"),
        "mixed_quant_qual": ("mixed",),
        "non_base_wage": ("non_base_wage", "mixed", "quantitative"),
        "reference_exclusion": ("reference_and_exclusion", "mixed"),
        "effective_date_or_classification_conflict": ("quantitative", "mixed"),
    }
    primary = {
        "quantitative_base_wage": "quantitative",
        "qualitative_mechanism": "qualitative",
        "mixed_quant_qual": "mixed",
        "non_base_wage": "non_base_wage",
        "reference_exclusion": "reference_and_exclusion",
        "effective_date_or_classification_conflict": "quantitative",
    }
    for role in roles:
        candidates = [
            row
            for row in by_lane[primary[role]]
            if row["extraction_case_id"] not in used
        ]
        if not candidates:
            candidates = [
                row
                for lane in preferred[role]
                for row in by_lane[lane]
                if row["extraction_case_id"] not in used
            ]
        if not candidates:
            raise RuntimeError(f"representative preflight path unavailable: {role}")
        selected = max(
            candidates,
            key=lambda row: role_score(
                row, packet_map[row["extraction_case_id"]], role
            ),
        )
        chosen.append((role, selected))
        used.add(selected["extraction_case_id"])
    return chosen


def preflight(
    output: Path,
    selection: list[dict[str, str]],
    packet_map: dict[str, list[base.PagePacket]],
    key: str,
) -> int:
    chosen = choose_preflight(selection, packet_map)
    requests = [
        base.Request(row, packet_map[row["extraction_case_id"]], f"preflight_remaining_{role}")
        for role, row in chosen
    ]
    results = base.call_gabriel(requests, key, parallel=1)
    metadata = [
        base.result_metadata(result, request)
        for result, request in zip(results, requests)
    ]
    timing = [
        {
            "request_phase": request.phase,
            "extraction_case_id": result.case_id,
            "started_at": "",
            "finished_at": base.now(),
            "local_packet_seconds": "0.000000",
            "gabriel_elapsed_seconds": f"{result.elapsed:.6f}",
            "request_status": result.status,
        }
        for result, request in zip(results, requests)
    ]
    base.write_csv(
        output / "remaining_parse_text_request_metadata.csv",
        base.METADATA_FIELDS,
        metadata,
    )
    base.write_csv(
        output / "remaining_parse_text_timing.csv", base.TIMING_FIELDS, timing
    )
    passed = len(results) == 7 and all(result.status == "success" for result in results)
    report = "# Remaining readable parse-text extraction preflight\n\n"
    report += "\n".join(
        f"- `{role}` / `{result.case_id}`: `{result.status}`"
        for (role, _), result in zip(chosen, results)
    )
    report += f"\n\nOverall: `{'pass' if passed else 'fail'}` ({sum(r.status == 'success' for r in results)} / 7 strict-valid).\n"
    report += "\nThe corrected 1,000-document seed was not sent to GABRIEL.\n"
    report += "No raw prompt, raw response, full text/table, or encoded image was saved.\n"
    (output / "remaining_parse_text_preflight_report.md").write_text(
        report, encoding="utf-8"
    )
    base.write_json(
        output / ".remaining_preflight_passed.json",
        {
            "passed": passed,
            "case_count": len(results),
            "schema_valid_count": sum(result.status == "success" for result in results),
            "roles": [role for role, _ in chosen],
            "seed_case_calls": 0,
            "selection_sha256": base.sha_file(
                output / "remaining_parse_text_selection_manifest.csv"
            ),
            "completed_at": base.now(),
        },
    )
    return 0 if passed else 2


def write_new_lanes(
    output: Path,
    selection: list[dict[str, str]],
    results: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    with tempfile.TemporaryDirectory(prefix="remaining_parse_text_lanes_") as temp:
        materialized = base.materialize_lanes(Path(temp), selection, results)
    rows = materialized["rows"]
    for key, relative in NEW_PATHS.items():
        base.write_csv(output / relative, BASE_FIELDS[key], rows[key])
    summaries = materialized["summaries"]
    base.write_json(
        output / "lanes_new/quantitative/quantitative_extraction_summary.json",
        summaries["quantitative"],
    )
    base.write_json(
        output / "lanes_new/qualitative/qualitative_mechanism_extraction_summary.json",
        summaries["qualitative"],
    )
    base.write_json(
        output / "lanes_new/mixed/mixed_extraction_summary.json",
        summaries["mixed"],
    )
    base.write_json(
        output / "lanes_new/non_base_wage/non_base_wage_compensation_summary.json",
        summaries["non_base_wage"],
    )
    base.write_json(
        output / "lanes_new/reference_and_exclusion/reference_exclusion_summary.json",
        summaries["reference_and_exclusion"],
    )
    return rows


def new_cumulative_row(row: dict[str, str], key: str) -> dict[str, str]:
    oid = row.get(ID_FIELDS[key], "")
    updated = dict(row)
    updated.update(
        {
            "cumulative_cohort": "remaining_parse_text_826_new",
            "source_seed_observation_id": "",
            "qa_original_status": row.get("qa_status", ""),
            "qa_resolution_classification": "pending_readable_parse_text_qa",
            "qa_resolution_status": "pending",
            "canonical_observation_id": oid,
            "duplicate_of": "",
            "active_in_provisional_lane": "true",
            "targeted_qa_resolution_ids": "",
            "targeted_qa_resolution_classification": "not_in_1000_targeted_qa",
            "targeted_qa_resolution_status": "not_applicable",
            "targeted_qa_reason_codes": "",
            "targeted_qa_source_observation_id": oid,
            "active_in_qa_corrected_lane": "true",
        }
    )
    return updated


def canonicalize_new_duplicates(
    cumulative: dict[str, list[dict[str, str]]],
    review_rows: list[dict[str, str]],
) -> int:
    duplicate_count = 0
    skip = {
        "qa_status", "cumulative_cohort", "source_seed_observation_id",
        "qa_original_status", "qa_resolution_classification",
        "qa_resolution_status", "canonical_observation_id", "duplicate_of",
        "active_in_provisional_lane", "targeted_qa_resolution_ids",
        "targeted_qa_resolution_classification", "targeted_qa_resolution_status",
        "targeted_qa_reason_codes", "targeted_qa_source_observation_id",
        "active_in_qa_corrected_lane",
    }
    for key in ("quant", "qual", "nonbase"):
        id_field = ID_FIELDS[key]
        fields = [field for field in BASE_FIELDS[key] if field not in {id_field} | skip]
        groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        for row in cumulative[key]:
            if active(row):
                groups[tuple(row.get(field, "") for field in fields)].append(row)
        for values in groups.values():
            if len(values) <= 1:
                continue
            if all(row.get("duplicate_of") for row in values[1:]):
                continue
            ordered = sorted(values, key=lambda row: row[id_field])
            canonical = ordered[0][id_field]
            duplicates: list[str] = []
            for row in ordered:
                row["canonical_observation_id"] = canonical
                row["qa_resolution_classification"] = "duplicate_or_same_observation"
                row["qa_resolution_status"] = "resolved"
                if row[id_field] != canonical:
                    row["duplicate_of"] = canonical
                    row["active_in_provisional_lane"] = "false"
                    row["active_in_qa_corrected_lane"] = "false"
                    row["qa_status"] = "duplicate_canonicalized"
                    duplicates.append(row[id_field])
            duplicate_count += len(duplicates)
            review_rows.append(
                {
                    "review_type": "exact_structured_content_duplicate",
                    "extraction_case_id": ordered[0]["extraction_case_id"],
                    "page_number": ordered[0].get("page_number", ""),
                    "lane": key,
                    "observation_ids": "|".join(row[id_field] for row in ordered),
                    "observation_count": str(len(ordered)),
                    "qa_reason": "EXACT_STRUCTURED_CONTENT_REPEATED",
                    "resolution_classification": "duplicate_or_same_observation",
                    "resolution_status": "resolved",
                    "unresolved_flag": "false",
                    "structured_basis": "Exact structured content; earliest stable observation ID is canonical.",
                    "canonical_observation_id": canonical,
                    "duplicate_observation_ids": "|".join(duplicates),
                }
            )
    return duplicate_count


def materialize_cumulative(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    results: dict[str, dict[str, Any]],
    seed_dir: Path,
) -> dict[str, Any]:
    if len(results) != EXPECTED_NEW or set(results) != {
        row["extraction_case_id"] for row in selection
    }:
        raise RuntimeError("cumulative materialization requires all 826 frozen results")
    new_rows = write_new_lanes(output, selection, results)
    cumulative: dict[str, list[dict[str, str]]] = {}
    fields: dict[str, list[str]] = {}
    for key, relative in SEED_PATHS.items():
        seed_fields, seed_rows = read_csv_with_fields(seed_dir / relative)
        fields[key] = list(seed_fields)
        for field in BASE_FIELDS[key] + base.CUMULATIVE_QA_FIELDS:
            if field not in fields[key]:
                fields[key].append(field)
        for field in (
            "targeted_qa_resolution_ids",
            "targeted_qa_resolution_classification",
            "targeted_qa_resolution_status",
            "targeted_qa_reason_codes",
            "targeted_qa_source_observation_id",
            "active_in_qa_corrected_lane",
        ):
            if field not in fields[key]:
                fields[key].append(field)
        cumulative[key] = seed_rows + [new_cumulative_row(row, key) for row in new_rows[key]]

    review_rows: list[dict[str, str]] = []
    new_duplicate_count = canonicalize_new_duplicates(cumulative, review_rows)

    active_quant = [row for row in cumulative["quant"] if active(row)]
    conflict_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in active_quant:
        key = tuple(
            row.get(field, "")
            for field in (
                "extraction_case_id", "page_number", "compensation_type",
                "occupation_unit_classification_rank", "pay_band", "step",
                "grade", "effective_date", "currency_or_unit",
            )
        )
        conflict_groups[key].append(row)
    conflict_counts: Counter[str] = Counter()
    unresolved_groups = 0
    for values in conflict_groups.values():
        signatures = {
            tuple(
                row.get(field, "")
                for field in (
                    "rate_value", "salary_value", "hourly_rate",
                    "annual_salary", "percentage_increase",
                )
            )
            for row in values
        }
        if len(signatures) <= 1:
            continue
        seed_only = all(
            row.get("cumulative_cohort") != "remaining_parse_text_826_new"
            for row in values
        )
        if seed_only and any(
            row.get("qa_resolution_status") == "unresolved" for row in values
        ):
            classification = next(
                (
                    row.get("qa_resolution_classification", "")
                    for row in values
                    if row.get("qa_resolution_status") == "unresolved"
                ),
                "insufficient_evidence_needs_review",
            )
            basis = "Carried forward from corrected 1,000-document targeted-QA shadow."
        else:
            classification, basis = conflict_resolution(values)
        unresolved = classification in {
            "true_conflict_unresolved", "insufficient_evidence_needs_review"
        }
        conflict_counts[classification] += 1
        unresolved_groups += int(unresolved)
        for row in values:
            if row.get("cumulative_cohort") == "remaining_parse_text_826_new":
                row["qa_resolution_classification"] = classification
                row["qa_resolution_status"] = "unresolved" if unresolved else "resolved"
                row["qa_status"] = (
                    "needs_conflict_review" if unresolved else "qa_structural_conflict_resolved"
                )
        review_rows.append(
            {
                "review_type": "potential_quantitative_conflict",
                "extraction_case_id": values[0]["extraction_case_id"],
                "page_number": values[0]["page_number"],
                "lane": "quantitative",
                "observation_ids": "|".join(
                    row["quantitative_observation_id"] for row in values
                ),
                "observation_count": str(len(values)),
                "qa_reason": "SAME_EVIDENCE_KEY_DIFFERENT_VALUES",
                "resolution_classification": classification,
                "resolution_status": "unresolved" if unresolved else "resolved",
                "unresolved_flag": "true" if unresolved else "false",
                "structured_basis": basis,
                "canonical_observation_id": "",
                "duplicate_observation_ids": "",
            }
        )

    contamination: list[dict[str, str]] = []
    for row in cumulative["quant"]:
        if not active(row):
            continue
        family = nonbase_type(row)
        retained = row.get("targeted_qa_resolution_classification") == (
            "retain_quantitative_base_wage"
        )
        if family and not retained:
            contamination.append(row)
            row["qa_resolution_classification"] = "insufficient_evidence_needs_review"
            row["qa_resolution_status"] = "unresolved"
            row["qa_status"] = "needs_non_base_wage_review"
            review_rows.append(
                {
                    "review_type": "possible_non_base_wage_quantitative",
                    "extraction_case_id": row["extraction_case_id"],
                    "page_number": row["page_number"],
                    "lane": "quantitative",
                    "observation_ids": row["quantitative_observation_id"],
                    "observation_count": "1",
                    "qa_reason": f"POSSIBLE_NON_BASE_{family.upper()}",
                    "resolution_classification": "insufficient_evidence_needs_review",
                    "resolution_status": "unresolved",
                    "unresolved_flag": "true",
                    "structured_basis": "Strict cumulative routing scan detected a non-base family in an active quantitative record.",
                    "canonical_observation_id": "",
                    "duplicate_observation_ids": "",
                }
            )

    active_quant_ids = {
        row["quantitative_observation_id"] for row in cumulative["quant"] if active(row)
    }
    active_qual_ids = {
        row["qualitative_observation_id"] for row in cumulative["qual"] if active(row)
    }
    duplicate_map = {
        row[ID_FIELDS[key]]: row.get("canonical_observation_id", row[ID_FIELDS[key]])
        for key in ("quant", "qual")
        for row in cumulative[key]
    }
    for row in cumulative["mixed"]:
        quant_ids: list[str] = []
        for oid in row.get("quantitative_observation_ids", "").split("|"):
            canonical = duplicate_map.get(oid, oid)
            if canonical in active_quant_ids and canonical not in quant_ids:
                quant_ids.append(canonical)
        qual_ids: list[str] = []
        for oid in row.get("qualitative_observation_ids", "").split("|"):
            canonical = duplicate_map.get(oid, oid)
            if canonical in active_qual_ids and canonical not in qual_ids:
                qual_ids.append(canonical)
        row["quantitative_observation_ids"] = "|".join(quant_ids)
        row["qualitative_observation_ids"] = "|".join(qual_ids)
        row["quantitative_observation_count"] = str(len(quant_ids))
        row["qualitative_observation_count"] = str(len(qual_ids))
        flag = "true" if quant_ids and qual_ids else "false"
        row["active_in_provisional_lane"] = flag
        row["active_in_qa_corrected_lane"] = flag

    for key, relative in CUMULATIVE_PATHS.items():
        base.write_csv(output / relative, fields[key], cumulative[key])
    base.write_csv(
        output / "remaining_parse_text_conflict_review.csv", REVIEW_FIELDS, review_rows
    )

    active_rows = {key: [row for row in rows if active(row)] for key, rows in cumulative.items()}
    combined_packets = base.read_csv(FROZEN_1000_PACKET) + packet_rows
    pages_by_case: dict[str, set[int]] = defaultdict(set)
    for row in combined_packets:
        pages_by_case[row["extraction_case_id"]].add(int(row["page_number"]))
    observation_rows = active_rows["quant"] + active_rows["qual"] + active_rows["nonbase"]
    invalid_pages = sum(
        int(row["page_number"]) not in pages_by_case[row["extraction_case_id"]]
        for row in observation_rows
    )
    all_ids = (
        [row["quantitative_observation_id"] for row in cumulative["quant"]]
        + [row["qualitative_observation_id"] for row in cumulative["qual"]]
        + [row["non_base_wage_observation_id"] for row in cumulative["nonbase"]]
    )
    duplicate_ids = len(all_ids) - len(set(all_ids))
    conflict_rate = unresolved_groups / max(1, len(active_rows["quant"]))
    packet_compliant = (
        len({row["extraction_case_id"] for row in packet_rows}) == EXPECTED_NEW
        and all(
            int(row["packet_page_count"]) <= 6
            and int(row["packet_text_chars"]) <= 6000
            and int(row["text_chars"]) <= 1500
            for row in packet_rows
        )
    )
    frozen = base.read_csv(FROZEN_1000_SELECTION)
    cumulative_selection = frozen + selection
    unit_counts = Counter(row["unit_type"] for row in cumulative_selection)
    case_count = len({row["extraction_case_id"] for row in cumulative_selection})
    hash_count = len({row["content_hash"] for row in cumulative_selection})
    matching_preserved = (
        unit_counts == {"police": 780, "fire": 439, "non_safety": 607}
        and case_count == EXPECTED_CUMULATIVE
        and hash_count == EXPECTED_CUMULATIVE
    )
    metadata = base.read_csv(output / "remaining_parse_text_request_metadata.csv")
    live_rows = [row for row in metadata if row["request_phase"] == "live_remaining"]
    live_valid_ids = {
        row["extraction_case_id"] for row in live_rows if row["schema_valid"] == "true"
    }
    integrity_pass = (
        len(selection) == EXPECTED_NEW
        and len(results) == EXPECTED_NEW
        and packet_compliant
        and invalid_pages == 0
        and duplicate_ids == 0
        and len(contamination) == 0
        and conflict_rate <= 0.02
        and matching_preserved
    )
    decision_name = (
        "readable_parse_text_provisional_extraction_completed_qa_pass"
        if integrity_pass
        else "readable_parse_text_extraction_targeted_qa_required"
    )
    decision = {
        "task_id": TASK_ID,
        "generated_at": base.now(),
        "decision": decision_name,
        "qa_status": "pass" if integrity_pass else "fail",
        "qa_pass": integrity_pass,
        "integrity_qa_pass": integrity_pass,
        "corrected_1000_seed_count": EXPECTED_SEED,
        "seed_gabriel_calls": 0,
        "remaining_selection_count": len(selection),
        "remaining_unique_hash_count": len({row["content_hash"] for row in selection}),
        "cumulative_unique_case_count": case_count,
        "cumulative_unique_content_hash_count": hash_count,
        "case_level_schema_valid_count": EXPECTED_SEED + len(results),
        "case_level_schema_valid_rate": round(
            (EXPECTED_SEED + len(results)) / EXPECTED_CUMULATIVE, 6
        ),
        "new_case_schema_valid_count": len(results),
        "new_case_schema_valid_rate": round(len(results) / EXPECTED_NEW, 6),
        "live_request_attempt_count": len(live_rows),
        "live_schema_valid_unique_case_count": len(live_valid_ids),
        "preflight_case_count": 7,
        "preflight_schema_valid_count": 7,
        "packet_compliant": packet_compliant,
        "packet_rows": len(packet_rows),
        "duplicate_observation_id_count": duplicate_ids,
        "new_exact_duplicate_observations_canonicalized": new_duplicate_count,
        "invalid_observation_page_count": invalid_pages,
        "quantitative_conflict_group_count": sum(conflict_counts.values()),
        "conflict_resolution_counts": dict(conflict_counts),
        "unresolved_quantitative_conflict_group_count": unresolved_groups,
        "unresolved_quantitative_conflict_rate": round(conflict_rate, 8),
        "base_non_base_wage_contamination_count": len(contamination),
        "targeted_qa_required": not integrity_pass or unresolved_groups > 0,
        "targeted_qa_required_before_final_merge": unresolved_groups > 0 or bool(contamination),
        "matched_representation_intact": matching_preserved,
        "unit_type_counts": dict(unit_counts),
        "state_count": len({row["state"] for row in cumulative_selection}),
        "source_type_counts": dict(
            Counter(row["candidate_source_type"] for row in cumulative_selection)
        ),
        "quantitative_observation_count": len(active_rows["quant"]),
        "qualitative_mechanism_observation_count": len(active_rows["qual"]),
        "mixed_case_count": len(active_rows["mixed"]),
        "non_base_wage_observation_count": len(active_rows["nonbase"]),
        "reference_exclusion_case_count": len(active_rows["refs"]),
        "new_quantitative_observation_count": len(new_rows["quant"]),
        "new_qualitative_mechanism_observation_count": len(new_rows["qual"]),
        "new_mixed_case_count": len(new_rows["mixed"]),
        "new_non_base_wage_observation_count": len(new_rows["nonbase"]),
        "new_reference_exclusion_case_count": len(new_rows["refs"]),
        "next_recommendation": (
            "targeted_qa_before_any_final_provisional_merge"
            if unresolved_groups or contamination
            else "design_stop_before_final_merge_review"
        ),
        "final_merge_allowed": False,
        "ingestion_allowed": False,
        "codify_allowed": False,
        "wage_gap_analysis_allowed": False,
        "raw_prompts_saved": False,
        "raw_responses_saved": False,
        "full_text_saved": False,
        "full_tables_saved": False,
        "encoded_images_saved": False,
    }
    base.write_json(output / "remaining_parse_text_decision_report.json", decision)
    report = f"""# Remaining readable parse-text cumulative QA report

- Integrity QA: `{'pass' if integrity_pass else 'fail'}`
- Corrected 1,000-document seed reused without GABRIEL: 1,000
- New schema-valid cases: {len(results)} / 826
- Cumulative readable hashes/cases: {hash_count} / {case_count}
- Packet compliance: `{str(packet_compliant).lower()}`
- Invalid bounded observation pointers: {invalid_pages}
- Duplicate observation IDs: {duplicate_ids}
- Newly canonicalized exact structured duplicates: {new_duplicate_count}
- Quantitative conflict groups: {sum(conflict_counts.values())}
- Unresolved quantitative conflict groups: {unresolved_groups}
- Unresolved quantitative conflict rate: {conflict_rate:.4%}
- Base/non-base contamination: {len(contamination)}
- Active quantitative observations: {len(active_rows['quant'])}
- Active qualitative mechanisms: {len(active_rows['qual'])}
- Active mixed cases: {len(active_rows['mixed'])}
- Active non-base-wage observations: {len(active_rows['nonbase'])}
- Reference/exclusion cases: {len(active_rows['refs'])}
- Decision: `{decision_name}`
- Targeted QA before final merge: `{str(decision['targeted_qa_required_before_final_merge']).lower()}`

The cumulative outputs cover every unique durable readable parse-text hash and
remain provisional and separate from final analysis inputs. This task stops
before final merge, ingestion, codification, wage-gap analysis, or regression.
"""
    (output / "remaining_parse_text_qa_report.md").write_text(report, encoding="utf-8")
    validation = f"""# Remaining readable parse-text extraction validation — 2026-07-25

- Exact new unique hashes: `{'pass' if len(selection) == EXPECTED_NEW else 'fail'}` ({len(selection)})
- Corrected 1,000 seed API calls: `pass` (0)
- New strict-schema cases: `{'pass' if len(results) == EXPECTED_NEW else 'fail'}` ({len(results)})
- Cumulative unique readable hashes: `{'pass' if hash_count == EXPECTED_CUMULATIVE else 'fail'}` ({hash_count})
- Packet limits: `{'pass' if packet_compliant else 'fail'}`
- Invalid bounded pointers: `{'pass' if invalid_pages == 0 else 'fail'}` ({invalid_pages})
- Duplicate observation IDs: `{'pass' if duplicate_ids == 0 else 'fail'}` ({duplicate_ids})
- Base/non-base contamination: `{'pass' if not contamination else 'fail'}` ({len(contamination)})
- Conflict-rate gate (<=2%): `{'pass' if conflict_rate <= 0.02 else 'fail'}` ({conflict_rate:.4%})
- Police/fire/non-safety coverage: `{'pass' if matching_preserved else 'fail'}`
- Raw prompts/responses, full text/tables, encoded images saved: `false`

Repository-wide validation commands are recorded after the complete test suite.
"""
    (output / "remaining_parse_text_validation_2026-07-25.md").write_text(
        validation, encoding="utf-8"
    )
    return {"decision": decision, "rows": cumulative}


def live(
    output: Path,
    selection: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    packet_map: dict[str, list[base.PagePacket]],
    seed_dir: Path,
    key: str,
    resume: bool,
) -> int:
    marker = base.read_json(output / ".remaining_preflight_passed.json")
    if (
        marker.get("passed") is not True
        or int(marker.get("schema_valid_count", 0)) != 7
        or int(marker.get("seed_case_calls", -1)) != 0
        or marker.get("selection_sha256")
        != base.sha_file(output / "remaining_parse_text_selection_manifest.csv")
    ):
        raise RuntimeError("live remaining lanes require successful seven-path preflight")
    checkpoint = output / "remaining_parse_text_case_results.jsonl"
    stored: dict[str, dict[str, Any]] = {}
    if resume and checkpoint.is_file():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            stored[item["extraction_case_id"]] = item["result"]
    selection_ids = {row["extraction_case_id"] for row in selection}
    if not set(stored).issubset(selection_ids):
        raise RuntimeError("checkpoint contains a case outside the frozen 826")
    metadata_path = output / "remaining_parse_text_request_metadata.csv"
    timing_path = output / "remaining_parse_text_timing.csv"
    metadata = base.read_csv(metadata_path) if metadata_path.is_file() else []
    timing = base.read_csv(timing_path) if timing_path.is_file() else []
    by_id = {row["extraction_case_id"]: row for row in selection}
    for attempt_round in range(1, 11):
        pending_ids = sorted(selection_ids - set(stored))
        if not pending_ids:
            break
        for start in range(0, len(pending_ids), 25):
            batch_ids = pending_ids[start : start + 25]
            requests: list[base.Request] = []
            for case_id in batch_ids:
                request_row = dict(by_id[case_id])
                errors = [
                    row["error_message"]
                    for row in metadata
                    if row["request_phase"] == "live_remaining"
                    and row["extraction_case_id"] == case_id
                    and row["error_message"].startswith(
                        "non-base compensation is in quantitative array: "
                    )
                ]
                if errors:
                    request_row["_nonbase_retry_hint"] = errors[-1].rsplit(": ", 1)[-1]
                requests.append(
                    base.Request(request_row, packet_map[case_id], "live_remaining")
                )
            results = base.call_gabriel(requests, key, parallel=2)
            for result, request in zip(results, requests):
                metadata.append(base.result_metadata(result, request))
                timing.append(
                    {
                        "request_phase": "live_remaining",
                        "extraction_case_id": result.case_id,
                        "started_at": "",
                        "finished_at": base.now(),
                        "local_packet_seconds": "0.000000",
                        "gabriel_elapsed_seconds": f"{result.elapsed:.6f}",
                        "request_status": result.status,
                    }
                )
                if result.status == "success" and result.parsed is not None:
                    stored[result.case_id] = result.parsed
            checkpoint.write_text(
                "\n".join(
                    json.dumps(
                        {"extraction_case_id": case_id, "result": stored[case_id]},
                        sort_keys=True,
                    )
                    for case_id in sorted(stored)
                )
                + ("\n" if stored else ""),
                encoding="utf-8",
            )
            base.write_csv(metadata_path, base.METADATA_FIELDS, metadata)
            base.write_csv(timing_path, base.TIMING_FIELDS, timing)
            print(
                json.dumps(
                    {
                        "phase": "live_remaining",
                        "attempt_round": attempt_round,
                        "batch_attempted": len(batch_ids),
                        "schema_valid_results_stored": len(stored),
                        "remaining": EXPECTED_NEW - len(stored),
                        "batch_success": sum(r.status == "success" for r in results),
                        "batch_failed": sum(r.status != "success" for r in results),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    if len(stored) != EXPECTED_NEW:
        unresolved_case_ids = sorted(selection_ids - set(stored))
        live_requests = [
            row for row in metadata if row.get("request_phase") == "live_remaining"
        ]
        base.write_json(
            output / "remaining_parse_text_decision_report.json",
            {
                "task_id": TASK_ID,
                "generated_at": base.now(),
                "decision": "live_incomplete_schema_invalid",
                "qa_status": "not_run",
                "selection_count": EXPECTED_NEW,
                "unique_remaining_content_hash_count": EXPECTED_NEW,
                "corrected_1000_seed_count": EXPECTED_SEED,
                "schema_valid_new_case_count": len(stored),
                "schema_valid_new_case_rate": len(stored) / EXPECTED_NEW,
                "unresolved_new_case_count": EXPECTED_NEW - len(stored),
                "unresolved_new_case_ids": unresolved_case_ids,
                "live_case_attempt_count": len(live_requests),
                "live_schema_invalid_attempt_count": sum(
                    row.get("schema_valid") != "true" for row in live_requests
                ),
                "preflight_case_count": 7,
                "preflight_schema_valid_count": 7,
                "preflight_schema_valid_rate": 1.0,
                "gabriel_backend": live_requests[-1].get("gabriel_backend", "")
                if live_requests
                else "",
                "gabriel_model": live_requests[-1].get("gabriel_model", "")
                if live_requests
                else "",
                "seed_gabriel_calls": 0,
                "cumulative_materialization_completed": False,
                "cumulative_case_count": EXPECTED_SEED,
                "cumulative_readable_parse_text_target_count": EXPECTED_CUMULATIVE,
                "targeted_qa_required": True,
                "next_recommendation": (
                    "resolve_only_the_remaining_education_certification_routing_case"
                ),
                "final_merge_allowed": False,
                "ingestion_allowed": False,
                "codify_allowed": False,
            },
        )
        return 2
    materialized = materialize_cumulative(
        output, selection, packet_rows, stored, seed_dir
    )
    return 0 if materialized["decision"]["qa_pass"] else 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("freeze_remaining_selection", "preflight_remaining", "live_remaining"),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed-dir", type=Path, default=SEED_DIR)
    parser.add_argument("--case-limit", type=int, default=EXPECTED_NEW)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-representative-cases", action="store_true")
    parser.add_argument("--allow-gabriel", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output_dir.resolve()
    seed_dir = args.seed_dir.resolve()
    if args.case_limit != EXPECTED_NEW:
        raise ValueError(f"remaining modes require exactly {EXPECTED_NEW} cases")
    if args.mode == "freeze_remaining_selection":
        if not args.dry_run or args.allow_gabriel:
            raise ValueError("remaining selection freeze must be a no-call dry run")
        output.mkdir(parents=True, exist_ok=True)
        selection = freeze_selection(output, seed_dir, args.case_limit)
        packet_rows, _ = freeze_packets(output, selection)
        write_freeze_outputs(output, selection, packet_rows, seed_dir)
        print(
            json.dumps(
                {
                    "status": "frozen",
                    "selection_count": len(selection),
                    "unique_hash_count": len({row["content_hash"] for row in selection}),
                    "seed_case_count": EXPECTED_SEED,
                    "seed_gabriel_calls": 0,
                    "packet_rows": len(packet_rows),
                    "gabriel_calls": 0,
                },
                sort_keys=True,
            )
        )
        return 0
    selection = load_selection(output)
    packet_rows, packet_map = packet_rows_and_map(output, selection)
    if not args.allow_gabriel:
        raise ValueError("preflight/live modes require --allow-gabriel")
    key = base.load_key()
    if not key:
        raise RuntimeError("GABRIEL credential unavailable")
    if args.mode == "preflight_remaining":
        if not args.preflight_representative_cases:
            raise ValueError("representative preflight flag required")
        return preflight(output, selection, packet_map, key)
    if not args.resume:
        raise ValueError("live remaining mode requires --resume")
    return live(output, selection, packet_rows, packet_map, seed_dir, key, True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {str(exc)[:300]}", file=__import__("sys").stderr)
        raise SystemExit(1)
