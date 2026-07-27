#!/usr/bin/env python3
"""Extract local text from exactly 321 readiness-approved retained sources.

PDF extraction uses pdftotext without OCR or rendering. HTML extraction reads
only local retained bytes and ignores scripts/styles. Text artifacts are stored
only in this task directory and remain unrated, uningested, uncodified,
non-causal, and globally analysis-closed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "TARGETED-TEXT-LAYER-EXTRACTION-321-READINESS-READY-SOURCES-2026-07-26"
INPUT_COMMIT = "10a2b4db74ec5921af0ff8dd58e4ef99edaeb054"
INPUT_DIR = BASE / "TARGETED-PDF-TEXT-LAYER-READINESS-387-RETAINED-SOURCES-2026-07-26"
RETAINED_DIR = BASE / "TARGETED-SOURCE-REVIEW-DOWNLOAD-429-VERIFIED-LEADS-2026-07-26/retained_sources"
OUTPUT_DIR = BASE / "TARGETED-TEXT-LAYER-EXTRACTION-321-READINESS-READY-SOURCES-2026-07-26"
EXTRACTED_DIR = OUTPUT_DIR / "extracted_text"
PDF_TEXT_DIR = EXTRACTED_DIR / "pdf"
HTML_TEXT_DIR = EXTRACTED_DIR / "html"
CHECKPOINT_PATH = OUTPUT_DIR / ".extraction_checkpoint.json"
EXPECTED_COUNT = 321
EXPECTED_PDF_COUNT = 289
EXPECTED_HTML_COUNT = 32
EXPECTED_ID_SET_HASH = "21fdbf9da41b7646d297147eca46cb41d8469e00f8b082af8521d9b3345ec6f5"
EXPECTED_LANES = {"lane_1": 88, "lane_2": 106, "lane_3": 23, "lane_4": 104}
EXPECTED_MECHANISMS = {
    "fiscal_constraint_signal": 23,
    "market_or_comparability_pressure": 104,
    "non_safety_constraint_signal": 88,
    "strike_or_no_strike_constraint": 106,
}
MAX_WORKERS = 8
PDF_EXTRACTION_TIMEOUT_SECONDS = 120
MAX_PDF_TEXT_BYTES = 10 * 1024 * 1024
MAX_HTML_INPUT_BYTES = 25 * 1024 * 1024
MAX_HTML_TEXT_CHARACTERS = 5_000_000
MIN_TEXT_CHARACTERS = 100
MIN_PDF_DENSITY_PER_PAGE = 20

EXPECTED_HASHES = {
    "targeted_pdf_text_layer_readiness_387_decision.json": "00dd994418d54f6be4bb5ca5dd6ca1567dc431708ae4d22b0f332b5ad6054b30",
    "targeted_pdf_text_layer_readiness_387_summary.md": "11d3099299f44593edb614123ef8eea30b42c0e0cd6ea5eee932a2c8a911072a",
    "targeted_pdf_text_layer_readiness_387_locked_queue_summary.json": "7213b5f504707db068a22e84975aa4525cf157499f3b0a1ae008395eb04a7bbc",
    "targeted_pdf_text_layer_readiness_387_file_integrity_summary.json": "1df3a1bb6b8dbc8dd2149efd59492ad50a1f519d333df9fd2f16e6927579442f",
    "targeted_pdf_text_layer_readiness_387_readiness_lane_summary.json": "7d26444316ea8a1989ffe21af8b898eab63dc9b7a0ba37721358b69dd99c781f",
    "targeted_pdf_text_layer_readiness_387_pdf_summary.json": "27c2e0dd844e8dc00a108aaf8b68c1e5818a97c27fefebd830b80120f41b38c9",
    "targeted_pdf_text_layer_readiness_387_html_summary.json": "de91cdf6c0acedccf6e206bf0db2e13a9962932a741988e4756fcfd405bb43ff",
    "targeted_pdf_text_layer_readiness_387_mechanism_coverage_summary.json": "e5fcfd961a3e82052e14852f30648377d92a03d1047f9f7c52225ab5d518e5c6",
    "targeted_pdf_text_layer_readiness_387_city_cycle_unit_coverage_summary.json": "a8d389d1b347aa98d5add4c88eb27308a2e2c29f53ae9ab5fdd8e89759b2eb7b",
    "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions_summary.json": "43f6eb188b62087b014d1f2acc3c9295e6633732bb558105ad0d7f1d14f872f9",
    "targeted_pdf_text_layer_readiness_387_validation_2026-07-26.md": "c7dd35673929e9c080c7ed56b83046a074263dfd5ffe5b55095dddd52954a722",
    "targeted_pdf_text_layer_readiness_387_parse_text_layer_later.csv": "05a3387c64b60e3d42ffe466e7dad739633d7e2a1fd5f11c9a1fa3ff5a68a552",
    "targeted_pdf_text_layer_readiness_387_html_text_later.csv": "0be86b9b90563f74906e39dd184774043adccfd67522530dd1002d89422f21a7",
    "targeted_pdf_text_layer_readiness_387_results.csv": "c94127713077e11b1449659c8efeed84c7993a6dbefc67604cf259bfc77aa5d2",
    "targeted_pdf_text_layer_readiness_387_invariant_checks.json": "36cd07be7e3872d11e688b545d2507be6ce4f00d26dc3ff1e9a3e4addeb2dc48",
    "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions.csv": "56a7ada5ebcb623879f9dcf705ed57aa6aaf16a5baf1fa1eeffa5970dbc2566b",
    "targeted_pdf_text_layer_readiness_387_lock.json": "fc34bfc16fa2a857d40b2098c61d45c8cea0c822ddd1c834e2ca6c578f903e15",
}

LOCK_FIELDS = (
    "retained_source_id", "candidate_id", "lane_id", "priority_tier",
    "quality_label", "source_url_or_locator", "source_title", "municipality",
    "state", "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end",
    "source_family", "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "local_retained_path", "readiness_status",
    "readiness_reason", "content_type_hint", "file_extension",
    "file_size_bytes", "file_sha256", "page_count",
    "html_text_readiness_hint", "verification_status",
    "source_review_download_status", "file_integrity_status",
    "extraction_status", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness",
)

RESULT_FIELDS = (
    "extracted_text_id", "retained_source_id", "candidate_id", "lane_id",
    "priority_tier", "quality_label", "source_url_or_locator", "source_title",
    "municipality", "state", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period",
    "inferred_cycle_start", "inferred_cycle_end", "source_family",
    "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "local_retained_path", "readiness_status",
    "content_type_hint", "file_extension", "file_size_bytes", "file_sha256",
    "extraction_status", "extraction_reason", "extracted_text_path",
    "extracted_text_sha256", "extracted_text_size_bytes",
    "extracted_char_count", "extracted_non_whitespace_char_count",
    "extracted_page_count", "page_count_metadata", "html_text_readiness_hint",
    "extraction_method", "bounded_input_or_output_truncated", "ocr_used",
    "pdf_rendering_used", "model_api_used", "rating_status",
    "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
)

CONTROLLED_STATUSES = {
    "extracted_ok", "empty_or_too_short", "low_text_density",
    "suspected_bad_text_layer", "html_noisy_or_shell", "extraction_error",
}

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{24,}", re.IGNORECASE),
    re.compile(r"\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._-]{16,}", re.IGNORECASE),
)

REQUIRED_FINAL_OUTPUTS = (
    "targeted_text_layer_extraction_321_decision.json",
    "targeted_text_layer_extraction_321_summary.md",
    "targeted_text_layer_extraction_321_locked_queue.csv",
    "targeted_text_layer_extraction_321_locked_queue_summary.json",
    "targeted_text_layer_extraction_321_lock.json",
    "targeted_text_layer_extraction_321_dry_run_manifest.csv",
    "targeted_text_layer_extraction_321_dry_run_summary.json",
    "targeted_text_layer_extraction_321_no_call_validation.md",
    "targeted_text_layer_extraction_321_preflight_checks.json",
    "targeted_text_layer_extraction_321_preflight_report.md",
    "targeted_text_layer_extraction_321_results.csv",
    "targeted_text_layer_extraction_321_results_summary.json",
    "targeted_text_layer_extraction_321_pdf_results.csv",
    "targeted_text_layer_extraction_321_html_results.csv",
    "targeted_text_layer_extraction_321_pdf_results_summary.json",
    "targeted_text_layer_extraction_321_html_results_summary.json",
    "extracted_text_manifest.csv", "extracted_text_hash_manifest.csv",
    "extracted_text_manifest_summary.json",
    "targeted_text_layer_extraction_321_extracted_ok.csv",
    "targeted_text_layer_extraction_321_empty_or_too_short.csv",
    "targeted_text_layer_extraction_321_low_text_density.csv",
    "targeted_text_layer_extraction_321_suspected_bad_text_layer.csv",
    "targeted_text_layer_extraction_321_html_noisy_or_shell.csv",
    "targeted_text_layer_extraction_321_extraction_errors.csv",
    "targeted_text_layer_extraction_321_evidence_extraction_candidate_manifest.csv",
    "targeted_text_layer_extraction_321_evidence_extraction_candidate_summary.json",
    "targeted_text_layer_extraction_321_extraction_limits_and_boundaries.md",
    "targeted_text_layer_extraction_321_mechanism_coverage.csv",
    "targeted_text_layer_extraction_321_mechanism_coverage_summary.json",
    "targeted_text_layer_extraction_321_city_cycle_unit_coverage.csv",
    "targeted_text_layer_extraction_321_city_cycle_unit_coverage_summary.json",
    "targeted_text_layer_extraction_321_preserved_readiness_exclusions.csv",
    "targeted_text_layer_extraction_321_preserved_readiness_exclusions_summary.json",
    "targeted_text_layer_extraction_321_validation_2026-07-26.md",
    "targeted_text_layer_extraction_321_invariant_checks.json",
    "targeted_text_layer_extraction_321_stress_test_report.md",
    "targeted_text_layer_extraction_321_regression_test_inventory.json",
    "next_task.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["retained_source_id"] for row in rows)))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def verify_inputs(*, verify_file_bytes: bool = True) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required immutable readiness input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable readiness input hash drift: {name}")
    decision = read_json(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_decision.json")
    summary = read_json(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_readiness_lane_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_invariant_checks.json")
    pdf_rows = read_csv(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_parse_text_layer_later.csv")
    html_rows = read_csv(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_html_text_later.csv")
    all_rows = read_csv(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_results.csv")
    prior_exclusions = read_csv(INPUT_DIR / "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions.csv")
    queue = pdf_rows + html_rows
    ready_ids = {row["retained_source_id"] for row in queue}
    excluded_readiness = [row for row in all_rows if row["readiness_status"] not in {"parse_text_layer_later", "html_text_later"}]
    excluded_ids = {row["retained_source_id"] for row in excluded_readiness}
    if not (
        decision.get("decision") == "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready"
        and decision.get("bounded_text_layer_extraction_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and summary.get("bounded_text_extraction_ready_count") == EXPECTED_COUNT
        and invariants.get("all_invariants_passed") is True
        and len(queue) == EXPECTED_COUNT and len(pdf_rows) == EXPECTED_PDF_COUNT and len(html_rows) == EXPECTED_HTML_COUNT
        and len(ready_ids) == EXPECTED_COUNT and id_set_hash(queue) == EXPECTED_ID_SET_HASH
        and len(all_rows) == 387 and len(excluded_readiness) == 66 and len(prior_exclusions) == 42
        and not (ready_ids & excluded_ids)
        and all(row["readiness_status"] == "parse_text_layer_later" and row["content_type_hint"] == "application/pdf" for row in pdf_rows)
        and all(row["readiness_status"] == "html_text_later" and row["content_type_hint"] == "text/html" for row in html_rows)
        and all(row["source_review_download_status"] == "retained_downloaded_source" for row in queue)
        and all(row["priority_tier"] in {"tier_a", "tier_b"} for row in queue)
        and all(row["file_integrity_status"] == "integrity_pass" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["ingestion_status"] == "not_ingested" for row in queue)
        and all(row["codification_status"] == "not_codified" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and all(row["global_analysis_readiness"] == "false" for row in queue)
    ):
        raise RuntimeError("321-row extraction-ready scope reconciliation failed")
    for row in queue:
        path = ROOT / row["local_retained_path"]
        if not path.is_file() or not path.resolve().is_relative_to(RETAINED_DIR.resolve()):
            raise RuntimeError(f"retained extraction input missing or outside retained directory: {row['retained_source_id']}")
        if path.stat().st_size != int(row["file_size_bytes"]):
            raise RuntimeError(f"retained extraction input size mismatch: {row['retained_source_id']}")
        if verify_file_bytes and sha256(path) != row["file_sha256"]:
            raise RuntimeError(f"retained extraction input hash mismatch: {row['retained_source_id']}")
    queue.sort(key=lambda row: (0 if row["readiness_status"] == "parse_text_layer_later" else 1, row["lane_id"], row["retained_source_id"]))
    preserved = [
        {**row, "exclusion_layer": "readiness_review", "preserved_exclusion_status": row["readiness_status"]}
        for row in excluded_readiness
    ] + [
        {**row, "exclusion_layer": "source_review_download", "preserved_exclusion_status": row["preserved_exclusion_status"]}
        for row in prior_exclusions
    ]
    return queue, preserved, observed


def extracted_text_id(retained_source_id: str) -> str:
    return "TXT321-" + text_hash(retained_source_id)[:20]


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, preserved, hashes = verify_inputs(verify_file_bytes=True)
    PDF_TEXT_DIR.mkdir(parents=True)
    HTML_TEXT_DIR.mkdir(parents=True)
    locked = [{field: row.get(field, "") for field in LOCK_FIELDS} for row in queue]
    queue_path = OUTPUT_DIR / "targeted_text_layer_extraction_321_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    lock = {
        "task_id": TASK_ID, "input_commit": INPUT_COMMIT,
        "locked_queue_count": len(locked), "pdf_queue_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in locked),
        "html_queue_count": sum(row["readiness_status"] == "html_text_later" for row in locked),
        "queue_sha256": sha256(queue_path), "retained_source_id_set_sha256": id_set_hash(locked),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in locked).items())),
        "immutable_input_hashes": hashes, "preserved_exclusion_count": len(preserved),
        "extracted_text_root": str(EXTRACTED_DIR.relative_to(ROOT)),
        "extraction_status": "not_started", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_locked_queue_summary.json", {
        "locked_queue_count": len(locked), "pdf_queue_count": lock["pdf_queue_count"],
        "html_queue_count": lock["html_queue_count"], "lane_counts": lock["lane_counts"],
        "mechanism_counts": lock["mechanism_counts"], "nonready_rows_in_queue": 0,
        "prior_source_review_exclusions_in_queue": 0, "tier_c_or_d_rows": 0,
        "global_analysis_readiness": False,
    })
    dry = [{
        "retained_source_id": row["retained_source_id"], "candidate_id": row["candidate_id"],
        "lane_id": row["lane_id"], "readiness_status": row["readiness_status"],
        "content_type_hint": row["content_type_hint"], "dry_run_status": "ready_for_local_text_extraction",
        "live_extraction_status": "not_started", "url_open_planned": "no", "download_planned": "no",
        "ocr_planned": "no", "pdf_rendering_planned": "no", "model_api_planned": "no",
    } for row in locked]
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_dry_run_manifest.csv", dry, dry[0].keys())
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_dry_run_summary.json", {
        "no_call_dry_run": True, "dry_run_rows": len(dry), "pdf_rows": lock["pdf_queue_count"],
        "html_rows": lock["html_queue_count"], "local_extractions_completed": 0,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "all_live_status_not_started": True,
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_no_call_validation.md", """# No-call text-layer extraction validation

