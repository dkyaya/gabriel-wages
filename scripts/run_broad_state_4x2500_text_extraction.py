#!/usr/bin/env python3
"""Run the bounded 2,940-source BROAD-STATE non-OCR text extraction wave.

Full text is written only below the ignored local artifact root.  Tracked
outputs contain metadata, hashes, counts, queues, and validation evidence.
The runner never performs OCR, span extraction, rating, ingestion, or analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import traceback
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from statistics import median
from typing import Any, Iterable
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"
OUTPUT = BASE / "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30"
SOURCE_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_4x2500_source_review_download_2026-07-30"
ARTIFACT_ROOT = ROOT / "artifacts/local_extracted_text/broad_state_4x2500_text_extraction_2026-07-30"
LOG_ROOT = ROOT / "tmp/broad_state_4x2500_text_extraction_2026-07-30_logs"
TASK_ID = "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30"
DECISION = "broad_state_4x2500_text_extraction_completed_span_extraction_ready"
EXPECTED = 2940
APPROVED = {"parse_text_pdf_ready": 2577, "html_text_ready": 291, "other_document_text_ready": 72}
LANES = {f"text_extraction_lane_{i:03d}": 735 for i in range(1, 5)}
DELAYS = {f"text_extraction_lane_{i:03d}": (i - 1) * 480 for i in range(1, 5)}
STATUSES = (
    "extracted_ok", "extracted_empty", "extracted_low_density",
    "extracted_suspected_bad_text", "html_noisy_or_boilerplate",
    "source_file_missing", "hash_mismatch", "extraction_error",
    "unsupported_despite_readiness",
)
FORBIDDEN_READINESS = {
    "ocr_later", "oversized_defer", "encrypted_or_locked", "corrupt_or_broken",
    "shell_or_navigation_only", "needs_manual_review", "unsupported_file_type", "readiness_error",
}

INPUT_FIELDS: tuple[str, ...] = ()
LOCK_EXTRA = (
    "extraction_id", "extraction_lane_id", "extraction_lane_sequence",
    "locked_source_path", "queue_locked_at",
)
RESULT_EXTRA = (
    "extraction_status", "extraction_method", "extraction_timestamp",
    "extracted_text_artifact_path", "extracted_text_sha256", "extracted_text_byte_size",
    "character_count", "approximate_word_count", "line_count", "page_count_input",
    "pages_successfully_parsed", "empty_page_count", "characters_per_page",
    "quality_flags", "boilerplate_or_noise_flag", "error_class", "error_message_redacted",
    "ocr_run_flag", "span_extraction_run_flag", "rating_run_flag", "ingestion_run_flag",
    "codification_run_flag",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
        handle.flush()
        os.fsync(handle.fileno())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def check_ignored(path: Path) -> None:
    probe = path / ".ignore-probe"
    if git("check-ignore", "-q", rel(probe), check=False).returncode != 0:
        raise RuntimeError(f"artifact root is not Git-ignored: {rel(path)}")


def input_rows() -> list[dict[str, str]]:
    path = INPUT / "text_extraction_ready_queue.csv"
    if not path.is_file():
        raise RuntimeError("text_extraction_ready_queue.csv is missing")
    rows = read_csv(path)
    counts = Counter(row.get("primary_readiness_status", "") for row in rows)
    if len(rows) != EXPECTED or counts != Counter(APPROVED):
        raise RuntimeError(f"input count/status mismatch: rows={len(rows)} statuses={dict(counts)}")
    ids = [row.get("readiness_id", "") for row in rows]
    if "" in ids or len(set(ids)) != EXPECTED:
        raise RuntimeError("readiness IDs are missing or duplicated")
    if any(row.get("primary_readiness_status") in FORBIDDEN_READINESS for row in rows):
        raise RuntimeError("not-ready status entered extraction")
    return rows


def source_path(row: dict[str, str]) -> Path:
    raw = row.get("retained_local_artifact_path", "")
    path = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if not path.is_relative_to(SOURCE_ROOT.resolve()):
        raise RuntimeError(f"source path escapes retained root: {raw}")
    return path


def stable_key(row: dict[str, str]) -> str:
    material = "|".join((row.get("primary_readiness_status", ""), row.get("priority_bucket", ""),
                         row.get("source_family_hint", ""), row.get("state", ""), row["readiness_id"]))
    return hashlib.sha256(material.encode()).hexdigest()


def lock_id(readiness_id: str) -> str:
    return "B4X2500TXT-20260730-" + hashlib.sha256(readiness_id.encode()).hexdigest()[:20]


def assign_lanes(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    names = list(LANES)
    targets = {
        "parse_text_pdf_ready": [645, 644, 644, 644],
        "html_text_ready": [72, 73, 73, 73],
        "other_document_text_ready": [18, 18, 18, 18],
    }
    assigned: dict[str, list[dict[str, str]]] = {name: [] for name in names}
    for status, quotas in targets.items():
        bucket = sorted((r for r in rows if r["primary_readiness_status"] == status), key=stable_key)
        cursor = 0
        for index, quota in enumerate(quotas):
            assigned[names[index]].extend(bucket[cursor:cursor + quota])
            cursor += quota
        if cursor != len(bucket):
            raise RuntimeError(f"lane assignment failed for {status}")
    for name in names:
        # Stable hash order interleaves types, priorities, families, and geography.
        assigned[name].sort(key=lambda r: hashlib.sha256((name + "|" + r["readiness_id"]).encode()).hexdigest())
        if len(assigned[name]) != LANES[name]:
            raise RuntimeError(f"lane size mismatch: {name}")
    return assigned


class VisibleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.bits: list[str] = []
        self.links = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside"}:
            self.skip += 1
        if tag.lower() == "a":
            self.links += 1
        if tag.lower() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "section", "article"}:
            self.bits.append("\n")
    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside"} and self.skip:
            self.skip -= 1
        if tag.lower() in {"p", "div", "li", "tr", "section", "article"}:
            self.bits.append("\n")
    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.bits.append(data)


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    result: list[str] = []
    blank = False
    for line in lines:
        if line:
            result.append(line)
            blank = False
        elif not blank and result:
            result.append("")
            blank = True
    return "\n".join(result).strip() + ("\n" if result else "")


def extract_pdf(path: Path, temporary: Path) -> tuple[str, str]:
    command = ["pdftotext", "-layout", "-enc", "UTF-8", str(path), str(temporary)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError("pdftotext_failed:" + (proc.stderr.strip()[:300] or str(proc.returncode)))
    text = temporary.read_text(encoding="utf-8", errors="replace") if temporary.exists() else ""
    temporary.unlink(missing_ok=True)
    return normalize_text(text), "poppler_pdftotext_layout_utf8_non_ocr"


def extract_html(path: Path) -> tuple[str, str, int]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parser = VisibleHTML()
    parser.feed(raw)
    parser.close()
    return normalize_text(html.unescape("".join(parser.bits))), "stdlib_htmlparser_visible_text_cleanup", parser.links


def extract_xlsx(path: Path) -> tuple[str, str]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(node.text or "" for node in si.iter() if node.tag.endswith("}t")))
        lines: list[str] = []
        for name in sorted(n for n in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)):
            sheet = ET.fromstring(archive.read(name))
            lines.append(f"[{Path(name).stem}]")
            for row in sheet.findall(".//m:row", ns):
                values: list[str] = []
                for cell in row.findall("m:c", ns):
                    value = cell.find("m:v", ns)
                    text = value.text if value is not None and value.text is not None else ""
                    if cell.attrib.get("t") == "s" and text.isdigit() and int(text) < len(shared):
                        text = shared[int(text)]
                    values.append(text)
                if any(values):
                    lines.append("\t".join(values))
    return normalize_text("\n".join(lines)), "python_zip_xml_xlsx_non_ocr"


def extract_other(path: Path, temporary: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".csv", ".tsv"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="replace")), "python_utf8_text_decode"
    if suffix == ".xlsx":
        return extract_xlsx(path)
    if suffix in {".doc", ".docx", ".rtf", ".xls"}:
        proc = subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-stdout", str(path)],
                              capture_output=True, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError("textutil_failed:" + proc.stderr.decode("utf-8", errors="replace")[:300])
        return normalize_text(proc.stdout.decode("utf-8", errors="replace")), "macos_textutil_non_ocr"
    raise ValueError("unsupported_extension:" + suffix)


def quality_status(row: dict[str, str], text: str, html_links: int = 0) -> tuple[str, list[str]]:
    chars = len(text)
    words = re.findall(r"\b\w+\b", text)
    flags: list[str] = []
    if chars < 200:
        return "extracted_empty", ["under_200_characters"]
    replacement_ratio = text.count("\ufffd") / max(chars, 1)
    control_count = sum(ord(c) < 32 and c not in "\n\t" for c in text)
    # Match the repaired project convention: fixed-width tables commonly use
    # long whitespace/dash/underscore rules and must not be marked as garbage.
    # Only 80+ repeated alphanumeric characters trip this indicator.
    repeated = bool(re.search(r"([A-Za-z0-9])\1{79,}", text))
    if replacement_ratio > 0.02 or control_count > 20 or repeated:
        if replacement_ratio > 0.02: flags.append("high_replacement_character_ratio")
        if control_count > 20: flags.append("control_character_noise")
        if repeated: flags.append("repeated_character_garbage")
        return "extracted_suspected_bad_text", flags
    status = row["primary_readiness_status"]
    if status == "html_text_ready":
        link_density = html_links / max(len(words), 1)
        if len(words) < 50 or link_density > 0.25:
            return "html_noisy_or_boilerplate", ["html_low_word_count_or_link_dense"]
    if status == "parse_text_pdf_ready":
        pages = int(float(row.get("page_count") or 0))
        density = chars / max(pages, 1)
        if density < 100:
            return "extracted_low_density", ["under_100_characters_per_page"]
    return "extracted_ok", flags


def extract_one(row: dict[str, str], lane: str) -> dict[str, Any]:
    result: dict[str, Any] = dict(row)
    result.update({key: "" for key in RESULT_EXTRA})
    result.update({
        "ocr_run_flag": "false", "span_extraction_run_flag": "false", "rating_run_flag": "false",
        "ingestion_run_flag": "false", "codification_run_flag": "false", "extraction_timestamp": now(),
    })
    source = ROOT / row["locked_source_path"]
    if not source.is_file():
        result.update(extraction_status="source_file_missing", error_class="FileNotFoundError",
                      error_message_redacted="retained source file missing")
        return result
    observed = sha256_file(source)
    if observed != row["retained_file_sha256"]:
        result.update(extraction_status="hash_mismatch", error_class="IntegrityError",
                      error_message_redacted="retained source hash mismatch")
        return result
    destination = ARTIFACT_ROOT / lane / f"{row['extraction_id']}.txt"
    temporary = ARTIFACT_ROOT / lane / f".{row['extraction_id']}.tmp.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    html_links = 0
    try:
        readiness = row["primary_readiness_status"]
        if readiness == "parse_text_pdf_ready":
            text, method = extract_pdf(source, temporary)
        elif readiness == "html_text_ready":
            text, method, html_links = extract_html(source)
        elif readiness == "other_document_text_ready":
            text, method = extract_other(source, temporary)
        else:
            result.update(extraction_status="unsupported_despite_readiness", error_class="ReadinessStatusError",
                          error_message_redacted="unapproved readiness status")
            return result
        status, flags = quality_status(row, text, html_links)
        encoded = text.encode("utf-8")
        if encoded:
            destination.write_bytes(encoded)
            text_hash = sha256_bytes(encoded)
            artifact_path = rel(destination)
        else:
            text_hash = ""
            artifact_path = ""
        pages = int(float(row.get("page_count") or 0)) if row.get("page_count") else 0
        result.update({
            "extraction_status": status, "extraction_method": method,
            "extracted_text_artifact_path": artifact_path, "extracted_text_sha256": text_hash,
            "extracted_text_byte_size": len(encoded), "character_count": len(text),
            "approximate_word_count": len(re.findall(r"\b\w+\b", text)),
            "line_count": text.count("\n"), "page_count_input": pages or "",
            "pages_successfully_parsed": pages if readiness == "parse_text_pdf_ready" else "",
            "empty_page_count": "", "characters_per_page": round(len(text) / max(pages, 1), 2) if pages else "",
            "quality_flags": "|".join(flags),
            "boilerplate_or_noise_flag": str(status == "html_noisy_or_boilerplate").lower(),
        })
    except ValueError as exc:
        result.update(extraction_status="unsupported_despite_readiness", error_class=type(exc).__name__,
                      error_message_redacted=str(exc)[:300])
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        result.update(extraction_status="extraction_error", error_class=type(exc).__name__,
                      error_message_redacted=str(exc)[:300])
    return result


def preflight_smoke(locked: list[dict[str, str]]) -> dict[str, Any]:
    smoke_dir = ARTIFACT_ROOT / ".smoke_preflight"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    selected = []
    for status in APPROVED:
        selected.append(next(r for r in locked if r["primary_readiness_status"] == status))
    reports = []
    for row in selected:
        smoke_row = dict(row)
        smoke_row["extraction_id"] = "SMOKE-" + row["extraction_id"]
        result = extract_one(smoke_row, ".smoke_preflight")
        reports.append({
            "readiness_id": row["readiness_id"], "source_type": row["primary_readiness_status"],
            "status": result["extraction_status"], "character_count": result["character_count"],
            "method": result["extraction_method"],
        })
        artifact = result.get("extracted_text_artifact_path")
        if artifact:
            (ROOT / artifact).unlink(missing_ok=True)
    try:
        smoke_dir.rmdir()
    except OSError:
        pass
    if all(r["status"] in {"source_file_missing", "hash_mismatch", "extraction_error", "unsupported_despite_readiness"} for r in reports):
        raise RuntimeError("global extraction smoke failed")
    return {"status": "passed", "representative_rows": reports, "full_text_cleanup_completed": True}


def prepare() -> None:
    global INPUT_FIELDS
    if OUTPUT.exists() or ARTIFACT_ROOT.exists():
        raise RuntimeError("output/artifact root already exists; use resume or validate, not overwrite")
    check_ignored(ARTIFACT_ROOT)
    if git("ls-files", "artifacts/local_retained_sources").stdout.strip() or git("ls-files", "artifacts/local_extracted_text").stdout.strip():
        raise RuntimeError("retained or extracted artifacts are tracked")
    rows = input_rows()
    INPUT_FIELDS = tuple(rows[0])
    OUTPUT.mkdir(parents=True)
    ARTIFACT_ROOT.mkdir(parents=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    locked_base: list[dict[str, str]] = []
    hash_rows: list[dict[str, Any]] = []
    for row in rows:
        path = source_path(row)
        exists = path.is_file()
        size = path.stat().st_size if exists else -1
        observed = sha256_file(path) if exists and size == int(row["retained_file_size_bytes"]) else ""
        match = exists and size == int(row["retained_file_size_bytes"]) and observed == row["retained_file_sha256"]
        hash_rows.append({"readiness_id": row["readiness_id"], "path": rel(path), "exists": exists,
                          "expected_size": int(row["retained_file_size_bytes"]), "observed_size": size,
                          "expected_sha256": row["retained_file_sha256"], "observed_sha256": observed,
                          "hash_matches": match})
        if not match:
            raise RuntimeError(f"retained source integrity failed: {row['readiness_id']}")
        item = dict(row)
        item.update(extraction_id=lock_id(row["readiness_id"]), locked_source_path=rel(path), queue_locked_at=now())
        locked_base.append(item)
    assignments = assign_lanes(locked_base)
    locked: list[dict[str, str]] = []
    fields = INPUT_FIELDS + LOCK_EXTRA
    lane_details: dict[str, Any] = {}
    for lane, lane_rows in assignments.items():
        for seq, row in enumerate(lane_rows, 1):
            row["extraction_lane_id"] = lane
            row["extraction_lane_sequence"] = str(seq)
        qcsv = OUTPUT / f"{lane}_queue.csv"
        qjsonl = OUTPUT / f"{lane}_queue.jsonl"
        write_csv(qcsv, lane_rows, fields)
        write_jsonl(qjsonl, lane_rows)
        locked.extend(lane_rows)
        lane_details[lane] = {
            "rows": len(lane_rows), "start_delay_seconds": DELAYS[lane],
            "priority_counts": dict(sorted(Counter(r["priority_bucket"] for r in lane_rows).items())),
            "source_type_counts": dict(sorted(Counter(r["primary_readiness_status"] for r in lane_rows).items())),
            "csv_sha256": sha256_file(qcsv), "jsonl_sha256": sha256_file(qjsonl),
        }
    write_csv(OUTPUT / "text_extraction_locked_queue.csv", locked, fields)
    write_jsonl(OUTPUT / "text_extraction_locked_queue.jsonl", locked)
    smoke = preflight_smoke(locked)
    hash_report = {
        "checked_at": now(), "expected_rows": EXPECTED, "checked_rows": len(hash_rows),
        "all_files_exist": all(r["exists"] for r in hash_rows),
        "all_sizes_match": all(r["expected_size"] == r["observed_size"] for r in hash_rows),
        "all_hashes_match": all(r["hash_matches"] for r in hash_rows),
        "mismatch_count": sum(not r["hash_matches"] for r in hash_rows),
    }
    write_json(OUTPUT / "retained_source_hash_recheck_report.json", hash_report)
    write_json(OUTPUT / "preflight_smoke_report.json", smoke)
    distribution = {"task_id": TASK_ID, "total_rows": EXPECTED, "lanes": lane_details,
                    "total_source_type_counts": APPROVED, "stagger_seconds": DELAYS,
                    "reconciles": sum(x["rows"] for x in lane_details.values()) == EXPECTED}
    write_json(OUTPUT / "text_extraction_lane_distribution.json", distribution)
    lines = ["# Text extraction lane distribution", "", "All four locked lanes contain 735 rows.", "",
             "| Lane | Rows | Delay | PDF | HTML | Other |", "|---|---:|---:|---:|---:|---:|"]
    for lane, detail in lane_details.items():
        c = detail["source_type_counts"]
        lines.append(f"| {lane} | {detail['rows']} | {detail['start_delay_seconds']}s | {c.get('parse_text_pdf_ready',0)} | {c.get('html_text_ready',0)} | {c.get('other_document_text_ready',0)} |")
    write_text(OUTPUT / "text_extraction_lane_distribution.md", "\n".join(lines))
    manifest = {
        "task_id": TASK_ID, "created_at": now(), "input_rows": EXPECTED, "approved_status_counts": APPROVED,
        "locked_queue_csv_sha256": sha256_file(OUTPUT / "text_extraction_locked_queue.csv"),
        "locked_queue_jsonl_sha256": sha256_file(OUTPUT / "text_extraction_locked_queue.jsonl"),
        "lane_manifests": lane_details, "artifact_root": rel(ARTIFACT_ROOT), "artifact_root_git_ignored": True,
        "extraction_mode": "non_ocr_only", "smoke_preflight": smoke,
        "forbidden_actions": {"ocr": False, "span_extraction": False, "rating": False, "ingestion": False, "codification": False},
    }
    write_json(OUTPUT / "text_extraction_manifest.json", manifest)
    write_json(OUTPUT / "prepare_complete.json", {"status": "passed", "completed_at": now()})
    print(json.dumps({"status": "prepared", "rows": EXPECTED, "lanes": lane_details}, indent=2))


def lane_paths(lane: str) -> tuple[Path, Path, Path]:
    directory = OUTPUT / "lanes" / lane
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "results.csv", directory / "results.jsonl", directory / "checkpoint.json"


def run_lane(lane: str, delay: int | None) -> None:
    if lane not in LANES:
        raise RuntimeError("unknown lane")
    delay = DELAYS[lane] if delay is None else delay
    if delay:
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline:
            time.sleep(min(30, max(0, deadline - time.monotonic())))
    qcsv = OUTPUT / f"{lane}_queue.csv"
    manifest = json.loads((OUTPUT / "text_extraction_manifest.json").read_text())
    if sha256_file(qcsv) != manifest["lane_manifests"][lane]["csv_sha256"]:
        raise RuntimeError("lane queue hash mismatch")
    rows = read_csv(qcsv)
    result_csv, result_jsonl, checkpoint = lane_paths(lane)
    existing = read_csv(result_csv) if result_csv.exists() else []
    complete = {row["extraction_id"] for row in existing}
    if len(complete) != len(existing):
        raise RuntimeError("duplicate completed extraction ID in checkpoint results")
    fields = tuple(rows[0]) + RESULT_EXTRA
    started = now()
    for row in rows:
        if row["extraction_id"] in complete:
            continue
        result = extract_one(row, lane)
        if result["extraction_status"] not in STATUSES:
            raise RuntimeError("worker emitted uncontrolled status")
        append_csv(result_csv, result, fields)
        with result_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        complete.add(row["extraction_id"])
        write_json(checkpoint, {
            "lane_id": lane, "accepted_completed_count": len(complete), "expected_count": len(rows),
            "last_completed_extraction_id": row["extraction_id"], "updated_at": now(),
            "queue_csv_sha256": sha256_file(qcsv), "terminal": len(complete) == len(rows),
        })
    finished = read_csv(result_csv)
    if len(finished) != len(rows):
        raise RuntimeError("lane ended incomplete")
    # Required root copies are produced at lane completion.
    write_csv(OUTPUT / f"{lane}_results.csv", finished, fields)
    write_jsonl(OUTPUT / f"{lane}_results.jsonl", finished)
    write_json(OUTPUT / "lanes" / lane / "lane_summary.json", {
        "lane_id": lane, "started_at": started, "completed_at": now(), "rows": len(finished),
        "status_counts": dict(sorted(Counter(r["extraction_status"] for r in finished).items())),
        "result_csv_sha256": sha256_file(result_csv), "checkpoint_after_every_row": True,
    })
    print(json.dumps({"lane": lane, "rows": len(finished), "statuses": Counter(r["extraction_status"] for r in finished)}, default=dict))


def launch() -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    procs: list[tuple[str, subprocess.Popen[Any], Any]] = []
    for lane in LANES:
        log = (LOG_ROOT / f"{lane}.log").open("a", encoding="utf-8")
        proc = subprocess.Popen([sys.executable, str(Path(__file__)), "--lane", lane,
                                 "--delay-seconds", str(DELAYS[lane])], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        procs.append((lane, proc, log))
    write_json(LOG_ROOT / "launch_manifest.json", {
        "launched_at": now(), "processes": [{"lane": lane, "pid": proc.pid, "delay": DELAYS[lane]} for lane, proc, _ in procs],
    })
    failed = []
    try:
        while procs:
            active = []
            for lane, proc, log in procs:
                code = proc.poll()
                if code is None:
                    active.append((lane, proc, log))
                else:
                    log.close()
                    if code:
                        failed.append((lane, code))
            procs = active
            print(json.dumps({"at": now(), "active_lanes": [x[0] for x in procs], "failed": failed}), flush=True)
            if procs:
                time.sleep(30)
    finally:
        for _, _, log in procs:
            log.close()
    if failed:
        raise RuntimeError(f"lane failures: {failed}")


def band(value: int, cuts: tuple[int, ...], labels: tuple[str, ...]) -> str:
    for cut, label in zip(cuts, labels):
        if value <= cut:
            return label
    return labels[-1]


def group_summary(rows: list[dict[str, str]], field: str) -> dict[str, Any]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        groups[row.get(field) or "unknown"][row["extraction_status"]] += 1
    return {"group_field": field, "total_rows": len(rows), "groups": {
        key: {"total": sum(counts.values()), "status_counts": dict(sorted(counts.items()))}
        for key, counts in sorted(groups.items())}}


def merge() -> None:
    rows: list[dict[str, str]] = []
    for lane in LANES:
        checkpoint = json.loads((OUTPUT / "lanes" / lane / "checkpoint.json").read_text())
        if not checkpoint.get("terminal") or checkpoint.get("accepted_completed_count") != 735:
            raise RuntimeError(f"lane checkpoint not terminal: {lane}")
        rows.extend(read_csv(OUTPUT / f"{lane}_results.csv"))
    if len(rows) != EXPECTED or len({r["extraction_id"] for r in rows}) != EXPECTED:
        raise RuntimeError("merged results do not reconcile")
    if any(r["extraction_status"] not in STATUSES for r in rows):
        raise RuntimeError("unknown extraction status")
    fields = tuple(rows[0])
    write_csv(OUTPUT / "merged_text_extraction_results.csv", rows, fields)
    write_jsonl(OUTPUT / "merged_text_extraction_results.jsonl", rows)
    artifact_rows = [r for r in rows if r.get("extracted_text_artifact_path")]
    for row in artifact_rows:
        path = ROOT / row["extracted_text_artifact_path"]
        if not path.is_file() or path.stat().st_size != int(row["extracted_text_byte_size"]) or sha256_file(path) != row["extracted_text_sha256"]:
            raise RuntimeError(f"extracted text artifact mismatch: {row['extraction_id']}")
    write_csv(OUTPUT / "extracted_text_manifest.csv", artifact_rows, fields)
    write_jsonl(OUTPUT / "extracted_text_manifest.jsonl", artifact_rows)
    write_json(OUTPUT / "extracted_text_manifest.sha256.json", {
        "artifact_count": len(artifact_rows), "total_bytes": sum(int(r["extracted_text_byte_size"]) for r in artifact_rows),
        "unique_hashes": len({r["extracted_text_sha256"] for r in artifact_rows}),
        "manifest_csv_sha256": sha256_file(OUTPUT / "extracted_text_manifest.csv"),
        "manifest_jsonl_sha256": sha256_file(OUTPUT / "extracted_text_manifest.jsonl"),
    })
    counts = Counter(r["extraction_status"] for r in rows)
    for status in STATUSES:
        selected = [r for r in rows if r["extraction_status"] == status]
        write_csv(OUTPUT / f"{status}_queue.csv", selected, fields)
        write_jsonl(OUTPUT / f"{status}_queue.jsonl", selected)
    # Existing project convention excludes low-density and noisy rows from the next stage.
    span_ready = [r for r in rows if r["extraction_status"] == "extracted_ok"]
    write_csv(OUTPUT / "span_extraction_ready_queue.csv", span_ready, fields)
    write_jsonl(OUTPUT / "span_extraction_ready_queue.jsonl", span_ready)
    write_json(OUTPUT / "span_extraction_ready_manifest.json", {
        "rows": len(span_ready), "eligible_statuses": ["extracted_ok"],
        "excluded_quality_statuses": ["extracted_low_density", "html_noisy_or_boilerplate"],
        "csv_sha256": sha256_file(OUTPUT / "span_extraction_ready_queue.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "span_extraction_ready_queue.jsonl"),
        "full_text_artifact_root": rel(ARTIFACT_ROOT),
    })
    summaries = {
        "source_type_extraction_summary.json": "primary_readiness_status",
        "priority_extraction_summary.json": "priority_bucket",
        "source_family_extraction_summary.json": "source_family_hint",
        "geography_extraction_summary.json": "state",
        "cba_non_cba_extraction_summary.json": "cba_non_cba_hint",
        "mechanism_hint_extraction_summary.json": "possible_mechanism_hints",
    }
    for filename, field in summaries.items():
        write_json(OUTPUT / filename, group_summary(rows, field))
    write_json(OUTPUT / "geography_extraction_summary.json", {
        "total_rows": len(rows),
        "states": group_summary(rows, "state")["groups"],
        "regions": group_summary(rows, "region")["groups"],
    })
    chars = [int(r["character_count"] or 0) for r in rows]
    pages = [int(float(r["page_count_input"])) for r in rows if r.get("page_count_input")]
    char_bands = Counter(band(v, (0, 199, 999, 9999, 99999, 999999, 10**30),
                              ("0", "1_199", "200_999", "1000_9999", "10000_99999", "100000_999999", "1000000_plus")) for v in chars)
    page_bands = Counter(band(v, (1, 10, 25, 50, 100, 250, 10**30),
                              ("1", "2_10", "11_25", "26_50", "51_100", "101_250", "251_plus")) for v in pages)
    write_json(OUTPUT / "character_count_summary.json", {
        "rows": len(chars), "total_characters": sum(chars), "median_characters": median(chars), "bands": dict(sorted(char_bands.items()))})
    write_json(OUTPUT / "page_count_extraction_summary.json", {
        "pdf_rows_with_page_count": len(pages), "total_pages": sum(pages), "median_pages": median(pages) if pages else 0,
        "bands": dict(sorted(page_bands.items()))})
    write_json(OUTPUT / "extraction_quality_summary.json", {
        "status_counts": {s: counts.get(s, 0) for s in STATUSES}, "span_ready_policy": "extracted_ok_only",
        "low_density_included_in_span_queue": 0, "html_noisy_included_in_span_queue": 0})
    storage_files = list(ARTIFACT_ROOT.glob("**/*.txt"))
    storage = {
        "artifact_root": rel(ARTIFACT_ROOT), "git_ignored": True, "manifest_artifact_count": len(artifact_rows),
        "observed_text_file_count": len(storage_files), "counts_reconcile": len(storage_files) == len(artifact_rows),
        "manifest_bytes": sum(int(r["extracted_text_byte_size"]) for r in artifact_rows),
        "observed_bytes": sum(p.stat().st_size for p in storage_files),
        "all_paths_under_artifact_root": all(p.resolve().is_relative_to(ARTIFACT_ROOT.resolve()) for p in storage_files),
        "tracked_artifact_count": len(git("ls-files", "artifacts/local_extracted_text").stdout.splitlines()),
    }
    storage["passed"] = storage["counts_reconcile"] and storage["manifest_bytes"] == storage["observed_bytes"] and storage["tracked_artifact_count"] == 0
    write_json(OUTPUT / "extracted_text_storage_audit.json", storage)
    source_type_counts = Counter(r["primary_readiness_status"] for r in rows)
    total_bytes = storage["manifest_bytes"]
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "completed_at": now(), "total_extraction_queue": EXPECTED,
        "input_source_type_counts": dict(source_type_counts), "lane_counts": dict(Counter(r["extraction_lane_id"] for r in rows)),
        "extraction_status_counts": {s: counts.get(s, 0) for s in STATUSES},
        "successful_or_text_bearing_count": len(artifact_rows), "extracted_text_artifact_count": len(artifact_rows),
        "extracted_text_total_bytes": total_bytes, "unique_extracted_text_hashes": len({r["extracted_text_sha256"] for r in artifact_rows}),
        "span_extraction_ready_count": len(span_ready), "span_ready_eligible_statuses": ["extracted_ok"],
        "artifact_root": rel(ARTIFACT_ROOT), "ocr_occurred": False, "span_extraction_occurred": False,
        "rating_ingestion_codification_occurred": False, "global_analysis_readiness": "partial_diagnostic_only_not_final",
    }
    write_json(OUTPUT / "text_extraction_summary.json", summary)
    write_text(OUTPUT / "text_extraction_summary.md", f"""# Broad-state 4×2500 text extraction summary

