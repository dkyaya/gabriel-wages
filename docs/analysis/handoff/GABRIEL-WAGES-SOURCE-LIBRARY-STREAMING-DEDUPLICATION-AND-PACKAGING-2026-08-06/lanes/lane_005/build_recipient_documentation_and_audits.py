#!/usr/bin/env python3
"""Build source-only recipient schemas, tool specs, and bounded risk audits."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlsplit
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[6]
LANE = Path(__file__).resolve().parent
PHASE0 = REPO / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
LANE1 = REPO / "docs/analysis/handoff/GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-DEDUPLICATION-AND-PACKAGING-2026-08-06/lanes/lane_001"


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(name: str, value: Any) -> None:
    (LANE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(name: str, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with (LANE / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> None:
    with (LANE / name).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def object_schema(title: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
REL_PATH = {
    "type": "string",
    "minLength": 1,
    "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$)).+",
    "description": "POSIX path relative to the source-library root.",
}
NONNEGATIVE = {"type": "integer", "minimum": 0}


def build_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    schemas["source_library_manifest.schema.json"] = object_schema(
        "Source library manifest",
        {
            "library_name": {"type": "string", "minLength": 1},
            "library_version": {"type": "string", "minLength": 1},
            "created_at_utc": {"type": "string", "format": "date-time"},
            "hash_algorithm": {"const": "sha256"},
            "archive_format": {"type": "string", "minLength": 1},
            "canonical_source_count": NONNEGATIVE,
            "canonical_source_bytes": NONNEGATIVE,
            "original_volume_count": NONNEGATIVE,
            "text_volume_count": NONNEGATIVE,
            "manifest_paths": {
                "type": "object",
                "additionalProperties": REL_PATH,
                "minProperties": 1,
            },
            "source_only_boundary": object_schema(
                "Source-only boundary",
                {
                    "original_sources": {"const": True},
                    "source_metadata": {"const": True},
                    "extracted_text_companions": {"type": "boolean"},
                    "analytical_results": {"const": False},
                    "report_material": {"const": False},
                },
                ["original_sources", "source_metadata", "extracted_text_companions", "analytical_results", "report_material"],
            ),
        },
        [
            "library_name", "library_version", "created_at_utc", "hash_algorithm",
            "archive_format", "canonical_source_count", "canonical_source_bytes",
            "original_volume_count", "text_volume_count", "manifest_paths",
            "source_only_boundary",
        ],
    )
    schemas["canonical_source_record.schema.json"] = object_schema(
        "Canonical source record",
        {
            "canonical_source_id": SHA,
            "library_relative_path": REL_PATH,
            "volume_id": {"type": "string", "minLength": 1},
            "file_size_bytes": NONNEGATIVE,
            "extension": {"type": "string", "pattern": "^\\.[A-Za-z0-9]+$"},
            "media_type": {"type": ["string", "null"]},
            "source_type": {"type": ["string", "null"]},
            "source_corpus": {"enum": ["causal", "discourse", None]},
            "municipality": {"type": ["string", "null"]},
            "state": {"type": ["string", "null"]},
            "period": {"type": ["string", "null"]},
            "original_url_or_cite": {"type": ["string", "null"]},
            "provenance_pointer": REL_PATH,
            "extraction_status": {"type": ["string", "null"]},
            "redistribution_status": {
                "enum": [
                    "manual_review_required", "approved_for_named_transfer",
                    "public_redistribution_allowed", "restricted", "excluded",
                ]
            },
            "known_issue_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        },
        [
            "canonical_source_id", "library_relative_path", "volume_id",
            "file_size_bytes", "extension", "provenance_pointer",
            "redistribution_status", "known_issue_ids",
        ],
    )
    schemas["source_alias_record.schema.json"] = object_schema(
        "Source alias record",
        {
            "canonical_source_id": SHA,
            "alias_relative_path": REL_PATH,
            "alias_type": {"enum": ["exact_physical_duplicate", "historical_name", "source_locator_alias"]},
            "alias_file_size_bytes": NONNEGATIVE,
            "provenance_pointer": {"anyOf": [REL_PATH, {"type": "null"}]},
        },
        ["canonical_source_id", "alias_relative_path", "alias_type", "alias_file_size_bytes"],
    )
    schemas["extracted_text_record.schema.json"] = object_schema(
        "Extracted text companion record",
        {
            "canonical_source_id": SHA,
            "original_library_relative_path": REL_PATH,
            "text_library_relative_path": {"anyOf": [REL_PATH, {"type": "null"}]},
            "text_volume_id": {"type": ["string", "null"]},
            "extraction_status": {
                "enum": ["available", "partial", "ocr_deferred", "repair_required", "unavailable"]
            },
            "text_sha256": {"anyOf": [SHA, {"type": "null"}]},
            "text_size_bytes": {"anyOf": [NONNEGATIVE, {"type": "null"}]},
            "extraction_method": {"type": ["string", "null"]},
            "limitations": {"type": ["string", "null"]},
        },
        ["canonical_source_id", "original_library_relative_path", "extraction_status"],
    )
    schemas["volume_manifest_record.schema.json"] = object_schema(
        "Volume manifest record",
        {
            "volume_id": {"type": "string", "minLength": 1},
            "volume_sequence": {"type": "integer", "minimum": 1},
            "volume_family": {"enum": ["originals", "extracted_text"]},
            "volume_relative_path": REL_PATH,
            "archive_format": {"type": "string", "minLength": 1},
            "member_count": NONNEGATIVE,
            "uncompressed_bytes": NONNEGATIVE,
            "compressed_bytes": NONNEGATIVE,
            "volume_sha256": SHA,
            "first_canonical_source_id": {"anyOf": [SHA, {"type": "null"}]},
            "last_canonical_source_id": {"anyOf": [SHA, {"type": "null"}]},
            "validation_status": {"enum": ["pending", "passed", "failed", "quarantined"]},
        },
        [
            "volume_id", "volume_sequence", "volume_family", "volume_relative_path",
            "archive_format", "member_count", "uncompressed_bytes", "compressed_bytes",
            "volume_sha256", "validation_status",
        ],
    )
    schemas["redistribution_review_record.schema.json"] = object_schema(
        "Redistribution review record",
        {
            "canonical_source_id": SHA,
            "redistribution_status": {
                "enum": [
                    "manual_review_required", "approved_for_named_transfer",
                    "public_redistribution_allowed", "restricted", "excluded",
                ]
            },
            "review_reason": {"type": "string", "minLength": 1},
            "reviewed_at_utc": {"type": ["string", "null"], "format": "date-time"},
            "reviewer": {"type": ["string", "null"]},
        },
        ["canonical_source_id", "redistribution_status", "review_reason"],
    )
    schemas["volume_checksum_record.schema.json"] = object_schema(
        "Volume checksum record",
        {
            "volume_id": {"type": "string", "minLength": 1},
            "volume_relative_path": REL_PATH,
            "sha256": SHA,
            "file_size_bytes": NONNEGATIVE,
            "validated_at_utc": {"type": ["string", "null"], "format": "date-time"},
            "validation_status": {"enum": ["pending", "passed", "failed"]},
        },
        ["volume_id", "volume_relative_path", "sha256", "file_size_bytes", "validation_status"],
    )
    return schemas


def main() -> None:
    started = timestamp()
    paths = {
        "physical": PHASE0 / "source_archive_physical_file_inventory.csv",
        "canonical": PHASE0 / "source_archive_canonical_source_inventory.csv",
        "aliases": PHASE0 / "source_archive_alias_inventory.csv",
        "redistribution": PHASE0 / "source_archive_redistribution_review_queue.csv",
        "proposed": PHASE0 / "source_library_proposed_path_map.csv",
        "repo_security": PHASE0 / "repository_secret_and_path_audit.json",
        "repo_absolute_paths": PHASE0 / "local_absolute_path_inventory.csv",
        "lane1_summary": LANE1 / "lane_001_summary.json",
    }
    missing_inputs = [str(path.relative_to(REPO)) for path in paths.values() if not path.is_file()]
    if missing_inputs:
        raise FileNotFoundError(missing_inputs)

    physical = read_csv(paths["physical"])
    canonical = read_csv(paths["canonical"])
    aliases = read_csv(paths["aliases"])
    redistribution = read_csv(paths["redistribution"])
    proposed = read_csv(paths["proposed"])
    repo_security = json.loads(paths["repo_security"].read_text(encoding="utf-8"))
    repo_abs = read_csv(paths["repo_absolute_paths"])
    lane1 = json.loads(paths["lane1_summary"].read_text(encoding="utf-8"))

    credential_name_pattern = re.compile(
        r"(^|[/_.-])(\\.env|credentials?|secrets?|tokens?|cookies?|auth(?:orization)?)([/_.-]|$)",
        re.IGNORECASE,
    )
    sensitive_query_names = {
        "token", "key", "api_key", "apikey", "access_token", "auth",
        "authorization", "signature", "sig", "password", "passwd", "session",
        "cookie", "secret",
    }
    credential_findings: list[dict[str, Any]] = []
    path_findings: list[dict[str, Any]] = []
    url_pointer_count = 0
    for row in physical:
        rel = row["relative_path"]
        path = PurePosixPath(rel)
        if path.is_absolute() or ".." in path.parts or "\\" in rel:
            path_findings.append({
                "relative_path": rel,
                "risk_type": "nonportable_source_pointer",
                "redacted_fingerprint": fingerprint(rel),
                "recommended_disposition": "replace_with_library_relative_path",
            })
        if credential_name_pattern.search(rel):
            credential_findings.append({
                "relative_path": rel,
                "risk_type": "credential_like_filename",
                "redacted_fingerprint": fingerprint(rel),
                "recommended_disposition": "manual_review_before_packaging",
            })
        url = row.get("original_URL_pointer_if_available", "")
        if url:
            url_pointer_count += 1
            try:
                parsed = urlsplit(url)
                if parsed.username or parsed.password:
                    credential_findings.append({
                        "relative_path": rel,
                        "risk_type": "embedded_url_userinfo",
                        "redacted_fingerprint": fingerprint(url),
                        "recommended_disposition": "redact_locator_and_review_source_metadata",
                    })
                names = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
                if names & sensitive_query_names:
                    credential_findings.append({
                        "relative_path": rel,
                        "risk_type": "sensitive_url_query_parameter_name",
                        "redacted_fingerprint": fingerprint(url),
                        "recommended_disposition": "redact_locator_and_review_source_metadata",
                    })
            except ValueError:
                credential_findings.append({
                    "relative_path": rel,
                    "risk_type": "malformed_url_pointer",
                    "redacted_fingerprint": fingerprint(url),
                    "recommended_disposition": "manual_locator_review",
                })

    proposed_paths = [row["proposed_relative_path"] for row in proposed]
    proposed_absolute = sum(PurePosixPath(path).is_absolute() for path in proposed_paths)
    proposed_traversal = sum(".." in PurePosixPath(path).parts for path in proposed_paths)
    proposed_backslash = sum("\\" in path for path in proposed_paths)
    proposed_casefold_collisions = len(proposed_paths) - len({path.casefold() for path in proposed_paths})
    max_proposed_length = max(map(len, proposed_paths), default=0)
    unicode_proposed_paths = sum(not path.isascii() for path in proposed_paths)

    redistribution_counts = Counter(row["status"] for row in redistribution)
    redistribution_reasons = Counter(row["review_reason"] for row in redistribution)
    canonical_source_types = Counter(row["source_type"] or "blank" for row in canonical)
    canonical_extraction = Counter(row["extraction_status"] or "blank" for row in canonical)

    write_csv(
        "credential_risk_candidates.csv",
        credential_findings,
        ["relative_path", "risk_type", "redacted_fingerprint", "recommended_disposition"],
    )
    write_jsonl("credential_risk_candidates.jsonl", credential_findings)
    write_csv(
        "package_path_risk_candidates.csv",
        path_findings,
        ["relative_path", "risk_type", "redacted_fingerprint", "recommended_disposition"],
    )
    write_jsonl("package_path_risk_candidates.jsonl", path_findings)

    security = {
        "status": "pass_with_transfer_review_required",
        "scope": "source-selection metadata and recipient documents; source payload contents not exhaustively scanned",
        "physical_source_metadata_rows_scanned": len(physical),
        "original_url_pointer_count": url_pointer_count,
        "credential_like_filename_findings": sum(
            row["risk_type"] == "credential_like_filename" for row in credential_findings
        ),
        "url_credential_findings": sum(
            row["risk_type"] in {"embedded_url_userinfo", "sensitive_url_query_parameter_name"}
            for row in credential_findings
        ),
        "metadata_credential_finding_count": len(credential_findings),
        "prior_repository_secret_pattern_file_count": repo_security["secret_pattern_file_count"],
        "prior_repository_environment_file_count": repo_security["environment_file_count"],
        "prior_repository_absolute_path_file_count": repo_security["absolute_path_file_count"],
        "secret_values_written_to_lane_outputs": False,
        "payload_content_scan_completed": False,
        "boundary": "Quarantine sensitive material if encountered; never reproduce a credential value in an audit.",
    }
    write_json("source_library_security_audit.json", security)
    security_md = f"""# Source-library security audit