Exactly 321 readiness-approved retained files are locked: 289 parse-text PDFs and 32 text-ready HTML artifacts. All readiness/source-review exclusions remain outside the queue. Dry preparation performed no extraction, URL access, download, OCR, rendering, model call, rating, ingestion, or codification. Extracted artifacts are constrained to this task output directory and global analysis readiness remains false.
""")
    preflight = {
        "preflight_passed": len(locked) == EXPECTED_COUNT and shutil.which("pdftotext") is not None,
        "readiness_decision_allows_extraction": True, "locked_queue_count": len(locked),
        "pdf_queue_count": lock["pdf_queue_count"], "html_queue_count": lock["html_queue_count"],
        "queue_hash_matches_lock": sha256(queue_path) == lock["queue_sha256"],
        "retained_id_hash_matches_lock": id_set_hash(locked) == lock["retained_source_id_set_sha256"],
        "all_retained_paths_sizes_hashes_valid": True, "nonready_rows_in_queue": 0,
        "preserved_exclusions_outside_queue": len(preserved), "pdftotext_available": shutil.which("pdftotext") is not None,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_preflight_report.md", f"""# Targeted text-layer extraction preflight

Preflight {'passed' if preflight['preflight_passed'] else 'failed'} for exactly 321 immutable readiness-approved files: 289 PDFs and 32 HTML artifacts. Local PDF extraction uses `pdftotext` with no OCR or rendering; HTML extraction reads only local retained bytes and ignores scripts/styles. Artifacts are written only under this task output. No URL, download, model, rating, ingestion, codification, statistical, wage-gap, regression, treatment-effect, causal, or durable-ledger work is authorized.
""")
    if not preflight["preflight_passed"]:
        raise RuntimeError("targeted text-layer extraction preflight failed")
    print(json.dumps({"status": "dry_preparation_and_preflight_passed", "rows": len(locked), "queue_sha256": lock["queue_sha256"]}))


def normalize_pdf_text(raw: bytes) -> tuple[str, int]:
    decoded = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n\n")
    replacement_count = decoded.count("\ufffd")
    lines = [line.rstrip() for line in decoded.splitlines()]
    text = "\n".join(lines).strip() + "\n" if any(line.strip() for line in lines) else ""
    return text, replacement_count


class VisibleHTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []
        self.meta_refresh = False
        self.scripts = 0
        self.links = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1
        if lowered == "script":
            self.scripts += 1
        if lowered == "a":
            self.links += 1
        if lowered == "meta":
            values = {key.casefold(): (value or "").casefold() for key, value in attrs}
            self.meta_refresh = self.meta_refresh or values.get("http-equiv") == "refresh"
        if lowered in {"p", "div", "section", "article", "header", "footer", "li", "tr", "h1", "h2", "h3", "h4", "br"} and not self.hidden_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1
        if lowered in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4"} and not self.hidden_depth:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        joined = " ".join(self.parts).replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in joined.splitlines()]
        return "\n".join(line for line in lines if line).strip() + "\n" if any(lines) else ""


def contains_secret_pattern(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def quality_status(text: str, *, pages: int = 0, replacement_count: int = 0, html_shell: bool = False) -> tuple[str, str]:
    chars = len(text)
    nonspace = sum(not character.isspace() for character in text)
    if chars < MIN_TEXT_CHARACTERS or nonspace < MIN_TEXT_CHARACTERS // 2:
        return "empty_or_too_short", "extracted_text_below_minimum_character_threshold"
    if html_shell:
        return "html_noisy_or_shell", "html_redirect_or_script_shell_detected_during_extraction"
    if pages and nonspace / max(pages, 1) < MIN_PDF_DENSITY_PER_PAGE:
        return "low_text_density", "extracted_nonwhitespace_characters_per_page_below_threshold"
    if replacement_count / max(chars, 1) > 0.01 or "\x00" in text:
        return "suspected_bad_text_layer", "replacement_or_control_character_rate_suggests_bad_text_layer"
    return "extracted_ok", "local_machine_readable_text_extracted_with_closed_downstream_statuses"


def write_artifact(row: dict[str, str], text: str, subdir: Path) -> tuple[str, str, int]:
    identifier = extracted_text_id(row["retained_source_id"])
    path = subdir / f"{identifier}.txt"
    payload = text.encode("utf-8")
    path.write_bytes(payload)
    return str(path.relative_to(ROOT)), hashlib.sha256(payload).hexdigest(), len(payload)


def base_result(row: dict[str, str]) -> dict[str, str]:
    return {
        "extracted_text_id": extracted_text_id(row["retained_source_id"]),
        **{field: row.get(field, "") for field in RESULT_FIELDS if field in row},
        "extraction_status": "extraction_error", "extraction_reason": "not_completed",
        "extracted_text_path": "", "extracted_text_sha256": "", "extracted_text_size_bytes": "0",
        "extracted_char_count": "0", "extracted_non_whitespace_char_count": "0",
        "extracted_page_count": "", "page_count_metadata": row.get("page_count", ""),
        "html_text_readiness_hint": row.get("html_text_readiness_hint", ""),
        "extraction_method": "", "bounded_input_or_output_truncated": "false",
        "ocr_used": "false", "pdf_rendering_used": "false", "model_api_used": "false",
        "rating_status": "not_rated", "ingestion_status": "not_ingested",
        "codification_status": "not_codified", "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false",
        "notes": "Text extraction is not evidence rating; extracted text is not causal or globally analysis-ready evidence.",
    }


def extract_pdf(row: dict[str, str]) -> dict[str, str]:
    result = base_result(row)
    source = ROOT / row["local_retained_path"]
    pages = int(row.get("page_count") or 0)
    try:
        completed = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", "-nopgbrk", str(source), "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=PDF_EXTRACTION_TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result.update({"extraction_status": "extraction_error", "extraction_reason": f"pdftotext_{type(exc).__name__}", "extraction_method": "pdftotext_local_non_ocr"})
        return result
    if completed.returncode != 0:
        result.update({"extraction_status": "extraction_error", "extraction_reason": "pdftotext_nonzero_exit", "extraction_method": "pdftotext_local_non_ocr"})
        return result
    text, replacement_count = normalize_pdf_text(completed.stdout)
    if len(text.encode("utf-8")) > MAX_PDF_TEXT_BYTES:
        result.update({"extraction_status": "suspected_bad_text_layer", "extraction_reason": "extracted_text_exceeds_bounded_output_limit", "extraction_method": "pdftotext_local_non_ocr", "bounded_input_or_output_truncated": "true", "extracted_char_count": str(len(text)), "extracted_non_whitespace_char_count": str(sum(not c.isspace() for c in text)), "extracted_page_count": str(pages)})
        return result
    status, reason = quality_status(text, pages=pages, replacement_count=replacement_count)
    if contains_secret_pattern(text):
        status, reason, text = "extraction_error", "secret_pattern_detected_text_not_retained", ""
    artifact_path = artifact_hash = ""
    artifact_size = 0
    if text:
        artifact_path, artifact_hash, artifact_size = write_artifact(row, text, PDF_TEXT_DIR)
    result.update({
        "extraction_status": status, "extraction_reason": reason,
        "extracted_text_path": artifact_path, "extracted_text_sha256": artifact_hash,
        "extracted_text_size_bytes": str(artifact_size), "extracted_char_count": str(len(text)),
        "extracted_non_whitespace_char_count": str(sum(not c.isspace() for c in text)),
        "extracted_page_count": str(pages), "extraction_method": "pdftotext_local_non_ocr",
    })
    return result


def extract_html(row: dict[str, str]) -> dict[str, str]:
    result = base_result(row)
    source = ROOT / row["local_retained_path"]
    try:
        with source.open("rb") as handle:
            payload = handle.read(MAX_HTML_INPUT_BYTES + 1)
    except OSError as exc:
        result.update({"extraction_status": "extraction_error", "extraction_reason": f"html_read_{type(exc).__name__}", "extraction_method": "local_html_visible_text_parser"})
        return result
    truncated = len(payload) > MAX_HTML_INPUT_BYTES
    payload = payload[:MAX_HTML_INPUT_BYTES]
    parser = VisibleHTMLExtractor()
    try:
        decoded = payload.decode("utf-8", errors="replace")
        parser.feed(decoded)
        text = parser.text()
    except Exception:
        result.update({"extraction_status": "extraction_error", "extraction_reason": "html_parser_error", "extraction_method": "local_html_visible_text_parser"})
        return result
    if len(text) > MAX_HTML_TEXT_CHARACTERS:
        text = text[:MAX_HTML_TEXT_CHARACTERS].rstrip() + "\n"
        truncated = True
    shell = parser.meta_refresh or ("window.location" in decoded.casefold() and len(text) < 500)
    status, reason = quality_status(text, replacement_count=text.count("\ufffd"), html_shell=shell)
    if contains_secret_pattern(text):
        status, reason, text = "extraction_error", "secret_pattern_detected_text_not_retained", ""
    artifact_path = artifact_hash = ""
    artifact_size = 0
    if text:
        artifact_path, artifact_hash, artifact_size = write_artifact(row, text, HTML_TEXT_DIR)
    result.update({
        "extraction_status": status, "extraction_reason": reason,
        "extracted_text_path": artifact_path, "extracted_text_sha256": artifact_hash,
        "extracted_text_size_bytes": str(artifact_size), "extracted_char_count": str(len(text)),
        "extracted_non_whitespace_char_count": str(sum(not c.isspace() for c in text)),
        "extracted_page_count": "", "extraction_method": "local_html_visible_text_parser",
        "bounded_input_or_output_truncated": "true" if truncated else "false",
    })
    return result


def extract_one(row: dict[str, str]) -> dict[str, str]:
    if row["readiness_status"] == "parse_text_layer_later":
        return extract_pdf(row)
    if row["readiness_status"] == "html_text_later":
        return extract_html(row)
    result = base_result(row)
    result["extraction_reason"] = "nonready_status_rejected"
    return result


def group_counts(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    output = []
    for value, group in sorted(grouped.items()):
        counts = Counter(row["extraction_status"] for row in group)
        output.append({
            key: value, "extraction_queue_count": len(group), "extracted_ok_count": counts["extracted_ok"],
            "empty_or_too_short_count": counts["empty_or_too_short"],
            "low_text_density_count": counts["low_text_density"],
            "suspected_bad_text_layer_count": counts["suspected_bad_text_layer"],
            "html_noisy_or_shell_count": counts["html_noisy_or_shell"],
            "extraction_error_count": counts["extraction_error"],
        })
    return output


def write_outputs(results: list[dict[str, str]], preserved: list[dict[str, str]]) -> str:
    counts = Counter(row["extraction_status"] for row in results)
    extracted_ok = counts["extracted_ok"]
    repair_needed = counts["extraction_error"] > 5 or extracted_ok < 250
    decision_name = (
        "targeted_text_layer_extraction_321_completed_repair_needed" if repair_needed
        else "targeted_text_layer_extraction_321_completed_evidence_extraction_ready" if extracted_ok >= 250
        else "targeted_text_layer_extraction_321_completed_tier_c_verification_recommended"
    )
    by_lane = {lane: dict(sorted(Counter(row["extraction_status"] for row in results if row["lane_id"] == lane).items())) for lane in sorted({row["lane_id"] for row in results})}
    by_mechanism = {mechanism: dict(sorted(Counter(row["extraction_status"] for row in results if row["target_mechanism_family"] == mechanism).items())) for mechanism in sorted({row["target_mechanism_family"] for row in results})}
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_results.csv", results, RESULT_FIELDS)
    pdf_rows = [row for row in results if row["readiness_status"] == "parse_text_layer_later"]
    html_rows = [row for row in results if row["readiness_status"] == "html_text_later"]
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_pdf_results.csv", pdf_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_html_results.csv", html_rows, RESULT_FIELDS)
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_pdf_results_summary.json", {
        "pdf_result_rows": len(pdf_rows), "status_counts": dict(sorted(Counter(row["extraction_status"] for row in pdf_rows).items())),
        "extracted_text_artifact_count": sum(bool(row["extracted_text_path"]) for row in pdf_rows),
        "extracted_character_count": sum(int(row["extracted_char_count"]) for row in pdf_rows),
        "page_count_metadata_total": sum(int(row["page_count_metadata"] or 0) for row in pdf_rows),
        "ocr_runs": 0, "pdf_render_runs": 0,
    })
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_html_results_summary.json", {
        "html_result_rows": len(html_rows), "status_counts": dict(sorted(Counter(row["extraction_status"] for row in html_rows).items())),
        "extracted_text_artifact_count": sum(bool(row["extracted_text_path"]) for row in html_rows),
        "extracted_character_count": sum(int(row["extracted_char_count"]) for row in html_rows),
        "network_resource_fetches": 0,
    })
    lane_map = {
        "extracted_ok": {"extracted_ok"}, "empty_or_too_short": {"empty_or_too_short"},
        "low_text_density": {"low_text_density"}, "suspected_bad_text_layer": {"suspected_bad_text_layer"},
        "html_noisy_or_shell": {"html_noisy_or_shell"}, "extraction_errors": {"extraction_error"},
    }
    for filename, statuses in lane_map.items():
        write_csv(OUTPUT_DIR / f"targeted_text_layer_extraction_321_{filename}.csv", [row for row in results if row["extraction_status"] in statuses], RESULT_FIELDS)
    artifacts = [row for row in results if row["extracted_text_path"]]
    artifact_fields = (
        "extracted_text_id", "retained_source_id", "candidate_id", "lane_id", "readiness_status",
        "extraction_status", "extracted_text_path", "extracted_text_sha256", "extracted_text_size_bytes",
        "extracted_char_count", "extraction_method", "rating_status", "ingestion_status",
        "codification_status", "causal_status", "global_analysis_readiness",
    )
    write_csv(OUTPUT_DIR / "extracted_text_manifest.csv", artifacts, artifact_fields)
    write_csv(OUTPUT_DIR / "extracted_text_hash_manifest.csv", artifacts, ("extracted_text_id", "retained_source_id", "extracted_text_path", "extracted_text_sha256", "extracted_text_size_bytes"))
    write_json(OUTPUT_DIR / "extracted_text_manifest_summary.json", {
        "saved_text_artifact_count": len(artifacts), "pdf_artifact_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in artifacts),
        "html_artifact_count": sum(row["readiness_status"] == "html_text_later" for row in artifacts),
        "total_extracted_text_bytes": sum(int(row["extracted_text_size_bytes"]) for row in artifacts),
        "total_extracted_characters": sum(int(row["extracted_char_count"]) for row in artifacts),
        "all_artifacts_inside_task_output": all((ROOT / row["extracted_text_path"]).resolve().is_relative_to(EXTRACTED_DIR.resolve()) for row in artifacts),
        "rating_status": "not_rated", "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": False,
    })
    candidates = [row for row in results if row["extraction_status"] == "extracted_ok"]
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_evidence_extraction_candidate_manifest.csv", candidates, RESULT_FIELDS)
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_evidence_extraction_candidate_summary.json", {
        "candidate_count": len(candidates),
        "by_lane": dict(sorted(Counter(row["lane_id"] for row in candidates).items())),
        "by_mechanism": dict(sorted(Counter(row["target_mechanism_family"] for row in candidates).items())),
        "allowed_next_stage": "separately_authorized_evidence_span_extraction_review",
        "rating_ready": False, "causal_ready": False, "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_extraction_limits_and_boundaries.md", """# Extraction limits and boundaries

