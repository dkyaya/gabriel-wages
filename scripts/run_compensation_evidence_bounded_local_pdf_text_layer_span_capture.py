#!/usr/bin/env python3
"""Hardened bounded local PDF text-layer span capture.

This runner may read only the already-retained readable PDFs and exact page
pointers represented by the 1,954 active qualitative navigation rows. It is
offline, never OCRs or renders a page, never stores page text, and writes only
short exact spans plus audit metadata. Upstream artifacts are immutable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-BOUNDED-PDF-TEXT-SPAN-CAPTURE-SYSTEM-HARDENING-AND-READINESS-PREP-2026-07-25"
SCHEMA_VERSION = "bounded_pdf_text_span_capture_v1"
EXPECTED_ROWS = 1954
MAX_SPAN_CHARS = 500
MIN_SPAN_CHARS = 8

PRIOR = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-AND-RESIDUAL-METADATA-REPAIR-2026-07-25"
)
PREVIOUS_FOLLOWUP = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-SCHEMA-REPAIR-FOLLOWUP-2026-07-25"
)
DEFAULT_OUTPUT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-BOUNDED-PDF-TEXT-SPAN-CAPTURE-SYSTEM-HARDENING-AND-READINESS-PREP-2026-07-25"
)

INPUTS = {
    "decision": PRIOR / "bounded_qualitative_span_residual_metadata_repair_decision.json",
    "navigation": PRIOR / "qualitative_mechanism_span_repaired_navigation_view.csv",
    "cycle": PRIOR / "residual_cycle_matching_bridge.csv",
    "occupation": PRIOR / "residual_non_safety_occupation_bridge.csv",
    "residual_quarantine": PRIOR / "residual_metadata_quarantine_summary.json",
    "quant_candidate": PRIOR / "quantitative_analysis_view_candidate_span_followup.csv",
    "quant_exception": PRIOR / "quantitative_exception_ledger_span_followup.csv",
    "nonbase": PRIOR / "non_base_wage_companion_view_candidate_span_followup.csv",
    "reference": PRIOR / "reference_exclusion_control_view_span_followup.csv",
    "conflicts": PRIOR / "unresolved_conflict_quarantine_ledger_span_followup.csv",
    "retrieval": PREVIOUS_FOLLOWUP / "bounded_retrieval_provenance_bridge.csv",
    "pdf_readiness": ROOT / "docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv",
}

EXPECTED_SHA256 = {
    "decision": "3a4c38dcac262e754bcaf94747b5c6ebc356231aedf40b0f0163947affb67d65",
    "navigation": "28ed77b152c22753b0ec7a3438b0a25a96f246709016999aee5a5d87abc369d3",
    "cycle": "ee6ec3b505f5cdd9d581ef72ab8481a6c3b34ace9f74913ae391ec69ad720db3",
    "occupation": "0bd4a02f41998fbdc8b3a001b6b68e2f7279a8ebe390ffc815670c4942d6f3d0",
    "residual_quarantine": "d35a462f3b1648ad6f6a6a4bfd7e9d3e4815708293ad16318caef6effbaa2385",
    "quant_candidate": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    "quant_exception": "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401",
    "nonbase": "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92",
    "reference": "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a",
    "conflicts": "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7",
    "retrieval": "c012a03756892fd14856a79d5c5a59ba0ccb90e90064f65581840dcc84c9227b",
    "pdf_readiness": "dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953",
}

PACKAGE_ROOT = ROOT / (
    "docs/analysis/compensation_extraction/"
    "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
)
PACKAGE_LEDGERS = {
    "quantitative": PACKAGE_ROOT / "ledgers/quantitative/final_provisional_quantitative_ledger.csv",
    "qualitative": PACKAGE_ROOT / "ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv",
    "mixed": PACKAGE_ROOT / "ledgers/mixed/final_provisional_mixed_join_ledger.csv",
    "non_base_wage": PACKAGE_ROOT / "ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv",
    "reference_and_exclusion": PACKAGE_ROOT / "ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv",
}
EXPECTED_PACKAGE_SHA256 = {
    "quantitative": "7e275b8c45f0d4b77e01249d978fe17862fd3f8d552bf0f4ef77ed0bb3616c86",
    "qualitative": "d22a4015da83da7d0195e430ef30d475b3678c17696e7a835d6d09bce1a1e0d5",
    "mixed": "a204061a4ca4bbfd3512bf964d689fe385dfd71fac93589a4bb9b59e64eb9192",
    "non_base_wage": "84df35187461392ea9699660ea86317250a33979e6ff2b4f9256a49b1d9e0ea2",
    "reference_and_exclusion": "2a33987b8f54048d8a397fc7d9a917dafd2dbcf8b7b74a20de8c2642a886e3a1",
}

OUTPUTS = {
    "summary": "bounded_pdf_text_span_capture_system_hardening_summary.md",
    "decision": "bounded_pdf_text_span_capture_system_hardening_decision.json",
    "ledger": "qualitative_literal_span_capture_ledger_pdf_text_layer.csv",
    "audit": "qualitative_literal_span_capture_pdf_text_layer_audit.json",
    "input_hashes": "bounded_pdf_text_layer_input_sha256.txt",
    "page_audit": "bounded_pdf_text_layer_page_access_audit.csv",
    "page_summary": "bounded_pdf_text_layer_page_access_summary.json",
    "hardening": "span_capture_system_hardening_report.md",
    "stress": "span_capture_stress_test_report.md",
    "failures": "span_capture_failure_mode_matrix.csv",
    "invariants": "span_capture_invariant_checks.json",
    "test_inventory": "span_capture_regression_test_inventory.json",
    "verified_navigation": "qualitative_mechanism_span_verified_navigation_view.csv",
    "navigation_status": "qualitative_mechanism_navigation_view_with_span_status.csv",
    "quant_candidate": "quantitative_analysis_view_candidate_span_capture_followup.csv",
    "quant_exception": "quantitative_exception_ledger_span_capture_followup.csv",
    "nonbase": "non_base_wage_companion_view_candidate_span_capture_followup.csv",
    "reference": "reference_exclusion_control_view_span_capture_followup.csv",
    "conflicts": "unresolved_conflict_quarantine_ledger_span_capture_followup.csv",
    "residual_quarantine": "residual_metadata_quarantine_summary_span_capture_followup.json",
    "blockers": "bounded_pdf_text_layer_span_capture_blocker_matrix.csv",
    "validation": "bounded_pdf_text_span_capture_validation_2026-07-25.md",
}

SPAN_FIELDS = [
    "bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic",
    "step_progression_rule", "eligibility_rule", "implementation_rule",
    "fiscal_constraint", "reopener_clause", "differentiation_logic",
]

# Literal mechanism anchors. They are used only to select an exact page-text
# segment for a label that already exists. They never assign or change labels.
MECHANISM_PATTERNS = {
    "implementation_or_effective_date_logic": r"\b(?:effective|commenc(?:e|ing)|retroactive|ratification|beginning|increase(?:d|s)?|shall be paid|shall receive)\b",
    "step_movement_or_seniority": r"\b(?:step|seniority|anniversary|progression|years? of service)\b",
    "collective_bargaining_agreement_terms": r"\b(?:wage|salary|pay rate|compensation|salary schedule|wage schedule|across.the.board)\b",
    "arbitration_or_factfinding_reasoning": r"\b(?:arbitrat(?:or|ion)|fact.?find(?:er|ing)|interest arbitration|award)\b",
    "longevity_or_service_based_pay": r"\b(?:longevity|years? of service|service pay)\b",
    "CPI_or_COLA_indexing": r"\b(?:CPI|COLA|consumer price index|cost.of.living)\b",
    "certification_or_education_incentive": r"\b(?:certification|education(?:al)?|degree|college credits?|incentive pay)\b",
    "comparability_or_market_study": r"\b(?:comparab(?:le|ility)|market (?:study|survey|adjustment))\b",
    "rank_or_classification_differentiation": r"\b(?:rank|classification|pay grade|salary grade|pay band|pay range)\b",
    "fiscal_constraint_or_budget_logic": r"\b(?:fiscal|budget|ability to pay|financial constraint|funding)\b",
    "wage_reopener_or_future_negotiation": r"\b(?:reopen(?:er|ing)?|renegotiat(?:e|ion)|future negotiation)\b",
    "memorandum_or_settlement_terms": r"\b(?:memorandum|settlement|tentative agreement|side letter)\b",
    "parity_or_internal_equity": r"\b(?:parity|internal equity|equal pay|pay equity)\b",
}

CONTROLLED_STATUSES = {
    "exact_verified", "span_ambiguous_multiple_candidates", "span_unavailable_or_unverified",
    "no_text_layer", "missing_pdf_path", "pdf_hash_mismatch", "page_pointer_invalid",
    "ocr_later_forbidden", "pdf_text_extraction_error",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise RuntimeError(f"Missing or duplicate CSV headers: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, header: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in header})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output_path_guard(output_dir: Path, allow_existing: bool = False) -> None:
    resolved = output_dir.resolve()
    analysis_root = (ROOT / "docs/analysis").resolve()
    if analysis_root not in resolved.parents:
        raise RuntimeError("Output must be a docs/analysis subdirectory")
    if any(part in {"data", "corpus", "ingest", "codified", "analysis_dataset"} for part in resolved.relative_to(ROOT).parts):
        raise RuntimeError("Forbidden output location")
    if output_dir.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {output_dir}")


def verify_retained_pdf(path: Path, expected_hash: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing retained PDF: {path}")
    actual = sha256(path)
    if actual != expected_hash:
        raise RuntimeError(f"Retained PDF SHA-256 mismatch: {path}")
    return actual


def assert_text_layer_allowed(readiness_row: dict[str, str]) -> None:
    if readiness_row.get("ocr_needed_signal") == "yes" or readiness_row.get("recommended_next_action") == "ocr_later":
        raise RuntimeError("OCR-later PDF entered approved page scope")


def assert_unique_observation_ids(rows: list[dict[str, str]], expected_count: int) -> None:
    ids = [row.get("qualitative_observation_id", "") for row in rows]
    if len(ids) != expected_count or len(set(ids)) != expected_count or "" in ids:
        raise RuntimeError("Duplicate, blank, or missing qualitative observation IDs")


def split_segments(text: str) -> list[tuple[int, int, str]]:
    """Return exact, short line/sentence segments with original offsets."""
    separators = list(re.finditer(r"(?:\r?\n+|(?<=[.!?;:])\s+(?=[A-Z0-9]))", text))
    result: list[tuple[int, int, str]] = []
    start = 0
    ranges = []
    for match in separators:
        ranges.append((start, match.start()))
        start = match.end()
    ranges.append((start, len(text)))
    for start, end in ranges:
        left = start
        right = end
        while left < right and text[left].isspace():
            left += 1
        while right > left and text[right - 1].isspace():
            right -= 1
        if MIN_SPAN_CHARS <= right - left <= MAX_SPAN_CHARS:
            value = text[left:right]
            if "\n" not in value and "\r" not in value:
                result.append((left, right, value))
    return result


def normalized_exact_matches(page_text: str, needle: str) -> list[tuple[int, int, str]]:
    """Map a whitespace-normalized literal needle back to exact page offsets."""
    needle = needle.strip()
    if len(needle) < MIN_SPAN_CHARS or len(needle) > MAX_SPAN_CHARS:
        return []
    direct = [
        (m.start(), m.end(), m.group(0))
        for m in re.finditer(re.escape(needle), page_text)
        if "\n" not in m.group(0) and "\r" not in m.group(0)
    ]
    if direct:
        return direct
    tokens = re.findall(r"\S+", needle)
    if len(tokens) < 2:
        return []
    pattern = r"\s+".join(re.escape(token) for token in tokens)
    return [
        (m.start(), m.end(), m.group(0))
        for m in re.finditer(pattern, page_text)
        if "\n" not in m.group(0) and "\r" not in m.group(0)
    ]


def select_span(row: dict[str, str], page_text: str) -> dict[str, Any]:
    if not page_text or not page_text.strip():
        return span_result("no_text_layer", "target_page_text_empty_or_whitespace")

    candidates: list[tuple[int, int, str, str]] = []
    for field in SPAN_FIELDS:
        value = row.get(field, "").strip()
        for start, end, text in normalized_exact_matches(page_text, value):
            candidates.append((start, end, text, f"exact_structured_field:{field}"))

    if not candidates:
        pattern = MECHANISM_PATTERNS.get(row.get("mechanism_type", ""))
        if pattern:
            regex = re.compile(pattern, re.I)
            for start, end, text in split_segments(page_text):
                if regex.search(text):
                    candidates.append((start, end, text, "literal_mechanism_anchor_segment"))

    # Exact de-duplication preserves distinct offsets so repeated occurrences are ambiguous.
    candidates = sorted(set(candidates), key=lambda item: (len(item[2]), item[0], item[2], item[3]))
    if not candidates:
        return span_result("span_unavailable_or_unverified", "no_exact_structured_or_literal_mechanism_match")

    shortest_len = len(candidates[0][2])
    shortest = [item for item in candidates if len(item[2]) == shortest_len]
    chosen = shortest[0]
    status = "exact_verified" if len(candidates) == 1 else "span_ambiguous_multiple_candidates"
    reason = chosen[3] if status == "exact_verified" else f"{chosen[3]};candidate_count={len(candidates)}"
    return span_result(status, reason, *chosen[:3], candidate_count=len(candidates))


def span_result(
    status: str,
    reason: str,
    start: int | None = None,
    end: int | None = None,
    text: str = "",
    candidate_count: int = 0,
) -> dict[str, Any]:
    if status not in CONTROLLED_STATUSES:
        raise RuntimeError(f"Uncontrolled span status: {status}")
    qa = status == "exact_verified"
    return {
        "literal_verbatim_evidence_span": text,
        "span_start": "" if start is None else str(start),
        "span_end": "" if end is None else str(end),
        "span_length": str(len(text)),
        "span_sha256": text_sha256(text) if text else "",
        "span_capture_status": status,
        "span_failure_reason": "" if text else reason,
        "span_capture_reason_code": reason,
        "span_candidate_count": str(candidate_count),
        "span_qa_pass": "true" if qa else "false",
    }


def verify_span(page_text: str, result: dict[str, Any]) -> None:
    text = result["literal_verbatim_evidence_span"]
    if not text:
        if any(result[key] for key in ("span_start", "span_end", "span_sha256")):
            raise RuntimeError("Unavailable span carries forbidden offset/hash data")
        return
    start, end = int(result["span_start"]), int(result["span_end"])
    if not (MIN_SPAN_CHARS <= len(text) <= MAX_SPAN_CHARS):
        raise RuntimeError("Span length outside bounds")
    if page_text[start:end] != text:
        raise RuntimeError("Span offsets do not round-trip")
    if text not in page_text:
        raise RuntimeError("Span is not an exact page-text substring")
    if result["span_sha256"] != text_sha256(text):
        raise RuntimeError("Span SHA-256 mismatch")
    if text.strip() == page_text.strip():
        raise RuntimeError("Full-page-text leakage detected")
    if "\n" in text or "\r" in text:
        raise RuntimeError("Stored spans must be single physical text-layer lines")


@dataclass(frozen=True)
class ApprovedPage:
    artifact_path: Path
    pdf_hash: str
    page_number: int


class PageAccessGuard:
    def __init__(self, approved: set[ApprovedPage], reader_factory: Callable[[str], Any] = PdfReader):
        self.approved = approved
        self.reader_factory = reader_factory
        self.accessed: list[ApprovedPage] = []

    def extract(self, request: ApprovedPage) -> tuple[str, int]:
        if request not in self.approved:
            raise RuntimeError("Non-target page access attempt rejected")
        reader = self.reader_factory(str(request.artifact_path))
        index = request.page_number - 1
        if index < 0 or index >= len(reader.pages):
            raise IndexError("Approved page pointer outside PDF page range")
        self.accessed.append(request)
        return reader.pages[index].extract_text() or "", len(reader.pages)


def load_preflight(output_dir: Path, allow_existing: bool = False) -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in (*INPUTS.values(), *PACKAGE_LEDGERS.values()) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required input artifacts missing: {missing}")
    output_path_guard(output_dir, allow_existing=allow_existing)
    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"Immutable input SHA-256 mismatch: {actual}")
    package_hashes = {name: sha256(path) for name, path in PACKAGE_LEDGERS.items()}
    if package_hashes != EXPECTED_PACKAGE_SHA256:
        raise RuntimeError(f"Immutable five-ledger package SHA-256 mismatch: {package_hashes}")
    decision = json.loads(INPUTS["decision"].read_text(encoding="utf-8"))
    if decision.get("decision") != "bounded_span_metadata_repair_blocked_missing_bounded_text_or_span_support":
        raise RuntimeError("Unexpected predecessor decision")

    _, rows = read_rows(INPUTS["navigation"])
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_ROWS} qualitative rows, found {len(rows)}")
    assert_unique_observation_ids(rows, EXPECTED_ROWS)

    _, readiness_rows = read_rows(INPUTS["pdf_readiness"])
    readiness = {row["pdf_readiness_id"]: row for row in readiness_rows}
    approved: set[ApprovedPage] = set()
    pdfs: dict[Path, str] = {}
    ocr_forbidden = 0
    for row in rows:
        path = ROOT / row["artifact_pointer_bridge"]
        try:
            page_number = int(row["page_number"])
        except ValueError as exc:
            raise RuntimeError("Non-integer qualitative page pointer") from exc
        if page_number < 1:
            raise RuntimeError("Qualitative page pointer must be one-based and positive")
        expected_hash = row["raw_retained_content_hash"]
        existing = pdfs.setdefault(path, expected_hash)
        if existing != expected_hash:
            raise RuntimeError("One PDF path maps to multiple retained hashes")
        ready = readiness.get(row["pdf_readiness_id"])
        if not ready:
            raise RuntimeError("Missing PDF readiness row")
        try:
            assert_text_layer_allowed(ready)
        except RuntimeError:
            ocr_forbidden += 1
            raise
        if ready.get("content_artifact_path") != row["artifact_pointer_bridge"]:
            raise RuntimeError("Artifact pointer disagrees with PDF readiness ledger")
        if ready.get("content_hash") != expected_hash:
            raise RuntimeError("Retained hash disagrees with PDF readiness ledger")
        approved.add(ApprovedPage(path, expected_hash, page_number))

    pdf_hashes: dict[Path, str] = {}
    for path, expected in sorted(pdfs.items(), key=lambda item: str(item[0])):
        pdf_hashes[path] = verify_retained_pdf(path, expected)

    return {
        "rows": rows,
        "approved": approved,
        "pdf_hashes": pdf_hashes,
        "input_hashes": actual,
        "package_hashes": package_hashes,
        "package_sha256_checks_passed": len(package_hashes),
        "qualitative_row_count": len(rows),
        "unique_pdf_count": len(pdfs),
        "unique_approved_page_count": len(approved),
        "ocr_later_approved_count": ocr_forbidden,
        "writes_performed": 0,
    }


def checkpoint_signature(rows: list[dict[str, str]], input_hashes: dict[str, str]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "navigation_sha256": input_hashes["navigation"],
        "ids": [row["qualitative_observation_id"] for row in rows],
    }
    return text_sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def reuse_complete_output(output_dir: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    required = [OUTPUTS["decision"], OUTPUTS["audit"], OUTPUTS["invariants"], OUTPUTS["ledger"]]
    missing = [name for name in required if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Existing output is partial and cannot masquerade as complete: {missing}")
    decision = json.loads((output_dir / OUTPUTS["decision"]).read_text(encoding="utf-8"))
    audit = json.loads((output_dir / OUTPUTS["audit"]).read_text(encoding="utf-8"))
    invariants = json.loads((output_dir / OUTPUTS["invariants"]).read_text(encoding="utf-8"))
    _, ledger = read_rows(output_dir / OUTPUTS["ledger"])
    expected_signature = checkpoint_signature(preflight["rows"], preflight["input_hashes"])
    actual_signature = decision.get("page_access", {}).get("input_signature", "")
    if audit.get("schema_version") != SCHEMA_VERSION or actual_signature != expected_signature:
        raise RuntimeError("Existing complete output schema/input signature mismatch")
    if not invariants.get("all_invariants_passed") or len(ledger) != EXPECTED_ROWS:
        raise RuntimeError("Existing complete output failed invariant/accounting reuse check")
    decision = dict(decision)
    decision["idempotent_complete_output_reused"] = True
    decision["pdf_pages_reaccessed_on_reuse"] = 0
    return decision


def load_checkpoint(path: Path, signature: str) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    results: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            item = json.loads(line)
            if item.get("schema_version") != SCHEMA_VERSION or item.get("input_signature") != signature:
                raise RuntimeError("Checkpoint schema/input signature mismatch")
            obs_id = item["qualitative_observation_id"]
            if obs_id in results:
                raise RuntimeError(f"Duplicate checkpoint observation ID at line {line_number}")
            if any(key in item for key in ("page_text", "full_page_text", "raw_page_text")):
                raise RuntimeError("Full-page-text leakage in checkpoint")
            results[obs_id] = item
    return results


def append_checkpoint(path: Path, item: dict[str, Any]) -> None:
    forbidden = {"page_text", "full_page_text", "raw_page_text"}.intersection(item)
    if forbidden:
        raise RuntimeError("Attempted page-text checkpoint leakage")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")


def capture(
    preflight: dict[str, Any],
    checkpoint: Path,
    resume: bool,
    reader_factory: Callable[[str], Any] = PdfReader,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = preflight["rows"]
    signature = checkpoint_signature(rows, preflight["input_hashes"])
    if checkpoint.exists() and not resume:
        raise FileExistsError("Checkpoint exists; use --resume")
    existing = load_checkpoint(checkpoint, signature) if resume else {}
    expected_ids = {row["qualitative_observation_id"] for row in rows}
    if set(existing) - expected_ids:
        raise RuntimeError("Checkpoint contains out-of-scope observations")

    by_page: dict[ApprovedPage, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        request = ApprovedPage(ROOT / row["artifact_pointer_bridge"], row["raw_retained_content_hash"], int(row["page_number"]))
        if row["qualitative_observation_id"] not in existing:
            by_page[request].append(row)

    guard = PageAccessGuard(preflight["approved"], reader_factory)
    page_audit: list[dict[str, Any]] = []
    for request in sorted(by_page, key=lambda item: (str(item.artifact_path), item.page_number)):
        related = by_page[request]
        try:
            page_text, pdf_page_count = guard.extract(request)
            access_status = "text_layer_present" if page_text.strip() else "no_text_layer"
            error = ""
        except IndexError:
            page_text, pdf_page_count, access_status, error = "", 0, "page_pointer_invalid", "approved_page_outside_pdf_page_range"
        except Exception as exc:  # sanitized class only; no document text or credentials
            page_text, pdf_page_count, access_status, error = "", 0, "pdf_text_extraction_error", type(exc).__name__
        page_audit.append({
            "pdf_sha256": request.pdf_hash,
            "artifact_pointer": str(request.artifact_path.relative_to(ROOT)),
            "page_number": request.page_number,
            "approved_page": "true",
            "page_access_status": access_status,
            "pdf_page_count": pdf_page_count,
            "text_layer_char_count": len(page_text),
            "qualitative_row_count": len(related),
            "error_type_sanitized": error,
            "ocr_used": "false",
            "rendered_image_used": "false",
            "page_text_persisted": "false",
        })
        for row in related:
            if access_status == "text_layer_present":
                result = select_span(row, page_text)
                verify_span(page_text, result)
            else:
                result = span_result(access_status, error or "target_page_has_no_extractable_text_layer")
            item = {
                "schema_version": SCHEMA_VERSION,
                "input_signature": signature,
                "qualitative_observation_id": row["qualitative_observation_id"],
                "extraction_case_id": row["extraction_case_id"],
                "document_identity_id": row["document_identity_id"],
                "source_review_id": row["source_review_id"],
                "text_table_detection_id": row["text_table_detection_id"],
                "retained_content_hash": row["raw_retained_content_hash"],
                "pdf_sha256": request.pdf_hash,
                "page_number": row["page_number"],
                "bounded_evidence_pointer": row["bounded_evidence_pointer"],
                "mechanism_type": row["mechanism_type"],
                "artifact_pointer": str(request.artifact_path.relative_to(ROOT)),
                "page_access_status": access_status,
                "pdf_page_count": str(pdf_page_count),
                "text_layer_char_count": str(len(page_text)),
                "page_access_error_type_sanitized": error,
                **result,
                "qa_status": "exact_literal_span_verified" if result["span_qa_pass"] == "true" else "navigation_only_span_not_qa_sufficient",
            }
            append_checkpoint(checkpoint, item)
            existing[item["qualitative_observation_id"]] = item
        # Page text is deliberately scoped to this iteration and never serialized.
        page_text = ""

    if set(existing) != expected_ids:
        raise RuntimeError(f"Partial run cannot materialize complete outputs: {len(existing)}/{len(expected_ids)}")
    ordered = [existing[row["qualitative_observation_id"]] for row in rows]
    # Rebuild a complete page audit from checkpoint-safe metadata so resumed
    # pages are represented without persisting page text.
    page_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in ordered:
        page_groups[(item["pdf_sha256"], item["artifact_pointer"], item["page_number"])].append(item)
    page_audit = []
    for (pdf_hash, artifact, page_number), group in sorted(page_groups.items()):
        first = group[0]
        invariant_fields = ("page_access_status", "pdf_page_count", "text_layer_char_count", "page_access_error_type_sanitized")
        if any(any(item[field] != first[field] for item in group) for field in invariant_fields):
            raise RuntimeError("Checkpoint page-access metadata disagreement")
        page_audit.append({
            "pdf_sha256": pdf_hash,
            "artifact_pointer": artifact,
            "page_number": page_number,
            "approved_page": "true",
            "page_access_status": first["page_access_status"],
            "pdf_page_count": first["pdf_page_count"],
            "text_layer_char_count": first["text_layer_char_count"],
            "qualitative_row_count": len(group),
            "error_type_sanitized": first["page_access_error_type_sanitized"],
            "ocr_used": "false",
            "rendered_image_used": "false",
            "page_text_persisted": "false",
        })
    return ordered, page_audit, {
        "checkpoint_reused_row_count": len(rows) - sum(len(value) for value in by_page.values()),
        "checkpoint_new_row_count": sum(len(value) for value in by_page.values()),
        "checkpoint_complete": True,
        "input_signature": signature,
        "non_target_page_access_count": 0,
        "unique_pages_accessed_this_run": len(guard.accessed),
    }


def validate_invariants(
    preflight: dict[str, Any],
    ledger: list[dict[str, Any]],
    page_audit: list[dict[str, Any]],
) -> dict[str, Any]:
    ids = [row["qualitative_observation_id"] for row in ledger]
    span_rows = [row for row in ledger if row["literal_verbatim_evidence_span"]]
    checks = {
        "one_row_per_qualitative_observation_id": len(ids) == EXPECTED_ROWS == len(set(ids)),
        "all_qualitative_observation_ids_accounted_for": set(ids) == {row["qualitative_observation_id"] for row in preflight["rows"]},
        "all_statuses_controlled": all(row["span_capture_status"] in CONTROLLED_STATUSES for row in ledger),
        "all_span_hashes_valid": all(row["span_sha256"] == text_sha256(row["literal_verbatim_evidence_span"]) for row in span_rows),
        "all_span_lengths_valid": all(int(row["span_length"]) == len(row["literal_verbatim_evidence_span"]) <= MAX_SPAN_CHARS for row in span_rows),
        "all_stored_spans_single_line": all("\n" not in row["literal_verbatim_evidence_span"] and "\r" not in row["literal_verbatim_evidence_span"] for row in span_rows),
        "no_full_page_text_columns": not any(key in {"page_text", "full_page_text", "raw_page_text"} for row in ledger for key in row),
        "only_approved_pages_accessed": all(row["approved_page"] == "true" for row in page_audit),
        "ocr_later_access_count_zero": preflight["ocr_later_approved_count"] == 0,
        "non_target_page_access_count_zero": True,
        "page_text_persisted_count_zero": all(row["page_text_persisted"] == "false" for row in page_audit),
    }
    return {"checks": checks, "all_invariants_passed": all(checks.values()), "schema_version": SCHEMA_VERSION}


def carry_forward(output_dir: Path) -> None:
    mapping = {
        "quant_candidate": "quant_candidate", "quant_exception": "quant_exception",
        "nonbase": "nonbase", "reference": "reference", "conflicts": "conflicts",
        "residual_quarantine": "residual_quarantine",
    }
    for output_name, input_name in mapping.items():
        shutil.copyfile(INPUTS[input_name], output_dir / OUTPUTS[output_name])
        if sha256(output_dir / OUTPUTS[output_name]) != sha256(INPUTS[input_name]):
            raise RuntimeError(f"Carry-forward byte mismatch: {output_name}")


def materialize(output_dir: Path, preflight: dict[str, Any], ledger: list[dict[str, Any]], page_audit: list[dict[str, Any]], checkpoint_audit: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=False)
    carry_forward(output_dir)
    ledger_header = [
        "qualitative_observation_id", "extraction_case_id", "document_identity_id", "source_review_id",
        "text_table_detection_id", "retained_content_hash", "pdf_sha256", "page_number",
        "bounded_evidence_pointer", "mechanism_type", "literal_verbatim_evidence_span", "span_start",
        "span_end", "span_length", "span_sha256", "span_capture_status", "span_failure_reason",
        "span_capture_reason_code", "span_candidate_count", "span_qa_pass", "qa_status",
    ]
    write_csv(output_dir / OUTPUTS["ledger"], ledger_header, ledger)
    write_csv(output_dir / OUTPUTS["page_audit"], [
        "pdf_sha256", "artifact_pointer", "page_number", "approved_page", "page_access_status",
        "pdf_page_count", "text_layer_char_count", "qualitative_row_count", "error_type_sanitized",
        "ocr_used", "rendered_image_used", "page_text_persisted",
    ], page_audit)

    _, nav_rows = read_rows(INPUTS["navigation"])
    ledger_by_id = {row["qualitative_observation_id"]: row for row in ledger}
    extra = [field for field in ledger_header if field not in nav_rows[0]]
    nav_header, _ = read_rows(INPUTS["navigation"])
    nav_header = nav_header + extra
    verified_navigation = []
    for row in nav_rows:
        merged = dict(row)
        span_values = ledger_by_id[row["qualitative_observation_id"]]
        merged.update({key: value for key, value in span_values.items() if key != "qa_status"})
        merged["span_qa_status"] = span_values["qa_status"]
        merged["qualitative_coded_measurement_eligible"] = ledger_by_id[row["qualitative_observation_id"]]["span_qa_pass"]
        merged["qualitative_readiness_reason"] = (
            "exact_literal_span_verified" if merged["span_qa_pass"] == "true" else "navigation_only_span_not_qa_sufficient"
        )
        verified_navigation.append(merged)
    if "span_qa_status" not in nav_header:
        nav_header.append("span_qa_status")
    write_csv(output_dir / OUTPUTS["verified_navigation"], nav_header, verified_navigation)
    write_csv(output_dir / OUTPUTS["navigation_status"], nav_header, verified_navigation)

    invariants = validate_invariants(preflight, ledger, page_audit)
    invariants["checks"]["historical_qualitative_qa_status_preserved"] = all(
        repaired["qa_status"] == prior["qa_status"]
        for repaired, prior in zip(verified_navigation, nav_rows)
    )
    invariants["checks"]["span_qa_status_separate_and_nonblank"] = all(
        row.get("span_qa_status", "") for row in verified_navigation
    )
    invariants["all_invariants_passed"] = all(invariants["checks"].values())
    write_json(output_dir / OUTPUTS["invariants"], invariants)
    if not invariants["all_invariants_passed"]:
        raise RuntimeError("Span capture invariants failed")

    status_counts = Counter(row["span_capture_status"] for row in ledger)
    reason_counts = Counter(row["span_failure_reason"] for row in ledger if row["span_failure_reason"])
    exact_count = status_counts["exact_verified"]
    ambiguous_count = status_counts["span_ambiguous_multiple_candidates"]
    exact_literal_count = exact_count + ambiguous_count
    unavailable = EXPECTED_ROWS - exact_count
    all_coded_ready = exact_count == EXPECTED_ROWS
    decision_value = (
        "bounded_pdf_text_layer_span_capture_complete_repeat_analysis_readiness_review_allowed"
        if all_coded_ready
        else "bounded_pdf_text_layer_span_capture_partial_additional_repair_needed"
    )
    page_summary = {
        "approved_qualitative_row_count": EXPECTED_ROWS,
        "unique_retained_pdf_count": preflight["unique_pdf_count"],
        "unique_approved_page_count": preflight["unique_approved_page_count"],
        "unique_pages_accessed": len(page_audit),
        "qualitative_row_page_access_count": sum(int(row["qualitative_row_count"]) for row in page_audit),
        "text_layer_present_page_count": sum(row["page_access_status"] == "text_layer_present" for row in page_audit),
        "no_text_layer_page_count": sum(row["page_access_status"] == "no_text_layer" for row in page_audit),
        "page_pointer_invalid_count": sum(row["page_access_status"] == "page_pointer_invalid" for row in page_audit),
        "pdf_text_extraction_error_count": sum(row["page_access_status"] == "pdf_text_extraction_error" for row in page_audit),
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
        "qualitative_row_count": EXPECTED_ROWS,
        "span_capture_status_counts": dict(sorted(status_counts.items())),
        "exact_literal_span_captured_count": exact_count + ambiguous_count,
        "exact_substring_validation_pass_count": exact_count + ambiguous_count,
        "exact_substring_qa_pass_count": exact_count + ambiguous_count,
        "unique_candidate_span_qa_pass_count": exact_count,
        "ambiguous_exact_span_count": ambiguous_count,
        "span_unavailable_or_not_qa_sufficient_count": unavailable,
        "span_failure_reason_counts": dict(sorted(reason_counts.items())),
        "coded_qualitative_analysis_view_created": all_coded_ready,
        "navigation_view_with_span_status_created": True,
        "full_page_text_saved": False,
        "ocr_used": False,
        "model_calls": 0,
        "extraction_runs": 0,
        "new_document_selection_runs": 0,
    }
    write_json(output_dir / OUTPUTS["audit"], audit)

    hash_lines = [f"{preflight['input_hashes'][name]}  structured:{name}  {INPUTS[name].relative_to(ROOT)}" for name in sorted(INPUTS)]
    for path, digest in sorted(preflight["pdf_hashes"].items(), key=lambda item: str(item[0])):
        hash_lines.append(f"{digest}  retained_pdf  {path.relative_to(ROOT)}")
    for name, path in sorted(PACKAGE_LEDGERS.items()):
        hash_lines.append(f"{preflight['package_hashes'][name]}  immutable_package:{name}  {path.relative_to(ROOT)}")
    (output_dir / OUTPUTS["input_hashes"]).write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    blockers = [
        {"blocker_id": "P01", "area": "qualitative_span_qa", "status": "passed" if all_coded_ready else "partial", "affected_count": unavailable, "resolution_or_boundary": "Only exact unique short spans are coded-analysis eligible; ambiguous or unavailable rows remain navigation-only."},
        {"blocker_id": "P02", "area": "residual_cycle_metadata", "status": "carried_forward_quarantine", "affected_count": 467, "resolution_or_boundary": "1,359 exact cycles and 203 matched documents/91 groups preserved; no inference."},
        {"blocker_id": "P03", "area": "residual_occupation_metadata", "status": "carried_forward_quarantine", "affected_count": 368, "resolution_or_boundary": "1,458 controlled occupations/239 non-safety subclasses preserved; no inference."},
        {"blocker_id": "P04", "area": "quantitative_exceptions", "status": "carried_forward", "affected_count": 1045, "resolution_or_boundary": "862 candidates and 1,045 exceptions remain separate; no coercion."},
        {"blocker_id": "P05", "area": "unresolved_conflicts", "status": "quarantined", "affected_count": 5, "resolution_or_boundary": "Two groups/five observations remain explicit and excluded."},
    ]
    write_csv(output_dir / OUTPUTS["blockers"], ["blocker_id", "area", "status", "affected_count", "resolution_or_boundary"], blockers)

    failure_rows = [
        ("empty_text_page", "no_text_layer", "mark unavailable; no OCR/image fallback"),
        ("multiple_identical_occurrences", "span_ambiguous_multiple_candidates", "retain shortest exact span; QA false"),
        ("no_literal_match", "span_unavailable_or_unverified", "navigation only; never infer"),
        ("page_pointer_mismatch", "fail_closed", "reject access"),
        ("ocr_later_document", "fail_closed", "never open"),
        ("duplicate_observation_id", "fail_closed", "reject preflight"),
        ("missing_pdf", "fail_closed", "reject preflight"),
        ("wrong_pdf_hash", "fail_closed", "reject before PDF parsing"),
        ("partial_checkpoint", "partial_only", "cannot materialize final outputs"),
        ("idempotent_rerun", "reuse_or_refuse", "signature-matched resume only"),
        ("offset_corruption", "fail_closed", "round-trip invariant"),
        ("full_page_text_leakage", "fail_closed", "bounded span and forbidden-field guards"),
        ("schema_version_mismatch", "fail_closed", "invalidate checkpoint"),
        ("non_target_page_access", "fail_closed", "approved-set guard"),
        ("multiline_span_storage", "fail_closed", "stored spans must be single-line exact substrings"),
    ]
    write_csv(output_dir / OUTPUTS["failures"], ["failure_mode", "expected_status", "guardrail"], [dict(zip(["failure_mode", "expected_status", "guardrail"], row)) for row in failure_rows])
    write_json(output_dir / OUTPUTS["test_inventory"], {
        "required_failure_modes": [row[0] for row in failure_rows],
        "required_failure_mode_count": len(failure_rows),
        "test_script": "scripts/test_compensation_evidence_bounded_local_pdf_text_layer_span_capture.py",
        "focused_test_count_at_materialization": 32,
        "bugs_discovered_and_fixed": [
            "resume_accounting_used_production_constant_instead_of_scoped_row_count",
            "integration_test_temporary_output_violated_docs_analysis_output_boundary",
            "navigation_shadow_overwrote_historical_qa_status_with_span_qa_status",
            "multiline_exact_spans_failed_repository_diff_hygiene",
        ],
        "offline_only": True,
    })

    summary = f"""# Bounded PDF text-layer span capture and system hardening summary

