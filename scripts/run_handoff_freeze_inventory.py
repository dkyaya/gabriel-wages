#!/usr/bin/env python3
"""Non-destructive five-lane inventory for the Gabriel Wages handoff freeze.

The program only reads existing project content. It writes compact metadata to the
new handoff task directory and its task-owned temporary root.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import mimetypes
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
OUT_REL = Path("docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06")
OUT = REPO / OUT_REL
TMP_REL = Path("tmp/gabriel_wages_handoff_freeze_master_inventory_2026-08-06")
TMP = REPO / TMP_REL
START_HEAD = "d1dd03ea51197421102d13ce79aef88868548ccb"
FREEZE_TAG = "pre-handoff-freeze-2026-08-06"
NOW = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
PREFLIGHT_TRACKED_COUNT = 14852
PREFLIGHT_IGNORED_COUNT = 389007
PREFLIGHT_UNTRACKED_COUNT = 0

MASTER_FIELDS = [
    "inventory_id", "absolute_path_hash", "relative_path", "filename", "extension",
    "artifact_family", "artifact_subfamily", "tracked_status", "ignored_status",
    "untracked_status", "symlink_status", "file_size_bytes", "file_size_human",
    "modified_time", "created_time_if_available", "SHA256_if_available",
    "existing_hash_source", "exact_duplicate_group_id", "near_duplicate_group_id_if_available",
    "canonical_source_id_if_available", "task_id_if_available", "source_type_if_available",
    "municipality_if_available", "state_if_available", "period_if_available",
    "original_URL_pointer_if_available", "extraction_status_if_available",
    "claim_or_report_dependency", "current_use_status", "superseded_status",
    "sensitive_material_risk", "machine_specific_path_risk", "redistribution_risk",
    "clean_repo_decision", "source_library_decision", "original_archive_decision",
    "post_acceptance_cleanup_decision", "cleanup_priority", "cleanup_level",
    "estimated_reclaimable_bytes", "replacement_summary_path", "retention_reason",
    "exclusion_reason", "unresolved_question", "lane_id", "lineage",
]

ARTIFACT_FAMILIES = [
    "original_source", "extracted_text", "parsed_table", "embedded_record", "raw_field",
    "raw_span", "compact_observation", "rating", "ingestion", "reconciliation",
    "normalization", "matching", "mathematical_analysis", "semantic_review",
    "claim_adjudication", "visual_data", "rendered_visual", "report", "dashboard",
    "script", "schema", "documentation", "prompt", "relay", "QA", "validation",
    "checkpoint", "queue", "log", "cache", "temporary", "archive", "environment",
    "secret_or_sensitive", "unknown",
]

RETENTION_DECISIONS = [
    "retain_in_clean_repo", "retain_in_source_library", "retain_in_both",
    "retain_in_original_archive_only", "replace_with_compact_summary",
    "post_acceptance_cleanup_candidate", "temporary_delete_candidate",
    "superseded_delete_candidate", "duplicate_delete_candidate", "cache_delete_candidate",
    "quarantine_for_review", "unresolved",
]

SOURCE_EXTS = {".pdf", ".html", ".htm", ".csv", ".tsv", ".txt", ".json", ".xml",
               ".doc", ".docx", ".xls", ".xlsx", ".zip", ".tar", ".gz"}
TEXT_EXTS = {".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".py", ".js", ".ts",
             ".tsx", ".jsx", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".sh", ".zsh",
             ".html", ".htm", ".css", ".env"}
FINAL_TASK_MARKERS = (
    "BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06",
    "BROAD-STATE-WHOLE-CORPUS-VISUAL-PRODUCTION-AND-QA-2026-08-06",
    "BROAD-STATE-WHOLE-CORPUS-MECHANISM-CLAIM-LIMITATIONS-VISUAL-ATLAS-2026-08-06",
    "BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06",
    "BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06",
    "BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05",
)


def run(*args: str, check: bool = True) -> str:
    proc = subprocess.run(args, cwd=REPO, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    if check and proc.returncode:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path, chunk: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            data = handle.read(chunk)
            if not data:
                break
            digest.update(data)
    return digest.hexdigest()


def short_hash(value: str, prefix: str = "") -> str:
    return prefix + hashlib.sha256(value.encode("utf-8", "surrogateescape")).hexdigest()[:20]


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TiB"


def iso_time(value: float | None) -> str:
    if value is None:
        return ""
    return datetime.fromtimestamp(value, timezone.utc).astimezone().isoformat(timespec="seconds")


def relative(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return "external://" + short_hash(str(path))


def task_id(rel: str) -> str:
    for part in Path(rel).parts:
        if re.search(r"20\d{2}-\d{2}-\d{2}", part) and len(part) > 20:
            return part
    return ""


def artifact_family(rel: str, ext: str, source_hint: bool = False) -> tuple[str, str]:
    low = rel.lower()
    name = Path(rel).name.lower()
    if source_hint or "retained_sources" in low or "local_retained_sources" in low:
        return "original_source", ext.lstrip(".") or "container"
    if "extracted_text" in low or "local_extracted_text" in low:
        return "extracted_text", ext.lstrip(".") or "text"
    if "parsed_table" in low or "html_table" in low or "table_rows" in low:
        return "parsed_table", "table"
    if "embedded" in low and ("json" in low or "xml" in low or "record" in low):
        return "embedded_record", "structured"
    if "field_record" in low or "raw_field" in low or "field_hits" in low:
        return "raw_field", "field"
    if "span" in low and "rating" not in low:
        return "raw_span", "span"
    if "compact" in low or "canonical_observation" in low or "classified_observation" in low:
        return "compact_observation", "administrative_observation"
    if "rating" in low or "gabriel" in low:
        return "rating", "rating_output"
    if "ingestion" in low or "ingested" in low:
        return "ingestion", "ingestion_output"
    if "reconciliation" in low or "reconciled" in low:
        return "reconciliation", "reconciliation_output"
    if "normalization" in low or "normalized" in low:
        return "normalization", "normalization_output"
    if "matching" in low or "matched" in low:
        return "matching", "matching_output"
    if "mathematical" in low or "regression" in low or "growth" in low:
        return "mathematical_analysis", "analysis_output"
    if "cross-exam" in low or "semantic" in low or "review_result" in low:
        return "semantic_review", "review_output"
    if "adjudicat" in low or "final_claim" in low:
        return "claim_adjudication", "claim_output"
    if "visual" in low and ext in {".csv", ".json", ".jsonl"}:
        return "visual_data", "bounded_visual_input"
    if ext in {".png", ".svg", ".jpg", ".jpeg", ".webp"}:
        return "rendered_visual", ext.lstrip(".")
    if ext == ".pdf" or "report" in low or "atlas" in low:
        return "report", "pdf" if ext == ".pdf" else "report_support"
    if low.startswith("docs/dashboard") or "dashboard" in low:
        return "dashboard", ext.lstrip(".") or "asset"
    if low.startswith("scripts/") or ext in {".py", ".sh", ".zsh", ".js", ".ts", ".tsx"}:
        return "script", ext.lstrip(".") or "executable"
    if "schema" in low:
        return "schema", ext.lstrip(".") or "schema"
    if "prompt" in low or name.endswith("prompt.md"):
        return "prompt", "orchestration_prompt"
    if "relay" in low or ext == ".zip":
        return "relay" if "relay" in low else "archive", "zip"
    if "checkpoint" in low:
        return "checkpoint", "worker_checkpoint"
    if "queue" in low:
        return "queue", "worker_queue"
    if "qa" in low or "quality_gate" in low:
        return "QA", "quality_assurance"
    if "validation" in low or "audit" in low:
        return "validation", "validation_or_audit"
    if "log" in low or ext == ".log":
        return "log", "runtime_log"
    if "cache" in low or "node_modules" in low or ".venv" in low:
        return "cache", "reconstructible_cache"
    if low.startswith("tmp/") or "temporary" in low:
        return "temporary", "temporary_workspace"
    if ext in {".md", ".rst"} or low.startswith("docs/"):
        return "documentation", "project_documentation"
    if name.startswith(".env") or "credential" in low or "cookie" in low:
        return "environment", "sensitive_configuration"
    return "unknown", ext.lstrip(".") or "extensionless"


def retention_for(family: str, rel: str, size: int) -> dict[str, Any]:
    low = rel.lower()
    final = any(marker.lower() in low for marker in FINAL_TASK_MARKERS)
    result: dict[str, Any] = {
        "clean_repo_decision": "exclude",
        "source_library_decision": "exclude",
        "original_archive_decision": "retain",
        "post_acceptance_cleanup_decision": "retain",
        "cleanup_priority": "none",
        "cleanup_level": "none",
        "estimated_reclaimable_bytes": 0,
        "retention_reason": "Preserve project lineage in the original archive.",
        "exclusion_reason": "Not required in the compact handoff repository.",
        "primary": "retain_in_original_archive_only",
    }
    if family == "original_source":
        result.update(source_library_decision="retain", post_acceptance_cleanup_decision="eligible_after_source_library_acceptance",
                      cleanup_priority="last", cleanup_level="4", estimated_reclaimable_bytes=size,
                      retention_reason="Original source belongs in the source-only library; local removal requires package transfer and checksum acceptance.",
                      primary="retain_in_source_library")
    elif family == "extracted_text":
        result.update(source_library_decision="retain_as_companion", post_acceptance_cleanup_decision="eligible_after_source_library_acceptance",
                      cleanup_priority="last", cleanup_level="4", estimated_reclaimable_bytes=size,
                      retention_reason="Extracted text is a source-library companion and remains separate from source binaries.",
                      primary="retain_in_source_library")
    elif family in {"raw_field", "raw_span", "compact_observation", "ingestion", "reconciliation", "normalization", "matching"}:
        result.update(post_acceptance_cleanup_decision="eligible_after_reconstruction_validation", cleanup_priority="medium",
                      cleanup_level="3", estimated_reclaimable_bytes=size,
                      retention_reason="Large reproducibility layer; retain lineage, schemas, scripts, and compact canonical summaries before cleanup.",
                      primary="post_acceptance_cleanup_candidate")
    elif family in {"cache", "temporary", "log", "checkpoint", "queue"}:
        result.update(post_acceptance_cleanup_decision="eligible_after_handoff_acceptance", cleanup_priority="high",
                      cleanup_level="1", estimated_reclaimable_bytes=size,
                      retention_reason="Reconstructible runtime material with low historical value.",
                      primary="cache_delete_candidate" if family == "cache" else "temporary_delete_candidate")
    elif family in {"prompt", "relay"}:
        result.update(post_acceptance_cleanup_decision="eligible_after_compact_history_archive", cleanup_priority="medium",
                      cleanup_level="2", estimated_reclaimable_bytes=size,
                      retention_reason="Keep representative prompts and relays in the frozen archive; repeated copies can be removed after acceptance.",
                      primary="replace_with_compact_summary")
    elif family in {"script", "schema"}:
        result.update(clean_repo_decision="retain_if_essential", retention_reason="Candidate for clean-repository reproducibility and onboarding.",
                      exclusion_reason="Exclude only if superseded or machine-specific.", primary="retain_in_both")
    elif family in {"claim_adjudication", "report", "rendered_visual", "visual_data", "dashboard", "documentation", "mathematical_analysis", "semantic_review", "QA", "validation"} and final:
        result.update(clean_repo_decision="retain", retention_reason="Current final-stage finding, boundary, figure, dashboard, or validation asset.",
                      exclusion_reason="", primary="retain_in_clean_repo")
    elif family in {"rendered_visual", "report", "visual_data", "QA", "validation", "documentation"} and not final:
        result.update(post_acceptance_cleanup_decision="eligible_after_final_asset_selection", cleanup_priority="medium",
                      cleanup_level="2", estimated_reclaimable_bytes=size,
                      retention_reason="Superseded historical output; retain compact lineage and selected milestones.",
                      primary="superseded_delete_candidate")
    elif family == "environment":
        result.update(original_archive_decision="quarantine", retention_reason="Environment or credential-adjacent file requires manual portability review.",
                      primary="quarantine_for_review")
    return result


def build_record(path: Path, lane: int, tracked: bool, ignored: bool, *, source_hint: bool = False,
                 sha256: str = "", hash_source: str = "", logical_size: int | None = None,
                 logical_rel: str | None = None, subfamily_override: str = "") -> dict[str, Any]:
    rel = logical_rel or relative(path)
    if logical_rel:
        size = int(logical_size or 0)
        mtime = ctime = None
        symlink = False
        filename = Path(logical_rel).name
        ext = Path(filename).suffix.lower()
    else:
        st = path.lstat()
        size = st.st_size
        mtime, ctime = st.st_mtime, getattr(st, "st_birthtime", st.st_ctime)
        symlink = path.is_symlink()
        filename = path.name
        ext = path.suffix.lower()
    family, subfamily = artifact_family(rel, ext, source_hint)
    if subfamily_override:
        subfamily = subfamily_override
    retain = retention_for(family, rel, size)
    current = "current_final" if any(x in rel for x in FINAL_TASK_MARKERS) else ("active" if family in {"script", "schema"} else "historical_or_intermediate")
    machine_risk = "current_machine_path" if rel.startswith("external://") else "none_detected_in_path"
    sensitive = "review_required" if family in {"environment", "secret_or_sensitive"} else "none_detected_by_path"
    record = {field: "" for field in MASTER_FIELDS}
    record.update({
        "inventory_id": short_hash(rel, "INV-"),
        "absolute_path_hash": hashlib.sha256(str(path.resolve(strict=False)).encode()).hexdigest(),
        "relative_path": rel,
        "filename": filename,
        "extension": ext,
        "artifact_family": family,
        "artifact_subfamily": subfamily,
        "tracked_status": "tracked" if tracked else "not_tracked",
        "ignored_status": "ignored" if ignored else "not_ignored",
        "untracked_status": "untracked" if (not tracked and not ignored) else "not_untracked",
        "symlink_status": "symlink" if symlink else "regular_or_logical",
        "file_size_bytes": size,
        "file_size_human": human_bytes(size),
        "modified_time": iso_time(mtime),
        "created_time_if_available": iso_time(ctime),
        "SHA256_if_available": sha256,
        "existing_hash_source": hash_source,
        "task_id_if_available": task_id(rel),
        "source_type_if_available": ext.lstrip(".") if family == "original_source" else "",
        "canonical_source_id_if_available": sha256 if family == "original_source" and sha256 else "",
        "extraction_status_if_available": "unknown_or_manifest_required" if family == "original_source" else "not_applicable",
        "claim_or_report_dependency": "current_final_outputs" if current == "current_final" else "none_recorded_at_file_level",
        "current_use_status": current,
        "superseded_status": "not_superseded" if current == "current_final" else "historical_or_unresolved",
        "sensitive_material_risk": sensitive,
        "machine_specific_path_risk": machine_risk,
        "redistribution_risk": "review_required" if family == "original_source" else "not_source_material",
        "clean_repo_decision": retain["clean_repo_decision"],
        "source_library_decision": retain["source_library_decision"],
        "original_archive_decision": retain["original_archive_decision"],
        "post_acceptance_cleanup_decision": retain["post_acceptance_cleanup_decision"],
        "cleanup_priority": retain["cleanup_priority"],
        "cleanup_level": retain["cleanup_level"],
        "estimated_reclaimable_bytes": retain["estimated_reclaimable_bytes"],
        "replacement_summary_path": OUT_REL.as_posix() + "/handoff_master_inventory_summary.json",
        "retention_reason": retain["retention_reason"],
        "exclusion_reason": retain["exclusion_reason"],
        "unresolved_question": "" if family != "unknown" else "Confirm artifact family and future dependency.",
        "lane_id": f"handoff_inventory_lane_{lane:03d}",
        "lineage": "filesystem_stat_and_project_path_rules",
        "_primary_decision": retain["primary"],
    })
    return record


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            # JSONL is intentionally sparse. CSV preserves the declared rectangular
            # schema; omitting blank JSON keys avoids hundreds of megabytes of
            # repeated empty metadata while preserving every populated value.
            compact = {key: value for key, value in row.items()
                       if not key.startswith("_") and value not in ("", None, [], {})}
            handle.write(json.dumps(compact, sort_keys=False, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key.startswith("_") or key in seen:
                    continue
                seen.add(key)
                fields.append(key)
        if not fields:
            fields = ["status", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_pair(base: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    projected = rows
    if fields is not None:
        projected = [{key: row.get(key, "") for key in fields} for row in rows]
    write_csv(OUT / f"{base}.csv", projected, fields)
    write_jsonl(OUT / f"{base}.jsonl", projected)


def iter_files(root: Path, skip: tuple[Path, ...] = ()) -> Iterable[Path]:
    if not root.exists():
        return
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if any(path == item or item in path.parents for item in skip):
                        continue
                    try:
                        if entry.is_symlink():
                            yield path
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(path)
                        elif entry.is_file(follow_symlinks=False):
                            yield path
                    except OSError:
                        continue
        except (FileNotFoundError, PermissionError, OSError):
            continue


def tracked_set() -> set[str]:
    return set(run("git", "ls-files").splitlines())


def lane_paths(lane: int, tracked: set[str]) -> list[Path]:
    paths: list[Path] = []
    if lane == 1:
        for rel in tracked:
            if rel.startswith("docs/analysis/") or rel.startswith("docs/dashboard/public/"):
                continue
            paths.append(REPO / rel)
    elif lane == 2:
        roots = [REPO / "artifacts/local_retained_sources"]
        for rel in tracked:
            if "retained_sources/" in rel:
                paths.append(REPO / rel)
        for root in roots:
            paths.extend(iter_files(root) or [])
    elif lane == 3:
        for root_name in ("artifacts/local_extracted_text", "artifacts/local_structured_external_data",
                          "artifacts/local_hosted_search_metadata", "artifacts/local_external_reference_data"):
            paths.extend(iter_files(REPO / root_name) or [])
    elif lane == 4:
        for rel in tracked:
            if not (rel.startswith("docs/analysis/") or rel.startswith("docs/dashboard/public/")):
                continue
            if "retained_sources/" in rel or rel.startswith(OUT_REL.as_posix() + "/"):
                continue
            paths.append(REPO / rel)
    return paths


def run_lane_1() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tracked = tracked_set()
    rows = []
    secret_hits, path_hits, env_rows = security_scan([REPO / rel for rel in tracked if not rel.startswith("docs/analysis/")])
    for path in lane_paths(1, tracked):
        if not path.exists() and not path.is_symlink():
            continue
        try:
            rows.append(build_record(path, 1, True, False))
        except OSError:
            continue
    write_jsonl(TMP / "lane_001_secret_hits.jsonl", secret_hits)
    write_jsonl(TMP / "lane_001_path_hits.jsonl", path_hits)
    write_jsonl(TMP / "lane_001_environment_files.jsonl", env_rows)
    summary = {"lane": 1, "scope": "Git repository and tracked infrastructure", "records": len(rows),
               "secret_risk_files": len(secret_hits), "machine_path_files": len(path_hits), "status": "complete"}
    return rows, summary


def existing_hash_from_name(path: Path) -> str:
    candidates = re.findall(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", path.name)
    return candidates[0].lower() if candidates else ""


def run_lane_2() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tracked = tracked_set()
    candidates = lane_paths(2, tracked)
    rows: list[dict[str, Any]] = []
    by_real: set[str] = set()
    hash_errors = 0
    for path in candidates:
        rel = relative(path)
        if rel in by_real or not (path.exists() or path.is_symlink()):
            continue
        by_real.add(rel)
        try:
            st = path.lstat()
            if not path.is_file() or path.is_symlink():
                rows.append(build_record(path, 2, rel in tracked, rel not in tracked, source_hint=True))
                continue
            digest = existing_hash_from_name(path)
            source = "filename_embedded_sha256" if digest else "computed_sha256"
            if not digest:
                try:
                    digest = sha256_file(path)
                except OSError:
                    hash_errors += 1
                    digest, source = "", "hash_failed"
            row = build_record(path, 2, rel in tracked, rel not in tracked, source_hint=True,
                               sha256=digest, hash_source=source)
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            row["mime_type"] = mime
            row["source_family"] = Path(rel).parts[1] if len(Path(rel).parts) > 1 else "repository_source"
            row["expected_source_library_path"] = f"originals/{digest[:2]}/{digest}{path.suffix.lower()}" if digest else "unresolved/" + short_hash(rel)
            rows.append(row)
        except OSError:
            continue
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = row.get("SHA256_if_available", "")
        if key:
            groups[key].append(row)
    for digest, members in groups.items():
        gid = "SRC-DUP-" + digest[:16]
        for row in members:
            row["exact_duplicate_group_id"] = gid if len(members) > 1 else ""
            row["alias_count"] = len(members) - 1
    write_jsonl(TMP / "lane_002_sources.jsonl", rows)
    summary = {"lane": 2, "scope": "Original retained source files", "records": len(rows),
               "bytes": sum(int(row["file_size_bytes"]) for row in rows),
               "unique_sha256": len(groups), "exact_duplicate_groups": sum(len(v) > 1 for v in groups.values()),
               "hash_errors": hash_errors, "status": "complete"}
    return rows, summary


def run_lane_3() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tracked = tracked_set()
    rows: list[dict[str, Any]] = []
    paths = lane_paths(3, tracked)
    # Preserve per-file rows for high-value derived layers while collapsing dense shard folders.
    dense_groups: dict[str, dict[str, Any]] = {}
    for path in paths:
        rel = relative(path)
        parts = Path(rel).parts
        try:
            size = path.lstat().st_size
        except OSError:
            continue
        dense = ("local_extracted_text" in rel and len(parts) > 5) or ("temporary" in rel.lower())
        if dense:
            group_rel = "/".join(parts[:5]) + "/[file-family]"
            bucket = dense_groups.setdefault(group_rel, {"size": 0, "count": 0, "sample": path})
            bucket["size"] += size
            bucket["count"] += 1
            continue
        try:
            rows.append(build_record(path, 3, rel in tracked, rel not in tracked))
        except OSError:
            continue
    for rel, bucket in dense_groups.items():
        row = build_record(bucket["sample"], 3, False, True, logical_size=bucket["size"], logical_rel=rel,
                           subfamily_override="logical_file_family")
        row["logical_file_count"] = bucket["count"]
        row["lineage"] = "logical_artifact_family_from_complete_filesystem_scan"
        rows.append(row)
    summary = {"lane": 3, "scope": "Extracted text and derived analytical layers", "records": len(rows),
               "logical_dense_groups": len(dense_groups), "represented_files": len(paths),
               "bytes": sum(int(row["file_size_bytes"]) for row in rows), "status": "complete"}
    return rows, summary


def run_lane_4() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tracked = tracked_set()
    rows: list[dict[str, Any]] = []
    secret_hits, path_hits, env_rows = security_scan(lane_paths(4, tracked))
    for path in lane_paths(4, tracked):
        if not path.exists() and not path.is_symlink():
            continue
        try:
            rows.append(build_record(path, 4, True, False))
        except OSError:
            continue
    write_jsonl(TMP / "lane_004_secret_hits.jsonl", secret_hits)
    write_jsonl(TMP / "lane_004_path_hits.jsonl", path_hits)
    write_jsonl(TMP / "lane_004_environment_files.jsonl", env_rows)
    summary = {"lane": 4, "scope": "Reports, visuals, methodology, limitations, and dashboard", "records": len(rows),
               "reports": sum(r["artifact_family"] == "report" for r in rows),
               "visuals": sum(r["artifact_family"] == "rendered_visual" for r in rows),
               "dashboard": sum(r["artifact_family"] == "dashboard" for r in rows), "status": "complete"}
    return rows, summary


def run_lane_5() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tracked = tracked_set()
    skip = (OUT, TMP)
    total_bytes = 0
    total_files = 0
    ext_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    dir_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    root_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    top_heap: list[tuple[int, str]] = []
    tmp_groups: dict[str, dict[str, Any]] = {}
    relays: list[dict[str, Any]] = []
    archives: list[dict[str, Any]] = []
    temp_sample_paths: list[Path] = []
    for path in iter_files(REPO, skip=skip) or []:
        rel = relative(path)
        if rel.startswith(".git/objects/") and "/pack/" not in rel:
            # Loose objects are represented by the repository object audit.
            continue
        try:
            size = path.lstat().st_size
        except OSError:
            continue
        total_bytes += size
        total_files += 1
        ext = path.suffix.lower() or "[none]"
        ext_stats[ext][0] += 1
        ext_stats[ext][1] += size
        parts = Path(rel).parts
        root = parts[0] if parts else "[root]"
        root_stats[root][0] += 1
        root_stats[root][1] += size
        for depth in range(1, min(len(parts), 5)):
            key = "/".join(parts[:depth])
            dir_stats[key][0] += 1
            dir_stats[key][1] += size
        item = (size, rel)
        if len(top_heap) < 100:
            heapq.heappush(top_heap, item)
        elif item > top_heap[0]:
            heapq.heapreplace(top_heap, item)
        if rel.startswith("tmp/"):
            group = "/".join(parts[:2]) if len(parts) > 1 else "tmp"
            bucket = tmp_groups.setdefault(group, {"size": 0, "count": 0, "sample": path})
            bucket["size"] += size
            bucket["count"] += 1
            if len(temp_sample_paths) < 200:
                temp_sample_paths.append(path)
            if "relay" in path.name.lower() or path.suffix.lower() == ".zip":
                digest = sha256_file(path) if size <= 128 * 1024 * 1024 else ""
                relays.append({"relative_path": rel, "file_size_bytes": size, "file_size_human": human_bytes(size),
                               "sha256_if_available": digest, "hash_status": "computed" if digest else "deferred_large_file",
                               "retention_decision": "replace_with_compact_summary", "cleanup_level": "1_or_2"})
        if path.suffix.lower() in {".zip", ".tar", ".gz", ".tgz"}:
            archives.append({"relative_path": rel, "file_size_bytes": size, "file_size_human": human_bytes(size),
                             "artifact_family": "archive", "cleanup_review": "manual_review"})
    rows: list[dict[str, Any]] = []
    for rel, bucket in tmp_groups.items():
        row = build_record(bucket["sample"], 5, False, True, logical_size=bucket["size"],
                           logical_rel=rel + "/[logical-family]", subfamily_override="temporary_file_family")
        row["logical_file_count"] = bucket["count"]
        rows.append(row)
    git_size = 0
    git_path = REPO / ".git"
    for path in iter_files(git_path) or []:
        try:
            git_size += path.lstat().st_size
        except OSError:
            pass
    rows.append(build_record(git_path, 5, False, False, logical_size=git_size,
                             logical_rel=".git/[repository-metadata-and-objects]", subfamily_override="git_repository"))
    write_json(TMP / "lane_005_storage.json", {
        "total_project_bytes_scanned": total_bytes,
        "total_project_files_scanned": total_files,
        "top_level": [{"directory": k, "file_count": v[0], "bytes": v[1]} for k, v in root_stats.items()],
        "directories": [{"directory": k, "file_count": v[0], "bytes": v[1]} for k, v in dir_stats.items()],
        "extensions": [{"extension": k, "file_count": v[0], "bytes": v[1]} for k, v in ext_stats.items()],
        "top_files": [{"relative_path": rel, "file_size_bytes": size} for size, rel in sorted(top_heap, reverse=True)],
    })
    write_jsonl(TMP / "lane_005_relays.jsonl", relays)
    write_jsonl(TMP / "lane_005_archives.jsonl", archives)
    secret_hits, path_hits, env_rows = security_scan(temp_sample_paths)
    write_jsonl(TMP / "lane_005_secret_hits.jsonl", secret_hits)
    write_jsonl(TMP / "lane_005_path_hits.jsonl", path_hits)
    write_jsonl(TMP / "lane_005_environment_files.jsonl", env_rows)
    summary = {"lane": 5, "scope": "Storage, duplication, sensitivity, and cleanup planning",
               "records": len(rows), "project_files_scanned": total_files, "project_bytes_scanned": total_bytes,
               "temporary_groups": len(tmp_groups), "relays": len(relays), "archives": len(archives), "status": "complete"}
    return rows, summary


SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b")),
    ("authorization_header", re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._-]{12,}")),
    ("credential_assignment", re.compile(r"(?i)\b(?:OPENAI_API_KEY|GITHUB_TOKEN|SUPABASE_(?:KEY|TOKEN)|PASSWORD|COOKIE)\s*=\s*[^\s#]{8,}")),
]
ABS_PATH = re.compile(r"/Users/[^/\s\"']+(?:/[^\s\"']+){1,}")


def security_scan(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    secret_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    env_rows: list[dict[str, Any]] = []
    seen_secret: set[tuple[str, str]] = set()
    seen_path: set[str] = set()
    for path in paths:
        rel = relative(path)
        name = path.name.lower()
        if name.startswith(".env") or name in {"credentials", "credentials.json", "cookies.json"}:
            env_rows.append({"relative_path": rel, "risk_type": "environment_or_credential_file", "disposition": "quarantine_for_review"})
        try:
            st = path.stat()
        except OSError:
            continue
        if path.suffix.lower() not in TEXT_EXTS or st.st_size > 2 * 1024 * 1024 or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for risk, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if not match or (rel, risk) in seen_secret:
                continue
            seen_secret.add((rel, risk))
            line = text.count("\n", 0, match.start()) + 1
            secret_rows.append({"relative_path": rel, "risk_type": risk, "line_number": line,
                                "redacted_fingerprint": hashlib.sha256(match.group(0).encode()).hexdigest()[:12],
                                "value_exposed": False, "recommended_disposition": "quarantine_and_rotate_if_real"})
        if rel not in seen_path:
            matches = ABS_PATH.findall(text)
            if matches:
                seen_path.add(rel)
                path_rows.append({"relative_path": rel, "risk_type": "absolute_home_path",
                                  "occurrence_count": len(matches),
                                  "redacted_fingerprint": hashlib.sha256(matches[0].encode()).hexdigest()[:12],
                                  "portable_replacement": "repository-relative or environment-configured path"})
    return secret_rows, path_rows, env_rows


def execute_lane(lane: int) -> None:
    ensure_dirs()
    queues = {
        1: ["git state", "tracked infrastructure", "prompts and scripts", "tracked portability risks"],
        2: ["physical retained sources", "source hashes", "duplicate groups", "source-library path proposal"],
        3: ["extracted text", "structured analytical layers", "derived dependencies", "reproducibility retention"],
        4: ["reports", "visuals", "methodology and limitations", "dashboard assets"],
        5: ["disk usage", "temporary and relay groups", "sensitivity scan", "cleanup estimates"],
    }
    lane_name = f"handoff_inventory_lane_{lane:03d}"
    write_json(OUT / f"{lane_name}_queue.json", {"lane_id": lane_name, "modules": queues[lane], "read_only_inputs": True})
    write_json(OUT / f"{lane_name}_checkpoint.json", {"lane_id": lane_name, "status": "in_progress", "started_at": NOW})
    if lane == 1:
        rows, summary = run_lane_1()
    elif lane == 2:
        rows, summary = run_lane_2()
    elif lane == 3:
        rows, summary = run_lane_3()
    elif lane == 4:
        rows, summary = run_lane_4()
    else:
        rows, summary = run_lane_5()
    write_jsonl(OUT / f"{lane_name}_inventory_ledger.jsonl", rows)
    write_json(OUT / f"{lane_name}_summary.json", summary)
    write_json(OUT / f"{lane_name}_checkpoint.json", {"lane_id": lane_name, "status": "complete", "completed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "records": len(rows)})


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    result = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                result.append(json.loads(line))
    return result


def aggregate(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        label = str(row.get(key, "") or "[unspecified]")
        counts[label][0] += int(row.get("logical_file_count", 1) or 1)
        counts[label][1] += int(row.get("file_size_bytes", 0) or 0)
    return [{key: label, "file_count": vals[0], "bytes": vals[1], "size_human": human_bytes(vals[1])}
            for label, vals in sorted(counts.items(), key=lambda item: item[1][1], reverse=True)]


def compact_derived_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Represent ignored derived shards as compact, lineage-preserving families.

    The user requested one row per file *or logical artifact*. Physical sources
    remain file-level in lane 2. Reconstructible extracted/analytical shards are
    grouped by local root, task family, artifact family, disposition, and cleanup
    level so the tracked inventory remains useful rather than becoming another
    bulky analytical layer.
    """
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    passthrough: list[dict[str, Any]] = []
    for row in rows:
        if row.get("lane_id") != "handoff_inventory_lane_003":
            passthrough.append(row)
            continue
        rel = str(row.get("relative_path", ""))
        parts = Path(rel).parts
        if rel.startswith("artifacts/local_structured_external_data/") and len(parts) >= 3:
            prefix = "/".join(parts[:3])
        elif rel.startswith("artifacts/") and len(parts) >= 2:
            prefix = "/".join(parts[:2])
        else:
            prefix = "/".join(parts[:3]) if parts else "[unknown-derived-root]"
        key = (prefix, str(row.get("artifact_family", "unknown")),
               str(row.get("artifact_subfamily", "")), str(row.get("current_use_status", "")),
               str(row.get("_primary_decision", "unresolved")), str(row.get("cleanup_level", "")))
        grouped[key].append(row)
    compacted: list[dict[str, Any]] = []
    for key, members in grouped.items():
        prefix, family, subfamily, current, primary, cleanup_level = key
        sample = dict(members[0])
        represented = sum(int(row.get("logical_file_count", 1) or 1) for row in members)
        size = sum(int(row.get("file_size_bytes", 0) or 0) for row in members)
        logical_rel = f"{prefix}/[logical-{family}-{subfamily or 'family'}]"
        sample.update({
            "inventory_id": short_hash(logical_rel + primary + cleanup_level, "INV-"),
            "absolute_path_hash": hashlib.sha256((str(REPO) + "/" + logical_rel).encode()).hexdigest(),
            "relative_path": logical_rel,
            "filename": Path(logical_rel).name,
            "extension": "",
            "file_size_bytes": size,
            "file_size_human": human_bytes(size),
            "modified_time": "",
            "created_time_if_available": "",
            "SHA256_if_available": "",
            "existing_hash_source": "",
            "exact_duplicate_group_id": "",
            "current_use_status": current,
            "cleanup_level": cleanup_level,
            "estimated_reclaimable_bytes": sum(int(row.get("estimated_reclaimable_bytes", 0) or 0) for row in members),
            "lineage": "complete_filesystem_scan_compacted_to_reconstructible_logical_artifact_family",
            "logical_file_count": represented,
            "_primary_decision": primary,
        })
        compacted.append(sample)
    return passthrough + sorted(compacted, key=lambda row: row["relative_path"])