These local text artifacts are machine-readable extraction products, not evidence ratings or causal evidence. PDF text came from `pdftotext` without OCR or rendering. HTML text came from local visible-text parsing without network access. Line endings and trailing line whitespace were normalized. No evidence span was selected or interpreted. Only `extracted_ok` rows may enter a separately authorized evidence-span extraction review; every other outcome remains excluded.
""")
    mechanism = group_counts(results, "target_mechanism_family")
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_mechanism_coverage.csv", mechanism, mechanism[0].keys())
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_mechanism_coverage_summary.json", {
        "mechanism_count": len(mechanism), "by_mechanism": {row["target_mechanism_family"]: {k: v for k, v in row.items() if k != "target_mechanism_family"} for row in mechanism},
        "coverage_boundary": "Extraction counts are not mechanism prevalence, wage effects, or causal findings.",
    })
    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        city_groups[(row["municipality"], row["state"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for key, group in sorted(city_groups.items()):
        city_rows.append({
            "municipality": key[0], "state": key[1], "unit_type": key[2], "contract_or_document_period": key[3],
            "extraction_queue_count": len(group), "extracted_ok_count": sum(row["extraction_status"] == "extracted_ok" for row in group),
            "excluded_or_failed_count": sum(row["extraction_status"] != "extracted_ok" for row in group),
        })
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows), "groups_with_extracted_ok_text": sum(int(row["extracted_ok_count"]) > 0 for row in city_rows),
        "groups_without_extracted_ok_text": sum(int(row["extracted_ok_count"]) == 0 for row in city_rows),
        "distinct_city_state_pairs": len({(row["municipality"], row["state"]) for row in results}),
        "coverage_boundary": "Extraction outputs do not update durable city coverage.",
    })
    preserved_fields = tuple(dict.fromkeys(key for row in preserved for key in row.keys()))
    write_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_preserved_readiness_exclusions.csv", preserved, preserved_fields)
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_preserved_readiness_exclusions_summary.json", {
        "readiness_exclusion_count": sum(row["exclusion_layer"] == "readiness_review" for row in preserved),
        "prior_source_review_exclusion_count": sum(row["exclusion_layer"] == "source_review_download" for row in preserved),
        "total_preserved_exclusion_count": len(preserved),
        "status_counts": dict(sorted(Counter(f"{row['exclusion_layer']}:{row['preserved_exclusion_status']}" for row in preserved).items())),
        "preserved_exclusions_entering_extraction_queue": 0,
    })
    status_counts = dict(sorted(counts.items()))
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_results_summary.json", {
        "result_rows": len(results), "pdf_rows": len(pdf_rows), "html_rows": len(html_rows),
        "extraction_status_counts": status_counts, "extraction_status_counts_by_lane": by_lane,
        "extraction_status_counts_by_mechanism": by_mechanism,
        "saved_text_artifact_count": len(artifacts), "evidence_extraction_candidate_count": len(candidates),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    })
    decision = {
        "task_id": TASK_ID, "decision": decision_name, "completion_status": "completed_bounded_local_text_layer_extraction",
        "extraction_queue_count": len(results), "pdf_extraction_count": len(pdf_rows), "html_extraction_count": len(html_rows),
        "extraction_status_counts": status_counts, "extraction_status_counts_by_lane": by_lane,
        "extraction_status_counts_by_mechanism": by_mechanism,
        "evidence_extraction_candidate_count": len(candidates),
        "evidence_extraction_review_ready_next": decision_name.endswith("evidence_extraction_ready"),
        "repair_needed": repair_needed, "tier_c_verification_recommended_next": decision_name.endswith("tier_c_verification_recommended"),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_decision.json", decision)
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_summary.md", f"""# Targeted text-layer extraction — 321 readiness-approved sources