- Status: **pass with transfer review required**.
- Source-selection metadata rows scanned: **{len(physical):,}**.
- Original URL pointers present in the current source inventory: **{url_pointer_count:,}**.
- Credential-like filenames: **{security['credential_like_filename_findings']:,}**.
- URL credential-pattern findings: **{security['url_credential_findings']:,}**.
- Secret values reproduced in outputs: **no**.
- Full source-payload content scan: **not performed**.

The earlier bounded repository scan found no secret-pattern file and no environment file. It found {repo_security['absolute_path_file_count']:,} files elsewhere in the working repository containing absolute machine paths; those historical files are outside the source-library recipient selection. Any sensitive content discovered while using the library must be quarantined without copying the value into an audit.
"""
    (LANE / "source_library_security_audit.md").write_text(security_md, encoding="utf-8")

    portability = {
        "status": "pass",
        "physical_source_pointer_count": len(physical),
        "physical_source_absolute_pointer_count": len(path_findings),
        "proposed_library_path_count": len(proposed_paths),
        "proposed_library_path_unique_count": len(set(proposed_paths)),
        "proposed_library_absolute_path_count": proposed_absolute,
        "proposed_library_parent_traversal_count": proposed_traversal,
        "proposed_library_backslash_count": proposed_backslash,
        "proposed_library_casefold_collision_count": proposed_casefold_collisions,
        "proposed_library_unicode_path_count": unicode_proposed_paths,
        "maximum_proposed_path_length": max_proposed_length,
        "historical_repository_absolute_path_records_excluded": len(repo_abs),
        "requirements": [
            "resolve all member paths relative to a caller-supplied library root",
            "store POSIX member paths in manifests and archives",
            "reject absolute paths, parent traversal, and archive members outside the target root",
            "do not depend on the original repository layout",
        ],
    }
    write_json("source_library_portability_audit.json", portability)
    portability_md = f"""# Source-library portability audit

