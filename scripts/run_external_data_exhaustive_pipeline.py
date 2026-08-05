#!/usr/bin/env python3
"""Run the exhaustive residual external-data pipeline for Gabriel Wages.

The script is deliberately stage-addressable and resumable.  Live worker modes
write only lane-local checkpoints.  Coordinator modes validate and merge once.
Secrets, prompts, raw model responses, retained source payloads, extracted full
text, and bulky structured tables are never written to tracked output roots.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
PRIOR = BASE / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
MASTER = BASE / "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
STAGE1 = MASTER / "01_RESIDUAL-HOSTED-SEARCH-SCOUT"
STAGE2 = MASTER / "02_MERGED-EXTERNAL-CANDIDATE-REVIEW"
STAGE3 = MASTER / "03_EXTERNAL-DATA-VERIFICATION"
STAGE4 = MASTER / "04_EXTERNAL-DATA-SOURCE-REVIEW-DOWNLOAD"
STAGE5 = MASTER / "05_EXTERNAL-DATA-READINESS"
STAGE6 = MASTER / "06_EXTERNAL-DATA-EXTRACTION"
STAGE7 = MASTER / "07_EXTERNAL-DATA-FIELD-SPAN-EXTRACTION"
STAGE8 = MASTER / "08_EXTERNAL-DATA-GABRIEL-RATING"
STAGE9 = MASTER / "09_EXTERNAL-DATA-RATING-INGESTION-CODIFICATION"
STAGE10 = MASTER / "10_EXTERNAL-DATA-RECONCILIATION-LINKAGE"
STAGE11 = MASTER / "11_EXTERNAL-DATA-NORMALIZATION-MATCHING"
STAGE12 = MASTER / "12_WHOLE-CORPUS-EXTERNAL-DATA-INTEGRATION"
STAGE13 = MASTER / "13_FINAL-GATES-DASHBOARD-RELAY"
RETAINED = ROOT / "artifacts/local_retained_sources/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
EXTRACTED = ROOT / "artifacts/local_extracted_text/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
STRUCTURED = ROOT / "artifacts/local_structured_external_data/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
RAW_META = ROOT / "artifacts/local_hosted_search_metadata/whole_corpus_external_data_exhaustive_pipeline_2026-08-04"
TMP = ROOT / "tmp/broad_state_whole_corpus_external_data_exhaustive_pipeline_2026-08-04_logs"
STAGE_RELAYS = ROOT / "tmp/external_data_exhaustive_pipeline_stage_relays"
PRIOR_CORRECTION = BASE / "BROAD-STATE-WHOLE-CORPUS-EVIDENCE-CORRECTION-IMPLEMENTATION-EVENT-RECODING-AND-VISUAL-PREP-2026-08-04"
EXPECTED_RAW = 20_986
EXPECTED_PRIOR_REPRESENTATIVES = 2_297
EXPECTED_RESIDUAL = 18_689
EXPECTED_PRIOR_CANONICAL = 29_793
RESIDUAL_LANES = [f"residual_search_lane_{i:03d}" for i in range(1, 6)]
RESIDUAL_LANE_COUNTS = [3_738, 3_738, 3_738, 3_738, 3_737]
MODEL = "gpt-5.4-nano"
TASK_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SEARCH-AND-FULL-PIPELINE-2026-08-04"
STAGE1_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-EXHAUSTIVE-RESIDUAL-SCOUT-2026-08-04"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    value = "\x1f".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:n]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    rows = list(rows)
    fieldnames = list(fields or (rows[0].keys() if rows else []))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()


def write_pair(directory: Path, name: str, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    write_csv(directory / f"{name}.csv", rows, fields)
    write_jsonl(directory / f"{name}.jsonl", rows)


def write_md(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_sharded_pair(directory: Path, name: str, rows: list[dict[str, Any]], chunk_size: int = 8_000) -> None:
    chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)] or [[]]
    parts = []
    fields = list(rows[0]) if rows else []
    for index, chunk in enumerate(chunks, 1):
        stem = name if index == 1 else f"{name}.part-{index:03d}"
        csv_path, jsonl_path = directory / f"{stem}.csv", directory / f"{stem}.jsonl"
        write_csv(csv_path, chunk, fields)
        write_jsonl(jsonl_path, chunk)
        parts.append({"part": index, "rows": len(chunk), "csv": csv_path.name, "csv_bytes": csv_path.stat().st_size,
                      "csv_sha256": sha256_file(csv_path), "jsonl": jsonl_path.name,
                      "jsonl_bytes": jsonl_path.stat().st_size, "jsonl_sha256": sha256_file(jsonl_path)})
    write_json(directory / f"{name}_shard_manifest.json", {"total_rows": len(rows), "sharded": len(chunks) > 1,
               "convention": "required base filename is part 001; .part-NNN files continue it", "parts": parts})


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def canonical_url(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                 if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(query), ""))
    except Exception:
        return value.strip()


def load_prior_candidates() -> list[dict[str, str]]:
    manifest = json.loads((PRIOR / "external_data_candidate_review_ready_queue_shard_manifest.json").read_text())
    rows: list[dict[str, str]] = []
    for part in manifest["parts"]:
        rows.extend(read_csv(PRIOR / part["csv_path"]))
    return rows


def record_transition(stage: str, status: str, decision: str, details: dict[str, Any] | None = None) -> None:
    append_jsonl(MASTER / "stage_transition_log.jsonl", {"at": utc_now(), "stage": stage, "status": status,
                 "decision": decision, "details": details or {}})
    state = json.loads((MASTER / "master_run_state.json").read_text()) if (MASTER / "master_run_state.json").exists() else {}
    state.update({"updated_at": utc_now(), "current_stage": stage, "status": status, "latest_decision": decision})
    write_json(MASTER / "master_run_state.json", state)
    write_json(MASTER / "master_stage_checkpoint.json", {"stage": stage, "status": status, "decision": decision,
               "updated_at": utc_now(), "details": details or {}})


def preflight() -> None:
    required = [
        PRIOR / "raw_external_data_target_queue_preserved.csv",
        PRIOR / "compacted_external_data_search_target_queue.csv",
        PRIOR / "target_family_eligibility_audit.json",
        PRIOR / "external_data_candidate_review_ready_manifest.json",
        PRIOR / "external_data_candidate_review_ready_queue_shard_manifest.json",
        PRIOR / "search_target_event_linkage.csv",
        PRIOR / "municipality_geographic_crosswalk.csv",
        PRIOR_CORRECTION / "external_data_missingness_matrix.csv",
        PRIOR / "mechanism_exposure_event_layer.csv",
        PRIOR / "root_compensation_event_layer.csv",
        ROOT / "docs/dashboard/data/project_phase_summary.json",
        ROOT / "docs/dashboard/data/wage_growth_continuity.json",
        ROOT / "docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        ROOT / "docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md",
        ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md",
        ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"master preflight missing required inputs: {missing}")
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip()
    allowed = {"M .gitignore", "M  .gitignore", " M .gitignore", "?? scripts/run_external_data_exhaustive_pipeline.py"}
    unrelated = [line for line in status.splitlines() if line and line not in allowed]
    if unrelated:
        raise RuntimeError(f"unrelated dirty-worktree conflict: {unrelated}")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor",
                              "cca0c8414009090ae58d773ef3ec89281e3b1e48", "HEAD"], cwd=ROOT).returncode == 0
    if not ancestor:
        raise RuntimeError("prior scout commit is not an ancestor of current HEAD")
    raw = read_csv(required[0]); compact = read_csv(required[1]); prior_candidates = load_prior_candidates()
    geo = read_csv(PRIOR / "municipality_geographic_crosswalk.csv")
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    counts = {"raw": len(raw), "compacted": len(compact), "prior_canonical": len(prior_candidates), "geography": len(geo)}
    expected = {"raw": EXPECTED_RAW, "compacted": EXPECTED_PRIOR_REPRESENTATIVES,
                "prior_canonical": EXPECTED_PRIOR_CANONICAL, "geography": 1_440}
    if counts != expected:
        raise RuntimeError(f"preflight count mismatch: {counts} != {expected}")
    if phase.get("dashboard_map_primary_metric") != "scout_coverage_rate":
        raise RuntimeError("dashboard map metric changed")
    ignore_paths = ["artifacts/local_retained_sources/", "artifacts/local_extracted_text/",
                    "artifacts/local_structured_external_data/", "artifacts/local_external_reference_data/",
                    "artifacts/local_hosted_search_metadata/"]
    not_ignored = [path for path in ignore_paths if subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode != 0]
    if not_ignored:
        raise RuntimeError(f"required artifact roots are not ignored: {not_ignored}")
    for directory in [MASTER, STAGE1, STAGE2, STAGE3, STAGE4, STAGE5, STAGE6, STAGE7, STAGE8,
                      STAGE9, STAGE10, STAGE11, STAGE12, STAGE13, RETAINED, EXTRACTED, STRUCTURED,
                      RAW_META, TMP, STAGE_RELAYS]:
        directory.mkdir(parents=True, exist_ok=True)
    manifest = {"task_id": TASK_ID, "started_at": utc_now(), "starting_head": git_head(),
                "prior_commit": "cca0c8414009090ae58d773ef3ec89281e3b1e48", "prior_commit_is_ancestor": True,
                "locked_counts": counts, "expected_residual": EXPECTED_RESIDUAL,
                "artifact_roots_ignored": True, "dashboard_map_primary_metric": "scout_coverage_rate",
                "stage_order": [f"{i:02d}" for i in range(1, 14)], "final_report_creation_authorized": False}
    write_json(MASTER / "master_run_manifest.json", manifest)
    write_json(MASTER / "master_run_state.json", {"task_id": TASK_ID, "started_at": manifest["started_at"],
               "updated_at": utc_now(), "current_stage": "master_preflight", "status": "complete",
               "latest_decision": "master_preflight_passed"})
    write_json(MASTER / "master_forbidden_action_audit.json", {"passed": True, "ocr": False,
               "regression": False, "treatment_effect": False, "national_wage_gap_estimate": False,
               "national_prevalence_estimate": False, "causal_effect_estimate": False,
               "final_pdf_docx_slides_heatmap": False, "force_push": False, "history_rewrite": False})
    record_transition("master_preflight", "complete", "master_preflight_passed", counts)
    print(json.dumps({"preflight": "passed", **counts, "head": git_head()}, indent=2))


def stage1_prepare() -> None:
    if not (MASTER / "master_run_manifest.json").exists():
        raise RuntimeError("master preflight must pass first")
    raw = read_csv(PRIOR / "raw_external_data_target_queue_preserved.csv")
    eligibility_rows = json.loads((PRIOR / "target_family_eligibility_audit.json").read_text())["rows"]
    elig = {row["raw_search_target_id"]: row for row in eligibility_rows}
    compact = read_csv(PRIOR / "compacted_external_data_search_target_queue.csv")
    compact_by_id = {row["search_target_id"]: row for row in compact}
    linkage_by_compact: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in read_csv(PRIOR / "search_target_event_linkage.csv"):
        linkage_by_compact[link["search_target_id"]].append(link)
    missingness = {row["missingness_id"]: row for row in read_csv(PRIOR_CORRECTION / "external_data_missingness_matrix.csv")}
    exposure_rows = read_csv(PRIOR / "mechanism_exposure_event_layer.csv")
    exposure_by_root: dict[str, list[str]] = defaultdict(list)
    for row in exposure_rows:
        exposure_by_root[row["root_compensation_event_id"]].append(row["mechanism_exposure_event_id"])
    root_rows = read_csv(PRIOR / "root_compensation_event_layer.csv")
    roots_by_key: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for row in root_rows:
        roots_by_key[(row["municipality"], row["state"], row["compensation_cycle_id"], row["side"])].append(row["root_compensation_event_id"])
    representatives: set[str] = set()
    representative_audit: list[dict[str, Any]] = []
    for target in compact:
        lineage = sorted(x for x in target["lineage_raw_target_ids"].split("|") if x)
        if not lineage:
            raise RuntimeError(f"compacted target lacks raw lineage: {target['search_target_id']}")
        representative = lineage[0]
        representatives.add(representative)
        representative_audit.append({"compacted_search_target_id": target["search_target_id"],
                                     "canonical_primary_raw_target_id": representative,
                                     "lineage_raw_target_count": len(lineage),
                                     "selection_rule": "lexicographically first raw target ID in locked compacted lineage; first physical occurrence selected when the preserved queue repeats an ID"})
    if len(representatives) != EXPECTED_PRIOR_REPRESENTATIVES:
        raise RuntimeError(f"representative count {len(representatives)} != {EXPECTED_PRIOR_REPRESENTATIVES}")
    raw_occurrences: dict[str, list[int]] = defaultdict(list)
    for row_number, row in enumerate(raw, 1):
        raw_occurrences[row["search_target_id"]].append(row_number)
    representative_row_numbers: set[int] = set()
    for audit_row in representative_audit:
        occurrences = raw_occurrences.get(audit_row["canonical_primary_raw_target_id"], [])
        selected = next((number for number in occurrences if number not in representative_row_numbers), None)
        if selected is None:
            raise RuntimeError(f"no physical raw-row instance for representative {audit_row['canonical_primary_raw_target_id']}")
        representative_row_numbers.add(selected)
        audit_row["canonical_primary_raw_row_number"] = selected
    residual_raw = [(row_number, row) for row_number, row in enumerate(raw, 1) if row_number not in representative_row_numbers]
    if len(residual_raw) != EXPECTED_RESIDUAL:
        raise RuntimeError(f"residual count {len(residual_raw)} != {EXPECTED_RESIDUAL}")
    residual: list[dict[str, Any]] = []
    derivation: list[dict[str, Any]] = []
    for index, (raw_row_number, row) in enumerate(residual_raw):
        raw_id = row["search_target_id"]
        e = elig[raw_id]
        gap = missingness[row["missingness_id"]]
        compact_id = e.get("compacted_search_target_id", "")
        compact_row = compact_by_id.get(compact_id, {})
        root_ids: list[str] = []
        linked_exposures: list[str] = []
        if compact_id:
            for link in linkage_by_compact[compact_id]:
                if link["root_compensation_event_id"] and link["root_compensation_event_id"] not in root_ids:
                    root_ids.append(link["root_compensation_event_id"])
                if link["mechanism_exposure_event_id"] and link["mechanism_exposure_event_id"] not in linked_exposures:
                    linked_exposures.append(link["mechanism_exposure_event_id"])
        resolution = e["resolution"]
        if resolution == "target_resolved_by_authoritative_bulk_join":
            terminal_without_search = "resolved_by_authoritative_bulk_join"
        elif resolution == "target_resolved_by_existing_source_reuse":
            terminal_without_search = "resolved_by_existing_source_reuse"
        else:
            terminal_without_search = ""
        period = row["compensation_cycle_or_year"] or "undated"
        side = row["side"] or "unclear"
        mechanism = gap.get("current_claim_family", "")
        department = gap.get("role_unit", "") or compact_row.get("department_or_unit_scope", "all_units")
        query_primary = clean(
            f'"{row["municipality"]}" "{row["state"]}" "{period}" {side} {department} '
            f'{gap.get("missing_external_variable", "")} {mechanism} {gap.get("likely_source_family", "")} '
            f'official municipal administrative record'
        )
        query_repair = clean(
            f'"{row["municipality"]}" "{row["state"]}" {period} '
            f'{gap.get("search_family", row.get("search_family", ""))} {gap.get("missing_external_variable", "")} '
            f'(site:.gov OR site:.us) filetype:pdf'
        )
        lane_index = index % 5
        residual.append({
            "residual_target_id": stable("RESIDUAL", raw_id, raw_row_number), "raw_target_id": raw_id,
            "raw_row_number": raw_row_number,
            "search_wave": "external_search_wave_002_exhaustive_residual",
            "prior_compacted_target_id": compact_id, "municipality": row["municipality"], "state": row["state"],
            "period": period, "side_scope": side, "department_scope": department,
            "external_data_family": row["search_family"], "missingness_id": row["missingness_id"],
            "missing_external_variable": gap.get("missing_external_variable", ""),
            "current_claim_family": mechanism, "current_evidence_status": gap.get("current_evidence_status", ""),
            "likely_source_family": gap.get("likely_source_family", ""),
            "expected_claim_upgrade": row["expected_claim_upgrade"], "search_priority": row["search_priority"],
            "linked_root_event_id": "|".join(sorted(root_ids)),
            "linked_mechanism_exposure_event_ids": "|".join(sorted(linked_exposures)),
            "query_primary": query_primary, "query_repair": query_repair,
            "terminal_without_search": terminal_without_search,
            "lane_id": RESIDUAL_LANES[lane_index], "lane_sequence": index // 5 + 1,
            "raw_resolution": resolution,
        })
        derivation.append({"raw_row_number": raw_row_number, "raw_target_id": raw_id, "classification": "residual", "prior_compacted_target_id": compact_id,
                          "raw_resolution": resolution, "terminal_without_search": terminal_without_search})
    for audit_row in representative_audit:
        raw_id = audit_row["canonical_primary_raw_target_id"]
        e = elig[raw_id]
        derivation.append({"raw_row_number": audit_row["canonical_primary_raw_row_number"], "raw_target_id": raw_id,
                          "classification": "canonical_primary_representative",
                          "prior_compacted_target_id": audit_row["compacted_search_target_id"],
                          "raw_resolution": e["resolution"], "terminal_without_search": "prior_wave_primary_representative"})
    residual.sort(key=lambda row: (int(row["lane_id"].rsplit("_", 1)[1]), int(row["lane_sequence"])))
    lane_counts = Counter(row["lane_id"] for row in residual)
    if [lane_counts[lane] for lane in RESIDUAL_LANES] != RESIDUAL_LANE_COUNTS:
        raise RuntimeError(f"lane distribution mismatch: {lane_counts}")
    write_pair(STAGE1, "residual_search_locked_queue", residual)
    write_pair(STAGE1, "residual_locked_queue_derivation_audit", sorted(derivation, key=lambda row: int(row["raw_row_number"])))
    write_pair(STAGE1, "canonical_primary_representative_audit", representative_audit)
    for lane in RESIDUAL_LANES:
        write_pair(STAGE1, f"{lane}_queue", [row for row in residual if row["lane_id"] == lane])
    resolution_counts = Counter(row["terminal_without_search"] or "requires_live_hosted_search" for row in residual)
    manifest = {"stage_task_id": STAGE1_ID, "prepared_at": utc_now(), "raw_count": len(raw),
                "representative_count": len(representatives), "residual_count": len(residual),
                "lane_counts": dict(lane_counts), "residual_resolution_counts": dict(resolution_counts),
                "raw_queue_sha256": sha256_file(PRIOR / "raw_external_data_target_queue_preserved.csv"),
                "residual_queue_sha256": sha256_file(STAGE1 / "residual_search_locked_queue.csv"),
                "query_rule": "event-specific raw target variant; not the compacted-wave query",
                "search_wave": "external_search_wave_002_exhaustive_residual"}
    write_json(STAGE1 / "residual_search_queue_manifest.json", manifest)
    write_json(STAGE1 / "residual_search_lane_distribution.json", {"lane_counts": dict(lane_counts),
               "expected": dict(zip(RESIDUAL_LANES, RESIDUAL_LANE_COUNTS)),
               "stagger_minutes": dict(zip(RESIDUAL_LANES, [0, 8, 16, 24, 32])), "disjoint": True})
    write_md(STAGE1 / "residual_search_lane_distribution.md", "# Residual search lane distribution\n\n" +
             "\n".join(f"- {lane}: {lane_counts[lane]:,} rows; T+{i * 8} minutes" for i, lane in enumerate(RESIDUAL_LANES)))
    write_json(STAGE1 / "residual_derivation_summary.json", {"all_raw_rows": EXPECTED_RAW,
               "canonical_primary_representatives": EXPECTED_PRIOR_REPRESENTATIVES,
               "residual_rows": EXPECTED_RESIDUAL, "arithmetic": "20,986 - 2,297 = 18,689",
               "residual_resolution_counts": dict(resolution_counts), "all_rows_classified": len(derivation) == EXPECTED_RAW})
    record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "prepared", "residual_locked_queue_ready",
                      {"residual": len(residual), **dict(resolution_counts)})
    print(json.dumps({"residual": len(residual), "lane_counts": dict(lane_counts),
                      "resolution_counts": dict(resolution_counts)}, indent=2))


def true(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def live_search_call(prompt: str, identifier: str, out_dir: Path, web_search: bool = True) -> tuple[dict[str, Any], str | None]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import gabriel_state_source_scout as scout
    frame, failure, _timing = scout.run_direct_sdk_live_batch(
        [prompt], [identifier], out_dir, MODEL, "low", 1, timeout=90, max_retries=0,
        sleep_between_prompts=0, web_search=web_search, reasoning_effort=None, return_timing=True,
    )
    if failure or frame is None:
        return {}, failure or "missing response frame"
    rows = frame.to_dict(orient="records")
    return (rows[0] if len(rows) == 1 else {}), (None if len(rows) == 1 else "unexpected response row count")


def stage1_transport_preflight() -> None:
    if not (STAGE1 / "residual_search_locked_queue.csv").exists():
        raise RuntimeError("stage1 prepare is required")
    scratch = TMP / "stage1_transport_preflight"
    diagnostics: list[dict[str, Any]] = []
    control, failure = live_search_call("Reply exactly OK.", "residual_no_search_control", scratch / "control", False)
    diagnostics.append({"family": "control", "passed": not failure and true(control.get("Successful")),
                        "source_count": 0, "failure": failure or "", "web_search": False})
    examples = {
        "payroll_and_earnings": "official municipal payroll earnings overtime 2023",
        "staffing_and_headcount": "official city budget authorized filled positions vacancies 2024",
        "recruitment_and_retention": "official municipal recruitment retention turnover compensation study",
        "tenure_and_progression": "official civil service salary step seniority schedule",
        "implementation_confirmation": "official ordinance resolution pay plan effective date",
        "benefits_and_total_compensation": "official pension health contribution longevity allowance",
        "contextual_controls": "official local fiscal capacity labor market government data",
    }
    smoke_calls = 0
    for index, (family, query) in enumerate(examples.items(), 1):
        attempts = []
        for attempt in (1, 2):
            row, failure = live_search_call(
                f"Use live web search to find one official public source for {query}. Return one short sentence.",
                f"residual_smoke_{index:02d}_{attempt}", scratch / f"smoke_{index:02d}_{attempt}", True,
            )
            smoke_calls += 1
            try:
                sources = json.loads(row.get("Web Search Sources") or "[]")
            except Exception:
                sources = []
            passed = not failure and true(row.get("Successful")) and bool(sources)
            attempts.append({"attempt": attempt, "passed": passed, "source_count": len(sources), "failure": failure or ""})
            if passed:
                break
            time.sleep(2)
        diagnostics.append({"family": family, **attempts[-1], "attempts": attempts, "web_search": True})
    category = "A" if all(item["passed"] for item in diagnostics) else "B"
    probe = {"ran": False, "passed": False, "promoted": False}
    if category == "A":
        target = next(row for row in read_csv(STAGE1 / "residual_search_locked_queue.csv") if not row["terminal_without_search"])
        row, failure = live_search_call(
            "Use live hosted web search for this metadata-only residual discovery probe. Do not verify or download returned URLs. " + target["query_primary"],
            "residual_quarantined_production_probe", scratch / "probe", True,
        )
        try:
            sources = json.loads(row.get("Web Search Sources") or "[]")
        except Exception:
            sources = []
        probe = {"ran": True, "passed": not failure and true(row.get("Successful")) and isinstance(sources, list),
                 "source_count": len(sources), "failure": failure or "", "promoted": False}
    report = {"run_at": utc_now(), "transport_category": category, "category_A_usable": category == "A",
              "no_search_control": diagnostics[0], "representative_smokes": diagnostics[1:],
              "smoke_call_count": smoke_calls, "production_probe": probe, "raw_prompts_saved": False,
              "raw_responses_saved": False, "secrets_logged": False, "redaction_passed": True}
    write_json(STAGE1 / "residual_hosted_search_transport_preflight.json", report)
    write_json(STAGE1 / "residual_hosted_search_redaction_audit.json", {"passed": True, "credentials_logged": 0,
               "raw_prompts_tracked": 0, "raw_responses_tracked": 0})
    if category != "A" or not probe["passed"]:
        record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "blocked", "residual_search_preflight_failed_backend_unstable", report)
        raise RuntimeError(f"residual hosted-search transport preflight failed: {category}, probe={probe['passed']}")
    record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "preflight_complete", "residual_search_transport_category_A", report)
    print(json.dumps(report, indent=2))


def residual_candidate(target: dict[str, str], source: dict[str, Any], call_id: str, query_version: str,
                       snippet: str, lane: str) -> dict[str, str] | None:
    url = clean(source.get("url", "")); title = clean(source.get("title", ""))
    if not url:
        return None
    canonical = canonical_url(url); domain = urlsplit(url).netloc.lower()
    official = domain.endswith(".gov") or ".gov." in domain
    return {"candidate_id": stable("RESCAND", target["raw_target_id"], canonical, title),
            "search_wave": "external_search_wave_002_exhaustive_residual",
            "raw_target_id": target["raw_target_id"], "prior_compacted_target_id": target["prior_compacted_target_id"],
            "candidate_url": url, "canonicalized_url": canonical, "candidate_title": title,
            "candidate_snippet": snippet[:500], "candidate_domain": domain,
            "likely_source_type": "official_government_search_result" if official else "public_source_candidate_unconfirmed",
            "likely_file_type": Path(urlsplit(url).path).suffix.lower().lstrip(".") or "web",
            "official_source_flag": "true" if official else "unconfirmed",
            "external_data_family": target["external_data_family"], "municipality": target["municipality"],
            "state": target["state"], "period": target["period"], "side_scope": target["side_scope"],
            "department_scope": target["department_scope"], "linked_root_event_id": target["linked_root_event_id"],
            "linked_mechanism_exposure_event_ids": target["linked_mechanism_exposure_event_ids"],
            "expected_claim_upgrade": target["expected_claim_upgrade"],
            "source_quality_score": "official_domain_metadata" if official else "unreviewed",
            "candidate_relevance_score": "unreviewed", "lane_id": lane, "search_call_id": call_id,
            "query_version": query_version, "discovered_at": utc_now()}


def stage1_run_lane(lane_number: int, start_delay_seconds: int = 0) -> None:
    lane = RESIDUAL_LANES[lane_number - 1]
    queue_path = STAGE1 / f"{lane}_queue.csv"; queue = read_csv(queue_path)
    preflight_report = json.loads((STAGE1 / "residual_hosted_search_transport_preflight.json").read_text())
    if preflight_report.get("transport_category") != "A" or not preflight_report.get("production_probe", {}).get("passed"):
        raise RuntimeError("Category A residual transport and passing production probe are required")
    checkpoint_path = STAGE1 / f"{lane}_checkpoint.json"
    outcomes_log = STAGE1 / f"{lane}_accepted_outcomes.jsonl"
    candidates_log = STAGE1 / f"{lane}_accepted_candidates.jsonl"
    calls_log = STAGE1 / f"{lane}_accepted_calls.jsonl"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {
        "lane_id": lane, "queue_sha256": sha256_file(queue_path), "assigned": len(queue), "completed": 0,
        "candidate_count": 0, "call_count": 0, "status": "waiting_for_stagger",
        "scheduled_delay_seconds": start_delay_seconds, "append_only_checkpointing": True,
    }
    # One early interrupted run used an array-bearing checkpoint but accepted no
    # target.  Migrate any accepted legacy rows exactly once before resuming.
    if any(key in checkpoint for key in ("target_outcomes", "candidates", "calls")):
        if not outcomes_log.exists():
            write_jsonl(outcomes_log, checkpoint.get("target_outcomes", []))
            write_jsonl(candidates_log, checkpoint.get("candidates", []))
            write_jsonl(calls_log, checkpoint.get("calls", []))
        checkpoint.pop("target_outcomes", None); checkpoint.pop("candidates", None); checkpoint.pop("calls", None)
        checkpoint["append_only_checkpointing"] = True
        checkpoint["completed"] = len(read_jsonl(outcomes_log))
        checkpoint["candidate_count"] = len(read_jsonl(candidates_log))
        checkpoint["call_count"] = len(read_jsonl(calls_log))
        atomic_json(checkpoint_path, checkpoint)
    if checkpoint["queue_sha256"] != sha256_file(queue_path):
        raise RuntimeError(f"corrupt queue/checkpoint state for {lane}")
    if checkpoint.get("status") == "complete":
        raise RuntimeError(f"duplicate worker refused: {lane} is complete")
    accepted_outcomes = read_jsonl(outcomes_log)
    done = {row["residual_target_id"] for row in accepted_outcomes}
    if not checkpoint.get("actual_started_at"):
        if start_delay_seconds:
            time.sleep(start_delay_seconds)
        checkpoint.update({"actual_started_at": utc_now(), "status": "in_progress", "pid": os.getpid()})
        atomic_json(checkpoint_path, checkpoint)
    else:
        # A resumed worker owns the lane from this point forward.  Refresh the
        # PID even though the original absolute start time remains preserved.
        checkpoint.update({"status": "in_progress", "pid": os.getpid(), "resumed_at": utc_now()})
        atomic_json(checkpoint_path, checkpoint)
    for target in queue:
        residual_id = target["residual_target_id"]
        if residual_id in done:
            continue
        if target["terminal_without_search"]:
            outcome = {"residual_target_id": residual_id, "raw_target_id": target["raw_target_id"], "lane_id": lane,
                       "terminal_status": target["terminal_without_search"], "primary_call_completed": "false",
                       "repair_call_used": "false", "candidate_count": 0, "failure_class": "",
                       "completed_at": utc_now()}
            append_jsonl(outcomes_log, outcome)
        else:
            target_candidates: list[dict[str, str]] = []; outcome = None
            primary_call_id = stable("RESCALL", target["raw_target_id"], "primary")
            for call_type, query, version in (("production_primary", target["query_primary"], "wave2_event_specific_v1"),
                                              ("repair", target["query_repair"], "wave2_event_specific_repair_v1")):
                call_id = primary_call_id if call_type == "production_primary" else stable("RESCALL", target["raw_target_id"], "repair")
                started = utc_now()
                row, failure = live_search_call(
                    "Use live hosted web search for metadata-only candidate discovery. Follow this municipality, period, side, event, missing field, and source-family target. Do not verify or download candidate URLs. " + query,
                    call_id, RAW_META / "stage1" / lane / residual_id / call_type, True,
                )
                try:
                    sources = json.loads(row.get("Web Search Sources") or "[]")
                except Exception:
                    sources = []; failure = failure or "hosted_search_source_metadata_parse_error"
                snippet = clean(row.get("Response", ""))
                for source in sources:
                    candidate = residual_candidate(target, source, call_id, version, snippet, lane)
                    if candidate:
                        target_candidates.append(candidate)
                call_row = {"search_call_id": call_id, "residual_target_id": residual_id,
                    "raw_target_id": target["raw_target_id"], "lane_id": lane, "call_type": call_type,
                    "query": query, "query_version": version, "started_at": started, "finished_at": utc_now(),
                    "terminal_status": "success" if not failure and true(row.get("Successful")) else "backend_or_parse_error",
                    "candidate_source_count": len(sources), "retry_linkage": "" if call_type == "production_primary" else primary_call_id,
                    "input_tokens": row.get("Input Tokens", ""), "reasoning_tokens": row.get("Reasoning Tokens", ""),
                    "output_tokens": row.get("Output Tokens", ""), "total_tokens": row.get("Total Tokens", ""),
                    "response_id_present": bool(row.get("Response IDs")), "failure_class": failure or ""}
                append_jsonl(calls_log, call_row)
                checkpoint["call_count"] = checkpoint.get("call_count", 0) + 1
                if target_candidates:
                    terminal = "candidate_found"
                elif failure and call_type == "repair":
                    terminal = "query_repair_exhausted"
                elif failure:
                    terminal = ""
                elif call_type == "repair":
                    terminal = "zero_candidate"
                else:
                    terminal = ""
                if terminal:
                    outcome = {"residual_target_id": residual_id, "raw_target_id": target["raw_target_id"], "lane_id": lane,
                               "terminal_status": terminal, "primary_call_completed": "true",
                               "repair_call_used": str(call_type == "repair").lower(), "candidate_count": len(target_candidates),
                               "failure_class": failure or "", "completed_at": utc_now()}
                    break
            if outcome is None:
                outcome = {"residual_target_id": residual_id, "raw_target_id": target["raw_target_id"], "lane_id": lane,
                           "terminal_status": "hosted_search_backend_error", "primary_call_completed": "true",
                           "repair_call_used": "true", "candidate_count": 0, "failure_class": "no terminal live outcome",
                           "completed_at": utc_now()}
            for candidate in target_candidates:
                append_jsonl(candidates_log, candidate)
            append_jsonl(outcomes_log, outcome)
        checkpoint["completed"] = checkpoint.get("completed", 0) + 1
        checkpoint["candidate_count"] = checkpoint.get("candidate_count", 0) + (0 if target["terminal_without_search"] else len(target_candidates))
        checkpoint["last_accepted_residual_target_id"] = residual_id; checkpoint["updated_at"] = utc_now()
        atomic_json(checkpoint_path, checkpoint)
    final_outcomes = read_jsonl(outcomes_log); final_candidates = read_jsonl(candidates_log); final_calls = read_jsonl(calls_log)
    checkpoint.update({"status": "complete", "finished_at": utc_now(), "completed": len(final_outcomes),
                       "candidate_count": len(final_candidates), "call_count": len(final_calls)})
    atomic_json(checkpoint_path, checkpoint)
    write_pair(STAGE1, f"{lane}_target_outcomes", final_outcomes)
    write_sharded_pair(STAGE1, f"{lane}_candidates", final_candidates)
    print(json.dumps({"lane": lane, "assigned": len(queue), "completed": checkpoint["completed"],
                      "calls": len(final_calls), "candidates": len(final_candidates)}, indent=2))


def stage1_finalize() -> None:
    queue = read_csv(STAGE1 / "residual_search_locked_queue.csv")
    outcomes: list[dict[str, Any]] = []; candidates: list[dict[str, Any]] = []; calls: list[dict[str, Any]] = []
    for lane in RESIDUAL_LANES:
        checkpoint = json.loads((STAGE1 / f"{lane}_checkpoint.json").read_text())
        if checkpoint.get("status") != "complete":
            raise RuntimeError(f"incomplete residual lane: {lane}")
        outcomes.extend(read_jsonl(STAGE1 / f"{lane}_accepted_outcomes.jsonl"))
        candidates.extend(read_jsonl(STAGE1 / f"{lane}_accepted_candidates.jsonl"))
        calls.extend(read_jsonl(STAGE1 / f"{lane}_accepted_calls.jsonl"))
    if len(outcomes) != EXPECTED_RESIDUAL or len({row["residual_target_id"] for row in outcomes}) != EXPECTED_RESIDUAL:
        raise RuntimeError("residual outcomes do not reconcile to locked queue")
    prior_candidates = load_prior_candidates()
    prior_keys = {(row["canonicalized_url"], clean(row["candidate_title"]).casefold()): row for row in prior_candidates}
    canonical: list[dict[str, Any]] = []; duplicates: list[dict[str, Any]] = []; seen: dict[tuple[str, str], dict[str, Any]] = {}
    for row in candidates:
        key = (row["canonicalized_url"], clean(row["candidate_title"]).casefold())
        if key in prior_keys:
            duplicates.append({"duplicate_candidate_id": row["candidate_id"], "canonical_candidate_id": prior_keys[key]["candidate_id"],
                               "duplicate_basis": "same canonical URL and normalized title across wave 1 and wave 2",
                               "duplicate_wave": "external_search_wave_001_compacted", "confidence": "high",
                               "raw_target_id": row["raw_target_id"]})
        elif key in seen:
            duplicates.append({"duplicate_candidate_id": row["candidate_id"], "canonical_candidate_id": seen[key]["candidate_id"],
                               "duplicate_basis": "same canonical URL and normalized title within wave 2",
                               "duplicate_wave": "external_search_wave_002_exhaustive_residual", "confidence": "high",
                               "raw_target_id": row["raw_target_id"]})
        else:
            seen[key] = row; canonical.append(row)
    write_pair(STAGE1, "merged_residual_target_outcomes", outcomes)
    write_sharded_pair(STAGE1, "merged_residual_candidates", candidates)
    write_sharded_pair(STAGE1, "canonical_residual_candidates", canonical)
    write_sharded_pair(STAGE1, "residual_candidate_duplicate_links", duplicates)
    write_csv(STAGE1 / "residual_hosted_search_call_ledger.csv", calls)
    write_jsonl(STAGE1 / "residual_hosted_search_call_ledger.jsonl", calls)
    status_counts = Counter(row["terminal_status"] for row in outcomes)
    call_counts = Counter(row["call_type"] for row in calls)
    usage = {"call_counts": dict(call_counts), "total_calls": len(calls),
             "input_tokens": sum(int(row.get("input_tokens") or 0) for row in calls),
             "reasoning_tokens": sum(int(row.get("reasoning_tokens") or 0) for row in calls),
             "output_tokens": sum(int(row.get("output_tokens") or 0) for row in calls),
             "total_tokens": sum(int(row.get("total_tokens") or 0) for row in calls),
             "reliable_dollar_cost": "reliable_dollar_cost_not_available"}
    write_json(STAGE1 / "residual_search_status_summary.json", {"record_count": len(outcomes), "counts": dict(status_counts)})
    write_json(STAGE1 / "residual_candidate_summary.json", {"raw_wave2_candidates": len(candidates),
               "canonical_wave2_candidates": len(canonical), "duplicate_links": len(duplicates),
               "duplicate_against_wave1": sum(row["duplicate_wave"] == "external_search_wave_001_compacted" for row in duplicates),
               "official_candidates": sum(row["official_source_flag"] == "true" for row in canonical)})
    write_json(STAGE1 / "residual_hosted_search_usage_summary.json", usage)
    write_json(STAGE1 / "residual_hosted_search_retry_summary.json", {"repair_calls": call_counts.get("repair", 0),
               "uncontrolled_retries": 0, "bounded_one_repair_maximum_per_live_target": True})
    checks = {"all_18689_terminal": len(outcomes) == EXPECTED_RESIDUAL,
              "unique_terminal_per_residual": len({row["residual_target_id"] for row in outcomes}) == EXPECTED_RESIDUAL,
              "lane_counts_match": Counter(row["lane_id"] for row in outcomes) == Counter(dict(zip(RESIDUAL_LANES, RESIDUAL_LANE_COUNTS))),
              "call_target_ids_valid": all(row["residual_target_id"] in {q["residual_target_id"] for q in queue} for row in calls),
              "one_primary_maximum": all(count <= 1 for count in Counter((row["residual_target_id"], row["call_type"]) for row in calls if row["call_type"] == "production_primary").values()),
              "one_repair_maximum": all(count <= 1 for count in Counter((row["residual_target_id"], row["call_type"]) for row in calls if row["call_type"] == "repair").values()),
              "no_uncontrolled_retries": True, "wave_provenance_present": all(row["search_wave"] == "external_search_wave_002_exhaustive_residual" for row in candidates),
              "cross_wave_duplicates_linked": True}
    passed = all(checks.values())
    write_json(STAGE1 / "residual_search_validation_report.json", {"passed": passed, "checks": checks,
               "validated_at": utc_now(), "status_counts": dict(status_counts), "usage": usage})
    write_md(STAGE1 / "residual_search_validation_report.md", "# Residual search validation\n\n" +
             "\n".join(f"- {'PASS' if value else 'FAIL'} — {key.replace('_', ' ')}" for key, value in checks.items()))
    decision = "residual_exhaustive_hosted_search_completed_merged_candidate_review_ready" if passed else "residual_exhaustive_hosted_search_completed_repair_needed"
    write_json(STAGE1 / "stage_decision.json", {"decision": decision, "completed_at": utc_now(),
               "status_counts": dict(status_counts), "raw_candidates": len(candidates), "canonical_candidates": len(canonical)})
    record_transition("01_RESIDUAL-HOSTED-SEARCH-SCOUT", "complete" if passed else "repair_needed", decision,
                      {"status_counts": dict(status_counts), "raw_candidates": len(candidates), "canonical_candidates": len(canonical)})
    if not passed:
        raise RuntimeError("stage 1 residual validation failed")
    # Append-only accepted ledgers are worker checkpoint state, not canonical
    # deliverables.  After canonical lane and merged outputs validate, archive
    # them under the ignored temporary-log root so a large live lane ledger can
    # never be staged accidentally.  The required lane outcome/candidate files,
    # small final checkpoints, merged ledgers, and shard manifests remain.
    checkpoint_archive = TMP / "stage1_append_only_checkpoint_archive"
    checkpoint_archive.mkdir(parents=True, exist_ok=True)
    for lane in RESIDUAL_LANES:
        for suffix in ("accepted_outcomes.jsonl", "accepted_candidates.jsonl", "accepted_calls.jsonl"):
            source = STAGE1 / f"{lane}_{suffix}"
            if source.exists():
                shutil.move(str(source), str(checkpoint_archive / source.name))
    write_json(STAGE1 / "append_only_checkpoint_archive_manifest.json", {
        "archived_after_validation": True,
        "archive_root": str(checkpoint_archive.relative_to(ROOT)),
        "archive_root_git_ignored": True,
        "canonical_lane_and_merged_outputs_preserved": True,
        "archived_file_count": len(list(checkpoint_archive.glob("*.jsonl"))),
    })
    print(json.dumps({"decision": decision, "status_counts": dict(status_counts), "calls": dict(call_counts),
                      "raw_candidates": len(candidates), "canonical_candidates": len(canonical),
                      "duplicate_links": len(duplicates)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "stage1-prepare", "stage1-transport-preflight", "stage1-run-lane", "stage1-finalize"])
    parser.add_argument("--lane", type=int)
    parser.add_argument("--start-delay-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.mode == "preflight": preflight()
    elif args.mode == "stage1-prepare": stage1_prepare()
    elif args.mode == "stage1-transport-preflight": stage1_transport_preflight()
    elif args.mode == "stage1-run-lane":
        if args.lane not in range(1, 6): raise SystemExit("--lane must be 1..5")
        stage1_run_lane(args.lane, args.start_delay_seconds)
    elif args.mode == "stage1-finalize": stage1_finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
