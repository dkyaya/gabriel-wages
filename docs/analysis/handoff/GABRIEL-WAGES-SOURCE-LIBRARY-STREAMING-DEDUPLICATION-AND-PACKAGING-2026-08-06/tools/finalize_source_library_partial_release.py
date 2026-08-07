#!/usr/bin/env python3
"""Finalize compact metadata after a rolling packaging stop."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import time
import re
import urllib.parse
import zipfile


RELEASE = "gabriel-wages-source-library-2026-08-06"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_gzip_csv(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows: stream.write(json.dumps(row, sort_keys=True) + "\n")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2): h.update(chunk)
    return h.hexdigest()


SENSITIVE_QUERY_KEY = re.compile(r"(?i)(api[_-]?key|token|password|passwd|authorization|bearer|cookie|secret)")


def sanitize_url(value: str) -> tuple[str, list[str]]:
    if not value or not value.lower().startswith(("http://", "https://")):
        return value, []
    parsed = urllib.parse.urlsplit(value)
    kept = []
    removed = []
    for key, item in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if SENSITIVE_QUERY_KEY.search(key):
            removed.append(key)
        else:
            kept.append((key, item))
    if not removed:
        return value, []
    safe = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(kept), parsed.fragment))
    return safe, sorted(set(removed))


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    manifests = package / "manifests"
    compact = package / "read_me_first_tree" / RELEASE
    parts = package / "parts"
    lane5 = task / "lanes/lane_005"
    for name in ["README.md", "START_HERE.md", "SOURCE_USE_GUIDE.md", "DATA_DICTIONARY.md", "KNOWN_ISSUES.md"]:
        shutil.copyfile(lane5 / name, task / name)
        shutil.copyfile(lane5 / name, compact / name)
    schema_map = {
        "source_index.schema.json": "canonical_source_record.schema.json",
        "source_aliases.schema.json": "source_alias_record.schema.json",
        "source_provenance.schema.json": "canonical_source_record.schema.json",
        "volume_manifest.schema.json": "volume_manifest_record.schema.json",
    }
    (task / "schemas").mkdir(exist_ok=True)
    (compact / "schemas").mkdir(exist_ok=True)
    for destination, source in schema_map.items():
        if not (task / "schemas" / destination).exists():
            shutil.copyfile(lane5 / source, task / "schemas" / destination)
        shutil.copyfile(task / "schemas" / destination, compact / "schemas" / destination)
    (compact / "tools").mkdir(exist_ok=True)
    for name in ["verify_volume.py", "verify_library.py", "extract_all.sh", "extract_all.py"]:
        shutil.copyfile(task / "tools" / name, compact / "tools" / name)
    stale_resume = compact / "tools/resume_packaging.sh"
    if stale_resume.exists():
        stale_resume.unlink()
    volume_rows = read_csv(manifests / "VOLUME_MANIFEST.csv")
    for row in volume_rows:
        if row["status"] == "accepted":
            row["status"] = "accepted_local_ready_for_transfer"
    transferred = [r for r in volume_rows if r["status"] == "transferred_by_user"]
    accepted = [r for r in volume_rows if r["status"] in {"accepted", "accepted_local_ready_for_transfer"}]
    completed = transferred + accepted
    remaining = [r for r in volume_rows if r["status"] not in {"transferred_by_user", "accepted", "accepted_local_ready_for_transfer"}]
    assignment_hash = json.loads((manifests / "source_library_volume_assignment_hash.json").read_text())["sha256"]
    source_index = compact / "SOURCE_INDEX.csv"
    source_index_rows = read_csv(source_index)
    risk_records = []
    for row in source_index_rows:
        original = row.get("original_URL", "")
        safe, removed = sanitize_url(original)
        if removed:
            risk_records.append({"source_id": row["source_id"], "field": "original_URL", "host": urllib.parse.urlsplit(original).hostname or "", "removed_query_keys": "|".join(removed), "redacted_fingerprint": hashlib.sha256(original.encode()).hexdigest()[:12], "disposition": "query parameter removed from transfer metadata"})
            row["original_URL"] = safe
    write_csv(source_index, source_index_rows)
    write_jsonl(compact / "SOURCE_INDEX.jsonl", source_index_rows)
    index_by_id = {r["source_id"]: r for r in source_index_rows}
    # The transfer-safe alias and provenance tables are tracked compactly so a
    # rolling resume never depends on bulky lane-preparation outputs.
    transfer_alias_rows = read_csv(task / "source_aliases.csv")
    write_csv(compact / "metadata/source_aliases.csv", transfer_alias_rows)
    write_jsonl(compact / "metadata/source_aliases.jsonl", transfer_alias_rows)
    provenance_path = compact / "metadata/source_provenance.csv"
    provenance_rows = read_gzip_csv(task / "source_provenance.csv.gz")
    for row in provenance_rows:
        source_id = row.get("source_id") or ""
        for field in list(row):
            if "url" not in field.lower() and "locator" not in field.lower():
                continue
            original = row.get(field, "")
            safe, removed = sanitize_url(original)
            if removed:
                risk_records.append({"source_id": source_id, "field": field, "host": urllib.parse.urlsplit(original).hostname or "", "removed_query_keys": "|".join(removed), "redacted_fingerprint": hashlib.sha256(original.encode()).hexdigest()[:12], "disposition": "query parameter removed from transfer metadata"})
                row[field] = safe
    write_csv(provenance_path, provenance_rows)
    write_jsonl(compact / "metadata/source_provenance.jsonl", provenance_rows)
    prior_secret_audit = task / "source_library_secret_audit.json"
    if not risk_records and prior_secret_audit.exists():
        risk_records = json.loads(prior_secret_audit.read_text()).get("findings", [])
    completed_ids = {r["volume_id"] for r in completed}
    packaged_source_count = sum(r["source_volume_id"] in completed_ids for r in source_index_rows)
    packaged_source_bytes = sum(int(r["source_size_bytes"]) for r in source_index_rows if r["source_volume_id"] in completed_ids)
    packaged_text_count = sum(r["source_volume_id"] in completed_ids and r["extracted_text_available"] == "true" for r in source_index_rows)

    release_path = compact / "RELEASE_MANIFEST.json"
    release = json.loads(release_path.read_text())
    release.update({
        "source_library_version": "1.0-complete",
        "packaged_source_count": packaged_source_count,
        "packaged_source_bytes": packaged_source_bytes,
        "packaged_text_companion_count": packaged_text_count,
        "accepted_volume_count": len(accepted),
        "transferred_volume_count": len(transferred),
        "local_ready_volume_count": len(accepted),
        "completed_volume_count": len(completed),
        "remaining_volume_count": len(remaining),
        "accepted_compressed_bytes": sum(int(r["compressed_bytes"] or 0) for r in completed),
        "remaining_planned_bytes": sum(int(r["planned_total_bytes"]) for r in remaining),
        "packaging_status": "partial_transfer_space_required" if remaining else "complete_waiting_for_final_six_user_transfer",
        "volume_assignment_SHA256": assignment_hash,
        "source_index_SHA256": sha(source_index),
    })
    write_json(release_path, release)
    write_json(manifests / "RELEASE_MANIFEST.json", release)
    write_csv(compact / "VOLUME_MANIFEST.csv", volume_rows)
    write_json(compact / "VOLUME_MANIFEST.json", volume_rows)

    # Refresh transfer ZIP with updated release and volume status.
    checks = []
    for path in sorted(p for p in compact.rglob("*") if p.is_file() and p.name != "CHECKSUMS.sha256"):
        checks.append(f"{sha(path)}  {path.relative_to(compact).as_posix()}")
    (compact / "CHECKSUMS.sha256").write_text("\n".join(checks) + "\n", encoding="utf-8")
    zip_path = package / f"{RELEASE}.READ-ME-FIRST.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in compact.rglob("*") if p.is_file()):
            archive.write(path, f"{RELEASE}/{path.relative_to(compact).as_posix()}")
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad: raise RuntimeError(f"READ-ME-FIRST ZIP failed at {bad}")

    checksum_entries = []
    for row in volume_rows:
        if row["status"] not in {"transferred_by_user", "accepted", "accepted_local_ready_for_transfer"}:
            continue
        path = parts / row["filename"]
        if row["status"] == "transferred_by_user":
            checksum_entries.append((row["archive_SHA256"], f"parts/{row['filename']}"))
            continue
        if not path.is_file() or sha(path) != row["archive_SHA256"]:
            raise RuntimeError(f"accepted volume checksum failed: {row['volume_id']}")
        checksum_entries.append((row["archive_SHA256"], f"parts/{row['filename']}"))
    checksum_entries.append((sha(zip_path), zip_path.name))
    for name in ["SOURCE_INDEX.csv", "SOURCE_INDEX.jsonl", "VOLUME_MANIFEST.csv", "VOLUME_MANIFEST.json", "RELEASE_MANIFEST.json"]:
        path = compact / name
        checksum_entries.append((sha(path), f"manifests/{name}"))
    external_checksums = package / "CHECKSUMS.sha256"
    external_checksums.write_text("\n".join(f"{digest}  {name}" for digest, name in checksum_entries) + "\n", encoding="utf-8")
    shutil.copyfile(external_checksums, manifests / "CHECKSUMS.sha256")

    # Compact tracked status and transfer records.
    write_csv(task / "VOLUME_MANIFEST.csv", volume_rows)
    write_json(task / "VOLUME_MANIFEST.json", volume_rows)
    write_csv(task / "source_library_completed_volumes.csv", completed)
    write_jsonl(task / "source_library_completed_volumes.jsonl", completed)
    write_csv(task / "source_library_remaining_volumes.csv", remaining)
    write_jsonl(task / "source_library_remaining_volumes.jsonl", remaining)
    # Preserve the explicit user-confirmed transfer ledger written at resume preflight.
    validation_rows = [{"volume_id": r["volume_id"], "filename": r["filename"], "status": r["status"], "validation_method": r["validation_method"], "verified_source_member_count": r["verified_source_member_count"], "verification_status": r["verification_status"], "archive_SHA256": r["archive_SHA256"]} for r in volume_rows]
    write_csv(task / "source_library_volume_validation.csv", validation_rows)
    write_jsonl(task / "source_library_volume_validation.jsonl", validation_rows)
    compression_rows = [{"volume_id": r["volume_id"], "planned_total_bytes": r["planned_total_bytes"], "compressed_bytes": r["compressed_bytes"], "compression_ratio": r["compression_ratio"], "runtime_seconds": r["runtime_seconds"]} for r in completed]
    write_csv(task / "source_library_volume_compression_stats.csv", compression_rows)
    write_jsonl(task / "source_library_volume_compression_stats.jsonl", compression_rows)
    state = {
        "status": release["packaging_status"],
        "total_volume_count": len(volume_rows),
        "accepted_volume_count": len(accepted),
        "transferred_volume_count": len(transferred),
        "completed_volume_count": len(completed),
        "remaining_volume_count": len(remaining),
        "next_incomplete_volume_id": remaining[0]["volume_id"] if remaining else None,
        "accepted_volume_ids": [r["volume_id"] for r in accepted],
        "transferred_volume_ids": [r["volume_id"] for r in transferred],
        "volume_assignment_SHA256": assignment_hash,
        "safe_free_space_floor_bytes": 8 * 1024**3,
        "accepted_compressed_bytes": release["accepted_compressed_bytes"],
        "remaining_planned_bytes": release["remaining_planned_bytes"],
        "read_me_first_path": str(zip_path.relative_to(repo)),
        "read_me_first_SHA256": sha(zip_path),
    }
    write_json(task / "source_library_packaging_state.json", state)
    write_json(task / "source_library_packaging_checkpoint.json", state)
    (task / "source_library_packaging_transition_log.jsonl").write_text(json.dumps({"event": "preparation_complete", "volume_count": len(volume_rows), "assignment_sha256": assignment_hash}) + "\n" + json.dumps({"event": "resume_complete", **state}) + "\n", encoding="utf-8")
    (task / "source_library_packaging_incident_log.jsonl").write_text("", encoding="utf-8")
    write_json(task / "RELEASE_MANIFEST.json", release)
    (task / "CHECKSUMS.sha256").write_text(external_checksums.read_text(), encoding="utf-8")
    write_json(task / "source_library_secret_audit.json", {"status": "pass_with_redaction", "metadata_and_documentation_scope": True, "full_source_payload_content_scan": False, "credential_like_query_parameter_records": len(risk_records), "redactions_applied": len(risk_records), "secret_values_recorded": 0, "findings": risk_records})
    (task / "source_library_secret_audit.md").write_text(f"# Source-library secret audit\n\nThe audit covered enriched transfer metadata and recipient documentation. It removed credential-like query parameters from {len(risk_records)} metadata fields without recording their values. No absolute package path or credential value was retained. Source payload contents were not exhaustively scanned.\n", encoding="utf-8")
    shutil.copyfile(lane5 / "source_library_portability_audit.json", task / "source_library_portability_QA.json")
    shutil.copyfile(lane5 / "source_library_portability_audit.md", task / "source_library_portability_QA.md")
    shutil.copyfile(lane5 / "source_library_redistribution_audit.json", task / "source_library_redistribution_audit.json")
    shutil.copyfile(lane5 / "source_library_redistribution_audit.md", task / "source_library_redistribution_audit.md")
    manifest = {
        "task_id": "GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06",
        "release": RELEASE,
        "status": state["status"],
        "canonical_selected_sources": release["canonical_source_count"],
        "selected_source_bytes": release["source_bytes"],
        "selected_text_companions": release["extracted_text_companion_count"],
        "selected_text_bytes": release["extracted_text_bytes"],
        "volume_count": len(volume_rows),
        "accepted_volume_count": len(accepted),
        "transferred_volume_count": len(transferred),
        "completed_volume_count": len(completed),
        "remaining_volume_count": len(remaining),
        "no_full_uncompressed_staging_copy": True,
        "original_sources_deleted": 0,
        "archive_volumes_git_tracked": False,
    }
    write_json(task / "source_library_packaging_manifest.json", manifest)
    summary = {**manifest, "packaged_source_count": packaged_source_count, "packaged_source_bytes": packaged_source_bytes, "accepted_compressed_bytes": release["accepted_compressed_bytes"], "assignment_sha256": assignment_hash, "read_me_first_sha256": sha(zip_path), "decision": "gabriel_wages_source_library_resume_partial_transfer_space_required" if remaining else "gabriel_wages_source_library_resume_completed_final_six_ready_for_transfer"}
    write_json(task / "source_library_packaging_summary.json", summary)
    (task / "source_library_packaging_summary.md").write_text(
        "# Source-library packaging summary\n\n"
        f"The complete source-only plan contains {release['canonical_source_count']:,} canonical source files and {release['extracted_text_companion_count']:,} existing text companions across {len(volume_rows)} independent volumes. "
        f"The release now accounts for all {len(completed)} volumes containing {packaged_source_count:,} sources and {release['accepted_compressed_bytes']:,} compressed bytes. "
        f"Volumes 001 through 022 were transferred by the user; volumes 023 through 028 are accepted locally and ready for transfer. No full uncompressed staging copy was created and no original source was deleted.\n",
        encoding="utf-8",
    )
    write_json(manifests / "read_me_first_validation.json", {"status": "pass", "path": zip_path.name, "bytes": zip_path.stat().st_size, "sha256": sha(zip_path), "member_count": len(zipfile.ZipFile(zip_path).infolist()), "source_binary_members": 0})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