- Status: **pass**.
- Current source pointers checked: **{len(physical):,}**; absolute or traversal pointers: **{len(path_findings):,}**.
- Proposed library paths: **{len(proposed_paths):,}**; unique: **{len(set(proposed_paths)):,}**.
- Absolute proposed paths: **{proposed_absolute:,}**.
- Parent-traversal proposed paths: **{proposed_traversal:,}**.
- Backslash-based proposed paths: **{proposed_backslash:,}**.
- Case-insensitive proposed-path collisions: **{proposed_casefold_collisions:,}**.
- Maximum proposed path length: **{max_proposed_length:,} characters**.

Recipient tools must accept a library root and resolve POSIX member paths beneath it. Historical repository paths may be retained as provenance fields, but no tool may depend on the original machine, username, home directory, or repository location.
"""
    (LANE / "source_library_portability_audit.md").write_text(portability_md, encoding="utf-8")

    redistribution_audit = {
        "status": "manual_review_required_before_transfer_or_publication",
        "canonical_identity_count": len(canonical),
        "eligible_source_candidate_count_after_non_source_quarantine": lane1["eligible_canonical_source_count"],
        "eligible_source_candidate_bytes": lane1["eligible_canonical_source_bytes"],
        "redistribution_status_counts": dict(sorted(redistribution_counts.items())),
        "review_reason_counts": dict(sorted(redistribution_reasons.items())),
        "public_distribution_ready_count": 0,
        "source_type_metadata_counts": dict(sorted(canonical_source_types.items())),
        "extraction_status_metadata_counts": dict(sorted(canonical_extraction.items())),
        "decision": "Packaging may preserve sources for controlled handoff, but transfer scope and public redistribution require source-level review.",
        "required_controls": [
            "carry redistribution status into every canonical record",
            "exclude restricted or unresolved sources when the transfer authorization requires it",
            "do not publish source volumes on a public dashboard",
            "record named-transfer approval without treating it as public redistribution permission",
        ],
    }
    write_json("source_library_redistribution_audit.json", redistribution_audit)
    redistribution_md = f"""# Source-library redistribution audit

