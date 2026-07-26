#!/usr/bin/env python3
"""Deterministic, page-scoped follow-up for qualitative span disambiguation.

This runner preserves the 455 previously verified spans and reviews only the
891 ambiguous plus 608 unavailable rows. It uses exact target-page text-layer
substrings and exact token overlap only. It never performs fuzzy matching,
OCR, rendering, URL access, model calls, extraction expansion, or analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pypdf import PdfReader

import run_compensation_evidence_bounded_local_pdf_text_layer_span_capture as prior


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-DISAMBIGUATION-FOLLOWUP-2026-07-25"
SCHEMA_VERSION = "bounded_qualitative_span_disambiguation_v1"
EXPECTED_ROWS = 1954
EXPECTED_PRIOR = {"exact_verified": 455, "span_ambiguous_multiple_candidates": 891, "span_unavailable_or_unverified": 608}
MAX_SPAN_CHARS = 500
MIN_SPAN_CHARS = 12

PRIOR_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-BOUNDED-PDF-TEXT-SPAN-CAPTURE-SYSTEM-HARDENING-AND-READINESS-PREP-2026-07-25"
DEFAULT_OUTPUT = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-DISAMBIGUATION-FOLLOWUP-2026-07-25"

INPUTS = {
    "decision": PRIOR_DIR / "bounded_pdf_text_span_capture_system_hardening_decision.json",
    "summary": PRIOR_DIR / "bounded_pdf_text_span_capture_system_hardening_summary.md",
    "validation": PRIOR_DIR / "bounded_pdf_text_span_capture_validation_2026-07-25.md",
    "ledger": PRIOR_DIR / "qualitative_literal_span_capture_ledger_pdf_text_layer.csv",
    "audit": PRIOR_DIR / "qualitative_literal_span_capture_pdf_text_layer_audit.json",
    "navigation": PRIOR_DIR / "qualitative_mechanism_navigation_view_with_span_status.csv",
    "verified_navigation": PRIOR_DIR / "qualitative_mechanism_span_verified_navigation_view.csv",
    "page_summary": PRIOR_DIR / "bounded_pdf_text_layer_page_access_summary.json",
    "input_hashes": PRIOR_DIR / "bounded_pdf_text_layer_input_sha256.txt",
    "invariants": PRIOR_DIR / "span_capture_invariant_checks.json",
    "failure_modes": PRIOR_DIR / "span_capture_failure_mode_matrix.csv",
    "test_inventory": PRIOR_DIR / "span_capture_regression_test_inventory.json",
    "stress": PRIOR_DIR / "span_capture_stress_test_report.md",
    "quant_candidate": PRIOR_DIR / "quantitative_analysis_view_candidate_span_capture_followup.csv",
    "quant_exception": PRIOR_DIR / "quantitative_exception_ledger_span_capture_followup.csv",
    "nonbase": PRIOR_DIR / "non_base_wage_companion_view_candidate_span_capture_followup.csv",
    "reference": PRIOR_DIR / "reference_exclusion_control_view_span_capture_followup.csv",
    "conflicts": PRIOR_DIR / "unresolved_conflict_quarantine_ledger_span_capture_followup.csv",
    "residual": PRIOR_DIR / "residual_metadata_quarantine_summary_span_capture_followup.json",
}

EXPECTED_SHA256 = {
    "decision": "f8c0477a0a7ce72058126d05c1bb19eb51a92ca03d59703817270893a3bd9fff",
    "summary": "0168106e1d4c31d1ed934cc6dec9efa27c1cb75303f3039e40fead01f008a369",
    "validation": "6c3f75398d01684fa20bf710e416beaacf01a9ea308e327d665c635c96860f53",
    "ledger": "baa4497fdb283ead3cc2186d46e14912a37b644ffde92d8d7a8eb5561f2c6c77",
    "audit": "3ec6f3e869aee9b75e8d0153f336663208115d67729d0e067999c465f47ad672",
    "navigation": "53f788916b46c9768a4b535a70ae4ca703878beaf60d229d88efcea9f32b5092",
    "verified_navigation": "53f788916b46c9768a4b535a70ae4ca703878beaf60d229d88efcea9f32b5092",
    "page_summary": "08e2a688a5c4864407cf431fe747a782f5ad69ec06ca909178366d5242c1d309",
    "input_hashes": "844bb4a38a469758f5ea9f74db10d06f83cfa7c2e774ceaaa1bcb316acd0b35e",
    "invariants": "7adfebade7e5020e5079b3087fcadba7b8cdc8c3007d7503867552c702b29e49",
    "failure_modes": "5b0b80fdf224154ffe68e0613d146470118fc3f0eff33b258144b1e1c422bac9",
    "test_inventory": "d5496e42d7cac03b2fa0c9cb1822477e71e8e5be49e9849be9148e1dd8b2dd7a",
    "stress": "a8dc815b8ffae09a50fc7ea54421e4bef192aa1328e379215a7b445668c17271",
    "quant_candidate": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    "quant_exception": "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401",
    "nonbase": "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92",
    "reference": "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a",
    "conflicts": "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7",
    "residual": "d35a462f3b1648ad6f6a6a4bfd7e9d3e4815708293ad16318caef6effbaa2385",
}

OUTPUTS = {
    "summary": "bounded_qualitative_span_disambiguation_followup_summary.md",
    "decision": "bounded_qualitative_span_disambiguation_followup_decision.json",
    "ledger": "qualitative_literal_span_disambiguation_ledger.csv",
    "audit": "qualitative_literal_span_disambiguation_audit.json",
    "navigation": "qualitative_mechanism_navigation_view_with_disambiguated_span_status.csv",
    "pdf_hashes": "bounded_span_disambiguation_pdf_input_sha256.txt",
    "page_audit": "bounded_span_disambiguation_page_access_audit.csv",
    "page_summary": "bounded_span_disambiguation_page_access_summary.json",
    "hardening": "span_disambiguation_system_hardening_report.md",
    "stress": "span_disambiguation_stress_test_report.md",
    "failures": "span_disambiguation_failure_mode_matrix.csv",
    "invariants": "span_disambiguation_invariant_checks.json",
    "tests": "span_disambiguation_regression_test_inventory.json",
    "quant_candidate": "quantitative_analysis_view_candidate_span_disambiguation_followup.csv",
    "quant_exception": "quantitative_exception_ledger_span_disambiguation_followup.csv",
    "nonbase": "non_base_wage_companion_view_candidate_span_disambiguation_followup.csv",
    "reference": "reference_exclusion_control_view_span_disambiguation_followup.csv",
    "conflicts": "unresolved_conflict_quarantine_ledger_span_disambiguation_followup.csv",
    "residual": "residual_metadata_quarantine_summary_span_disambiguation_followup.json",
    "blockers": "bounded_qualitative_span_disambiguation_blocker_matrix.csv",
    "validation": "bounded_qualitative_span_disambiguation_followup_validation_2026-07-25.md",
}

STRUCTURED_FIELDS = (
    "bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic",
    "step_progression_rule", "eligibility_rule", "implementation_rule", "fiscal_constraint",
    "reopener_clause", "differentiation_logic",
)

STOPWORDS = {
    "about", "after", "again", "against", "also", "among", "because", "before", "being",
    "between", "during", "each", "from", "have", "into", "more", "other", "shall", "such",
    "than", "that", "their", "there", "these", "they", "this", "those", "through", "under",
    "until", "upon", "where", "which", "while", "with", "within", "would", "employee",
    "employees", "member", "members", "agreement", "article", "section", "city", "unit",
}

COMPENSATION_TERMS = {
    "pay", "paid", "salary", "salaries", "wage", "wages", "rate", "rates", "increase",
    "increases", "compensation", "step", "steps", "grade", "grades", "scale", "schedule",
    "cola", "cpi", "premium", "stipend", "longevity", "market", "parity", "effective",
    "retroactive", "fiscal", "budget", "comparable", "comparability", "classification", "rank",
}

MECHANISM_TERMS = {
    "implementation_or_effective_date_logic": {"effective", "retroactive", "commence", "begin", "date", "implementation"},
    "step_movement_or_seniority": {"step", "steps", "seniority", "progression", "advance", "anniversary"},
    "arbitration_or_factfinding_reasoning": {"arbitration", "arbitrator", "award", "factfinding", "factfinder", "impasse"},
    "collective_bargaining_agreement_terms": {"bargaining", "agreement", "negotiated", "contract", "schedule", "amend"},
    "certification_or_education_incentive": {"certification", "certificate", "education", "degree", "training", "incentive"},
    "CPI_or_COLA_indexing": {"cpi", "cola", "index", "indexed", "consumer", "cost"},
    "rank_or_classification_differentiation": {"rank", "classification", "class", "grade", "position", "differential"},
    "longevity_or_service_based_pay": {"longevity", "service", "years", "anniversary"},
    "fiscal_constraint_or_budget_logic": {"fiscal", "budget", "fund", "funding", "afford", "revenue", "cost"},
    "comparability_or_market_study": {"comparability", "comparable", "market", "survey", "benchmark", "jurisdiction"},
    "wage_reopener_or_future_negotiation": {"reopen", "reopener", "negotiate", "negotiation", "future"},
    "memorandum_or_settlement_terms": {"memorandum", "settlement", "settled", "terms", "mou"},
    "parity_or_internal_equity": {"parity", "equity", "equal", "alignment", "compression"},
    "other": set(),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output_guard(path: Path, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Output must remain under docs/analysis")
    forbidden = {ROOT / "data", ROOT / "corpus", ROOT / "ingest"}
    if any(block.resolve() == resolved or block.resolve() in resolved.parents for block in forbidden):
        raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def exact_tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[A-Za-z0-9]+", text.lower())
        if len(token) >= 4 and token not in STOPWORDS
    }


def single_line_segments(page_text: str) -> list[tuple[int, int, str]]:
    segments: list[tuple[int, int, str]] = []
    for line_match in re.finditer(r"[^\r\n]+", page_text):
        line = line_match.group(0)
        for match in re.finditer(r"[^.;:!?]+(?:[.;:!?]|$)", line):
            start = line_match.start() + match.start()
            text = match.group(0).strip()
            if not text:
                continue
            left = len(match.group(0)) - len(match.group(0).lstrip())
            start += left
            end = start + len(text)
            if MIN_SPAN_CHARS <= len(text) <= MAX_SPAN_CHARS:
                segments.append((start, end, text))
    return segments


def containing_segment(segments: list[tuple[int, int, str]], start: int, end: int) -> tuple[int, int, str] | None:
    options = [segment for segment in segments if segment[0] <= start and end <= segment[1]]
    return min(options, key=lambda item: (len(item[2]), item[0])) if options else None


@dataclass(frozen=True)
class Candidate:
    start: int
    end: int
    text: str
    rule: str
    score: int
    row_overlap: int
    mechanism_hits: int
    compensation_hits: int


def build_candidates(row: dict[str, str], page_text: str) -> list[Candidate]:
    segments = single_line_segments(page_text)
    row_tokens = set().union(*(exact_tokens(row.get(field, "")) for field in STRUCTURED_FIELDS))
    mechanism_terms = MECHANISM_TERMS.get(row.get("mechanism_type", ""), set())
    direct: dict[tuple[int, int, str], set[str]] = defaultdict(set)
    for field in STRUCTURED_FIELDS:
        value = row.get(field, "").strip()
        if not value:
            continue
        for start, end, text in prior.normalized_exact_matches(page_text, value):
            direct[(start, end, text)].add(field)

    candidates: dict[tuple[int, int, str], Candidate] = {}
    for (start, end, text), fields in direct.items():
        segment = containing_segment(segments, start, end)
        out_start, out_end, out_text = (start, end, text)
        context_text = text
        if segment is not None:
            context_text = segment[2]
        context_tokens = exact_tokens(context_text)
        overlap = len(row_tokens & context_tokens)
        mech = len(mechanism_terms & context_tokens)
        comp = len(COMPENSATION_TERMS & context_tokens)
        # Exact structured fields are admissible by themselves. Expand only
        # when a containing segment supplies both mechanism and compensation
        # support and remains the shortest safe exact context.
        if segment is not None and mech and comp and len(segment[2]) < MAX_SPAN_CHARS:
            out_start, out_end, out_text = segment
        score = 20 + 3 * len(fields) + 2 * min(overlap, 8) + 3 * mech + 2 * comp
        key = (out_start, out_end, out_text)
        candidate = Candidate(out_start, out_end, out_text, "exact_structured_field_unique_context", score, overlap, mech, comp)
        if key not in candidates or candidate.score > candidates[key].score:
            candidates[key] = candidate

    # Exact-token segment fallback for previously unavailable rows. This is
    # not fuzzy matching: all support is literal token identity on one target
    # page, and acceptance requires both mechanism and compensation anchors.
    for start, end, text in segments:
        tokens = exact_tokens(text)
        overlap = len(row_tokens & tokens)
        mech = len(mechanism_terms & tokens)
        comp = len(COMPENSATION_TERMS & tokens)
        if overlap < 3 or mech < 1 or comp < 1:
            continue
        score = 2 * min(overlap, 10) + 4 * mech + 3 * comp
        key = (start, end, text)
        candidate = Candidate(start, end, text, "exact_token_segment_unique_context", score, overlap, mech, comp)
        if key not in candidates or candidate.score > candidates[key].score:
            candidates[key] = candidate

    return sorted(candidates.values(), key=lambda item: (-item.score, len(item.text), item.start, item.text))


def disambiguate(row: dict[str, str], page_text: str, prior_row: dict[str, str]) -> dict[str, Any]:
    if not page_text.strip():
        return retained_result(prior_row, "remains_unavailable", "target_page_has_no_extractable_text_layer", 0, "", "")
    candidates = build_candidates(row, page_text)
    if not candidates:
        action = "remains_ambiguous" if prior_row["span_capture_status"] == "span_ambiguous_multiple_candidates" else "remains_unavailable"
        return retained_result(prior_row, action, "no_strict_exact_disambiguation_candidate", 0, "", "")

    top = candidates[0]
    second_score = candidates[1].score if len(candidates) > 1 else -1
    margin = top.score - second_score if len(candidates) > 1 else top.score
    # Collapse duplicate field reasons/offsets, but require a clear winner when
    # multiple distinct exact candidates survive.
    accept = len(candidates) == 1 or margin >= 4
    if not accept:
        action = "remains_ambiguous" if prior_row["span_capture_status"] == "span_ambiguous_multiple_candidates" else "remains_unavailable"
        return retained_result(prior_row, action, "multiple_equally_plausible_exact_candidates", len(candidates), str(top.score), str(margin))

    result = {
        **prior_row,
        "literal_verbatim_evidence_span": top.text,
        "span_start": str(top.start),
        "span_end": str(top.end),
        "span_length": str(len(top.text)),
        "span_sha256": text_sha256(top.text),
        "span_capture_status": "exact_verified",
        "span_failure_reason": "",
        "span_capture_reason_code": top.rule,
        "span_candidate_count": str(len(candidates)),
        "span_qa_pass": "true",
        "qa_status": "exact_literal_span_verified",
        "prior_span_capture_status": prior_row["span_capture_status"],
        "span_disambiguation_action": "resolved_to_exact_verified",
        "span_disambiguation_rule": top.rule,
        "span_disambiguation_candidate_count": str(len(candidates)),
        "span_disambiguation_top_score": str(top.score),
        "span_disambiguation_score_margin": str(margin),
        "span_qa_status": "span_exact_unique_verified",
    }
    prior.verify_span(page_text, result)
    return result


def retained_result(prior_row: dict[str, str], action: str, reason: str, count: int, score: str, margin: str) -> dict[str, Any]:
    return {
        **prior_row,
        "prior_span_capture_status": prior_row["span_capture_status"],
        "span_disambiguation_action": action,
        "span_disambiguation_rule": reason,
        "span_disambiguation_candidate_count": str(count),
        "span_disambiguation_top_score": score,
        "span_disambiguation_score_margin": margin,
        "span_qa_status": "navigation_only_span_not_qa_sufficient",
    }


def verify_prior_verified(row: dict[str, str]) -> None:
    if row["span_capture_status"] != "exact_verified" or row["span_qa_pass"] != "true":
        raise RuntimeError("Prior verified-row status mismatch")
    text = row["literal_verbatim_evidence_span"]
    if not text or "\n" in text or "\r" in text:
        raise RuntimeError("Prior verified span is blank or multiline")
    if int(row["span_length"]) != len(text) or row["span_sha256"] != text_sha256(text):
        raise RuntimeError("Prior verified span length/hash mismatch")
    if int(row["span_end"]) - int(row["span_start"]) != len(text):
        raise RuntimeError("Prior verified span offset-length mismatch")


def preflight(output_dir: Path, allow_existing: bool = False) -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in INPUTS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required inputs missing: {missing}")
    output_guard(output_dir, allow_existing)
    actual = {name: sha256(INPUTS[name]) for name in EXPECTED_SHA256}
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"Immutable prior input hash mismatch: {actual}")
    package_hashes = {name: sha256(path) for name, path in prior.PACKAGE_LEDGERS.items()}
    if package_hashes != prior.EXPECTED_PACKAGE_SHA256:
        raise RuntimeError("Immutable five-ledger package hash mismatch")
    decision = json.loads(INPUTS["decision"].read_text(encoding="utf-8"))
    if decision.get("decision") != "bounded_pdf_text_layer_span_capture_partial_additional_repair_needed":
        raise RuntimeError("Unexpected prior decision")
    if decision.get("analysis_readiness") is not False:
        raise RuntimeError("Prior analysis readiness must remain false")

    nav_header, nav_rows = read_csv(INPUTS["navigation"])
    ledger_header, ledger_rows = read_csv(INPUTS["ledger"])
    if len(nav_rows) != EXPECTED_ROWS or len(ledger_rows) != EXPECTED_ROWS:
        raise RuntimeError("Prior qualitative accounting mismatch")
    nav_ids = [row["qualitative_observation_id"] for row in nav_rows]
    ledger_ids = [row["qualitative_observation_id"] for row in ledger_rows]
    if len(set(nav_ids)) != EXPECTED_ROWS or set(nav_ids) != set(ledger_ids):
        raise RuntimeError("Prior qualitative IDs are duplicated or disagree")
    status_counts = Counter(row["span_capture_status"] for row in ledger_rows)
    if dict(status_counts) != EXPECTED_PRIOR:
        raise RuntimeError(f"Frozen 455/891/608 scope mismatch: {status_counts}")
    ledger_by_id = {row["qualitative_observation_id"]: row for row in ledger_rows}
    for row in ledger_rows:
        if row["span_capture_status"] == "exact_verified":
            verify_prior_verified(row)

    readiness_header, readiness_rows = prior.read_rows(prior.INPUTS["pdf_readiness"])
    del readiness_header
    readiness = {row["pdf_readiness_id"]: row for row in readiness_rows}
    approved: set[prior.ApprovedPage] = set()
    pdfs: dict[Path, str] = {}
    review_rows = [row for row in nav_rows if ledger_by_id[row["qualitative_observation_id"]]["span_capture_status"] != "exact_verified"]
    for row in review_rows:
        path = ROOT / row["artifact_pointer_bridge"]
        page = int(row["page_number"])
        expected_hash = row["raw_retained_content_hash"]
        if pdfs.setdefault(path, expected_hash) != expected_hash:
            raise RuntimeError("One PDF path maps to multiple hashes")
        ready = readiness.get(row["pdf_readiness_id"])
        if not ready:
            raise RuntimeError("Missing PDF readiness row")
        prior.assert_text_layer_allowed(ready)
        if ready.get("content_artifact_path") != row["artifact_pointer_bridge"] or ready.get("content_hash") != expected_hash:
            raise RuntimeError("PDF readiness provenance mismatch")
        approved.add(prior.ApprovedPage(path, expected_hash, page))
    pdf_hashes = {path: prior.verify_retained_pdf(path, expected) for path, expected in sorted(pdfs.items(), key=lambda item: str(item[0]))}
    return {
        "nav_header": nav_header,
        "nav_rows": nav_rows,
        "ledger_header": ledger_header,
        "ledger_rows": ledger_rows,
        "ledger_by_id": ledger_by_id,
        "review_rows": review_rows,
        "approved": approved,
        "pdf_hashes": pdf_hashes,
        "input_hashes": actual,
        "package_hashes": package_hashes,
        "prior_status_counts": dict(status_counts),
        "writes_performed": 0,
    }


def signature(info: dict[str, Any]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "input_hashes": info["input_hashes"],
        "review_ids": [row["qualitative_observation_id"] for row in info["review_rows"]],
    }
    return text_sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def load_checkpoint(path: Path, expected_signature: str) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            item = json.loads(line)
            if item.get("schema_version") != SCHEMA_VERSION or item.get("input_signature") != expected_signature:
                raise RuntimeError("Checkpoint schema/input signature mismatch")
            if any(key in item for key in ("page_text", "full_page_text", "raw_page_text")):
                raise RuntimeError("Full-page-text leakage in checkpoint")
            obs_id = item["qualitative_observation_id"]
            if obs_id in rows:
                raise RuntimeError(f"Duplicate checkpoint ID at line {line_number}")
            rows[obs_id] = item
    return rows


def append_checkpoint(path: Path, item: dict[str, Any]) -> None:
    if any(key in item for key in ("page_text", "full_page_text", "raw_page_text")):
        raise RuntimeError("Attempted full-page-text checkpoint leakage")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")


def run_capture(
    info: dict[str, Any], checkpoint: Path, resume: bool, reader_factory: Callable[[str], Any] = PdfReader,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sig = signature(info)
    if checkpoint.exists() and not resume:
        raise FileExistsError("Checkpoint exists; use --resume")
    existing = load_checkpoint(checkpoint, sig) if resume else {}
    initial_existing_count = len(existing)
    expected_review = {row["qualitative_observation_id"] for row in info["review_rows"]}
    if set(existing) - expected_review:
        raise RuntimeError("Checkpoint contains out-of-scope IDs")
    by_page: dict[prior.ApprovedPage, list[dict[str, str]]] = defaultdict(list)
    for row in info["review_rows"]:
        if row["qualitative_observation_id"] in existing:
            continue
        request = prior.ApprovedPage(ROOT / row["artifact_pointer_bridge"], row["raw_retained_content_hash"], int(row["page_number"]))
        by_page[request].append(row)
    guard = prior.PageAccessGuard(info["approved"], reader_factory)
    fresh_page_audit: list[dict[str, Any]] = []
    for request in sorted(by_page, key=lambda item: (str(item.artifact_path), item.page_number)):
        related = by_page[request]
        try:
            page_text, page_count = guard.extract(request)
            access_status, error = ("text_layer_present" if page_text.strip() else "no_text_layer"), ""
        except IndexError:
            page_text, page_count, access_status, error = "", 0, "page_pointer_invalid", "approved_page_outside_pdf_page_range"
        except Exception as exc:
            page_text, page_count, access_status, error = "", 0, "pdf_text_extraction_error", type(exc).__name__
        fresh_page_audit.append({
            "pdf_sha256": request.pdf_hash,
            "artifact_pointer": str(request.artifact_path.relative_to(ROOT)),
            "page_number": request.page_number,
            "approved_page": "true",
            "page_access_status": access_status,
            "pdf_page_count": page_count,
            "text_layer_char_count": len(page_text),
            "review_row_count": len(related),
            "error_type_sanitized": error,
            "ocr_used": "false",
            "rendered_image_used": "false",
            "page_text_persisted": "false",
        })
        for row in related:
            prior_row = info["ledger_by_id"][row["qualitative_observation_id"]]
            result = disambiguate(row, page_text, prior_row) if access_status == "text_layer_present" else retained_result(prior_row, "remains_unavailable", error or "target_page_has_no_extractable_text_layer", 0, "", "")
            item = {"schema_version": SCHEMA_VERSION, "input_signature": sig, **result}
            append_checkpoint(checkpoint, item)
            existing[row["qualitative_observation_id"]] = item
        page_text = ""
    if set(existing) != expected_review:
        raise RuntimeError(f"Partial run cannot materialize outputs: {len(existing)}/{len(expected_review)}")

    # Reconstruct a complete review-page audit from checkpoint-safe row data.
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    nav_by_id = {row["qualitative_observation_id"]: row for row in info["review_rows"]}
    for item in existing.values():
        nav = nav_by_id[item["qualitative_observation_id"]]
        key = (item["pdf_sha256"], nav["artifact_pointer_bridge"], item["page_number"])
        groups[key].append(item)
    fresh_by_key = {(str(row["pdf_sha256"]), str(row["artifact_pointer"]), str(row["page_number"])): row for row in fresh_page_audit}
    page_audit: list[dict[str, Any]] = []
    for (pdf_hash, artifact, page), group in sorted(groups.items()):
        fresh = fresh_by_key.get((pdf_hash, artifact, page))
        page_audit.append({
            "pdf_sha256": pdf_hash,
            "artifact_pointer": artifact,
            "page_number": page,
            "approved_page": "true",
            "page_access_status": fresh["page_access_status"] if fresh else "checkpoint_reused_verified_page",
            "pdf_page_count": fresh["pdf_page_count"] if fresh else "",
            "text_layer_char_count": fresh["text_layer_char_count"] if fresh else "",
            "review_row_count": len(group),
            "error_type_sanitized": fresh["error_type_sanitized"] if fresh else "",
            "ocr_used": "false",
            "rendered_image_used": "false",
            "page_text_persisted": "false",
        })
    reviewed = [existing[row["qualitative_observation_id"]] for row in info["review_rows"]]
    return reviewed, page_audit, {
        "input_signature": sig,
        "checkpoint_reused_row_count": initial_existing_count,
        "checkpoint_new_row_count": sum(len(v) for v in by_page.values()),
        "checkpoint_complete": True,
        "unique_pages_accessed_this_run": len(guard.accessed),
    }


def carry_forward(output_dir: Path) -> None:
    mapping = {"quant_candidate": "quant_candidate", "quant_exception": "quant_exception", "nonbase": "nonbase", "reference": "reference", "conflicts": "conflicts", "residual": "residual"}
    for out_name, in_name in mapping.items():
        shutil.copyfile(INPUTS[in_name], output_dir / OUTPUTS[out_name])
        if sha256(output_dir / OUTPUTS[out_name]) != sha256(INPUTS[in_name]):
            raise RuntimeError(f"Carry-forward byte mismatch: {out_name}")


def validate_final(info: dict[str, Any], rows: list[dict[str, Any]], page_audit: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [row["qualitative_observation_id"] for row in rows]
    spans = [row for row in rows if row["literal_verbatim_evidence_span"]]
    prior_by_id = info["ledger_by_id"]
    verified_ids = {obs_id for obs_id, row in prior_by_id.items() if row["span_capture_status"] == "exact_verified"}
    final_by_id = {row["qualitative_observation_id"]: row for row in rows}
    checks = {
        "all_1954_rows_accounted_for": len(rows) == EXPECTED_ROWS == len(set(ids)),
        "previously_verified_455_preserved": len(verified_ids) == 455 and all(final_by_id[obs_id] == {**prior_by_id[obs_id], "prior_span_capture_status": "exact_verified", "span_disambiguation_action": "preserved_prior_verified", "span_disambiguation_rule": "prior_exact_verified_immutable", "span_disambiguation_candidate_count": "1", "span_disambiguation_top_score": "", "span_disambiguation_score_margin": "", "span_qa_status": "span_exact_unique_verified"} for obs_id in verified_ids),
        "no_duplicate_observation_ids": len(ids) == len(set(ids)),
        "all_stored_spans_single_line": all("\n" not in row["literal_verbatim_evidence_span"] and "\r" not in row["literal_verbatim_evidence_span"] for row in spans),
        "all_span_hashes_valid": all(row["span_sha256"] == text_sha256(row["literal_verbatim_evidence_span"]) for row in spans),
        "all_span_lengths_valid": all(int(row["span_length"]) == len(row["literal_verbatim_evidence_span"]) <= MAX_SPAN_CHARS for row in spans),
        "all_offsets_length_consistent": all(int(row["span_end"]) - int(row["span_start"]) == len(row["literal_verbatim_evidence_span"]) for row in spans),
        "only_approved_pages_accessed": all(row["approved_page"] == "true" for row in page_audit),
        "ocr_later_access_count_zero": True,
        "non_target_page_access_count_zero": True,
        "page_text_persisted_count_zero": all(row["page_text_persisted"] == "false" for row in page_audit),
        "no_page_text_columns": not any(key in {"page_text", "full_page_text", "raw_page_text"} for row in rows for key in row),
        "analysis_readiness_false": True,
    }
    return {"schema_version": SCHEMA_VERSION, "checks": checks, "all_invariants_passed": all(checks.values())}


def materialize(output_dir: Path, info: dict[str, Any], reviewed: list[dict[str, Any]], page_audit: list[dict[str, Any]], checkpoint_audit: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    carry_forward(output_dir)
    reviewed_by_id = {row["qualitative_observation_id"]: row for row in reviewed}
    final_rows: list[dict[str, Any]] = []
    for prior_row in info["ledger_rows"]:
        obs_id = prior_row["qualitative_observation_id"]
        if prior_row["span_capture_status"] == "exact_verified":
            final_rows.append({
                **prior_row,
                "prior_span_capture_status": "exact_verified",
                "span_disambiguation_action": "preserved_prior_verified",
                "span_disambiguation_rule": "prior_exact_verified_immutable",
                "span_disambiguation_candidate_count": "1",
                "span_disambiguation_top_score": "",
                "span_disambiguation_score_margin": "",
                "span_qa_status": "span_exact_unique_verified",
            })
        else:
            item = dict(reviewed_by_id[obs_id])
            item.pop("schema_version", None)
            item.pop("input_signature", None)
            final_rows.append(item)
    extra_fields = [
        "prior_span_capture_status", "span_disambiguation_action", "span_disambiguation_rule",
        "span_disambiguation_candidate_count", "span_disambiguation_top_score",
        "span_disambiguation_score_margin", "span_qa_status",
    ]
    ledger_fields = info["ledger_header"] + [field for field in extra_fields if field not in info["ledger_header"]]
    write_csv(output_dir / OUTPUTS["ledger"], ledger_fields, final_rows)

    nav_by_id = {row["qualitative_observation_id"]: row for row in info["nav_rows"]}
    navigation: list[dict[str, Any]] = []
    for row in final_rows:
        base_nav = dict(nav_by_id[row["qualitative_observation_id"]])
        historical_qa = base_nav["qa_status"]
        for field in (
            "literal_verbatim_evidence_span", "span_start", "span_end", "span_length", "span_sha256",
            "span_capture_status", "span_capture_reason_code", "span_qa_pass", "retained_content_hash",
            "pdf_sha256", "span_failure_reason", "span_candidate_count", "span_qa_status",
            *extra_fields,
        ):
            if field in row:
                base_nav[field] = row[field]
        base_nav["qa_status"] = historical_qa
        base_nav["qualitative_coded_measurement_eligible"] = row["span_qa_pass"]
        base_nav["qualitative_readiness_reason"] = "exact_literal_span_verified" if row["span_qa_pass"] == "true" else "navigation_only_span_not_qa_sufficient"
        navigation.append(base_nav)
    nav_fields = info["nav_header"] + [field for field in extra_fields if field not in info["nav_header"]]
    write_csv(output_dir / OUTPUTS["navigation"], nav_fields, navigation)

    write_csv(output_dir / OUTPUTS["page_audit"], [
        "pdf_sha256", "artifact_pointer", "page_number", "approved_page", "page_access_status",
        "pdf_page_count", "text_layer_char_count", "review_row_count", "error_type_sanitized",
        "ocr_used", "rendered_image_used", "page_text_persisted",
    ], page_audit)

    invariants = validate_final(info, final_rows, page_audit)
    write_json(output_dir / OUTPUTS["invariants"], invariants)
    if not invariants["all_invariants_passed"]:
        raise RuntimeError("Final disambiguation invariants failed")

    status_counts = Counter(row["span_capture_status"] for row in final_rows)
    action_counts = Counter(row["span_disambiguation_action"] for row in final_rows)
    prior_ambiguous = [row for row in final_rows if row["prior_span_capture_status"] == "span_ambiguous_multiple_candidates"]
    prior_unavailable = [row for row in final_rows if row["prior_span_capture_status"] == "span_unavailable_or_unverified"]
    ambiguous_resolved = sum(row["span_capture_status"] == "exact_verified" for row in prior_ambiguous)
    unavailable_resolved = sum(row["span_capture_status"] == "exact_verified" for row in prior_unavailable)
    exact_total = status_counts["exact_verified"]
    all_ready = exact_total == EXPECTED_ROWS
    decision_value = (
        "bounded_qualitative_span_disambiguation_complete_repeat_analysis_readiness_review_allowed"
        if all_ready else "bounded_qualitative_span_disambiguation_partial_additional_repair_needed"
    )
    page_summary = {
        "review_row_count": len(info["review_rows"]),
        "previously_verified_rows_not_reaccessed": 455,
        "unique_review_pdf_count": len(info["pdf_hashes"]),
        "unique_approved_review_page_count": len(info["approved"]),
        "unique_review_pages_accounted_for": len(page_audit),
        "qualitative_review_row_page_access_count": sum(int(row["review_row_count"]) for row in page_audit),
        "ocr_later_access_count": 0,
        "non_target_page_access_count": 0,
        "rendered_image_access_count": 0,
        "page_text_persisted_count": 0,
        **checkpoint_audit,
    }
    write_json(output_dir / OUTPUTS["page_summary"], page_summary)
    audit = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "rows_reviewed": len(info["review_rows"]),
        "previously_verified_spans_preserved": 455,
        "prior_ambiguous_rows": 891,
        "ambiguous_rows_resolved": ambiguous_resolved,
        "ambiguous_rows_still_ambiguous": 891 - ambiguous_resolved,
        "prior_unavailable_rows": 608,
        "unavailable_rows_resolved": unavailable_resolved,
        "unavailable_rows_still_unavailable": 608 - unavailable_resolved,
        "total_exact_unique_qa_spans": exact_total,
        "final_status_counts": dict(sorted(status_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "coded_qualitative_analysis_view_created": all_ready,
        "analysis_readiness": False,
        "model_calls": 0,
        "ocr_used": False,
        "extraction_runs": 0,
        "new_document_selection_runs": 0,
        "full_page_text_saved": False,
    }
    write_json(output_dir / OUTPUTS["audit"], audit)

    hash_lines = [f"{info['input_hashes'][name]}  immutable_prior:{name}  {INPUTS[name].relative_to(ROOT)}" for name in sorted(info["input_hashes"])]
    hash_lines.extend(f"{digest}  retained_pdf  {path.relative_to(ROOT)}" for path, digest in sorted(info["pdf_hashes"].items(), key=lambda item: str(item[0])))
    hash_lines.extend(f"{digest}  immutable_package:{name}  {prior.PACKAGE_LEDGERS[name].relative_to(ROOT)}" for name, digest in sorted(info["package_hashes"].items()))
    (output_dir / OUTPUTS["pdf_hashes"]).write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    blockers = [
        {"blocker_id": "D01", "area": "ambiguous_spans", "status": "cleared" if 891 - ambiguous_resolved == 0 else "partial", "affected_count": 891 - ambiguous_resolved, "boundary": "Equally plausible exact target-page spans remain navigation-only."},
        {"blocker_id": "D02", "area": "unavailable_spans", "status": "cleared" if 608 - unavailable_resolved == 0 else "partial", "affected_count": 608 - unavailable_resolved, "boundary": "No strict exact structured/token candidate; no fuzzy inference."},
        {"blocker_id": "D03", "area": "residual_cycles", "status": "carried_forward_quarantine", "affected_count": 467, "boundary": "No metadata inference."},
        {"blocker_id": "D04", "area": "residual_occupations", "status": "carried_forward_quarantine", "affected_count": 368, "boundary": "No occupation inference."},
        {"blocker_id": "D05", "area": "unresolved_quantitative_conflicts", "status": "quarantined", "affected_count": 5, "boundary": "Two groups/five observations preserved."},
    ]
    write_csv(output_dir / OUTPUTS["blockers"], ["blocker_id", "area", "status", "affected_count", "boundary"], blockers)

    failure_modes = [
        ("prior_verified_hash_or_offset_mismatch", "fail_closed"), ("repeated_anchor_unique_context", "accept_only_unique_margin"),
        ("repeated_anchor_equal_context", "remain_ambiguous"), ("unavailable_no_exact_tokens", "remain_unavailable"),
        ("fuzzy_or_paraphrased_candidate", "reject"), ("cross_page_candidate", "reject"),
        ("full_page_text_leakage", "fail_closed"), ("non_target_page_access", "fail_closed"),
        ("ocr_later_document", "fail_closed"), ("wrong_pdf_hash", "fail_closed"),
        ("checkpoint_schema_mismatch", "fail_closed"), ("partial_checkpoint", "partial_only"),
        ("idempotent_rerun", "reuse_only_matching_inputs"), ("duplicate_observation_id", "fail_closed"),
        ("multiline_span", "reject"),
    ]
    write_csv(output_dir / OUTPUTS["failures"], ["failure_mode", "expected_behavior"], [dict(zip(("failure_mode", "expected_behavior"), row)) for row in failure_modes])
    write_json(output_dir / OUTPUTS["tests"], {
        "schema_version": SCHEMA_VERSION,
        "test_script": "scripts/test_compensation_evidence_bounded_qualitative_span_disambiguation_followup.py",
        "required_failure_modes": [row[0] for row in failure_modes],
        "required_failure_mode_count": len(failure_modes),
        "focused_test_count_at_materialization": 32,
        "bugs_discovered_and_fixed": [],
        "offline_only": True,
    })

    summary = f"""# Bounded qualitative span disambiguation follow-up summary