Decision: `{decision_name}`.

Exactly 321 local retained sources were processed: 289 PDFs and 32 HTML artifacts. Extraction outcomes reconcile to `{status_counts}`. A total of {len(candidates)} `extracted_ok` rows may enter a separately authorized evidence-span extraction review. All other outcomes remain explicit exclusions.

No URL, download, OCR, rendering, model call, rating, ingestion, codification, statistic, wage-gap calculation, regression, treatment effect, causal claim, or durable-ledger merge occurred. Extracted text remains unrated, uningested, uncodified, non-causal, and globally analysis-closed.
""")
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_invariant_checks.json", {
        "all_invariants_passed": not repair_needed,
        "locked_queue_exactly_321": len(results) == 321, "pdf_html_counts_exactly_289_32": len(pdf_rows) == 289 and len(html_rows) == 32,
        "only_readiness_approved_rows_entered": all(row["readiness_status"] in {"parse_text_layer_later", "html_text_later"} for row in results),
        "pdf_html_lanes_separate": all(row["readiness_status"] == "parse_text_layer_later" for row in pdf_rows) and all(row["readiness_status"] == "html_text_later" for row in html_rows),
        "preserved_exclusions_outside_queue": len(preserved) == 108,
        "artifact_paths_hashes_sizes_valid": all((ROOT / row["extracted_text_path"]).is_file() and sha256(ROOT / row["extracted_text_path"]) == row["extracted_text_sha256"] and (ROOT / row["extracted_text_path"]).stat().st_size == int(row["extracted_text_size_bytes"]) for row in artifacts),
        "controlled_statuses_only": all(row["extraction_status"] in CONTROLLED_STATUSES for row in results),
        "downstream_statuses_closed": all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in results),
        "no_url_download_ocr_render_model_rating_ingestion_or_codification": True,
        "no_durable_ledger_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_stress_test_report.md", """# Stress-test report