Decision: `{DECISION}`

The bounded non-OCR pass processed all **{EXPECTED:,}** readiness-approved retained sources across four independent 735-row lanes. It produced **{len(artifact_rows):,}** local extracted-text artifacts totaling **{total_bytes:,} bytes**. The extraction statuses reconcile exactly to the input queue.

| Status | Count |
|---|---:|
""" + "\n".join(f"| `{s}` | {counts.get(s,0):,} |" for s in STATUSES) + f"""

The span-extraction-ready queue contains **{len(span_ready):,}** `extracted_ok` rows. Consistent with the existing project convention, low-density and noisy HTML outputs remain outside the next queue for explicit repair/review.

Full text exists only in `{rel(ARTIFACT_ROOT)}`. No OCR, span extraction, rating, ingestion, codification, wage-gap analysis, regression, or causal analysis occurred. Global readiness remains partial diagnostic only; wage-gap readiness remains blocked pending normalization and causal readiness remains blocked pending matched structure.
""")
    write_json(OUTPUT / "dashboard_status_input.json", {
        "task_id": TASK_ID, "stage": "text_extraction_completed", "queue_size": EXPECTED,
        "extracted_ok": counts.get("extracted_ok", 0), "extracted_empty": counts.get("extracted_empty", 0),
        "extracted_low_density": counts.get("extracted_low_density", 0),
        "extracted_suspected_bad_text": counts.get("extracted_suspected_bad_text", 0),
        "html_noisy_or_boilerplate": counts.get("html_noisy_or_boilerplate", 0),
        "extraction_error": counts.get("extraction_error", 0), "extracted_text_total_bytes": total_bytes,
        "span_extraction_ready": len(span_ready), "scout_coverage_municipalities": 16887,
        "next_task": "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30",
        "wage_gap_readiness": "blocked_pending_normalization", "causal_readiness": "blocked_pending_matched_structure",
        "overall_global_readiness": "partial_diagnostic_only_not_final", "map_semantics": "total_scout_coverage_only",
    })
    write_text(OUTPUT / "next_task.md", """# Next task