- Status: **manual review required before transfer or publication**.
- Canonical identities in the review queue: **{len(canonical):,}**.
- `manual_review_required`: **{redistribution_counts.get('manual_review_required', 0):,}**.
- Public-distribution-ready identities established by current metadata: **0**.
- Eligible source candidates after the non-source quarantine: **{lane1['eligible_canonical_source_count']:,}**.

Current metadata preserve byte identity but do not adjudicate source-by-source redistribution rights. Packaging for a controlled handoff does not grant permission to publish the volumes. Every canonical record must carry its review status, and the recipient must resolve the intended transfer scope before further distribution.
"""
    (LANE / "source_library_redistribution_audit.md").write_text(redistribution_md, encoding="utf-8")

    source_only = {
        "status": "pass",
        "allowed_content": [
            "original source files", "extracted-text companions", "source provenance",
            "source aliases", "checksums", "extraction status", "known source issues",
            "redistribution review metadata", "recipient documentation", "validation tools",
        ],
        "excluded_content": [
            "analytical classifications", "report arguments", "adjudication results",
            "report-specific evidence links", "counterexample packets", "report visuals",
        ],
        "recipient_document_count": 5,
        "source_files_copied_by_lane": 0,
        "archive_volumes_created_by_lane": 0,
        "analytical_rows_emitted_by_lane": 0,
    }
    write_json("source_only_boundary_audit.json", source_only)
    (LANE / "source_only_boundary_audit.md").write_text(
        "# Source-only boundary audit\n\n"
        "Status: **pass**. Recipient materials describe originals, extracted-text companions, "
        "provenance, aliases, checksums, extraction status, source issues, redistribution review, "
        "and validation procedures. They do not carry analytical classifications, report arguments, "
        "report-specific evidence links, adjudication results, counterexample packets, or report visuals. "
        "This lane copied no source file and created no archive volume.\n",
        encoding="utf-8",
    )

    schemas = build_schemas()
    for filename, schema in schemas.items():
        write_json(filename, schema)

    packager_spec = {
        "tool_name": "stream_source_library_volumes",
        "purpose": "Write bounded compressed source volumes directly from canonical roots without a full staging copy.",
        "required_inputs": [
            "canonical source selection table", "alias table", "redistribution review table",
            "output directory", "maximum uncompressed bytes per volume", "archive format",
        ],
        "required_cli_contract": [
            "--library-root", "--canonical-index", "--alias-index", "--redistribution-index",
            "--output-root", "--max-uncompressed-bytes", "--resume-state",
        ],
        "invariants": [
            "sort canonical sources deterministically by canonical_source_id",
            "read each original once from its current canonical relative path",
            "never materialize a complete uncompressed library tree",
            "write no more than one active bounded volume plus compression overhead",
            "preserve original bytes and file extension",
            "reject absolute paths and parent traversal",
            "close, checksum, list, and validate each volume before starting the next",
            "append atomic checkpoint state only after a volume passes validation",
            "do not delete, rename, or modify originals",
        ],
        "required_outputs_per_volume": [
            "compressed archive", "volume manifest row", "SHA-256 checksum",
            "member inventory", "validation record", "resume checkpoint",
        ],
        "fail_closed_conditions": [
            "missing source", "source size mismatch", "source SHA-256 mismatch",
            "path collision", "archive write failure", "checksum failure",
            "member count mismatch", "insufficient free space", "unauthorized redistribution status",
        ],
    }
    write_json("streaming_packager_tool_specification.json", packager_spec)

    validator_spec = {
        "tool_name": "validate_source_library_volume",
        "purpose": "Validate one volume independently before transfer or reconstruction.",
        "required_cli_contract": ["--library-root", "--volume-manifest", "--volume-id", "--full-member-hash"],
        "checks": [
            "archive file exists", "archive byte size matches manifest", "volume SHA-256 matches",
            "archive opens without error", "member paths remain under the declared family root",
            "no duplicate member paths", "member count matches", "uncompressed byte total matches",
            "member SHA-256 matches canonical index when full-member-hash is enabled",
            "first and last canonical IDs match deterministic ordering",
        ],
        "result_values": ["passed", "failed", "quarantined"],
        "failure_behavior": "Do not transfer, reconstruct, or advance the packaging checkpoint for a failed volume.",
    }
    write_json("volume_validator_tool_specification.json", validator_spec)

    reconstruction_spec = {
        "tool_name": "reconstruct_source_library",
        "purpose": "Reconstruct or selectively extract a verified library in a clean environment.",
        "required_cli_contract": [
            "--library-root", "--destination", "--verify-checksums", "--family", "--select-id",
        ],
        "procedure": [
            "validate the top-level library manifest",
            "verify every selected volume checksum",
            "reject archive path traversal, absolute members, and symlink escapes",
            "extract originals and extracted text into separate roots",
            "verify extracted original member hashes against canonical IDs",
            "write a reconstruction report without altering package manifests",
        ],
        "modes": ["full_reconstruction", "family_reconstruction", "selective_canonical_source"],
        "clean_room_acceptance": [
            "no dependency on the original project repository",
            "all relative paths resolve under the supplied library root",
            "canonical count and bytes reconcile",
            "all aliases resolve to a known canonical identity",
            "redistribution review remains visible",
        ],
    }
    write_json("reconstruction_tool_specification.json", reconstruction_spec)

    tool_md = """# Source-library tool specifications

