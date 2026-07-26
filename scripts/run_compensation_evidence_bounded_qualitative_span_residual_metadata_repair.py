#!/usr/bin/env python3
"""Run bounded qualitative-span and residual-metadata schema repair.

The runner is deliberately offline and non-extractive. It reads only committed
structured ledgers and retained bounded packet manifests. It never opens PDFs,
calls a model, selects documents, or mutates an upstream ledger. Literal spans
are accepted only when a packet artifact contains the page text and the span is
an exact substring; metadata is accepted only under deterministic rules.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
FOLLOWUP = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-SCHEMA-REPAIR-FOLLOWUP-2026-07-25"
)
PRIOR_REPAIR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-AND-RESIDUAL-METADATA-REPAIR-2026-07-25"
)

CURRENT_INPUTS = {
    "decision": FOLLOWUP / "bounded_schema_repair_followup_decision.json",
    "summary": FOLLOWUP / "bounded_schema_repair_followup_summary.md",
    "validation": FOLLOWUP / "bounded_schema_repair_followup_validation_2026-07-25.md",
    "cycle_bridge": FOLLOWUP / "bounded_cycle_matching_bridge.csv",
    "cycle_audit": FOLLOWUP / "bounded_cycle_matching_bridge_audit.json",
    "retrieval_bridge": FOLLOWUP / "bounded_retrieval_provenance_bridge.csv",
    "retrieval_audit": FOLLOWUP / "bounded_retrieval_provenance_bridge_audit.json",
    "occupation_bridge": FOLLOWUP / "bounded_non_safety_occupation_bridge.csv",
    "occupation_audit": FOLLOWUP / "bounded_non_safety_occupation_bridge_audit.json",
    "quarantine": FOLLOWUP / "bounded_followup_quarantine_summary.json",
    "blockers": FOLLOWUP / "bounded_followup_blocker_matrix.csv",
    "span_availability": FOLLOWUP / "qualitative_evidence_span_availability_audit.json",
    "qual_navigation": FOLLOWUP / "qualitative_mechanism_navigation_view_candidate_followup.csv",
    "qual_shadow": FOLLOWUP / "repaired_qualitative_mechanism_shadow_followup.csv",
    "quant_shadow": FOLLOWUP / "repaired_quantitative_shadow_followup.csv",
    "mixed_shadow": FOLLOWUP / "repaired_mixed_join_shadow_followup.csv",
    "nonbase_shadow": FOLLOWUP / "repaired_non_base_wage_shadow_followup.csv",
    "reference_shadow": FOLLOWUP / "repaired_reference_exclusion_shadow_followup.csv",
    "quant_candidate": FOLLOWUP / "quantitative_analysis_view_candidate_followup.csv",
    "quant_exceptions": FOLLOWUP / "quantitative_followup_exception_ledger.csv",
    "nonbase_candidate": FOLLOWUP / "non_base_wage_companion_view_candidate_followup.csv",
    "reference_control": FOLLOWUP / "reference_exclusion_control_view_followup.csv",
    "conflict_quarantine": PRIOR_REPAIR / "unresolved_conflict_quarantine_ledger.csv",
}

DURABLE_INPUTS = {
    "candidate_queue": ROOT / "docs/analysis/national_scout_candidate_queue_2026-07-20.csv",
    "content_triage": ROOT / "docs/analysis/content_triage_ledgers/content_triage_ledger_latest.csv",
    "verification": ROOT / "docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv",
    "source_review": ROOT / "docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv",
    "pdf_readiness": ROOT / "docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv",
    "text_table_detection": ROOT / "docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_latest.csv",
}

PACKET_INPUTS = {
    "packet_500": ROOT / (
        "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-500DOC-2026-07-25/"
        "compensation_extraction_500_packet_manifest.csv"
    ),
    "packet_1000": ROOT / (
        "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25/"
        "compensation_extraction_1000_packet_manifest.csv"
    ),
    "packet_remaining": ROOT / (
        "docs/analysis/compensation_extraction/"
        "COMPENSATION-EVIDENCE-EXTRACTION-REMAINING-PARSE-TEXT-826-2026-07-25/"
        "remaining_parse_text_packet_manifest.csv"
    ),
}

EXPECTED_ANCHOR_SHA256 = {
    "decision": "abd873183cf7406890e06a87ec05cfe7b1f47f7543ae5e04b6cc5347ae730ff3",
    "cycle_bridge": "790e82c98c098a77c73d625dea057f44304cd43fbd161f8dca3859f0de4604af",
    "occupation_bridge": "4a4322a06d24329719315588de95e41945121edd59a8ed96bda2449ea8e75068",
    "qual_navigation": "5cb7c84512debbbcce0e9fee5db95ba4918b2c3027cca1a595fd3938bdeb51cd",
    "quant_candidate": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    "quant_exceptions": "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401",
    "nonbase_candidate": "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92",
    "reference_control": "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a",
    "conflict_quarantine": "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7",
    "packet_500": "484e8059d2f0bc6d883ac2f6d206cae5cb388cc9e5f20be132abcf1f82a9ef68",
    "packet_1000": "8a8253d7bb1dfcff59f7d5592df34e8b329a6f9d3a2ae16d7fc5c8a0cf211343",
    "packet_remaining": "f6699c7ae0fbc1a979a503b8ebc5cba2bed16c072f35306707a3283c46b8dd81",
}

OUTPUTS = {
    "summary": "bounded_qualitative_span_residual_metadata_repair_summary.md",
    "decision": "bounded_qualitative_span_residual_metadata_repair_decision.json",
    "span_audit": "qualitative_literal_span_capture_audit.json",
    "span_ledger": "qualitative_literal_span_capture_ledger.csv",
    "qual_navigation": "qualitative_mechanism_span_repaired_navigation_view.csv",
    "cycle_bridge": "residual_cycle_matching_bridge.csv",
    "cycle_audit": "residual_cycle_matching_bridge_audit.json",
    "occupation_bridge": "residual_non_safety_occupation_bridge.csv",
    "occupation_audit": "residual_non_safety_occupation_bridge_audit.json",
    "metadata_quarantine": "residual_metadata_quarantine_summary.json",
    "input_hashes": "bounded_span_repair_durable_input_sha256.txt",
    "quant_candidate": "quantitative_analysis_view_candidate_span_followup.csv",
    "quant_exceptions": "quantitative_exception_ledger_span_followup.csv",
    "nonbase_candidate": "non_base_wage_companion_view_candidate_span_followup.csv",
    "reference_control": "reference_exclusion_control_view_span_followup.csv",
    "conflict_quarantine": "unresolved_conflict_quarantine_ledger_span_followup.csv",
    "blockers": "bounded_span_residual_metadata_blocker_matrix.csv",
    "future_prompt": "next_bounded_schema_repair_followup_prompt.md",
    "validation": "bounded_qualitative_span_residual_metadata_repair_validation_2026-07-25.md",
}

TASK_ID = "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-AND-RESIDUAL-METADATA-REPAIR-2026-07-25"
DECISION = "bounded_span_metadata_repair_blocked_missing_bounded_text_or_span_support"
TEXT_PAYLOAD_FIELDS = ("page_text", "bounded_text", "text_excerpt", "text_snippet", "page_excerpt")

RESIDUAL_OCCUPATION_RULES = {
    "clerical_admin": re.compile(r"\b(?:administrative|clerical) unit\b|\badmin(?:istrative)? staff\b", re.I),
    "public_works": re.compile(r"\b(?:water|sewer|street|highway|engineering) (?:department|division|employees?|workers?)\b", re.I),
    "parks_rec": re.compile(r"\bparks? (?:department|employees?|workers?)\b|\brecreation (?:department|employees?|workers?)\b", re.I),
    "library": re.compile(r"\blibrary (?:employees?|workers?|staff|unit)\b", re.I),
    "other": re.compile(r"\b(?:general|municipal|city|town|county) employees?\b|\bsupervisory employees?\b|\bcivilian employees?\b", re.I),
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise RuntimeError(f"Missing or duplicate headers in {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, header: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in header})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_{hashlib.sha256('|'.join(parts).encode()).hexdigest()[:24]}"


def load_predecessor() -> Any:
    path = ROOT / "scripts/run_compensation_evidence_bounded_schema_repair_followup.py"
    spec = importlib.util.spec_from_file_location("bounded_schema_followup_for_span_repair", path)
    if not spec or not spec.loader:
        raise RuntimeError("Unable to load predecessor follow-up module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_output_path(output_dir: Path) -> None:
    if output_dir.exists():
        raise FileExistsError(f"Rollback-safe output already exists: {output_dir}")
    resolved = output_dir.resolve()
    if (ROOT / "docs/analysis").resolve() not in resolved.parents:
        raise RuntimeError("Output must be a new docs/analysis subdirectory")
    forbidden = {"data", "corpus", "ingest", "codified", "analysis_dataset"}
    if forbidden.intersection(resolved.relative_to(ROOT).parts):
        raise RuntimeError(f"Forbidden output path: {resolved}")


def no_write_preflight(output_dir: Path) -> dict[str, Any]:
    required = {**CURRENT_INPUTS, **DURABLE_INPUTS, **PACKET_INPUTS}
    missing = [str(path.relative_to(ROOT)) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required artifacts missing: {missing}")
    validate_output_path(output_dir)
    decision = json.loads(CURRENT_INPUTS["decision"].read_text(encoding="utf-8"))
    if decision.get("decision") != "bounded_schema_followup_partial_additional_bounded_repair_needed":
        raise RuntimeError("Unexpected predecessor decision")
    anchors = {
        **{name: sha256(CURRENT_INPUTS[name]) for name in EXPECTED_ANCHOR_SHA256 if name in CURRENT_INPUTS},
        **{name: sha256(PACKET_INPUTS[name]) for name in EXPECTED_ANCHOR_SHA256 if name in PACKET_INPUTS},
    }
    if anchors != EXPECTED_ANCHOR_SHA256:
        raise RuntimeError(f"Immutable anchor SHA-256 mismatch: {anchors}")
    predecessor = load_predecessor()
    package = predecessor.input_preflight(output_dir)
    _, qual_rows = read_rows(CURRENT_INPUTS["qual_navigation"])
    _, cycle_rows = read_rows(CURRENT_INPUTS["cycle_bridge"])
    _, occupation_rows = read_rows(CURRENT_INPUTS["occupation_bridge"])
    if len(qual_rows) != 1954 or len(cycle_rows) != 1826 or len(occupation_rows) != 1826:
        raise RuntimeError("Unexpected predecessor row counts")
    return {
        "writes_performed": 0,
        "package_sha256_checks_passed": package["package_sha256_checks_passed"],
        "qualitative_navigation_rows": len(qual_rows),
        "document_identity_count": len(cycle_rows),
        "residual_cycle_identity_count": sum(not row["negotiation_cycle_id"] for row in cycle_rows),
        "residual_non_safety_identity_count": sum(
            row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]
            for row in occupation_rows
        ),
        "analysis_readiness_after_task": False,
    }


def unique_index(rows: list[dict[str, str]], key: str, expected: set[str]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get(key, "") in expected:
            grouped[row[key]].append(row)
    bad = {value: group for value, group in grouped.items() if len(group) != 1}
    missing = expected - set(grouped)
    if bad or missing:
        raise RuntimeError(f"Unsafe {key} bridge: duplicate={len(bad)} missing={len(missing)}")
    return {value: group[0] for value, group in grouped.items()}


def packet_index() -> tuple[dict[tuple[str, str, str], list[str]], dict[str, Any]]:
    index: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    field_audit: dict[str, Any] = {}
    for name, path in PACKET_INPUTS.items():
        header, rows = read_rows(path)
        text_fields = [field for field in TEXT_PAYLOAD_FIELDS if field in header]
        populated = sum(bool(row.get(field, "")) for row in rows for field in text_fields)
        field_audit[name] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "row_count": len(rows),
            "text_payload_fields_present": text_fields,
            "populated_text_payload_cell_count": populated,
        }
        for row in rows:
            key = (row["extraction_case_id"], row["page_number"], row["bounded_evidence_pointer"])
            index[key].append(name)
    return index, field_audit


def exact_period_evidence(value: str, predecessor: Any) -> dict[tuple[str, str], list[str]]:
    """Return normalized pairs with the exact structured-field substring supporting each pair."""
    evidence: dict[tuple[str, str], list[str]] = defaultdict(list)
    for pattern in predecessor.PERIOD_PATTERNS:
        for match in pattern.finditer(value or ""):
            start = predecessor.parse_date_token(match.group("start"))
            end = predecessor.parse_date_token(match.group("end"))
            if start and end and start <= end:
                evidence[(start, end)].append(match.group(0))
    return dict(evidence)


def build_span_outputs() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], list[str]]:
    qual_header, qual_rows = read_rows(CURRENT_INPUTS["qual_navigation"])
    packets, field_audit = packet_index()
    ledger: list[dict[str, str]] = []
    repaired: list[dict[str, str]] = []
    exact_pointer_matches = 0
    for row in qual_rows:
        key = (row["extraction_case_id"], row["page_number"], row["bounded_evidence_pointer"])
        sources = packets.get(key, [])
        exact_pointer_matches += bool(sources)
        status = "span_unavailable_or_unverified"
        reason = (
            "bounded_packet_page_metadata_matched_but_no_retained_text_payload"
            if sources
            else "bounded_packet_page_pointer_not_matched"
        )
        span_row = {
            "qualitative_observation_id": row["qualitative_observation_id"],
            "extraction_case_id": row["extraction_case_id"],
            "document_identity_id": row["document_identity_id"],
            "source_review_id": row["source_review_id"],
            "text_table_detection_id": row["text_table_detection_id"],
            "raw_retained_content_hash": row["raw_retained_content_hash"],
            "mechanism_type": row["mechanism_type"],
            "page_number": row["page_number"],
            "bounded_evidence_pointer": row["bounded_evidence_pointer"],
            "bounded_packet_manifest_sources": "|".join(sorted(sources)),
            "bounded_page_pointer_exact_match": "true" if sources else "false",
            "bounded_text_payload_available": "false",
            "literal_verbatim_evidence_span": "",
            "span_start": "",
            "span_end": "",
            "span_length": "0",
            "span_sha256": "",
            "span_capture_status": status,
            "span_capture_reason_code": reason,
            "span_qa_pass": "false",
        }
        ledger.append(span_row)
        copy = dict(row)
        copy.update(
            {
                "literal_verbatim_evidence_span": "",
                "span_start": "",
                "span_end": "",
                "span_length": "0",
                "span_sha256": "",
                "span_capture_status": status,
                "span_capture_reason_code": reason,
                "span_qa_pass": "false",
                "qualitative_coded_measurement_eligible": "false",
                "qualitative_readiness_reason": "literal_span_unavailable_navigation_only",
            }
        )
        repaired.append(copy)
    audit = {
        "active_qualitative_navigation_rows": len(qual_rows),
        "exact_bounded_page_pointer_match_count": exact_pointer_matches,
        "bounded_packet_manifest_audit": field_audit,
        "retained_bounded_text_payload_count": 0,
        "literal_span_capture_attempted_row_count": len(qual_rows),
        "literal_span_captured_count": 0,
        "literal_span_exact_substring_qa_pass_count": 0,
        "span_unavailable_or_unverified_count": len(qual_rows),
        "coded_qualitative_analysis_view_created": False,
        "navigation_view_created": True,
        "result": "blocked_no_retained_bounded_page_text_payload",
        "pdfs_opened": 0,
        "ocr_runs": 0,
        "model_calls": 0,
        "extraction_runs": 0,
    }
    extra = [
        "span_start", "span_end", "span_length", "span_sha256", "span_capture_status",
        "span_capture_reason_code", "span_qa_pass",
    ]
    repaired_header = qual_header + [field for field in extra if field not in qual_header]
    return ledger, repaired, audit, repaired_header


def build_cycle_bridge(predecessor: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    header, prior_rows = read_rows(CURRENT_INPUTS["cycle_bridge"])
    ids = {row["candidate_queue_row_id"] for row in prior_rows}
    _, candidate_rows = read_rows(DURABLE_INPUTS["candidate_queue"])
    _, triage_rows = read_rows(DURABLE_INPUTS["content_triage"])
    _, source_rows = read_rows(DURABLE_INPUTS["source_review"])
    _, ttd_rows = read_rows(DURABLE_INPUTS["text_table_detection"])
    candidate = unique_index(candidate_rows, "queue_id", ids)
    triage = unique_index(triage_rows, "candidate_queue_row_id", ids)
    source = unique_index(source_rows, "candidate_queue_row_id", ids)
    ttd = unique_index(ttd_rows, "candidate_queue_row_id", ids)

    improved = 0
    conflict_disambiguated = 0
    output: list[dict[str, str]] = []
    for prior in prior_rows:
        row = dict(prior)
        row.update(
            {
                "residual_cycle_bridge_status": "preserved_prior_exact_cycle" if prior["negotiation_cycle_id"] else "",
                "residual_cycle_support_fields": "",
                "residual_cycle_exact_evidence": "",
                "residual_cycle_exact_evidence_sha256": "",
            }
        )
        if prior["negotiation_cycle_id"]:
            output.append(row)
            continue
        queue_id = prior["candidate_queue_row_id"]
        explicit_evidence: dict[str, dict[tuple[str, str], list[str]]] = {
            "candidate_queue.cycle_match_notes": exact_period_evidence(
                candidate[queue_id].get("cycle_match_notes", ""), predecessor
            ),
            "content_triage.source_year_or_period_prelim": exact_period_evidence(
                triage[queue_id].get("source_year_or_period_prelim", ""), predecessor
            ),
        }
        start_token = source[queue_id].get("contract_or_document_period_start", "").strip()
        end_token = source[queue_id].get("contract_or_document_period_end", "").strip()
        direct_pairs: set[tuple[str, str]] = set()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_token) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", end_token) and start_token <= end_token:
            direct_pairs.add((start_token, end_token))
        explicit_evidence["source_review.contract_or_document_period_start_end"] = (
            {(start_token, end_token): [f"{start_token}|{end_token}"]} if direct_pairs else {}
        )
        explicit_pairs = {name: set(values) for name, values in explicit_evidence.items()}
        residual_pairs = set().union(*explicit_pairs.values())
        original_pairs = set().union(
            predecessor.exact_period_pairs(candidate[queue_id].get("contract_years_scouted", "")),
            predecessor.exact_period_pairs(candidate[queue_id].get("visible_year_evidence", "")),
            predecessor.exact_period_pairs(ttd[queue_id].get("candidate_contract_period_text", "")),
        )
        accepted: tuple[str, str] | None = None
        if len(residual_pairs) == 1 and not original_pairs:
            accepted = next(iter(residual_pairs))
            row["residual_cycle_bridge_status"] = "established_single_exact_pair_from_explicit_cycle_metadata"
        elif len(residual_pairs) == 1 and len(original_pairs) > 1 and next(iter(residual_pairs)) in original_pairs:
            accepted = next(iter(residual_pairs))
            row["residual_cycle_bridge_status"] = "established_exact_cycle_note_disambiguation_of_prior_conflict"
            conflict_disambiguated += 1
        elif len(residual_pairs) > 1:
            row["residual_cycle_bridge_status"] = "quarantined_multiple_residual_exact_pairs"
        elif original_pairs:
            row["residual_cycle_bridge_status"] = "quarantined_prior_conflict_not_deterministically_disambiguated"
        else:
            row["residual_cycle_bridge_status"] = "quarantined_no_exact_full_date_pair_in_bounded_structured_metadata"
        if accepted:
            start, end = accepted
            row["contract_period_start"] = start
            row["contract_period_end"] = end
            row["negotiation_cycle_id"] = stable_id("cycle", row["state"], row["municipality"], start, end)
            row["city_unit_negotiation_cycle_key"] = stable_id(
                "cuc", row["state"], row["municipality"], row["unit_type"], start, end
            )
            row["cycle_bridge_status"] = "established_single_exact_pair"
            improved += 1
            support_names = [name for name, pairs in explicit_pairs.items() if accepted in pairs]
            evidence = sorted(
                token
                for name in support_names
                for token in explicit_evidence[name].get(accepted, [])
            )[0]
            row["residual_cycle_exact_evidence"] = evidence
            row["residual_cycle_exact_evidence_sha256"] = hashlib.sha256(evidence.encode()).hexdigest()
            row["residual_cycle_support_fields"] = "|".join(support_names)
        output.append(row)

    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in output:
        row["matched_set_id"] = ""
        if row["negotiation_cycle_id"]:
            groups[(row["state"], row["municipality"], row["contract_period_start"], row["contract_period_end"])].append(row)
    matched_groups = 0
    for key, rows in groups.items():
        units = {row["unit_type"] for row in rows}
        if units.intersection({"police", "fire"}) and "non_safety" in units:
            matched_groups += 1
            matched = stable_id("match", *key)
            for row in rows:
                row["matched_set_id"] = matched
    prior_exact = sum(bool(row["negotiation_cycle_id"]) for row in prior_rows)
    prior_matched = sum(bool(row["matched_set_id"]) for row in prior_rows)
    audit = {
        "document_identity_count": len(output),
        "prior_exact_cycle_count": prior_exact,
        "residual_identity_scope_count": len(output) - prior_exact,
        "new_exact_cycle_count": improved,
        "prior_conflicts_deterministically_disambiguated_count": conflict_disambiguated,
        "revised_exact_cycle_count": sum(bool(row["negotiation_cycle_id"]) for row in output),
        "prior_matched_set_document_count": prior_matched,
        "revised_matched_set_document_count": sum(bool(row["matched_set_id"]) for row in output),
        "revised_matched_set_group_count": matched_groups,
        "revised_cycle_quarantine_count": sum(not row["negotiation_cycle_id"] for row in output),
        "exact_full_dates_only": True,
        "cycle_note_field_is_explicit_structured_metadata": True,
        "filename_or_title_inference_used": False,
        "pdf_or_url_text_used": False,
        "status_counts": dict(sorted(Counter(row["residual_cycle_bridge_status"] for row in output).items())),
    }
    return output, audit


def build_occupation_bridge() -> tuple[list[dict[str, str]], dict[str, Any]]:
    _, prior_rows = read_rows(CURRENT_INPUTS["occupation_bridge"])
    ids = {row["candidate_queue_row_id"] for row in prior_rows}
    _, candidate_rows = read_rows(DURABLE_INPUTS["candidate_queue"])
    candidate = unique_index(candidate_rows, "queue_id", ids)
    output: list[dict[str, str]] = []
    improved = 0
    for prior in prior_rows:
        row = dict(prior)
        row.update(
            {
                "residual_occupation_bridge_status": "preserved_prior_controlled_class" if prior["controlled_occupation_class"] else "",
                "residual_occupation_support_fields": "",
                "residual_occupation_evidence_token": "",
                "residual_occupation_evidence_sha256": "",
            }
        )
        if prior["unit_type"] != "non_safety" or prior["controlled_occupation_class"]:
            output.append(row)
            continue
        queue = candidate[prior["candidate_queue_row_id"]]
        fields = ("unit_type_scouted", "document_title", "union_name")
        matches: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for field in fields:
            value = queue.get(field, "")
            for label, pattern in RESIDUAL_OCCUPATION_RULES.items():
                for match in pattern.finditer(value):
                    matches[label].append((field, match.group(0)))
        if len(matches) == 1:
            label = next(iter(matches))
            support = matches[label]
            tokens = sorted({token for _, token in support}, key=str.casefold)
            fields_used = sorted({field for field, _ in support})
            evidence = "|".join(tokens)
            row["controlled_occupation_class"] = label
            row["occupation_class_bridge_status"] = "established_single_explicit_residual_structured_label_rule"
            row["residual_occupation_bridge_status"] = "established_single_explicit_residual_structured_label_rule"
            row["residual_occupation_support_fields"] = "|".join(f"candidate_queue.{field}" for field in fields_used)
            row["residual_occupation_evidence_token"] = evidence
            row["residual_occupation_evidence_sha256"] = hashlib.sha256(evidence.encode()).hexdigest()
            improved += 1
        elif len(matches) > 1:
            row["residual_occupation_bridge_status"] = "quarantined_multiple_controlled_residual_labels"
        else:
            row["residual_occupation_bridge_status"] = "quarantined_no_explicit_controlled_residual_label"
        output.append(row)
    prior_controlled = sum(bool(row["controlled_occupation_class"]) for row in prior_rows)
    prior_non_safety = sum(
        row["unit_type"] == "non_safety" and bool(row["controlled_occupation_class"])
        for row in prior_rows
    )
    audit = {
        "document_identity_count": len(output),
        "prior_controlled_occupation_count": prior_controlled,
        "prior_non_safety_subclass_count": prior_non_safety,
        "residual_non_safety_scope_count": sum(
            row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]
            for row in prior_rows
        ),
        "new_non_safety_subclass_count": improved,
        "revised_controlled_occupation_count": sum(bool(row["controlled_occupation_class"]) for row in output),
        "revised_non_safety_subclass_count": sum(
            row["unit_type"] == "non_safety" and bool(row["controlled_occupation_class"])
            for row in output
        ),
        "revised_non_safety_quarantine_count": sum(
            row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]
            for row in output
        ),
        "controlled_vocabulary": sorted(set(RESIDUAL_OCCUPATION_RULES) | {"police", "fire", "teacher", "sanitation", "transit", "nurse_health"}),
        "generic_explicit_employee_labels_map_to": "other",
        "government_name_inference_used": False,
        "bounded_or_explicit_structured_evidence_only": True,
        "status_counts": dict(sorted(Counter(row["residual_occupation_bridge_status"] for row in output).items())),
    }
    return output, audit


def copy_carried_forward(output_dir: Path) -> None:
    copies = {
        "quant_candidate": "quant_candidate",
        "quant_exceptions": "quant_exceptions",
        "nonbase_candidate": "nonbase_candidate",
        "reference_control": "reference_control",
        "conflict_quarantine": "conflict_quarantine",
    }
    for output_name, input_name in copies.items():
        shutil.copyfile(CURRENT_INPUTS[input_name], output_dir / OUTPUTS[output_name])


def run(output_dir: Path) -> dict[str, Any]:
    preflight = no_write_preflight(output_dir)
    current_before = {name: sha256(path) for name, path in CURRENT_INPUTS.items()}
    durable_before = {name: sha256(path) for name, path in DURABLE_INPUTS.items()}
    packet_before = {name: sha256(path) for name, path in PACKET_INPUTS.items()}
    predecessor = load_predecessor()

    ledger, repaired_qual, span_audit, repaired_qual_header = build_span_outputs()
    cycle_rows, cycle_audit = build_cycle_bridge(predecessor)
    occupation_rows, occupation_audit = build_occupation_bridge()
    output_dir.mkdir(parents=True)

    span_header = [
        "qualitative_observation_id", "extraction_case_id", "document_identity_id",
        "source_review_id", "text_table_detection_id", "raw_retained_content_hash",
        "mechanism_type", "page_number", "bounded_evidence_pointer",
        "bounded_packet_manifest_sources", "bounded_page_pointer_exact_match",
        "bounded_text_payload_available", "literal_verbatim_evidence_span", "span_start",
        "span_end", "span_length", "span_sha256", "span_capture_status",
        "span_capture_reason_code", "span_qa_pass",
    ]
    write_csv(output_dir / OUTPUTS["span_ledger"], span_header, ledger)
    write_csv(output_dir / OUTPUTS["qual_navigation"], repaired_qual_header, repaired_qual)
    write_json(output_dir / OUTPUTS["span_audit"], span_audit)

    cycle_header = list(cycle_rows[0])
    occupation_header = list(occupation_rows[0])
    write_csv(output_dir / OUTPUTS["cycle_bridge"], cycle_header, cycle_rows)
    write_csv(output_dir / OUTPUTS["occupation_bridge"], occupation_header, occupation_rows)
    write_json(output_dir / OUTPUTS["cycle_audit"], cycle_audit)
    write_json(output_dir / OUTPUTS["occupation_audit"], occupation_audit)
    copy_carried_forward(output_dir)

    hash_lines = []
    for group, inputs in (("current_followup", CURRENT_INPUTS), ("durable", DURABLE_INPUTS), ("bounded_packet", PACKET_INPUTS)):
        for name, path in sorted(inputs.items()):
            hash_lines.append(f"{sha256(path)}  {group}:{name}  {path.relative_to(ROOT)}")
    (output_dir / OUTPUTS["input_hashes"]).write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    quant_header, quant_candidates = read_rows(CURRENT_INPUTS["quant_candidate"])
    _, quant_exceptions = read_rows(CURRENT_INPUTS["quant_exceptions"])
    _, nonbase = read_rows(CURRENT_INPUTS["nonbase_candidate"])
    _, reference = read_rows(CURRENT_INPUTS["reference_control"])
    _, conflicts = read_rows(CURRENT_INPUTS["conflict_quarantine"])
    original_other = [row for row in nonbase if row.get("non_base_wage_type") == "other"]
    other_status = Counter(row.get("non_base_subtype_status", "") for row in original_other)
    if len(quant_candidates) != 862 or len(quant_exceptions) != 1045:
        raise RuntimeError("Quantitative carry-forward counts changed")
    conflict_member_count = sum(int(row.get("observation_count") or 0) for row in conflicts)
    if len(nonbase) != 4733 or len(reference) != 345 or len(conflicts) != 2 or conflict_member_count != 5:
        raise RuntimeError("Companion/control/quarantine carry-forward counts changed")

    quarantine = {
        "residual_cycle_identity_count_before": 571,
        "residual_cycle_identity_count_after": cycle_audit["revised_cycle_quarantine_count"],
        "residual_non_safety_identity_count_before": 535,
        "residual_non_safety_identity_count_after": occupation_audit["revised_non_safety_quarantine_count"],
        "qualitative_span_unavailable_or_unverified_count": span_audit["span_unavailable_or_unverified_count"],
        "quantitative_exception_count": len(quant_exceptions),
        "unresolved_conflict_group_count": 2,
        "unresolved_conflict_member_observation_count": conflict_member_count,
        "analysis_readiness": False,
    }
    write_json(output_dir / OUTPUTS["metadata_quarantine"], quarantine)

    blockers = [
        {"blocker_id": "S01", "area": "qualitative_literal_spans", "status": "blocked_missing_retained_bounded_text_payload", "affected_count": 1954, "resolution_or_boundary": "All page pointers match retained packet manifests, but no manifest retains page text; PDFs/models/extraction are prohibited."},
        {"blocker_id": "S02", "area": "residual_cycle_and_matching", "status": "partial", "affected_count": cycle_audit["revised_cycle_quarantine_count"], "resolution_or_boundary": "Only one exact full-date pair in explicit cycle metadata is accepted; all remaining absent/multiple pairs stay quarantined."},
        {"blocker_id": "S03", "area": "residual_non_safety_occupation", "status": "partial", "affected_count": occupation_audit["revised_non_safety_quarantine_count"], "resolution_or_boundary": "Only one exact controlled unit-label rule is accepted; ambiguous or unsupported labels stay quarantined."},
        {"blocker_id": "S04", "area": "quantitative_normalization", "status": "carried_forward_partial", "affected_count": len(quant_exceptions), "resolution_or_boundary": "Raw values and the 862/1,045 candidate/exception split are byte-preserved; no coercion occurred."},
        {"blocker_id": "S05", "area": "residual_conflicts", "status": "quarantined", "affected_count": conflict_member_count, "resolution_or_boundary": "Two groups/five observations remain explicitly outside candidates."},
        {"blocker_id": "S06", "area": "non_base_and_reference", "status": "separated", "affected_count": len(nonbase) + len(reference), "resolution_or_boundary": "Non-base remains companion-only and reference/exclusion remains control-only."},
    ]
    write_csv(output_dir / OUTPUTS["blockers"], ["blocker_id", "area", "status", "affected_count", "resolution_or_boundary"], blockers)

    future_prompt = """# Future task: bounded local qualitative span capture with explicit parse-text authorization