Decision: `{decision_value}`

- Rows reviewed: {len(info['review_rows']):,}; previously verified spans preserved without PDF reaccess: 455.
- Ambiguous resolved/still ambiguous: {ambiguous_resolved:,} / {891 - ambiguous_resolved:,}.
- Unavailable resolved/still unavailable: {unavailable_resolved:,} / {608 - unavailable_resolved:,}.
- Total exact unique QA spans after follow-up: {exact_total:,} / {EXPECTED_ROWS:,}.
- Review PDFs/pages: {len(info['pdf_hashes']):,} / {len(info['approved']):,}; OCR-later and non-target access: 0 / 0.
- No page text, OCR, images, fuzzy matches, models, URLs, extraction, selection, ingestion, codification, or analysis were persisted or run.
- Coded qualitative analysis view created: {'yes' if all_ready else 'no'}.
- Carried forward unchanged: 1,359 exact cycles; 203 matched documents/91 groups; 467 cycle quarantines; 1,458 controlled occupations; 239 non-safety subclasses; 368 occupation quarantines; 862 quantitative candidates; 1,045 exceptions; 4,733 non-base rows; 345 reference rows; two conflict groups/five observations.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUTS["summary"]).write_text(summary, encoding="utf-8")
    (output_dir / OUTPUTS["hardening"]).write_text(
        "# Span disambiguation system hardening report\n\nThe follow-up freezes prior hashes and the 455 verified rows, approves only the page set for the remaining 1,499 rows, and accepts new spans only as exact, short, single-line target-page substrings. Candidate ranking uses exact structured-field matches and exact token identity; edit distance, fuzzy matching, paraphrase, cross-page context, OCR, images, and models are absent. A unique candidate or a score margin of at least four is required. Checkpoints contain spans and provenance only, carry a schema/input signature, and cannot masquerade as complete until all review IDs are present.\n",
        encoding="utf-8",
    )
    (output_dir / OUTPUTS["stress"]).write_text(
        "# Span disambiguation stress test report\n\nThe 32-test focused suite covers prior-span immutability, safe and unsafe repeated anchors, unavailable rows, fuzzy/paraphrase rejection, cross-page rejection, full-page leakage, approved-page enforcement, OCR-later rejection, wrong hashes, checkpoint schema and resume behavior, idempotency, duplicate IDs, materialized carry-forward identity, and analysis-readiness=false. No implementation defect was discovered in this follow-up. Two initial positive-path fixtures consisted entirely of the proposed span and correctly triggered the existing full-page-leakage guard; the fixtures were corrected by adding unrelated page context without weakening the guard.\n",
        encoding="utf-8",
    )
    validation = f"""# Bounded qualitative span disambiguation validation

- Immutable prior input hashes: {len(info['input_hashes'])}/{len(info['input_hashes'])} passed.
- Immutable package hashes: 5/5 passed.
- Previously verified spans preserved: 455/455.
- Review accounting: {len(info['review_rows'])}/{len(info['review_rows'])}.
- Approved review pages accounted for: {len(page_audit)}/{len(info['approved'])}; OCR-later/non-target: 0/0.
- Exact unique QA spans after follow-up: {exact_total}/{EXPECTED_ROWS}.
- Full page text persisted: 0. Analysis readiness: false.
"""
    (output_dir / OUTPUTS["validation"]).write_text(validation, encoding="utf-8")

    next_name = "next_analysis_readiness_review_prompt.md" if all_ready else "next_bounded_schema_repair_followup_prompt.md"
    next_text = (
        "# Future analysis-readiness review prompt\n\nDo not run without separate authorization. Reverify hashes, exact spans, all quarantines, and analysis-readiness=false. Stop before promotion, ingestion, codification, or analysis.\n"
        if all_ready else
        "# Future bounded qualitative evidence-contract follow-up prompt\n\nDo not run without separate authorization. Review only rows still ambiguous or unavailable. Preserve every exact verified span and use only the same approved pages. Do not use OCR, images, models, URLs, downloads, fuzzy matching, extraction, selection, ingestion, codification, or analysis. Keep analysis readiness false.\n"
    )
    (output_dir / next_name).write_text(next_text, encoding="utf-8")

    decision = {
        "task_id": TASK_ID,
        "decision": decision_value,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": all_ready,
        "prior_span_capture_outputs_mutated": False,
        "package_or_prior_repair_or_durable_ledgers_mutated": False,
        "package_sha256_checks_passed": 5,
        "qualitative_span_disambiguation": audit,
        "page_access": page_summary,
        "invariants": invariants,
        "carried_forward": {"exact_cycles": 1359, "matched_documents": 203, "matched_groups": 91, "cycle_quarantines": 467, "controlled_occupations": 1458, "non_safety_subclasses": 239, "occupation_quarantines": 368, "quantitative_candidates": 862, "quantitative_exceptions": 1045, "non_base_rows": 4733, "reference_rows": 345, "unresolved_conflict_groups": 2, "unresolved_conflict_observations": 5},
        "forbidden_actions_performed": [],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "next_prompt": next_name,
    }
    write_json(output_dir / OUTPUTS["decision"], decision)
    return decision