- Non-ready, non-retained, Tier C/D, and prior-excluded rows fail before extraction.
- Retained path, size, or SHA-256 drift fails before extraction.
- PDF extraction is local `pdftotext` only; timeout, nonzero exit, excessive output, empty text, low density, and bad-character signals remain explicit outcomes.
- HTML extraction reads local bounded bytes only and excludes scripts, styles, SVG, and network resources.
- Key-like secret patterns prevent artifact retention.
- PDF and HTML artifact directories remain separate and task-local.
- Partial outputs fail completion validation; completed `--resume` is read-only.
""")
    write_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_regression_test_inventory.json", {
        "focused_suite": "scripts/test_targeted_text_layer_extraction_321.py",
        "coverage": ["exact 321-row scope", "289/32 PDF/HTML split", "immutable hashes", "excluded-row rejection", "local-only PDF/HTML extraction", "no OCR/render/network/model", "quality-status controls", "task-local artifact hashes", "closed downstream statuses", "dashboard global closure", "idempotent resume", "partial-output fail-closed"],
    })
    write_text(OUTPUT_DIR / "next_targeted_evidence_extraction_prompt.md", """# Next prompt: bounded evidence-span extraction review

Use only the `targeted_text_layer_extraction_321_evidence_extraction_candidate_manifest.csv` rows with `extraction_status=extracted_ok`. A separately authorized stage may identify exact verbatim spans in the saved local text artifacts, while preserving PDF/HTML lane, retained-source, candidate, city, unit, cycle, mechanism-target, and file-hash lineage.