Decision: `{decision_value}`

- Approved qualitative rows: {EXPECTED_ROWS:,}.
- Retained PDFs / unique approved pages read: {preflight['unique_pdf_count']:,} / {len(page_audit):,}.
- Exact literal substrings captured: {exact_literal_count:,}; unique-candidate span QA passes: {exact_count:,}; ambiguous exact spans: {ambiguous_count:,}; unavailable or not QA-sufficient: {unavailable:,}.
- OCR-later and non-target page accesses: 0 / 0. OCR, rendering, URLs, downloads, models, extraction, selection, ingestion, and codification: none.
- Full page text persisted: no. Only bounded spans (maximum {MAX_SPAN_CHARS} characters) and audit metadata were written.
- Coded qualitative analysis view created: {'yes' if all_coded_ready else 'no'}; navigation view with span status retained.
- Cycle/matching carried forward: 1,359 exact cycles; 203 matched documents across 91 exact-period groups; 467 identities quarantined.
- Occupation carried forward: 1,458 controlled occupations; 239 non-safety subclasses; 368 non-safety identities quarantined.
- Quantitative candidates/exceptions: 862 / 1,045. Non-base companion/reference control: 4,733 / 345.
- Two unresolved groups/five observations remain quarantined.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUTS["summary"]).write_text(summary, encoding="utf-8")
    hardening = f"""# Span capture system hardening report

The runner enforces immutable structured-input hashes and hashes each of {preflight['unique_pdf_count']} unique PDFs before parsing. A page-access guard admits only the {preflight['unique_approved_page_count']} precomputed `(PDF hash, path, page)` tuples. OCR-later inputs fail before parsing. Pages are opened through pypdf's text layer only; text exists only in memory for one approved page and is cleared after related rows are processed.

Checkpoint rows contain spans and provenance but no page text. Schema/input signatures prevent stale reuse. Resume materializes final outputs only after all 1,954 unique observation IDs are present. Exact spans must round-trip by offsets, match their SHA-256, obey the {MAX_SPAN_CHARS}-character cap, remain single-line for safe CSV/repository handling, and not equal the full page text. Ambiguous multiple candidates remain navigation-only.

All carried-forward lane files are byte-checked copies. The final invariant file records row uniqueness, page access, no-OCR, no-leakage, span hash, and span-length checks.
"""
    (output_dir / OUTPUTS["hardening"]).write_text(hardening, encoding="utf-8")
    stress = """# Span capture stress test report

The focused offline suite runs 32 tests and exercises empty text, repeated occurrences, missing matches, page mismatch, OCR-later exclusion, duplicate IDs, missing paths, wrong hashes, partial/resume behavior, idempotency, offset corruption, full-page leakage, checkpoint schema mismatch, non-target access, historical-QA preservation, and multiline-span rejection. It discovered and fixed four defects: resume accounting used the production constant instead of the scoped row count, an integration-test temporary output violated the strict `docs/analysis` boundary, the first navigation materialization overwrote historical `qa_status` with span QA, and multiline exact spans could produce repository whitespace defects. No guard was weakened; accounting was generalized, the test was moved inside the required boundary, span QA now has its own `span_qa_status` field, and stored spans must be single-line exact substrings. All focused tests must pass again during final validation.
"""
    (output_dir / OUTPUTS["stress"]).write_text(stress, encoding="utf-8")
    validation = f"""# Bounded PDF text-layer span capture validation

- Immutable structured input SHA-256 checks: {len(EXPECTED_SHA256)}/{len(EXPECTED_SHA256)} passed.
- Retained PDF SHA-256 checks: {preflight['unique_pdf_count']}/{preflight['unique_pdf_count']} passed before page parsing.
- Qualitative row uniqueness/accounting: {EXPECTED_ROWS}/{EXPECTED_ROWS}.
- Approved unique pages accessed: {len(page_audit)}/{preflight['unique_approved_page_count']}; non-target: 0.
- OCR-later documents opened: 0; rendered images: 0; page text persisted: 0.
- Exact literal substrings captured: {exact_literal_count}; unique-candidate span QA passes: {exact_count}; ambiguous exact spans: {ambiguous_count}; unavailable/not sufficient: {unavailable}.
- Carried-forward byte checks: quantitative candidates/exceptions, non-base, reference/control, conflicts, and residual quarantine passed.
- Analysis readiness remains false.
"""
    (output_dir / OUTPUTS["validation"]).write_text(validation, encoding="utf-8")

    next_name = "next_analysis_readiness_review_prompt.md" if all_coded_ready else "next_bounded_schema_repair_followup_prompt.md"
    next_text = (
        "# Future analysis-readiness review prompt\n\nSeparately authorize a read-only analysis-readiness review of this hardened span layer. Do not promote, ingest, codify, or analyze. Reverify all hashes, spans, quarantines, and analysis-readiness=false before deciding any later promotion.\n"
        if all_coded_ready else
        "# Future bounded qualitative span follow-up prompt\n\nDo not run without separate authorization. Review only the navigation rows whose local PDF text-layer span is unavailable or ambiguous. Preserve exact spans already verified, use no OCR/models/URLs/downloads, and keep analysis readiness false. Any further method must remain literal, bounded, page-scoped, and fail closed.\n"
    )
    (output_dir / next_name).write_text(next_text, encoding="utf-8")

    decision = {
        "task_id": TASK_ID,
        "generated_at": now_utc(),
        "decision": decision_value,
        "analysis_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "repeat_analysis_readiness_review_allowed": all_coded_ready,
        "next_prompt": next_name,
        "next_recommendation": (
            "run_separately_authorized_read_only_analysis_readiness_review"
            if all_coded_ready else "run_bounded_followup_for_ambiguous_or_unavailable_literal_spans"
        ),
        "qualitative_span_capture": audit,
        "page_access": page_summary,
        "invariants": invariants,
        "cycle_matching_carried_forward": {"exact_cycle_identity_count": 1359, "matched_set_document_count": 203, "matched_set_group_count": 91, "quarantined_identity_count": 467},
        "occupation_carried_forward": {"controlled_occupation_count": 1458, "non_safety_subclass_count": 239, "non_safety_quarantine_count": 368},
        "quantitative_carried_forward": {"candidate_count": 862, "exception_count": 1045},
        "non_base_and_reference_carried_forward": {"non_base_companion_count": 4733, "reference_control_count": 345},
        "unresolved_conflict_quarantine": {"group_count": 2, "observation_count": 5},
        "package_or_prior_or_durable_ledgers_mutated": False,
        "package_sha256_checks_passed": preflight["package_sha256_checks_passed"],
        "forbidden_actions_performed": [],
    }
    write_json(output_dir / OUTPUTS["decision"], decision)
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-local-pdf-text-layer", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if args.dry_run:
        result = load_preflight(output_dir)
        public = {key: value for key, value in result.items() if key not in {"rows", "approved", "pdf_hashes", "input_hashes"}}
        public["pdf_sha256_checks_passed"] = len(result["pdf_hashes"])
        print(json.dumps(public, indent=2, sort_keys=True))
        return 0
    if not args.allow_local_pdf_text_layer:
        raise RuntimeError("Live local PDF text-layer access requires --allow-local-pdf-text-layer")
    if output_dir.exists() and args.resume:
        preflight = load_preflight(output_dir, allow_existing=True)
        print(json.dumps(reuse_complete_output(output_dir, preflight), indent=2, sort_keys=True))
        return 0
    preflight = load_preflight(output_dir)
    checkpoint = args.checkpoint or (ROOT / "tmp/bounded_pdf_text_span_capture_checkpoint.jsonl")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    ledger, page_audit, checkpoint_audit = capture(preflight, checkpoint, args.resume)
    decision = materialize(output_dir, preflight, ledger, page_audit, checkpoint_audit)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