Do not run this prompt without separate user authorization.

Create and retain bounded page-text artifacts only for the existing 1,954 qualitative navigation rows, using the already-retained readable local PDFs and their exact recorded page pointers. Local PDF text-layer access must be explicitly authorized; URLs, downloads, OCR, GABRIEL/API, document selection, new compensation extraction, ingestion, codification, promotion, wage-gap calculations, regressions, and causal analysis remain prohibited.

Limit each artifact to the recorded page and a short exact mechanism span. Require exact substring, page-pointer, observation-ID, case-ID, source/detection-ID, retained-hash, start/end offset, length, and SHA-256 validation. Do not paraphrase or pre-code mechanism meaning. Keep unresolved cycle, occupation, quantitative, and conflict quarantines unchanged unless explicit structured evidence deterministically resolves them. Keep analysis readiness false and stop before another readiness review unless separately authorized.
"""
    (output_dir / OUTPUTS["future_prompt"]).write_text(future_prompt, encoding="utf-8")

    summary = f"""# Bounded qualitative span and residual metadata repair summary

Decision: `{DECISION}`

- Immutable package SHA-256 checks: 5/5 passed.
- Package, prior repair, current follow-up, and durable ledgers modified: no.
- Qualitative rows/pointers: 1,954/1,954 exact packet-page pointer matches.
- Retained bounded page-text payloads / exact literal spans: 0 / 0.
- Coded qualitative analysis view created: no; navigation-only retained.
- Exact cycle identities: {cycle_audit['prior_exact_cycle_count']} prior + {cycle_audit['new_exact_cycle_count']} new = {cycle_audit['revised_exact_cycle_count']}/1,826.
- Matched-set documents/groups: {cycle_audit['revised_matched_set_document_count']}/{cycle_audit['revised_matched_set_group_count']}.
- Controlled non-safety subclasses: {occupation_audit['prior_non_safety_subclass_count']} prior + {occupation_audit['new_non_safety_subclass_count']} new = {occupation_audit['revised_non_safety_subclass_count']}; {occupation_audit['revised_non_safety_quarantine_count']} remain quarantined.
- Quantitative candidates/exceptions: {len(quant_candidates)}/{len(quant_exceptions)}, byte-preserved.
- Non-base companion/reference control rows: {len(nonbase)}/{len(reference)}; outcome eligible: 0/0.
- Non-base original `other` rows: {len(original_other)}; dispositions preserved: {json.dumps(dict(sorted(other_status.items())), sort_keys=True)}.
- Two unresolved groups / five observations remain quarantined.
- Analysis readiness: false; repeat analysis-readiness review: not allowed.