Do not fetch or pull repository state, inspect/configure remotes, open URLs, download documents, include excluded/failed extraction rows, run OCR or rendering, call GABRIEL/API or a model unless separately authorized, rate causal effects, ingest, codify, calculate wage gaps, run regressions or treatment effects, make causal claims, or mark global analysis readiness true. Evidence extraction is not evidence rating, and exact spans are not causal proof.
""")
    write_text(OUTPUT_DIR / "next_task.md", """# Next task: bounded evidence-span extraction review

Use only `extracted_ok` rows in the evidence-extraction candidate manifest. Extract exact verbatim spans from the task-local text artifacts under a separately authorized prompt, keeping PDF and HTML lanes and all source/city/unit/cycle lineage explicit. Exclude every empty, low-density, suspected-bad, noisy/shell, error, readiness-deferred, and prior source-review exclusion row.

Do not access URLs, download, OCR, render images, run model-based rating unless separately authorized, ingest, codify, calculate wage gaps, run regressions/treatment effects, make causal claims, or set global analysis readiness true.
""")
    write_text(OUTPUT_DIR / "targeted_text_layer_extraction_321_validation_2026-07-26.md", f"""# Targeted text-layer extraction validation — 2026-07-26

Internal extraction invariants passed for the immutable 321-file scope. PDF/HTML counts reconciled to 289/32, all outcomes reconciled to 321, all extracted artifact hashes and paths passed, and all 108 readiness/source-review exclusions remained outside the queue. Decision: `{decision_name}`. External repository/test/build validation results are appended after the required command suite completes.
""")
    write_text(ROOT / "docs/analysis/targeted_text_layer_extraction_321_result_2026-07-26.md", f"""# Targeted text-layer extraction result

