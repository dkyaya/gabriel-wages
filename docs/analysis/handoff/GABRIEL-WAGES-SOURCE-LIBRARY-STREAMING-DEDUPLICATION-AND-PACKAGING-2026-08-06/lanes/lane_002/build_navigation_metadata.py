#!/usr/bin/env python3
"""Build compact, source-only navigation metadata for packaging Lane 2.

This script reads existing Phase 0 inventories and source-review metadata. It
does not read, copy, package, modify, or delete source binaries. All outputs are
written to this lane directory.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


REPO = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
PHASE0 = REPO / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
COMP = REPO / "docs/analysis/compensation_extraction"

CANONICAL = PHASE0 / "source_archive_canonical_source_inventory.csv"
PHYSICAL = PHASE0 / "source_archive_physical_file_inventory.csv"
ALIASES = PHASE0 / "source_archive_alias_inventory.csv"
EXTRACTION = PHASE0 / "source_archive_extraction_status.csv"
PROPOSED = PHASE0 / "source_library_proposed_path_map.csv"

TARGETED_429 = COMP / "TARGETED-SOURCE-REVIEW-DOWNLOAD-429-VERIFIED-LEADS-2026-07-26/targeted_source_review_download_429_results.csv"
TARGETED_556 = COMP / "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27/targeted_tier_c_source_review_download_556_results.csv"
COMBINED = COMP / "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28/combined_broad_source_review_download_5589_results.csv"
FOUR_BY = COMP / "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30/merged_source_review_results.csv"
REMAINING = COMP / "BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02/retained_source_manifest.csv"
EXTERNAL_DIR = COMP / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
EXTERNAL_MANIFESTS = sorted((EXTERNAL_DIR / "04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD").glob("retained_source_manifest*.csv"))
EXTERNAL_READINESS = sorted((EXTERNAL_DIR / "05_EXTERNAL-DATA-READINESS").glob("canonical_source_readiness_results*.csv"))

REGION_BY_STATE = {
    **dict.fromkeys("CT ME MA NH RI VT NJ NY PA".split(), "Northeast"),
    **dict.fromkeys("IN IL MI OH WI IA KS MN MO NE ND SD".split(), "Midwest"),
    **dict.fromkeys("DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX".split(), "South"),
    **dict.fromkeys("AZ CO ID MT NV NM UT WY AK CA HI OR WA".split(), "West"),
}


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        yield from csv.DictReader(handle)


def first(row: dict, names: list[str]) -> str:
    for name in names:
        value = str(row.get(name, "") or "").strip()
        if value:
            return value
    return ""


def valid_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value or ""))


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_table(stem: str, rows: list[dict], fields: list[str] | None = None):
    if fields is None:
        fields = list(rows[0]) if rows else []
    compress = len(rows) > 1000
    plain_path = OUT / f"{stem}.csv"
    gzip_path = OUT / f"{stem}.csv.gz"
    if compress:
        if plain_path.exists():
            plain_path.unlink()
        raw_handle = gzip_path.open("wb")
        gzip_handle = gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0)
        handle = io.TextIOWrapper(gzip_handle, encoding="utf-8", newline="")
    else:
        if gzip_path.exists():
            gzip_path.unlink()
        handle = plain_path.open("w", newline="", encoding="utf-8")
    with handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def slug(value: str, maximum: int, fallback: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-+", "-", value)
    return (value[:maximum].rstrip("-") or fallback)


def normalized_extension(value: str, path: str) -> str:
    ext = (value or Path(path).suffix).lower().strip()
    if ext and not ext.startswith("."):
        ext = "." + ext
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", ext or ""):
        return ".bin"
    return ext


def normalize_family(raw: str, ext: str) -> str:
    value = (raw or "").lower().replace("-", "_")
    tests = [
        ("collective_bargaining", ["collective", "cba", "bargaining_agreement", "memorandum_of_agreement", "moa"]),
        ("arbitration_or_factfinding", ["arbitration", "factfinding", "fact_finding", "award"]),
        ("salary_schedule_or_pay_plan", ["salary_schedule", "wage_schedule", "pay_plan", "compensation_plan"]),
        ("budget_or_finance", ["budget", "finance", "appropriation"]),
        ("payroll_or_earnings", ["payroll", "earnings", "employee_pay"]),
        ("staffing_or_human_resources", ["staffing", "headcount", "human_resources", "recruitment", "retention", "vacancy"]),
        ("ordinance_or_policy", ["ordinance", "municipal_code", "policy", "resolution"]),
        ("benefits_or_pension", ["benefit", "pension", "health"]),
        ("administrative_report", ["administrative", "report", "study", "audit"]),
        ("news_or_context", ["news", "context", "secondary"]),
        ("structured_data", ["structured", "open_data", "dataset", "csv", "spreadsheet"]),
    ]
    for family, needles in tests:
        if any(needle in value for needle in needles):
            return family
    if ext in {".csv", ".tsv", ".json", ".xml", ".xlsx", ".xls"}:
        return "structured_data"
    if raw:
        return "other_document"
    return "unknown"


def parse_period(explicit: str, title: str):
    value = (explicit or "").strip()
    years = [int(x) for x in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", value)]
    basis = "explicit_metadata" if years else ""
    label = value
    if not years:
        title_years = [int(x) for x in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", title or "")]
        if title_years:
            years = title_years
            basis = "title_year_pattern"
            label = str(years[0]) if len(set(years)) == 1 else f"{min(years)}-{max(years)}"
    if not years:
        return "", "", "", "unresolved"
    return label, str(min(years)), str(max(years)), basis


def safe_url(value: str) -> str:
    value = (value or "").strip()
    return value if value.startswith(("http://", "https://")) else ""


def provenance_stage(path: str) -> str:
    upper = path.upper()
    if "TARGETED-SOURCE-REVIEW-DOWNLOAD-429" in upper:
        return "targeted_verified_leads"
    if "TIER-C-SOURCE-REVIEW-DOWNLOAD-556" in upper:
        return "targeted_tier_c"
    if "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589" in upper or "combined_broad_source_review_download_5589" in path:
        return "combined_broad_review"
    if "BROAD-STATE-4X2500" in upper or "broad_state_4x2500" in path:
        return "broad_state_4x2500"
    if "REMAINING-MUNICIPALITIES" in upper or "remaining_municipalities" in path:
        return "remaining_municipalities"
    if "whole_corpus_external_data_exhaustive_pipeline" in path:
        return "whole_corpus_external_pipeline"
    return "phase0_unclassified"


def standardize(row: dict, metadata_file: Path, source_rank: int) -> dict:
    sha = first(row, ["file_sha256", "retained_file_sha256", "SHA_256", "SHA256", "sha256"])
    path = first(row, ["local_retained_path", "retained_file_path", "retained_local_artifact_path", "local_artifact_path", "artifact_storage_pointer"])
    title = first(row, ["source_title", "candidate_title"])
    original_filename = first(row, ["original_filename"])
    if not original_filename and path:
        original_filename = Path(path).name
    url = safe_url(first(row, ["source_url_or_locator", "final_download_url", "final_download_locator", "canonical_final_url", "source_locator_or_url", "original_requested_urls"]))
    explicit_period = first(row, ["verified_contract_or_document_period", "contract_or_document_period", "period"])
    source_family = first(row, ["verified_source_family", "source_family", "source_family_hint", "final_administrative_source_type", "administrative_source_type", "primary_content_family"])
    municipality = first(row, ["verified_municipality", "municipality"])
    state = first(row, ["verified_state", "state"]).upper()
    return {
        "sha256": sha.lower(),
        "current_path": path,
        "source_title": title,
        "original_filename": original_filename,
        "original_url": url,
        "municipality": municipality,
        "state": state,
        "region": first(row, ["verified_region", "derived_region", "region"]) or REGION_BY_STATE.get(state, ""),
        "period_explicit": explicit_period,
        "source_family_raw": source_family,
        "document_type_raw": first(row, ["document_type_hint", "retained_file_type", "detected_file_type", "content_type_hint"]),
        "mime_type": first(row, ["MIME_type", "final_content_type", "content_type_hint", "content_type"]),
        "extraction_status": first(row, ["readiness_status", "extraction_status", "readiness_hint"]),
        "official_source_flag": first(row, ["official_source_flag"]),
        "source_review_id": first(row, ["source_review_id", "source_review_download_id"]),
        "retained_source_id": first(row, ["retained_source_id"]),
        "candidate_id": first(row, ["candidate_id", "source_candidate_id", "combined_review_id"]),
        "source_review_lane_id": first(row, ["source_review_lane_id", "lane_id"]),
        "retrieved_timestamp": first(row, ["retrieved_timestamp", "download_completed_at", "source_review_timestamp"]),
        "metadata_source_file": metadata_file.relative_to(REPO).as_posix(),
        "metadata_rank": source_rank,
    }


def richness(record: dict) -> tuple:
    core = sum(bool(record.get(k)) for k in ["source_title", "municipality", "state", "source_family_raw", "original_url", "period_explicit"])
    return (core, record.get("metadata_rank", 0))


def main():
    started = datetime.now(timezone.utc)
    # Remove only redundant lane-owned JSONL tables from an earlier local build.
    # The CSV tables are the canonical compact merge inputs.
    for stale in OUT.glob("*.jsonl"):
        stale.unlink()
    input_files = [CANONICAL, PHYSICAL, ALIASES, EXTRACTION, PROPOSED, TARGETED_429, TARGETED_556, COMBINED, FOUR_BY, REMAINING] + EXTERNAL_MANIFESTS + EXTERNAL_READINESS
    missing_inputs = [p.as_posix() for p in input_files if not p.exists()]
    if missing_inputs:
        raise SystemExit(f"Missing inputs: {missing_inputs}")

    queue_rows = []
    for order, path in enumerate(input_files, 1):
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            row_count = sum(1 for _ in reader)
        queue_rows.append({
            "queue_order": order,
            "input_role": "phase0_inventory" if path.parent == PHASE0 else "trusted_source_metadata",
            "relative_path": path.relative_to(REPO).as_posix(),
            "row_count": row_count,
            "byte_size": path.stat().st_size,
            "sha256": sha_file(path),
            "read_only": True,
        })
    write_table("lane_002_queue", queue_rows)

    canonical_rows = list(read_csv(CANONICAL))
    alias_rows_phase0 = list(read_csv(ALIASES))
    extraction_by_sha = {r["canonical_source_id"]: r.get("extraction_status", "") for r in read_csv(EXTRACTION)}
    proposed_by_sha = {r["canonical_source_id"]: r for r in read_csv(PROPOSED)}

    metadata_by_sha: dict[str, list[dict]] = defaultdict(list)
    metadata_inputs = [
        (TARGETED_429, 60),
        (TARGETED_556, 60),
        (COMBINED, 70),
        (FOUR_BY, 80),
        (REMAINING, 85),
    ] + [(p, 100) for p in EXTERNAL_MANIFESTS]
    raw_metadata_records = 0
    for path, rank in metadata_inputs:
        for row in read_csv(path):
            record = standardize(row, path, rank)
            if not valid_sha(record["sha256"]):
                continue
            raw_metadata_records += 1
            metadata_by_sha[record["sha256"]].append(record)

    readiness_by_sha = {}
    for path in EXTERNAL_READINESS:
        for row in read_csv(path):
            sha = first(row, ["SHA_256"]).lower()
            if valid_sha(sha):
                readiness_by_sha[sha] = first(row, ["readiness_status", "readiness_hint"])

    source_index = []
    provenance_rows = []
    inference_rows = []
    path_rows = []
    sanitization_rows = []
    path_to_ids = defaultdict(list)
    readable_path_to_ids = defaultdict(list)
    unresolved_counts = Counter()
    family_counts = Counter()
    stage_counts = Counter()
    metadata_match_counts = Counter()

    for canonical in canonical_rows:
        sha = canonical["canonical_source_id"].lower()
        current_path = canonical["canonical_relative_path"]
        candidates = metadata_by_sha.get(sha, [])
        best = max(candidates, key=richness) if candidates else {}
        metadata_match_basis = "sha256_exact" if candidates else "phase0_path_only"
        metadata_match_counts[metadata_match_basis] += 1
        stage = provenance_stage(current_path)
        stage_counts[stage] += 1

        ext = normalized_extension(Path(current_path).suffix, current_path)
        original_filename = best.get("original_filename", "") or Path(current_path).name
        raw_title = best.get("source_title", "")
        if raw_title:
            title = raw_title
            title_basis = "explicit_source_title"
        else:
            title = Path(original_filename).stem or "Source document"
            title_basis = "original_filename_fallback"

        municipality = best.get("municipality", "")
        state = best.get("state", "")
        region = best.get("region", "") or REGION_BY_STATE.get(state, "")
        geography_basis = "explicit_source_review_metadata" if municipality and state else ("partial_source_review_metadata" if municipality or state else "unresolved")
        period, start_year, end_year, period_basis = parse_period(best.get("period_explicit", ""), title)
        family_raw = best.get("source_family_raw", "")
        family = normalize_family(family_raw, ext)
        family_basis = "explicit_source_review_metadata" if family_raw else ("extension_fallback" if family != "unknown" else "unresolved")
        original_url = best.get("original_url", "")
        url_host = urlparse(original_url).netloc.lower() if original_url else ""
        extraction_status = readiness_by_sha.get(sha) or best.get("extraction_status", "") or extraction_by_sha.get(sha, "")

        is_system_file = Path(current_path).name in {"retained_quota.lock", "retained_quota_state.json"}
        if is_system_file:
            family = "system_control_metadata"
            family_basis = "filename_exact"
            title = Path(current_path).name
            title_basis = "system_filename"
        family_counts[family] += 1

        state_slug = slug(state, 8, "state-unknown")
        municipality_slug = slug(municipality, 48, "municipality-unknown")
        family_slug = slug(family, 48, "family-unknown")
        period_slug = slug(period, 32, "period-unknown")
        title_slug = slug(title, 80, "source-document")
        sha_prefix = sha[:16] if valid_sha(sha) else hashlib.sha256(current_path.encode()).hexdigest()[:16]
        archive_filename = f"{sha_prefix}__{title_slug}{ext}"
        archive_path = f"originals/{state_slug}/{municipality_slug}/{family_slug}/{period_slug}/{archive_filename}"
        readable_path = f"originals/{state_slug}/{municipality_slug}/{family_slug}/{period_slug}/{title_slug}{ext}"
        path_to_ids[archive_path.casefold()].append(sha)
        readable_path_to_ids[readable_path.casefold()].append(sha)

        unresolved = []
        for field, value in [
            ("municipality", municipality), ("state", state), ("period", period),
            ("source_family", "" if family == "unknown" else family),
            ("original_url", original_url), ("source_title", raw_title),
            ("mime_type", best.get("mime_type", "")), ("extraction_status", extraction_status),
        ]:
            if not value:
                unresolved.append(field)
                unresolved_counts[field] += 1

        core_explicit = sum([
            geography_basis == "explicit_source_review_metadata",
            period_basis == "explicit_metadata",
            family_basis == "explicit_source_review_metadata",
            title_basis == "explicit_source_title",
            bool(original_url),
        ])
        metadata_confidence = "high" if core_explicit >= 4 else "medium" if core_explicit >= 2 else "limited"
        packaging_eligible = not is_system_file
        exclusion_reason = "non_source_quota_control_file" if is_system_file else ""
        source_index_id = "SRCIDX-" + sha[:20]
        provenance_id = "PROV-" + sha[:20]
        row = {
            "source_index_id": source_index_id,
            "canonical_source_id": sha,
            "sha256": sha,
            "archive_relative_path": archive_path,
            "canonical_original_path": current_path,
            "display_title": title,
            "display_title_basis": title_basis,
            "original_filename": original_filename,
            "extension": ext,
            "mime_type": best.get("mime_type", ""),
            "file_size_bytes": int(canonical.get("file_size_bytes") or 0),
            "source_family": family,
            "source_family_raw": family_raw,
            "document_type_raw": best.get("document_type_raw", ""),
            "municipality": municipality,
            "state": state,
            "region": region,
            "period_label": period,
            "period_start_year": start_year,
            "period_end_year": end_year,
            "geography_basis": geography_basis,
            "period_basis": period_basis,
            "source_family_basis": family_basis,
            "metadata_confidence": metadata_confidence,
            "original_url": original_url,
            "url_host": url_host,
            "official_source_flag": best.get("official_source_flag", ""),
            "extraction_status": extraction_status,
            "redistribution_status": canonical.get("redistribution_status", ""),
            "physical_copy_count": int(canonical.get("physical_copy_count") or 0),
            "alias_count": int(canonical.get("alias_count") or 0),
            "provenance_index_id": provenance_id,
            "metadata_match_basis": metadata_match_basis,
            "source_metadata_status": "complete_core" if not any(x in unresolved for x in ["municipality", "state", "period", "source_family"]) else "bounded_with_unresolved_fields",
            "unresolved_fields": "|".join(unresolved),
            "navigation_packaging_eligible": packaging_eligible,
            "exclusion_reason": exclusion_reason,
            "phase0_expected_source_library_path": proposed_by_sha.get(sha, {}).get("proposed_relative_path", canonical.get("expected_source_library_path", "")),
            "phase0_lineage": "source_archive_canonical_source_inventory.csv",
        }
        source_index.append(row)

        provenance_rows.append({
            "provenance_index_id": provenance_id,
            "source_index_id": source_index_id,
            "canonical_source_id": sha,
            "retrieval_stage": stage,
            "source_review_id": best.get("source_review_id", ""),
            "retained_source_id": best.get("retained_source_id", ""),
            "candidate_id": best.get("candidate_id", ""),
            "source_review_lane_id": best.get("source_review_lane_id", ""),
            "retrieved_timestamp": best.get("retrieved_timestamp", ""),
            "metadata_source_file": best.get("metadata_source_file", ""),
            "metadata_match_basis": metadata_match_basis,
            "phase0_inventory_source": CANONICAL.relative_to(REPO).as_posix(),
        })

        inference_rows.append({
            "source_index_id": source_index_id,
            "canonical_source_id": sha,
            "municipality": municipality,
            "state": state,
            "region": region,
            "geography_basis": geography_basis,
            "period_label": period,
            "period_start_year": start_year,
            "period_end_year": end_year,
            "period_basis": period_basis,
            "source_family": family,
            "source_family_raw": family_raw,
            "source_family_basis": family_basis,
            "display_title_basis": title_basis,
            "metadata_confidence": metadata_confidence,
            "unresolved_fields": "|".join(unresolved),
            "manual_review_priority": "exclude_non_source" if is_system_file else ("high" if metadata_confidence == "limited" else "medium" if metadata_confidence == "medium" else "low"),
        })

        reasons = []
        if title != unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii"):
            reasons.append("unicode_transliterated")
        if re.search(r"[^A-Za-z0-9]+", title):
            reasons.append("punctuation_or_space_normalized")
        if len(slug(title, 10000, "")) > 80:
            reasons.append("title_truncated_to_80_slug_characters")
        if Path(original_filename).name != archive_filename:
            reasons.append("stable_hash_prefix_and_normalized_title_applied")
        audit_reasons = [reason for reason in reasons if reason in {"unicode_transliterated", "title_truncated_to_80_slug_characters"}]
        if len(archive_filename) > 120:
            audit_reasons.append("filename_over_120_characters")
        if len(archive_path) > 240:
            audit_reasons.append("archive_path_over_240_characters")
        if audit_reasons:
            sanitization_rows.append({
                "source_index_id": source_index_id,
                "canonical_source_id": sha,
                "original_filename": original_filename,
                "source_title": title,
                "sanitized_filename": archive_filename,
                "extension": ext,
                "sanitization_reasons": "|".join(audit_reasons),
                "sanitized_filename_length": len(archive_filename),
                "archive_path_length": len(archive_path),
                "filename_within_120_characters": len(archive_filename) <= 120,
                "archive_path_within_240_characters": len(archive_path) <= 240,
            })
        path_rows.append({
            "source_index_id": source_index_id,
            "canonical_source_id": sha,
            "deterministic_archive_relative_path": archive_path,
            "readable_path_before_hash_disambiguation": readable_path,
            "path_design_version": "source-navigation-v1",
            "path_components": "state/municipality/source_family/period/hash16__title.ext",
            "physical_action_this_lane": "none",
        })

    source_index.sort(key=lambda r: r["canonical_source_id"])
    provenance_rows.sort(key=lambda r: r["canonical_source_id"])
    inference_rows.sort(key=lambda r: r["canonical_source_id"])
    path_rows.sort(key=lambda r: r["canonical_source_id"])
    sanitization_rows.sort(key=lambda r: r["canonical_source_id"])

    aliases_out = []
    for i, alias in enumerate(sorted(alias_rows_phase0, key=lambda r: (r["canonical_source_id"], r["alias_relative_path"])), 1):
        sha = alias["canonical_source_id"]
        aliases_out.append({
            "alias_record_id": f"ALIAS-{i:06d}",
            "source_index_id": "SRCIDX-" + sha[:20],
            "canonical_source_id": sha,
            "alias_relative_path": alias["alias_relative_path"],
            "alias_filename": Path(alias["alias_relative_path"]).name,
            "alias_type": alias["alias_type"],
            "alias_file_size_bytes": int(alias.get("file_size_bytes") or 0),
            "archive_treatment": "metadata_alias_only_no_duplicate_binary",
            "future_action": alias.get("future_action", ""),
            "phase0_lineage": "source_archive_alias_inventory.csv",
        })

    collision_rows = []
    collision_group = 0
    for collision_type, groups in [("exact_or_casefold_archive_path", path_to_ids), ("readable_path_before_hash", readable_path_to_ids)]:
        for path_key, ids in sorted(groups.items()):
            unique_ids = sorted(set(ids))
            if len(unique_ids) < 2:
                continue
            collision_group += 1
            collision_rows.append({
                "collision_group_id": f"PATHCOLL-{collision_group:06d}",
                "collision_type": collision_type,
                "path_key": path_key,
                "canonical_source_count": len(unique_ids),
                "canonical_source_ids": "|".join(unique_ids),
                "resolved_by_hash_prefix": collision_type == "readable_path_before_hash",
                "requires_manual_repair": collision_type == "exact_or_casefold_archive_path",
            })

    source_fields = [
        "source_index_id", "canonical_source_id", "sha256", "archive_relative_path", "canonical_original_path",
        "display_title", "display_title_basis", "original_filename", "extension", "mime_type", "file_size_bytes",
        "source_family", "source_family_raw", "document_type_raw", "municipality", "state", "region",
        "period_label", "period_start_year", "period_end_year", "geography_basis", "period_basis",
        "source_family_basis", "metadata_confidence", "original_url", "url_host", "official_source_flag",
        "extraction_status", "redistribution_status", "physical_copy_count", "alias_count", "provenance_index_id",
        "metadata_match_basis", "source_metadata_status", "unresolved_fields", "navigation_packaging_eligible",
        "exclusion_reason", "phase0_expected_source_library_path", "phase0_lineage",
    ]
    inference_attention_rows = [
        row for row in inference_rows
        if row["metadata_confidence"] != "high"
        or row["period_basis"] != "explicit_metadata"
        or row["display_title_basis"] != "explicit_source_title"
    ]
    write_table("SOURCE_INDEX", source_index, source_fields)
    write_table("source_aliases", aliases_out)
    write_table("source_provenance", provenance_rows)
    write_table("source_metadata_inference_audit", inference_attention_rows)
    write_table("deterministic_archive_path_map", path_rows)
    write_table("filename_sanitization_audit", sanitization_rows)
    write_table("archive_path_collision_audit", collision_rows, [
        "collision_group_id", "collision_type", "path_key", "canonical_source_count", "canonical_source_ids",
        "resolved_by_hash_prefix", "requires_manual_repair",
    ])

    schema = {
        "schema_name": "Gabriel Wages source-library navigation index",
        "schema_version": "1.0.0",
        "row_unit": "one exact-deduplicated canonical physical source object",
        "primary_key": "source_index_id",
        "canonical_identity": "canonical_source_id and sha256 are the Phase 0 SHA-256 content identity",
        "exclusions": "No project claims, claim classes, counterexamples, report conclusions, or analytical tables.",
        "fields": {field: {"type": "integer" if field in {"file_size_bytes", "physical_copy_count", "alias_count"} else "boolean" if field == "navigation_packaging_eligible" else "string"} for field in source_fields},
        "path_design": "originals/state/municipality/source_family/period/hash16__sanitized-title.ext",
        "path_safety": "ASCII lowercase slugs; bounded components; SHA-256 prefix disambiguation; casefold collision audit.",
    }
    (OUT / "SOURCE_INDEX_schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "SOURCE_INDEX_schema.md").write_text(
        "# SOURCE_INDEX schema\n\n"
        "**Row unit:** one exact-deduplicated canonical physical source object.\n\n"
        "The index is navigation metadata for a source-only archive. It records content identity, a deterministic archive path, title, geography, period, source family, original URL, extraction status, aliases, redistribution status, and provenance. Raw metadata and the basis for any inference remain separate. It contains no claims, conclusions, counterexamples, or report-specific analytical outputs.\n\n"
        "Archive paths use `originals/state/municipality/source_family/period/hash16__sanitized-title.ext`. The hash prefix provides deterministic collision resistance; the collision audit separately records readable-name collisions before the hash is added.\n",
        encoding="utf-8",
    )

    total = len(source_index)
    high = sum(r["metadata_confidence"] == "high" for r in source_index)
    medium = sum(r["metadata_confidence"] == "medium" for r in source_index)
    limited = sum(r["metadata_confidence"] == "limited" for r in source_index)
    exact_path_collisions = sum(r["collision_type"] == "exact_or_casefold_archive_path" for r in collision_rows)
    readable_collisions = sum(r["collision_type"] == "readable_path_before_hash" for r in collision_rows)
    coverage = {
        "status": "complete_with_bounded_metadata_gaps" if unresolved_counts else "complete",
        "canonical_source_rows": total,
        "navigation_packaging_eligible_rows": sum(bool(r["navigation_packaging_eligible"]) for r in source_index),
        "excluded_non_source_control_rows": sum(not bool(r["navigation_packaging_eligible"]) for r in source_index),
        "phase0_alias_rows": len(aliases_out),
        "raw_trusted_metadata_rows_indexed": raw_metadata_records,
        "sha256_exact_metadata_matches": metadata_match_counts["sha256_exact"],
        "phase0_path_only_rows": metadata_match_counts["phase0_path_only"],
        "metadata_confidence": {"high": high, "medium": medium, "limited": limited},
        "unresolved_field_counts": dict(sorted(unresolved_counts.items())),
        "unresolved_field_rates": {k: round(v / total, 6) for k, v in sorted(unresolved_counts.items())},
        "source_family_counts": dict(sorted(family_counts.items())),
        "retrieval_stage_counts": dict(sorted(stage_counts.items())),
        "archive_path_collision_groups": exact_path_collisions,
        "readable_pre_hash_collision_groups": readable_collisions,
        "maximum_archive_path_length": max(len(r["archive_relative_path"]) for r in source_index),
        "maximum_sanitized_filename_length": max(len(Path(r["archive_relative_path"]).name) for r in source_index),
        "source_binaries_read": False,
        "source_binaries_copied_or_modified": False,
        "claims_or_analytical_outputs_included": False,
    }
    (OUT / "source_navigation_coverage_summary.json").write_text(json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    unresolved_lines = "\n".join(f"- `{key}`: {value:,} ({value / total:.2%})" for key, value in sorted(unresolved_counts.items()))
    (OUT / "source_navigation_coverage_summary.md").write_text(
        "# Source navigation coverage summary\n\n"
        f"The navigation index contains **{total:,}** Phase 0 canonical objects. **{coverage['navigation_packaging_eligible_rows']:,}** are source-package candidates; **{coverage['excluded_non_source_control_rows']:,}** quota-control files are explicitly excluded. Exact SHA-256 metadata matches were found for **{coverage['sha256_exact_metadata_matches']:,}** objects.\n\n"
        f"Metadata confidence: {high:,} high, {medium:,} medium, and {limited:,} limited. These ratings describe navigation metadata completeness, not source quality.\n\n"
        "## Unresolved navigation fields\n\n" + unresolved_lines + "\n\n"
        f"The deterministic archive paths have **{exact_path_collisions}** exact or case-insensitive collisions. There are **{readable_collisions}** collision groups before adding the SHA-256 prefix; all are resolved by the stable prefix. No source binary was opened, copied, packaged, altered, or deleted.\n",
        encoding="utf-8",
    )

    checkpoint = {
        "lane_id": "lane_002",
        "status": "complete",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "row_unit": "one exact-deduplicated canonical physical source object",
        "canonical_source_rows": total,
        "packaging_eligible_rows": coverage["navigation_packaging_eligible_rows"],
        "alias_rows": len(aliases_out),
        "sha256_exact_metadata_matches": coverage["sha256_exact_metadata_matches"],
        "phase0_path_only_rows": coverage["phase0_path_only_rows"],
        "exact_archive_path_collisions": exact_path_collisions,
        "readable_pre_hash_collision_groups": readable_collisions,
        "source_binaries_read": False,
        "source_binaries_copied_modified_or_deleted": False,
        "claims_conclusions_or_analytical_tables_included": False,
        "writes_outside_lane_directory": False,
        "runtime_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
        "outputs": [
            "SOURCE_INDEX.csv.gz/schema.json/schema.md", "source_aliases.csv",
            "source_provenance.csv.gz", "source_metadata_inference_audit.csv.gz",
            "deterministic_archive_path_map.csv.gz", "filename_sanitization_audit.csv.gz",
            "archive_path_collision_audit.csv", "source_navigation_coverage_summary.json/md",
            "lane_002_queue.csv", "lane_002_summary.md",
        ],
    }
    (OUT / "lane_002_checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    (OUT / "lane_002_summary.md").write_text(
        "# Lane 2 summary: source-library navigation metadata\n\n"
        f"Lane 2 built a source-only navigation index for {total:,} Phase 0 canonical objects. The archive-relative path is deterministic and collision-resistant, while geography, period, source family, title, URL, extraction status, aliases, and provenance retain an explicit metadata basis.\n\n"
        f"- Packaging-eligible source objects: {coverage['navigation_packaging_eligible_rows']:,}\n"
        f"- Non-source quota-control objects excluded: {coverage['excluded_non_source_control_rows']:,}\n"
        f"- Exact SHA-256 metadata matches: {coverage['sha256_exact_metadata_matches']:,}\n"
        f"- Path-only unresolved metadata objects: {coverage['phase0_path_only_rows']:,}\n"
        f"- Exact/casefold archive-path collisions: {exact_path_collisions}\n"
        f"- Readable-name collisions resolved by hash prefix: {readable_collisions}\n"
        f"- Exact duplicate alias records preserved as metadata: {len(aliases_out):,}\n\n"
        "No claims, conclusions, counterexamples, report-specific visuals, or analytical tables were included. No source binary was opened, copied, packaged, modified, moved, or deleted.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