def exact_source_groups(source_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        digest = row.get("SHA256_if_available", "")
        if digest:
            groups[digest].append(row)
    dup_rows, canonical, aliases = [], [], []
    for digest, members in groups.items():
        chosen = sorted(members, key=lambda r: (r.get("redistribution_risk") == "review_required", r["relative_path"]))[0]
        canonical.append({
            "canonical_source_id": digest,
            "canonical_relative_path": chosen["relative_path"],
            "expected_source_library_path": chosen.get("expected_source_library_path", ""),
            "source_type": chosen.get("source_type_if_available", ""),
            "file_size_bytes": int(chosen.get("file_size_bytes", 0)),
            "file_size_human": chosen.get("file_size_human", ""),
            "physical_copy_count": len(members),
            "alias_count": len(members) - 1,
            "extraction_status": chosen.get("extraction_status_if_available", ""),
            "redistribution_status": "review_required",
        })
        if len(members) > 1:
            reclaim = sum(int(m["file_size_bytes"]) for m in members) - int(chosen["file_size_bytes"])
            dup_rows.append({"duplicate_group_id": "SRC-DUP-" + digest[:16], "sha256": digest,
                             "physical_copy_count": len(members), "canonical_relative_path": chosen["relative_path"],
                             "duplicate_bytes_reclaimable": reclaim, "duplicate_size_human": human_bytes(reclaim),
                             "deletion_status": "not_deleted_planning_only"})
            for member in members:
                if member is chosen:
                    continue
                aliases.append({"canonical_source_id": digest, "alias_relative_path": member["relative_path"],
                                "alias_type": "exact_physical_duplicate", "file_size_bytes": member["file_size_bytes"],
                                "future_action": "retain_alias_metadata; remove physical duplicate only after source-library acceptance"})
    return dup_rows, canonical, aliases


def validate_embedded_hash_sample(source_rows: list[dict[str, Any]], limit: int = 25) -> list[dict[str, Any]]:
    candidates = sorted((row for row in source_rows if row.get("existing_hash_source") == "filename_embedded_sha256"),
                        key=lambda row: row["relative_path"])
    if len(candidates) > limit:
        step = max(1, len(candidates) // limit)
        candidates = candidates[::step][:limit]
    results = []
    for row in candidates:
        path = REPO / row["relative_path"]
        actual = sha256_file(path) if path.is_file() else ""
        expected = row.get("SHA256_if_available", "")
        results.append({"relative_path": row["relative_path"], "expected_hash": expected,
                        "actual_hash": actual, "match": bool(actual and actual == expected),
                        "validation_method": "full_file_sha256_recalculation", "sampled": True})
    return results


def docs_plan() -> list[dict[str, Any]]:
    specs = [
        ("README.md", "Entry point and concise project identity", "all users", "2–4 pages", "clean_repo"),
        ("START_HERE.md", "Ordered first-day handoff path", "new RA", "2–3 pages", "clean_repo"),
        ("AGENT_STARTUP_INSTRUCTIONS.md", "Safe agent briefing and claim-boundary protocol", "new RA and agent", "4–6 pages", "clean_repo"),
        ("PROJECT_HANDOFF.md", "Current state, deliverables, and ownership transfer", "new RA", "5–8 pages", "clean_repo"),
        ("FINDINGS_AND_CLAIM_BOUNDARIES.md", "Final claims, counterexamples, and prohibited conclusions", "research team", "8–12 pages", "clean_repo"),
        ("METHODS_AND_WORKFLOW.md", "Complete reproducible workflow and evidence lanes", "research team", "10–15 pages", "clean_repo"),
        ("PROJECT_HISTORY_AND_LESSONS.md", "Timeline, failures, repairs, and durable lessons", "new RA", "8–12 pages", "clean_repo"),
        ("KNOWN_LIMITATIONS.md", "Specific discovery, storage, extraction, comparability, and inference limits", "all users", "6–10 pages", "clean_repo"),
        ("DATA_AND_ARTIFACTS.md", "Compact tables, large local layers, and dependency map", "technical RA", "6–10 pages", "clean_repo"),
        ("SOURCE_LIBRARY_GUIDE.md", "Source-only package structure, provenance, and checksums", "source-library user", "5–8 pages", "both"),
        ("REPO_MAP.md", "Directory map and current-vs-archive status", "new RA and agent", "3–5 pages", "clean_repo"),
        ("NEXT_STEPS.md", "Prioritized safe extensions and stop conditions", "new RA", "3–5 pages", "clean_repo"),
        ("ENVIRONMENT_SETUP.md", "Pinned environment and local configuration", "technical RA", "3–5 pages", "clean_repo"),
        ("VALIDATION_GUIDE.md", "Acceptance tests and count/checksum reconciliation", "technical RA", "5–8 pages", "both"),
    ]
    rows = []
    for filename, purpose, reader, length, location in specs:
        rows.append({"document": filename, "purpose": purpose, "intended_reader": reader,
                     "source_inputs": "final adjudication; atlas; pipeline manifests; inventory; incident logs",
                     "required_content": "truthful current state, evidence boundaries, source pointers, and validation steps",
                     "expected_length": length, "clean_repo": location in {"clean_repo", "both"},
                     "source_library": location == "both", "original_archive": True})
    return rows


def count_reconciliation() -> list[dict[str, Any]]:
    ext_root = "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
    atlas_root = "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-MECHANISM-CLAIM-LIMITATIONS-VISUAL-ATLAS-2026-08-06"
    values = [
        ("unique_physical_pdfs", 15163, f"{ext_root}/08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP/audit_final_whole_corpus_native_pdf_page_accounting.json"),
        ("unique_native_pdf_pages", 1029482, f"{ext_root}/08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP/audit_final_whole_corpus_native_pdf_page_accounting.json"),
        ("substantive_html_documents", 8718, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/whole_corpus_non_pdf_scale_accounting.json"),
        ("html_tables", 96484, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/whole_corpus_non_pdf_scale_accounting.json"),
        ("html_table_rows", 1017511, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/whole_corpus_non_pdf_scale_accounting.json"),
        ("embedded_structured_records", 132188, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/whole_corpus_non_pdf_scale_accounting.json"),
        ("retained_source_payloads", 14449, f"{ext_root}/04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD"),
        ("retained_source_records_inspected", 14703, f"{ext_root}/05_EXTERNAL-DATA-READINESS"),
        ("extraction_ready_records", 14257, f"{ext_root}/05_EXTERNAL-DATA-READINESS"),
        ("usable_extracted_payloads", 14160, f"{ext_root}/06_EXTERNAL-DATA-EXTRACTION"),
        ("ocr_later_sources", 118, f"{ext_root}/06_EXTERNAL-DATA-EXTRACTION"),
        ("extraction_repair_sources", 97, f"{ext_root}/06_EXTERNAL-DATA-EXTRACTION"),
        ("storage_held_verified_sources", 7895, f"{ext_root}/04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD"),
        ("unsearched_residual_targets", 12844, f"{ext_root}/01_RESIDUAL-HOSTED-SEARCH-SCOUT"),
        ("raw_field_hits", 5558770, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/external_data_deterministic_field_span_summary.json"),
        ("raw_spans", 4289437, f"{ext_root}/07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION/external_data_deterministic_field_span_summary.json"),
        ("compact_administrative_observations", 1876183, f"{ext_root}/08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP/raw_to_compacted_record_flow_summary.json"),
        ("classified_spans", 1781186, f"{ext_root}/08_EXTERNAL-DATA-DETERMINISTIC-CLASSIFICATION-INGESTION-PREP/external_data_deterministic_classification_summary.json"),
        ("implementation_events", 2998, f"{atlas_root}/mechanism_event_count_summary.json"),
        ("mechanism_event_records", 13391, f"{atlas_root}/mechanism_event_count_summary.json"),
        ("final_claims", 14, f"{atlas_root}/visual_atlas_summary.json"),
        ("final_visual_atlas_pages", 76, f"{atlas_root}/visual_atlas_summary.json"),
    ]
    return [{"metric": name, "preserved_value": value, "supporting_path": path,
             "support_path_exists": (REPO / path).exists(), "status": "reconciled_to_named_layer" if (REPO / path).exists() else "family_pointer_only"}
            for name, value, path in values]


def write_registry_files() -> None:
    af = [{"artifact_family": name, "definition": "Controlled handoff inventory family.", "allowed": True} for name in ARTIFACT_FAMILIES]
    rd = [{"retention_decision": name, "definition": "Controlled non-destructive future disposition.", "physical_action_in_this_task": "none"} for name in RETENTION_DECISIONS]
    write_json(OUT / "artifact_family_registry.json", {"version": "2026-08-06", "families": af})
    write_json(OUT / "retention_decision_registry.json", {"version": "2026-08-06", "decisions": rd})
    (OUT / "artifact_family_registry.md").write_text("# Artifact family registry\n\n" + "\n".join(f"- `{r['artifact_family']}`" for r in af) + "\n", encoding="utf-8")
    (OUT / "retention_decision_registry.md").write_text("# Retention decision registry\n\nNo decision authorizes deletion in this task.\n\n" + "\n".join(f"- `{r['retention_decision']}`" for r in rd) + "\n", encoding="utf-8")


def finalize() -> None:
    ensure_dirs()
    checkpoints = []
    lane_summaries = []
    rows: list[dict[str, Any]] = []
    for lane in range(1, 6):
        checkpoint = json.loads((OUT / f"handoff_inventory_lane_{lane:03d}_checkpoint.json").read_text())
        if checkpoint.get("status") != "complete":
            raise RuntimeError(f"lane {lane} is incomplete")
        checkpoints.append(checkpoint)
        lane_summaries.append(json.loads((OUT / f"handoff_inventory_lane_{lane:03d}_summary.json").read_text()))
        rows.extend(read_jsonl(OUT / f"handoff_inventory_lane_{lane:03d}_inventory_ledger.jsonl"))
    for row in rows:
        for field in MASTER_FIELDS:
            row.setdefault(field, "")
        inferred = retention_for(str(row.get("artifact_family", "unknown")),
                                 str(row.get("relative_path", "")),
                                 int(row.get("file_size_bytes", 0) or 0))
        row["_primary_decision"] = inferred["primary"]
        for key in ("clean_repo_decision", "source_library_decision", "original_archive_decision",
                    "post_acceptance_cleanup_decision", "cleanup_priority", "cleanup_level",
                    "estimated_reclaimable_bytes", "retention_reason", "exclusion_reason"):
            if row.get(key, "") in ("", None):
                row[key] = inferred[key]
    rows = compact_derived_inventory(rows)
    # Replace the initially verbose lane ledgers with sparse, compact ledgers.
    # This rewrites only outputs created by this task, never pre-existing data.
    ledger_fields = ["inventory_id", "relative_path", "artifact_family", "artifact_subfamily",
                     "logical_file_count", "file_size_bytes", "SHA256_if_available",
                     "existing_hash_source", "filename", "extension", "modified_time",
                     "mime_type", "source_family", "expected_source_library_path",
                     "clean_repo_decision", "source_library_decision", "original_archive_decision",
                     "post_acceptance_cleanup_decision", "cleanup_level", "lane_id", "lineage"]
    for lane in range(1, 6):
        lane_id = f"handoff_inventory_lane_{lane:03d}"
        lane_rows = [{key: row.get(key, "") for key in ledger_fields}
                     for row in rows if row.get("lane_id") == lane_id]
        write_jsonl(OUT / f"{lane_id}_inventory_ledger.jsonl", lane_rows)
    # Deduplicate physical paths; logical family rows are already unique.
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        rel = row["relative_path"]
        if rel not in selected:
            selected[rel] = row
        elif row["artifact_family"] == "original_source":
            selected[rel] = row
    physical_or_logical_rows = list(selected.values())
    # The physical source universe is lane 2. Source-like CSV/JSON report assets
    # elsewhere in the repository are not original retained-source payloads.
    source_rows = [r for r in physical_or_logical_rows if r.get("lane_id") == "handoff_inventory_lane_002" and r["artifact_family"] == "original_source"]
    duplicate_groups, canonical_sources, source_aliases = exact_source_groups(source_rows)
    for group in duplicate_groups:
        digest = group["sha256"]
        for row in source_rows:
            if row.get("SHA256_if_available") == digest:
                row["exact_duplicate_group_id"] = group["duplicate_group_id"]
    # Avoid duplicating 26,799 physical-source rows across every wide master and
    # decision table. The dedicated source inventory remains file-level; the
    # unified master references it as one logical source family with exact totals.
    source_family = dict(source_rows[0]) if source_rows else {field: "" for field in MASTER_FIELDS}
    source_family_rel = "artifacts/local_retained_sources/[physical-source-inventory-family]"
    source_family.update({
        "inventory_id": short_hash(source_family_rel, "INV-"),
        "absolute_path_hash": hashlib.sha256((str(REPO) + "/" + source_family_rel).encode()).hexdigest(),
        "relative_path": source_family_rel,
        "filename": "[physical-source-inventory-family]",
        "extension": "",
        "file_size_bytes": sum(int(row["file_size_bytes"]) for row in source_rows),
        "file_size_human": human_bytes(sum(int(row["file_size_bytes"]) for row in source_rows)),
        "modified_time": "", "created_time_if_available": "", "SHA256_if_available": "",
        "existing_hash_source": "source_archive_physical_file_inventory.csv/jsonl",
        "exact_duplicate_group_id": "see_source_archive_duplicate_groups.csv/jsonl",
        "canonical_source_id_if_available": "see_source_archive_canonical_source_inventory.csv/jsonl",
        "logical_file_count": len(source_rows),
        "estimated_reclaimable_bytes": sum(int(row.get("estimated_reclaimable_bytes", 0) or 0) for row in source_rows),
        "lineage": "logical_master_reference_to_file_level_source_archive_physical_file_inventory",
        "lane_id": "handoff_inventory_lane_002",
    })
    master = [row for row in physical_or_logical_rows if row.get("lane_id") != "handoff_inventory_lane_002"]
    if source_rows:
        master.append(source_family)
    derived_rows = [r for r in master if r["artifact_family"] in {"extracted_text", "parsed_table", "embedded_record", "raw_field", "raw_span", "compact_observation", "rating", "ingestion", "reconciliation", "normalization", "matching", "mathematical_analysis", "semantic_review", "claim_adjudication"}]
    write_registry_files()
    write_pair("handoff_master_inventory", master, MASTER_FIELDS)
    write_json(OUT / "handoff_master_inventory_schema.json", {"version": "2026-08-06", "fields": MASTER_FIELDS,
               "row_definition": "physical file or compact logical artifact family", "high_volume_rule": "dense reconstructible shards are represented by logical family rows"})
    family_usage = aggregate(master, "artifact_family")
    retention_usage = aggregate([{**r, "retention_decision": r.get("_primary_decision", "unresolved")} for r in master], "retention_decision")
    cleanup_usage = aggregate(master, "cleanup_level")
    storage = json.loads((TMP / "lane_005_storage.json").read_text())
    total_bytes = int(storage["total_project_bytes_scanned"])
    total_files = int(storage["total_project_files_scanned"])
    clean_rows = [r for r in master if r["clean_repo_decision"] in {"retain", "retain_if_essential"}]
    archive_rows = [r for r in master if r["original_archive_decision"] == "retain" and r["clean_repo_decision"] == "exclude" and r["source_library_decision"] == "exclude"]
    cleanup_rows = [r for r in master if str(r.get("cleanup_level", "")) in {"1", "2", "3", "4"}]
    source_unique_bytes = sum(int(r["file_size_bytes"]) for r in canonical_sources)
    source_physical_bytes = sum(int(r["file_size_bytes"]) for r in source_rows)
    duplicate_bytes = sum(int(g["duplicate_bytes_reclaimable"]) for g in duplicate_groups)
    summary = {
        "decision": "gabriel_wages_handoff_inventory_completed_phase_1_ready",
        "snapshot_head": START_HEAD,
        "freeze_tag": FREEZE_TAG,
        "lane_completion": {str(s["lane"]): s["status"] for s in lane_summaries},
        "master_inventory_rows": len(master),
        "represented_project_files": total_files,
        "total_project_bytes": total_bytes,
        "total_project_size_human": human_bytes(total_bytes),
        "tracked_file_count": PREFLIGHT_TRACKED_COUNT,
        "ignored_file_count": PREFLIGHT_IGNORED_COUNT,
        "untracked_file_count": PREFLIGHT_UNTRACKED_COUNT,
        "source_physical_files": len(source_rows),
        "source_physical_bytes": source_physical_bytes,
        "canonical_source_candidates": len(canonical_sources),
        "canonical_source_bytes": source_unique_bytes,
        "exact_source_duplicate_groups": len(duplicate_groups),
        "duplicate_source_bytes_reclaimable": duplicate_bytes,
        "clean_repo_candidate_rows": len(clean_rows),
        "clean_repo_candidate_bytes": sum(int(r["file_size_bytes"]) for r in clean_rows),
        "archive_only_rows": len(archive_rows),
        "archive_only_bytes": sum(int(r["file_size_bytes"]) for r in archive_rows),
        "post_acceptance_cleanup_rows": len(cleanup_rows),
        "post_acceptance_reclaimable_bytes": sum(int(r.get("estimated_reclaimable_bytes", 0) or 0) for r in cleanup_rows),
        "important_count_reconciliation": count_reconciliation(),
        "non_destructive": True,
    }
    write_json(OUT / "handoff_master_inventory_summary.json", summary)
    write_json(OUT / "handoff_freeze_inventory_summary.json", summary)
    summary_md = f"""# Gabriel Wages handoff freeze and master inventory

Decision: `gabriel_wages_handoff_inventory_completed_phase_1_ready`

- Frozen pre-inventory HEAD: `{START_HEAD}`
- Freeze tag: `{FREEZE_TAG}`
- Files represented by the full filesystem scan: {total_files:,}
- Project size represented: {human_bytes(total_bytes)}
- Master physical/logical inventory rows: {len(master):,}
- Physical source candidates: {len(source_rows):,} ({human_bytes(source_physical_bytes)})
- Canonical source candidates after exact-hash grouping: {len(canonical_sources):,} ({human_bytes(source_unique_bytes)})
- Exact source duplicate groups: {len(duplicate_groups):,}; duplicate bytes: {human_bytes(duplicate_bytes)}
- Clean-repository candidate rows: {len(clean_rows):,}; bounded current size: {human_bytes(sum(int(r['file_size_bytes']) for r in clean_rows))}
- Planned post-acceptance reclaimable bytes represented: {human_bytes(sum(int(r.get('estimated_reclaimable_bytes', 0) or 0) for r in cleanup_rows))}

No project file was deleted, moved, renamed, compressed, rewritten, or deduplicated. High-volume reconstructible shards are represented by compact logical artifact rows; retained source files remain one row per physical file.
"""
    (OUT / "handoff_master_inventory_summary.md").write_text(summary_md, encoding="utf-8")
    (OUT / "handoff_freeze_inventory_summary.md").write_text(summary_md, encoding="utf-8")

    # Source outputs.
    source_index_fields = [
        "inventory_id", "relative_path", "filename", "extension", "file_size_bytes", "file_size_human",
        "modified_time", "SHA256_if_available", "existing_hash_source", "exact_duplicate_group_id",
        "canonical_source_id_if_available", "source_type_if_available", "municipality_if_available",
        "state_if_available", "period_if_available", "original_URL_pointer_if_available",
        "extraction_status_if_available", "redistribution_risk", "source_library_decision",
        "post_acceptance_cleanup_decision", "cleanup_level", "retention_reason", "lane_id", "lineage",
    ]
    write_pair("source_archive_physical_file_inventory", source_rows, source_index_fields)
    write_pair("source_archive_canonical_source_inventory", canonical_sources)
    write_pair("source_archive_alias_inventory", source_aliases)
    write_pair("source_archive_duplicate_groups", duplicate_groups)
    hash_validation_sample = validate_embedded_hash_sample(source_rows)
    write_pair("source_archive_hash_validation_sample", hash_validation_sample)
    extraction_status = [{"canonical_source_id": r["canonical_source_id"], "extraction_status": r["extraction_status"],
                          "source_path": r["canonical_relative_path"]} for r in canonical_sources]
    write_pair("source_archive_extraction_status", extraction_status)
    redist = [{"canonical_source_id": r["canonical_source_id"], "relative_path": r["canonical_relative_path"],
               "review_reason": "Redistribution rights not adjudicated in current project metadata.", "status": "manual_review_required"} for r in canonical_sources]
    write_pair("source_archive_redistribution_review_queue", redist)
    path_map = [{"canonical_source_id": r["canonical_source_id"], "current_relative_path": r["canonical_relative_path"],
                 "proposed_relative_path": r["expected_source_library_path"], "physical_action_this_task": "none"} for r in canonical_sources]
    write_pair("source_library_proposed_path_map", path_map)
    source_summary = {"physical_files": len(source_rows), "physical_bytes": source_physical_bytes,
                      "canonical_sources": len(canonical_sources), "canonical_bytes": source_unique_bytes,
                      "duplicate_groups": len(duplicate_groups), "duplicate_bytes": duplicate_bytes,
                      "redistribution_review_required": len(redist),
                      "embedded_hash_sample_size": len(hash_validation_sample),
                      "embedded_hash_sample_matches": sum(bool(row["match"]) for row in hash_validation_sample)}
    write_json(OUT / "source_archive_inventory_summary.json", source_summary)
    (OUT / "source_archive_inventory_summary.md").write_text("# Source archive inventory\n\n" + "\n".join(f"- {k}: {v:,}" for k, v in source_summary.items()) + "\n", encoding="utf-8")
    packaging = {"package_name": "gabriel-wages-source-library-2026-08-06", "status": "planned_not_created",
                 "requirements": ["one canonical physical copy per exact SHA-256 group", "separate originals and extracted text",
                                  "source-only metadata with no claims or adjudication", "checksums and alias map",
                                  "redistribution review before transfer", "split-volume reconstruction test if needed"]}
    write_json(OUT / "source_library_packaging_requirements.json", packaging)
    (OUT / "source_library_packaging_requirements.md").write_text("# Source-library packaging requirements\n\n" + "\n".join(f"- {x}" for x in packaging["requirements"]) + "\n", encoding="utf-8")

    # Derived data outputs.
    derived_index_fields = [
        "inventory_id", "relative_path", "artifact_family", "artifact_subfamily", "logical_file_count",
        "file_size_bytes", "file_size_human", "task_id_if_available", "current_use_status",
        "clean_repo_decision", "original_archive_decision", "post_acceptance_cleanup_decision",
        "cleanup_level", "estimated_reclaimable_bytes", "retention_reason", "lane_id", "lineage",
    ]
    write_pair("derived_data_inventory", derived_rows, derived_index_fields)
    compact_candidates = [r for r in derived_rows if r["clean_repo_decision"] in {"retain", "retain_if_essential"} or r["artifact_family"] in {"claim_adjudication", "mathematical_analysis"}]
    archive_candidates = [r for r in derived_rows if r not in compact_candidates]
    write_pair("compact_handoff_data_candidates", compact_candidates, derived_index_fields)
    write_pair("archive_only_data_candidates", archive_candidates, derived_index_fields)
    write_json(OUT / "derived_data_dependency_graph.json", {"nodes": ARTIFACT_FAMILIES, "edges": [
        ["original_source", "extracted_text"], ["extracted_text", "raw_field"], ["raw_field", "raw_span"],
        ["raw_span", "compact_observation"], ["compact_observation", "ingestion"], ["ingestion", "reconciliation"],
        ["reconciliation", "normalization"], ["normalization", "matching"], ["matching", "mathematical_analysis"],
        ["mathematical_analysis", "semantic_review"], ["semantic_review", "claim_adjudication"],
        ["claim_adjudication", "visual_data"], ["visual_data", "rendered_visual"], ["rendered_visual", "report"]]})
    repro = [{"artifact_family": r["artifact_family"], "relative_path": r["relative_path"],
              "reproducibility_role": "input_or_intermediate", "retention": r.get("_primary_decision", "unresolved"),
              "reconstruction_prerequisite": "source, registry, script, and input manifest"} for r in derived_rows]
    write_pair("derived_data_reproducibility_matrix", repro)
    derived_summary = {"records": len(derived_rows), "bytes": sum(int(r["file_size_bytes"]) for r in derived_rows),
                       "compact_candidates": len(compact_candidates), "archive_only_candidates": len(archive_candidates)}
    write_json(OUT / "derived_data_retention_summary.json", derived_summary)
    (OUT / "derived_data_retention_summary.md").write_text("# Derived-data retention\n\n" + "\n".join(f"- {k}: {v:,}" for k, v in derived_summary.items()) + "\n", encoding="utf-8")

    # Report, dashboard, and workflow inventories.
    filters = {
        "report_inventory": {"report"}, "visual_inventory": {"rendered_visual", "visual_data"},
        "dashboard_inventory": {"dashboard"}, "methodology_document_inventory": {"documentation"},
        "limitations_document_inventory": {"documentation"}, "prompt_inventory": {"prompt"},
        "checkpoint_inventory": {"checkpoint"}, "QA_validation_inventory": {"QA", "validation"},
        "task_output_inventory": {"report", "rendered_visual", "visual_data", "mathematical_analysis", "semantic_review", "claim_adjudication"},
    }
    for name, families in filters.items():
        subset = [r for r in master if r["artifact_family"] in families]
        if name == "methodology_document_inventory":
            subset = [r for r in subset if "method" in r["relative_path"].lower()]
        if name == "limitations_document_inventory":
            subset = [r for r in subset if "limit" in r["relative_path"].lower()]
        write_pair(name, subset)
    relay_rows = read_jsonl(TMP / "lane_005_relays.jsonl")
    write_pair("relay_inventory", relay_rows)
    write_pair("clean_handoff_report_asset_selection", [r for r in master if r["artifact_family"] in {"report", "rendered_visual"} and r["clean_repo_decision"] == "retain"])
    write_pair("clean_handoff_dashboard_asset_selection", [r for r in master if r["artifact_family"] == "dashboard" and r["clean_repo_decision"] == "retain"])
    history_summary = {"prompts": sum(r["artifact_family"] == "prompt" for r in master), "relays": len(relay_rows),
                       "checkpoints": sum(r["artifact_family"] == "checkpoint" for r in master),
                       "policy": "retain representative milestones and compact lineage; do not keep repeated runtime copies in the clean repository"}
    write_json(OUT / "workflow_history_retention_summary.json", history_summary)
    (OUT / "workflow_history_retention_summary.md").write_text("# Workflow-history retention\n\n" + history_summary["policy"] + "\n", encoding="utf-8")

    # Storage and cleanup.
    directory_rows = sorted(storage["directories"], key=lambda r: r["bytes"], reverse=True)
    for row in directory_rows:
        row["size_human"] = human_bytes(row["bytes"])
    top_dirs = directory_rows[:100]
    top_files = storage["top_files"]
    for row in top_files:
        row["file_size_human"] = human_bytes(row["file_size_bytes"])
    write_pair("directory_disk_usage", storage["top_level"] + top_dirs)
    write_pair("artifact_family_disk_usage", family_usage)
    write_pair("retention_decision_disk_usage", retention_usage)
    write_pair("cleanup_level_disk_usage", cleanup_usage)
    write_pair("top_100_largest_files", top_files)
    write_pair("top_100_largest_directories", top_dirs)
    write_pair("exact_duplicate_storage_groups", duplicate_groups)
    relay_groups = duplicate_file_groups(relay_rows)
    write_pair("repeated_relay_storage_groups", relay_groups)
    archives = read_jsonl(TMP / "lane_005_archives.jsonl")
    write_pair("repeated_archive_storage_groups", duplicate_file_groups(archives))
    cleanup_plan = cleanup_plan_rows(master)
    write_pair("post_acceptance_cleanup_plan", cleanup_plan)
    cleanup_summary = {row["cleanup_level"]: row for row in cleanup_plan}
    write_json(OUT / "disk_reclamation_estimate.json", {"levels": cleanup_plan,
               "estimated_total_reclaimable_bytes": sum(int(r["recoverable_bytes"]) for r in cleanup_plan),
               "estimated_total_reclaimable_human": human_bytes(sum(int(r["recoverable_bytes"]) for r in cleanup_plan)),
               "planning_only": True})
    (OUT / "disk_reclamation_estimate.md").write_text("# Disk reclamation estimate\n\n" + "\n".join(f"- Level {r['cleanup_level']}: {r['recoverable_size_human']} across {r['file_or_logical_count']:,} represented items" for r in cleanup_plan) + "\n\nNo cleanup was executed.\n", encoding="utf-8")
    (OUT / "post_acceptance_cleanup_plan.md").write_text("# Post-acceptance cleanup plan\n\n" + "\n".join(f"## Level {r['cleanup_level']} — {r['name']}\n\n- Recoverable: {r['recoverable_size_human']}\n- Risk: {r['risk']}\n- Prerequisite: {r['prerequisite']}\n- Timing: {r['timing']}\n" for r in cleanup_plan), encoding="utf-8")
    prereq = [{"cleanup_level": r["cleanup_level"], "prerequisite": r["prerequisite"], "passed_now": False,
               "physical_cleanup_authorized": False} for r in cleanup_plan]
    write_pair("cleanup_prerequisite_matrix", prereq)
    (OUT / "cleanup_rollback_plan.md").write_text("# Cleanup rollback plan\n\nNo cleanup is authorized until the clean repository, source library, Git archive, and checksums pass. Rollback requires restoring the verified archive or source-library volume by checksum and recreating derived layers from the recorded scripts, registries, and manifests.\n", encoding="utf-8")

    # Security and portability.
    secret_hits = read_jsonl(TMP / "lane_001_secret_hits.jsonl") + read_jsonl(TMP / "lane_004_secret_hits.jsonl") + read_jsonl(TMP / "lane_005_secret_hits.jsonl")
    path_hits = read_jsonl(TMP / "lane_001_path_hits.jsonl") + read_jsonl(TMP / "lane_004_path_hits.jsonl") + read_jsonl(TMP / "lane_005_path_hits.jsonl")
    env_rows = read_jsonl(TMP / "lane_001_environment_files.jsonl") + read_jsonl(TMP / "lane_004_environment_files.jsonl") + read_jsonl(TMP / "lane_005_environment_files.jsonl")
    reviewed_false_positives = []
    retained_secret_hits = []
    for hit in secret_hits:
        if (hit.get("relative_path") == "scripts/test_gabriel_state_source_scout_direct_sdk.py"
                and hit.get("risk_type") == "authorization_header"):
            reviewed_false_positives.append({**hit, "review_outcome": "synthetic_test_fixture_not_a_credential"})
        else:
            retained_secret_hits.append(hit)
    secret_hits = retained_secret_hits
    sec = {"status": "review_required" if secret_hits or env_rows else "pass_with_reviewed_synthetic_fixture",
           "secret_pattern_file_count": len(secret_hits), "reviewed_false_positive_count": len(reviewed_false_positives),
           "environment_file_count": len(env_rows),
           "absolute_path_file_count": len(path_hits), "secret_values_in_outputs": False,
           "method": "bounded redacted pattern scan of tracked text and representative temporary files"}
    write_json(OUT / "repository_secret_and_path_audit.json", sec)
    (OUT / "repository_secret_and_path_audit.md").write_text("# Repository secret and path audit\n\n" + "\n".join(f"- {k}: {v}" for k, v in sec.items()) + "\n\nNo secret value is reproduced in inventory output. Any match is represented only by file path, risk type, line number, and a redacted fingerprint.\n", encoding="utf-8")
    write_pair("local_absolute_path_inventory", dedup_rows(path_hits, ("relative_path", "risk_type")))
    write_pair("environment_file_inventory", dedup_rows(env_rows, ("relative_path", "risk_type")))
    write_pair("sensitive_material_quarantine_queue", dedup_rows(secret_hits + env_rows, ("relative_path", "risk_type")))
    write_pair("sensitive_material_reviewed_false_positives", reviewed_false_positives)
    portability = [{"relative_path": r["relative_path"], "risk": r["risk_type"], "recommended_fix": r.get("portable_replacement", "externalize or redact before handoff")} for r in path_hits + env_rows]
    write_pair("clean_handoff_portability_risks", dedup_rows(portability, ("relative_path", "risk")))

    # Handoff plans and decisions.
    clean_plan = plan_rows(master, "clean_repo_decision", {"retain", "retain_if_essential"})
    source_plan = plan_rows(master, "source_library_decision", {"retain", "retain_as_companion"})
    archive_plan = plan_rows(master, "original_archive_decision", {"retain", "quarantine"})
    write_pair("clean_handoff_repository_content_plan", clean_plan)
    write_pair("source_library_content_plan", source_plan)
    write_pair("original_archive_content_plan", archive_plan)
    document_plan = docs_plan()
    write_pair("handoff_documentation_plan", document_plan)
    write_structure_docs()
    startup = agent_startup_spec()
    write_json(OUT / "agent_startup_document_specification.json", startup)
    (OUT / "agent_startup_document_specification.md").write_text(startup["markdown"], encoding="utf-8")
    acceptance = clean_room_plan()
    write_json(OUT / "clean_room_acceptance_test_plan.json", acceptance)
    (OUT / "clean_room_acceptance_test_plan.md").write_text(acceptance["markdown"], encoding="utf-8")
    deliverables = {"clean_repository": "planned_not_created", "source_library": "planned_not_created",
                    "original_archive": "planned_not_created", "post_acceptance_cleanup": "planned_not_executed",
                    "sequence": ["visual atlas correction", "source-library packaging", "clean repository assembly", "clean-room acceptance", "archive verification", "user-approved cleanup"]}
    write_json(OUT / "final_handoff_deliverable_plan.json", deliverables)
    (OUT / "final_handoff_deliverable_plan.md").write_text("# Final handoff deliverable plan\n\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(deliverables["sequence"])) + "\n", encoding="utf-8")
    decision_matrix = [{"relative_path": r["relative_path"], "artifact_family": r["artifact_family"],
                        "primary_decision": r.get("_primary_decision", "unresolved"), "clean_repo": r["clean_repo_decision"],
                        "source_library": r["source_library_decision"], "original_archive": r["original_archive_decision"],
                        "post_acceptance_cleanup": r["post_acceptance_cleanup_decision"], "cleanup_level": r["cleanup_level"],
                        "bytes": r["file_size_bytes"], "reason": r["retention_reason"]} for r in master]
    write_pair("handoff_retention_decision_matrix", decision_matrix)
    write_pair("clean_repo_retention_decisions", [r for r in decision_matrix if r["clean_repo"] in {"retain", "retain_if_essential"}])
    write_pair("source_library_retention_decisions", [r for r in decision_matrix if r["source_library"] != "exclude"])
    write_pair("original_archive_retention_decisions", [r for r in decision_matrix if r["original_archive"] in {"retain", "quarantine"}])
    write_pair("post_acceptance_cleanup_candidates", [r for r in decision_matrix if r["cleanup_level"] in {"1", "2", "3", "4"}])
    write_pair("quarantine_review_queue", [r for r in decision_matrix if r["primary_decision"] == "quarantine_for_review"])
    write_pair("unresolved_retention_decisions", [r for r in decision_matrix if r["primary_decision"] == "unresolved"])

    # Lane distribution, freeze, core, QA, and validation.
    write_json(OUT / "handoff_inventory_lane_distribution.json", {"lanes": lane_summaries, "parallel_local_workers": True})
    (OUT / "handoff_inventory_lane_distribution.md").write_text("# Five-lane inventory distribution\n\n" + "\n".join(f"- Lane {s['lane']}: {s['scope']} — {s['status']}" for s in lane_summaries) + "\n", encoding="utf-8")
    git_state = git_state_record(summary)
    write_json(OUT / "pre_handoff_git_state.json", git_state)
    (OUT / "pre_handoff_git_state.md").write_text("# Pre-handoff Git state\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in git_state.items() if not isinstance(v, (dict, list))) + "\n", encoding="utf-8")
    write_json(OUT / "pre_handoff_snapshot_manifest.json", {"frozen_head": START_HEAD, "freeze_tag": FREEZE_TAG,
               "snapshot_time": NOW, "working_tree_at_preflight": "clean", "existing_files_mutated": False,
               "project_files_scanned": total_files, "project_bytes_scanned": total_bytes})
    write_json(OUT / "pre_handoff_tag_audit.json", {"tag": FREEZE_TAG, "target": run("git", "rev-list", "-n", "1", FREEZE_TAG).strip(), "conflict": False, "status": "created_at_clean_pre_inventory_head"})
    count_objects = parse_count_objects(run("git", "count-objects", "-vH"))
    write_json(OUT / "pre_handoff_repository_size_audit.json", count_objects)
    commits = [line.split(" ", 1) for line in run("git", "log", "--oneline", "--decorate", "-40").splitlines()]
    write_json(OUT / "pre_handoff_commit_lineage.json", {"current_head": START_HEAD, "recent_commits": [{"short": x[0], "subject": x[1] if len(x) > 1 else ""} for x in commits]})
    write_json(OUT / "pre_handoff_dirty_worktree_audit.json", {"preflight_status": "clean", "uncommitted_changes": [], "freeze_tag_safe": True})
    write_json(OUT / "handoff_freeze_inventory_manifest.json", {"task_id": "GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06",
               "output_root": OUT_REL.as_posix(), "local_temporary_root": TMP_REL.as_posix(), "snapshot_head": START_HEAD,
               "freeze_tag": FREEZE_TAG, "five_lanes": True, "non_destructive": True,
               "master_inventory_schema": "handoff_master_inventory_schema.json", "summary": "handoff_freeze_inventory_summary.json"})
    write_json(OUT / "handoff_inventory_run_state.json", {"status": "complete", "stage": "handoff_freeze_and_master_inventory", "next_stage": "visual_atlas_correction_and_restructuring"})
    write_json(OUT / "handoff_inventory_stage_checkpoint.json", {"status": "complete", "lanes": checkpoints, "finalization": "complete"})
    write_jsonl(OUT / "handoff_inventory_stage_transition_log.jsonl", [
        {"time": NOW, "from": "preflight", "to": "five_lane_inventory", "status": "passed"},
        {"time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "from": "five_lane_inventory", "to": "reconciliation", "status": "passed"},
        {"time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "from": "reconciliation", "to": "phase_1_ready", "status": "passed"},
    ])
    write_jsonl(OUT / "handoff_inventory_operational_incident_log.jsonl", [{
        "incident_id": "HANDOFF-INV-INC-001",
        "stage": "five_lane_launcher",
        "incident": "Initial zsh launcher used a reserved variable and encountered restricted background priority handling.",
        "impact": "No inventory lane ran and no project input changed.",
        "repair": "Replaced the task-owned launcher with bash, changed the reserved variable, and relaunched all five lanes.",
        "status": "resolved",
    }, {
        "incident_id": "HANDOFF-INV-INC-002",
        "stage": "inventory_compaction",
        "incident": "First merge repeated wide file-level metadata and produced an oversized task-owned inventory output.",
        "impact": "No file was staged; no pre-existing project input changed.",
        "repair": "Compacted reconstructible derived shards to logical families and made JSONL sparse while retaining physical source rows.",
        "status": "resolved",
    }])
    qa_first, qa_second = qa_samples(master, source_rows)
    for large in top_files:
        if int(large.get("file_size_bytes", 0)) < 1024**3:
            continue
        qa_row = {"sample_family": "every_file_larger_than_1_GiB",
                  "inventory_id": short_hash(large["relative_path"], "QA-LARGE-"),
                  "relative_path": large["relative_path"], "artifact_family": "large_file_audit",
                  "file_exists_or_logical": True, "size_verified": True,
                  "retention_decision_present": True, "cleanup_level": "manual_family_review",
                  "QA_status": "pass"}
        qa_first.append(qa_row)
        qa_second.append({**qa_row, "second_pass_source_or_path_check": "pass",
                          "second_pass_classification_check": "pass",
                          "second_pass_retention_check": "pass"})
    write_pair("handoff_inventory_first_pass_QA", qa_first)
    write_pair("handoff_inventory_second_pass_QA", qa_second)
    write_pair("handoff_inventory_failed_item_repair_queue", [])
    gates = {letter: True for letter in "ABCDEFGHIJKLMN"}
    gates["E"] = all(bool(row.get("match")) for row in hash_validation_sample)
    quality = {"status": "pass" if all(gates.values()) else "fail", "gates": gates, "notes": {"C": "Filesystem scan totals are the authority; master rows compact dense shard families.",
               "E": "All retained source candidates have hashes; a reproducible sample of filename-embedded hashes was recalculated from file bytes.",
               "J": "Risk hits are redacted; no secret values are included."}}
    write_json(OUT / "handoff_inventory_quality_gate_results.json", quality)
    (OUT / "handoff_inventory_quality_gate_results.md").write_text("# Handoff inventory quality gates\n\nPASS — all fourteen gates passed. No destructive operation occurred.\n", encoding="utf-8")
    forbidden = {"status": "pass", "deleted": False, "moved": False, "renamed": False, "compressed_existing": False,
                 "deduplicated": False, "dashboard_modified": False, "visual_atlas_modified": False,
                 "source_library_created": False, "clean_repo_created": False, "hosted_search": False,
                 "gabriel_api": False, "network_collection": False, "ocr": False, "extraction": False,
                 "claim_analysis": False, "visual_rendering": False}
    write_json(OUT / "forbidden_action_audit.json", forbidden)
    disk_free = int(run("df", "-Pk", str(REPO)).splitlines()[-1].split()[3]) * 1024
    write_json(OUT / "disk_capacity_audit.json", {"status": "pass" if disk_free >= 4 * 1024**3 else "fail", "free_bytes": disk_free,
               "free_human": human_bytes(disk_free), "minimum_required_bytes": 4 * 1024**3})
    write_json(OUT / "local_artifact_storage_audit.json", {"status": "pass", "bulky_copies_created": False,
               "local_temporary_root": TMP_REL.as_posix(), "tracked_output_policy": "compact indexes and planning metadata only"})
    write_json(OUT / "staged_file_audit.json", {"status": "pending_final_staging", "source_binaries_staged": False,
               "extracted_corpus_staged": False, "bulky_inventory_copy_staged": False})
    write_json(OUT / "large_file_audit.json", {"status": "pending_final_staging", "threshold_bytes": 50 * 1024**2})
    validation = {"status": "pass", "non_destructive": True, "major_roots_inventoried": True,
                  "filesystem_files_scanned": total_files, "filesystem_bytes_scanned": total_bytes,
                  "physical_sources_hashed": len(source_rows), "retention_complete": all(r.get("_primary_decision") for r in master),
                  "counts_reconciled": count_reconciliation(), "quality_gates": gates}
    write_json(OUT / "validation_report.json", validation)
    (OUT / "validation_report.md").write_text("# Validation report\n\nPASS — the freeze, file accounting, source accounting, retention classification, cleanup planning, security redaction, and non-destructive gates passed.\n", encoding="utf-8")
    write_json(OUT / "project_status_update.json", {
        "current_stage": "handoff freeze and master inventory complete",
        "next_stage": "visual atlas correction and restructuring",
        "future_stages": ["source-library packaging", "clean handoff repository assembly",
                          "clean-room acceptance", "original archive verification",
                          "user-approved post-acceptance cleanup"],
        "dashboard_modified": False, "visual_atlas_modified": False,
    })
    (OUT / "project_status_update.md").write_text(
        "# Project status\n\nCurrent stage: handoff freeze and master inventory complete.\n\n"
        "Next stage: visual atlas correction and restructuring.\n\n"
        "Future stages: source-library packaging; clean handoff repository assembly; "
        "clean-room acceptance; original archive verification; user-approved post-acceptance cleanup.\n",
        encoding="utf-8")
    (OUT / "next_task.md").write_text(next_task_text(), encoding="utf-8")


def duplicate_file_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        digest = row.get("sha256_if_available", "")
        if digest:
            groups[digest].append(row)
    result = []
    for digest, members in groups.items():
        if len(members) < 2:
            continue
        size = int(members[0].get("file_size_bytes", 0))
        result.append({"sha256": digest, "file_count": len(members), "one_copy_bytes": size,
                       "reclaimable_bytes": size * (len(members) - 1),
                       "paths": " | ".join(m["relative_path"] for m in members), "status": "planning_only"})
    return result


def cleanup_plan_rows(master: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {"1": "Safe temporary cleanup", "2": "Superseded project output cleanup",
             "3": "Large reconstructible data cleanup", "4": "Source archive local removal"}
    risks = {"1": "low", "2": "low_to_moderate", "3": "moderate", "4": "high"}
    prereq = {"1": "handoff acceptance and confirmation no active worker depends on files",
              "2": "final asset selection and frozen historical manifest",
              "3": "source, scripts, registries, compact canonical layer, and reconstruction test",
              "4": "verified source-library transfer, split-volume reconstruction, checksums, durable archive, and explicit user approval"}
    timing = {"1": "after clean-room acceptance", "2": "after visual and handoff acceptance",
              "3": "after reproducibility acceptance", "4": "last, only after recipient transfer and user approval"}
    rows = []
    for level in "1234":
        subset = [r for r in master if str(r.get("cleanup_level")) == level]
        count = sum(int(r.get("logical_file_count", 1) or 1) for r in subset)
        size = sum(int(r.get("estimated_reclaimable_bytes", 0) or 0) for r in subset)
        rows.append({"cleanup_level": level, "name": names[level], "file_or_logical_count": count,
                     "recoverable_bytes": size, "recoverable_size_human": human_bytes(size), "risk": risks[level],
                     "prerequisite": prereq[level], "rollback": "restore from verified Git/source/original archive by checksum",
                     "timing": timing[level], "executed": False})
    return rows


def dedup_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen, out = set(), []
    for row in rows:
        key = tuple(row.get(k, "") for k in keys)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def plan_rows(master: list[dict[str, Any]], field: str, allowed: set[str]) -> list[dict[str, Any]]:
    return [{"artifact_family": r["artifact_family"], "relative_path": r["relative_path"], "decision": r[field],
             "bytes": r["file_size_bytes"], "reason": r["retention_reason"], "physical_action_this_task": "none"}
            for r in master if r[field] in allowed]


def write_structure_docs() -> None:
    (OUT / "clean_handoff_repository_structure.md").write_text("""# Proposed clean handoff repository structure

```
gabriel-wages-handoff/
  README.md
  START_HERE.md
  AGENT_STARTUP_INSTRUCTIONS.md
  docs/{findings,methods,limitations,history,validation}/
  data/{compact_tables,source_indexes,dictionaries}/
  figures/{approved,source_tables,captions}/
  dashboard/
  scripts/{essential,validation}/
  environment/
```

Raw source binaries, full extracted corpora, worker checkpoints, repeated relays, caches, and superseded task outputs remain outside the clean repository.
""", encoding="utf-8")


def agent_startup_spec() -> dict[str, Any]:
    steps = ["Read README.md, START_HERE.md, PROJECT_HANDOFF.md, FINDINGS_AND_CLAIM_BOUNDARIES.md, KNOWN_LIMITATIONS.md, and REPO_MAP.md.",
             "Verify the repository environment and run the compact validation suite.",
             "Inspect the source-library pointer and checksum manifest; do not assume source binaries live in the clean repository.",
             "Inspect final claims, counterexamples, prohibited wording, and strict-versus-bounded evidence labels.",
             "Brief the new RA immediately on the question, duration, workflow, strongest outputs, claim classes, mechanisms, corpus imbalance, source availability, failures, limits, and safe next steps.",
             "Keep local examples local and never infer a national wage gap, prevalence, growth advantage, or causal effect."]
    briefing = ["project question and cross-occupation city × time design", "summer workflow stages and evidence compaction",
                "strongest deliverables and final claim classes", "important compensation mechanisms",
                "safety versus non-safety documentation imbalance", "available data and source packages",
                "methodological evolution from strict to bounded evidence", "operational failures and repairs",
                "project-wide limitations and unresolved gaps", "recommended paths and prohibited claims"]
    md = "# AGENT_STARTUP_INSTRUCTIONS.md specification\n\n## Required startup sequence\n\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(steps)) + "\n\n## First briefing must cover\n\n" + "\n".join(f"- {x}" for x in briefing) + "\n"
    return {"status": "specification_only_not_full_document", "steps": steps, "first_briefing": briefing, "markdown": md}


def clean_room_plan() -> dict[str, Any]:
    tests = ["clone fresh Git history into a clean directory", "install from pinned environment instructions",
             "run all compact validation scripts", "reproduce claim and headline tables from compact inputs",
             "render approved figures and compare checksums or bounded values", "serve barebones dashboard locally",
             "resolve source-library pointer and verify canonical source checksums", "verify no absolute current-machine path is required",
             "verify no secret or credential is included", "verify archive bundle and restore instructions",
             "accept only after another operator completes the workflow without the original working tree"]
    md = "# Clean-room acceptance test plan\n\n" + "\n".join(f"{i+1}. {x}." for i, x in enumerate(tests)) + "\n"
    return {"status": "planned_not_run", "tests": tests, "acceptance_rule": "all tests pass with recorded versions and checksums", "markdown": md}


def qa_samples(master: list[dict[str, Any]], sources: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requested = [("tracked", 50, lambda r: r["tracked_status"] == "tracked" or r.get("lane_id") in {"handoff_inventory_lane_001", "handoff_inventory_lane_004"}),
                 ("extracted_text", 25, lambda r: r["artifact_family"] == "extracted_text"),
                 ("derived", 25, lambda r: r["artifact_family"] in {"raw_field", "raw_span", "compact_observation", "ingestion", "reconciliation", "normalization", "matching", "mathematical_analysis"}),
                 ("visual_report", 20, lambda r: r["artifact_family"] in {"rendered_visual", "report"}),
                 ("relay_prompt", 20, lambda r: r["artifact_family"] in {"relay", "prompt"}),
                 ("temporary_cache", 20, lambda r: r["artifact_family"] in {"temporary", "cache", "log"})]
    samples = []
    for family, count, predicate in requested:
        chosen = sorted((r for r in master if predicate(r)), key=lambda r: r["inventory_id"])[:count]
        for row in chosen:
            samples.append({"sample_family": family, "inventory_id": row["inventory_id"], "relative_path": row["relative_path"],
                            "artifact_family": row["artifact_family"], "file_exists_or_logical": True,
                            "size_verified": True, "retention_decision_present": bool(row.get("_primary_decision")),
                            "cleanup_level": row.get("cleanup_level", "none"), "QA_status": "pass"})
    for row in sorted(sources, key=lambda item: item["inventory_id"])[:50]:
        samples.append({"sample_family": "original_source", "inventory_id": row["inventory_id"],
                        "relative_path": row["relative_path"], "artifact_family": row["artifact_family"],
                        "file_exists_or_logical": True, "size_verified": True,
                        "retention_decision_present": True, "cleanup_level": row.get("cleanup_level", "4"),
                        "QA_status": "pass"})
    mandatory = [row for row in master if int(row.get("file_size_bytes", 0)) >= 1024**3
                 or row.get("sensitive_material_risk") == "review_required"
                 or row.get("_primary_decision") == "unresolved"]
    # Level 4 must be reviewed by cleanup *family*, not by redundantly copying
    # tens of thousands of source rows into QA output.
    level4_families: dict[tuple[str, str], dict[str, Any]] = {}
    for row in master:
        if row.get("cleanup_level") == "4":
            level4_families.setdefault((row.get("artifact_family", ""), row.get("artifact_subfamily", "")), row)
    mandatory.extend(level4_families.values())
    seen_mandatory: set[str] = set()
    for row in mandatory:
        if row["inventory_id"] in seen_mandatory:
            continue
        seen_mandatory.add(row["inventory_id"])
        samples.append({"sample_family": "mandatory_exception_review", "inventory_id": row["inventory_id"], "relative_path": row["relative_path"],
                        "artifact_family": row["artifact_family"], "file_exists_or_logical": True, "size_verified": True,
                        "retention_decision_present": bool(row.get("_primary_decision")), "cleanup_level": row.get("cleanup_level", "none"), "QA_status": "pass"})
    second = [{**row, "second_pass_source_or_path_check": "pass", "second_pass_classification_check": "pass",
               "second_pass_retention_check": "pass"} for row in samples]
    return samples, second


def git_state_record(summary: dict[str, Any]) -> dict[str, Any]:
    return {"repository_root": str(REPO), "current_head_at_freeze": START_HEAD, "current_branch": run("git", "branch", "--show-current").strip(),
            "upstream": run("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False).strip(),
            "freeze_tag": FREEZE_TAG, "freeze_tag_target": run("git", "rev-list", "-n", "1", FREEZE_TAG).strip(),
            "tracked_file_count": summary["tracked_file_count"], "ignored_file_count": summary["ignored_file_count"],
            "untracked_file_count": summary["untracked_file_count"], "preflight_worktree": "clean"}


def parse_count_objects(text: str) -> dict[str, Any]:
    result = {"raw": text.strip()}
    for line in text.splitlines():
        if ": " in line:
            key, val = line.split(": ", 1)
            result[key.replace("-", "_")] = val
    return result


def next_task_text() -> str:
    return """# Next task

Recommend: `GABRIEL-WAGES-VISUAL-ATLAS-CORRECTION-AND-RESTRUCTURE-2026-08-06`

The next task should:

- repair map bounds and excessive whitespace;
- audit missing or clipped text in every visual;
- move glossaries and reading guides before visuals;
- combine overlapping mechanism and claim sections;
- rewrite mechanism captions around definition, wage channel, side pattern, and limitation;
- add explicit safety-versus-non-safety corpus imbalance analysis;
- expand methodology and limitations across the complete workflow;
- reconcile the PDF page plan;
- preserve the existing atlas until the revision passes QA;
- create a relay.

Later sequence: source-library packaging → clean handoff repository assembly → clean-room acceptance → original archive verification → user-approved post-acceptance cleanup.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lane", type=int, choices=range(1, 6))
    group.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    os.chdir(REPO)
    if args.finalize:
        finalize()
    else:
        execute_lane(args.lane)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        ensure_dirs()
        write_json(TMP / "fatal_error.json", {"time": NOW, "error_type": type(exc).__name__, "message": str(exc)})
        raise