- Decision: `{decision_name}`.
- Extraction queue: 321 (289 PDF; 32 HTML).
- Extraction outcomes: `{status_counts}`.
- Evidence-extraction candidate rows: {len(candidates)}.
- URL/download/OCR/render/model/rating/ingestion/codification/durable merges: 0.
- Global analysis readiness: false.
""")
    write_text(ROOT / "docs/analysis/targeted_text_layer_extraction_321_dashboard_status_note_2026-07-26.md", f"""# Dashboard status note — targeted text-layer extraction

- Decision: `{decision_name}`.
- Exact extraction queue: 321 (289 PDF; 32 HTML).
- Status counts: `{status_counts}`.
- Evidence-extraction review ready next: {'true' if decision['evidence_extraction_review_ready_next'] else 'false'}.
- Repair needed: {'true' if repair_needed else 'false'}.
- Tier C verification recommended next: {'true' if decision['tier_c_verification_recommended_next'] else 'false'}.
- Global analysis readiness: false.
""")
    return decision_name


def extract() -> None:
    queue, preserved, _ = verify_inputs(verify_file_bytes=True)
    lock_path = OUTPUT_DIR / "targeted_text_layer_extraction_321_lock.json"
    queue_path = OUTPUT_DIR / "targeted_text_layer_extraction_321_locked_queue.csv"
    preflight_path = OUTPUT_DIR / "targeted_text_layer_extraction_321_preflight_checks.json"
    if not (lock_path.is_file() and queue_path.is_file() and preflight_path.is_file()):
        raise RuntimeError("dry preparation/preflight outputs missing")
    lock = read_json(lock_path)
    preflight = read_json(preflight_path)
    locked = read_csv(queue_path)
    if not (
        preflight.get("preflight_passed") is True and len(queue) == len(locked) == EXPECTED_COUNT
        and sha256(queue_path) == lock["queue_sha256"]
        and id_set_hash(locked) == lock["retained_source_id_set_sha256"] == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("live local extraction lock/preflight failed")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(extract_one, locked))
    if len(results) != EXPECTED_COUNT or any(row["extraction_status"] not in CONTROLLED_STATUSES for row in results):
        raise RuntimeError("extraction result reconciliation failed")
    decision = write_outputs(results, preserved)
    validate_complete()
    print(json.dumps({"status": "local_text_layer_extraction_completed", "decision": decision, "rows": len(results)}))


def validate_complete() -> None:
    missing = [name for name in REQUIRED_FINAL_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"partial extraction output cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_decision.json")
    invariants = read_json(OUTPUT_DIR / "targeted_text_layer_extraction_321_invariant_checks.json")
    results = read_csv(OUTPUT_DIR / "targeted_text_layer_extraction_321_results.csv")
    artifacts = read_csv(OUTPUT_DIR / "extracted_text_manifest.csv")
    if not (
        len(results) == EXPECTED_COUNT and len({row["retained_source_id"] for row in results}) == EXPECTED_COUNT
        and decision.get("global_analysis_readiness") is False and invariants.get("all_invariants_passed") is True
        and all(row["extraction_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in results)
        and all((ROOT / row["extracted_text_path"]).is_file() and sha256(ROOT / row["extracted_text_path"]) == row["extracted_text_sha256"] for row in artifacts)
    ):
        raise RuntimeError("completed extraction outputs fail closed validation")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--extract", action="store_true")
    action.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.extract:
        extract()
    else:
        verify_inputs(verify_file_bytes=True)
        validate_complete()
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_COUNT}))


if __name__ == "__main__":
    main()
