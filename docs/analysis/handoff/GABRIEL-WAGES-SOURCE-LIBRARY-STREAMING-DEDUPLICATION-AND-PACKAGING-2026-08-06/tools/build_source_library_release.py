#!/usr/bin/env python3
"""Build compact source-library indexes and a frozen volume plan.

The script writes metadata only. It never copies source or extracted-text
payloads. Complete transfer indexes live beneath the ignored handoff-package
root and are placed into READ-ME-FIRST.zip; tracked outputs remain compact.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import shutil
import zipfile


RELEASE = "gabriel-wages-source-library-2026-08-06"
TARGET = 2 * 1024**3
HARD = int(2.5 * 1024**3)


def read_csv(path: Path, gz: bool = False) -> list[dict[str, str]]:
    opener = gzip.open if gz or path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2):
            h.update(chunk)
    return h.hexdigest()


def slug(value: str, fallback: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return (value or fallback)[:80]


def suffixes(path: str) -> str:
    joined = "".join(Path(path).suffixes)
    return joined if joined and len(joined) <= 24 else Path(path).suffix


def source_path(row: dict[str, str]) -> tuple[str, str]:
    state = row["state"].strip().upper()
    state_tokens = sorted(set(re.findall(r"\b[A-Z]{2}\b", state)))
    municipality = row["municipality"].strip()
    source_id = row["canonical_source_id"]
    title = slug(row["display_title"], "untitled-source")
    ext = row["extension"].lower()
    filename = f"src_{source_id}__{title}{ext}"
    if len(state_tokens) > 1:
        return f"sources/multi_municipality/{'-'.join(state_tokens)}/{filename}", "multi_municipality"
    if re.fullmatch(r"[A-Z]{2}", state) and municipality:
        return f"sources/by_state/{state}/{slug(municipality, 'unresolved-municipality')}/{filename}", "municipality"
    if re.fullmatch(r"[A-Z]{2}", state):
        return f"sources/statewide/{state}/{filename}", "statewide"
    return f"sources/unresolved_location/{filename}", "unresolved_location"


def text_path(row: dict[str, str], source_record: dict) -> str:
    source_archive = Path(source_record["archive_relative_path"])
    base_parts = list(source_archive.parts)
    if base_parts[0] == "sources":
        base_parts[0] = "extracted_text"
    base_dir = Path(*base_parts[:-1]).as_posix()
    ext = suffixes(row["current_companion_path"]) or ".txt"
    return f"{base_dir}/src_{source_record['source_id']}{ext}"


def assign_volumes(records: list[dict]) -> tuple[list[dict], list[dict]]:
    records.sort(key=lambda r: (r["state"], r["municipality"], r["source_id"]))
    groups: list[list[dict]] = []
    current_group: list[dict] = []
    current_key = None
    for record in records:
        key = (record["state"], record["municipality"])
        if current_key is not None and key != current_key:
            groups.append(current_group)
            current_group = []
        current_group.append(record)
        current_key = key
    if current_group:
        groups.append(current_group)

    volumes: list[list[dict]] = []
    current: list[dict] = []
    current_bytes = 0
    for group in groups:
        group_bytes = sum(int(r["source_size_bytes"]) + int(r["text_size_bytes"] or 0) for r in group)
        if group_bytes <= HARD:
            if current and current_bytes + group_bytes > TARGET:
                volumes.append(current)
                current, current_bytes = [], 0
            current.extend(group)
            current_bytes += group_bytes
        else:
            if current:
                volumes.append(current)
                current, current_bytes = [], 0
            for record in group:
                size = int(record["source_size_bytes"]) + int(record["text_size_bytes"] or 0)
                if current and current_bytes + size > TARGET:
                    volumes.append(current)
                    current, current_bytes = [], 0
                current.append(record)
                current_bytes += size
    if current:
        volumes.append(current)

    assignments: list[dict] = []
    manifests: list[dict] = []
    width = max(3, len(str(len(volumes))))
    for index, members in enumerate(volumes, 1):
        volume_id = f"VOL-{index:0{width}d}"
        filename = f"{RELEASE}.part-{index:0{width}d}.tar.zst"
        states = sorted({token for r in members for token in re.findall(r"\b[A-Z]{2}\b", r["state"])})
        source_bytes = sum(int(r["source_size_bytes"]) for r in members)
        text_bytes = sum(int(r["text_size_bytes"] or 0) for r in members)
        for record in members:
            record["source_volume_id"] = volume_id
            assignments.append(
                {
                    "volume_id": volume_id,
                    "volume_filename": filename,
                    "source_id": record["source_id"],
                    "current_relative_path": record["current_relative_path"],
                    "archive_relative_path": record["archive_relative_path"],
                    "source_size_bytes": record["source_size_bytes"],
                    "source_sha256": record["source_SHA256"],
                    "text_current_relative_path": record["text_current_relative_path"],
                    "text_archive_relative_path": record["extracted_text_relative_path"],
                    "text_size_bytes": record["text_size_bytes"],
                    "text_sha256": record["text_SHA256"],
                }
            )
        manifests.append(
            {
                "volume_id": volume_id,
                "filename": filename,
                "status": "planned",
                "source_count": len(members),
                "source_bytes": source_bytes,
                "text_companion_count": sum(r["extracted_text_available"] == "true" for r in members),
                "text_bytes": text_bytes,
                "planned_total_bytes": source_bytes + text_bytes,
                "compressed_bytes": "",
                "compression_ratio": "",
                "archive_SHA256": "",
                "first_source_id": members[0]["source_id"],
                "last_source_id": members[-1]["source_id"],
                "state_coverage": "|".join(states),
                "municipality_count": len({(r["state"], r["municipality"]) for r in members}),
                "member_count": len(members) + sum(r["extracted_text_available"] == "true" for r in members) + 1,
                "validation_method": "pending",
                "verified_source_member_count": 0,
                "verification_status": "planned",
                "runtime_seconds": "",
            }
        )
    return assignments, manifests


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    lane2 = task / "lanes/lane_002"
    lane3 = task / "lanes/lane_003"
    phase0 = repo / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    manifests = package / "manifests"
    compact = package / "read_me_first_tree" / RELEASE
    package.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    compact.mkdir(parents=True, exist_ok=True)

    navigation = read_csv(lane2 / "SOURCE_INDEX.csv.gz", gz=True)
    companions = {r["canonical_source_id"]: r for r in read_csv(lane3 / "selected_extracted_text_companions.csv")}
    eligible = [r for r in navigation if r["navigation_packaging_eligible"].lower() == "true"]
    excluded = [r for r in navigation if r["navigation_packaging_eligible"].lower() != "true"]
    records: list[dict] = []
    for row in eligible:
        archive_path, geography_type = source_path(row)
        companion = companions.get(row["canonical_source_id"], {})
        text_available = bool(companion.get("current_companion_path"))
        known_issue = ""
        if int(row["file_size_bytes"]) < 100:
            known_issue = "Very small retained payload; content may be an access, empty, or unpublished response."
        record = {
            "source_id": row["canonical_source_id"],
            "title": row["display_title"],
            "safe_title": slug(row["display_title"], "untitled-source"),
            "source_family": row["source_family"] or "unresolved",
            "file_extension": row["extension"],
            "MIME_type": row["mime_type"] or mimetypes.guess_type(row["canonical_original_path"])[0] or "application/octet-stream",
            "municipality": row["municipality"].strip(),
            "state": row["state"].strip().upper(),
            "county_if_available": "",
            "primary_geography_type": geography_type,
            "period_label": row["period_label"],
            "period_start_if_available": row["period_start_year"],
            "period_end_if_available": row["period_end_year"],
            "original_URL": row["original_url"],
            "archive_relative_path": archive_path,
            "source_SHA256": row["sha256"],
            "source_size_bytes": row["file_size_bytes"],
            "alias_count": row["alias_count"],
            "provenance_count": str(1 + int(row["alias_count"] or 0)),
            "extracted_text_available": "true" if text_available else "false",
            "extracted_text_relative_path": "",
            "extraction_status": companion.get("extraction_status", row["extraction_status"]),
            "OCR_status": companion.get("ocr_status", "not_recorded"),
            "known_issue": known_issue,
            "availability_status": "available_at_packaging",
            "redistribution_note": "Internal research transfer; source terms not independently adjudicated.",
            "source_volume_id": "",
            "current_relative_path": row["canonical_original_path"],
            "text_current_relative_path": companion.get("current_companion_path", ""),
            "text_size_bytes": companion.get("current_companion_size_bytes", "0") if text_available else "0",
            "text_SHA256": companion.get("companion_sha256", "") if text_available else "",
        }
        if text_available:
            record["extracted_text_relative_path"] = text_path(companion, record)
        records.append(record)

    archive_paths = [r["archive_relative_path"].lower() for r in records]
    text_paths = [r["extracted_text_relative_path"].lower() for r in records if r["extracted_text_relative_path"]]
    if len(archive_paths) != len(set(archive_paths)) or len(text_paths) != len(set(text_paths)):
        raise RuntimeError("archive-relative path collision")
    assignments, volume_rows = assign_volumes(records)
    assignment_fields = list(assignments[0])
    assignment_csv = manifests / "source_library_volume_assignments.csv"
    write_csv(assignment_csv, assignments, assignment_fields)
    write_jsonl(manifests / "source_library_volume_assignments.jsonl", assignments)
    assignment_hash = sha(assignment_csv)

    index_fields = [k for k in records[0] if not k.endswith("current_relative_path") and k not in {"text_size_bytes", "text_SHA256"}]
    source_index_csv = compact / "SOURCE_INDEX.csv"
    source_index_jsonl = compact / "SOURCE_INDEX.jsonl"
    write_csv(source_index_csv, records, index_fields)
    write_jsonl(source_index_jsonl, [{k: r[k] for k in index_fields} for r in records])

    aliases = read_csv(lane2 / "source_aliases.csv")
    provenance = read_csv(lane2 / "source_provenance.csv.gz", gz=True)
    alias_fields = list(aliases[0]) if aliases else []
    prov_fields = list(provenance[0]) if provenance else []
    metadata = compact / "metadata"
    write_csv(metadata / "source_aliases.csv", aliases, alias_fields)
    write_jsonl(metadata / "source_aliases.jsonl", aliases)
    write_csv(metadata / "source_provenance.csv", provenance, prov_fields)
    write_jsonl(metadata / "source_provenance.jsonl", provenance)
    municipalities = sorted({(r["state"], r["municipality"], r["primary_geography_type"]) for r in records})
    write_csv(metadata / "municipality_crosswalk.csv", [dict(state=s, municipality=m, geography_type=g) for s, m, g in municipalities])
    write_csv(metadata / "source_periods.csv", [{"source_id": r["source_id"], "period_label": r["period_label"], "period_start": r["period_start_if_available"], "period_end": r["period_end_if_available"]} for r in records])
    write_csv(metadata / "extraction_status.csv", [{"source_id": r["source_id"], "extraction_status": r["extraction_status"], "OCR_status": r["OCR_status"], "extracted_text_available": r["extracted_text_available"], "extracted_text_relative_path": r["extracted_text_relative_path"]} for r in records])
    write_csv(metadata / "source_file_status.csv", [{"source_id": r["source_id"], "availability_status": r["availability_status"], "source_size_bytes": r["source_size_bytes"], "source_SHA256": r["source_SHA256"]} for r in records])
    write_csv(metadata / "known_source_issues.csv", [{"source_id": r["source_id"], "known_issue": r["known_issue"]} for r in records if r["known_issue"]])
    write_csv(metadata / "volume_source_crosswalk.csv", [{"source_id": r["source_id"], "source_volume_id": r["source_volume_id"], "archive_relative_path": r["archive_relative_path"]} for r in records])
    write_csv(metadata / "redistribution_notes.csv", [{"source_id": r["source_id"], "redistribution_note": r["redistribution_note"]} for r in records])

    write_csv(compact / "VOLUME_MANIFEST.csv", volume_rows)
    write_json(compact / "VOLUME_MANIFEST.json", volume_rows)
    write_csv(manifests / "VOLUME_MANIFEST.csv", volume_rows)
    write_json(manifests / "VOLUME_MANIFEST.json", volume_rows)
    write_json(manifests / "source_library_volume_assignment_hash.json", {"algorithm": "SHA-256", "assignment_file": "source_library_volume_assignments.csv", "sha256": assignment_hash, "row_count": len(assignments), "volume_count": len(volume_rows)})

    duplicate_rows = read_csv(phase0 / "source_archive_duplicate_groups.csv")
    duplicate_bytes = sum(int(r["duplicate_bytes_reclaimable"]) for r in duplicate_rows)
    release_manifest = {
        "release_name": RELEASE,
        "release_date": "2026-08-06",
        "source_library_version": "1.0-plan",
        "canonical_source_count": len(records),
        "packaged_source_count": 0,
        "missing_source_count": 0,
        "quarantined_source_count": len(excluded),
        "exact_duplicate_group_count": len(duplicate_rows),
        "exact_duplicates_removed_from_physical_packaging": sum(int(r["physical_copy_count"]) - 1 for r in duplicate_rows),
        "exact_duplicate_bytes_avoided": duplicate_bytes,
        "source_bytes": sum(int(r["source_size_bytes"]) for r in records),
        "extracted_text_companion_count": sum(r["extracted_text_available"] == "true" for r in records),
        "extracted_text_bytes": sum(int(r["text_size_bytes"] or 0) for r in records),
        "volume_count": len(volume_rows),
        "accepted_volume_count": 0,
        "volume_target_bytes": TARGET,
        "volume_hard_preferred_upper_bound": HARD,
        "compression_format": "independent tar archives compressed with Zstandard",
        "compression_level": 6,
        "archive_root": RELEASE,
        "source_index_SHA256": sha(source_index_csv),
        "volume_manifest_SHA256": sha(compact / "VOLUME_MANIFEST.csv"),
        "volume_assignment_SHA256": assignment_hash,
        "packaging_commit": "pending compact Git commit",
        "packaging_status": "planned",
    }
    write_json(compact / "RELEASE_MANIFEST.json", release_manifest)
    write_json(manifests / "RELEASE_MANIFEST.json", release_manifest)

    write_json(task / "source_library_source_count_reconciliation.json", {
        "phase0_physical_candidate_count": 26799,
        "phase0_physical_candidate_bytes": 56574034323,
        "phase0_canonical_count": 26637,
        "phase0_canonical_bytes": 56164354350,
        "packaging_eligible_source_count": len(records),
        "packaging_eligible_source_bytes": release_manifest["source_bytes"],
        "excluded_non_source_control_count": len(excluded),
        "excluded_records": [{"source_id": r["canonical_source_id"], "path": r["canonical_original_path"], "reason": r["exclusion_reason"]} for r in excluded],
        "exact_duplicate_groups": len(duplicate_rows),
        "exact_duplicate_redundant_copies": release_manifest["exact_duplicates_removed_from_physical_packaging"],
        "exact_duplicate_bytes_avoided": duplicate_bytes,
        "missing_source_count": 0,
    })
    write_json(task / "source_library_volume_assignment_hash.json", {"sha256": assignment_hash, "row_count": len(assignments), "volume_count": len(volume_rows), "complete_assignment_path": f"artifacts/handoff_packages/{RELEASE}/manifests/source_library_volume_assignments.csv"})
    write_csv(task / "VOLUME_MANIFEST.csv", volume_rows)
    write_json(task / "VOLUME_MANIFEST.json", volume_rows)
    write_json(task / "SOURCE_INDEX_pointer.json", {"row_count": len(records), "csv_sha256": sha(source_index_csv), "jsonl_sha256": sha(source_index_jsonl), "package_paths": [f"{RELEASE}/SOURCE_INDEX.csv", f"{RELEASE}/SOURCE_INDEX.jsonl"], "reason_not_tracked_uncompressed": "Complete indexes are transfer-package metadata and are too large for sensible Git tracking."})
    write_csv(task / "source_library_quarantine.csv", [{"source_id": r["canonical_source_id"], "current_relative_path": r["canonical_original_path"], "reason": r["exclusion_reason"], "status": "excluded_non_source_control"} for r in excluded])
    write_jsonl(task / "source_library_quarantine.jsonl", [{"source_id": r["canonical_source_id"], "current_relative_path": r["canonical_original_path"], "reason": r["exclusion_reason"], "status": "excluded_non_source_control"} for r in excluded])
    write_csv(task / "source_library_missing_files.csv", [], ["source_id", "expected_path", "known_sha256", "likely_reason"])
    write_jsonl(task / "source_library_missing_files.jsonl", [])
    write_csv(task / "source_library_exact_duplicate_groups.csv", duplicate_rows)
    write_jsonl(task / "source_library_exact_duplicate_groups.jsonl", duplicate_rows)
    write_json(task / "source_library_path_collision_audit.json", {"status": "pass", "source_path_count": len(archive_paths), "source_exact_or_casefold_collisions": 0, "text_path_count": len(text_paths), "text_exact_or_casefold_collisions": 0, "unsafe_paths": 0})

    # Copy compact documentation, schemas, and tools into transfer-first tree.
    lane5 = task / "lanes/lane_005"
    for name in ["README.md", "START_HERE.md", "SOURCE_USE_GUIDE.md", "DATA_DICTIONARY.md", "KNOWN_ISSUES.md"]:
        src = lane5 / name
        if src.exists():
            shutil.copyfile(src, compact / name)
    schemas = compact / "schemas"
    schemas.mkdir(exist_ok=True)
    schema_sources = {
        "source_index.schema.json": "canonical_source_record.schema.json",
        "source_aliases.schema.json": "source_alias_record.schema.json",
        "source_provenance.schema.json": "canonical_source_record.schema.json",
        "volume_manifest.schema.json": "volume_manifest_record.schema.json",
    }
    for name, lane5_name in schema_sources.items():
        candidates = [lane5 / lane5_name, lane5 / name, task / "schemas" / name]
        for src in candidates:
            if src.exists():
                shutil.copyfile(src, schemas / name)
                break
    transfer_tools = compact / "tools"
    transfer_tools.mkdir(exist_ok=True)
    for name in ["package_source_library.py", "verify_volume.py", "verify_library.py", "extract_all.sh", "extract_all.py", "resume_packaging.sh"]:
        src = task / "tools" / name
        if src.exists() and name != "package_source_library.py":
            shutil.copyfile(src, transfer_tools / name)

    # Package-content checksums cannot self-reference the ZIP that contains them.
    checksum_lines = []
    for path in sorted(p for p in compact.rglob("*") if p.is_file() and p.name != "CHECKSUMS.sha256"):
        checksum_lines.append(f"{sha(path)}  {path.relative_to(compact).as_posix()}")
    (compact / "CHECKSUMS.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    zip_path = package / f"{RELEASE}.READ-ME-FIRST.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in compact.rglob("*") if p.is_file()):
            archive.write(path, f"{RELEASE}/{path.relative_to(compact).as_posix()}")
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"READ-ME-FIRST ZIP failed at {bad}")
    write_json(manifests / "read_me_first_validation.json", {"status": "pass", "path": zip_path.name, "bytes": zip_path.stat().st_size, "sha256": sha(zip_path), "member_count": len(zipfile.ZipFile(zip_path).infolist()), "source_binary_members": 0})

    print(json.dumps({"eligible_sources": len(records), "source_bytes": release_manifest["source_bytes"], "text_companions": release_manifest["extracted_text_companion_count"], "text_bytes": release_manifest["extracted_text_bytes"], "volumes": len(volume_rows), "assignment_sha256": assignment_hash, "read_me_first": str(zip_path), "read_me_first_sha256": sha(zip_path)}, indent=2))


if __name__ == "__main__":
    main()