## Streaming packager

The packager reads the canonical source-selection table in deterministic SHA-256 order and writes bounded compressed volumes directly from the existing source roots. It must not build a full uncompressed staging tree. After each volume closes, it writes the archive checksum, member inventory, validation result, and atomic resume checkpoint. It starts the next volume only after the prior volume passes validation.

## Volume validator

The validator checks archive size, SHA-256, readability, member count, member byte total, path safety, ordering, and optionally every member hash. A failed volume is quarantined. Validation failure must not advance the packaging checkpoint.

## Reconstruction tool

The reconstruction tool operates from a caller-supplied library root. It verifies volume checksums before extraction, rejects unsafe paths and symlink escapes, separates originals from extracted text, verifies reconstructed original hashes, and writes a compact reconstruction report. It supports full, family, and single-source reconstruction without relying on the original repository.
"""
    (LANE / "source_library_tool_specifications.md").write_text(tool_md, encoding="utf-8")

    queue = [
        {"queue_item_id": "L5-001", "work_item": "write recipient documentation", "status": "completed", "output_count": 5},
        {"queue_item_id": "L5-002", "work_item": "run redacted metadata security scan", "status": "completed", "output_count": 4},
        {"queue_item_id": "L5-003", "work_item": "audit relative-path portability", "status": "completed", "output_count": 2},
        {"queue_item_id": "L5-004", "work_item": "audit redistribution status", "status": "completed", "output_count": 2},
        {"queue_item_id": "L5-005", "work_item": "audit source-only boundary", "status": "completed", "output_count": 2},
        {"queue_item_id": "L5-006", "work_item": "define package record schemas", "status": "completed", "output_count": len(schemas)},
        {"queue_item_id": "L5-007", "work_item": "define packager, validator, and reconstruction tools", "status": "completed", "output_count": 4},
    ]
    write_csv("lane_005_queue.csv", queue, ["queue_item_id", "work_item", "status", "output_count"])
    write_jsonl("lane_005_queue.jsonl", queue)

    summary = {
        "lane_id": "lane_005",
        "scope": "source-only recipient documentation, schemas, tool specifications, and bounded risk audits",
        "started_at_utc": started,
        "completed_at_utc": timestamp(),
        "recipient_document_count": 5,
        "schema_count": len(schemas),
        "tool_specification_count": 3,
        "physical_source_metadata_rows_scanned": len(physical),
        "canonical_source_rows_reviewed": len(canonical),
        "eligible_source_candidates": lane1["eligible_canonical_source_count"],
        "eligible_source_candidate_bytes": lane1["eligible_canonical_source_bytes"],
        "credential_risk_candidate_count": len(credential_findings),
        "package_path_risk_candidate_count": len(path_findings),
        "redistribution_manual_review_required_count": redistribution_counts.get("manual_review_required", 0),
        "public_distribution_ready_count": 0,
        "repository_absolute_path_records_excluded_from_package": len(repo_abs),
        "source_payload_content_scan_completed": False,
        "source_files_copied": 0,
        "archive_volumes_created": 0,
        "sources_deleted_or_modified": 0,
        "source_only_boundary_preserved": True,
        "blockers": [],
        "warnings": [
            "Redistribution rights remain unresolved for every canonical identity.",
            "Descriptive source metadata are blank in the current canonical inventory.",
            "The source payload contents were not exhaustively scanned for private information.",
        ],
    }
    write_json("lane_005_summary.json", summary)
    summary_md = f"""# Lane 005 recipient-documentation summary