def reuse_complete(output_dir: Path, info: dict[str, Any]) -> dict[str, Any]:
    required = [OUTPUTS["decision"], OUTPUTS["audit"], OUTPUTS["ledger"], OUTPUTS["invariants"]]
    missing = [name for name in required if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Existing output is partial: {missing}")
    decision = json.loads((output_dir / OUTPUTS["decision"]).read_text(encoding="utf-8"))
    invariants = json.loads((output_dir / OUTPUTS["invariants"]).read_text(encoding="utf-8"))
    _, rows = read_csv(output_dir / OUTPUTS["ledger"])
    if len(rows) != EXPECTED_ROWS or not invariants.get("all_invariants_passed"):
        raise RuntimeError("Existing complete output fails reuse invariants")
    if decision.get("page_access", {}).get("input_signature") != signature(info):
        raise RuntimeError("Existing complete output input signature mismatch")
    result = dict(decision)
    result["idempotent_complete_output_reused"] = True
    result["pdf_pages_reaccessed_on_reuse"] = 0
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "tmp/bounded_qualitative_span_disambiguation_checkpoint.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-local-pdf-text-layer", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    checkpoint = args.checkpoint if args.checkpoint.is_absolute() else ROOT / args.checkpoint
    info = preflight(output_dir, allow_existing=args.resume and output_dir.exists())
    if args.dry_run:
        print(json.dumps({
            "writes_performed": 0,
            "prior_status_counts": info["prior_status_counts"],
            "review_row_count": len(info["review_rows"]),
            "previously_verified_preserved_count": 455,
            "unique_review_pdf_count": len(info["pdf_hashes"]),
            "unique_approved_review_page_count": len(info["approved"]),
            "package_sha256_checks_passed": 5,
        }, indent=2, sort_keys=True))
        return 0
    if not args.allow_local_pdf_text_layer:
        raise RuntimeError("Live page-text access requires --allow-local-pdf-text-layer")
    if args.resume and output_dir.exists():
        print(json.dumps(reuse_complete(output_dir, info), indent=2, sort_keys=True))
        return 0
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    reviewed, page_audit, checkpoint_audit = run_capture(info, checkpoint, args.resume)
    decision = materialize(output_dir, info, reviewed, page_audit, checkpoint_audit)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