The metadata repair used exact full-date cycle notes and exact controlled unit-label matches only. Literal qualitative span capture is blocked because the retained packet manifests contain bounded page metadata but no page-text payload, and this task prohibits reopening PDFs or rerunning extraction.
"""
    (output_dir / OUTPUTS["summary"]).write_text(summary, encoding="utf-8")

    validation = f"""# Bounded qualitative span and residual metadata repair validation

- No-write dry run: passed; writes before materialization: {preflight['writes_performed']}.
- Immutable package SHA-256 checks: 5/5 passed.
- Current follow-up anchors and packet hashes: passed.
- Prior/current/durable inputs changed during run: no.
- Qualitative page-pointer reconciliation: {span_audit['exact_bounded_page_pointer_match_count']}/1,954.
- Retained bounded page-text payload count: 0; exact literal spans accepted: 0.
- Coded qualitative analysis view created: no.
- Residual cycle scope: 571 only; exact verified repairs: {cycle_audit['new_exact_cycle_count']}.
- Residual non-safety scope: 535 only; controlled explicit-label repairs: {occupation_audit['new_non_safety_subclass_count']}.
- Quantitative candidate/exception files: byte-identical carry-forward (862/1,045).
- Non-base companion/reference control files: byte-identical carry-forward (4,733/345).
- Two unresolved groups/five observations: byte-identical quarantine carry-forward.
- Package ledgers, prior repair outputs, current follow-up outputs, durable ledgers, and packet manifests modified: no.
- URL, download, PDF opening, OCR, GABRIEL/API, extraction, selection, ingestion, codification, analysis dataset, wage-gap, regression, or causal work: none.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUTS["validation"]).write_text(validation, encoding="utf-8")

    decision = {
        "task_id": TASK_ID,
        "generated_at": now_utc(),
        "decision": DECISION,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": False,
        "next_prompt": OUTPUTS["future_prompt"],
        "next_recommendation": "seek_separate_authorization_for_bounded_local_pdf_text_layer_span_capture",
        "package_sha256_checks_passed": 5,
        "package_ledgers_mutated": False,
        "prior_repair_outputs_mutated": False,
        "current_followup_outputs_mutated": False,
        "durable_ledgers_mutated": False,
        "bounded_packet_manifests_mutated": False,
        "qualitative_span_capture": span_audit,
        "cycle_matching": cycle_audit,
        "occupation": occupation_audit,
        "quantitative": {"candidate_count": len(quant_candidates), "exception_count": len(quant_exceptions), "raw_or_normalized_values_modified": False},
        "non_base_wage": {"active_companion_count": len(nonbase), "original_other_count": len(original_other), "other_disposition_counts": dict(sorted(other_status.items())), "base_wage_outcome_eligible_count": 0},
        "reference_and_exclusion": {"active_control_count": len(reference), "analysis_outcome_eligible_count": 0},
        "quarantine": quarantine,
        "ocr_later_documents_included": False,
        "forbidden_actions_performed": [],
    }
    write_json(output_dir / OUTPUTS["decision"], decision)

    current_after = {name: sha256(path) for name, path in CURRENT_INPUTS.items()}
    durable_after = {name: sha256(path) for name, path in DURABLE_INPUTS.items()}
    packet_after = {name: sha256(path) for name, path in PACKET_INPUTS.items()}
    if current_after != current_before or durable_after != durable_before or packet_after != packet_before:
        raise RuntimeError("An immutable input changed during repair")
    # Ensure carry-forward outputs really are byte-identical.
    for output_name, input_name in {
        "quant_candidate": "quant_candidate", "quant_exceptions": "quant_exceptions",
        "nonbase_candidate": "nonbase_candidate", "reference_control": "reference_control",
        "conflict_quarantine": "conflict_quarantine",
    }.items():
        if sha256(output_dir / OUTPUTS[output_name]) != sha256(CURRENT_INPUTS[input_name]):
            raise RuntimeError(f"Carry-forward output changed bytes: {output_name}")
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    result = no_write_preflight(output) if args.dry_run else run(output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