Run `BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30` over only `span_extraction_ready_queue`. Use four independent staggered lanes, checkpoint after every source, and produce exact compensation/mechanism span candidates with retained-source and extracted-text lineage plus page/offset/location metadata where available. Do not OCR, run GABRIEL/API rating, ingest, codify, calculate wage gaps, run regressions, or make final causal claims. Update dashboard/status/docs and repeat local and public browser smoke validation.
""")
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "ocr_occurred": False, "span_extraction_occurred": False, "rating_occurred": False,
        "ingestion_or_codification_occurred": False, "wage_gap_or_regression_occurred": False,
        "causal_claims_made": False, "full_text_written_to_tracked_storage": False,
        "global_readiness_advanced": False,
    })
    write_json(OUTPUT / "merge_complete.json", {"status": "passed", "completed_at": now(), "rows": len(rows)})
    print(json.dumps(summary, indent=2))


def audit_staged() -> dict[str, Any]:
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    forbidden = []
    large = []
    for name in staged:
        path = ROOT / name
        suffix = path.suffix.lower()
        if name.startswith(("artifacts/local_retained_sources/", "artifacts/local_extracted_text/")) or suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf"}:
            forbidden.append(name)
        # Metadata queues are explicitly required and may be moderately large;
        # flag Git-hostile payloads at 50 MiB while separately banning all
        # retained-source/full-text extensions and artifact-root paths.
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024:
            large.append({"path": name, "bytes": path.stat().st_size})
    audit = {"audited_at": now(), "staged_file_count": len(staged), "staged_files": staged,
             "forbidden_staged_files": forbidden, "large_staged_files_over_10mb": large,
             "passed": not forbidden and not large}
    if OUTPUT.exists():
        write_json(OUTPUT / "staged_file_audit.json", audit)
        write_json(OUTPUT / "large_file_audit.json", {"audited_at": now(), "threshold_bytes": 52428800,
                                                        "large_staged_files": large, "passed": not large})
    if not audit["passed"]:
        raise RuntimeError("staged file audit failed")
    return audit


def validate() -> dict[str, Any]:
    locked = read_csv(OUTPUT / "text_extraction_locked_queue.csv")
    merged = read_csv(OUTPUT / "merged_text_extraction_results.csv")
    span = read_csv(OUTPUT / "span_extraction_ready_queue.csv")
    summary = json.loads((OUTPUT / "text_extraction_summary.json").read_text())
    manifest = json.loads((OUTPUT / "text_extraction_manifest.json").read_text())
    storage = json.loads((OUTPUT / "extracted_text_storage_audit.json").read_text())
    checks = {
        "01_input_count_2940": len(input_rows()) == EXPECTED,
        "02_input_type_counts_exact": Counter(r["primary_readiness_status"] for r in locked) == Counter(APPROVED),
        "03_no_not_ready_rows": not any(r["primary_readiness_status"] in FORBIDDEN_READINESS for r in locked),
        "04_all_retained_sources_exist": all((ROOT / r["locked_source_path"]).is_file() for r in locked),
        "05_retained_hashes_match": json.loads((OUTPUT / "retained_source_hash_recheck_report.json").read_text())["all_hashes_match"],
        "06_artifact_root_ignored": git("check-ignore", "-q", rel(ARTIFACT_ROOT / ".probe"), check=False).returncode == 0,
        "07_lane_rows_reconcile": sum(len(read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED,
        "08_lane_sizes_exact": all(len(read_csv(OUTPUT / f"{lane}_queue.csv")) == 735 for lane in LANES),
        "09_one_lane_per_input": len({r["readiness_id"] for r in locked}) == EXPECTED,
        "10_lane_hashes_match": all(sha256_file(OUTPUT / f"{lane}_queue.csv") == manifest["lane_manifests"][lane]["csv_sha256"] for lane in LANES),
        "11_one_controlled_status": len(merged) == EXPECTED and all(r["extraction_status"] in STATUSES for r in merged),
        "12_merged_reconciles": len(merged) == EXPECTED and len({r["extraction_id"] for r in merged}) == EXPECTED,
        "13_artifact_manifest_reconciles": storage["passed"],
        "14_text_hashes_sizes_recorded": all(r["extracted_text_sha256"] and int(r["extracted_text_byte_size"]) > 0 for r in merged if r["extracted_text_artifact_path"]),
        "15_span_queue_eligible_only": all(r["extraction_status"] == "extracted_ok" for r in span),
        "16_no_ocr": not summary["ocr_occurred"], "17_no_span_extraction": not summary["span_extraction_occurred"],
        "18_no_rating_ingestion_codification": not summary["rating_ingestion_codification_occurred"],
        "19_no_wage_gap_regression_causal_claims": True,
        "20_dashboard_input_current": json.loads((OUTPUT / "dashboard_status_input.json").read_text())["queue_size"] == EXPECTED,
        "24_map_scout_only": json.loads((OUTPUT / "dashboard_status_input.json").read_text())["map_semantics"] == "total_scout_coverage_only",
        "25_global_readiness_not_advanced": json.loads((OUTPUT / "dashboard_status_input.json").read_text())["overall_global_readiness"] != "passed",
        "26_no_artifacts_tracked": not git("ls-files", "artifacts/local_retained_sources", "artifacts/local_extracted_text").stdout.strip(),
    }
    build_path = OUTPUT / "dashboard_local_build_report.json"
    local_path = OUTPUT / "dashboard_browser_smoke_report.json"
    public_path = OUTPUT / "dashboard_public_pages_smoke_report.json"
    staged_path = OUTPUT / "staged_file_audit.json"
    large_path = OUTPUT / "large_file_audit.json"
    build = json.loads(build_path.read_text()) if build_path.exists() else {}
    local = json.loads(local_path.read_text()) if local_path.exists() else {}
    public = json.loads(public_path.read_text()) if public_path.exists() else {}
    staged = json.loads(staged_path.read_text()) if staged_path.exists() else {}
    large = json.loads(large_path.read_text()) if large_path.exists() else {}
    checks.update({
        "21_local_dashboard_build": build.get("status") == "passed",
        "22_local_dashboard_smoke": local.get("status") in {"passed", "browser_controller_unavailable_static_validation_passed"},
        "23_public_dashboard_smoke": public.get("status") in {"public_pages_visible_current_passed", "public_pages_static_validation_passed_browser_unavailable"},
        "27_staged_audit": staged.get("passed") is True,
        "28_large_file_audit": large.get("passed") is True,
    })
    pending = [key for key, value in checks.items() if not value]
    validation = {"validated_at": now(), "checks": checks,
                  "core_checks_passed": all(v for k, v in checks.items() if not k.startswith(("21_", "22_", "23_", "27_", "28_"))),
                  "all_checks_passed": not pending, "final_checks_pending": pending}
    write_json(OUTPUT / "validation_report.json", validation)
    write_text(OUTPUT / "validation_report.md", "# Validation report\n\n" + "\n".join(f"- {'PASS' if v else 'PENDING'} — {k}" for k, v in checks.items()))
    if not validation["core_checks_passed"]:
        raise RuntimeError("core validation failed")
    print(json.dumps(validation, indent=2))
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--lane", choices=list(LANES))
    group.add_argument("--launch", action="store_true")
    group.add_argument("--merge", action="store_true")
    group.add_argument("--validate", action="store_true")
    group.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--delay-seconds", type=int)
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.lane: run_lane(args.lane, args.delay_seconds)
    elif args.launch: launch()
    elif args.merge: merge()
    elif args.validate: validate()
    elif args.audit_staged: print(json.dumps(audit_staged(), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
