#!/usr/bin/env python3
"""Reconcile one current extracted-text companion per Phase 0 canonical source.

This is an inventory-only script. It reads existing manifests and writes compact
lane-owned indexes. It never extracts, OCRs, copies, moves, packages, or deletes
source or companion files.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[7]
LANE = Path(__file__).resolve().parents[1]
PHASE0 = REPO / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
PIPELINE = REPO / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
READINESS = PIPELINE / "05_EXTERNAL-DATA-READINESS"
EXTRACTION = PIPELINE / "06_EXTERNAL-DATA-EXTRACTION"

LEGACY_MANIFESTS = [
    {
        "name": "targeted_text_layer_321",
        "priority": 10,
        "path": REPO / "docs/analysis/compensation_extraction/TARGETED-TEXT-LAYER-EXTRACTION-321-READINESS-READY-SOURCES-2026-07-26/targeted_text_layer_extraction_321_results.csv",
        "source_hash": "file_sha256",
        "path_field": "extracted_text_path",
        "size_field": "extracted_text_size_bytes",
        "text_hash": "extracted_text_sha256",
        "ocr_field": "ocr_used",
    },
    {
        "name": "tier_c_text_layer_378",
        "priority": 20,
        "path": REPO / "docs/analysis/compensation_extraction/DASHBOARD-DECLUTTER-MAP-CORRECTION-AND-TIER-C-TEXT-SPAN-EXTRACTION-378-2026-07-27/tier_c_text_layer_extraction_378_results.csv",
        "source_hash": "file_sha256",
        "path_field": "extracted_text_path",
        "size_field": "extracted_text_size_bytes",
        "text_hash": "extracted_text_sha256",
        "ocr_field": "ocr_used",
    },
    {
        "name": "combined_broad_text_4051",
        "priority": 30,
        "path": REPO / "docs/analysis/compensation_extraction/COMBINED-BROAD-TEXT-EXTRACTION-4051-PARALLEL-LANES-2026-07-28/combined_broad_text_extraction_4051_results.csv",
        "source_hash": "retained_file_sha256",
        "path_field": "extracted_text_artifact_path",
        "size_field": "extracted_text_size_bytes",
        "text_hash": "extracted_text_sha256",
        "ocr_field": "",
    },
    {
        "name": "broad_state_4x2500_text",
        "priority": 40,
        "path": REPO / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30/extracted_text_manifest.csv",
        "source_hash": "retained_file_sha256",
        "path_field": "extracted_text_artifact_path",
        "size_field": "extracted_text_byte_size",
        "text_hash": "extracted_text_sha256",
        "ocr_field": "ocr_run_flag",
    },
    {
        "name": "remaining_municipalities_text",
        "priority": 50,
        "path": REPO / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-TEXT-EXTRACTION-2026-08-02/extracted_text_manifest.csv",
        "source_hash": "retained_file_sha256",
        "path_field": "extracted_text_artifact_path",
        "size_field": "extracted_text_byte_size",
        "text_hash": "extracted_text_sha256",
        "ocr_field": "ocr_run_flag",
    },
]

TEXT_ARTIFACT_KINDS = {
    "full_pdf_text": 100,
    "full_html_visible_text": 100,
    "full_plain_text": 100,
}
STRUCTURED_ONLY_KINDS = {"full_csv_rows", "compressed_exact_csv", "csv_schema"}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO.resolve()).as_posix()
    except (ValueError, FileNotFoundError):
        return p.as_posix()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        yield from csv.DictReader(handle)


def read_shards(root: Path, manifest_name: str):
    manifest = json.loads((root / manifest_name).read_text())
    for part in manifest["parts"]:
        yield from read_csv(root / part["csv"])


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bool_text(value: str) -> str:
    value = (value or "").strip().lower()
    if value in {"false", "0", "no", "n"}:
        return "not_run"
    if value in {"true", "1", "yes", "y"}:
        return "performed"
    return "not_indicated_in_manifest"


def companion_suffix(path: str, kind: str) -> str:
    lower = path.lower()
    if kind == "full_html_visible_text" or lower.endswith(".visible_text.txt.gz"):
        return ".visible_text.txt.gz"
    if lower.endswith(".txt.gz"):
        return ".txt.gz"
    if lower.endswith(".txt"):
        return ".txt"
    return Path(path).suffix or ".txt"


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    canonical_rows = list(read_csv(PHASE0 / "source_archive_canonical_source_inventory.csv"))
    canonical = {r["canonical_source_id"].lower(): r for r in canonical_rows}

    proposed = {
        r["canonical_source_id"].lower(): r
        for r in read_csv(PHASE0 / "source_library_proposed_path_map.csv")
    }

    readiness_by_hash: dict[str, list[dict]] = defaultdict(list)
    for row in read_shards(READINESS, "canonical_source_readiness_results_shard_manifest.json"):
        readiness_by_hash[row["SHA_256"].lower()].append(row)

    extraction_result_by_payload = {}
    extraction_result_by_id = {}
    for row in read_shards(EXTRACTION, "canonical_source_extraction_results_shard_manifest.json"):
        extraction_result_by_payload[row["canonical_payload_id"]] = row
        extraction_result_by_id[row["extraction_result_id"]] = row

    candidates: dict[str, list[dict]] = defaultdict(list)
    structured_only: dict[str, list[dict]] = defaultdict(list)
    for row in read_shards(EXTRACTION, "extraction_artifact_pointer_manifest_shard_manifest.json"):
        source_hash = row["source_SHA_256"].lower()
        kind = row["artifact_kind"]
        item = {
            "source_hash": source_hash,
            "candidate_source": "whole_corpus_external_non_ocr_extraction",
            "candidate_priority": 100,
            "artifact_kind": kind,
            "current_path": row["output_local_path"],
            "manifested_size_bytes": int(row["output_byte_size"] or 0),
            "companion_sha256": row["output_SHA_256"],
            "ocr_status": "not_run",
            "extraction_status": extraction_result_by_id.get(row["extraction_result_id"], {}).get(
                "primary_terminal_status", "extracted_usable"
            ),
            "lineage_manifest": rel(EXTRACTION / "extraction_artifact_pointer_manifest_shard_manifest.json"),
        }
        if kind in TEXT_ARTIFACT_KINDS:
            candidates[source_hash].append(item)
        elif kind in STRUCTURED_ONLY_KINDS:
            structured_only[source_hash].append(item)

    legacy_input_audit = []
    for spec in LEGACY_MANIFESTS:
        loaded = 0
        accepted = 0
        if not spec["path"].exists():
            legacy_input_audit.append({"manifest": rel(spec["path"]), "status": "missing", "rows": 0, "accepted": 0})
            continue
        for row in read_csv(spec["path"]):
            loaded += 1
            if row.get("extraction_status") != "extracted_ok":
                continue
            source_hash = (row.get(spec["source_hash"]) or "").strip().lower()
            artifact_path = (row.get(spec["path_field"]) or "").strip()
            if len(source_hash) != 64 or not artifact_path:
                continue
            accepted += 1
            ocr_field = spec.get("ocr_field")
            candidates[source_hash].append(
                {
                    "source_hash": source_hash,
                    "candidate_source": spec["name"],
                    "candidate_priority": spec["priority"],
                    "artifact_kind": "legacy_full_text",
                    "current_path": artifact_path,
                    "manifested_size_bytes": int(row.get(spec["size_field"]) or 0),
                    "companion_sha256": row.get(spec["text_hash"], ""),
                    "ocr_status": bool_text(row.get(ocr_field, "")) if ocr_field else "not_indicated_in_manifest",
                    "extraction_status": row.get("extraction_status", "extracted_ok"),
                    "lineage_manifest": rel(spec["path"]),
                }
            )
        legacy_input_audit.append(
            {"manifest": rel(spec["path"]), "status": "loaded", "rows": loaded, "accepted": accepted}
        )

    queue_rows = []
    result_rows = []
    missing_rows = []
    ambiguity_rows = []
    selected_rows = []
    status_counts = Counter()
    uncertainty_counts = Counter()
    selected_source_counts = Counter()
    selected_bytes = 0
    selected_manifested_bytes = 0
    source_files_present = 0
    missing_manifested_candidate_total = 0

    for source_hash in sorted(canonical):
        source = canonical[source_hash]
        source_path = source["canonical_relative_path"]
        source_exists = (REPO / source_path).is_file()
        source_files_present += int(source_exists)
        source_proposed = proposed.get(source_hash, {}).get(
            "proposed_relative_path", source.get("expected_source_library_path", "")
        )
        queue_rows.append(
            {
                "canonical_source_id": source_hash,
                "current_source_path": source_path,
                "source_exists": str(source_exists).lower(),
                "source_size_bytes": source["file_size_bytes"],
                "proposed_original_archive_path": source_proposed,
                "selection_basis": "phase_0_exact_duplicate_canonical_source_inventory",
            }
        )

        all_candidates = candidates.get(source_hash, [])
        for candidate in all_candidates:
            p = REPO / candidate["current_path"]
            candidate["exists"] = p.is_file()
            candidate["actual_size_bytes"] = p.stat().st_size if p.is_file() else 0

        existing = [c for c in all_candidates if c["exists"]]
        selected = max(
            existing,
            key=lambda c: (
                c["candidate_priority"],
                TEXT_ARTIFACT_KINDS.get(c["artifact_kind"], 0),
                c["actual_size_bytes"],
                c["current_path"],
            ),
            default=None,
        )

        readiness_rows = readiness_by_hash.get(source_hash, [])
        readiness_statuses = sorted({r["readiness_status"] for r in readiness_rows if r.get("readiness_status")})
        terminal_statuses = sorted(
            {
                extraction_result_by_payload[r["canonical_payload_id"]]["primary_terminal_status"]
                for r in readiness_rows
                if r.get("canonical_payload_id") in extraction_result_by_payload
            }
        )

        distinct_text_hashes = sorted({c["companion_sha256"] for c in existing if c["companion_sha256"]})
        missing_manifested = sum(not c["exists"] for c in all_candidates)
        missing_manifested_candidate_total += missing_manifested
        if selected:
            if len(distinct_text_hashes) > 1:
                uncertainty = "multiple_distinct_companion_versions_selected_by_priority"
            elif len(existing) > 1:
                uncertainty = "multiple_paths_same_or_unhashed_text_selected_by_priority"
            else:
                uncertainty = "none_exact_source_hash_link"
            companion_status = "current_text_companion_available"
            extraction_status = selected["extraction_status"]
            suffix = companion_suffix(selected["current_path"], selected["artifact_kind"])
            proposed_companion = f"extracted_text/{source_hash[:2]}/{source_hash}{suffix}"
            selected_bytes += selected["actual_size_bytes"]
            selected_manifested_bytes += selected["manifested_size_bytes"]
            selected_source_counts[selected["candidate_source"]] += 1
        else:
            selected = {
                "candidate_source": "",
                "artifact_kind": "",
                "current_path": "",
                "actual_size_bytes": 0,
                "manifested_size_bytes": 0,
                "companion_sha256": "",
                "ocr_status": "not_applicable_or_not_run",
                "lineage_manifest": "",
            }
            proposed_companion = ""
            if all_candidates:
                companion_status = "manifested_text_companion_missing_on_disk"
                extraction_status = "manifested_extracted_text_file_missing"
                uncertainty = "high_missing_manifested_companion"
            elif source_hash in structured_only:
                companion_status = "structured_only_no_text_companion"
                extraction_status = "structured_extraction_available"
                uncertainty = "none_text_companion_not_applicable_to_csv"
            elif any(s in {"parse_error", "parse_timeout"} for s in terminal_statuses):
                companion_status = "no_text_companion_extraction_repair_required"
                extraction_status = "|".join(terminal_statuses)
                uncertainty = "none_known_extraction_failure"
            elif "ocr_later" in readiness_statuses:
                companion_status = "no_text_companion_ocr_deferred"
                extraction_status = "ocr_later_not_run"
                selected["ocr_status"] = "deferred_not_run"
                uncertainty = "none_known_ocr_hold"
            elif readiness_statuses:
                companion_status = "no_text_companion_readiness_excluded"
                extraction_status = "|".join(readiness_statuses)
                uncertainty = "none_known_readiness_exclusion"
            else:
                companion_status = "no_text_companion_no_extraction_manifest"
                extraction_status = "no_extraction_manifest"
                uncertainty = "linkage_unavailable"

        row = {
            "canonical_source_id": source_hash,
            "current_source_path": source_path,
            "source_exists": str(source_exists).lower(),
            "source_size_bytes": source["file_size_bytes"],
            "source_extension": source.get("source_type", ""),
            "proposed_original_archive_path": source_proposed,
            "companion_status": companion_status,
            "extraction_status": extraction_status,
            "ocr_status": selected["ocr_status"],
            "linkage_method": "exact_source_sha256" if all_candidates or source_hash in structured_only else "no_companion_link",
            "linkage_uncertainty": uncertainty,
            "candidate_companion_count": len(all_candidates),
            "existing_candidate_count": len(existing),
            "distinct_existing_companion_hash_count": len(distinct_text_hashes),
            "missing_manifested_candidate_count": missing_manifested,
            "selected_companion_source": selected["candidate_source"],
            "selected_artifact_kind": selected["artifact_kind"],
            "current_companion_path": selected["current_path"],
            "current_companion_size_bytes": selected["actual_size_bytes"],
            "manifested_companion_size_bytes": selected["manifested_size_bytes"],
            "companion_sha256": selected["companion_sha256"],
            "proposed_companion_archive_path": proposed_companion,
            "readiness_statuses": "|".join(readiness_statuses),
            "terminal_statuses": "|".join(terminal_statuses),
            "companion_lineage_manifest": selected["lineage_manifest"],
        }
        result_rows.append(row)
        status_counts[companion_status] += 1
        uncertainty_counts[uncertainty] += 1
        if selected["current_path"]:
            selected_rows.append(row)
        else:
            missing_rows.append(row)
        if uncertainty.startswith("multiple_") or uncertainty.startswith("high_") or uncertainty == "linkage_unavailable":
            ambiguity_rows.append(row)

    fields = list(result_rows[0])
    queue_fields = list(queue_rows[0])
    write_csv(LANE / "lane_003_queue.csv", queue_rows, queue_fields)
    write_csv(LANE / "source_companion_reconciliation.csv", result_rows, fields)
    write_csv(LANE / "selected_extracted_text_companions.csv", selected_rows, fields)
    write_csv(LANE / "missing_or_nontext_companions.csv", missing_rows, fields)
    write_csv(LANE / "companion_linkage_uncertainty.csv", ambiguity_rows, fields)
    write_csv(
        LANE / "companion_status_summary.csv",
        [
            {"companion_status": key, "source_count": value}
            for key, value in sorted(status_counts.items())
        ],
        ["companion_status", "source_count"],
    )

    collisions = Counter(r["proposed_companion_archive_path"] for r in selected_rows)
    collision_rows = [
        {"proposed_companion_archive_path": path, "source_count": count}
        for path, count in collisions.items()
        if path and count > 1
    ]
    write_csv(
        LANE / "companion_proposed_path_collision_audit.csv",
        collision_rows,
        ["proposed_companion_archive_path", "source_count"],
    )

    # Bounded validation: verify 50 evenly spaced selected companion hashes.
    hash_sample = []
    if selected_rows:
        sample_count = min(50, len(selected_rows))
        sample_indexes = sorted({(i * len(selected_rows)) // sample_count for i in range(sample_count)})
        for index in sample_indexes:
            row = selected_rows[index]
            observed = sha256_file(REPO / row["current_companion_path"])
            expected = row["companion_sha256"]
            hash_sample.append(
                {
                    "canonical_source_id": row["canonical_source_id"],
                    "current_companion_path": row["current_companion_path"],
                    "expected_sha256": expected,
                    "observed_sha256": observed,
                    "match": bool(expected) and expected == observed,
                }
            )
    write_csv(
        LANE / "sampled_companion_hash_QA.csv",
        hash_sample,
        ["canonical_source_id", "current_companion_path", "expected_sha256", "observed_sha256", "match"],
    )

    qa = {
        "generated_at": generated_at,
        "canonical_source_count": len(canonical),
        "queue_row_count": len(queue_rows),
        "reconciliation_row_count": len(result_rows),
        "unique_reconciliation_source_count": len({r["canonical_source_id"] for r in result_rows}),
        "selected_companion_count": len(selected_rows),
        "canonical_source_files_present": source_files_present,
        "canonical_source_files_missing": len(canonical) - source_files_present,
        "selected_companions_exist": all((REPO / r["current_companion_path"]).is_file() for r in selected_rows),
        "selected_links_use_exact_source_hash": all(r["linkage_method"] == "exact_source_sha256" for r in selected_rows),
        "proposed_companion_path_collisions": len(collision_rows),
        "source_hashes_outside_phase0_canonical_inventory": len(set(candidates) - set(canonical)),
        "manifested_size_matches_actual_for_selected": sum(
            int(r["current_companion_size_bytes"]) == int(r["manifested_companion_size_bytes"])
            for r in selected_rows
        ),
        "manifested_size_mismatch_for_selected": sum(
            int(r["current_companion_size_bytes"]) != int(r["manifested_companion_size_bytes"])
            for r in selected_rows
        ),
        "sampled_companion_hash_count": len(hash_sample),
        "sampled_companion_hash_matches": sum(r["match"] for r in hash_sample),
        "no_extraction_performed": True,
        "no_ocr_performed": True,
        "no_files_copied_moved_deleted_or_packaged": True,
    }
    qa["passed"] = all(
        [
            qa["canonical_source_count"] == qa["queue_row_count"] == qa["reconciliation_row_count"],
            qa["canonical_source_count"] == qa["unique_reconciliation_source_count"],
            qa["selected_companions_exist"],
            qa["selected_links_use_exact_source_hash"],
            qa["proposed_companion_path_collisions"] == 0,
            qa["source_hashes_outside_phase0_canonical_inventory"] == 0,
            qa["canonical_source_files_missing"] == 0,
            qa["sampled_companion_hash_count"] == qa["sampled_companion_hash_matches"],
        ]
    )

    summary = {
        "generated_at": generated_at,
        "lane_id": "lane_003",
        "scope": "extracted_text_companion_reconciliation_only",
        "selection_universe": "Phase 0 canonical sources after exact duplicate grouping",
        "canonical_source_count": len(canonical),
        "selected_text_companion_count": len(selected_rows),
        "selected_text_companion_bytes": selected_bytes,
        "selected_text_companion_manifested_bytes": selected_manifested_bytes,
        "sources_without_selected_text_companion": len(missing_rows),
        "canonical_source_files_present": source_files_present,
        "canonical_source_files_missing": len(canonical) - source_files_present,
        "missing_manifested_companion_candidate_paths": missing_manifested_candidate_total,
        "companion_status_counts": dict(sorted(status_counts.items())),
        "linkage_uncertainty_counts": dict(sorted(uncertainty_counts.items())),
        "selected_companion_source_counts": dict(sorted(selected_source_counts.items())),
        "legacy_manifest_input_audit": legacy_input_audit,
        "qa": qa,
        "blockers": [],
        "uncertainties": [
            "Multiple exact-hash-linked text variants are retained as alternatives; the newest complete pipeline is selected first.",
            "Sources without any extraction manifest are not assumed to lack extractable text; they are left unlinked.",
            "CSV sources with structured extraction are classified separately because they do not have a text companion.",
        ],
        "forbidden_actions": {
            "extraction": False,
            "ocr": False,
            "copy": False,
            "delete": False,
            "package": False,
            "stage": False,
            "commit": False,
        },
    }
    write_json(LANE / "lane_003_companion_reconciliation_summary.json", summary)
    write_json(LANE / "lane_003_QA.json", qa)

    checkpoint = {
        "generated_at": generated_at,
        "lane_id": "lane_003",
        "status": "completed" if qa["passed"] else "completed_with_QA_failure",
        "completed_segments": [
            "phase_0_canonical_source_queue",
            "whole_corpus_non_ocr_extraction_pointer_reconciliation",
            "legacy_extraction_manifest_reconciliation",
            "companion_selection",
            "status_and_uncertainty_classification",
            "QA",
        ],
        "accepted_canonical_source_ids": len(canonical),
        "selected_companion_count": len(selected_rows),
        "resume_required": not qa["passed"],
        "output_hashes": {},
    }
    for name in [
        "lane_003_queue.csv",
        "source_companion_reconciliation.csv",
        "selected_extracted_text_companions.csv",
        "missing_or_nontext_companions.csv",
        "companion_linkage_uncertainty.csv",
        "companion_status_summary.csv",
        "companion_proposed_path_collision_audit.csv",
        "sampled_companion_hash_QA.csv",
        "lane_003_companion_reconciliation_summary.json",
        "lane_003_QA.json",
    ]:
        checkpoint["output_hashes"][name] = sha256_file(LANE / name)
    write_json(LANE / "lane_003_checkpoint.json", checkpoint)

    gib = selected_bytes / (1024**3)
    summary_md = f"""# Lane 003: extracted-text companion reconciliation