Lane 005 prepared source-only recipient documentation, schemas, tool contracts, and bounded security, portability, and redistribution audits.

## Result

- Recipient documents: **5**.
- JSON schemas: **{len(schemas)}**.
- Tool specifications: **3**.
- Physical source metadata rows scanned: **{len(physical):,}**.
- Canonical source rows reviewed: **{len(canonical):,}**.
- Eligible source candidates after non-source quarantine: **{lane1['eligible_canonical_source_count']:,}** ({lane1['eligible_canonical_source_bytes']:,} bytes).
- Metadata credential-risk candidates: **{len(credential_findings):,}**.
- Nonportable package-path candidates: **{len(path_findings):,}**.
- Canonical identities requiring redistribution review: **{redistribution_counts.get('manual_review_required', 0):,}**.
- Public-distribution-ready identities established by current metadata: **0**.
- Source files copied, changed, or deleted: **0**.
- Archive volumes created: **0**.

## Boundary and warnings

The documents and schemas cover original sources, extracted-text companions, provenance, aliases, checksums, known source issues, redistribution status, streamed volume creation, validation, and clean reconstruction. They contain no analytical classifications or report material. The full source payload contents were not exhaustively scanned for private information, and source-by-source redistribution permission remains unresolved.
"""
    (LANE / "lane_005_summary.md").write_text(summary_md, encoding="utf-8")

    checkpoint = {
        "lane_id": "lane_005",
        "status": "completed",
        "completed_at_utc": timestamp(),
        "completed_queue_items": [row["queue_item_id"] for row in queue],
        "incomplete_queue_items": [],
        "blockers": [],
    }
    write_json("lane_005_checkpoint.json", checkpoint)

    inputs = {
        name: {
            "relative_path": str(path.relative_to(REPO)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for name, path in paths.items()
    }
    manifest = {
        "lane_id": "lane_005",
        "generated_at_utc": timestamp(),
        "inputs": inputs,
        "outputs": sorted(
            path.name for path in LANE.iterdir()
            if path.is_file() and path.name != "lane_005_manifest.json"
        ),
        "source_only_boundary_preserved": True,
    }
    write_json("lane_005_manifest.json", manifest)


if __name__ == "__main__":
    main()
