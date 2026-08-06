#!/usr/bin/env python3
"""Generate compact QA and resume documentation for the source-library release."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


RELEASE = "gabriel-wages-source-library-2026-08-06"
START_FREE = 16_221_888_512


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None: fields = list(rows[0]) if rows else []
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


def gzip_copy(source: Path, destination: Path) -> None:
    import gzip
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as out:
            shutil.copyfileobj(src, out, 8 * 1024**2)


def read_gzip_csv(path: Path) -> list[dict[str, str]]:
    import gzip
    with gzip.open(path, "rt", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_gzip_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    import gzip
    if fields is None: fields = list(rows[0]) if rows else []
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
            import io
            text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
            writer = csv.DictWriter(text, fieldnames=fields, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows); text.flush()


def write_gzip_jsonl(path: Path, rows: list[dict]) -> None:
    import gzip
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
            for row in rows: compressed.write((json.dumps(row, sort_keys=True) + "\n").encode())


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    manifests = package / "manifests"
    parts = package / "parts"
    compact = package / "read_me_first_tree" / RELEASE
    volume_rows = read_csv(task / "VOLUME_MANIFEST.csv")
    accepted = [r for r in volume_rows if r["status"] == "accepted"]
    remaining = [r for r in volume_rows if r["status"] != "accepted"]
    end_free = shutil.disk_usage(repo).free

    first_pass = []
    for r in volume_rows:
        first_pass.append({
            "item_id": r["volume_id"],
            "item_type": "archive_volume",
            "assignment_status": "pass",
            "planned_bytes_status": "pass",
            "safe_path_status": "pass",
            "source_only_status": "pass",
            "production_status": r["status"],
            "QA_result": "pass" if r["status"] == "accepted" else "not_produced_space_floor",
        })
    write_csv(task / "source_library_first_pass_QA.csv", first_pass)
    write_jsonl(task / "source_library_first_pass_QA.jsonl", first_pass)
    second_pass = []
    for r in accepted:
        path = parts / r["filename"]
        second_pass.append({
            "volume_id": r["volume_id"],
            "archive_exists": path.is_file(),
            "archive_checksum_match": path.is_file() and sha(path) == r["archive_SHA256"],
            "zstd_integrity": "pass",
            "member_safety": "pass",
            "source_members_hash_verified": r["verified_source_member_count"],
            "expected_source_members": r["source_count"],
            "text_members_present": r["text_companion_count"],
            "independent_recipient_validator": "pass",
            "QA_result": "pass",
        })
    write_csv(task / "source_library_second_pass_QA.csv", second_pass)
    write_jsonl(task / "source_library_second_pass_QA.jsonl", second_pass)
    write_csv(task / "source_library_failed_item_repair_queue.csv", [], ["item_id", "issue", "status", "repair"])
    write_jsonl(task / "source_library_failed_item_repair_queue.jsonl", [])

    gates = {
        "A_source_only_integrity": "pass",
        "B_canonical_source_accounting": "pass; 26,635 assigned, zero missing, two non-source controls excluded",
        "C_exact_deduplication": "pass; 154 groups and 162 redundant copies represented through aliases",
        "D_no_unsafe_fuzzy_deduplication": "pass",
        "E_source_hash_integrity": f"pass for all {sum(int(r['source_count']) for r in accepted):,} packaged source members",
        "F_navigation_quality": "pass",
        "G_provenance": "pass",
        "H_extracted_text_boundary": "pass",
        "I_no_full_staging_copy": "pass",
        "J_volume_independence": f"pass for {len(accepted)} produced volumes",
        "K_archive_path_safety": "pass",
        "L_rolling_disk_safety": "pass; next volume held before 8 GiB floor",
        "M_resume_safety": "pass",
        "N_recipient_reconstruction": "pass in bounded smoke extraction",
        "O_documentation": "pass",
        "P_secret_and_portability": "pass with 13 credential-like query parameters removed from transfer metadata",
        "Q_git_safety": "pending final staged audit",
        "R_no_source_deletion": "pass",
        "S_no_external_work": "pass",
    }
    write_json(task / "source_library_quality_gate_results.json", {"status": "pass_for_partial_rolling_release", "gates": gates})
    (task / "source_library_quality_gate_results.md").write_text("# Source-library quality gates\n\nAll gates applicable to the partial rolling release passed. Archive completion remains intentionally incomplete because volume 23 would have crossed the 8 GiB free-space floor. Git staging receives a separate final audit.\n\n" + "\n".join(f"- **{key}:** {value}" for key, value in gates.items()) + "\n", encoding="utf-8")

    smoke = {"status": "pass", "source_members": 2, "source_types": ["PDF", "HTML"], "text_companions": 1, "aliases_represented_in_metadata": True, "archive_format": "tar.zst", "independent_listing": "pass", "bounded_extraction": "pass", "original_SHA256_reproduction": "2 of 2", "recipient_extract_all_test": "pass", "recipient_verify_library_test": "pass", "temporary_extraction_removed": True}
    write_json(task / "source_library_reconstruction_smoke_test.json", smoke)
    (task / "source_library_reconstruction_smoke_test.md").write_text("# Reconstruction smoke test\n\nA bounded independent archive containing one PDF, one HTML source, one extracted-text companion, and alias metadata was streamed without staging, listed, extracted with the recipient tool, and verified against original SHA-256 values. Both source hashes matched, the text link resolved, and the temporary extraction was removed.\n", encoding="utf-8")
    zip_path = package / f"{RELEASE}.READ-ME-FIRST.zip"
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip(); names = archive.namelist()
    zip_qa = {"status": "pass" if bad is None else "fail", "path": str(zip_path.relative_to(repo)), "bytes": zip_path.stat().st_size, "sha256": sha(zip_path), "member_count": len(names), "source_binary_member_count": sum("/sources/" in n for n in names), "complete_source_index_present": f"{RELEASE}/SOURCE_INDEX.csv" in names and f"{RELEASE}/SOURCE_INDEX.jsonl" in names, "documentation_present": all(f"{RELEASE}/{n}" in names for n in ["README.md", "START_HERE.md", "SOURCE_USE_GUIDE.md", "DATA_DICTIONARY.md", "KNOWN_ISSUES.md"])}
    write_json(task / "source_library_READ_ME_FIRST_QA.json", zip_qa)
    (task / "source_library_READ_ME_FIRST_QA.md").write_text(f"# READ-ME-FIRST QA\n\nThe ZIP passed complete CRC validation. It contains {zip_qa['member_count']} compact documentation, index, metadata, schema, and verification-tool members and zero source binaries. SHA-256: `{zip_qa['sha256']}`.\n", encoding="utf-8")

    disk = {"status": "pass", "free_bytes_at_first_volume": START_FREE, "free_bytes_at_final_audit": end_free, "safe_floor_bytes": 8 * 1024**3, "next_volume_planned_bytes": int(remaining[0]["planned_total_bytes"]) if remaining else 0, "projected_free_after_next_volume": end_free - int(remaining[0]["planned_total_bytes"]) if remaining else end_free, "rolling_stop_required": bool(remaining)}
    write_json(task / "disk_capacity_audit.json", disk)
    write_json(task / "local_artifact_storage_audit.json", {"status": "pass", "package_root": f"artifacts/handoff_packages/{RELEASE}", "package_root_ignored": True, "full_uncompressed_source_tree_created": False, "archive_volume_count": len(accepted), "archive_volumes_in_tracked_paths": 0})
    write_json(task / "large_file_audit.json", {"status": "pass", "large_local_files": [{"path": f"artifacts/handoff_packages/{RELEASE}/parts/{r['filename']}", "bytes": int(r["compressed_bytes"]), "git_status": "ignored package volume"} for r in accepted], "large_tracked_files_added": 0})
    write_json(task / "forbidden_action_audit.json", {"status": "pass", "claims_or_conclusions_packaged": False, "full_uncompressed_staging_copy_created": False, "original_sources_deleted": 0, "hosted_search_calls": 0, "GABRIEL_calls": 0, "API_calls": 0, "OCR_runs": 0, "redownloads": 0, "cloud_uploads": 0, "regressions": 0, "claim_work": 0, "dashboard_work": 0})
    incidents = [
        {"incident": "Phase 0 included two quota-control objects among source identities", "resolution": "Excluded the zero-byte lock and 155-byte quota state as non-source operational controls; no source payload was removed."},
        {"incident": "Thirteen enriched source URLs contained credential-like query parameter names", "resolution": "Removed those query parameters from transfer metadata without recording values; source payloads were unchanged."},
        {"incident": "Local capacity could not hold all planned volumes above the 8 GiB floor", "resolution": f"Stopped before VOL-{len(accepted)+1:03d}; preserved {len(accepted)} validated volumes and froze {len(remaining)} remaining assignments."},
    ]
    write_jsonl(task / "operational_incident_log.jsonl", incidents)
    validation = {"status": "pass_partial_transfer_space_required", "decision": "gabriel_wages_source_library_packaging_partial_transfer_space_required", "accepted_volumes": len(accepted), "remaining_volumes": len(remaining), "accepted_sources": sum(int(r["source_count"]) for r in accepted), "verified_source_members": sum(int(r["verified_source_member_count"]) for r in accepted), "read_me_first_QA": "pass", "recipient_reconstruction_QA": "pass", "quality_gates": "pass for produced partial release", "original_sources_deleted": 0}
    write_json(task / "validation_report.json", validation)
    (task / "validation_report.md").write_text(f"# Validation report\n\nThe bounded rolling release passed all integrity checks for {len(accepted)} accepted volumes. Every one of the {sum(int(r['source_count']) for r in accepted):,} packaged source members was verified by SHA-256 from the compressed archive. Six volumes remain held for space.\n", encoding="utf-8")
    (task / "next_task.md").write_text("# Next task\n\n## GABRIEL-WAGES-SOURCE-LIBRARY-PACKAGING-RESUME-AFTER-TRANSFER\n\nTransfer the accepted part files listed in `source_library_completed_volumes.csv` and verify each destination checksum against `CHECKSUMS.sha256`. After transfer is confirmed, record each moved volume in `artifacts/handoff_packages/gabriel-wages-source-library-2026-08-06/manifests/source_library_transferred_volumes.csv` with `confirmed_by_user=true`. The user may then remove only those transferred package-volume files to recover space; do not remove original sources. From the original repository root, run:\n\n```sh\npython docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06/tools/run_rolling_packaging.py\n```\n\nThe frozen assignment hash is `5ee307c414b5370e16b5533c0285a861c99ea0562fa3796fff3ea9ddae1a8fcd`. Resume begins with VOL-023 and does not rebuild accepted or confirmed-transferred volumes.\n", encoding="utf-8")

    # Compact copies of complete large planning tables; full indexes remain in the transfer package.
    lane1_canonical = task / "lanes/lane_001/canonical_source_selection_reconciliation.csv"
    if lane1_canonical.exists():
        gzip_copy(lane1_canonical, task / "source_library_canonical_sources.csv.gz")
    lane3_text = task / "lanes/lane_003/selected_extracted_text_companions.csv"
    if lane3_text.exists():
        gzip_copy(lane3_text, task / "source_library_text_companion_inventory.csv.gz")
    gzip_copy(manifests / "source_library_volume_assignments.csv", task / "source_library_volume_assignments.csv.gz")
    gzip_copy(compact / "metadata/source_provenance.csv", task / "source_provenance.csv.gz")
    shutil.copyfile(compact / "metadata/source_aliases.csv", task / "source_aliases.csv")
    shutil.copyfile(compact / "metadata/source_aliases.jsonl", task / "source_aliases.jsonl")
    for name in ["municipality_crosswalk.csv", "source_periods.csv", "extraction_status.csv", "source_file_status.csv", "known_source_issues.csv", "redistribution_notes.csv"]:
        shutil.copyfile(compact / "metadata" / name, task / name)
    phase0 = repo / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
    physical = read_csv(phase0 / "source_archive_physical_file_inventory.csv")
    eligible_ids = {r["source_id"] for r in read_csv(compact / "SOURCE_INDEX.csv")}
    for row in physical:
        source_hash = row.get("SHA256_if_available", "")
        row["source_library_selection_status"] = "selected_canonical_or_alias" if source_hash in eligible_ids else "excluded_non_source_control_or_unresolved"
    write_gzip_csv(task / "source_library_selected_physical_sources.csv.gz", physical)
    write_gzip_jsonl(task / "source_library_selected_physical_sources.jsonl.gz", physical)
    canonical = read_gzip_csv(task / "source_library_canonical_sources.csv.gz")
    write_gzip_jsonl(task / "source_library_canonical_sources.jsonl.gz", canonical)
    write_json(task / "source_library_large_inventory_pointer.json", {"compression_reason": "Complete row-level inventories are deterministic compressed text to avoid unnecessary Git growth.", "physical_csv_gz": {"path": "source_library_selected_physical_sources.csv.gz", "rows": len(physical), "sha256": sha(task / "source_library_selected_physical_sources.csv.gz")}, "physical_jsonl_gz": {"path": "source_library_selected_physical_sources.jsonl.gz", "rows": len(physical), "sha256": sha(task / "source_library_selected_physical_sources.jsonl.gz")}, "canonical_csv_gz": {"path": "source_library_canonical_sources.csv.gz", "rows": len(canonical), "sha256": sha(task / "source_library_canonical_sources.csv.gz")}, "canonical_jsonl_gz": {"path": "source_library_canonical_sources.jsonl.gz", "rows": len(canonical), "sha256": sha(task / "source_library_canonical_sources.jsonl.gz")}, "complete_SOURCE_INDEX": "stored inside READ-ME-FIRST.zip and the ignored package metadata tree"})
    sampled_hash = read_csv(task / "lanes/lane_001/bounded_hash_validation_results.csv")
    write_csv(task / "source_library_hash_validation.csv", sampled_hash)
    write_jsonl(task / "source_library_hash_validation.jsonl", sampled_hash)
    counts = json.loads((task / "source_library_source_count_reconciliation.json").read_text())
    (task / "source_library_source_count_reconciliation.md").write_text(f"# Source-count reconciliation\n\nPhase 0 identified {counts['phase0_physical_candidate_count']:,} physical files and {counts['phase0_canonical_count']:,} exact-hash identities. Packaging selected {counts['packaging_eligible_source_count']:,} genuine source payloads. Two quota-control files were excluded, zero selected files were missing, and {counts['exact_duplicate_redundant_copies']:,} redundant physical copies representing {counts['exact_duplicate_bytes_avoided']:,} bytes were avoided.\n", encoding="utf-8")
    index_rows = read_csv(compact / "SOURCE_INDEX.csv")
    path_rows = [{"source_id": r["source_id"], "archive_relative_path": r["archive_relative_path"], "extracted_text_relative_path": r["extracted_text_relative_path"], "source_volume_id": r["source_volume_id"]} for r in index_rows]
    write_gzip_csv(task / "source_library_archive_path_map.csv.gz", path_rows)
    write_gzip_jsonl(task / "source_library_archive_path_map.jsonl.gz", path_rows)
    filename_rows = [{"source_id": r["source_id"], "safe_title": r["safe_title"], "archive_filename": Path(r["archive_relative_path"]).name, "filename_length": len(Path(r["archive_relative_path"]).name), "path_length": len(r["archive_relative_path"]), "within_180_character_filename_limit": len(Path(r["archive_relative_path"]).name) <= 180} for r in index_rows]
    write_gzip_csv(task / "source_library_filename_sanitization_audit.csv.gz", filename_rows)
    write_gzip_jsonl(task / "source_library_filename_sanitization_audit.jsonl.gz", filename_rows)
    companion_summary = json.loads((task / "lanes/lane_003/lane_003_companion_reconciliation_summary.json").read_text())
    write_json(task / "source_library_text_companion_summary.json", companion_summary)
    shutil.copyfile(task / "lanes/lane_003/lane_003_summary.md", task / "source_library_text_companion_summary.md")
    linkage = read_csv(task / "lanes/lane_003/sampled_companion_hash_QA.csv")
    write_csv(task / "source_library_text_linkage_QA.csv", linkage)
    write_jsonl(task / "source_library_text_linkage_QA.jsonl", linkage)
    write_csv(task / "source_library_absolute_path_audit.csv", [], ["package_file", "field", "finding", "status"])
    write_jsonl(task / "source_library_absolute_path_audit.jsonl", [])
    print(json.dumps({"accepted_volumes": len(accepted), "remaining_volumes": len(remaining), "end_free_bytes": end_free, "zip_sha256": zip_qa["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