Status: **{'complete' if qa['passed'] else 'QA failed'}**

This lane reconciled existing extracted-text companions against the Phase 0 canonical source inventory. It did not run extraction or OCR, and it did not copy, move, delete, package, stage, or commit any source or companion file.

## Results

- Canonical source universe: **{len(canonical):,}**
- Current text companions selected by exact source SHA-256: **{len(selected_rows):,}**
- Selected current companion bytes: **{selected_bytes:,}** ({gib:.2f} GiB)
- Sources without a selected text companion: **{len(missing_rows):,}**
- Proposed companion-path collisions: **{len(collision_rows):,}**

## Status distribution

"""
    for key, value in sorted(status_counts.items()):
        summary_md += f"- `{key}`: {value:,}\n"
    summary_md += "\n## Selection provenance\n\n"
    for key, value in sorted(selected_source_counts.items()):
        summary_md += f"- `{key}`: {value:,}\n"
    summary_md += """

## Linkage policy

All selected links use the original source file's SHA-256. The current whole-corpus non-OCR extraction layer has first priority, followed by earlier complete extraction manifests in chronological order. Filename-only inference is never used. When several exact-hash-linked text variants remain, the chosen current companion is recorded alongside the multiplicity and uncertainty flag.

CSV structured rows are not mislabeled as extracted text. OCR-later, extraction-repair, readiness-excluded, and no-manifest sources remain explicit non-companion statuses.

## Packaging boundary

The `proposed_companion_archive_path` field is only a future path plan. This lane created no archive and copied no data.
"""
    (LANE / "lane_003_summary.md").write_text(summary_md, encoding="utf-8")


if __name__ == "__main__":
    main()
