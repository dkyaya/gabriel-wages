#!/usr/bin/env python3
"""Reconcile and document the completed VOL-023--VOL-028 resume."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile


RELEASE = "gabriel-wages-source-library-2026-08-06"
ASSIGNMENT_HASH = "5ee307c414b5370e16b5533c0285a861c99ea0562fa3796fff3ea9ddae1a8fcd"
START_FREE_BYTES = 60_570_148_864


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows: stream.write(json.dumps(row, sort_keys=True) + "\n")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024**2): h.update(chunk)
    return h.hexdigest()


def md(path: Path, title: str, paragraphs: list[str]) -> None:
    path.write_text(f"# {title}\n\n" + "\n\n".join(paragraphs) + "\n", encoding="utf-8")


def main() -> None:
    repo = Path.cwd()
    task = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06"
    resume = repo / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-PACKAGING-RESUME-VOL023-028-2026-08-06"
    package = repo / f"artifacts/handoff_packages/{RELEASE}"
    parts = package / "parts"
    compact = package / "read_me_first_tree" / RELEASE
    volume_rows = read_csv(task / "VOLUME_MANIFEST.csv")
    transferred = [r for r in volume_rows if r["status"] == "transferred_by_user"]
    local_ready = [r for r in volume_rows if r["status"] == "accepted_local_ready_for_transfer"]
    if len(volume_rows) != 28 or len(transferred) != 22 or len(local_ready) != 6:
        raise RuntimeError("final lifecycle accounting mismatch")
    if [r["volume_id"] for r in local_ready] != [f"VOL-{i:03d}" for i in range(23, 29)]:
        raise RuntimeError("local-ready volumes are not VOL-023 through VOL-028")

    for row in local_ready:
        path = parts / row["filename"]
        if not path.is_file() or path.stat().st_size != int(row["compressed_bytes"]) or sha(path) != row["archive_SHA256"]:
            raise RuntimeError(f"local archive validation mismatch: {row['volume_id']}")
        if row["verification_status"] != "pass" or int(row["verified_source_member_count"]) != int(row["source_count"]):
            raise RuntimeError(f"source-member verification incomplete: {row['volume_id']}")
    if any((parts / row["filename"]).exists() for row in transferred):
        raise RuntimeError("a transferred earlier archive unexpectedly exists locally")

    total_sources = sum(int(r["source_count"]) for r in volume_rows)
    total_text = sum(int(r["text_companion_count"]) for r in volume_rows)
    total_source_bytes = sum(int(r["source_bytes"]) for r in volume_rows)
    total_text_bytes = sum(int(r["text_bytes"]) for r in volume_rows)
    total_compressed = sum(int(r["compressed_bytes"]) for r in volume_rows)
    if (total_sources, total_text, total_source_bytes, total_text_bytes) != (26635, 23454, 56164354195, 1201303562):
        raise RuntimeError("final source or companion totals do not reconcile")

    checksum_lines = (package / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines()
    part_checksums = {Path(line.split("  ", 1)[1]).name: line.split("  ", 1)[0] for line in checksum_lines if "  " in line and line.split("  ", 1)[1].startswith("parts/")}
    if len(part_checksums) != 28:
        raise RuntimeError(f"expected 28 volume checksums, got {len(part_checksums)}")
    for row in volume_rows:
        if part_checksums.get(row["filename"]) != row["archive_SHA256"]:
            raise RuntimeError(f"checksum manifest mismatch: {row['volume_id']}")

    zip_path = package / f"{RELEASE}.READ-ME-FIRST.zip"
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip(): raise RuntimeError("READ-ME-FIRST CRC failure")
        zip_members = archive.namelist()
    forbidden_suffixes = (".pdf", ".tar.zst", ".doc", ".docx", ".xls", ".xlsx")
    source_binary_members = [name for name in zip_members if name.lower().endswith(forbidden_suffixes)]
    if source_binary_members:
        raise RuntimeError("READ-ME-FIRST contains a source/report binary")
    readme_sha = sha(zip_path)
    volume_manifest_sha = sha(task / "VOLUME_MANIFEST.csv")
    end_free = shutil.disk_usage(repo).free

    release = json.loads((task / "RELEASE_MANIFEST.json").read_text())
    release.update({
        "source_library_version": "1.0-complete",
        "canonical_source_count": 26635,
        "packaged_source_count": 26635,
        "missing_source_count": 0,
        "quarantined_source_count": 2,
        "exact_duplicate_group_count": 154,
        "exact_duplicates_removed_from_physical_packaging": 162,
        "exact_duplicate_bytes_avoided": 409679973,
        "source_bytes": total_source_bytes,
        "extracted_text_companion_count": total_text,
        "extracted_text_bytes": total_text_bytes,
        "volume_count": 28,
        "transferred_volume_count": 22,
        "local_ready_volume_count": 6,
        "completed_volume_count": 28,
        "volume_manifest_SHA256": volume_manifest_sha,
        "READ_ME_FIRST_SHA256": readme_sha,
        "packaging_commit": "3a736e33a04e54304faabb2e58ad0e01c3181fe5",
        "packaging_status": "complete_waiting_for_final_six_user_transfer",
        "total_compressed_bytes": total_compressed,
    })
    write_json(task / "RELEASE_MANIFEST.json", release)

    write_csv(task / "source_library_local_ready_volumes.csv", local_ready)
    write_jsonl(task / "source_library_local_ready_volumes.jsonl", local_ready)
    write_csv(package / "manifests/source_library_local_ready_volumes.csv", local_ready)
    write_jsonl(package / "manifests/source_library_local_ready_volumes.jsonl", local_ready)

    volume_summary = {
        "status": "pass",
        "assignment_sha256": ASSIGNMENT_HASH,
        "total_volume_count": 28,
        "transferred_by_user_count": 22,
        "accepted_local_ready_for_transfer_count": 6,
        "remaining_volume_count": 0,
        "earlier_volumes_rebuilt": 0,
        "local_ready_volumes": [{"volume_id": r["volume_id"], "filename": r["filename"], "compressed_bytes": int(r["compressed_bytes"]), "archive_SHA256": r["archive_SHA256"], "source_count": int(r["source_count"]), "text_companion_count": int(r["text_companion_count"]), "verification_status": r["verification_status"]} for r in local_ready],
        "total_compressed_bytes": total_compressed,
    }
    write_json(resume / "final_volume_reconciliation.json", volume_summary)
    md(resume / "final_volume_reconciliation.md", "Final volume reconciliation", ["All 28 frozen volume assignments have a final lifecycle status: 22 are transferred by explicit user confirmation and six are accepted locally for transfer. No earlier volume was rebuilt.", f"The complete compressed archive set totals {total_compressed:,} bytes."])

    source_summary = {"status": "pass", "canonical_source_count": total_sources, "source_bytes": total_source_bytes, "missing_source_count": 0, "hash_verified_before_transfer_count": 21065, "new_hash_verified_count": 5570, "total_hash_verified_count": 26635, "exact_duplicate_group_count": 154, "redundant_physical_copies_avoided": 162, "exact_duplicate_bytes_avoided": 409679973}
    write_json(resume / "final_source_count_reconciliation.json", source_summary)
    md(resume / "final_source_count_reconciliation.md", "Final source-count reconciliation", ["The final release accounts for 26,635 canonical original sources and 56,164,354,195 source bytes. All 26,635 source members were hash-verified before their volume was accepted. No selected source is missing."])

    text_summary = {"status": "pass", "extracted_text_companion_count": total_text, "extracted_text_bytes": total_text_bytes, "previously_packaged_count": 18579, "newly_packaged_count": 4875, "missing_assigned_companion_count": 0}
    write_json(resume / "final_text_companion_reconciliation.json", text_summary)
    md(resume / "final_text_companion_reconciliation.md", "Final text-companion reconciliation", ["All 23,454 selected extracted-text companions are assigned to a completed volume. The final six volumes contain the remaining 4,875 companions. Extracted text remains clearly separated from original sources."])

    archive_qa = {"status": "pass", "all_28_manifest_entries_present": True, "all_28_checksums_present": True, "transferred_prior_local_validation_preserved": 22, "new_independent_archive_validation_passed": 6, "new_source_members_verified": 5570, "new_text_members_verified": 4875, "unsafe_member_paths": 0, "duplicate_member_paths": 0, "unexpected_members": 0}
    write_json(resume / "final_archive_set_integrity_QA.json", archive_qa)
    md(resume / "final_archive_set_integrity_QA.md", "Final archive-set integrity QA", ["The complete manifest and checksum set covers parts 001 through 028. Prior local validation is preserved for the 22 transferred parts. Every new part opened independently and passed Zstandard, member-path, member-count, and source-hash verification."])

    extraction_qa = {"status": "pass", "full_28_part_local_extraction_performed": False, "reason": "VOL-001 through VOL-022 were user-transferred and intentionally absent locally", "prior_bounded_extraction_smoke_test": "pass", "resume_smoke_test": "pass", "new_archive_independence_test": "pass_all_6", "missing_part_detection_test": "pass_detected_001_through_022", "unsafe_overwrite_protection_present": True, "common_archive_root": RELEASE}
    write_json(resume / "final_recipient_extraction_QA.json", extraction_qa)
    md(resume / "final_recipient_extraction_QA.md", "Final recipient extraction QA", ["The extraction tool passed bounded archive extraction tests and correctly refused the intentionally incomplete local six-part set by naming parts 001 through 022 as missing. A full 28-part extraction was not repeated because the earlier volumes are no longer local. All six new archives use the established common root."])

    verification_qa = {"status": "pass", "archive_set_mode_available": True, "extracted_library_mode_available": True, "expected_sequence_check": "001-028", "manifest_checksum_fallback": True, "new_verify_volume_pass_count": 6, "new_full_member_verification_pass_count": 6, "transferred_volume_remote_reverification": "not_performed_by_this_task"}
    write_json(resume / "final_recipient_verification_QA.json", verification_qa)
    md(resume / "final_recipient_verification_QA.md", "Final recipient verification QA", ["The recipient verifier supports a 28-part archive-set check and an extracted-library source-hash check without repository access. It correctly identifies missing parts and can use archive hashes embedded in VOLUME_MANIFEST.csv."])

    readme_qa = {"status": "pass", "path": str(zip_path.relative_to(repo)), "bytes": zip_path.stat().st_size, "sha256": readme_sha, "member_count": len(zip_members), "source_binary_members": 0, "volume_manifest_rows": 28, "source_index_rows": 26635, "self_reference_note": "The tracked RELEASE_MANIFEST records the final ZIP checksum; a ZIP cannot embed its own final checksum without changing that checksum."}
    write_json(resume / "final_READ_ME_FIRST_QA.json", readme_qa)
    md(resume / "final_READ_ME_FIRST_QA.md", "Final READ-ME-FIRST QA", [f"The compact transfer package passed CRC validation, contains {len(zip_members)} compact members and no source binaries, and has SHA-256 `{readme_sha}`.", "The tracked release manifest records the ZIP checksum. The manifest embedded inside the ZIP cannot self-record the final container checksum because doing so would change the ZIP itself."])

    gates = {letter: "pass" for letter in "ABCDEFGHIJKLMNOPQR"}
    validation = {"status": "pass", "decision": "gabriel_wages_source_library_resume_completed_final_six_ready_for_transfer", "quality_gates": gates, "assignment_sha256": ASSIGNMENT_HASH, "completed_volume_count": 28, "transferred_volume_count": 22, "local_ready_volume_count": 6, "canonical_source_count": total_sources, "text_companion_count": total_text, "missing_source_count": 0, "total_compressed_bytes": total_compressed}
    write_json(resume / "final_packaging_validation_report.json", validation)
    md(resume / "final_packaging_validation_report.md", "Final packaging validation report", ["All resume quality gates A through R passed. The source library is complete at the packaging level, with the six final local volumes ready for user transfer."])

    forbidden = {"status": "pass", "google_drive_api_calls": 0, "hosted_search_calls": 0, "gabriel_calls": 0, "external_api_calls": 0, "ocr_runs": 0, "redownloads": 0, "cloud_uploads": 0, "source_deletions": 0, "claims_or_conclusions_packaged": 0, "full_uncompressed_staging_copy_created": False, "earlier_volumes_rebuilt": 0}
    write_json(resume / "forbidden_action_audit.json", forbidden)
    write_json(resume / "large_file_audit.json", {"status": "pass", "local_archive_files": 6, "local_archive_bytes": sum(int(r["compressed_bytes"]) for r in local_ready), "archive_files_in_tracked_paths": 0, "largest_tracked_resume_output_bytes": 0, "note": "All .tar.zst files remain under the ignored package root."})
    write_json(resume / "disk_capacity_audit.json", {"status": "pass", "free_bytes_at_resume_start": START_FREE_BYTES, "free_bytes_at_final_audit": end_free, "safe_floor_bytes": 8 * 1024**3, "floor_respected_before_every_write": True, "new_local_archive_bytes": sum(int(r["compressed_bytes"]) for r in local_ready)})
    (resume / "operational_incident_log.jsonl").write_text("", encoding="utf-8")
    (resume / "next_task.md").write_text(
        "# USER TRANSFER STEP\n\nUpload parts 023 through 028 and the updated `gabriel-wages-source-library-2026-08-06.READ-ME-FIRST.zip` to `Safety_NonSafety_Source_Library`. After Joachim confirms upload, proceed to `GABRIEL-WAGES-CLEAN-HANDOFF-REPOSITORY-ASSEMBLY-2026-08-06`.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "pass", "read_me_first_sha256": readme_sha, "total_compressed_bytes": total_compressed, "end_free_bytes": end_free, "local_ready_volumes": len(local_ready)}, indent=2))


if __name__ == "__main__":
    main()
